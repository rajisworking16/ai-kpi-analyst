import duckdb
import pytest

from eval.inject import inject

M = "2018-02"


def _run(fixture_db, tmp_path, ops):
    out = tmp_path / "inj.duckdb"
    inject({"id": "t", "month": M, "ops": ops}, fixture_db, out, level=0)
    return duckdb.connect(str(out), read_only=True)


def _col(con, sql):
    return [r[0] for r in con.execute(sql).fetchall()]


def test_base_db_untouched(fixture_db, tmp_path):
    _run(fixture_db, tmp_path, [{"op": "delete_random", "fraction": [1.0]}])
    con = duckdb.connect(str(fixture_db), read_only=True)
    assert con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 4


def test_delete_orders_cascades_and_only_hits_segment(fixture_db, tmp_path):
    con = _run(fixture_db, tmp_path, [{"op": "delete_orders", "dimension": "category",
                                        "segment": "health_beauty", "fraction": [1.0]}])
    assert sorted(_col(con, "SELECT order_id FROM orders")) == ["o3", "o4"]
    for t in ["order_items", "payments", "reviews"]:
        ids = set(_col(con, f"SELECT order_id FROM {t}"))
        assert not ids & {"o1", "o2"}
    assert _col(con, "SELECT price FROM order_items WHERE order_id = 'o4'") == [300]


def test_scale_price_only_category_and_month(fixture_db, tmp_path):
    con = _run(fixture_db, tmp_path, [{"op": "scale_price", "dimension": "category",
                                        "segment": "computers_accessories", "factor": [1.3]}])
    prices = dict(con.execute("SELECT order_id || '-' || order_item_id, price "
                              "FROM order_items").fetchall())
    assert prices["o2-1"] == pytest.approx(260)
    assert prices["o2-2"] == pytest.approx(50)
    assert prices["o1-1"] == pytest.approx(100)
    assert prices["o4-1"] == pytest.approx(300)


def test_delay_and_reviews(fixture_db, tmp_path):
    con = _run(fixture_db, tmp_path, [{"op": "delay", "state": "RJ", "days": [10],
                                        "review_fraction": [1.0]}])
    d = dict(con.execute("SELECT order_id, CAST(order_delivered_customer_date AS DATE)::VARCHAR"
                         " FROM orders").fetchall())
    assert d["o2"] == "2018-03-07" and d["o1"] == "2018-02-10" and d["o4"] == "2018-03-04"
    scores = dict(con.execute("SELECT review_id, review_score FROM reviews").fetchall())
    assert scores["r2a"] == 1 and scores["r2b"] == 1 and scores["r1"] == 5


def test_scale_freight_state_only(fixture_db, tmp_path):
    con = _run(fixture_db, tmp_path, [{"op": "scale_freight", "state": "SP", "factor": [1.8]}])
    f = dict(con.execute("SELECT order_id || '-' || order_item_id, freight_value "
                         "FROM order_items").fetchall())
    assert f["o1-1"] == pytest.approx(18)
    assert f["o2-1"] == pytest.approx(20)
    assert f["o4-1"] == pytest.approx(30)


def test_duplicate_orders_copies_children(fixture_db, tmp_path):
    con = _run(fixture_db, tmp_path, [{"op": "duplicate_orders", "state": "SP",
                                        "fraction": [1.0]}])
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["orders", "order_items", "payments", "reviews"]}
    assert counts == {"orders": 6, "order_items": 5, "payments": 4, "reviews": 7}
    assert con.execute("SELECT COUNT(DISTINCT order_id) FROM orders").fetchone()[0] == 6
    assert con.execute("SELECT COUNT(DISTINCT review_id) FROM reviews").fetchone()[0] == 7


def test_switch_payment_month_only(fixture_db, tmp_path):
    con = _run(fixture_db, tmp_path, [{"op": "switch_payment", "from": "credit_card",
                                        "to": "voucher", "fraction": [1.0]}])
    p = dict(con.execute("SELECT order_id, payment_type FROM payments").fetchall())
    assert p == {"o1": "voucher", "o2": "boleto", "o4": "credit_card"}


def test_cancel_orders(fixture_db, tmp_path):
    con = _run(fixture_db, tmp_path, [{"op": "cancel_orders", "dimension": "category",
                                        "segment": "computers_accessories", "fraction": [1.0]}])
    s = dict(con.execute("SELECT order_id, order_status FROM orders").fetchall())
    assert s == {"o1": "delivered", "o2": "canceled", "o3": "canceled", "o4": "delivered"}


def test_delete_random_only_target_month(fixture_db, tmp_path):
    con = _run(fixture_db, tmp_path, [{"op": "delete_random", "fraction": [0.5]}])
    ids = _col(con, "SELECT order_id FROM orders")
    assert "o4" in ids and len(ids) == 2
