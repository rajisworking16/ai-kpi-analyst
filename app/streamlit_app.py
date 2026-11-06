"""Streamlit app: KPI trends, detection, decomposition, agent trace and verified report.

Run with: streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import DB_PATH, EVAL_DATA_DIR, RESULTS_DIR, TRACES_DIR  # noqa: E402
from src.context import build_context  # noqa: E402
from src.detect import shift_month  # noqa: E402
from src.kpis import DIMENSIONS, KPI_DEFINITIONS, WINDOW_END, WINDOW_START  # noqa: E402

SERIES = "#2a78d6"
HIGHLIGHT = "#eb6834"
BADGE = {"verified": ("🟢", "verified"), "partially_verified": ("🟡", "partially verified"),
         "unsupported": ("🔴", "unsupported")}
PRESET_QUESTIONS = [
    "Why did revenue change?", "Why did revenue drop?", "Why did AOV rise?",
    "Why did AOV fall?", "Why did late deliveries rise?", "Why did review scores fall?",
    "Why did the freight ratio rise?", "Why did orders rise?", "What changed in payments?",
    "Why did cancellations rise?", "Why did revenue drop and late deliveries rise?",
]
MODES = {"Agent + verifier": "agent_verify", "Agent": "agent", "Baseline (LLM only)": "baseline"}


def months() -> list[str]:
    out, m = [], WINDOW_START
    while m <= WINDOW_END:
        out.append(m)
        m = shift_month(m, 1)
    return out


def databases() -> dict[str, Path]:
    dbs = {"Real data (olist.duckdb)": DB_PATH}
    for p in sorted(EVAL_DATA_DIR.glob("*.duckdb")):
        dbs[f"Eval scenario: {p.stem}"] = p
    return dbs


@st.cache_data(show_spinner=False)
def cached_context(db: str, month: str, question: str):
    ctx = build_context(db, month, question)
    return {"focus": ctx.focus_kpis, "kpi_table": ctx.kpi_table,
            "detection": pd.DataFrame([c.to_dict() for c in ctx.detection]),
            "split": ctx.decomposition["revenue_split"],
            "segments": ctx.decomposition["segments"]}


def trend_chart(table: pd.DataFrame, kpi: str, month: str) -> go.Figure:
    start = shift_month(month, -11)
    t = table[(table["period"] >= start) & (table["period"] <= month)]
    label = KPI_DEFINITIONS[kpi]["label"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t["period"], y=t[kpi], mode="lines+markers", name=label,
                             line={"color": SERIES, "width": 2}, marker={"size": 8},
                             hovertemplate="%{x}: %{y:,.4g}<extra></extra>"))
    cur = t[t["period"] == month]
    fig.add_trace(go.Scatter(x=cur["period"], y=cur[kpi], mode="markers+text",
                             name="Target month", text=[f"{month}"], textposition="top center",
                             marker={"color": HIGHLIGHT, "size": 13,
                                     "line": {"color": "white", "width": 2}},
                             hovertemplate="%{x}: %{y:,.4g}<extra>target</extra>"))
    fig.update_layout(title=f"{label}, last 12 months", height=330, showlegend=False,
                      margin={"l": 10, "r": 10, "t": 50, "b": 10}, hovermode="x unified",
                      yaxis={"gridcolor": "rgba(128,128,128,0.2)"},
                      xaxis={"showgrid": False})
    return fig


def show_detection(det: pd.DataFrame) -> None:
    d = det[["kpi", "previous", "current", "pct_change", "z_score", "significant"]].copy()
    st.dataframe(d, hide_index=True, width="stretch",
                 column_config={"pct_change": st.column_config.NumberColumn(format="percent"),
                                "z_score": st.column_config.NumberColumn(format="%.2f")})


def show_decomposition(ctxd: dict) -> None:
    s = ctxd["split"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue change", f"{s['total_change']:,.0f}")
    c2.metric("Volume effect", f"{s['volume_effect']:,.0f}")
    c3.metric("AOV effect", f"{s['aov_effect']:,.0f}")
    c4.metric("Interaction", f"{s['interaction']:,.0f}")
    for kpi in ctxd["focus"]:
        st.markdown(f"**{KPI_DEFINITIONS[kpi]['label']}: top segments by contribution**")
        tabs = st.tabs(DIMENSIONS)
        for tab, dim in zip(tabs, DIMENSIONS, strict=True):
            with tab:
                st.dataframe(ctxd["segments"][kpi][dim], hide_index=True, width="stretch")


def show_trace(run: dict) -> None:
    queries = {q["query_id"]: q for q in run.get("queries", [])}
    if not run.get("hypotheses"):
        st.info("Baseline mode: no hypotheses or SQL, the model only saw the monthly KPI table.")
        return
    for h in run["hypotheses"]:
        icon = {"supported": "✅", "rejected": "❌", "inconclusive": "❔"}.get(h["status"], "⏳")
        with st.expander(f"{icon} {h['id']} [{h['status']}]: {h['statement']}"):
            st.caption(f"Dimension {h.get('dimension')} = {h.get('segment')}. "
                       f"Test: {h.get('test')}")
            for q in [q for q in queries.values() if q.get("hypothesis_id") == h["id"]]:
                st.markdown(f"`{q['query_id']}`" + (f" error: {q['error']}" if q["error"]
                                                     else f", {q['row_count']} rows"))
                st.code(q["sql"].strip(), language="sql")
                if q["rows"]:
                    st.dataframe(pd.DataFrame(q["rows"]), hide_index=True, width="stretch")


def show_report(run: dict) -> None:
    rep, ver = run["report"], run["verification"]
    labels = {f["index"]: f["label"] for f in ver["findings"]}
    rate = ver["unsupported_rate"]
    st.markdown(f"**Summary.** {rep['summary']}")
    st.caption(f"Unsupported claim rate: {'n/a' if rate is None else f'{rate:.1%}'} "
               f"({ver['unsupported_numbers']}/{ver['total_numbers']} numbers). "
               f"Revised by verifier: {run['revised']}. Steps: {run['n_steps']}, "
               f"time {run['elapsed_s']:.0f}s.")
    for i, f in enumerate(rep["findings"]):
        icon, text = BADGE.get(labels.get(i, ""), ("⚪", "not checked"))
        with st.container(border=True):
            st.markdown(f"{icon} **{text}** · `{f['dimension']} = {f['segment']}` · "
                        f"KPI `{f['kpi']}` · confidence {f['confidence']}")
            st.markdown(f"{i + 1}. {f['claim']}")
            checks = ver["findings"][i]["numbers"] if i < len(ver["findings"]) else []
            for n in checks:
                where = f", in {n['matched_in']}" if n["matched_in"] else ""
                mark = "✔" if n["supported"] else "✘"
                st.markdown(f"- {mark} `{n['text']}` ({n['source']}{where})")
            if f["evidence_query_ids"]:
                st.caption("Evidence: " + ", ".join(f["evidence_query_ids"]))
    st.subheader("Investigate next")
    for item in rep["investigate_next"]:
        st.markdown(f"- **{item['item']}**: {item['why']} _(data needed: {item['data_needed']})_")


def analyze_page() -> None:
    st.title("AI KPI Analyst")
    st.caption("Deterministic detection and decomposition first; a local LLM proposes and "
               "tests hypotheses with read-only SQL; a verifier checks every number.")
    dbs = databases()
    with st.sidebar:
        db_label = st.selectbox("Database", list(dbs))
        ms = months()
        default_month = st.query_params.get("month", "2018-05")
        month = st.selectbox("Month", ms, index=ms.index(default_month)
                             if default_month in ms else 0)
        preset = st.selectbox("Question", [*PRESET_QUESTIONS, "Custom..."])
        question = st.text_input("Your question") if preset == "Custom..." else preset
        mode_label = st.radio("Mode", list(MODES))
        run_clicked = st.button("Run analysis", type="primary", width="stretch")
        saved = sorted(p.stem for p in TRACES_DIR.glob("*.json")) if TRACES_DIR.exists() else []
        qrun = st.query_params.get("run")
        options = ["(none)", *saved]
        load = st.selectbox("Or load a saved run", options,
                            index=options.index(qrun) if qrun in options else 0)
    db = str(dbs[db_label])
    ctxd = cached_context(db, month, question or "Why did revenue change?")
    kpi = st.selectbox("Trend KPI", list(KPI_DEFINITIONS), index=list(KPI_DEFINITIONS).index(
        ctxd["focus"][0]), format_func=lambda k: KPI_DEFINITIONS[k]["label"])
    st.plotly_chart(trend_chart(ctxd["kpi_table"], kpi, month), width="stretch")
    st.subheader(f"1. Detection: {month} vs {shift_month(month, -1)}")
    show_detection(ctxd["detection"])
    st.subheader("2. Decomposition")
    show_decomposition(ctxd)
    if run_clicked:
        from src.pipeline import run
        with st.spinner("Running the local model (this takes 1 to 4 minutes)..."):
            st.session_state["run"] = run(db, month, question, MODES[mode_label])
    elif load != "(none)":
        st.session_state["run"] = json.loads((TRACES_DIR / f"{load}.json").read_text())
    result = st.session_state.get("run")
    st.subheader("3. Agent trace")
    if result is None:
        st.info("Click **Run analysis** (needs Ollama running) or load a saved run.")
        return
    st.caption(f"Run `{result['run_id']}`: {result['question']} ({result['mode']})")
    show_trace(result)
    st.subheader("4. Report")
    show_report(result)


def results_page() -> None:
    st.title("Evaluation results")
    summary_md, summary_json = RESULTS_DIR / "eval_summary.md", RESULTS_DIR / "eval_summary.json"
    if not summary_json.exists():
        st.info("No evaluation results yet. Run `python -m eval.run_eval`.")
        return
    s = json.loads(summary_json.read_text())
    cfg = s["configs"]
    names = [f"{c}. {m['name']}" for c, m in cfg.items()]
    vals = [m["hit1"] for m in cfg.values()]
    fig = go.Figure(go.Bar(x=names, y=vals, marker={"color": SERIES, "cornerradius": 4},
                           text=[f"{v:g}/{s['n_scenarios']}" for v in vals],
                           textposition="outside",
                           hovertemplate="%{x}: %{y:g} hits<extra></extra>"))
    fig.update_layout(title="Root cause hit@1 by configuration", height=350,
                      yaxis={"range": [0, s["n_scenarios"]], "gridcolor": "rgba(128,128,128,0.2)",
                             "title": "scenarios"},
                      margin={"l": 10, "r": 10, "t": 50, "b": 10})
    st.plotly_chart(fig, width="stretch")
    st.markdown(summary_md.read_text())


st.set_page_config(page_title="AI KPI Analyst", layout="wide")
pages = ["Analyze", "Results"]
page = st.sidebar.radio("Page", pages, index=1 if st.query_params.get("page") == "results" else 0)
st.sidebar.divider()
if page == "Analyze":
    analyze_page()
else:
    results_page()
