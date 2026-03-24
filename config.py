import os

# -------------------------------------------------------------------
# AURORA SENTINEL: AI MODEL CONFIGURATION
# -------------------------------------------------------------------

# Set the primary Vision-Language Model provider.
# Options: 
# "ollama_cloud"   -> Use Ollama (e.g., qwen3-vl:235b-cloud) as primary
# "qwen2vl_local"  -> Use local PyTorch-based Qwen2-VL as primary
PRIMARY_VLM_PROVIDER = os.getenv("PRIMARY_VLM_PROVIDER", "ollama_cloud")

# The specific model to use when Ollama is called
OLLAMA_CLOUD_MODEL = os.getenv("OLLAMA_CLOUD_MODEL", "qwen3-vl:235b-cloud")

# The specific local model to use when Qwen2-VL local is called
QWEN2VL_MODEL_ID = os.getenv("QWEN2VL_MODEL_ID", "Qwen/Qwen2-VL-2B-Instruct")

# Whether to enable Nemotron for verification (if time permits)
ENABLE_NEMOTRON_VERIFICATION = True

# Whether to load heavy local models (Qwen2-VL, Nemotron) into VRAM on startup.
# Set to False to save 4-6GB of system RAM when using the cloud!
PRELOAD_LOCAL_MODELS = False

# Embedding model used for RAG Vector Database
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "all-MiniLM-L6-v2")

# PyTorch Local Generative Models
NEMOTRON_MODEL_ID = os.getenv("NEMOTRON_MODEL_ID", "nvidia/nemotron-colembed-vl-4b-v2")
PIX2STRUCT_MODEL_ID = os.getenv("PIX2STRUCT_MODEL_ID", "google/pix2struct-chartqa-base")
