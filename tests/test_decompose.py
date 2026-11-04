import pandas as pd
import pytest

from src.decompose import decompose, revenue_split, segment_contribution
from src.detect import detect_from_table, shift_month


def test_revenue_split_sums_to_total():
    s = revenue_split(orders0=100, aov0=50.0, orders1=80, aov1=62.5)
    assert s["volume_effect"] + s["aov_effect"] + s["interaction"] == pytest.approx(
        s["total_change"])
    assert s["volume_effect"] == pytest.approx(-1000)
    assert s["aov_effect"] == pytest.approx(1250)
    assert s["interaction"] == pytest.approx(-250)


@pytest.mark.parametrize("o0,a0,o1,a1", [(7003, 136.1, 6798, 143.2), (1, 1, 0, 0), (5, 2, 9, 1)])
def test_revenue_split_random(o0, a0, o1, a1):
    s = revenue_split(o0, a0, o1, a1)
    assert s["volume_effect"] + s["aov_effect"] + s["interaction"] == pytest.approx(
        o1 * a1 - o0 * a0)


def test_shift_month():
    assert shift_month("2018-01", -1) == "2017-12"
    assert shift_month("2017-12", 1) == "2018-01"


def test_decompose_on_fixture(fixture_con):
    d = decompose(fixture_con, "2018-03", ["revenue", "late_rate"], dims=["category"])
    s = d["revenue_split"]
    assert s["total_change"] == pytest.approx(300 - 350)
    rev = d["segments"]["revenue"]["category"].set_index("segment")
    assert rev.at["health_beauty", "change"] == pytest.approx(-150)
    assert rev.at["computers_accessories", "change"] == pytest.approx(100)
    assert rev["change"].sum() == pytest.approx(-50)
    assert rev["share_of_change"].sum() == pytest.approx(1.0)


def _seg(rows):
    return pd.DataFrame(rows, columns=["period", "state", "late_rate", "delivered_with_date"])


def test_rate_contribution_sums_and_separates_mix():
    # Rates unchanged in each segment; only the mix shifts toward the slow state.
    seg = _seg([("m0", "A", 0.1, 90), ("m0", "B", 0.5, 10),
                ("m1", "A", 0.1, 50), ("m1", "B", 0.5, 50)])
    out = segment_contribution(seg, "state", "late_rate", "m0", "m1")
    total = (0.1 * 0.5 + 0.5 * 0.5) - (0.1 * 0.9 + 0.5 * 0.1)
    assert out["contribution"].sum() == pytest.approx(total)
    assert out["rate_effect"].abs().sum() == pytest.approx(0)
    assert out["mix_effect"].sum() == pytest.approx(total)


def test_rate_contribution_rate_effect():
    seg = _seg([("m0", "A", 0.1, 50), ("m0", "B", 0.1, 50),
                ("m1", "A", 0.1, 50), ("m1", "B", 0.5, 50)])
    out = segment_contribution(seg, "state", "late_rate", "m0", "m1").set_index("segment")
    assert out.at["B", "rate_effect"] == pytest.approx(0.2)
    assert out.at["A", "contribution"] == pytest.approx(0)


def test_detect_flags_large_change():
    rows = []
    for i, m in enumerate(["2017-09", "2017-10", "2017-11", "2017-12", "2018-01", "2018-02"]):
        rows.append({"period": m, **{k: 100.0 + i for k in _kpis()}})
    rows.append({"period": "2018-03", **{k: 60.0 for k in _kpis()}})
    changes = {c.kpi: c for c in detect_from_table(pd.DataFrame(rows), "2018-03")}
    rev = changes["revenue"]
    assert rev.significant and rev.direction == "down"
    assert rev.pct_change == pytest.approx((60 - 105) / 105)
    assert rev.z_score < -2


def test_detect_not_flagged_for_small_change():
    rows = [{"period": m, **{k: v for k in _kpis()}}
            for m, v in [("2017-09", 100), ("2017-10", 90), ("2017-11", 110), ("2017-12", 95),
                         ("2018-01", 105), ("2018-02", 100), ("2018-03", 101)]]
    changes = detect_from_table(pd.DataFrame(rows), "2018-03")
    assert not any(c.significant for c in changes)


def _kpis():
    from src.kpis import KPI_NAMES
    return KPI_NAMES
