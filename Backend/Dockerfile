# Multi-stage Dockerfile for KisanNet FastAPI Backend (Cloud Run Ready)
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

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

# Copy application source code and migrations
COPY app/ ./app/
COPY migrations/ ./migrations/

# Expose port
EXPOSE 8080

# (Removed Docker HEALTHCHECK to avoid conflicts with Railway/Render dynamic ports)

# Start uvicorn server for Cloud Run / Railway
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"
