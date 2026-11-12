# AI KPI Analyst

A tool that explains why an e-commerce KPI moved in a given month. It finds which metrics changed, breaks the change down by segment, lets a local LLM test its own hypotheses against the database with read-only SQL, and then checks every number in the final report against the query results.

![App overview](docs/img/app_overview.png)

## The problem

A dashboard tells you that revenue dropped or late deliveries went up. Working out why takes most of an analyst's time: slicing by category, region, seller and payment type until something explains the change. An LLM can speed that up, but LLMs make up numbers, and an explanation you can't check isn't worth much.

## How it works

1. **Detect.** Compare each of 8 KPIs with the previous month and with the mean of the trailing 6 months. A KPI is flagged if its z-score is 2 or more in either direction, or if it changed by 15% or more month over month.
2. **Decompose.** Split the revenue change into volume, average order value and interaction effects. Rank segments (category, customer state, seller, payment type) by how much of the change they account for. Rate KPIs are split into a rate effect and a mix effect.
3. **Hypothesize.** The LLM reads those tables and proposes 3 to 5 possible causes.
4. **Investigate.** For each step the LLM writes one `SELECT` query. A guard parses it with sqlglot and runs it against a read-only DuckDB connection with a row limit and a timeout. The model then marks each hypothesis as supported, rejected or inconclusive.
5. **Verify.** Every number in the findings and summary has to appear in a cited query result or in the detection and decomposition tables, within 1%. Percentages and fractions are treated as the same value, so 23% matches 0.23. In config C (see Results), any unsupported numbers go back to the model for one round of correction.
6. **Report.** A summary, findings with their evidence and a verified, partially verified or unsupported label, and a list of what an analyst should check next.

The model is `qwen2.5:7b` running locally through Ollama. It uses JSON-schema structured outputs rather than native tool calling. More detail is in [docs/architecture.md](docs/architecture.md), and the reasoning behind the design choices is in [docs/DECISIONS.md](docs/DECISIONS.md).

## Results

The evaluation uses 12 planted anomalies injected into a copy of the real data for May 2018: a category demand drop, a price hike, a top seller dropping out, a regional delivery delay, a delay that also hurts reviews, a freight spike, a regional demand surge, a payment mix shift, a cancellation spike, a drop in a big-ticket category, two causes at once, and a decoy with no single cause. Each configuration answers the scenario's question. A run counts as a hit when its top finding names the planted dimension and segment.

<!-- results:start -->
| Config | Root cause hit@1 | Root cause hit@3 | Unsupported claim rate | Mean steps | Mean time per run (s) |
|---|---|---|---|---|---|
| A. Baseline (LLM only) | 1/12 | 1/12 | 29.8% (25/84) | 1.0 | 46.9 |
| B. Agent | 4.5/12 | 7/12 | 1.5% (1/67) | 9.8 | 216.0 |
| C. Agent + verifier revision | 5.5/12 | 7/12 | 0.0% (0/56) | 9.6 | 185.6 |
<!-- results:end -->

Settings: `qwen2.5:7b` on Ollama 0.40.15, temperature 0, seed 42, one run per scenario, on an Apple M5 with 24 GB RAM (macOS 26.7.2). Per-scenario results are in [results/eval_summary.md](results/eval_summary.md) and every individual run is in [results/eval_runs.csv](results/eval_runs.csv).

The agent put the planted cause first in 4.5 of 12 scenarios without revision (B) and 5.5 with it (C), and had it somewhere in its top 3 in 7 of 12. The LLM-only baseline managed 1 of 12. It only sees monthly totals, so it usually blames "overall" performance, and its one hit was the payment scenario.

The bigger difference is in made-up numbers. In the baseline reports, 25 of 84 numbers (29.8%) didn't appear in any table the model was given, and one report cited a seller ID that doesn't exist. The agent's reports had 1 unsupported number out of 67 (1.5%), and 0 out of 56 after one verifier revision round.

Scoring: each scenario is worth one point, except the two-cause scenario, which gives half a point per cause found. A run that crashes counts as a miss.

## Example report

This is a run on the real data for March 2018, asking "Why did revenue change?", with the agent and verifier (config C). It's trimmed from [results/reports/example_2018-03_revenue.md](results/reports/example_2018-03_revenue.md). The run took 11 steps and 133 seconds, and none of its 9 numbers were unsupported.

