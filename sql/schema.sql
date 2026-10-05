-- MySQL 8+ schema. Apply this before src/load_to_mysql.py.
CREATE DATABASE IF NOT EXISTS claims_intelligence;
USE claims_intelligence;

DROP TABLE IF EXISTS claims;
CREATE TABLE claims (
    claim_id VARCHAR(32) PRIMARY KEY,
    patient_id VARCHAR(32) NOT NULL,
    provider_id VARCHAR(20) NOT NULL,
    diagnosis VARCHAR(100) NOT NULL,
    procedure VARCHAR(20) NOT NULL,
    procedure_description VARCHAR(120) NULL,
    claim_date DATE NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    insurance_plan VARCHAR(80) NOT NULL,
    billed_amount DECIMAL(14,2) NOT NULL,
    allowed_amount DECIMAL(14,2) NOT NULL,
    paid_amount DECIMAL(14,2) NOT NULL,
    patient_responsibility DECIMAL(14,2) NOT NULL,
    claim_status VARCHAR(20) NOT NULL,
    provider_state CHAR(2) NOT NULL,
    claim_month CHAR(7) NOT NULL,
    is_denied TINYINT NOT NULL,
    discount_amount DECIMAL(14,2) NOT NULL,
    patient_share DECIMAL(10,6) NULL,
    INDEX idx_claim_date (claim_date),
    INDEX idx_provider_date (provider_id, claim_date),
    INDEX idx_procedure_status (procedure, claim_status),
    INDEX idx_patient_procedure_date (patient_id, procedure, claim_date),
    INDEX idx_state_provider (provider_state, provider_id)
);
