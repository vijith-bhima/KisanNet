# Multi-stage Dockerfile for KisanNet FastAPI Backend (Cloud Run Ready)
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code, migrations, scripts, and seed data
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY data/ ./data/
COPY start.sh ./start.sh
COPY livekit_agent.py ./livekit_agent.py

# Expose port
EXPOSE 8080

# (Removed Docker HEALTHCHECK to avoid conflicts with Railway/Render dynamic ports)

# Start script for Hugging Face
CMD ["bash", "start.sh"]
