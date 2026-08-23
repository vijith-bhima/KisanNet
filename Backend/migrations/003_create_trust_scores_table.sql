-- Create the Trust Scores Materialized View in BigQuery
-- Implements Bayesian Average and Wilson Score Interval
-- As per v6.0 specification

CREATE OR REPLACE MATERIALIZED VIEW `kisannet.trust_scores` AS
SELECT 
    j.ai_source AS advice_identifier,
    j.ai_source AS source_document,
    JSON_EXTRACT_SCALAR(j.cost_benefit_json, '$.treatment') AS treatment_name,
    COUNT(DISTINCT f.farmer_id) AS total_unique_farmers,
    COUNTIF(f.feedback = 1) AS positive_votes,
    COUNTIF(f.feedback = 2) AS negative_votes,
    (
        (COUNTIF(f.feedback = 1) * 1.0 / NULLIF(COUNT(DISTINCT f.farmer_id), 0) * COUNT(DISTINCT f.farmer_id)) 
        + (5 * 0.55)
    ) / NULLIF(COUNT(DISTINCT f.farmer_id) + 5, 0) AS bayesian_score,
    (
        (COUNTIF(f.feedback = 1) * 1.0 / NULLIF(COUNT(DISTINCT f.farmer_id), 0)) 
        + (POW(1.96, 2) / (2 * COUNT(DISTINCT f.farmer_id))) 
        - 1.96 * SQRT(
            (COUNTIF(f.feedback = 1) * 1.0 / NULLIF(COUNT(DISTINCT f.farmer_id), 0) * 
             (1 - COUNTIF(f.feedback = 1) * 1.0 / NULLIF(COUNT(DISTINCT f.farmer_id), 0)) 
             + POW(1.96, 2) / (4 * POW(COUNT(DISTINCT f.farmer_id), 2))
            ) / NULLIF(COUNT(DISTINCT f.farmer_id), 0)
        )
    ) / (1 + POW(1.96, 2) / NULLIF(COUNT(DISTINCT f.farmer_id), 0)) AS wilson_lower_bound,
    CURRENT_TIMESTAMP() AS last_updated
FROM `kisannet.farm_journals_analytics` j
LEFT JOIN `kisannet.answer_feedback` f ON j.id = f.journal_id
WHERE j.ai_source IS NOT NULL
  AND f.feedback IS NOT NULL
GROUP BY j.ai_source, treatment_name;
