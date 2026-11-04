# AI KPI Analyst: Project Spec for Claude Code (fully autonomous build)

**Owner:** Sai Pranav Raj Kandula (GitHub: `rajisworking16`)
**Repo name:** `ai-kpi-analyst`
**Mode:** Pranav has done the one-time setup (Homebrew, GitHub CLI login) and won't touch anything else. You do everything: install tools, download data, build, test, run evals, write the README, push, and fill in the resume points.

---

## 0. Instructions to Claude Code (read all of this first)

### 0.1 How to work
1. **Work autonomously. Don't ask Pranav questions.** When a choice comes up, make the most reasonable call, record it in `docs/DECISIONS.md` (one line: decision + reason), and keep going.
2. **Only stop for a true blocker**: something that needs Pranav's password, a browser login, or a paid service. If that happens, write the blocker at the top of `PROGRESS.md` in plain language, and finish every other step that doesn't depend on it.
3. **Keep `PROGRESS.md` updated** after every milestone: which steps are done, what's in progress, and what's next. If this session ends (usage limits, crash, Mac sleeping), a new session must be able to continue from `PROGRESS.md` alone.
4. Follow the build order in Section 10. Commit after each milestone. Don't move to the next step while tests for the current one are failing.
5. Stay inside `~/projects/ai-kpi-analyst/` and `~/projects/ai-kpi-analyst-private/`. The only system-level changes allowed are the Homebrew installs listed in Section 0.3 and `ollama pull`.

### 0.2 Hard constraints
1. **Zero cost.** No paid APIs, no API keys, no cloud LLMs, no paid hosting. The only LLM is a local model served by **Ollama**. Every library must be free and open source.
2. **Data never goes in Git.** Raw and processed data live in `data/`, which is gitignored.
3. **No made-up numbers anywhere.** The README results, `results/` files and resume points come only from what the code actually computed. If something hasn't been produced, write `[TBD]`. Never estimate or round in a way that changes the meaning.
4. **Deterministic first, LLM second.** All KPI math, change detection and decomposition are plain Python/SQL. The LLM only proposes hypotheses, writes SQL to test them, and writes the narrative.
5. **Read-only SQL.** The agent can only run `SELECT` / `WITH` queries against a read-only DuckDB connection, with a row limit and a timeout.
6. **No secrets in the repo.** No tokens, no `.env`, no personal email in commits (see 0.3).
7. Keep code readable: type hints, short functions, docstrings on public functions. No notebooks in the main pipeline.

### 0.3 Environment setup (you do all of this)
Run these checks in order, and fix what's missing:

| Check | If missing |
|---|---|
| `brew --version` | Blocker: Pranav must install Homebrew (it needs his password). Log it and stop. |
| `gh auth status` succeeds | Blocker: Pranav must run `gh auth login`. Log it, then build everything locally and push once auth exists. |
| Python ≥ 3.10 | `brew install uv`, then `uv python install 3.12`. Use `uv venv` and `uv pip` for the project environment. |
| `ollama --version` | `brew install ollama`, then `brew services start ollama`. Wait until `curl -s localhost:11434` responds. |
| Model pulled | Read RAM with `sysctl -n hw.memsize`. If it's 16 GB or more, `ollama pull qwen2.5:7b`. Otherwise `ollama pull qwen2.5:3b`. Save the choice in `.env.example` and `config.py` as `KPI_MODEL`, and log it in `docs/DECISIONS.md`. |
| Model works | Run `ollama run <model> "Reply with the word OK"` and confirm it responds. |
| Git identity | If `git config user.name` is empty, set it locally (repo only) to `Sai Pranav Raj Kandula`. Set `user.email` to the GitHub noreply address: get the id and login with `gh api user --jq '.id,.login'` and use `<id>+<login>@users.noreply.github.com`. |

### 0.4 Quality gates (must all pass before the final push)
- `pytest` passes with 0 failures.
- `ruff check .` passes (add `ruff` to dev requirements).
- **End-to-end smoke test:** `python -m src.cli --month 2018-03 --question "Why did revenue change?"` runs the full pipeline on real data and writes a report.
- **Repo hygiene check (`scripts/check_repo.py`):** fails if any tracked file is a `.csv`, `.duckdb`, `.parquet` or `.env`, if any tracked file is over 5 MB, or if anything that looks like a token or key is found.
- **README consistency check (`scripts/check_readme.py`):** every number in the README results table must equal the matching value in `results/eval_summary.json`. It fails on any mismatch.
- The app starts: `streamlit run app/streamlit_app.py --server.headless true` boots without errors (start it, check the health endpoint, then stop it).

