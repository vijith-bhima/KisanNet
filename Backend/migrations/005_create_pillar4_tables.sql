-- Migration 005: Pillar 4 Schema (Auto-Matching With Past Solvers)
CREATE EXTENSION IF NOT EXISTS vector;

-- Ensure farmers table exists with necessary solver contact details
CREATE TABLE IF NOT EXISTS farmers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,
  phone_number VARCHAR(20),
  village VARCHAR(100),
  region VARCHAR(50),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trust scores metrics bridge columns for 1:1 join with advice_identifier
ALTER TABLE trust_scores ADD COLUMN IF NOT EXISTS wilson_lower_bound FLOAT DEFAULT 0.0;
ALTER TABLE trust_scores ADD COLUMN IF NOT EXISTS bayesian_score FLOAT DEFAULT 0.0;
ALTER TABLE trust_scores ADD COLUMN IF NOT EXISTS total_unique_farmers INTEGER DEFAULT 0;

-- Farm journals structured and solution attributes
ALTER TABLE farm_journals ADD COLUMN IF NOT EXISTS crop_type VARCHAR(50);
ALTER TABLE farm_journals ADD COLUMN IF NOT EXISTS disease_name VARCHAR(100);
ALTER TABLE farm_journals ADD COLUMN IF NOT EXISTS region VARCHAR(50);
ALTER TABLE farm_journals ADD COLUMN IF NOT EXISTS season VARCHAR(20); -- 'KHARIF', 'RABI', 'SUMMER'
ALTER TABLE farm_journals ADD COLUMN IF NOT EXISTS solution_text TEXT;
-- Written by Pillar 2 (or backfilled by Pillar 3) using the SAME resolution
-- logic as TrustEngine._resolve_advice_identifier() in Pillar 3.
ALTER TABLE farm_journals ADD COLUMN IF NOT EXISTS advice_identifier VARCHAR(300);
ALTER TABLE farm_journals ADD COLUMN IF NOT EXISTS observation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Solution embeddings table for semantic vector similarity fallback (384-dim all-MiniLM-L6-v2)
CREATE TABLE IF NOT EXISTS solution_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  journal_id UUID REFERENCES farm_journals(id) ON DELETE CASCADE UNIQUE,
  farmer_id UUID REFERENCES farmers(id) ON DELETE CASCADE,
  solution_text TEXT NOT NULL,
  embedding VECTOR(384) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_solution_embeddings_cosine
  ON solution_embeddings USING hnsw (embedding vector_cosine_ops);

-- Farmer connections tracking table for browser and mobile calls/SMS
CREATE TABLE IF NOT EXISTS farmer_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_farmer_id UUID REFERENCES farmers(id) ON DELETE CASCADE,
  target_farmer_id UUID REFERENCES farmers(id) ON DELETE CASCADE,
  journal_id UUID REFERENCES farm_journals(id) ON DELETE CASCADE,
  channel VARCHAR(10) NOT NULL,          -- 'BROWSER' or 'MOBILE'
  connection_method VARCHAR(12),         -- 'NUMBER_SHOWN', 'BRIDGED_CALL', 'SMS_FALLBACK'
  call_status VARCHAR(20),               -- Twilio call status, mobile only
  connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  feedback_given BOOLEAN DEFAULT FALSE,
  UNIQUE(source_farmer_id, target_farmer_id, journal_id)
);

CREATE INDEX IF NOT EXISTS idx_journals_crop ON farm_journals(crop_type);
CREATE INDEX IF NOT EXISTS idx_journals_disease ON farm_journals(disease_name);
CREATE INDEX IF NOT EXISTS idx_journals_region ON farm_journals(region);
CREATE INDEX IF NOT EXISTS idx_journals_season ON farm_journals(season);
CREATE INDEX IF NOT EXISTS idx_journals_advice_id ON farm_journals(advice_identifier);
CREATE INDEX IF NOT EXISTS idx_connections_source ON farmer_connections(source_farmer_id);
