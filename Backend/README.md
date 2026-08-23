# KisanNet — Backend Server API (Pillars 1–4)

**BRICS AgriTech Hackathon — Problem Statement 4: AgriN / Regenerative Agricultural Intelligence**

KisanNet is a voice-first agricultural intelligence platform engineered for hands-free farm documentation, RAG-grounded advisory generation, voice-driven community trust scoring, and database-native peer matchmaking across BRICS nations.

---

## 1. 100% Google AI Native Architecture & Matchmaking Stack

This backend server is built natively on the Google AI stack in full compliance with hackathon regulations:

*   **Google Gemini 2.0 Flash (`google-genai` SDK)**: Drives structured field extraction from farmer voice logs and synthesizes RAG advisories using controlled JSON output (`response_schema`).
*   **Google Cloud Speech-to-Text (`google-cloud-speech`)**: Transcribes multi-lingual farmer audio inputs using per-farmer `language_code` and automatic punctuation, utilizing native `[0.0, 1.0]` confidence scores.
*   **Google Cloud Text-to-Speech (`google-cloud-texttospeech`)**: Synthesizes localized voice prompts for farmers in their native dialect.
*   **Google Vertex AI / GenAI Embeddings (`text-embedding-004`)**: Generates 768-dimensional text embeddings stored directly in PostgreSQL via `pgvector` with HNSW cosine index optimization (`vector_cosine_ops`).
*   **Pillar 4 Solver Matchmaking (`sentence-transformers` 384-dim + pgvector HNSW)**: Matches farmers with past solvers using structured filtering and semantic fallback vector similarity, backed by Twilio voice call bridging and SMS alerts.
*   **Google Cloud Translation API (`google-cloud-translate`)**: Provides cross-lingual translation across BRICS languages.

---

## 2. Quickstart & Local Setup

### Prerequisites
*   Python 3.11+
*   PostgreSQL 15+ with `pgvector` extension enabled (`CREATE EXTENSION vector;`)
*   Redis server (for Pillar 3 retry & rate-limiting counters)

### Setup Steps
```bash
# 1. Navigate to backend workspace
cd "c:/Kissan Net/Backend"

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env to add your GOOGLE_API_KEY, DATABASE_URL, and REDIS_URL
```

### Database Migrations
Apply plain numbered SQL migrations in order:
```bash
psql -U postgres -d kisannet -f migrations/001_create_farm_journals_table.sql
psql -U postgres -d kisannet -f migrations/002_create_knowledge_base_table.sql
psql -U postgres -d kisannet -f migrations/003_create_trust_scores_table.sql
psql -U postgres -d kisannet -f migrations/004_create_regions_table.sql
psql -U postgres -d kisannet -f migrations/005_create_pillar4_tables.sql
psql -U postgres -d kisannet -f migrations/006_generalize_issue_categories.sql
```

### Running Locally
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```
*   **Interactive Swagger Documentation**: [http://localhost:8080/docs](http://localhost:8080/docs)
*   **OpenAPI Schema**: [http://localhost:8080/openapi.json](http://localhost:8080/openapi.json)

---

## 3. Containerization & One-Line Cloud Run Deployment

Ship to container runtime or Google Cloud Run in one command:

```bash
# Build Docker image
docker build -t kisannet-backend .

# Run locally on port 8080
docker run -p 8080:8080 --env-file .env kisannet-backend

# Deploy to Google Cloud Run
gcloud run deploy kisannet-backend --source . --region us-central1 --allow-unauthenticated
```

---

## 4. Mapping to Judging Criteria (25% Weight Each)

*   **AI / Technical Execution (25%)**: 100% Google AI Native integration (`google_llm.py`, `google_speech.py`, `google_tts.py`, `google_embeddings.py`). Structured output schema constraints enforce strict JSON schemas without free-text hallucination risks. PostgreSQL `pgvector` HNSW index speeds vector retrieval.
*   **Deployability & Scalability (25%)**: Fully containerized Dockerfile optimized for Google Cloud Run. Async SQLAlchemy 2.0 + asyncpg pool, Redis retry tracking, stateless Twilio webhooks, and CORS `allow_origins=["*"]` for instant frontend binding.
*   **Cross-Border Applicability (20%)**: Dynamic language dictionary structure (`VoiceIntentClassifier`), configurable `regions` table, and zero hardcoded crop/disease enums.
*   **Innovation & Impact (30%)**: Voice-first design for illiterate or semi-literate smallholder farmers, combined with Bayesian + Wilson Lower Bound trust scoring to prevent misinformation.

---

## 5. Cross-Border BRICS Piloting Note

KisanNet is designed from the ground up for seamless cross-border deployment across all BRICS member nations (India, Brazil, Russia, China, South Africa, Egypt, Ethiopia, Iran, UAE). 

To pilot KisanNet in another BRICS country (e.g., Brazil or South Africa):
1. **Language Pack Swap**: Simply add a dictionary entry to `app/pillar3/intent_classifier.py` for target ISO language codes (`pt-BR`, `zh-CN`, `ru-RU`, `ar-SA`). The negation-first regex engine handles intent classification automatically without touching business logic.
2. **KVK / Expert Routing Taxonomy**: Update the `regions` database table with local agricultural extensions (e.g., EMBRAPA in Brazil, ARC in South Africa) and contact endpoints.
3. **Taxonomy & Vector Ingestion**: Hot-reload local scientific documents via `POST /api/v1/pillar2/knowledge/ingest`. Vector embeddings (`text-embedding-004`) work seamlessly across multi-lingual content in PostgreSQL `pgvector`.

---

## 6. Known Hackathon Shortcuts & Notes
*   **Authentication**: Firebase Authentication dependency `app/auth.py` includes a mock fallback (`X-Farmer-ID` and `X-Expert-ID` headers or default UUIDs) for rapid hackathon testing without mandatory auth login walls.
