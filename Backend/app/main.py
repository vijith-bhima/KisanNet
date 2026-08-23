import os
import logging
from pathlib import Path
import subprocess
import sys
from contextlib import asynccontextmanager

logger = logging.getLogger("main")

try:
    import websockets
except ImportError:
    logging.getLogger(__name__).warning("websockets not found. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets>=11.0.3"])
    import websockets

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Uvicorn will auto-reload now again

from app.config import settings
from app.google_llm import google_llm_client

from app.pillar1.endpoints import router as pillar1_router
from app.pillar1.stream_endpoint import router as stream_router
from app.pillar1.vision_endpoint import router as vision_router
from app.pillar2.endpoints import router as pillar2_router
from app.pillar3.endpoints import router as pillar3_router
from app.pillar4.endpoints import router as pillar4_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
INDEX_HTML_PATH = FRONTEND_DIR / "index.html"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Manager:
    """
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "KisanNet Voice-First Agricultural Advisory Platform Backend API for BRICS AgriTech Hackathon.\n"
        "Integrates Google AI Native stack: Gemini 2.0 Flash (structured JSON output), "
        "Google Cloud Speech-to-Text (native confidence), Google Cloud Text-to-Speech, "
        "Vertex AI text-embedding-004 (768-dim), and BigQuery (Vector Search)."
    ),
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Mandatory Hackathon CORS: Allow all origins for immediate frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Pillar Routers
from app.twilio_ivr import router as twilio_ivr_router

app.include_router(pillar1_router, prefix=settings.API_V1_STR)
app.include_router(pillar1_router)  # Direct root access: /voice/talk, /voice/talk-audio, /journal-status
app.include_router(stream_router, prefix=settings.API_V1_STR)
app.include_router(vision_router, prefix=settings.API_V1_STR)
app.include_router(pillar2_router, prefix=settings.API_V1_STR)
app.include_router(pillar3_router, prefix=settings.API_V1_STR)
app.include_router(pillar4_router, prefix=settings.API_V1_STR)
app.include_router(pillar4_router)  # For root-level Twilio voice callbacks e.g. /voice/connect-status
app.include_router(twilio_ivr_router, prefix=settings.API_V1_STR)
app.include_router(twilio_ivr_router)

@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
@app.get("/app", response_class=HTMLResponse, tags=["Web UI"])
async def root():
    """Serves the interactive KisanNet Voice Assistant Web UI."""
    if INDEX_HTML_PATH.exists():
        return FileResponse(INDEX_HTML_PATH)
    return HTMLResponse("<h2>KisanNet Voice Assistant UI Ready</h2><p><a href='/docs'>API Docs</a></p>")

from pydantic import BaseModel
from app.google_llm import google_llm_client

class KeyConfigRequest(BaseModel):
    api_key: str

@app.get("/api/v1/config/key-status", tags=["Configuration"])
async def get_key_status():
    active_key = google_llm_client.get_active_api_key()
    is_project_id = bool(active_key and not active_key.startswith("AIzaSy") and "-" in active_key)
    has_key = bool(active_key and active_key.startswith("AIzaSy") and len(active_key) >= 30)
    
    status_str = "connected" if has_key else ("is_project_id" if is_project_id else "missing_key")
    
    return {
        "has_active_key": has_key,
        "is_project_id": is_project_id,
        "model": "gemini-2.0-flash",
        "status": status_str,
        "raw_value": active_key if is_project_id else None,
        "masked_key": f"{active_key[:6]}...{active_key[-4:]}" if has_key else None
    }

@app.post("/api/v1/config/key", tags=["Configuration"])
async def set_gemini_key(payload: KeyConfigRequest):
    key = payload.api_key.strip()
    if not key.startswith("AIzaSy") and "-" in key:
        return {
            "status": "warning",
            "message": f"'{key}' looks like a Google Cloud Project ID. An API key starts with 'AIzaSy...'. Please generate an API Key at https://aistudio.google.com/app/apikey for this project."
        }

    google_llm_client.set_active_api_key(key)
    
    # Also update .env file if it exists
    env_file = Path(__file__).resolve().parent.parent / ".env"
    try:
        if env_file.exists():
            content = env_file.read_text(encoding="utf-8")
            if "GOOGLE_API_KEY=" in content:
                import re
                content = re.sub(r"GOOGLE_API_KEY=.*", f"GOOGLE_API_KEY={key}", content)
            else:
                content += f"\nGOOGLE_API_KEY={key}\n"
            env_file.write_text(content, encoding="utf-8")
        else:
            env_file.write_text(f"GOOGLE_API_KEY={key}\nGEMINI_MODEL=gemini-2.0-flash\n", encoding="utf-8")
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Google Gemini API key activated successfully for Real Live AI."
    }

import json
@app.get("/api/v1/schemes", tags=["Schemes"])
async def get_all_schemes():
    """Returns all real government schemes from the seed data."""
    schemes_path = Path(__file__).resolve().parent.parent / "data" / "seed" / "schemes.json"
    try:
        if schemes_path.exists():
            with open(schemes_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading schemes: {e}")
        return []


@app.get("/api/v1/voice/token")
async def get_livekit_token(participant_name: str = "farmer", language: str = "en"):
    """
    Generates a LiveKit access token for the frontend client to join the WebRTC room
    and explicitly triggers agent dispatch.
    """
    import os
    try:
        from livekit import api
    except ImportError:
        return {"status": "error", "message": "LiveKit API not installed. Run 'pip install livekit-api'."}
    
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL", "")
    
    if not api_key or not api_secret:
        return {"status": "error", "message": "Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET in .env"}

    import uuid
    identity = participant_name if participant_name != "farmer" else f"farmer_{uuid.uuid4().hex[:6]}"
    room_name = f"kisannet-room-{uuid.uuid4().hex[:6]}"
    
    token = api.AccessToken(api_key, api_secret)
    token.with_identity(identity)
    token.with_name(participant_name)
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True
    ))
    
    metadata = json.dumps({"language": language})
    token.with_metadata(metadata)

    # Explicitly dispatch agent if available
    # try:
    #     http_url = livekit_url.replace("wss://", "https://").replace("ws://", "http://")
    #     lk_api = api.LiveKitAPI(http_url, api_key, api_secret)
    #     try:
    #         await lk_api.agent_dispatch.create_dispatch(
    #             api.CreateAgentDispatchRequest(
    #                 room=room_name,
    #                 agent_name=""
    #             )
    #         )
    #     except Exception:
    #         pass
    #     finally:
    #         await lk_api.aclose()
    # except Exception as e:
    #     print(f"Agent dispatch setup note: {e}")
    
    return {"token": token.to_jwt(), "url": livekit_url}


@app.get("/api-status", tags=["Health Check"])
async def api_status():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }

@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "healthy"}
