# Healthcare Claims Analytics & Cost Analysis

This report uses synthetic healthcare claims data only; it contains no PHI.

## KPI snapshot

| Metric | Value |
|---|---:|
| Total claims | 250,000 |
| Total paid | $670.46M |
| Average claim payment | $2,682 |
| Overall denial rate | 8.1% |
| Average patient responsibility | $414 |

## Main findings

1. **Inpatient Stay** has the highest total paid spending: **$205.35M**.
2. **Cancer** generates the most paid spending among diagnoses: **$80.45M**.
3. **P0499** has the highest provider spending, with 2,710 claims and **$8.43M** paid.
4. **Prior-Authorization Procedure** has the highest denial rate: **30.2%** across 19,447 claims.
5. **High-Deductible Plan** has the highest average patient responsibility: **$976**.
6. Monthly spending changed from **$18.61M** in 2023-01 to **$19.06M** in 2025-12.

## Data quality

The pipeline read 250,000 rows, removed 0 invalid rows, and analyzed 250,000 claims from 2023-01-01 to 2025-12-31.
