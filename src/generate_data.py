import argparse
from pathlib import Path

import numpy as np
import pandas as pd


# Healthcare procedures
PROCEDURES = [
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
]


DIAGNOSES = {
    "Evaluation": ["Hypertension", "Diabetes", "Back Pain"],
    "Imaging": ["Cancer", "Fracture", "Pneumonia"],
    "Laboratory": ["Diabetes", "Anemia", "Infection"],
    "Therapy": ["Back Pain", "Arthritis", "Injury"],
    "Emergency": ["Sepsis", "Injury", "Chest Pain"],
    "Surgery": ["Cancer", "Heart Failure", "Fracture"],
    "Inpatient": ["Sepsis", "Pneumonia", "Heart Failure"],
    "Specialty": ["Cancer", "Kidney Disease", "Autoimmune Disorder"],
    "Behavioral": ["Anxiety", "Depression", "Stress"],
}


PLANS = [
    ("Commercial PPO", 1.00, 0.15),
    ("Commercial HMO", 0.92, 0.12),
    ("Medicare Advantage", 0.86, 0.10),
    ("Medicaid", 0.79, 0.04),
    ("High-Deductible Plan", 1.05, 0.28),
]


STATES = [
    "CA", "TX", "FL", "NY", "PA", "IL",
    "OH", "GA", "NC", "MI", "AZ", "WA"
]


def generate_claims(number_of_rows, seed):
    np.random.seed(seed)

    data = []

    for i in range(number_of_rows):

        # Choose procedure
        procedure = PROCEDURES[np.random.randint(len(PROCEDURES))]

        procedure_id = procedure[0]
        procedure_name = procedure[1]
        service_type = procedure[2]
        base_price = procedure[3]
        base_denial_rate = procedure[4]

        # Create IDs
        claim_id = f"CLM{i + 1:09d}"
        patient_id = f"PT{np.random.randint(1, 35001):05d}"
        provider_id = f"P{np.random.randint(1, 801):04d}"

        # Other information
        state = np.random.choice(STATES)
        plan = PLANS[np.random.randint(len(PLANS))]

        insurance_plan = plan[0]
        allowed_factor = plan[1]
        coinsurance = plan[2]

        diagnosis = np.random.choice(
            DIAGNOSES[service_type]
        )

        # Random date between 2023 and 2025
        random_days = np.random.randint(0, 1096)
        claim_date = pd.Timestamp("2023-01-01") + pd.Timedelta(
            days=random_days
        )

        # Calculate amounts
        allowed_amount = (
            base_price
            * allowed_factor
            * np.random.uniform(0.8, 1.2)
        )

        allowed_amount = max(allowed_amount, 35)

        billed_amount = (
            allowed_amount
            * np.random.uniform(1.08, 1.72)
        )

        # Decide whether claim is denied
        denial_probability = min(
            base_denial_rate + np.random.uniform(-0.02, 0.02),
            0.70
        )

        denied = np.random.random() < denial_probability

        # Small chance of pending claim
        pending = (
            not denied
            and np.random.random() < 0.012
        )

        # Patient responsibility
        patient_responsibility = (
            allowed_amount
            * coinsurance
            * np.random.uniform(0.75, 1.25)
        )

        patient_responsibility = min(
            patient_responsibility,
            allowed_amount
        )

        if denied or pending:
            paid_amount = 0
            patient_responsibility = 0

        else:
            paid_amount = (
                allowed_amount - patient_responsibility
            )

        # Status
        if denied:
            status = "Denied"
        elif pending:
            status = "Pending"
        else:
            status = "Approved"

        data.append([
            claim_id,
            patient_id,
            provider_id,
            diagnosis,
            procedure_id,
            procedure_name,
            claim_date,
            service_type,
            insurance_plan,
            round(billed_amount, 2),
            round(allowed_amount, 2),
            round(paid_amount, 2),
            round(patient_responsibility, 2),
            status,
            state
        ])

    columns = [
        "claim_id",
        "patient_id",
        "provider_id",
        "diagnosis",
        "procedure",
        "procedure_description",
        "claim_date",
        "service_type",
        "insurance_plan",
        "billed_amount",
        "allowed_amount",
        "paid_amount",
        "patient_responsibility",
        "claim_status",
        "provider_state"
    ]

    return pd.DataFrame(data, columns=columns)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--rows",
        type=int,
        default=250000
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=20261002
    )

    parser.add_argument(
        "--output",
        default="data/raw/healthcare_claims_raw.csv"
    )

    args = parser.parse_args()

    output_file = Path(args.output)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    claims = generate_claims(
        args.rows,
        args.seed
    )

    claims.to_csv(
        output_file,
        index=False
    )

    print(
        f"Created {len(claims)} claims."
    )

    print(
        f"Saved to: {output_file}"
    )


if __name__ == "__main__":
    main()
