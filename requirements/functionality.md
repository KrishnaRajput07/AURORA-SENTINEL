# Requirements — Functionality

Dependency specifications organized by component.

## Files

### `backend.txt`
- Core backend dependencies (FastAPI, SQLAlchemy, OpenCV, etc.)
- ML stack: torch (CPU), ultralytics, transformers
- AI providers: google-generativeai, ollama
- Database: sqlalchemy, psycopg2-binary (PostgreSQL)
- Vector search: chromadb, sentence-transformers
- Utilities: python-dotenv, pillow, pyyaml

### `ai-intelligence.txt`
- AI Intelligence Layer specific dependencies
- Additional model libraries: qwen-vl-utils, timm
- Flask dependencies for the standalone AI router server

### `tests.txt`
- Testing framework dependencies
- pytest, pytest-asyncio, hypothesis (property-based testing)
- Coverage: pytest-cov
- Mocking: pytest-mock

### `videollama.txt`
- VideoLLaMA model dependencies (legacy/experimental)
- Specialized video-language model support

## Notes
- Backend installs CPU-only PyTorch by default (saves ~2.5GB)
- For GPU support, manually install CUDA-enabled torch
- All requirements files are referenced by Dockerfile and setup scripts
