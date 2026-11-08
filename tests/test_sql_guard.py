import pytest

from src.sql_guard import RunTrace, SQLGuardError, run_readonly, validate

BAD = [
    "DELETE FROM orders",
    "INSERT INTO orders VALUES (1)",
    "UPDATE orders SET order_status = 'x'",
    "DROP TABLE orders",
    "CREATE TABLE t AS SELECT 1",
    "ATTACH 'other.duckdb' AS o",
    "COPY orders TO 'out.csv'",
    "INSTALL httpfs",
    "LOAD httpfs",
    "PRAGMA database_list",
    "SELECT * FROM read_csv('data/raw/olist_orders_dataset.csv')",
    "SELECT * FROM read_parquet('x.parquet')",
    "SELECT * FROM 'data/raw/olist_orders_dataset.csv'",
    "SELECT 1; SELECT 2",
    "SELECT 1; DROP TABLE orders",
    "SET threads = 1",
    "",
]


@pytest.mark.parametrize("sql", BAD)
def test_rejects(sql):
    with pytest.raises(SQLGuardError):
        validate(sql)


def test_allows_select_and_with():
    assert "LIMIT 200" in validate("SELECT 1 AS x")
    assert validate("WITH a AS (SELECT 1 AS x) SELECT * FROM a").upper().startswith("WITH")


def test_limit_enforced_and_kept_when_smaller():
    assert "LIMIT 200" in validate("SELECT * FROM orders LIMIT 100000")
    assert "LIMIT 5" in validate("SELECT * FROM orders LIMIT 5")


def test_string_literal_with_keyword_ok():
    validate("SELECT * FROM orders WHERE order_status = 'delete me'")


def test_run_readonly_returns_rows_and_traces(fixture_db):
    trace = RunTrace()
    r = run_readonly("SELECT order_id FROM orders ORDER BY order_id", db_path=fixture_db,
                     trace=trace, max_rows=2)
    assert r.error is None
    assert r.row_count == 2
    assert r.rows[0] == {"order_id": "o1"}
    assert r.query_id.startswith("q_") and r.query_id in trace.queries


def test_run_readonly_reports_errors(fixture_db):
    r = run_readonly("SELECT nope FROM orders", db_path=fixture_db)
    assert r.error and r.error.startswith("sql error")
    r = run_readonly("DELETE FROM orders", db_path=fixture_db)
    assert r.error.startswith("rejected")


def test_connection_is_read_only(fixture_db):
    import duckdb
    con = duckdb.connect(str(fixture_db), read_only=True)
    with pytest.raises(duckdb.Error):
        con.execute("DELETE FROM orders")
    con.close()
