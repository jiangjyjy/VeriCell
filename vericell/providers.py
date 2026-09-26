"""Provider boundary for the VeriCell pipeline.

The offline provider is deterministic and is the default used by the tests and
the demonstration.  The live adapter is deliberately opt-in: credentials are
read from an environment variable and no request is made during import.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


class ProviderError(RuntimeError):
    """A provider transport or response error with no secret-bearing payload."""


@dataclass(frozen=True)
class ProviderResponse:
    content: str
    model: str
    returned_model: str | None
    status: str
    http_status: int | None = None


class Provider(Protocol):
    def generate(self, messages: list[dict[str, str]]) -> ProviderResponse: ...


def _proposal_json() -> dict[str, Any]:
    """Safe deterministic proposal used by the offline path."""
    return {
        "model_family": "Ridge",
        "preprocessing_steps": ["train_only_standardize"],
        "modify_metrics": False,
        "modify_splits": False,
        "training_row_roles": ["TRAIN"],
        "result_affecting_validation_update": False,
        "resource_request": None,
        "validation_query_count": 0,
    }


class MockProvider:
    """Deterministic local provider; it never opens a socket.

    ``inject_violation_once`` is useful for integration tests: the first
    proposal intentionally violates the contract and a subsequent repair
    request receives a safe proposal.
    """

    def __init__(self, model: str = "offline-mock", *, inject_violation_once: bool = False) -> None:
        self.model = model
        self.calls = 0
        self.inject_violation_once = inject_violation_once
        self.messages: list[list[dict[str, str]]] = []

    def generate(self, messages: list[dict[str, str]]) -> ProviderResponse:
        if not messages:
            raise ProviderError("empty message list")
        self.calls += 1
        self.messages.append(messages)
        repair_request = any(message.get("role") == "user" and message.get("content", "").startswith("REPAIR:") for message in messages)
        proposal = _proposal_json()
        if self.inject_violation_once and self.calls == 1 and not repair_request:
            proposal.update(
                {
                    "preprocessing_steps": ["fit_on_validation"],
                    "result_affecting_validation_update": True,
                }
            )
        return ProviderResponse(
            content=json.dumps(proposal, sort_keys=True),
            model=self.model,
            returned_model=self.model,
            status="OK",
        )


@dataclass(frozen=True)
class LiveProviderConfig:
    """Configuration for an OpenAI-compatible endpoint.

    The endpoint must be supplied by the caller.  API keys are never stored in
    a repository config file; ``api_key_env`` names the environment variable
    read at request time.
    """

    base_url: str
    model: str
    api_key_env: str = "VERICELL_LLM_API_KEY"
    timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> "LiveProviderConfig":
        base_url = os.environ.get("VERICELL_LLM_BASE_URL", "").strip()
        model = os.environ.get("VERICELL_LLM_MODEL", "").strip()
        if not base_url or not model:
            raise ProviderError("VERICELL_LLM_BASE_URL and VERICELL_LLM_MODEL are required")
        return cls(
            base_url=base_url,
            model=model,
            api_key_env=os.environ.get("VERICELL_LLM_API_KEY_ENV", "VERICELL_LLM_API_KEY"),
            timeout_seconds=float(os.environ.get("VERICELL_LLM_TIMEOUT_SECONDS", "60")),
        )


class OpenAICompatibleProvider:
    """Small stdlib-only adapter for an explicitly requested live run."""

    def __init__(self, config: LiveProviderConfig) -> None:
        if not config.base_url.startswith("https://"):
            raise ProviderError("live provider base_url must use HTTPS")
        self.config = config

    def request_payload(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

    def generate(self, messages: list[dict[str, str]]) -> ProviderResponse:
        key = os.environ.get(self.config.api_key_env, "")
        if not key:
            raise ProviderError(f"missing API key environment variable: {self.config.api_key_env}")
        endpoint = self.config.base_url.rstrip("/") + "/chat/completions"
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(self.request_payload(messages)).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                status = int(response.status)
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise ProviderError(f"provider HTTP status {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ProviderError(f"provider transport/JSON failure: {type(exc).__name__}") from exc
        try:
            choice = body["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("provider response did not contain choices[0].message.content") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("provider returned empty content")
        return ProviderResponse(
            content=content,
            model=self.config.model,
            returned_model=body.get("model"),
            status="OK",
            http_status=status,
        )


def parse_proposal(response: ProviderResponse) -> dict[str, Any]:
    """Parse and validate only the provider's public workflow proposal."""
    if response.status != "OK":
        raise ProviderError(f"provider response status is {response.status}")
    try:
        proposal = json.loads(response.content)
    except json.JSONDecodeError as exc:
        raise ProviderError("provider content was not JSON") from exc
    if not isinstance(proposal, dict):
        raise ProviderError("provider JSON proposal must be an object")
    required = {"model_family", "preprocessing_steps", "modify_metrics", "modify_splits"}
    if not required.issubset(proposal):
        raise ProviderError("provider proposal omitted required contract fields")
    return proposal
