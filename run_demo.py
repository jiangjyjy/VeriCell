from __future__ import annotations

import argparse

from vericell.runner import run_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline certified-workflow demo.")
    parser.add_argument("--config", default=None, help="Optional relative YAML configuration path.")
    parser.add_argument("--output", default="outputs/demo", help="Relative output directory.")
    args = parser.parse_args()
    certificate = run_demo(args.config, args.output)
    print(f"certified={certificate['certification']['passed']}")
    print(f"sealed_test_pearson={certificate['sealed_test_metrics']['pearson']:.6f}")
    print(f"output={args.output}")


if __name__ == "__main__":
    main()
