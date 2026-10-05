"""Load the cleaned claims extract into MySQL after applying sql/schema.sql."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


def main() -> None:
    parser = argparse.ArgumentParser(description="Load cleaned claims to MySQL.")
    parser.add_argument("--input", type=Path, default=Path("data/processed/healthcare_claims_cleaned.csv"))
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"), help="Example: mysql+pymysql://user:password@host:3306/claims_intelligence")
    parser.add_argument("--if-exists", choices=["append", "replace", "fail"], default="append")
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("Provide --database-url or set DATABASE_URL. Run sql/schema.sql first.")
    claims = pd.read_csv(args.input, parse_dates=["claim_date"])
    engine = create_engine(args.database_url, pool_pre_ping=True)
    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))
        claims.to_sql("claims", connection, if_exists=args.if_exists, index=False, chunksize=10_000, method="multi")
    print(f"Loaded {len(claims):,} claims into MySQL table claims.")


if __name__ == "__main__":
    main()
