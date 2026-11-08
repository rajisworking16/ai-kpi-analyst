"""Deterministic claim verifier: every cited number must exist in the cited evidence."""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field

from config import VERIFY_REL_TOL

SCALE_WORDS = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "mn": 1e6,
               "bn": 1e9, "billion": 1e9}
NUM_RE = re.compile(
    r"(?<![\w.])(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?)"
    r"(\s?%|\s?(?:k|K|M|mn|bn|thousand|million|billion)\b)?(?![\w])"
)
STRIP_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?\b"),                 # dates and months
    re.compile(r"\b[0-9a-f]{16,}\b"),                          # seller / product ids
    re.compile(r"\b(?:q_[0-9a-z]+|H\d+|decomp_\w+)\b"),        # query / hypothesis ids
    re.compile(r"(?m)^\s*\d+[.)]\s"),                          # list numbering
    re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|"
               r"October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|"
               r"Dec)\.?\s+\d{1,2}\b"),                         # month day
]
SMALL_INT_MAX = 10  # bare integers 0..10 are treated as wording ("top 3"), not data claims


@dataclass
class CheckedNumber:
    value: float
    text: str
    source: str  # "numbers", "claim" or "summary"
    supported: bool
    matched_in: str | None = None


@dataclass
class FindingCheck:
    index: int
    label: str
    numbers: list[CheckedNumber]
    valid_ids: list[str]
    invalid_ids: list[str]


@dataclass
class Verification:
    findings: list[FindingCheck] = field(default_factory=list)
    summary_numbers: list[CheckedNumber] = field(default_factory=list)

    @property
    def all_numbers(self) -> list[CheckedNumber]:
        return [n for f in self.findings for n in f.numbers] + self.summary_numbers

    @property
    def total_numbers(self) -> int:
        return len(self.all_numbers)

    @property
    def unsupported_numbers(self) -> int:
        return sum(not n.supported for n in self.all_numbers)

    @property
    def unsupported_rate(self) -> float | None:
        return self.unsupported_numbers / self.total_numbers if self.total_numbers else None

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(total_numbers=self.total_numbers, unsupported_numbers=self.unsupported_numbers,
                 unsupported_rate=self.unsupported_rate)
        return d


def _decimals(text: str) -> int:
    return len(text.split(".")[1]) if "." in text else 0


def extract_numbers(text: str) -> list[tuple[float, str, int, float, bool]]:
    """Extract numbers from free text as (value, raw, decimals, scale, is_percent).

    Years, dates, ids, list numbering and bare small integers are ignored.
    """
    clean = text or ""
    for pat in STRIP_PATTERNS:
        clean = pat.sub(" ", clean)
    out = []
    for m in NUM_RE.finditer(clean):
        raw, suffix = m.group(1), (m.group(2) or "").strip().lower()
        base = float(raw.replace(",", ""))
        is_pct = suffix == "%"
        scale = SCALE_WORDS.get(suffix, 1.0)
        is_int = "." not in raw
        if not is_pct and scale == 1.0 and is_int and "," not in raw:
            if 1900 <= base <= 2100 or abs(base) <= SMALL_INT_MAX:
                continue
        out.append((base * scale, m.group(0).strip(), _decimals(raw), scale, is_pct))
    return out


def _close(target: float, cand: float, decimals: int | None, scale: float) -> bool:
    t, c = abs(target), abs(cand)
    if c == 0 or t == 0:
        return t == c
    if abs(t - c) / c <= VERIFY_REL_TOL:
        return True
    if decimals is not None:
        return round(c / scale, decimals) == round(t / scale, decimals)
    return False


def number_supported(value: float, candidates: dict[str, list[float]],
                     decimals: int | None = None, scale: float = 1.0) -> str | None:
    """Return the evidence id containing a match for `value`, or None.

    Fractions and percentages are equivalent (0.23 matches 23), and the sign is ignored
    because text usually states direction in words ("fell by 120").
    """
    variants = [(value, decimals, scale), (value / 100, None if decimals is None
                else decimals + 2, scale), (value * 100, None, scale)]
    for eid, nums in candidates.items():
        for v, d, s in variants:
            if any(_close(v, c, d, s) for c in nums):
                return eid
    return None


def _numbers_in_rows(rows: list[dict]) -> list[float]:
    out = []
    for r in rows:
        for v in r.values():
            if isinstance(v, bool) or v is None:
                continue
            if isinstance(v, int | float) and math.isfinite(v):
                out.append(float(v))
    return out


def _check_text(text: str, source: str, cands: dict[str, list[float]],
                skip: list[float]) -> list[CheckedNumber]:
    out = []
    for value, raw, dec, scale, is_pct in extract_numbers(text):
        if any(math.isclose(value, s, rel_tol=1e-9) for s in skip):
            continue
        if is_pct:
            eid = number_supported(value / 100, cands, dec + 2, 1.0) or number_supported(
                value, cands, dec, 1.0)
        else:
            eid = number_supported(value, cands, dec, scale)
        out.append(CheckedNumber(value, raw, source, eid is not None, eid))
    return out


def _label(numbers: list[CheckedNumber], valid: list[str], invalid: list[str]) -> str:
    if not numbers:
        return "verified" if valid and not invalid else "unsupported"
    ok = sum(n.supported for n in numbers)
    if ok == 0:
        return "unsupported"
    if ok == len(numbers) and not invalid:
        return "verified"
    return "partially_verified"


def verify_report(report: dict, sources: dict[str, list[dict]],
                  always: list[str]) -> Verification:
    """Verify `report` against evidence.

    `sources` maps evidence id -> rows (query results and deterministic tables).
    `always` lists evidence ids that every number may match (detection/decomposition or,
    for the baseline, the KPI totals table), cited or not.
    """
    numeric = {eid: _numbers_in_rows(rows) for eid, rows in sources.items()}
    base = {eid: numeric[eid] for eid in always if eid in numeric}
    result = Verification()
    all_cited: dict[str, list[float]] = dict(base)
    for i, f in enumerate(report.get("findings", [])):
        ids = list(dict.fromkeys(f.get("evidence_query_ids", [])))
        valid = [e for e in ids if e in numeric]
        invalid = [e for e in ids if e not in numeric]
        cands = {**{e: numeric[e] for e in valid}, **base}
        all_cited.update({e: numeric[e] for e in valid})
        checked = []
        for n in f.get("numbers", []):
            v = float(n["value"])
            eid = number_supported(v, cands, _decimals(repr(v)))
            checked.append(CheckedNumber(v, repr(v), "numbers", eid is not None, eid))
        skip = [c.value for c in checked]
        checked += _check_text(f.get("claim", ""), "claim", cands, skip)
        result.findings.append(FindingCheck(i, _label(checked, valid, invalid), checked,
                                            valid, invalid))
    result.summary_numbers = _check_text(report.get("summary", ""), "summary", all_cited, [])
    return result


def unsupported_items(report: dict, ver: Verification) -> list[dict]:
    """List unsupported numbers with the finding they belong to (for the revision prompt)."""
    items = []
    for fc in ver.findings:
        claim = report["findings"][fc.index]["claim"]
        for n in fc.numbers:
            if not n.supported:
                items.append({"finding": fc.index + 1, "number": n.text, "where": n.source,
                              "claim": claim, "cited": fc.valid_ids})
    for n in ver.summary_numbers:
        if not n.supported:
            items.append({"finding": "summary", "number": n.text, "where": "summary",
                          "claim": report.get("summary", ""), "cited": []})
    return items
