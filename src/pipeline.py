import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def load_data(file_path):

    df = pd.read_csv(file_path)

    # Clean column names
    df.columns = df.columns.str.strip().str.lower()

    # Convert numbers
    money_columns = [
        "billed_amount",
        "allowed_amount",
        "paid_amount",
        "patient_responsibility"
    ]

    for column in money_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Convert date
    df["claim_date"] = pd.to_datetime(
        df["claim_date"],
        errors="coerce"
    )

    # Remove invalid rows
    invalid = (
        df["claim_date"].isna()
        | df[money_columns].isna().any(axis=1)
        | (df[money_columns] < 0).any(axis=1)
    )

    invalid_rows = invalid.sum()

    df = df[~invalid].copy()

    # Remove duplicate claim IDs
    df = df.drop_duplicates(
        subset="claim_id"
    )

    # Clean text
    for column in df.select_dtypes(
        include="object"
    ).columns:

        df[column] = df[column].str.strip()

    quality = {
        "source_rows": int(invalid_rows + len(df)),
        "invalid_rows_removed": int(invalid_rows),
        "clean_rows": int(len(df)),
        "date_min": str(df["claim_date"].min().date()),
        "date_max": str(df["claim_date"].max().date())
    }

    return df, quality


def add_columns(df):

    df = df.copy()

    # Difference between billed and allowed amount
    df["discount_amount"] = (
        df["billed_amount"]
        - df["allowed_amount"]
    )

    # Percentage paid by patient
    df["patient_share"] = np.where(
        df["allowed_amount"] > 0,
        df["patient_responsibility"]
        / df["allowed_amount"],
        np.nan
    )

    # Month of claim
    df["claim_month"] = (
        df["claim_date"]
        .dt.to_period("M")
        .astype(str)
    )

    # 1 = denied, 0 = not denied
    df["is_denied"] = (
        df["claim_status"] == "Denied"
    ).astype(int)

    return df


def create_summaries(df, output_folder):

    # 1. Spending by procedure
    procedure_summary = (
        df.groupby(
            ["procedure", "procedure_description"]
        )
        .agg(
            claims=("claim_id", "count"),
            total_paid=("paid_amount", "sum"),
            avg_paid=("paid_amount", "mean")
        )
        .reset_index()
        .sort_values(
            "total_paid",
            ascending=False
        )
    )

    # 2. Spending by diagnosis
    diagnosis_summary = (
        df.groupby("diagnosis")
        .agg(
            claims=("claim_id", "count"),
            total_paid=("paid_amount", "sum"),
            avg_paid=("paid_amount", "mean")
        )
        .reset_index()
        .sort_values(
            "total_paid",
            ascending=False
        )
    )

    # 3. Provider summary
    provider_summary = (
        df.groupby(
            ["provider_id", "provider_state"]
        )
        .agg(
            claims=("claim_id", "count"),
            total_paid=("paid_amount", "sum"),
            avg_paid=("paid_amount", "mean"),
            denial_rate=("is_denied", "mean")
        )
        .reset_index()
        .sort_values(
            "total_paid",
            ascending=False
        )
    )

    # 4. Denial summary
    denial_summary = (
        df.groupby(
            ["procedure", "procedure_description"]
        )
        .agg(
            claims=("claim_id", "count"),
            denied_claims=("is_denied", "sum"),
            denial_rate=("is_denied", "mean")
        )
        .reset_index()
        .sort_values(
            "denial_rate",
            ascending=False
        )
    )

    # 5. Insurance plan summary
    plan_summary = (
        df.groupby("insurance_plan")
        .agg(
            claims=("claim_id", "count"),
            avg_patient_responsibility=(
                "patient_responsibility",
                "mean"
            ),
            total_patient_responsibility=(
                "patient_responsibility",
                "sum"
            ),
            avg_patient_share=(
                "patient_share",
                "mean"
            )
        )
        .reset_index()
    )

    # 6. Monthly summary
    monthly_summary = (
        df.groupby("claim_month")
        .agg(
            claims=("claim_id", "count"),
            total_paid=("paid_amount", "sum"),
            avg_paid=("paid_amount", "mean"),
            denial_rate=("is_denied", "mean")
        )
        .reset_index()
        .sort_values("claim_month")
    )

    # 7. Top expensive claims
    top_expensive_claims = (
        df.nlargest(
            100,
            "paid_amount"
        )
        [
            [
                "claim_id",
                "patient_id",
                "provider_id",
                "diagnosis",
                "procedure",
                "claim_date",
                "paid_amount"
            ]
        ]
    )

    summaries = {
        "procedure_summary": procedure_summary,
        "diagnosis_summary": diagnosis_summary,
        "provider_summary": provider_summary,
        "denial_summary": denial_summary,
        "plan_summary": plan_summary,
        "monthly_summary": monthly_summary,
        "top_expensive_claims": top_expensive_claims
    }

    for name, table in summaries.items():

        table.to_csv(
            output_folder / f"{name}.csv",
            index=False
        )

    return summaries


def create_charts(summaries, output_folder):

    plt.figure()

    data = summaries["procedure_summary"].head(10)

    plt.barh(
        data["procedure_description"],
        data["total_paid"]
    )

    plt.xlabel("Total Paid")
    plt.ylabel("Procedure")
    plt.title("Top Procedures by Spending")

    plt.tight_layout()

    plt.savefig(
        output_folder / "01_procedure_spending.png"
    )

    plt.close()


    plt.figure()

    data = summaries["diagnosis_summary"].head(10)

    plt.barh(
        data["diagnosis"],
        data["total_paid"]
    )

    plt.xlabel("Total Paid")
    plt.ylabel("Diagnosis")
    plt.title("Top Diagnoses by Spending")

    plt.tight_layout()

    plt.savefig(
        output_folder / "02_diagnosis_spending.png"
    )

    plt.close()


    plt.figure()

    data = summaries["monthly_summary"]

    plt.plot(
        data["claim_month"],
        data["total_paid"]
    )

    plt.xlabel("Month")
    plt.ylabel("Total Paid")
    plt.title("Monthly Healthcare Spending")

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(
        output_folder / "04_monthly_spending.png"
    )

    plt.close()


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        default="data/raw/healthcare_claims_raw.csv"
    )

    parser.add_argument(
        "--output-dir",
        default="."
    )

    args = parser.parse_args()

    project_folder = Path(args.output_dir)

    processed_folder = (
        project_folder / "data" / "processed"
    )

    reports_folder = (
        project_folder / "reports"
    )

    figures_folder = (
        reports_folder / "figures"
    )

    processed_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    reports_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    figures_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # STEP 1: Load and clean
    df, quality = load_data(
        args.input
    )

    # STEP 2: Add calculated columns
    df = add_columns(df)

    # STEP 3: Save cleaned data
    df.to_csv(
        processed_folder
        / "healthcare_claims_clean.csv",
        index=False
    )

    # STEP 4: Create summaries
    summaries = create_summaries(
        df,
        reports_folder
    )

    # STEP 5: Create charts
    create_charts(
        summaries,
        figures_folder
    )

    # STEP 6: Save quality report
    with open(
        reports_folder
        / "data_quality_report.json",
        "w"
    ) as file:

        json.dump(
            quality,
            file,
            indent=4
        )

    print("Pipeline completed.")
    print(f"Rows analyzed: {len(df)}")


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
