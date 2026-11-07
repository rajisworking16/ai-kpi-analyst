# KPI analysis: Why did review scores fall?

- Month: 2018-05  
- Mode: agent_verify  
- Model: qwen2.5:7b (prompt v4)  
- Database: `s05_delay_hurts_reviews.duckdb`  
- Steps: 10, wall time: 143.2s  
- Unsupported claim rate: 0.0% (0/2 numbers)

## Summary

The overall decrease in review scores from 2018-04 to 2018-05 is primarily due to a general decline in customer satisfaction across all segments. This broad-based decline is supported by the overall average review scores for both months.

## Findings

### 1. The overall decrease in review scores is due to a general decline in customer satisfaction across all segments.

🟢 verified · KPI `avg_review_score` · overall = `all` · confidence high

- 4.12: Average review score in 2018-04
- 4.04: Average review score in 2018-05
- Evidence: `q_100347`

## Investigate next

- **Explore other KPIs such as cancellation rates, freight ratios, and delivery times to understand the broader impact on customer satisfaction.**: These KPIs can provide additional context on the overall customer experience and identify any specific issues that may be contributing to the decline in review scores. (data needed: Additional KPI data for 2018-04 and 2018-05.)
- **Analyze customer feedback and reviews in more detail to identify common themes or specific issues that customers are experiencing.**: Detailed analysis of customer feedback can help pinpoint specific areas for improvement and identify any recurring issues that may be affecting customer satisfaction. (data needed: Customer feedback and review text data.)

## Hypotheses tested

| id | status | statement |
|---|---|---|
| H1 | rejected | The decrease in review scores is primarily driven by the segment 'watches_gifts'. |
| H2 | rejected | The decrease in review scores is due to a higher proportion of orders using the 'credit_card' payment method. |
| H3 | rejected | The decrease in review scores is related to the performance of the seller '7d13fca15225358621be4086e1eb0964'. |
| H4 | supported | The overall decrease in review scores is due to a general decline in customer satisfaction across all segments. |

## Evidence queries

**`q_1aa5fd`** (H1, 10 rows)

```sql
WITH reviews AS (SELECT order_id, AVG(review_score) AS avg_review_score FROM reviews GROUP BY order_id) SELECT o.customer_state, AVG(r.avg_review_score) AS avg_review_score FROM orders_enriched o JOIN reviews r ON o.order_id = r.order_id WHERE o.order_month IN ('2018-04', '2018-05') AND o.order_status = 'delivered' AND o.category = 'watches_gifts' GROUP BY o.customer_state ORDER BY avg_review_score DESC LIMIT 10;
```

| customer_state | avg_review_score |
|---|---|
| AP | 5 |
| RN | 4.8333 |
| RO | 4.6667 |
| GO | 4.4667 |
| PA | 4.4 |
| DF | 4.3333 |
| SP | 4.3021 |
| ES | 4.2857 |
| MT | 4.2308 |
| PB | 4.2222 |

**`q_e661a5`** (H2, 1 rows)

```sql
WITH reviews AS (SELECT order_id, AVG(review_score) AS avg_review_score FROM reviews GROUP BY order_id) SELECT payment_type, AVG(r.avg_review_score) AS avg_review_score FROM orders_enriched o JOIN reviews r ON o.order_id = r.order_id WHERE o.order_month IN ('2018-04', '2018-05') AND o.order_status = 'delivered' AND o.payment_type = 'credit_card' GROUP BY payment_type ORDER BY avg_review_score DESC LIMIT 10;
```

| payment_type | avg_review_score |
|---|---|
| credit_card | 4.0851 |

**`q_feca41`** (H3, 1 rows)

```sql
WITH reviews AS (SELECT order_id, AVG(review_score) AS avg_review_score FROM reviews GROUP BY order_id) SELECT seller_id, AVG(r.avg_review_score) AS avg_review_score FROM orders_enriched o JOIN reviews r ON o.order_id = r.order_id WHERE o.order_month IN ('2018-04', '2018-05') AND o.order_status = 'delivered' AND o.seller_id = '7d13fca15225358621be4086e1eb0964' GROUP BY seller_id ORDER BY avg_review_score DESC LIMIT 10;
```

| seller_id | avg_review_score |
|---|---|
| 7d13fca15225358621be4086e1eb0964 | 4.1195 |

**`q_100347`** (H4, 2 rows)

```sql
WITH reviews AS (SELECT order_id, AVG(review_score) AS avg_review_score FROM reviews GROUP BY order_id) SELECT AVG(r.avg_review_score) AS avg_review_score FROM orders_enriched o JOIN reviews r ON o.order_id = r.order_id WHERE o.order_month IN ('2018-04', '2018-05') AND o.order_status = 'delivered' GROUP BY o.order_month ORDER BY o.order_month DESC LIMIT 10;
```

| avg_review_score |
|---|
| 4.0392 |
| 4.115 |

