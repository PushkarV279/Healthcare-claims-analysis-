# Healthcare Claims Analytics

A small data analytics project built with Python, Pandas, NumPy, Matplotlib and MySQL.

The project uses **synthetic healthcare claims data**. No real patient or medical information is used.

## What I wanted to analyze

The main goal was to understand:

- Which procedures have the highest spending?
- Which diagnoses account for the most spending?
- Which providers have high claim spending?
- Which procedures have higher denial rates?
- How much do patients pay under different insurance plans?
- How does spending change over time?
- Which individual claims have the highest payments?

## Project Flow

```
Generate synthetic data
        ↓
Raw CSV file
        ↓
Clean and validate data
        ↓
Add calculated columns
        ↓
Create summaries and charts
        ↓
Save cleaned CSV
        ↓
Load data into MySQL
        ↓
Run SQL analysis
```

## Project Structure

```
Healthcare-claims-analysis/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── reports/
│   ├── figures/
│   ├── tables/
│   └── EXECUTIVE_SUMMARY.md
│
├── sql/
│   ├── schema.sql
│   └── analysis_queries.sql
│
├── src/
│   ├── generate_data.py
│   ├── pipeline.py
│   └── load_to_mysql.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

## Python Part

### 1. `generate_data.py`

Creates synthetic healthcare claim records.

Each claim contains information such as:

- Claim ID
- Patient ID
- Provider ID
- Diagnosis
- Procedure
- Claim date
- Insurance plan
- Billed amount
- Allowed amount
- Paid amount
- Patient responsibility
- Claim status
- Provider state

A random seed is used so that the same input can produce the same dataset again.

### 2. `pipeline.py`

This is the main analysis script.

It:

1. Reads the raw CSV using Pandas.
2. Checks that required columns are present.
3. Converts amounts to numeric values.
4. Converts claim dates to date format.
5. Removes invalid rows.
6. Removes duplicate claim IDs.
7. Creates a few calculated columns.
8. Groups the data to answer business questions.
9. Saves summary tables.
10. Creates charts.
11. Creates a short executive summary.

The calculated columns are:

- `discount_amount` — billed amount minus allowed amount
- `patient_share` — patient responsibility divided by allowed amount
- `claim_month` — month extracted from the claim date
- `is_denied` — 1 if the claim was denied, otherwise 0

### 3. `load_to_mysql.py`

Reads the cleaned CSV and loads it into a MySQL `claims` table using SQLAlchemy.

## SQL Part

`schema.sql` creates the `claims_intelligence` database and the `claims` table.

`analysis_queries.sql` contains SQL questions using concepts such as:

- SELECT
- WHERE
- GROUP BY
- HAVING
- ORDER BY
- COUNT
- SUM
- AVG
- CASE
- JOIN
- CTE
- Window functions

The queries are mainly focused on spending, denials, providers, insurance plans and monthly trends.

## Running the Project

Install the required packages:

```powershell
python -m pip install -r requirements.txt
```

Generate the raw data:

```powershell
python src/generate_data.py --rows 250000 --output data/raw/healthcare_claims_raw.csv
```

Run the analysis:

```powershell
python src/pipeline.py --input data/raw/healthcare_claims_raw.csv --output-dir .
```

The cleaned data and analysis results will be created inside the `data/processed` and `reports` folders.

## MySQL

First run:

```text
sql/schema.sql
```

Then set the database connection:

```powershell
$env:DATABASE_URL = 'mysql+pymysql://username:password@localhost:3306/claims_intelligence'
```

Then load the cleaned data:

```powershell
python src/load_to_mysql.py --input data/processed/healthcare_claims_cleaned.csv
```

Finally, run the queries in:

```text
sql/analysis_queries.sql
```

## Limitations

This is a learning project using synthetic data.

The results should not be treated as real healthcare industry statistics. The project is intended to demonstrate Python data processing, SQL analysis and basic data visualization.

It is not a clinical system, fraud detection system or production healthcare application.
