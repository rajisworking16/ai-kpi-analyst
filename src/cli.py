"""Command-line entry point: python -m src.cli --month 2018-03 --question "..." """

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from config import DB_PATH
from src.pipeline import MODES, run
from src.report import save_report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Explain why a KPI changed.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--month", required=True, help="target month, YYYY-MM")
    parser.add_argument("--question", default="Why did revenue change?")
    parser.add_argument("--mode", choices=MODES, default="agent_verify")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    result = run(args.db, args.month, args.question, args.mode, run_id=args.run_id)
    path = save_report(result)
    ver = result["verification"]
    print(result["report"]["summary"])
    print(f"\nFindings: {len(result['report']['findings'])}, labels: "
          f"{[f['label'] for f in ver['findings']]}")
    print(f"Unsupported numbers: {ver['unsupported_numbers']}/{ver['total_numbers']}")
    print(f"Steps: {result['n_steps']}, time: {result['elapsed_s']}s")
    print(f"Report: {path}")


if __name__ == "__main__":
    main()
