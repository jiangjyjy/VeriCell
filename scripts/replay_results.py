#!/usr/bin/env python3
"""Offline-only inspection of the manuscript-aligned result bundle.

This command deliberately does not infer predictions from aggregate numbers.
It verifies that packaged tables are readable and reports whether a genuine
recomputation input is present in the release.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = (
    "table1.csv",
    "table2.csv",
    "table3.csv",
    "table4.md",
    "table5.csv",
    "table6.csv",
    "table7.md",
    "table8.csv",
    "table9.csv",
    "table10.csv",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_table(path: Path) -> dict[str, object]:
    if path.suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        return {
            "path": str(path.relative_to(ROOT)),
            "format": "csv",
            "rows": len(rows),
            "columns": list(rows[0]) if rows else [],
            "sha256": sha256(path),
            "recomputed": False,
            "status": "PAPER_REPORTED_ONLY",
        }
    text = path.read_text(encoding="utf-8")
    return {
        "path": str(path.relative_to(ROOT)),
        "format": "markdown",
        "rows": text.count("\n|") - 1,
        "columns": [],
        "sha256": sha256(path),
        "recomputed": False,
        "status": "PAPER_REPORTED_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="inspect every packaged table")
    args = parser.parse_args()
    if not args.all:
        parser.error("use --all for the complete packaged result bundle")

    records = []
    missing = []
    for name in TABLES:
        path = ROOT / "results" / name
        if not path.is_file():
            missing.append(name)
            continue
        records.append(inspect_table(path))
    summary = {
        "mode": "OFFLINE_PACKAGED_ARTIFACT_INSPECTION",
        "network_calls": 0,
        "provider_calls": 0,
        "sealed_test_loader_calls": 0,
        "training_runs": 0,
        "missing_tables": missing,
        "tables": records,
        "recomputed_tables": [r["path"] for r in records if r["recomputed"]],
        "paper_reported_only_tables": [r["path"] for r in records if not r["recomputed"]],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
