CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS farm_journals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID DEFAULT gen_random_uuid(),
    channel TEXT NOT NULL DEFAULT 'BROWSER', -- BROWSER, MOBILE, PHONE
    audio_file BYTEA,                        -- Base64 or raw audio payload
    transcription TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    detected_language TEXT NOT NULL DEFAULT 'en-US',
    crop TEXT,
    disease_symptom TEXT,
    region TEXT,
    season TEXT,
    advice_text TEXT,
    advice_source TEXT,
    cost_benefit TEXT,
    is_fully_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_farm_journals_processed ON farm_journals(is_fully_processed);
CREATE INDEX IF NOT EXISTS idx_farm_journals_farmer ON farm_journals(farmer_id);