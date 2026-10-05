# Healthcare Claims Analytics & Cost Analysis

A focused, student-friendly healthcare payments project using **Python, Pandas, NumPy, MySQL, and Matplotlib**. It uses synthetic data only—no PHI.

## What the project does

1. Loads healthcare claims data from CSV.
2. Cleans data with Pandas: fixes dates and numeric columns, removes invalid rows, and removes duplicate claim IDs.
3. Adds four simple business columns:
   * `discount_amount` = billed amount − allowed amount
   * `patient_share` = patient responsibility ÷ allowed amount
   * `claim_month` = month extracted from claim date
   * `is_denied` = 1 for denied claims, otherwise 0
4. Answers spending, provider, denial, patient-responsibility, time-trend, and expensive-claim questions.
5. Loads the cleaned data into MySQL and demonstrates readable SQL queries.
6. Creates five Matplotlib charts and an executive summary.

## Run it

From this folder:

```powershell
python -m pip install -r requirements.txt
python src/generate_data.py --rows 250000 --output data/raw/healthcare_claims_raw.csv
python src/pipeline.py --input data/raw/healthcare_claims_raw.csv --output-dir .
```

## Outputs

* `data/processed/healthcare_claims_cleaned.csv` — cleaned claims with the four calculated columns.
* `reports/EXECUTIVE_SUMMARY.md` — the main business findings.
* `reports/tables/` — simple CSV summaries made with Pandas `groupby()` and `agg()`.
* `reports/figures/` — five Matplotlib charts.

## MySQL

Apply `sql/schema.sql`, then load the cleaned CSV:

```powershell
$env:DATABASE_URL = 'mysql+pymysql://username:password@localhost:3306/claims_intelligence'
python src/load_to_mysql.py --input data/processed/healthcare_claims_cleaned.csv
```

Open `sql/analysis_queries.sql` to work through examples of `SELECT`, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`, `JOIN`, `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, and `CASE`. The final query is the only advanced one: a CTE with a window function.

## Interview description

> I built a healthcare claims analytics project using Python, Pandas, NumPy and MySQL. I worked with synthetic healthcare claims data and built a pipeline to clean and validate the data, calculate denial-rate and patient-responsibility metrics, and analyze spending by providers, procedures and diagnoses. I then loaded the data into MySQL and wrote SQL queries to perform similar business analyses. Finally, I created visualizations to communicate the major trends.

## Important limits

This is a learning project, not a clinical or fraud-detection system. The synthetic claims are designed for analytics practice only.
