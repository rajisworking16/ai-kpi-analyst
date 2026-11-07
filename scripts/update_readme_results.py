"""Regenerate the README results table from results/eval_summary.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_readme import README, SUMMARY, expected_cells  # noqa: E402


def table(summary: dict) -> str:
    n = summary["n_scenarios"]
    lines = ["| Config | Root cause hit@1 | Root cause hit@3 | Unsupported claim rate | "
             "Mean steps | Mean time per run (s) |", "|---|---|---|---|---|---|"]
    for c, cfg in summary["configs"].items():
        lines.append(f"| {c}. {cfg['name']} | " + " | ".join(expected_cells(cfg, n)) + " |")
    return "\n".join(lines)


def main() -> None:
    summary = json.loads(SUMMARY.read_text())
    text = README.read_text()
    new = re.sub(r"(<!-- results:start -->\n).*?(\n<!-- results:end -->)",
                 lambda m: m.group(1) + table(summary) + m.group(2), text, flags=re.S)
    README.write_text(new)
    print(table(summary))


if __name__ == "__main__":
    main()