---

## 1. What the project does

A user asks a business question such as *"Why did revenue drop in March 2018?"* The system:

1. **Detects** which KPIs moved significantly in that period (deterministic).
2. **Decomposes** the change by category, customer state, seller and payment type, and splits revenue change into volume and order-value effects (deterministic).
3. **Hypothesizes** 3 to 5 possible causes (LLM).
4. **Investigates** each hypothesis by writing and running read-only SQL, then keeps or rejects it based on the result (LLM agent loop).
5. **Verifies** every number and claim in the final write-up against the actual query results, and flags anything unsupported (deterministic).
6. **Reports** a short explanation, the evidence behind each finding, and a ranked list of what a human analyst should investigate next.

An **evaluation harness** plants known anomalies in a copy of the data and measures how often the system finds the true cause, compared with an LLM-only baseline.

---

## 2. Data (automated download)

**Dataset:** Brazilian E-Commerce Public Dataset by Olist, Kaggle handle `olistbr/brazilian-ecommerce`.

**`scripts/download_data.py`** does the following:
1. Try `kagglehub.dataset_download("olistbr/brazilian-ecommerce")` without credentials. kagglehub only needs authentication for private datasets or ones that require user consent, so this public dataset should download anonymously.
2. Copy the CSVs into `data/raw/`.
3. If the anonymous download fails with an auth error, check for `~/.kaggle/kaggle.json` or `KAGGLE_USERNAME`/`KAGGLE_KEY` and retry. If neither exists, log it as a blocker in `PROGRESS.md` ("Pranav: create a free Kaggle API token at kaggle.com/settings and save it to ~/.kaggle/kaggle.json") and stop the data-dependent steps.
4. Validate: all files below exist, each has more than 0 rows, and the orders file has the expected columns. Print row counts.

