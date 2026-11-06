"""Run the evaluation: scenarios x configurations x runs. Resumable via the runs CSV.

    python -m eval.run_eval --configs A B C --scenarios all --runs 1
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import platform
import subprocess
import time
import traceback
from datetime import datetime
from pathlib import Path

from config import DB_PATH, EVAL_DATA_DIR, KPI_MODEL, REPORTS_DIR, RESULTS_DIR
from eval.inject import build_scenario_db, load_scenarios
from eval.score import score_report
from src.pipeline import run
from src.prompts import PROMPT_VERSION
from src.report import save_report

CONFIG_MODES = {"A": "baseline", "B": "agent", "C": "agent_verify"}
CONFIG_NAMES = {"A": "Baseline (LLM only)", "B": "Agent",
                "C": "Agent + verifier revision"}
RUNS_CSV = RESULTS_DIR / "eval_runs.csv"
SUMMARY_JSON = RESULTS_DIR / "eval_summary.json"
SUMMARY_MD = RESULTS_DIR / "eval_summary.md"
FIELDS = ["run_id", "scenario", "config", "run", "hit1", "hit3", "unsupported_numbers",
          "total_numbers", "unsupported_rate", "unsupported_before_revision",
          "total_before_revision", "revised", "n_steps", "llm_calls", "elapsed_s",
          "top_dimension", "top_segment", "n_findings", "target_flagged", "error",
          "model", "prompt_version", "timestamp"]

log = logging.getLogger("eval")


def read_runs(path: Path = RUNS_CSV) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def append_run(row: dict, path: Path = RUNS_CSV) -> None:
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in FIELDS})


def ensure_db(scenario: dict, injections: dict) -> Path:
    path = EVAL_DATA_DIR / f"{scenario['id']}.duckdb"
    if not path.exists():
        injections[scenario["id"]] = build_scenario_db(scenario, DB_PATH)
    return path


def run_one(scenario: dict, config: str, run_no: int, flags: dict) -> dict:
    run_id = f"{scenario['id']}_{config}_r{run_no}"
    row = {"run_id": run_id, "scenario": scenario["id"], "config": config, "run": run_no,
           "model": KPI_MODEL, "prompt_version": PROMPT_VERSION,
           "timestamp": datetime.now().isoformat(timespec="seconds"),
           "target_flagged": json.dumps(flags)}
    start = time.perf_counter()
    try:
        res = run(EVAL_DATA_DIR / f"{scenario['id']}.duckdb", scenario["month"],
                  scenario["question"], CONFIG_MODES[config], run_id=run_id)
        save_report(res, REPORTS_DIR / "eval")
        ver, before = res["verification"], res.get("verification_before_revision")
        top = (res["report"]["findings"] or [{}])[0]
        row.update(score_report(res["report"], scenario))
        row.update(unsupported_numbers=ver["unsupported_numbers"],
                   total_numbers=ver["total_numbers"], unsupported_rate=ver["unsupported_rate"],
                   unsupported_before_revision=(before or ver)["unsupported_numbers"],
                   total_before_revision=(before or ver)["total_numbers"],
                   revised=res["revised"], n_steps=res["n_steps"], llm_calls=res["llm_calls"],
                   elapsed_s=res["elapsed_s"], top_dimension=top.get("dimension", ""),
                   top_segment=top.get("segment", ""),
                   n_findings=len(res["report"]["findings"]))
    except Exception as e:  # a failed run is scored as a miss, never dropped
        log.error("run %s failed: %s", run_id, traceback.format_exc())
        row.update(hit1=0.0, hit3=0.0, error=f"{type(e).__name__}: {str(e)[:200]}",
                   elapsed_s=round(time.perf_counter() - start, 2), unsupported_numbers=0,
                   total_numbers=0, n_steps=0)
    return row


def _f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def summarize(rows: list[dict], scenarios: list[dict]) -> dict:
    """Aggregate per-config metrics from run rows."""
    n_scen = len(scenarios)
    configs = {}
    for c in sorted({r["config"] for r in rows}):
        rs = [r for r in rows if r["config"] == c]
        runs = max(int(r["run"]) for r in rs)
        tot = sum(_f(r["total_numbers"]) for r in rs)
        uns = sum(_f(r["unsupported_numbers"]) for r in rs)
        tot_b = sum(_f(r["total_before_revision"] or r["total_numbers"]) for r in rs)
        uns_b = sum(_f(r["unsupported_before_revision"] or r["unsupported_numbers"]) for r in rs)
        configs[c] = {
            "name": CONFIG_NAMES[c], "n_runs": len(rs), "runs_per_scenario": runs,
            "hit1": round(sum(_f(r["hit1"]) for r in rs) / runs, 2),
            "hit3": round(sum(_f(r["hit3"]) for r in rs) / runs, 2),
            "hit1_rate": round(sum(_f(r["hit1"]) for r in rs) / len(rs), 3),
            "hit3_rate": round(sum(_f(r["hit3"]) for r in rs) / len(rs), 3),
            "unsupported_rate": round(uns / tot, 3) if tot else None,
            "unsupported_numbers": int(uns), "total_numbers": int(tot),
            "unsupported_rate_before_revision": round(uns_b / tot_b, 3) if tot_b else None,
            "mean_steps": round(sum(_f(r["n_steps"]) for r in rs) / len(rs), 1),
            "mean_time_s": round(sum(_f(r["elapsed_s"]) for r in rs) / len(rs), 1),
            "errors": sum(bool(r.get("error")) for r in rs),
            "revised_runs": sum(str(r.get("revised")) == "True" for r in rs),
        }
    per_scenario = {}
    for s in scenarios:
        per_scenario[s["id"]] = {r["config"]: {"hit1": _f(r["hit1"]), "hit3": _f(r["hit3"]),
                                               "top": f"{r['top_dimension']}={r['top_segment']}"}
                                 for r in rows if r["scenario"] == s["id"]}
    return {"n_scenarios": n_scen, "model": KPI_MODEL, "prompt_version": PROMPT_VERSION,
            "hardware": hardware(), "generated": datetime.now().isoformat(timespec="seconds"),
            "configs": configs, "per_scenario": per_scenario}


def hardware() -> str:
    try:
        cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True,
                             text=True).stdout.strip()
        mem = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True,
                                 text=True).stdout.strip()) / 2**30
        return f"{cpu}, {mem:.0f} GB RAM, macOS {platform.mac_ver()[0]}"
    except Exception:
        return platform.platform()


def summary_markdown(summary: dict) -> str:
    n = summary["n_scenarios"]
    lines = ["# Evaluation summary", "",
             f"Model `{summary['model']}`, prompt {summary['prompt_version']}, "
             f"{summary['hardware']}. Generated {summary['generated']}.", "",
             "| Config | Root cause hit@1 | Root cause hit@3 | Unsupported claim rate | "
             "Mean steps | Mean time per run (s) | Errors |", "|---|---|---|---|---|---|---|"]
    for c, m in summary["configs"].items():
        ur = "n/a" if m["unsupported_rate"] is None else f"{m['unsupported_rate']:.1%}"
        lines.append(f"| {c}. {m['name']} | {m['hit1']:g}/{n} | {m['hit3']:g}/{n} | {ur} "
                     f"({m['unsupported_numbers']}/{m['total_numbers']}) | {m['mean_steps']} | "
                     f"{m['mean_time_s']} | {m['errors']} |")
    lines += ["", "## Per scenario (hit@1 / hit@3, top finding)", "",
              "| Scenario | " + " | ".join(summary["configs"]) + " |",
              "|---|" + "---|" * len(summary["configs"])]
    for sid, by in summary["per_scenario"].items():
        cells = [f"{by[c]['hit1']:g} / {by[c]['hit3']:g} ({by[c]['top']})" if c in by else ""
                 for c in summary["configs"]]
        lines.append(f"| {sid} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_summary(scenarios: list[dict]) -> dict:
    summary = summarize(read_runs(), scenarios)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=1))
    SUMMARY_MD.write_text(summary_markdown(summary))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configs", nargs="+", default=["A", "B", "C"])
    parser.add_argument("--scenarios", nargs="+", default=["all"])
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    scenarios = load_scenarios()
    if args.scenarios != ["all"]:
        scenarios = [s for s in scenarios if s["id"] in args.scenarios
                     or s["id"].split("_")[0] in args.scenarios]
    injections_path = RESULTS_DIR / "eval_injections.json"
    injections = {r["id"]: r for r in json.loads(injections_path.read_text())} \
        if injections_path.exists() else {}
    done = {r["run_id"] for r in read_runs()}
    todo = [(s, c, k) for k in range(1, args.runs + 1) for s in scenarios for c in args.configs
            if f"{s['id']}_{c}_r{k}" not in done]
    log.info("%d runs to do (%d already done)", len(todo), len(done))
    t0, finished = time.perf_counter(), 0
    for s, c, k in todo:
        ensure_db(s, injections)
        flags = injections.get(s["id"], {}).get("target_flagged", {})
        row = run_one(s, c, k, flags)
        append_run(row)
        finished += 1
        log.info("done %s hit1=%s hit3=%s unsupported=%s/%s %.0fs", row["run_id"],
                 row["hit1"], row["hit3"], row.get("unsupported_numbers"),
                 row.get("total_numbers"), _f(row.get("elapsed_s")))
        if finished >= 3:
            per = (time.perf_counter() - t0) / finished
            log.info("ETA: %.0f min remaining (%d runs)", per * (len(todo) - finished) / 60,
                     len(todo) - finished)
        write_summary(load_scenarios())
    injections_path.write_text(json.dumps(list(injections.values()), indent=1))
    write_summary(load_scenarios())


if __name__ == "__main__":
    main()
