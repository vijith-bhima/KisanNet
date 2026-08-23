@echo off
echo Starting all KisanNet services...

start "KisanNet Frontend (Next.js)" cmd /k "cd kisannet-frontend && npm run dev"
start "KisanNet Backend API (FastAPI)" cmd /k "cd Backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
start "KisanNet Voice Agent (LiveKit)" cmd /k "cd Backend && python livekit_agent.py dev"

echo All KisanNet services launched in separate terminal windows!
