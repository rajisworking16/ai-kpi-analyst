"""Score a report against a scenario's ground truth."""

from __future__ import annotations

import re

BROAD_RE = re.compile(
    r"broad|across (all|many|most|every)|evenly|widespread|no single|uniform|general decline|"
    r"overall decline|all segments|across the board", re.IGNORECASE)
SHARE_WORDS = re.compile(r"share|explain|contribut|percent|%|portion|of the (drop|decline|"
                         r"change)", re.IGNORECASE)


def normalize_dimension(dim: str) -> str:
    """Map free-text dimension names to canonical ones."""
    d = (dim or "").lower()
    if "state" in d or "region" in d:
        return "customer_state"
    if "seller" in d:
        return "seller_id"
    if "payment" in d:
        return "payment_type"
    if "categor" in d or "product" in d:
        return "category"
    if d in ("", "overall", "all", "none", "total", "broad") or "overall" in d:
        return "overall"
    return d


def segment_matches(segment: str, aliases: list[str]) -> bool:
    """Case-insensitive match of a finding's segment against truth aliases."""
    s = (segment or "").lower().strip().strip("'\"`")
    for a in aliases:
        a = a.lower()
        if s == a or re.search(rf"(?<![a-z0-9_]){re.escape(a)}(?![a-z0-9_])", s):
            return True
        if len(a) == 32 and len(s) >= 8 and (a.startswith(s) or s.startswith(a[:8])):
            return True
    return False


def finding_hits(finding: dict, truth: dict) -> bool:
    return (normalize_dimension(finding.get("dimension", "")) == truth["dimension"]
            and segment_matches(finding.get("segment", ""), truth["aliases"]))


def _claims_majority(finding: dict) -> bool:
    if normalize_dimension(finding.get("dimension", "")) == "overall":
        return False
    for n in finding.get("numbers", []):
        v = abs(float(n["value"]))
        if SHARE_WORDS.search(n.get("meaning", "")) and (0.5 < v <= 1 or 50 < v <= 100):
            return True
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s?%", finding.get("claim", "")):
        if 50 < float(m.group(1)) <= 100 and SHARE_WORDS.search(finding.get("claim", "")):
            return True
    return False


def score_decoy(report: dict) -> dict:
    """Hit if no finding pins >50% of the drop on one segment and the summary says broad."""
    findings = report.get("findings", [])
    ok = (not any(_claims_majority(f) for f in findings)
          and bool(BROAD_RE.search(report.get("summary", ""))))
    return {"hit1": float(ok), "hit3": float(ok)}


def score_report(report: dict, scenario: dict) -> dict:
    """Root-cause hit@1 and hit@3. Multi-cause scenarios give partial credit per cause."""
    truths = scenario["truth"]
    if truths[0]["dimension"] == "overall":
        return score_decoy(report)
    findings = report.get("findings", [])
    w = 1.0 / len(truths)
    hit1 = sum(w for t in truths if findings and finding_hits(findings[0], t))
    hit3 = sum(w for t in truths if any(finding_hits(f, t) for f in findings[:3]))
    return {"hit1": hit1, "hit3": hit3}
