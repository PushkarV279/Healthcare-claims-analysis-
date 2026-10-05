"""A simple Pandas and Matplotlib healthcare claims analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


MONEY_COLUMNS = ["billed_amount", "allowed_amount", "paid_amount", "patient_responsibility"]
REQUIRED_COLUMNS = {"claim_id", "patient_id", "provider_id", "diagnosis", "procedure", "claim_date",
                    "insurance_plan", *MONEY_COLUMNS, "claim_status"}


def load_and_clean(source: Path) -> tuple[pd.DataFrame, dict]:
    """Read the CSV, fix data types, and remove unusable rows."""
    df = pd.read_csv(source)
    df.columns = df.columns.str.strip().str.lower()
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    source_rows = len(df)
    for column in MONEY_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["claim_date"] = pd.to_datetime(df["claim_date"], errors="coerce")
    for column in df.select_dtypes(include=["object", "string"]).columns:
        df[column] = df[column].astype("string").str.strip()

    invalid = df["claim_date"].isna() | df[MONEY_COLUMNS].isna().any(axis=1) | (df[MONEY_COLUMNS] < 0).any(axis=1)
    invalid_rows = int(invalid.sum())
    df = df.loc[~invalid].drop_duplicates(subset="claim_id").copy()
    df["claim_status"] = df["claim_status"].str.title()
    return df, {"source_rows": source_rows, "invalid_rows_removed": invalid_rows, "clean_rows": len(df),
                "date_min": str(df["claim_date"].min().date()), "date_max": str(df["claim_date"].max().date())}


def add_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add a few business-friendly fields that are easy to explain."""
    df = df.copy()
    df["discount_amount"] = (df["billed_amount"] - df["allowed_amount"]).round(2)
    df["patient_share"] = np.where(df["allowed_amount"] > 0,
                                   df["patient_responsibility"] / df["allowed_amount"], np.nan)
    df["claim_month"] = df["claim_date"].dt.to_period("M").astype(str)
    df["is_denied"] = (df["claim_status"] == "Denied").astype(int)
    return df


