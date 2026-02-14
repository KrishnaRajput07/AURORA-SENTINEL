# --- Stage 1: Build Frontend ---
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install --frozen-lockfile
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Final Image (CPU Optimized for 4GB Limit) ---
FROM python:3.10-slim

# Install system dependencies and clean up in one layer
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only PyTorch (Save ~2.5GB vs CUDA version)
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy requirements & install others
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy project files (Respects .dockerignore)
COPY . .

# Copy frontend build from Stage 1
COPY --from=frontend-builder /frontend/build ./frontend/build

# Expose API port
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