Expected files:
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_products_dataset.csv`
- `product_category_name_translation.csv`
- (`olist_geolocation_dataset.csv` is not needed and can be skipped)

**Analysis window:** 2017-01 through 2018-08. The months before and after are sparse. Print monthly order counts during the build to confirm this, adjust the window if the data says otherwise, and log the final window in `docs/DECISIONS.md`.

**Licence:** read the licence on the Kaggle dataset page (via the kagglehub metadata or the downloaded files). Credit Olist in the README and follow the licence terms.

---

## 3. KPI definitions

Build these in `src/kpis.py` as DuckDB SQL over a cleaned `orders_enriched` view (one row per order item, joined to orders, customers, sellers, products with English category names, and the order's average review score).

| KPI | Definition |
|---|---|
| Revenue | Sum of `price` for items in orders with status `delivered` |
| Orders | Count of distinct delivered `order_id` |
| AOV | Revenue / Orders |
| Freight ratio | Sum of `freight_value` / Revenue |
| Avg delivery days | Mean of (`order_delivered_customer_date` minus `order_purchase_timestamp`) in days |
| Late delivery rate | Share of delivered orders where delivered date is after `order_estimated_delivery_date` |
| Avg review score | Mean review score per order, averaged over orders |
| Cancellation rate | Canceled orders / all orders placed in the period |

Grain: monthly, with optional weekly. Store definitions in a single dict so the README and the LLM prompt both read from the same source. Handle nulls explicitly (orders with missing delivery dates are excluded from delivery KPIs, and the count excluded is logged).

---

## 4. Pipeline modules

### 4.1 `src/data_load.py`
- Load CSVs into a DuckDB file at `data/processed/olist.duckdb`.
- Parse timestamps, translate categories to English (keep the Portuguese name too), build the `orders_enriched` view.
- `build_database(raw_dir, db_path)` is idempotent.

### 4.2 `src/detect.py`
- For a target month, compare each KPI with (a) the previous month and (b) the trailing 6-month mean and standard deviation.
- Flag a KPI as significant if the absolute z-score is ≥ 2 **or** the month-over-month change is ≥ 15%. Both thresholds go in `config.py`.
- Returns a list of `KPIChange` dataclasses: kpi, current, previous, pct_change, z_score, direction.

### 4.3 `src/decompose.py`
- **Volume vs AOV split for revenue:**
  - volume effect = (Orders₁ − Orders₀) × AOV₀
  - AOV effect = (AOV₁ − AOV₀) × Orders₀
  - interaction = (Orders₁ − Orders₀) × (AOV₁ − AOV₀)
  - The three must sum to total revenue change (assert this in tests).
- **Segment contribution:** for each dimension (category, customer_state, seller_id, payment_type), compute each segment's change in the KPI and its share of the total change. Return the top 10 segments by absolute contribution per dimension.
- For rate KPIs (late rate, review score), report each segment's rate change and its volume weight, so mix shifts aren't mistaken for rate changes.

### 4.4 `src/sql_guard.py`
- `run_readonly(query, max_rows=200, timeout_s=10)`:
  - Reject anything that isn't a single `SELECT` or `WITH` statement (parse with `sqlglot`). Also reject `ATTACH`, `COPY`, `INSTALL`, `LOAD`, `PRAGMA`, file-reading functions (`read_csv`, `read_parquet` and similar) and multi-statement input.
  - Open DuckDB with `read_only=True`.
  - Enforce a `LIMIT`.
  - Return rows as a list of dicts plus a `query_id` (short hash). Log every query and result to the run trace.

### 4.5 `src/llm.py` and `src/agent.py`
`llm.py` is a thin Ollama wrapper: `chat_json(messages, schema) -> dict`. It uses Ollama **structured outputs** (pass the JSON schema to `format`), validates with Pydantic, and retries once on invalid JSON. Don't depend on native tool calling, because small local models handle it unreliably.

Each agent step, the model returns JSON in one of these shapes:

```json
{"action": "run_sql", "hypothesis_id": "H2", "reason": "...", "sql": "SELECT ..."}
{"action": "update_hypothesis", "hypothesis_id": "H2", "status": "supported|rejected|inconclusive", "evidence_query_ids": ["q_ab12"]}
{"action": "final_report", "report": { ...see schema below... }}
```

Loop rules:
- Start by giving the model: the question, KPI definitions, the schema of `orders_enriched`, the detection output and the decomposition tables.
- First step: the model must return 3 to 5 hypotheses (id, statement, how to test it).
- Max 12 steps (configurable). If a SQL query errors, return the error message to the model once. After 2 consecutive errors on one hypothesis, mark it inconclusive.
- If the step limit is hit, force a `final_report` from what's been gathered.
- Temperature 0. Set a seed if the Ollama version supports it.

**Final report schema:**
```json
{
  "summary": "2 to 4 sentences",
  "findings": [
    {"claim": "...", "kpi": "...", "dimension": "...", "segment": "...",
     "numbers": [{"value": 0.0, "meaning": "..."}],
     "evidence_query_ids": ["q_..."], "confidence": "high|medium|low"}
  ],
  "investigate_next": [{"item": "...", "why": "...", "data_needed": "..."}]
}
```

### 4.6 `src/verify.py`
For each finding:
- Every `evidence_query_id` must exist in the run trace.
- Every number in `numbers` must match a value in the cited query results, the decomposition tables, or the detection output, within tolerance (relative 1%, or a match after rounding to the same decimal places). Percentages and fractions count as equivalent (0.23 matches 23%).
- Also extract every number from `summary` and `claim` text with a regex and run the same check. Ignore years, months and list numbering.
- Each finding gets a label: `verified`, `partially_verified` or `unsupported`.
- Output: per-finding labels and the run's **unsupported claim rate** (unsupported numbers / total numbers).

**Revision mode (config C):** if any numbers are unsupported, send the model the list of unsupported items and their cited query results once, and ask for a corrected report. Verify again.

### 4.7 `src/baseline.py`
LLM-only baseline: give the model the question plus the monthly KPI totals table only (no decomposition, no SQL tools). Ask for the same final report schema. This is what "just paste the KPI report into an AI" looks like. Verify its numbers against the KPI totals table.

### 4.8 `src/report.py` and `src/cli.py`
- `report.py` renders a final report to Markdown: summary, findings with verification badges, evidence queries, and the investigate-next list. Saves to `results/reports/<run_id>.md`.
- `cli.py` runs the whole pipeline from the command line: `--db`, `--month`, `--question`, `--mode baseline|agent|agent_verify`.

---

## 5. Evaluation harness (`eval/`)

### 5.1 Anomaly injection (`eval/inject.py`)
Copy the DuckDB database, apply one anomaly to one target month, and save it as `data/eval/<scenario_id>.duckdb`. Each scenario is defined in `eval/scenarios.yaml` with: id, question, target month, target KPI, ground-truth dimension and segment, and the injection operation.

**Choosing segments:** pick them automatically from the data (log the picks in `docs/DECISIONS.md`). Rules: use a target month in the middle of the window (for example 2018-03), and choose segments with at least 3% of that month's orders, so the anomaly is large enough to be detectable but isn't the whole business. Use a different segment for each scenario where possible.

| # | Anomaly | Injection | Question asked |
|---|---|---|---|
| 1 | Category demand drop | Delete 50% of orders containing category A in month M | Why did revenue drop? |
| 2 | Category price hike | Multiply `price` by 1.3 for category B in M | Why did AOV rise? |
| 3 | Top seller drops out | Delete all orders from the top seller by revenue in M | Why did revenue drop? |
| 4 | Regional delivery delay | Add 10 days to delivered date for state S1 in M | Why did late deliveries rise? |
| 5 | Delay hurts reviews | Same delay as #4 for state S2 and set 50% of those orders' review scores to 1 | Why did review scores fall? |
| 6 | Freight spike | Multiply `freight_value` by 1.8 for state S3 in M | Why did the freight ratio rise? |
| 7 | Regional demand surge | Duplicate 40% of state S4 orders in M (new order ids, with matching items, payments and reviews) | Why did orders rise? |
| 8 | Payment mix shift | Switch 60% of credit card payments to voucher in M | What changed in payments? |
| 9 | Cancellation spike | Set 25% of orders in category C to `canceled` in M | Why did cancellations rise? |
| 10 | Big-ticket category drop | Delete 60% of orders in the highest-AOV category (with enough volume) in M | Why did AOV fall? |
| 11 | Two causes at once | #1 for category D plus #4 for state S5, same month | Why did revenue drop and late deliveries rise? |
| 12 | Decoy | Delete a random 15% of orders evenly across all segments (no single cause) | Why did revenue drop? |

Deletions must cascade across related tables (items, payments, reviews) so the data stays consistent. Use a fixed random seed. After injecting, run detection and confirm the target KPI is flagged as significant. If it isn't, increase the injection strength one step and log it.

Scenario 12 tests whether the system wrongly invents a single culprit. A correct answer says the drop is broad-based.

### 5.2 Configurations compared
- **A. Baseline:** LLM-only (Section 4.7)
- **B. Agent:** detection + decomposition + SQL agent
- **C. Agent + verifier revision:** B plus one revision round

### 5.3 Metrics (`eval/score.py`)
- **Root cause hit@1:** the top finding names the ground-truth dimension and segment (case-insensitive; accept the English or Portuguese category name, the state code, or the seller id).
- **Root cause hit@3:** the truth appears in any of the top 3 findings.
- For scenario 11, score each cause separately (each counts as half a hit). For scenario 12, a hit means no finding claims one segment explains more than 50% of the drop and the summary describes the drop as broad.
- **Unsupported claim rate** (from the verifier).
- **Mean steps and wall-clock time** per run.

### 5.4 Runner (`eval/run_eval.py`)
- CLI flags: `--configs A B C`, `--scenarios all`, `--runs 1`.
- Writes `results/eval_runs.csv` (one row per run), `results/eval_summary.json` and `results/eval_summary.md`.
- **Resumable:** skips runs that already exist in the CSV.
- Prints an estimated time remaining after the first 3 runs.

**Running it unattended:** start it in the background so the Mac doesn't sleep and the run survives the session:
```
nohup caffeinate -i .venv/bin/python -m eval.run_eval --configs A B C --scenarios all --runs 1 > results/eval.log 2>&1 &
```
Check `results/eval.log` every few minutes. Note the time and the expected finish in `PROGRESS.md`. If this session ends before the eval finishes, the next session resumes from the CSV.

---

## 6. Streamlit app (`app/streamlit_app.py`)

Runs locally with `streamlit run app/streamlit_app.py`. No hosting.

- Sidebar: choose the database (real data or an eval scenario), month, question (preset list plus free text), and mode (baseline / agent / agent + verifier).
- Main panel:
  1. KPI trend chart for the last 12 months (Plotly), with the target month highlighted
  2. Detection table
  3. Decomposition tables (tabs per dimension)
  4. Agent trace: each hypothesis, the SQL it ran, the rows returned, and its status
  5. Final report with a green / amber / red badge per finding from the verifier
  6. Investigate-next list
- A "Results" page showing `results/eval_summary.md` and a bar chart of hit@1 by configuration.

**Screenshots:** after the app works, use Playwright (free; `uv pip install playwright` and `playwright install chromium`) to load the app headlessly, run one example, and save `docs/img/app_overview.png` and `docs/img/agent_trace.png` for the README. If Playwright can't capture Streamlit reliably, skip it, log it in `docs/DECISIONS.md`, and leave an image placeholder in the README.

---

## 7. Repo structure

```
ai-kpi-analyst/
├── README.md
├── PROJECT_SPEC.md            # this file
├── PROGRESS.md                # checkpoint for resuming
├── requirements.txt
├── requirements-dev.txt       # pytest, ruff, playwright
├── .gitignore                 # data/, .venv/, __pycache__/, *.duckdb, .env, results/eval.log
├── .env.example               # KPI_MODEL=..., no secrets
├── config.py
├── scripts/
│   ├── download_data.py
│   ├── check_repo.py
│   └── check_readme.py
├── src/
│   ├── data_load.py
│   ├── kpis.py
│   ├── detect.py
│   ├── decompose.py
│   ├── sql_guard.py
│   ├── llm.py
│   ├── prompts.py             # all prompts, versioned (PROMPT_VERSION)
│   ├── agent.py
│   ├── baseline.py
│   ├── verify.py
│   ├── report.py
│   └── cli.py
├── eval/
│   ├── scenarios.yaml
│   ├── inject.py
│   ├── run_eval.py
│   └── score.py
├── app/
│   └── streamlit_app.py
├── tests/
│   ├── test_kpis.py           # KPI values on a tiny hand-built fixture
│   ├── test_decompose.py      # components sum to total change
│   ├── test_sql_guard.py      # rejects writes, ATTACH, file reads, multi-statement
│   ├── test_verify.py         # tolerance, % vs fraction, unsupported detection
│   └── test_inject.py         # each injection changes only the intended slice, cascades correctly
├── results/                   # committed: eval CSV, summary JSON/MD, sample reports
└── docs/
    ├── architecture.md        # Mermaid diagram of the pipeline
    ├── DECISIONS.md
    └── img/
