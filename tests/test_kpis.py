import pytest

from src.kpis import KPI_DEFINITIONS, compute_kpis, definitions_markdown


def _month(df, period):
    return df[df["period"] == period].iloc[0]


def test_monthly_kpis_on_fixture(fixture_con):
    df = compute_kpis(fixture_con, start="2018-02", end="2018-03")
    feb = _month(df, "2018-02")
    assert feb["revenue"] == pytest.approx(350)
    assert feb["orders"] == 2
    assert feb["aov"] == pytest.approx(175)
    assert feb["freight_ratio"] == pytest.approx(0.1)
    assert feb["avg_delivery_days"] == pytest.approx(10)
    assert feb["late_rate"] == pytest.approx(0.5)
    assert feb["avg_review_score"] == pytest.approx(3.0)  # (5 + avg(2,4) + 1) / 3
    assert feb["cancellation_rate"] == pytest.approx(1 / 3)
    mar = _month(df, "2018-03")
    assert mar["revenue"] == pytest.approx(300)
    assert mar["orders"] == 1
    assert mar["cancellation_rate"] == 0


def test_segment_kpis(fixture_con):
    df = compute_kpis(fixture_con, dims=["category"], start="2018-02", end="2018-02")
    rev = dict(zip(df["category"], df["revenue"]))
    assert rev["health_beauty"] == pytest.approx(150)
    assert rev["computers_accessories"] == pytest.approx(200)


def test_primary_payment_type(fixture_con):
    df = compute_kpis(fixture_con, dims=["payment_type"], start="2018-02", end="2018-03")
    assert set(df["payment_type"].dropna()) == {"credit_card", "boleto"}


def test_weekly_grain(fixture_con):
    df = compute_kpis(fixture_con, grain="week", start="2018-02", end="2018-03")
    assert df["revenue"].sum() == pytest.approx(650)


def test_definitions_single_source():
    md = definitions_markdown()
    for d in KPI_DEFINITIONS.values():
        assert d["label"] in md