def build_summaries(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Answer the core business questions with groupby and aggregation."""
    procedure = (df.groupby(["procedure", "procedure_description"], as_index=False)
                 .agg(claims=("claim_id", "count"), total_paid=("paid_amount", "sum"), avg_paid=("paid_amount", "mean"))
                 .sort_values("total_paid", ascending=False))
    diagnosis = (df.groupby("diagnosis", as_index=False)
                 .agg(claims=("claim_id", "count"), total_paid=("paid_amount", "sum"), avg_paid=("paid_amount", "mean"))
                 .sort_values("total_paid", ascending=False))
    provider = (df.groupby(["provider_id", "provider_state"], as_index=False)
                .agg(claims=("claim_id", "count"), total_paid=("paid_amount", "sum"), avg_paid=("paid_amount", "mean"),
                     denial_rate=("is_denied", "mean"))
                .sort_values("total_paid", ascending=False))
    denial = (df.groupby(["procedure", "procedure_description"], as_index=False)
              .agg(claims=("claim_id", "count"), denied_claims=("is_denied", "sum"), denial_rate=("is_denied", "mean"))
              .sort_values("denial_rate", ascending=False))
    plan = (df.groupby("insurance_plan", as_index=False)
            .agg(claims=("claim_id", "count"), avg_patient_responsibility=("patient_responsibility", "mean"),
                 total_patient_responsibility=("patient_responsibility", "sum"), avg_patient_share=("patient_share", "mean"))
            .sort_values("avg_patient_responsibility", ascending=False))
    monthly = (df.groupby("claim_month", as_index=False)
               .agg(claims=("claim_id", "count"), total_paid=("paid_amount", "sum"), avg_paid=("paid_amount", "mean"),
                    denial_rate=("is_denied", "mean"))
               .sort_values("claim_month"))
    expensive = df.nlargest(100, "paid_amount")["claim_id patient_id provider_id diagnosis procedure claim_date paid_amount".split()]
    return {"procedure_summary": procedure, "diagnosis_summary": diagnosis, "provider_summary": provider,
            "denial_summary": denial, "plan_summary": plan, "monthly_summary": monthly,
            "top_expensive_claims": expensive}


def make_charts(summaries: dict[str, pd.DataFrame], output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    def save(filename: str) -> None:
        plt.tight_layout(); plt.savefig(output / filename, dpi=160, bbox_inches="tight"); plt.close()

    data = summaries["procedure_summary"].head(10).sort_values("total_paid")
    plt.figure(figsize=(10, 5)); plt.barh(data["procedure_description"], data["total_paid"], color="#247ba0")
    plt.title("Top Procedures by Total Paid"); plt.xlabel("Total paid ($)"); save("01_procedure_spending.png")
    data = summaries["diagnosis_summary"].head(10).sort_values("total_paid")
    plt.figure(figsize=(10, 5)); plt.barh(data["diagnosis"], data["total_paid"], color="#70c1b3")
    plt.title("Top Diagnoses by Total Paid"); plt.xlabel("Total paid ($)"); save("02_diagnosis_spending.png")
    data = summaries["denial_summary"].query("claims >= 100").head(10).sort_values("denial_rate")
    plt.figure(figsize=(10, 5)); plt.barh(data["procedure_description"], data["denial_rate"], color="#e76f51")
    plt.gca().xaxis.set_major_formatter(lambda x, _: f"{x:.0%}"); plt.title("Denial Rate by Procedure"); plt.xlabel("Denial rate"); save("03_denial_rates.png")
    data = summaries["monthly_summary"]
    plt.figure(figsize=(11, 5)); plt.plot(data["claim_month"], data["total_paid"], marker="o", color="#247ba0")
    plt.xticks(rotation=45, ha="right"); plt.title("Monthly Paid Spending"); plt.xlabel(""); plt.ylabel("Total paid ($)"); save("04_monthly_spending.png")
    data = summaries["plan_summary"].sort_values("avg_patient_responsibility")
    plt.figure(figsize=(9, 5)); plt.barh(data["insurance_plan"], data["avg_patient_responsibility"], color="#9b5de5")
    plt.title("Average Patient Responsibility by Plan"); plt.xlabel("Average responsibility ($)"); save("05_patient_responsibility.png")


def money(value: float) -> str:
    return f"${value / 1_000_000:,.2f}M" if value >= 1_000_000 else f"${value:,.0f}"


def write_summary(df: pd.DataFrame, summaries: dict[str, pd.DataFrame], quality: dict, path: Path) -> None:
    procedure, diagnosis, provider, denial, plan, monthly = (summaries[key] for key in
        ["procedure_summary", "diagnosis_summary", "provider_summary", "denial_summary", "plan_summary", "monthly_summary"])
    top_procedure, top_diagnosis, top_provider, top_denial, top_plan = procedure.iloc[0], diagnosis.iloc[0], provider.iloc[0], denial.iloc[0], plan.iloc[0]
    first, last = monthly.iloc[0], monthly.iloc[-1]
    path.write_text(f"""# Healthcare Claims Analytics & Cost Analysis

This report uses synthetic healthcare claims data only; it contains no PHI.

## KPI snapshot

| Metric | Value |
|---|---:|
| Total claims | {len(df):,} |
| Total paid | {money(df['paid_amount'].sum())} |
| Average claim payment | {money(df['paid_amount'].mean())} |
| Overall denial rate | {df['is_denied'].mean():.1%} |
| Average patient responsibility | {money(df['patient_responsibility'].mean())} |

## Main findings

1. **{top_procedure.procedure_description}** has the highest total paid spending: **{money(top_procedure.total_paid)}**.
2. **{top_diagnosis.diagnosis}** generates the most paid spending among diagnoses: **{money(top_diagnosis.total_paid)}**.
3. **{top_provider.provider_id}** has the highest provider spending, with {top_provider.claims:,.0f} claims and **{money(top_provider.total_paid)}** paid.
4. **{top_denial.procedure_description}** has the highest denial rate: **{top_denial.denial_rate:.1%}** across {top_denial.claims:,.0f} claims.
5. **{top_plan.insurance_plan}** has the highest average patient responsibility: **{money(top_plan.avg_patient_responsibility)}**.
6. Monthly spending changed from **{money(first.total_paid)}** in {first.claim_month} to **{money(last.total_paid)}** in {last.claim_month}.

## Data quality

The pipeline read {quality['source_rows']:,} rows, removed {quality['invalid_rows_removed']:,} invalid rows, and analyzed {quality['clean_rows']:,} claims from {quality['date_min']} to {quality['date_max']}.
""", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run healthcare claims analysis.")
    parser.add_argument("--input", type=Path, default=Path("data/raw/healthcare_claims_raw.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--skip-charts", action="store_true", help="Run the data analysis without creating charts.")
    args = parser.parse_args()
    base = args.output_dir; processed = base / "data/processed"; reports = base / "reports"; tables = reports / "tables"; figures = reports / "figures"
    for folder in [processed, reports, tables, figures]: folder.mkdir(parents=True, exist_ok=True)
    df, quality = load_and_clean(args.input)
    df = add_columns(df)
    summaries = build_summaries(df)
    df.to_csv(processed / "healthcare_claims_cleaned.csv", index=False)
    for name, table in summaries.items(): table.to_csv(tables / f"{name}.csv", index=False)
    with open(reports / "data_quality_report.json", "w", encoding="utf-8") as file: json.dump(quality, file, indent=2)
    if not args.skip_charts:
        make_charts(summaries, figures)
    write_summary(df, summaries, quality, reports / "EXECUTIVE_SUMMARY.md")
    print(f"Complete: analyzed {len(df):,} claims.")


if __name__ == "__main__":
    main()