```

Tests that need the LLM are marked `@pytest.mark.llm` and skipped by default, so `pytest` stays fast and deterministic.

**requirements.txt (all free):** `duckdb`, `pandas`, `sqlglot`, `ollama`, `pydantic`, `pyyaml`, `streamlit`, `plotly`, `python-dotenv`, `kagglehub`. Pin versions after install (`uv pip freeze` for these packages).

---

## 8. README requirements

Write it for a hiring manager who'll spend 90 seconds on it. Plain, direct language. No hype words.

1. One-line pitch and the app screenshot
2. **The problem:** a dashboard shows *that* a KPI moved; analysts spend their time on *why*. LLMs can help, but they make up numbers.
3. **How it works:** Mermaid diagram plus 6 short steps
4. **Results:** table generated from `results/eval_summary.json` (hit@1, hit@3, unsupported claim rate, mean time per run, for configs A, B, C), plus the model used and the hardware it ran on. Use `[TBD]` until real numbers exist.
5. **Example report:** one real report from `results/reports/`, trimmed
6. **What didn't work / limitations:** written honestly from the actual eval results (scenarios where the agent failed, local model limits, synthetic anomalies vs real-world messiness)
7. **Run it yourself:** install steps, `python scripts/download_data.py`, build the DB, run the app, run the evals
8. **Cost:** $0. Everything runs locally on open-source tools.
9. Data credit to Olist and the licence

---

## 9. Out of scope

- Cloud deployment, auth, Docker
- Fine-tuning
- Multiple datasets
- Forecasting

---

## 10. Build order and commits

| Step | Work | Commit message |
|---|---|---|
| 1 | Environment setup (0.3), repo scaffold, `.gitignore`, requirements, `config.py`, `PROGRESS.md` | `chore: project scaffold` |
| 2 | `download_data.py`, `data_load.py`, `kpis.py` + `test_kpis.py`; print monthly KPIs to sanity-check | `feat: automated data download, DuckDB load, KPI definitions` |
| 3 | `detect.py`, `decompose.py` + tests | `feat: change detection and driver decomposition` |
| 4 | `sql_guard.py` + tests | `feat: read-only SQL guard` |
| 5 | `llm.py`, `prompts.py`, `agent.py`, `baseline.py`, `cli.py`; run the agent on one real month and save the report | `feat: hypothesis-testing agent and LLM baseline` |
| 6 | `verify.py` + tests, revision mode, `report.py` | `feat: claim verifier and revision loop` |
| 7 | `eval/` injection, scenarios, scoring + `test_inject.py`; run 1 scenario × 3 configs as a smoke test | `feat: anomaly injection eval harness` |
| 8 | Streamlit app, screenshots | `feat: Streamlit app with agent trace and verification badges` |
| 9 | README (results as `[TBD]`), `docs/architecture.md`, `scripts/check_repo.py`, `scripts/check_readme.py` | `docs: README and architecture` |
| 10 | Run all quality gates (0.4) except the README number check. Create the repo with `gh repo create rajisworking16/ai-kpi-analyst --public --source=. --push` | (push) |
| 11 | Start the full eval in the background (5.4). Monitor it. | |
| 12 | When the eval finishes: commit `results/`, fill the README results and limitations from real numbers, run **all** quality gates including `check_readme.py`, push | `results: eval run v1` |
| 13 | Write the private files (Section 11), update `PROGRESS.md` to "Done" | (not committed) |

If the full eval would take more than about 4 hours on this machine (based on the estimate after 3 runs), cut it to configs A and C first, then run B if time allows. Log this in `docs/DECISIONS.md` and the README.

---

## 11. Private files (outside the repo, never committed)

Write these to `~/projects/ai-kpi-analyst-private/`:

### 11.1 `RESUME_POINTS.md`
Fill every number from `results/eval_summary.json` and the data load output. If a result is weak (for example, the agent doesn't beat the baseline), don't hide it: rewrite the bullet around what the eval actually showed, and add a note explaining the change.

Template:

**Project header:** AI KPI Analyst | Python, DuckDB, SQL, Ollama (local LLM), Streamlit | github.com/rajisworking16/ai-kpi-analyst

- Built an AI analytics workflow that explains *why* e-commerce KPIs moved across [N] orders (Olist), combining deterministic change detection and driver decomposition with an LLM agent that tests its own hypotheses using read-only SQL
- Designed an evaluation harness of [12] planted anomalies (demand drops, price changes, delivery delays, seller churn, a no-single-cause decoy); the agent identified the root cause in [X]/[12] scenarios vs [Y]/[12] for an LLM-only baseline
- Added a claim verifier that checks every figure in the AI's write-up against query results, cutting unsupported numbers from [A]% (LLM-only) to [B]% (agent + verifier revision)
- Shipped a local Streamlit app showing the agent's query trace and verified findings, built entirely on free, open-source tools at $0 cost

**Shorter 2-line version:**
- Built an LLM agent (Python, DuckDB, Ollama) that diagnoses KPI changes by testing hypotheses with SQL; found the root cause in [X]/[12] planted-anomaly tests vs [Y]/[12] for an LLM-only baseline
- Built a verifier that checks every AI-cited figure against query results, cutting unsupported numbers from [A]% to [B]%

**Interview one-liner:** "Dashboards tell you a number moved. I built an agent that works out why, and then I measured how often it's right, because AI explanations are only useful if you can check them."

Rules for this file: no em-dashes, no buzzwords, every number traceable to a results file (list the source file under each bullet).

### 11.2 `INTERVIEW_PREP.md`
Plain-language walkthrough Pranav can read in 20 minutes:
- What each module does, in one or two sentences each
- Why each design choice was made (structured JSON over tool calling, deterministic decomposition before the LLM, read-only SQL guard, planted anomalies for evaluation, local model for zero cost)
- The actual results, including what failed and why
- The 8 questions an interviewer is most likely to ask, with honest answers grounded in this build
- 3 things he'd improve next

### 11.3 `SUMMARY.md`
Short status: repo link, what was built, final eval numbers, anything left unfinished, and any blockers.
