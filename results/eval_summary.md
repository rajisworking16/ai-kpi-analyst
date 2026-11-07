# Evaluation summary

Model `qwen2.5:7b`, prompt v4, Apple M5, 24 GB RAM, macOS 26.7.2. Generated 2026-11-08T02:09:05.

| Config | Root cause hit@1 | Root cause hit@3 | Unsupported claim rate | Mean steps | Mean time per run (s) | Errors |
|---|---|---|---|---|---|---|
| A. Baseline (LLM only) | 0/12 | 0/12 | 10.0% (1/10) | 1.0 | 50.5 | 0 |
| B. Agent | 1/12 | 1/12 | 0.0% (0/6) | 11.0 | 321.3 | 0 |
| C. Agent + verifier revision | 0/12 | 0/12 | n/a (0/0) | 0.0 | 95.9 | 1 |

## Per scenario (hit@1 / hit@3, top finding)

| Scenario | A | B | C |
|---|---|---|---|
| s01_category_demand_drop | 0 / 0 (overall=all) | 1 / 1 (category=health_beauty) | 0 / 0 (=) |
| s02_category_price_hike | 0 / 0 (overall=all) |  |  |
| s03_top_seller_dropout |  |  |  |
| s04_regional_delivery_delay |  |  |  |
| s05_delay_hurts_reviews |  |  |  |
| s06_freight_spike |  |  |  |
| s07_regional_demand_surge |  |  |  |
| s08_payment_mix_shift |  |  |  |
| s09_cancellation_spike |  |  |  |
| s10_big_ticket_category_drop |  |  |  |
| s11_two_causes |  |  |  |
| s12_decoy_broad_drop |  |  |  |
