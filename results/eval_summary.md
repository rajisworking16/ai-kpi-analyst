# Evaluation summary

Model `qwen2.5:7b`, prompt v4, Apple M5, 24 GB RAM, macOS 26.7.2. Generated 2026-11-08T03:32:05.

| Config | Root cause hit@1 | Root cause hit@3 | Unsupported claim rate | Mean steps | Mean time per run (s) | Errors |
|---|---|---|---|---|---|---|
| A. Baseline (LLM only) | 1/12 | 1/12 | 29.8% (25/84) | 1.0 | 46.9 | 0 |
| B. Agent | 4.5/12 | 7/12 | 1.5% (1/67) | 9.8 | 216.0 | 1 |
| C. Agent + verifier revision | 5.5/12 | 7/12 | 0.0% (0/56) | 9.6 | 185.6 | 1 |

## Per scenario (hit@1 / hit@3, top finding)

| Scenario | A | B | C |
|---|---|---|---|
| s01_category_demand_drop | 0 / 0 (overall=all) | 1 / 1 (category=health_beauty) | 1 / 1 (category=health_beauty) |
| s02_category_price_hike | 0 / 0 (overall=all) | 0 / 0 (customer_state=SP) | 0 / 0 (customer_state=SP) |
| s03_top_seller_dropout | 0 / 0 (orders=all) | 0 / 0 (overall=all) | 0 / 0 (overall=all) |
| s04_regional_delivery_delay | 0 / 0 (overall=all) | 0 / 0 (=) | 0 / 0 (=) |
| s05_delay_hurts_reviews | 0 / 0 (overall=all) | 0 / 0 (category=watches_gifts) | 0 / 0 (overall=all) |
| s06_freight_spike | 0 / 0 (freight_value=all) | 1 / 1 (customer_state=RJ) | 1 / 1 (customer_state=RJ) |
| s07_regional_demand_surge | 0 / 0 (overall=all) | 1 / 1 (customer_state=SP) | 1 / 1 (customer_state=SP) |
| s08_payment_mix_shift | 1 / 1 (payment_type=credit_card) | 0 / 1 (overall=all) | 1 / 1 (payment_type=voucher) |
| s09_cancellation_spike | 0 / 0 (overall=all) | 0 / 1 (customer_state=SC) | 0 / 1 (customer_state=SC) |
| s10_big_ticket_category_drop | 0 / 0 (overall=all) | 1 / 1 (category=watches_gifts) | 1 / 1 (category=watches_gifts) |
| s11_two_causes | 0 / 0 (seller_id=10000000000000000000000000000001) | 0.5 / 1 (category=sports_leisure) | 0.5 / 1 (category=sports_leisure) |
| s12_decoy_broad_drop | 0 / 0 (overall=all) | 0 / 0 (payment_type=credit_card) | 0 / 0 (customer_state=SP) |
