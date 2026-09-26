#!/usr/bin/env python3
"""Run the configured VeriCell pipeline (offline by default)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vericell.pipeline import run_pipeline
from vericell.providers import LiveProviderConfig, MockProvider, OpenAICompatibleProvider


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--output", default="outputs/pipeline")
    parser.add_argument("--mode", choices=("offline", "live"), default="offline")
    args = parser.parse_args()
    config = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    provider = MockProvider(inject_violation_once=True) if args.mode == "offline" else OpenAICompatibleProvider(LiveProviderConfig.from_env())
    certificate = run_pipeline(config, ROOT / args.output, provider)
    print(json.dumps({"mode": args.mode, "certified": certificate["certification"]["passed"], "output": args.output}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
