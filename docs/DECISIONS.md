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