> **Summary.** The increase in revenue in 2018-03 compared to 2018-02 is primarily driven by the SP customer state, followed by a significant shift in payment methods towards credit cards, and a substantial contribution from the watches_gifts category.
>
> **1. The SP customer state contributed the most to the revenue increase** (verified)
> - 69,205.19: revenue contribution from SP (evidence `decomp_revenue_customer_state`, `q_b22a63`)
>
> **2. Shift towards credit card payments** (verified)
> - 120,582.85: revenue contribution from credit cards (evidence `decomp_revenue_payment_type`, `q_bfa315`)
>
> **3. watches_gifts category** (verified)
> - 34,935.87: revenue contribution from watches_gifts (evidence `decomp_revenue_category`, `q_060ec2`)
>
> **Investigate next:** products inside watches_gifts that drove the growth; marketing activity in SP in March 2018.

![Agent trace](docs/img/agent_trace.png)

The verifier only checks that each number exists in the evidence. It doesn't check whether the interpretation is right. In the report above, the model calls the move to credit cards a significant shift, even though its excess share (0.1622) is fairly modest.

## Limitations

- It's still wrong more often than right at rank 1. The misses: the price hike (#2, where the agent blamed the state of SP), the top seller drop-out (#3, where config C marked the correct seller hypothesis as supported but left it out of the report, and config B named a different seller), the delay that hurts reviews (#5, reported as a broad decline), and the cancellation spike (#9, found at rank 2 behind the state of SC).
- The decoy failed in every configuration. Given a random 15% drop across the board, the agent still named SP, the baby category and credit cards as causes instead of calling it broad-based. A small model would rather point at a specific culprit.
- Two runs crashed, both on scenario #4 (configs B and C). The final report tripped Ollama's repetition guard, and the retry hit the 2,000-token output cap and returned truncated JSON. Both count as misses. A length limit on each evidence ID would probably fix it, but that change wasn't applied, so the results still match the code that was evaluated.
- The verifier barely had to do anything. Only 1 of the 12 config C runs needed a revision. Most of the drop in unsupported numbers comes from grounding the agent in tables and query results, not from the revision step. The gap in hit@1 between B and C (4.5 vs 5.5) is a single scenario (#8) and comes from run-to-run variation in the agent, not from the revision. Ollama isn't fully deterministic even at temperature 0 with a fixed seed.
- Many planted anomalies fall below the detection threshold. Even after one strength increase, detection didn't flag the target KPI in #1, #3, #5, #10 or the revenue half of #11, because a single category or seller is too small a share of revenue to move the monthly total by 15% or 2 standard deviations. The agent still got #1 and #10 right because it reads the segment breakdown, not just the flags.
- Synthetic anomalies are cleaner than real ones. Each scenario plants one sharp cause in one month, while real changes overlap with seasonality, promotions and data delays.
- The sample is small: 12 scenarios, one run each, so a difference of one scenario is within noise. The prompt was changed once, after a smoke test on scenarios #1 and #4, to add the deterministic "excess share" driver summary. The full evaluation ran after that change.
- It's slow. An agent run takes about 3 to 4 minutes on a laptop GPU, compared with under a minute for the baseline.

## Running it

You'll need macOS or Linux, Python 3.12 and [Ollama](https://ollama.com). Everything runs locally on open-source tools (DuckDB, sqlglot, pandas, Pydantic, Ollama, Streamlit, Plotly), so there are no API keys, cloud services or costs.

```bash
git clone https://github.com/rajisworking16/ai-kpi-analyst && cd ai-kpi-analyst
uv venv --python 3.12 && uv pip install -r requirements-dev.txt
ollama pull qwen2.5:7b                      # use qwen2.5:3b on machines with less than 16 GB RAM

.venv/bin/python scripts/download_data.py   # downloads the Olist CSVs from Kaggle into data/raw/
.venv/bin/python -m src.data_load           # builds data/processed/olist.duckdb

# run one analysis from the command line
.venv/bin/python -m src.cli --month 2018-03 --question "Why did revenue change?"

# start the app
.venv/bin/streamlit run app/streamlit_app.py

# run the evaluation (it can be resumed if interrupted)
.venv/bin/python -m eval.inject --generate --all
.venv/bin/python -m eval.run_eval --configs A B C --scenarios all --runs 1

# tests, lint and repo checks
.venv/bin/pytest && .venv/bin/ruff check . && .venv/bin/python scripts/check_repo.py
```

## Data and license

The data is the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce): about 100k orders from 2016 to 2018, of which 99,092 fall in the January 2017 to August 2018 window used here. Thanks to Olist for making it public. The dataset is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). It isn't included in this repository (the download script fetches it), and this project is non-commercial. The code is under the MIT license.
