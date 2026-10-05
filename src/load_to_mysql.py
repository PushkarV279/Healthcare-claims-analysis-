import argparse
import os

import pandas as pd
from sqlalchemy import create_engine


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        default="data/processed/healthcare_claims_clean.csv"
    )

    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL")
    )

    args = parser.parse_args()

    # Check database connection information
    if not args.database_url:

        print(
            "DATABASE_URL is not set."
        )

        return

    # Read cleaned CSV
    df = pd.read_csv(
        args.input,
        parse_dates=["claim_date"]
    )

    # Create database engine
    engine = create_engine(
        args.database_url
    )

    # Send dataq to MySQL
    df.to_sql(
        "claims",
        engine,
        if_exists="append",
        index=False,
        chunksize=10000
    )

    print(
        f"Loaded {len(df)} rows into MySQL."
    )


if __name__ == "__main__":
    main()
