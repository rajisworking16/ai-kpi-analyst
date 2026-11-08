"""Read-only SQL execution for the agent: parse, validate, limit, time out, trace."""

from __future__ import annotations

import datetime as dt
import decimal
import hashlib
import math
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import duckdb
import sqlglot
from sqlglot import exp

from config import DB_PATH, SQL_MAX_ROWS, SQL_TIMEOUT_S

BLOCKED_KEYWORDS = re.compile(
    r"\b(ATTACH|DETACH|COPY|INSTALL|LOAD|PRAGMA|EXPORT|IMPORT|CALL|CHECKPOINT|"
    r"INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|SET|RESET|USE|VACUUM)\b",
    re.IGNORECASE,
)
BLOCKED_FUNCTIONS = {
    "read_csv", "read_csv_auto", "read_parquet", "read_json", "read_json_auto",
    "read_json_objects", "read_ndjson", "read_ndjson_auto", "read_ndjson_objects",
    "read_text", "read_blob", "read_xlsx", "parquet_scan", "parquet_metadata",
    "parquet_schema", "csv_scan", "json_scan", "sniff_csv", "glob", "iceberg_scan",
    "delta_scan", "sqlite_scan", "postgres_scan", "mysql_scan", "query", "query_table",
    "getenv", "httpfs", "duckdb_secrets", "duckdb_settings", "duckdb_extensions",
}
BLOCKED_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter, exp.Command,
    exp.Copy, exp.Pragma, exp.Set, exp.Use, exp.Merge, exp.TruncateTable,
)


class SQLGuardError(ValueError):
    """Raised when a query is not allowed."""


@dataclass
class QueryResult:
    query_id: str
    sql: str
    executed_sql: str
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    row_count: int = 0
    error: str | None = None
    elapsed_s: float = 0.0
    hypothesis_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunTrace:
    """Every query and its result for one run, keyed by query_id."""

    queries: dict[str, QueryResult] = field(default_factory=dict)

    def add(self, result: QueryResult) -> None:
        self.queries[result.query_id] = result


def query_id_for(sql: str) -> str:
    """Short stable id for a query string."""
    return "q_" + hashlib.sha1(sql.strip().encode()).hexdigest()[:6]


def _function_names(tree: exp.Expression) -> set[str]:
    names = set()
    for node in tree.find_all(exp.Func):
        name = node.name if isinstance(node, exp.Anonymous) else node.sql_name()
        names.add(str(name).lower())
    for node in tree.find_all(exp.Table):
        if isinstance(node.this, exp.Anonymous):
            names.add(node.this.name.lower())
    return names


def validate(sql: str, max_rows: int = SQL_MAX_ROWS) -> str:
    """Validate `sql` as a single read-only SELECT/WITH and return it with a LIMIT enforced."""
    if not sql or not sql.strip():
        raise SQLGuardError("empty query")
    if BLOCKED_KEYWORDS.search(re.sub(r"'[^']*'", "''", sql)):
        raise SQLGuardError("query contains a blocked keyword; only SELECT/WITH is allowed")
    try:
        statements = [s for s in sqlglot.parse(sql, read="duckdb") if s is not None]
    except sqlglot.errors.ParseError as e:
        raise SQLGuardError(f"could not parse SQL: {str(e).splitlines()[0]}") from e
    if len(statements) != 1:
        raise SQLGuardError("exactly one statement is allowed")
    tree = statements[0]
    if not isinstance(tree, exp.Select | exp.SetOperation):
        raise SQLGuardError("only SELECT or WITH ... SELECT queries are allowed")
    if any(tree.find_all(*BLOCKED_NODES)):
        raise SQLGuardError("query contains a write or system statement")
    bad = _function_names(tree) & BLOCKED_FUNCTIONS
    if bad:
        raise SQLGuardError(f"blocked function(s): {sorted(bad)}")
    for table in tree.find_all(exp.Table):
        if table.this is not None and isinstance(table.this, exp.Identifier) and (
            table.this.quoted and re.search(r"[./\\]", table.name)
        ):
            raise SQLGuardError("reading files is not allowed")
    limit = tree.args.get("limit")
    current = None
    if limit is not None and isinstance(limit.expression, exp.Literal):
        try:
            current = int(limit.expression.this)
        except ValueError:
            current = None
    if current is None or current > max_rows:
        tree = tree.limit(max_rows)
    return tree.sql(dialect="duckdb")


def _jsonable(v):
    if isinstance(v, float):
        return None if not math.isfinite(v) else v
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, dt.datetime | dt.date | dt.time | dt.timedelta):
        return str(v)
    if hasattr(v, "item"):
        return v.item()
    return v


def run_readonly(
    query: str,
    max_rows: int = SQL_MAX_ROWS,
    timeout_s: float = SQL_TIMEOUT_S,
    db_path: Path | str = DB_PATH,
    trace: RunTrace | None = None,
    hypothesis_id: str | None = None,
) -> QueryResult:
    """Validate and run a read-only query. Errors are returned in the result, not raised."""
    qid = query_id_for(query)
    result = QueryResult(query_id=qid, sql=query, executed_sql="", hypothesis_id=hypothesis_id)
    start = time.perf_counter()
    try:
        result.executed_sql = validate(query, max_rows)
        con = duckdb.connect(str(db_path), read_only=True,
                             config={"enable_external_access": False})
        timer = threading.Timer(timeout_s, con.interrupt)
        timer.start()
        try:
            cur = con.execute(result.executed_sql)
            result.columns = [d[0] for d in cur.description]
            rows = cur.fetchmany(max_rows)
        finally:
            timer.cancel()
            con.close()
        result.rows = [{c: _jsonable(v) for c, v in zip(result.columns, r, strict=True)}
                       for r in rows]
        result.row_count = len(result.rows)
    except SQLGuardError as e:
        result.error = f"rejected: {e}"
    except duckdb.InterruptException:
        result.error = f"timeout: query exceeded {timeout_s}s"
    except duckdb.Error as e:
        result.error = f"sql error: {str(e).splitlines()[0][:300]}"
    result.elapsed_s = round(time.perf_counter() - start, 3)
    if trace is not None:
        trace.add(result)
    return result
