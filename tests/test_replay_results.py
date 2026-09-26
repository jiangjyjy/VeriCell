from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_packaged_result_replay_is_local_and_complete() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/replay_results.py", "--all"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)
    assert summary["network_calls"] == 0
    assert summary["provider_calls"] == 0
    assert summary["sealed_test_loader_calls"] == 0
    assert summary["missing_tables"] == []
    assert len(summary["tables"]) == 10
    assert summary["recomputed_tables"] == []
