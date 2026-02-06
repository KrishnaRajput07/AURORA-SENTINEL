FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3.10 -m pip install --upgrade pip

# Install PyTorch (GPU version)
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Copy requirements first for caching
COPY requirements.txt /app/requirements.txt
WORKDIR /app

# Install other dependencies
RUN pip3 install -r requirements.txt

# Copy project files
COPY . /app

# Expose API port
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
