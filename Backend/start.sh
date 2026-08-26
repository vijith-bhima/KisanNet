#!/bin/bash
# KisanNet Start Script for Hugging Face Spaces

echo "Starting KisanNet FastAPI (Port 7860 for Hugging Face Healthcheck)..."
uvicorn app.main:app --host 0.0.0.0 --port 7860 &

echo "Starting KisanNet Voice Agent (LiveKit)..."
python livekit_agent.py start
