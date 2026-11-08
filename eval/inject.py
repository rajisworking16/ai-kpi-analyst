"""Anomaly injection: copy the database, plant one known anomaly in one month, save it.

Usage:
    python -m eval.inject --generate      # pick segments from data, write eval/scenarios.yaml
    python -m eval.inject --all           # build data/eval/<scenario_id>.duckdb for every scenario
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path

import duckdb
import yaml

from config import DB_PATH, EVAL_DATA_DIR, RESULTS_DIR, ROOT
from src.detect import detect_changes

SCENARIOS_PATH = ROOT / "eval" / "scenarios.yaml"
INJECTIONS_PATH = RESULTS_DIR / "eval_injections.json"
SEED = 42
EVAL_MONTH = "2018-05"
MIN_ORDER_SHARE = 0.03
CHILD_TABLES = ["order_items", "payments", "reviews"]


# ---------------------------------------------------------------- segment picking

def _month_orders(con: duckdb.DuckDBPyConnection, month: str) -> int:
    return con.execute("SELECT COUNT(DISTINCT order_id) FROM orders_enriched WHERE "
                       "order_month = ? AND order_status = 'delivered'", [month]).fetchone()[0]


def _ranked(con, month: str, dim: str, order_by: str, min_orders: float) -> list[tuple]:
    extra = ", ANY_VALUE(category_pt)" if dim == "category" else ""
    sql = f"""
        SELECT {dim}, COUNT(DISTINCT order_id) AS n, SUM(price) AS revenue,
               SUM(price) / COUNT(DISTINCT order_id) AS aov{extra}
        FROM orders_enriched
        WHERE order_month = ? AND order_status = 'delivered' AND {dim} IS NOT NULL
          AND {dim} <> 'unknown'
        GROUP BY {dim} HAVING COUNT(DISTINCT order_id) >= ?
        ORDER BY {order_by} DESC"""
    return con.execute(sql, [month, min_orders]).fetchall()


def pick_segments(db_path: Path, month: str) -> dict:
    """Pick scenario segments automatically (each >= 3% of the month's delivered orders)."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        min_orders = MIN_ORDER_SHARE * _month_orders(con, month)
        cats_by_aov = _ranked(con, month, "category", "aov", min_orders)
        cats_by_rev = _ranked(con, month, "category", "revenue", min_orders)
        states = _ranked(con, month, "customer_state", "n", min_orders)
        sellers = _ranked(con, month, "seller_id", "revenue", 0)
    finally:
        con.close()
    pt = {c[0]: c[4] for c in cats_by_rev}
    picks = {"top_aov_category": cats_by_aov[0][0]}
    remaining = [c[0] for c in cats_by_rev if c[0] != picks["top_aov_category"]]
    for key, cat in zip(["A", "B", "C", "D"], remaining, strict=False):
        picks[key] = cat
    state_order = ["S4", "S3", "S1", "S2", "S5"]  # biggest state to the volume scenario
    for key, st in zip(state_order, [s[0] for s in states], strict=False):
        picks[key] = st
    picks["top_seller"] = sellers[0][0]
    picks["top_seller_order_share"] = sellers[0][1] / (min_orders / MIN_ORDER_SHARE)
    picks["category_pt"] = {v: pt[v] for k, v in picks.items()
                            if k in ("A", "B", "C", "D", "top_aov_category")}
    picks["min_orders"] = min_orders
    return picks


def _truth(dim: str, seg: str, picks: dict) -> dict:
    aliases = [seg]
    if dim == "category":
        aliases.append(picks["category_pt"][seg])
    return {"dimension": dim, "segment": seg, "aliases": aliases}


def build_scenarios(picks: dict, month: str = EVAL_MONTH) -> list[dict]:
    """The 12 scenarios of PROJECT_SPEC section 5.1 with concrete segments."""
    p = picks
    cat = lambda k: _truth("category", p[k], p)  # noqa: E731
    st = lambda k: _truth("customer_state", p[k], p)  # noqa: E731

    def sc(i, name, question, kpi, truth, ops):
        return {"id": f"s{i:02d}_{name}", "question": question, "month": month,
                "target_kpi": kpi, "truth": truth, "ops": ops}

    return [
        sc(1, "category_demand_drop", "Why did revenue drop?", ["revenue"], [cat("A")],
           [{"op": "delete_orders", "dimension": "category", "segment": p["A"],
             "fraction": [0.5, 0.75]}]),
        sc(2, "category_price_hike", "Why did AOV rise?", ["aov"], [cat("B")],
           [{"op": "scale_price", "dimension": "category", "segment": p["B"],
             "factor": [1.3, 1.6]}]),
        sc(3, "top_seller_dropout", "Why did revenue drop?", ["revenue"],
           [_truth("seller_id", p["top_seller"], p)],
           [{"op": "delete_orders", "dimension": "seller_id", "segment": p["top_seller"],
             "fraction": [1.0, 1.0]}]),
        sc(4, "regional_delivery_delay", "Why did late deliveries rise?", ["late_rate"],
           [st("S1")], [{"op": "delay", "state": p["S1"], "days": [10, 20]}]),
        sc(5, "delay_hurts_reviews", "Why did review scores fall?", ["avg_review_score"],
           [st("S2")], [{"op": "delay", "state": p["S2"], "days": [10, 20],
                         "review_fraction": [0.5, 0.75]}]),
        sc(6, "freight_spike", "Why did the freight ratio rise?", ["freight_ratio"], [st("S3")],
           [{"op": "scale_freight", "state": p["S3"], "factor": [1.8, 2.5]}]),
        sc(7, "regional_demand_surge", "Why did orders rise?", ["orders"], [st("S4")],
           [{"op": "duplicate_orders", "state": p["S4"], "fraction": [0.4, 0.8]}]),
        sc(8, "payment_mix_shift", "What changed in payments?", [],
           [{"dimension": "payment_type", "segment": "credit_card",
             "aliases": ["credit_card", "voucher"]}],
           [{"op": "switch_payment", "from": "credit_card", "to": "voucher",
             "fraction": [0.6, 0.9]}]),
        sc(9, "cancellation_spike", "Why did cancellations rise?", ["cancellation_rate"],
           [cat("C")], [{"op": "cancel_orders", "dimension": "category", "segment": p["C"],
                         "fraction": [0.25, 0.5]}]),
        sc(10, "big_ticket_category_drop", "Why did AOV fall?", ["aov"],
           [cat("top_aov_category")],
           [{"op": "delete_orders", "dimension": "category", "segment": p["top_aov_category"],
             "fraction": [0.6, 0.9]}]),
        sc(11, "two_causes", "Why did revenue drop and late deliveries rise?",
           ["revenue", "late_rate"], [cat("D"), st("S5")],
           [{"op": "delete_orders", "dimension": "category", "segment": p["D"],
             "fraction": [0.5, 0.75]},
            {"op": "delay", "state": p["S5"], "days": [10, 20]}]),
        sc(12, "decoy_broad_drop", "Why did revenue drop?", ["revenue"],
           [{"dimension": "overall", "segment": "broad", "aliases": []}],
           [{"op": "delete_random", "fraction": [0.15, 0.25]}]),
    ]


# ---------------------------------------------------------------- injection operations

def _ids(con, sql: str, params: list) -> list[str]:
    return sorted(r[0] for r in con.execute(sql, params).fetchall())


def _sample(ids: list[str], fraction: float, rng: random.Random) -> list[str]:
    k = round(len(ids) * fraction)
    return sorted(rng.sample(ids, k)) if k < len(ids) else list(ids)


def _with_ids(con, ids: list[str]) -> None:
    con.execute("CREATE OR REPLACE TEMP TABLE _sel (order_id VARCHAR)")
    if ids:
        con.executemany("INSERT INTO _sel VALUES (?)", [[i] for i in ids])


def _segment_orders(con, month: str, dim: str, segment: str) -> list[str]:
    return _ids(con, f"SELECT DISTINCT order_id FROM orders_enriched WHERE order_month = ? "
                     f"AND {dim} = ?", [month, segment])


def _state_orders(con, month: str, state: str, delivered_only: bool = False) -> list[str]:
    cond = " AND order_delivered_customer_date IS NOT NULL" if delivered_only else ""
    return _ids(con, f"SELECT DISTINCT order_id FROM orders_enriched WHERE order_month = ? "
                     f"AND customer_state = ?{cond}", [month, state])


def delete_orders(con, ids: list[str]) -> int:
    """Delete orders and cascade to items, payments and reviews."""
    _with_ids(con, ids)
    for t in [*CHILD_TABLES, "orders"]:
        con.execute(f"DELETE FROM {t} WHERE order_id IN (SELECT order_id FROM _sel)")
    return len(ids)


def op_delete_orders(con, month, rng, op, level) -> int:
    ids = _segment_orders(con, month, op["dimension"], op["segment"])
    return delete_orders(con, _sample(ids, op["fraction"][level], rng))


def op_delete_random(con, month, rng, op, level) -> int:
    ids = _ids(con, "SELECT order_id FROM orders WHERE strftime(order_purchase_timestamp, "
                    "'%Y-%m') = ?", [month])
    return delete_orders(con, _sample(ids, op["fraction"][level], rng))


def op_scale_price(con, month, rng, op, level) -> int:
    _with_ids(con, _segment_orders(con, month, op["dimension"], op["segment"]))
    con.execute("""UPDATE order_items SET price = price * ? WHERE order_id IN
        (SELECT order_id FROM _sel) AND product_id IN (SELECT p.product_id FROM products p
        LEFT JOIN category_translation t USING (product_category_name)
        WHERE COALESCE(t.product_category_name_english, p.product_category_name) = ?)""",
                [op["factor"][level], op["segment"]])
    return con.execute("SELECT COUNT(*) FROM _sel").fetchone()[0]


def op_delay(con, month, rng, op, level) -> int:
    ids = _state_orders(con, month, op["state"], delivered_only=True)
    _with_ids(con, ids)
    con.execute(f"""UPDATE orders SET order_delivered_customer_date =
        order_delivered_customer_date + INTERVAL {int(op['days'][level])} DAY
        WHERE order_id IN (SELECT order_id FROM _sel)""")
    if "review_fraction" in op:
        reviewed = _ids(con, "SELECT DISTINCT order_id FROM reviews WHERE order_id IN "
                             "(SELECT order_id FROM _sel)", [])
        _with_ids(con, _sample(reviewed, op["review_fraction"][level], rng))
        con.execute("UPDATE reviews SET review_score = 1 WHERE order_id IN "
                    "(SELECT order_id FROM _sel)")
    return len(ids)


def op_scale_freight(con, month, rng, op, level) -> int:
    ids = _state_orders(con, month, op["state"])
    _with_ids(con, ids)
    con.execute("UPDATE order_items SET freight_value = freight_value * ? WHERE order_id IN "
                "(SELECT order_id FROM _sel)", [op["factor"][level]])
    return len(ids)


def op_duplicate_orders(con, month, rng, op, level) -> int:
    """Copy orders with new ids; items, payments and reviews are copied too."""
    ids = _sample(_state_orders(con, month, op["state"]), op["fraction"][level], rng)
    _with_ids(con, ids)
    new = "md5(order_id || '_dup')"
    con.execute(f"INSERT INTO orders SELECT * REPLACE ({new} AS order_id) FROM orders "
                "WHERE order_id IN (SELECT order_id FROM _sel)")
    for t in ["order_items", "payments"]:
        con.execute(f"INSERT INTO {t} SELECT * REPLACE ({new} AS order_id) FROM {t} "
                    "WHERE order_id IN (SELECT order_id FROM _sel)")
    con.execute(f"INSERT INTO reviews SELECT * REPLACE ({new} AS order_id, "
                "md5(review_id || '_dup') AS review_id) FROM reviews "
                "WHERE order_id IN (SELECT order_id FROM _sel)")
    return len(ids)


def op_switch_payment(con, month, rng, op, level) -> int:
    rows = con.execute("""SELECT p.order_id, p.payment_sequential FROM payments p
        JOIN orders o USING (order_id) WHERE strftime(o.order_purchase_timestamp, '%Y-%m') = ?
        AND p.payment_type = ? ORDER BY 1, 2""", [month, op["from"]]).fetchall()
    k = round(len(rows) * op["fraction"][level])
    chosen = sorted(rng.sample(rows, k))
    con.execute("CREATE OR REPLACE TEMP TABLE _psel (order_id VARCHAR, seq BIGINT)")
    con.executemany("INSERT INTO _psel VALUES (?, ?)", [list(r) for r in chosen])
    con.execute("""UPDATE payments SET payment_type = ? WHERE (order_id, payment_sequential)
        IN (SELECT (order_id, seq) FROM _psel)""", [op["to"]])
    return k


def op_cancel_orders(con, month, rng, op, level) -> int:
    ids = _segment_orders(con, month, op["dimension"], op["segment"])
    chosen = _sample(ids, op["fraction"][level], rng)
    _with_ids(con, chosen)
    con.execute("UPDATE orders SET order_status = 'canceled', order_delivered_customer_date = "
                "NULL WHERE order_id IN (SELECT order_id FROM _sel)")
    return len(chosen)


OPS = {
    "delete_orders": op_delete_orders, "delete_random": op_delete_random,
    "scale_price": op_scale_price, "delay": op_delay, "scale_freight": op_scale_freight,
    "duplicate_orders": op_duplicate_orders, "switch_payment": op_switch_payment,
    "cancel_orders": op_cancel_orders,
}


def inject(scenario: dict, base_db: Path, out_path: Path, level: int = 0) -> dict:
    """Copy `base_db` to `out_path` and apply the scenario's ops at strength `level`."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(base_db, out_path)
    rng = random.Random(SEED)
    con = duckdb.connect(str(out_path))
    try:
        affected = [OPS[op["op"]](con, scenario["month"], rng, op, level)
                    for op in scenario["ops"]]
        con.execute("CHECKPOINT")
    finally:
        con.close()
    return {"affected": affected, "level": level}


def target_flagged(db_path: Path, scenario: dict) -> dict[str, bool]:
    """Whether detection flags each target KPI as significant on the injected database."""
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        changes = {c.kpi: c for c in detect_changes(con, scenario["month"])}
    finally:
        con.close()
    return {k: changes[k].significant for k in scenario["target_kpi"]}


def build_scenario_db(scenario: dict, base_db: Path = DB_PATH,
                      out_dir: Path = EVAL_DATA_DIR) -> dict:
    """Inject; if a target KPI is not flagged, retry once at the next strength level."""
    out = out_dir / f"{scenario['id']}.duckdb"
    info = inject(scenario, base_db, out, 0)
    flags = target_flagged(out, scenario)
    if flags and not all(flags.values()):
        info = inject(scenario, base_db, out, 1)
        flags = target_flagged(out, scenario)
    con = duckdb.connect(str(out), read_only=True)
    detection = {c.kpi: {"pct_change": c.pct_change, "z_score": c.z_score,
                         "significant": c.significant}
                 for c in detect_changes(con, scenario["month"])}
    con.close()
    return {"id": scenario["id"], **info, "target_flagged": flags,
            "detection": {k: detection[k] for k in scenario["target_kpi"]}}


def load_scenarios(path: Path = SCENARIOS_PATH) -> list[dict]:
    return yaml.safe_load(path.read_text())["scenarios"]


def write_scenarios(picks: dict, scenarios: list[dict], path: Path = SCENARIOS_PATH) -> None:
    header = ("# Generated by `python -m eval.inject --generate` from the data.\n"
              "# Segments are picked automatically (see docs/DECISIONS.md).\n"
              "# Strength lists are [base, one step stronger]; the stronger level is used only\n"
              "# if detection does not flag the target KPI at the base level.\n")
    body = yaml.safe_dump({"seed": SEED, "picks": picks, "scenarios": scenarios},
                          sort_keys=False, width=100)
    path.write_text(header + body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--scenario", default=None)
    args = parser.parse_args()
    if args.generate:
        picks = pick_segments(DB_PATH, EVAL_MONTH)
        write_scenarios(picks, build_scenarios(picks))
        print(json.dumps(picks, indent=1))
    if args.all or args.scenario:
        results = []
        for sc in load_scenarios():
            if args.scenario and sc["id"] != args.scenario:
                continue
            r = build_scenario_db(sc)
            print(json.dumps(r))
            results.append(r)
        if args.all:
            INJECTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
            INJECTIONS_PATH.write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
