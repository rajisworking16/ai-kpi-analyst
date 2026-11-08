# Decisions

One line each: decision, then reason.

- Model `qwen2.5:7b` (Ollama 0.40.15): machine has 24 GB RAM (Apple M5), spec says 7b when RAM >= 16 GB.
- Python 3.12 via `uv` venv: system Python is 3.13 but spec asks for 3.12 via uv.
- Repo-local git identity uses the GitHub noreply address: keeps personal email out of commits.
- Data downloaded anonymously with kagglehub: worked without credentials, no Kaggle token needed.
- Dataset licence is CC BY-NC-SA 4.0 (from Kaggle dataset metadata): README credits Olist and states the licence; repo is non-commercial.
- Analysis window 2017-01 to 2018-08: monthly order counts are 800 to 7,544 in that range; 2016 months and 2018-09/10 have 1 to 324 orders.
- `orders_enriched` keeps orders with no items (775 orders, mostly canceled/unavailable) via LEFT JOIN: needed so cancellation rate uses all orders placed.
- `payment_type` in `orders_enriched` is the order's primary payment type (largest total payment value): orders can have several payment rows; one value per order keeps segment math additive.
- KPI month is the purchase month for all KPIs, including delivery KPIs: one consistent cohort definition; deliveries of a month's orders are attributed to the purchase month.
- Late = delivered calendar date after estimated calendar date: estimated dates have no time component.
- Avg review score uses all orders with a review (any status): matches the KPI definition "averaged over orders".
- Segment KPIs count an order in every segment it touches (e.g. an order with two categories counts in both): item-level revenue stays exactly additive; order counts per segment may sum to slightly more than the total.
- Detection reports every KPI with a `significant` flag (not only flagged ones): the agent and app need the full picture; flagged ones are marked.
- Rate/ratio KPI decomposition uses a midpoint shift-share split (rate effect + mix effect per segment, sums exactly to the change in the weighted mean): separates mix shifts from rate changes as the spec asks.
- Decomposition runs on the KPIs named in the question (deterministic keyword map in `src/context.py`); if none match, the two most significant KPIs: keeps the prompt small enough for a 7B model. "Payments" questions decompose order counts (payment_type is a dimension).
- Structured outputs use one flat `AgentStep` schema (action enum + all fields, unused ones empty) instead of a union: simpler grammar for the constrained decoder. The final report is a separate call with the `Report` schema.
- Every list and string in the LLM schemas has a max length: with greedy decoding qwen2.5:7b looped forever inside `evidence_query_ids` (9,000+ tokens); `maxItems`/`maxLength` are enforced by Ollama's grammar. Also `num_predict=2000` and `num_ctx=32768`.
- Deterministic tables get evidence ids (`detection`, `revenue_split`, `decomp_<kpi>_<dim>`, `kpi_table`) so findings can cite them like query ids; the verifier treats them as always-available evidence (spec: numbers may match decomposition or detection output).
- Prompt includes a deterministic "Facts" line (direction and size of each focus KPI) and copyable SQL templates with real months: in the first test the 7B model wrote SQL that summed both months as "prev" and reported a 15% revenue rise as a decline.
- Step budget: hypothesis proposal counts as step 1 and the final report as the last step (max 12 LLM calls per agent run, plus one revision call in config C).
- Verifier: sign is ignored when matching (text states direction in words); bare integers 0 to 10 are treated as wording ("top 3"), not data claims; numbers like "30.7k" / "1.2 million" are scaled; a finding with no numbers and no valid evidence id is `unsupported`.
- Eval target month is 2018-05, not 2018-03: 2018-03 revenue naturally rose 15.4% MoM (and late rate +34%), which would contradict the "why did revenue drop?" scenarios; 2018-05 has revenue +0.4%, orders -0.7%, AOV +1.1% vs 2018-04.
- Eval segments picked automatically by `eval/inject.py --generate` (>= 3% of 2018-05 delivered orders = 202.5 orders): highest-AOV category watches_gifts (#10); then by revenue A=health_beauty (#1), B=bed_bath_table (#2), C=housewares (#9), D=sports_leisure (#11); states by order count S4=SP (#7 surge), S3=RJ (#6 freight), S1=MG (#4), S2=RS (#5), S5=PR (#11); top seller 7d13fca15225358621be4086e1eb0964 (3.04% of orders, #3).
- Strength escalation (one step) was applied where detection did not flag the target KPI: s01 (50% -> 75% deletion), s03 (already 100%, no stronger step exists), s05 (10 -> 20 days, 50% -> 75% reviews), s06 (1.8x -> 2.5x freight), s10 (60% -> 90% deletion), s11 (75% deletion, 20 days). After the step, s01, s03, s05, s10 and the revenue half of s11 are still NOT flagged: one category or seller is too small a share of revenue to move monthly revenue/AOV by 15% or 2 sigma. The eval still asks the question; `results/eval_injections.json` records the flags.
- Scenario 8 (payment mix) has no target KPI among the 8 KPIs, so no detection check; ground truth accepts credit_card or voucher as the segment.
- Price hike (#2) changes item price only; payment rows are left as-is: payment values are not used by any KPI.
- Duplicated orders (#7) get new ids `md5(order_id || '_dup')`, same customer, copied items, payments and reviews (new review ids).
- Canceled orders (#9) get `order_delivered_customer_date = NULL`.
- Scoring: a finding hits when its `dimension` (normalised synonyms) and `segment` (case-insensitive, English or Portuguese category, state code, seller id or 8+ char prefix) match the truth; claim text is not used. Decoy hit = summary describes a broad drop and no non-overall finding cites a share > 50%.
- Failed runs (LLM errors) are kept in the CSV as misses with the error message, never dropped.
- Streamlit app accepts `?run=<saved run id>&month=` query params: lets Playwright capture screenshots of a saved run without driving widgets.
