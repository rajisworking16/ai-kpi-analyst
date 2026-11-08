"""README consistency check: every number in the README results table must equal
the matching value in results/eval_summary.json.

The results table lives between `<!-- results:start -->` and `<!-- results:end -->`.
Rows look like: | A. Baseline (LLM only) | 3/12 | 5/12 | 12.5% (2/16) | 1.0 | 42.0 |
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SUMMARY = ROOT / "results" / "eval_summary.json"


def expected_cells(cfg: dict, n: int) -> list[str]:
    ur = "n/a" if cfg["unsupported_rate"] is None else f"{cfg['unsupported_rate']:.1%}"
    return [f"{cfg['hit1']:g}/{n}", f"{cfg['hit3']:g}/{n}",
            f"{ur} ({cfg['unsupported_numbers']}/{cfg['total_numbers']})",
            f"{cfg['mean_steps']}", f"{cfg['mean_time_s']}"]


def results_rows(text: str) -> dict[str, list[str]]:
    m = re.search(r"<!-- results:start -->(.*?)<!-- results:end -->", text, re.S)
    if not m:
        raise ValueError("README has no results block")
    rows = {}
    for line in m.group(1).strip().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        key = re.match(r"^([ABC])\.", cells[0])
        if key:
            rows[key.group(1)] = cells[1:]
    return rows


def main() -> int:
    text = README.read_text()
    if not SUMMARY.exists():
        print("FAIL: results/eval_summary.json missing")
        return 1
    summary = json.loads(SUMMARY.read_text())
    rows = results_rows(text)
    problems = []
    for c, cfg in summary["configs"].items():
        if c not in rows:
            problems.append(f"config {c} missing from README results table")
            continue
        exp = expected_cells(cfg, summary["n_scenarios"])
        got = rows[c][:len(exp)]
        if got != exp:
            problems.append(f"config {c}: README {got} != summary {exp}")
    for c in rows:
        if c not in summary["configs"]:
            problems.append(f"config {c} in README but not in summary")
    if "[TBD]" in "".join(" ".join(r) for r in rows.values()):
        problems.append("README results table still contains [TBD]")
    for p in problems:
        print("FAIL:", p)
    print("check_readme: OK" if not problems else f"check_readme: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
