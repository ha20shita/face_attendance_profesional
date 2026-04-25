# FastAPI Face Attendance System - Cloud Run Dockerfile

FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for dlib + face_recognition
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    gcc \
    g++ \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libdlib-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better Docker cache)
COPY requirements.txt .

# Upgrade pip and install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

# Create required folders
RUN mkdir -p uploads/students data

# Cloud Run requires port 8080 (but use $PORT env)
EXPOSE 8080

# Health check (VERY IMPORTANT)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
 CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\",8080)}/health')" || exit 1

# Start FastAPI app
# IMPORTANT:
# make sure your file is main.py
# and inside it you have:
# app = FastAPI()

CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
"uvicorn main:app --host 0.0.0.0 --port 8080"]
