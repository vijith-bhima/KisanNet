# 🌾 KisanNet — Multimodal AI Platform for Smart Agriculture

> **Empowering farmers with hands-free AI voice guidance, multimodal crop disease diagnosis, hyper-local agronomy advisory, government scheme discovery, and direct market access.**

---

## 🌟 Architecture Overview

KisanNet is built on a high-availability, modular architecture structured across **5 core pillars**:

```text
                               ┌─────────────────────────────┐
                               │   KisanNet Frontend UI      │
                               │   (Next.js 14 / TypeScript) │
                               └──────────────┬──────────────┘
                                              │ Web / Mobile Web
                                              ▼
┌───────────────────────────┐    ┌─────────────────────────────┐    ┌───────────────────────────┐
│ Twilio IVR Phone Service  │───►│  FastAPI Backend API Router │◄───│  LiveKit Voice Agent      │
│ (Feature Phone Call-In)   │    │  (Python 3.11 / Uvicorn)   │    │  (WebRTC Voice Stream)    │
└───────────────────────────┘    └──────────────┬──────────────┘    └───────────────────────────┘
                                                │
       ┌───────────────────┬────────────────────┼───────────────────┬───────────────────┐
       ▼                   ▼                    ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌───────────────────┐   ┌──────────────┐   ┌──────────────┐
│   Pillar 1   │   │   Pillar 2   │   │     Pillar 3      │   │   Pillar 4   │   │   Pillar 5   │
│ Hands-Free   │   │ Hyper-Local  │   │ Government Scheme │   │ Direct Market│   │ Human-in-the │
│ Farm Doc &   │   │ Agronomy RAG │   │   Discovery &     │   │ Linkages &   │   │ Loop Expert  │
│ Multimodal AI│   │   Engine     │   │   Trust Engine    │   │ Price Match  │   │ Escalation   │
└──────────────┘   └──────────────┘   └───────────────────┘   └──────────────┘   └──────────────┘
```

### 🏛️ The 5 Pillars
1. **Pillar 1 — Multimodal Farm Doc & Vision:** ResNet & Gemini Vision model analysis for real-time camera crop disease detection & automated farming logs.
2. **Pillar 2 — Agronomy Advisory & RAG Engine:** Semantic RAG retrieval powered by Google AI Embeddings over verified ICAR & agronomy knowledge bases.
3. **Pillar 3 — Government Scheme Discovery:** Natural language intent classification for scheme matching & regional language translation.
4. **Pillar 4 — Direct Market Linkages:** Peer-to-peer agricultural commodity price discovery & buyer/seller matching.
5. **Pillar 5 — Expert Escalation:** Automated escalation triggers routing uncertain queries to agricultural specialists.

---

## 📁 Repository Directory Structure

```text
KisanNet/
├── Ai/                       # Machine learning datasets, models, prompts & evaluation notebooks
├── Backend/                  # FastAPI web server, LiveKit voice agent, Twilio IVR & RAG pipelines
│   ├── app/                  # FastAPI routers, pillar implementations & GCP clients
│   ├── livekit_agent.py      # Real-time WebRTC AI Voice Agent
│   ├── Dockerfile            # Container build specification
│   ├── render.yaml           # 1-Click Render cloud deployment blueprint
│   └── .env.example          # Backend environment variable template
├── kisannet-frontend/        # Next.js 14 Web Application
│   ├── app/                  # Next.js App Router pages (advisory, market, schemes, weather)
│   ├── components/           # UI components (VoiceOrb, LanguageModal, AuthGuard)
│   ├── vercel.json           # Vercel deployment configuration
│   └── .env.example          # Frontend environment variable template
├── run_all.bat               # Windows batch script to launch all local services
├── requirements.txt          # Python dependencies
├── STRUCTURE.md              # Detailed repository & architecture component manual
└── README.md                 # Project documentation & deployment guide
```

---

## 🚀 Quickstart (Local Development)

### 1. Prerequisites
- **Python:** 3.11 or higher
- **Node.js:** v18+ and `npm`
- **PostgreSQL:** 15+ (with `pgvector` extension enabled) or local SQLite fallback
- **Redis:** 6+ (optional, for caching)

### 2. Environment Setup

#### Backend Configuration
Copy `.env.example` in `Backend/` to `.env`:
```bash
cp Backend/.env.example Backend/.env
```
Fill in your API keys in `Backend/.env`:
- `GOOGLE_API_KEY`: Google AI Studio API Key (for Gemini LLM & Embeddings)
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`: LiveKit WebRTC credentials
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`: Twilio IVR credentials (if using phone call-in)

#### Frontend Configuration
Copy `.env.example` in `kisannet-frontend/` to `.env.local`:
```bash
cp kisannet-frontend/.env.example kisannet-frontend/.env.local
```
Set `NEXT_PUBLIC_API_URL=http://localhost:8000`.

### 3. Running All Services

#### On Windows (One-Click Launch):
Simply double-click [`run_all.bat`](file:///c:/Kissan%20Net/run_all.bat) or run:
```cmd
run_all.bat
```

#### On Linux / macOS (Manual):
```bash
# Terminal 1: Next.js Frontend
cd kisannet-frontend && npm install && npm run dev

# Terminal 2: FastAPI Backend
cd Backend && pip install -r requirements.txt && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 3: LiveKit Voice Agent
cd Backend && python livekit_agent.py dev
```

* **Frontend UI:** `http://localhost:3000`
* **FastAPI Docs:** `http://localhost:8000/docs`

---

## 📤 How to Push to GitHub

1. **Initialize Git Repository (if not already done):**
   ```bash
   git init
   ```

2. **Verify `.gitignore` is active (Ensure secrets are NOT tracked):**
   ```bash
   git status
   ```
   *(Confirm `.env`, `.venv`, and `node_modules` are NOT listed)*

3. **Stage & Commit Files:**
   ```bash
   git add .
   git commit -m "feat: initial KisanNet repository setup with 5 pillars, voice agent & Next.js frontend"
   ```

4. **Connect Remote & Push:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/KisanNet.git
   git branch -M main
   git push -u origin main
   ```

---

## ☁️ Deployment Guide

### 1. Deploy Frontend to Vercel
1. Push your code to GitHub.
2. Import the repository on [Vercel](https://vercel.com).
3. Set the **Root Directory** to `kisannet-frontend`.
4. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL`: Your deployed FastAPI backend URL (e.g. `https://kisannet-backend.onrender.com`)
   - `NEXT_PUBLIC_LIVEKIT_URL`: Your LiveKit Cloud URL
   - `NEXT_PUBLIC_OPENWEATHER_API_KEY`: OpenWeather key
5. Deploy!

### 2. Deploy Backend to Render / Cloud Run

#### Option A: Render (Using `render.yaml`)
1. Connect your GitHub repository to [Render](https://render.com).
2. Render will automatically detect [`Backend/render.yaml`](file:///c:/Kissan%20Net/Backend/render.yaml) and create both:
   - `kisannet-backend-api` (Web Service)
   - `kisannet-voice-agent` (Background Worker)
3. Set environment secrets in the Render Dashboard (`GOOGLE_API_KEY`, `LIVEKIT_URL`, etc.).

#### Option B: GCP Cloud Run (Using Dockerfile)
Build and deploy using Google Cloud Build / Cloud Run:
```bash
cd Backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/kisannet-backend
gcloud run deploy kisannet-backend --image gcr.io/YOUR_PROJECT_ID/kisannet-backend --platform managed --allow-unauthenticated
```

---

## 📄 License & Credits
Built for Smart Agriculture & Hackathon Demonstrations by **KisanNet Team**.
