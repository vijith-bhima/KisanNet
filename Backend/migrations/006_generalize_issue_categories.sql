-- Migration 006: Generalize matching dimensions beyond crop diseases to all issue categories
ALTER TABLE farm_journals ADD COLUMN IF NOT EXISTS issue_category VARCHAR(50);
-- Valid categories: 'CROP_DISEASE', 'PEST', 'IRRIGATION', 'SOIL', 'MARKET_PRICE',
--                   'EQUIPMENT', 'WEATHER', 'GOVT_SCHEME', 'LIVESTOCK', 'POST_HARVEST', 'OTHER'

ALTER TABLE farm_journals ADD COLUMN IF NOT EXISTS issue_subtype VARCHAR(100);
-- General replacement for disease_name across domains (e.g. 'DRIP_SYSTEM_CLOG', 'LOW_MANDI_PRICE', 'PINK_BOLLWORM')

-- Backfill issue_category = 'CROP_DISEASE' and issue_subtype from existing disease_name / disease_symptom
UPDATE farm_journals
SET issue_category = 'CROP_DISEASE',
    issue_subtype = COALESCE(disease_name, disease_symptom)
WHERE (disease_name IS NOT NULL OR disease_symptom IS NOT NULL)
  AND issue_category IS NULL;

CREATE INDEX IF NOT EXISTS idx_journals_issue_category ON farm_journals(issue_category);
CREATE INDEX IF NOT EXISTS idx_journals_issue_subtype ON farm_journals(issue_subtype);
