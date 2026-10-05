"""Create a deterministic, synthetic healthcare claims source file.

All records are synthetic and contain no PHI.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PROCEDURES = pd.DataFrame(
    [
        ("PROC_101", "Office Visit", "Evaluation", 165, 0.025),
        ("PROC_102", "MRI Scan", "Imaging", 1540, 0.040),
        ("PROC_103", "CT Scan", "Imaging", 1120, 0.035),
        ("PROC_104", "X-Ray", "Imaging", 260, 0.070),
        ("PROC_105", "Blood Panel", "Laboratory", 180, 0.085),
        ("PROC_106", "Physical Therapy", "Therapy", 145, 0.090),
        ("PROC_107", "Emergency Visit", "Emergency", 1950, 0.055),
        ("PROC_108", "Outpatient Surgery", "Surgery", 6500, 0.060),
        ("PROC_109", "Inpatient Stay", "Inpatient", 8900, 0.045),
        ("PROC_110", "Chemotherapy", "Specialty", 7250, 0.080),
        ("PROC_111", "Dialysis", "Specialty", 3250, 0.035),
        ("PROC_112", "Ultrasound", "Imaging", 475, 0.040),
        ("PROC_205", "Specialist Consultation", "Evaluation", 480, 0.178),
        ("PROC_301", "Prior-Authorization Procedure", "Specialty", 2380, 0.294),
        ("PROC_401", "Behavioral Health Visit", "Behavioral", 285, 0.065),
    ],
    columns=["procedure", "procedure_description", "service_type", "base_allowed", "base_denial_rate"],
)

DIAGNOSES = {
    "Evaluation": ["Hypertension", "Type 2 Diabetes", "Hyperlipidemia"],
    "Imaging": ["Low Back Pain", "Osteoarthritis", "Abdominal Pain"],
    "Laboratory": ["Type 2 Diabetes", "Hyperlipidemia", "Anemia"],
    "Therapy": ["Low Back Pain", "Osteoarthritis", "Shoulder Pain"],
    "Emergency": ["Chest Pain", "Abdominal Pain", "Acute Injury"],
    "Surgery": ["Osteoarthritis", "Gallbladder Disease", "Cataract"],
    "Inpatient": ["Heart Failure", "Pneumonia", "Sepsis"],
    "Specialty": ["Cancer", "Kidney Disease", "Autoimmune Disorder"],
    "Behavioral": ["Depression", "Anxiety", "Substance Use Disorder"],
}

PLANS = pd.DataFrame(
    [
        ("Commercial PPO", 1.00, 0.15),
        ("Commercial HMO", 0.92, 0.12),
        ("Medicare Advantage", 0.86, 0.10),
        ("Medicaid", 0.79, 0.04),
        ("High-Deductible Plan", 1.05, 0.28),
    ],
    columns=["insurance_plan", "allowed_factor", "coinsurance"],
)

STATES = np.array(["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI", "AZ", "WA"])


def generate_claims(rows: int, seed: int) -> pd.DataFrame:
    """Return realistic but wholly synthetic claims with seeded patterns."""
    rng = np.random.default_rng(seed)
    provider_count = 800
    patient_count = max(35_000, rows // 3)
    providers = pd.DataFrame(
        {
            "provider_id": [f"P{i:04d}" for i in range(1, provider_count + 1)],
            "provider_state": rng.choice(STATES, provider_count),
            "provider_price_factor": np.clip(rng.lognormal(0, 0.28, provider_count), 0.58, 2.4),
            "provider_denial_lift": np.clip(rng.normal(0, 0.022, provider_count), -0.02, 0.16),
            "provider_volume_weight": rng.lognormal(0, 0.85, provider_count),
        }
    )

    proc_idx = rng.choice(len(PROCEDURES), size=rows, p=PROCEDURES["base_allowed"].to_numpy() ** 0.25 /
                          (PROCEDURES["base_allowed"].to_numpy() ** 0.25).sum())
    proc = PROCEDURES.iloc[proc_idx].reset_index(drop=True)
    provider_idx = rng.choice(provider_count, size=rows, p=providers["provider_volume_weight"] / providers["provider_volume_weight"].sum())
    provider = providers.iloc[provider_idx].reset_index(drop=True)
    plan_idx = rng.choice(len(PLANS), size=rows, p=[0.36, 0.24, 0.19, 0.13, 0.08])
    plan = PLANS.iloc[plan_idx].reset_index(drop=True)

    dates = pd.Timestamp("2023-01-01") + pd.to_timedelta(rng.integers(0, 1096, rows), unit="D")
    diagnoses = [rng.choice(DIAGNOSES[service]) for service in proc["service_type"]]
    allowed = (proc["base_allowed"].to_numpy() * provider["provider_price_factor"].to_numpy() *
               plan["allowed_factor"].to_numpy() * rng.lognormal(0, 0.30, rows))
    allowed = np.round(np.clip(allowed, 35, 150_000), 2)
    billed = np.round(allowed * rng.uniform(1.08, 1.72, rows), 2)
    denial_probability = np.clip(proc["base_denial_rate"].to_numpy() + provider["provider_denial_lift"].to_numpy() +
                                 rng.normal(0, 0.012, rows), 0.005, 0.70)
    denied = rng.random(rows) < denial_probability
    pending = (~denied) & (rng.random(rows) < 0.012)
    patient_resp = np.round(np.minimum(allowed * plan["coinsurance"].to_numpy() * rng.uniform(0.75, 1.25, rows), allowed), 2)
    paid = np.round(np.maximum(allowed - patient_resp, 0), 2)
    paid[denied | pending] = 0
    patient_resp[denied | pending] = 0
    status = np.where(denied, "Denied", np.where(pending, "Pending", "Approved"))

    claims = pd.DataFrame(
        {
            "claim_id": [f"CLM{i:09d}" for i in range(1, rows + 1)],
            "patient_id": [f"PT{i:07d}" for i in rng.integers(1, patient_count + 1, rows)],
            "provider_id": provider["provider_id"].to_numpy(),
            "diagnosis": diagnoses,
            "procedure": proc["procedure"].to_numpy(),
            "procedure_description": proc["procedure_description"].to_numpy(),
            "claim_date": dates.strftime("%Y-%m-%d"),
            "service_type": proc["service_type"].to_numpy(),
            "insurance_plan": plan["insurance_plan"].to_numpy(),
            "billed_amount": billed,
            "allowed_amount": allowed,
            "paid_amount": paid,
            "patient_responsibility": patient_resp,
            "claim_status": status,
            "provider_state": provider["provider_state"].to_numpy(),
        }
    )

    return claims


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic healthcare claims data.")
    parser.add_argument("--rows", type=int, default=250_000, help="Number of claims to synthesize (default: 250,000).")
    parser.add_argument("--seed", type=int, default=20261002, help="Random seed for reproducible output.")
    parser.add_argument("--output", type=Path, default=Path("data/raw/healthcare_claims_raw.csv"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    claims = generate_claims(args.rows, args.seed)
    claims.to_csv(args.output, index=False)
    print(f"Created {len(claims):,} synthetic claims at {args.output}")


if __name__ == "__main__":
    main()
