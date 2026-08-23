# 🏗️ KisanNet Repository Structure & Architecture Manual

This document provides a comprehensive component-by-component mapping of the entire **KisanNet** codebase.

---

## 📂 Root Directory

```text
KisanNet/
├── Ai/                       # Machine learning workspace (datasets, models, prompt engineering)
├── Backend/                  # Python FastAPI web server, LiveKit voice worker & Twilio IVR
├── kisannet-frontend/        # Next.js 14 Web Application (App Router, Tailwind, Framer Motion)
├── scripts/                  # Helper scripts & internal tools
├── .env.example              # Example environment variables placeholder
├── .gitignore                # Comprehensive Git ignore rules (secrets, venvs, node_modules)
├── README.md                 # Production project overview & deployment guide
├── STRUCTURE.md              # Detailed repository structure specification (this file)
├── requirements.txt          # Root Python dependencies
└── run_all.bat               # Windows 1-click startup script for all services
```

---

## 🤖 1. Machine Learning Workspace (`/Ai`)

| File / Subfolder | Purpose & Description |
| :--- | :--- |
| `Ai/models/` | Saved PyTorch / TensorFlow / ONNX model weight checkpoints (e.g. crop disease classifiers). |
| `Ai/datasets/` | Raw and preprocessed agricultural datasets (leaf photos, agronomy CSVs). |
| `Ai/notebooks/` | Jupyter research notebooks (`.ipynb`) for data exploration, Gemini prompt testing & RAG benchmarks. |
| `Ai/prompts/` | Versioned system prompt templates for KisanNet Pillar AI agents. |
| `Ai/rag/` | Offline vector embedding generation and agronomy document chunking scripts. |
| `Ai/evaluation/` | Accuracy, recall, and WER (Word Error Rate) test suites for multilingual voice/text models. |

---

## ⚙️ 2. Backend Service (`/Backend`)

```text
Backend/
├── app/
│   ├── main.py               # FastAPI application initialization & CORS middleware
│   ├── config.py             # Environment settings & configuration loader
│   ├── database.py           # PostgreSQL / AsyncPG connection pool setup
│   ├── auth.py               # Authentication middleware & Firebase token verification
│   ├── google_llm.py         # Google Gemini 2.0 Flash client & structured JSON generators
│   ├── google_embeddings.py  # Vertex AI text-embedding-004 vector generation client
│   ├── google_speech.py      # Google Cloud Speech-to-Text (STT) interface
│   ├── google_tts.py         # Google Cloud Text-to-Speech (TTS) interface
│   ├── google_translate.py   # Google Cloud Translation client for regional Indian languages
│   ├── agentic_research.py   # Autonomous multi-step agricultural research agent
│   ├── local_rag.py          # Local semantic RAG vector retrieval engine
│   ├── trusted_sources.py    # ICAR & KVK verified agronomy source registry
│   ├── twilio_ivr.py         # Interactive Voice Response (IVR) phone call handler
│   ├── twilio_service.py     # Twilio Voice REST API client
│   ├── firestore_client.py   # Google Cloud Firestore database integration
│   ├── bigquery_client.py    # Google Cloud BigQuery vector search integration
│   ├── redis_client.py       # Redis cache client for session & rate limiting
│   ├── pillar1/              # Pillar 1: Multimodal Farm Doc & Vision endpoints
│   ├── pillar2/              # Pillar 2: Hyper-Local Agronomy RAG advisory endpoints
│   ├── pillar3/              # Pillar 3: Government Scheme intent & trust engine
│   ├── pillar4/              # Pillar 4: Direct Market Linkages & P2P price matcher
│   └── pillar5/              # Pillar 5: Expert escalation rules & routing
├── scripts/
│   ├── ingest_knowledge_base.py # Ingestion pipeline for agricultural PDFs & documents
│   └── live_schemes_scraper.py  # Web scraper for live government schemes
├── livekit_agent.py          # Real-Time WebRTC Voice Agent worker (LiveKit RTC + Gemini)
├── Dockerfile                # Multi-stage Docker build config (GCP Cloud Run ready)
├── render.yaml               # Render 1-click cloud deployment blueprint
├── requirements.txt          # Backend Python dependencies
└── .env.example              # Backend environment variable template
```

---

## 💻 3. Frontend Web Application (`/kisannet-frontend`)

```text
kisannet-frontend/
├── app/                      # Next.js 14 App Router Pages
│   ├── layout.tsx            # Root HTML layout with Language & Auth providers
│   ├── page.tsx              # Main Dashboard (Quick stats, voice trigger, advisory)
│   ├── login/page.tsx        # Sign-in page (Google Auth & Mobile OTP)
│   ├── signup/page.tsx       # Sign-up & farmer onboarding page
│   ├── advisory/page.tsx     # Hyper-local agronomy advisory & crop doctor
│   ├── market/page.tsx       # Live Mandi commodity rates & peer trade
│   ├── schemes/page.tsx      # Government scheme search & eligibility checker
│   ├── weather/page.tsx      # 7-day hyperlocal weather forecast & farming tips
│   └── profile/page.tsx      # Farmer profile, farm acres & crop settings
├── components/               # Reusable React UI Components
│   ├── AuthGuard.tsx         # Route protection & automatic sign-in redirect
│   ├── SplashScreen.tsx      # Initial brand splash screen
│   ├── BottomNav.tsx         # Mobile bottom navigation bar
│   ├── Sidebar.tsx           # Desktop sidebar navigation (with logo)
│   ├── LanguageModal.tsx     # Multilingual selector modal (10 Indian languages)
│   └── VoiceAssistantModal.tsx # WebRTC Voice AI Assistant modal (with LiveKit & logo)
├── context/
│   └── LanguageContext.tsx   # React Context for app-wide language state & translation lookup
├── utils/
│   ├── translations.ts       # Multilingual dictionaries for 10 regional Indian languages
│   ├── api.ts                # Axios/Fetch client for Backend API calls
│   ├── weatherService.ts     # Weather API integration service
│   └── speech.ts             # Browser Web Speech synthesis fallback
├── lib/
│   ├── firebase.ts           # Firebase App & Auth SDK initialization
│   └── images.ts             # Asset mapping & image helper utilities
├── public/
│   ├── kisannet_logo.png     # Primary KisanNet brand logo
│   └── assets/               # Static image assets
├── vercel.json               # Vercel deployment configuration
├── package.json              # Node.js dependencies & npm scripts
└── .env.example              # Frontend environment variable template
```

---

## ⚙️ 4. Local Execution Workflow

Running [`run_all.bat`](file:///c:/Kissan%20Net/run_all.bat) launches 3 independent background processes:

```cmd
run_all.bat
```

1. **Frontend Server:** Runs Next.js on `http://localhost:3000`
2. **FastAPI Backend:** Runs FastAPI on `http://localhost:8000`
3. **Voice Worker:** Runs LiveKit WebRTC AI Voice Agent

---

## 🌐 5. Supported Languages

KisanNet features full internationalization (`i18n`) supporting:
- 🌐 **English (`en`)** *(Default)*
- 🌾 **Telugu (`te`)**
- 🇮🇳 **Hindi (`hi`)**
- 🌱 **Tamil (`ta`)**
- 🚜 **Kannada (`kn`)**
- 🌿 **Marathi (`mr`)**
- 🌴 **Malayalam (`ml`)**
- 🌾 **Punjabi (`pa`)**
- 🌿 **Bengali (`bn`)**
- 🌱 **Gujarati (`gu`)**
