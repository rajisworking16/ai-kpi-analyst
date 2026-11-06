import pytest

from src.verify import extract_numbers, number_supported, unsupported_items, verify_report

SOURCES = {
    "q_abc123": [{"customer_state": "SP", "revenue": 424628.36, "late_rate": 0.2312}],
    "decomp_revenue_category": [{"segment": "watches_gifts", "change": -30741.91,
                                 "share_of_change": 0.4513}],
    "detection": [{"kpi": "revenue", "current": 977544.69, "pct_change": -0.1534}],
}
ALWAYS = ["detection", "decomp_revenue_category"]


def _report(numbers, claim="x", ids=("q_abc123",), summary="Revenue fell."):
    return {"summary": summary, "findings": [{
        "claim": claim, "kpi": "revenue", "dimension": "customer_state", "segment": "SP",
        "numbers": [{"value": v, "meaning": "m"} for v in numbers],
        "evidence_query_ids": list(ids), "confidence": "high"}], "investigate_next": []}


def test_relative_tolerance():
    c = {"a": [424628.36]}
    assert number_supported(424628.36, c)
    assert number_supported(425000, c)          # within 1%
    assert not number_supported(440000, c)      # 3.6% off


def test_rounding_match():
    assert number_supported(0.23, {"a": [0.2312]}, decimals=2)
    assert not number_supported(0.25, {"a": [0.2312]}, decimals=2)


def test_percent_fraction_equivalence():
    assert number_supported(23.12, {"a": [0.2312]})
    assert number_supported(0.4513, {"a": [45.13]})


def test_sign_ignored():
    assert number_supported(30741.91, {"a": [-30741.91]})


def test_extract_ignores_years_months_ids_list_numbers():
    text = ("1. In 2018-05 (May 2018) revenue in SP fell 15.3% to R$ 977,544.69, see q_ab12cd "
            "and H2; seller 7d13fca15225358621be4086e1eb0964 and top 3 states.")
    vals = [v for v, *_ in extract_numbers(text)]
    assert vals == pytest.approx([15.3, 977544.69])


def test_extract_scale_words():
    vals = extract_numbers("a drop of 30.7k and 1.2 million")
    assert [v for v, *_ in vals] == pytest.approx([30700, 1200000])


def test_verified_finding():
    claim = "SP revenue was 424,628.36 with late rate 23.1%"
    v = verify_report(_report([424628.36, 0.2312], claim), SOURCES, ALWAYS)
    assert v.findings[0].label == "verified"
    assert v.unsupported_numbers == 0
    assert v.unsupported_rate == 0


def test_numbers_from_always_sources_without_citation():
    v = verify_report(_report([30741.91], ids=()), SOURCES, ALWAYS)
    assert v.findings[0].numbers[0].supported


def test_uncited_query_not_used():
    v = verify_report(_report([424628.36], ids=()), SOURCES, ALWAYS)
    assert not v.findings[0].numbers[0].supported
    assert v.findings[0].label == "unsupported"


def test_partially_verified_and_rate():
    v = verify_report(_report([424628.36, 999.5]), SOURCES, ALWAYS)
    assert v.findings[0].label == "partially_verified"
    assert v.unsupported_rate == pytest.approx(0.5)
    items = unsupported_items(_report([424628.36, 999.5]), v)
    assert items[0]["number"] == "999.5"


def test_invalid_query_id_flagged():
    v = verify_report(_report([424628.36], ids=("q_abc123", "q_missing")), SOURCES, ALWAYS)
    assert v.findings[0].invalid_ids == ["q_missing"]
    assert v.findings[0].label == "partially_verified"


def test_summary_numbers_checked():
    v = verify_report(_report([], summary="Revenue fell 15.34% to 977,544.69, not 12.5%."),
                      SOURCES, ALWAYS)
    sup = [n.supported for n in v.summary_numbers]
    assert sup == [True, True, False]


def test_finding_without_numbers_or_evidence_is_unsupported():
    v = verify_report(_report([], ids=()), SOURCES, ALWAYS)
    assert v.findings[0].label == "unsupported"
    assert v.unsupported_rate is None
