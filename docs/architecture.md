# Architecture

```mermaid
flowchart TD
    Q[Question + month] --> C
    subgraph Deterministic["Deterministic (Python + DuckDB SQL)"]
        DB[(DuckDB: orders_enriched)] --> K[kpis.py: monthly KPIs]
        K --> D[detect.py: MoM change + trailing z-score]
        DB --> X[decompose.py: volume/AOV split, segment contributions, rate vs mix]
        D --> C[context.py: facts + evidence tables with ids]
        X --> C
    end
    subgraph LLM["Local LLM (Ollama, qwen2.5:7b, JSON schema outputs)"]
        C --> H[agent.py: propose 3-5 hypotheses]
        H --> S{next action}
        S -- run_sql --> G[sql_guard.py: single SELECT/WITH, read-only, LIMIT, timeout]
        G --> T[(run trace: query ids + rows)]
        T --> S
        S -- update_hypothesis --> S
        S -- final_report --> R[report JSON: summary, findings, investigate next]
    end
    R --> V[verify.py: every number vs cited evidence]
    T --> V
    C --> V
    V -- unsupported numbers, config C --> RV[one revision call] --> V
    V --> M[report.py: Markdown with badges]
    V --> APP[Streamlit app]
```

## Modules

| Module | Job |
|---|---|
| `src/data_load.py` | Loads the Olist CSVs into DuckDB and builds the `orders_enriched` view. |
| `src/kpis.py` | Single source of KPI definitions and the SQL that computes them per period and segment. |
| `src/detect.py` | Flags KPIs whose month-over-month change is >= 15% or whose z-score vs the trailing 6 months is >= 2. |
| `src/decompose.py` | Splits revenue change into volume, AOV and interaction; ranks segments by contribution; splits rate KPIs into rate and mix effects. |
| `src/context.py` | Runs detection + decomposition, registers each table as citable evidence, formats prompts. |
| `src/sql_guard.py` | Parses SQL with sqlglot, rejects anything but one SELECT/WITH, blocks file functions, enforces LIMIT and a timeout, opens DuckDB read-only. |
| `src/llm.py`, `src/schemas.py` | Ollama wrapper with JSON-schema structured outputs, Pydantic validation and one retry. |
| `src/prompts.py` | All prompts, versioned with `PROMPT_VERSION`. |
| `src/agent.py` | The hypothesis loop (max 12 steps, error handling, forced final report). |
| `src/baseline.py` | LLM-only baseline: question + monthly KPI table, no tools. |
| `src/verify.py` | Checks every number in findings, claims and summary against evidence; labels findings; computes the unsupported claim rate. |
| `src/pipeline.py`, `src/cli.py` | End-to-end run for one question; saves trace JSON and Markdown report. |
| `eval/inject.py` | Picks segments from data, copies the DB and plants one anomaly per scenario. |
| `eval/score.py`, `eval/run_eval.py` | Root-cause hit@1/hit@3 scoring and the resumable eval runner. |
| `app/streamlit_app.py` | Local UI: trends, detection, decomposition, agent trace, verified report, eval results. |
