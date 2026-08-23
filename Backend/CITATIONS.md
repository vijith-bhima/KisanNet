# CITATIONS & THIRD-PARTY ATTRIBUTIONS

Per BRICS AgriTech Hackathon Rule 03, the following open-source packages, libraries, and Google AI services were utilized in building the KisanNet backend server:

## 1. Google AI Stack & SDKs
- **google-generativeai / google-genai**: Official Python SDK for Google Gemini API (`gemini-2.0-flash`). Used for structured field extraction and RAG answer synthesis via `response_schema`.
  - License: Apache 2.0
  - Ref: https://github.com/google-gemini/generative-ai-python
- **google-cloud-speech**: Official Google Cloud Speech-to-Text client library for voice transcription.
  - License: Apache 2.0
  - Ref: https://cloud.google.com/speech-to-text/docs
- **google-cloud-texttospeech**: Official Google Cloud Text-to-Speech client library for audio synthesis.
  - License: Apache 2.0
  - Ref: https://cloud.google.com/text-to-speech/docs
- **google-cloud-aiplatform**: Official Vertex AI SDK for 768-dimensional `text-embedding-004` generation.
  - License: Apache 2.0
- **google-cloud-translate**: Official Google Cloud Translation API client.
  - License: Apache 2.0

## 2. Core Backend Framework & Database
- **FastAPI**: Modern, fast web framework for building APIs with Python 3.11+.
  - License: MIT
  - Ref: https://github.com/fastapi/fastapi
- **Uvicorn**: ASGI web server implementation.
  - License: BSD 3-Clause
- **SQLAlchemy 2.0**: Python SQL toolkit and Object Relational Mapper (Async engine & session).
  - License: MIT
- **pgvector & pgvector-python**: Vector similarity search extension for PostgreSQL (HNSW index support).
  - License: PostgreSQL License
  - Ref: https://github.com/pgvector/pgvector-python
- **asyncpg**: Async PostgreSQL database driver for Python.
  - License: Apache 2.0
- **redis-py**: Python interface to Redis key-value store.
  - License: MIT

## 3. Mathematical & Algorithmic Foundations
- **Wilson Score Interval**: Adjusted Wald interval for Bernoulli parameters (95% confidence lower bound).
  - Ref: Wilson, E. B. (1927). "Probabilistic Inference and Most Probable Values". Journal of the American Statistical Association, 22(158), 209-212.
- **Laplace Smoothing for Beta-Binomial Conjugate Prior**: Used for Bayesian advisory trust score updates.
