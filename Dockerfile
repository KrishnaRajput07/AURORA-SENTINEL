# --- Stage 1: Build Frontend ---
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install --frozen-lockfile
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Final Image (GPU Supported) ---
# Using a runtime-only image to save space
FROM nvidia/cuda:11.8.0-base-ubuntu22.04

# Install Python and minimal system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch (GPU version) - This is the largest part
# We use --no-cache-dir to prevent large cache files from staying in the image
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

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
