from eval.score import normalize_dimension, score_report, segment_matches

SC = {"truth": [{"dimension": "category", "segment": "health_beauty",
                 "aliases": ["health_beauty", "beleza_saude"]}]}
TWO = {"truth": [SC["truth"][0], {"dimension": "customer_state", "segment": "PR",
                                  "aliases": ["PR"]}]}
DECOY = {"truth": [{"dimension": "overall", "segment": "broad", "aliases": []}]}


def _f(dim, seg, numbers=(), claim="c"):
    return {"dimension": dim, "segment": seg, "claim": claim,
            "numbers": [{"value": v, "meaning": m} for v, m in numbers]}


def test_dimension_synonyms():
    assert normalize_dimension("Customer State") == "customer_state"
    assert normalize_dimension("product category") == "category"
    assert normalize_dimension("seller") == "seller_id"


def test_segment_aliases_and_seller_prefix():
    assert segment_matches("Beleza_Saude", ["health_beauty", "beleza_saude"])
    assert segment_matches("'SP'", ["SP"])
    assert not segment_matches("ESP", ["SP"])
    sid = "7d13fca15225358621be4086e1eb0964"
    assert segment_matches("7d13fca1", [sid])


def test_hit_at_1_and_3():
    r = {"findings": [_f("customer_state", "SP"), _f("category", "health_beauty")]}
    assert score_report(r, SC) == {"hit1": 0.0, "hit3": 1.0}


def test_two_causes_half_credit():
    r = {"findings": [_f("category", "health_beauty"), _f("customer_state", "PR")]}
    assert score_report(r, TWO) == {"hit1": 0.5, "hit3": 1.0}


def test_decoy():
    good = {"summary": "The drop was broad-based across all segments.",
            "findings": [_f("overall", "all"), _f("category", "x", [(0.12, "share of change")])]}
    assert score_report(good, DECOY)["hit1"] == 1.0
    bad = {"summary": "The drop was broad-based.",
           "findings": [_f("category", "x", [(0.62, "share of the drop")])]}
    assert score_report(bad, DECOY)["hit1"] == 0.0
    no_broad = {"summary": "SP drove it.", "findings": [_f("customer_state", "SP")]}
    assert score_report(no_broad, DECOY)["hit1"] == 0.0
