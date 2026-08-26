#!/bin/bash
# KisanNet Smart Start Script
# Set SERVICE_TYPE=voice in Railway env vars for the voice agent service.
# Leave it unset (or set to "api") for the FastAPI backend service.

if [ "$SERVICE_TYPE" = "voice" ]; then
    echo "Starting KisanNet Voice Agent (LiveKit)..."
    python livekit_agent.py start
else
    echo "Starting KisanNet Backend API (FastAPI)..."
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
fi
