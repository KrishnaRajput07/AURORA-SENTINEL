# Scripts — Functionality

Utility and diagnostic scripts for development, testing, and operations.

## Documentation

### `AGENT_TESTING_GUIDE.md`
- Comprehensive guide for testing the agent service
- Examples of tool calls, expected responses, debugging tips

## Diagnostics

### `check_vlm_provider.py`
- Diagnostic tool for VLM provider availability
- Tests connection to Ollama, Gemini API, and local models
- Reports which providers are ready for use

### `debug_audio_raw.py`
- Low-level audio debugging
- Tests audio extraction from video files
- Validates audio pipeline without ML classification

### `debug_json_parsing.py`
- Tests JSON response parsing from VLM outputs
- Helps debug malformed JSON from AI models

### `vlm_diagnostic.py`
- Comprehensive VLM diagnostics (300+ lines)
- Tests all VLM providers with sample images
- Measures response times and validates output format
- Generates diagnostic reports

### `vlm_diagnostic_output.txt`
- Sample output from VLM diagnostic run

### `vlm_report.txt`
- Summary report of VLM testing results

## Testing Utilities

### `run_agent_tests.sh`
- Shell script to run agent service tests
- Automates test execution and result collection

### `test_agent_orchestration.py`
- Tests the agent orchestration logic
- Validates tool selection and execution flow

### `test_audio_cli.py`
- CLI tool for testing audio classification
- Quick audio analysis from command line

### `test_pipeline.py`
- End-to-end pipeline test runner
- Validates full processing chain

### `test_vlm_prompts.py`
- Tests different VLM prompt formats
- Helps optimize prompts for better AI responses

### `test_ws.py`
- WebSocket connection test
- Validates real-time stream connectivity

### `verify_audio.py`
- Audio system verification
- Checks audio dependencies and model availability

### `verify_context_logic.py`
- Tests context/narrative logic in VLM prompts
- Validates temporal context building

### `verify_json_fix.py`
- Tests JSON repair utilities
- Handles common VLM JSON output errors

### `verify_ml_merge.py`
- Tests ML and AI score merging logic
- Validates two-tier scoring calculations

## Operations

### `clean_data.sh`
- Cleans temporary and generated data files
- Resets storage directories to clean state

### `create_demo_video.py`
- Generates demonstration videos
- Creates sample footage for presentations/testing

### `download_models.py`
- Downloads required ML model weights
- Fetches YOLOv8 and other model files

### `optimize_models.py`
- Model optimization script
- Applies quantization and other optimizations for inference speed

### `prepare_demo_data.py`
- Prepares demonstration dataset
- Organizes sample videos for demos

### `print_routes.py`
- Utility to print all registered API routes
- Quick reference for available endpoints

### `reset_state.sh`
- Resets application state to defaults
- Clears database, cache, and temporary files

### `run_live_demo.py`
- Live demonstration runner
- Automates demo flow with sample videos

## Root-level Scripts

### `start.sh`
- Production startup script (Linux/macOS)
- Initializes environment, starts API server

### `start.ps1`
- Production startup script (Windows PowerShell)
- Windows equivalent of start.sh

## Usage Examples

```bash
# Check VLM providers
python scripts/check_vlm_provider.py

# Run diagnostics
python scripts/vlm_diagnostic.py

# Clean data
bash scripts/clean_data.sh

# Reset state
bash scripts/reset_state.sh

# Download models
python scripts/download_models.py
```
