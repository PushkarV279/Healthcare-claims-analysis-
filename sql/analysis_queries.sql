-- Healthcare Claims Analytics: MySQL 8+ query examples
USE claims_intelligence;

-- 1. Which procedures have the highest total spending?
SELECT procedure, procedure_description, COUNT(*) AS claims,
       ROUND(SUM(paid_amount), 2) AS total_paid,
       ROUND(AVG(paid_amount), 2) AS avg_paid
FROM claims
GROUP BY procedure, procedure_description
ORDER BY total_paid DESC
LIMIT 10;

-- 2. Which diagnoses generate the most spending?
SELECT diagnosis, COUNT(*) AS claims, ROUND(SUM(paid_amount), 2) AS total_paid
FROM claims
GROUP BY diagnosis
ORDER BY total_paid DESC;

-- 3. Provider spending and denial rate. HAVING removes very small provider groups.
SELECT provider_id, provider_state, COUNT(*) AS claims,
       ROUND(SUM(paid_amount), 2) AS total_paid,
       ROUND(AVG(paid_amount), 2) AS avg_paid,
       ROUND(100 * AVG(is_denied), 2) AS denial_rate_pct
FROM claims
GROUP BY provider_id, provider_state
HAVING COUNT(*) >= 30
ORDER BY total_paid DESC;

-- 4. Which procedures have the highest denial rate?
SELECT procedure, procedure_description, COUNT(*) AS claims,
       SUM(is_denied) AS denied_claims,
       ROUND(100 * AVG(is_denied), 2) AS denial_rate_pct
FROM claims
GROUP BY procedure, procedure_description
HAVING COUNT(*) >= 100
ORDER BY denial_rate_pct DESC;

-- 5. Patient responsibility by insurance plan.
SELECT insurance_plan, COUNT(*) AS claims,
       ROUND(AVG(patient_responsibility), 2) AS avg_patient_responsibility,
       ROUND(SUM(patient_responsibility), 2) AS total_patient_responsibility
FROM claims
GROUP BY insurance_plan
ORDER BY avg_patient_responsibility DESC;

-- 6. Monthly spending: separates claim volume from average cost.
SELECT claim_month, COUNT(*) AS claims,
       ROUND(SUM(paid_amount), 2) AS total_paid,
       ROUND(AVG(paid_amount), 2) AS avg_paid,
       ROUND(100 * AVG(is_denied), 2) AS denial_rate_pct
FROM claims
GROUP BY claim_month
ORDER BY claim_month;

-- 7. The most expensive individual claims (basic WHERE and ORDER BY).
SELECT claim_id, patient_id, provider_id, diagnosis, procedure, claim_date, paid_amount
FROM claims
WHERE paid_amount > 5000
ORDER BY paid_amount DESC
LIMIT 25;

-- 8. CASE groups claims into simple payment bands.
SELECT CASE
         WHEN paid_amount < 500 THEN 'Under $500'
         WHEN paid_amount < 2000 THEN '$500 to $1,999'
         WHEN paid_amount < 5000 THEN '$2,000 to $4,999'
         ELSE '$5,000 and above'
       END AS payment_band,
       COUNT(*) AS claims,
       ROUND(SUM(paid_amount), 2) AS total_paid
FROM claims
GROUP BY payment_band
ORDER BY total_paid DESC;

-- 9. JOIN example. Create a small provider lookup from the claims table once.
CREATE TABLE IF NOT EXISTS provider_reference AS
SELECT provider_id, MIN(provider_state) AS provider_state
FROM claims
GROUP BY provider_id;

SELECT p.provider_state, c.provider_id, COUNT(*) AS claims, ROUND(SUM(c.paid_amount), 2) AS total_paid
FROM claims c
JOIN provider_reference p ON c.provider_id = p.provider_id
GROUP BY p.provider_state, c.provider_id
ORDER BY total_paid DESC;

-- 10. One advanced example: rank providers by total paid within each state.
WITH provider_spending AS (
  SELECT provider_state, provider_id, SUM(paid_amount) AS total_paid
  FROM claims
  GROUP BY provider_state, provider_id
), ranked_providers AS (
  SELECT provider_state, provider_id, total_paid,
         DENSE_RANK() OVER (PARTITION BY provider_state ORDER BY total_paid DESC) AS spending_rank
  FROM provider_spending
)
SELECT provider_state, provider_id, ROUND(total_paid, 2) AS total_paid, spending_rank
FROM ranked_providers
WHERE spending_rank <= 3
ORDER BY provider_state, spending_rank;
