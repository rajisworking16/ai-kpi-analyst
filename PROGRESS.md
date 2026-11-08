**BLOCKER (needs Pranav):** creating the public GitHub repo was blocked by Claude Code's permission settings (public publish needs your OK). Run this once from the repo folder:

    cd ~/projects/ai-kpi-analyst && gh repo create rajisworking16/ai-kpi-analyst --public --source=. --push

Everything else is committed locally on `main`.

# Progress

Resume from here. Build order is Section 10 of PROJECT_SPEC.md. Venv: `.venv/bin/python`.

## Done
- Step 1: environment (uv, Python 3.12 venv, Ollama 0.40.15 + qwen2.5:7b, repo-local git identity with noreply email), scaffold
- Step 2: data download (anonymous kagglehub), DuckDB load, KPI definitions + tests
- Step 3: detect.py, decompose.py + tests
- Step 4: sql_guard.py + tests
- Step 5: llm.py, schemas.py, prompts.py, context.py, agent.py, baseline.py, pipeline.py, cli.py; example run saved (results/reports/example_2018-03_revenue.md)
- Step 6: verify.py + tests, revision mode, report.py
- Step 7: eval/inject.py, scenarios.yaml (generated), score.py, run_eval.py + tests; eval DBs built in data/eval/
- Step 8: Streamlit app, screenshots (scripts/screenshots.py)

## In progress
- Smoke eval (s01, s04 x A/B/C) -> results/eval_runs.csv
- Step 9: README drafted with [TBD], docs/architecture.md, scripts/check_repo.py, scripts/check_readme.py written

## Next
- Step 10: quality gates, `gh repo create rajisworking16/ai-kpi-analyst --public --source=. --push`
- Step 11: full eval in background with caffeinate (resumable: rerun same command)
- Step 12: fill README results/limitations from results/eval_summary.json, check_readme, push
- Step 13: private files in ~/projects/ai-kpi-analyst-private/

## Notes
- Rebuild DB: `.venv/bin/python -m src.data_load`; eval DBs: `.venv/bin/python -m eval.inject --all`
- Mac sleep pauses runs; always wrap long runs in `caffeinate -i`.
