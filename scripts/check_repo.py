"""Repo hygiene check: fails on tracked data files, large files, or anything token-like."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANNED_SUFFIXES = {".csv", ".duckdb", ".parquet", ".env"}
MAX_BYTES = 5 * 1024 * 1024
# Eval outputs the spec asks to commit (one row per eval run, no dataset rows).
ALLOWED = {"results/eval_runs.csv"}
SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),                 # GitHub tokens
    re.compile(r"AKIA[0-9A-Z]{16}"),                            # AWS access key
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),                       # OpenAI/Anthropic-style keys
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),                # Slack
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\"key\"\s*:\s*\"[0-9a-f]{32}\""),              # kaggle.json
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"),
]


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    return [ROOT / p for p in out.stdout.decode().split("\0") if p]


def check(files: list[Path]) -> list[str]:
    problems = []
    for f in files:
        rel = f.relative_to(ROOT)
        if (f.suffix.lower() in BANNED_SUFFIXES or f.name == ".env") and str(rel) not in ALLOWED:
            problems.append(f"banned file type tracked: {rel}")
        if not f.exists():
            continue
        if f.stat().st_size > MAX_BYTES:
            problems.append(f"file over 5 MB: {rel}")
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
            continue
        text = f.read_text(errors="ignore")
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                problems.append(f"possible secret ({pat.pattern[:30]}...) in {rel}")
    return problems


def main() -> int:
    problems = check(tracked_files())
    for p in problems:
        print("FAIL:", p)
    print("check_repo: OK" if not problems else f"check_repo: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
