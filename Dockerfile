# ═══════════════════════════════════════════════════
# Personal Research Assistant Agent — Backend Dockerfile
# (Optimized for CPU to reduce size from 8GB to <1GB)
# ═══════════════════════════════════════════════════

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file
COPY backend/requirements.txt .

# --- SIZE OPTIMIZATION STEP ---
# Force install CPU-only torch to avoid 7GB of GPU drivers
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Create persistent data directories
RUN mkdir -p data chroma_db

EXPOSE 8000

# Healthcheck using curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
