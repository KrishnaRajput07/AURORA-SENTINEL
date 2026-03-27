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

# Agent-style chat rollout gate (kept off by default)
ENABLE_AGENT_CHAT = os.getenv("ENABLE_AGENT_CHAT", "false").lower() == "true"

# Embedding model used for RAG Vector Database
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "all-MiniLM-L6-v2")

# PyTorch Local Generative Models
NEMOTRON_MODEL_ID = os.getenv("NEMOTRON_MODEL_ID", "nvidia/nemotron-colembed-vl-4b-v2")
PIX2STRUCT_MODEL_ID = os.getenv("PIX2STRUCT_MODEL_ID", "google/pix2struct-chartqa-base")

# -------------------------------------------------------------------
# SCORING THRESHOLDS
# -------------------------------------------------------------------

# Two-tier scoring weights (Final = ML_WEIGHT * ML + AI_WEIGHT * AI)
ML_SCORE_WEIGHT = 0.3
AI_SCORE_WEIGHT = 0.7

# Alert thresholds
ALERT_THRESHOLD = 60.0          # Uploaded video: alert if final_score exceeds this
LIVE_ALERT_THRESHOLD = 65       # Live stream: alert if risk_score exceeds this
RECORDING_THRESHOLD = 50        # Live stream: auto-start recording above this

# ML-to-AI gating
ML_SKIP_AI_THRESHOLD = 20       # Skip AI analysis if ML score is below this
STRUCTURED_PROMPT_THRESHOLD = 70 # Use detailed JSON prompt above this ML score

# Alert severity levels (based on final_score)
ALERT_LEVEL_CRITICAL = 70
ALERT_LEVEL_HIGH = 50
ALERT_LEVEL_MEDIUM = 30

# Sport/boxing safety cap
SPORT_RISK_CAP = 15             # Max risk when sport indicators detected

# -------------------------------------------------------------------
# TIMING & INTERVALS
# -------------------------------------------------------------------

ALERT_COOLDOWN_SECONDS = 10     # Min seconds between persisted alerts
VLM_ANALYSIS_INTERVAL = 10     # Seconds between periodic VLM calls (live)
VLM_HIGH_RISK_INTERVAL = 3     # Min seconds between VLM calls for high risk
OFFLINE_ANALYSIS_INTERVAL = 2   # Seconds between ML checks on uploaded video
CHANGE_TRIGGER_COOLDOWN = 3.0   # Min seconds between motion-triggered VLM calls
LIVE_VLM_CONTEXT_WINDOW = 4     # Rolling narratives included in live VLM prompt
VLM_INTERVAL_MIN_SECONDS = 2     # Runtime control lower bound
VLM_INTERVAL_MAX_SECONDS = 30    # Runtime control upper bound

# -------------------------------------------------------------------
# TIMEOUTS
# -------------------------------------------------------------------

AI_TOTAL_TIMEOUT = 5.0          # Hard cap on total AI analysis time
NEMOTRON_TIMEOUT = 3.0          # Max time for Nemotron verification
QWEN_TIMEOUT = 2.0             # Max time for Qwen2-VL analysis

# -------------------------------------------------------------------
# SEVERITY THRESHOLDS (for uploaded video event classification)
# -------------------------------------------------------------------

SEVERITY_HIGH_THRESHOLD = 65
SEVERITY_MEDIUM_THRESHOLD = 35

# -------------------------------------------------------------------
# SCORING CONFIDENCE VALUES
# -------------------------------------------------------------------

CONFIDENCE_BOTH_AVAILABLE = 0.8  # When both ML and AI scores exist
CONFIDENCE_ML_ONLY = 0.3         # When only ML score available
CONFIDENCE_AI_ONLY = 0.6         # When only AI score available
CONFIDENCE_NONE = 0.0            # When neither available

# -------------------------------------------------------------------
# CHAT SETTINGS
# -------------------------------------------------------------------

CHAT_SESSION_TTL_SECONDS = int(os.getenv("CHAT_SESSION_TTL_SECONDS", "1800"))
CHAT_MAX_TURNS = int(os.getenv("CHAT_MAX_TURNS", "12"))
CHAT_TIMELINE_LIMIT = int(os.getenv("CHAT_TIMELINE_LIMIT", "5"))

# -------------------------------------------------------------------
# AGENT SETTINGS
# -------------------------------------------------------------------

# Agent model and provider (local or cloud)
# Note: qwen3:4B is chosen as default based on user's local inventory.
AGENT_MODEL = os.getenv("AGENT_MODEL", "qwen3:4B")
AGENT_PROVIDER = os.getenv("AGENT_PROVIDER", "ollama_local")

# Agent logic constraints
AGENT_MAX_TOOL_CALLS = int(os.getenv("AGENT_MAX_TOOL_CALLS", "3"))
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.1"))

# Search constraints for counting tools
COUNT_SEARCH_LIMIT = int(os.getenv("COUNT_SEARCH_LIMIT", "500"))
