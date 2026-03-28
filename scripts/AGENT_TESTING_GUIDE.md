# Agent Service Testing Guide

## Overview

The improved `test_agent_orchestration.py` script provides comprehensive testing of the AgentService orchestration loop with detailed validation, performance metrics, and error handling.

## Prerequisites

1. **Ollama Instance**: Running on localhost:11434 (or configure via OLLAMA_HOST env var)
2. **Agent Model**: Default is `kimi-k2.5:cloud` (configurable via AGENT_MODEL env var)
3. **Video Data**: Storage/metadata.json with processed video records
4. **Dependencies**: All backend services and their dependencies

## Installation & Setup

```bash
# Ensure all dependencies are installed
pip install -r requirements/backend.txt

# Set up environment (optional)
export AGENT_MODEL="kimi-k2.5:cloud"
export OLLAMA_HOST="localhost:11434"
export ENABLE_AGENT_CHAT="true"
```

## Usage

### Basic Test Suite
```bash
# Run full test suite
python3 scripts/test_agent_orchestration.py

# Run with verbose output (default)
python3 scripts/test_agent_orchestration.py --verbose

# Run with performance benchmarks
python3 scripts/test_agent_orchestration.py --performance

# Run error scenario tests
python3 scripts/test_agent_orchestration.py --errors
```

### Single Query Testing
```bash
# Test specific query
python3 scripts/test_agent_orchestration.py --query "How many fights were there?"

# Test with specific video context
python3 scripts/test_agent_orchestration.py --query "What happened at 30s?" --context "fight_0257.mpeg"
```

### Test Categories

#### 1. Tool Registration Tests
- Verifies all 5 expected tools are registered
- Checks tool definitions and parameters
- Validates tool availability

#### 2. Individual Tool Tests
- Tests each tool in isolation
- Validates basic functionality
- Measures response times

#### 3. Orchestration Tests
- Tests complex multi-tool queries
- Validates tool sequencing
- Checks response quality and confidence

#### 4. Performance Benchmarks
- Measures response times for different query types
- Tracks confidence scores
- Monitors tool call efficiency

#### 5. Error Scenario Tests
- Tests graceful failure handling
- Validates fallback behavior
- Checks error message quality

## Test Cases

### Complex Query Examples

1. **Time-Range Counting**: `"How many people were in red hoodies between 10s and 50s?"`
   - Expected tools: `timeline_search`, `count_events`
   - Validates time range parsing and counting

2. **Cross-Video Analysis**: `"Find all fights across all videos and count them."`
   - Expected tools: `cross_video_search`, `count_events`
   - Tests multi-video search capabilities

3. **Timestamp Query**: `"What happened at the 30-second mark in this video?"`
   - Expected tools: `timeline_search`
   - Tests precise timestamp handling

4. **Video Summary**: `"Summarize this video's key events."`
   - Expected tools: `get_video_info`, `timeline_search`
   - Tests information synthesis

## Expected Output

### Console Output
```
[14:30:15] [INFO] Checking prerequisites...
[14:30:15] [INFO] ✅ Ollama available with 5 models
[14:30:15] [INFO] ✅ Agent service initialized with model: kimi-k2.5:cloud
[14:30:15] [INFO] ✅ Found 3 video records in metadata
[14:30:16] [INFO] Testing tool registration...
[14:30:16] [INFO] ✅ PASS tool_registration: Registered: {'timeline_search', 'count_events', 'visual_qa', 'cross_video_search', 'get_video_info'}
[14:30:16] [INFO] Testing individual tool calls...
[14:30:16] [INFO] ✅ timeline_search: 0.45s
[14:30:17] [INFO] ✅ count_events: 0.23s
[14:30:17] [INFO] ✅ get_video_info: 0.12s
[14:30:17] [INFO] ✅ PASS single_tool_calls: Tested 3 tools
```

### Test Report
A JSON report is saved to `test_results/agent_test_report_[timestamp].json` with:
- Test summary and pass/fail rates
- Individual test results with metrics
- Performance benchmarks
- Environment information

## Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   ```
   ❌ Ollama not available: Connection refused
   ```
   **Solution**: Start Ollama service or check OLLAMA_HOST configuration

2. **No Metadata Found**
   ```
   ⚠️ No metadata found - some tests will be skipped
   ```
   **Solution**: Process some videos first to populate storage/metadata.json

3. **Model Not Available**
   ```
   ❌ Model 'kimi-k2.5:cloud' not found
   ```
   **Solution**: Pull the model or set AGENT_MODEL to an available model

4. **Tool Execution Errors**
   ```
   ❌ timeline_search exception: Tool execution failed
   ```
   **Solution**: Check SearchService initialization and vector DB setup

### Debug Mode

For detailed debugging, modify the script to enable more verbose logging:
```python
# Add at the top of main()
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Issues

If tests are running slowly:
1. Check Ollama model size (smaller models for testing)
2. Verify vector DB performance
3. Monitor system resources (CPU/RAM)
4. Consider using local models instead of cloud models

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Test Agent Service
  run: |
    python3 scripts/test_agent_orchestration.py --performance
    # Check exit code for pass/fail
    if [ $? -eq 0 ]; then
      echo "Agent tests passed"
    else
      echo "Agent tests failed"
      exit 1
    fi
```

### Test Result Validation
The script returns exit code 0 for pass rates ≥80%, 1 otherwise. Adjust this threshold in the main() function if needed.

## Extending Tests

### Adding New Test Cases
```python
# Add to complex_queries list in test_complex_queries()
{
    "query": "Your new test query here",
    "expected_tools": ["tool1", "tool2"],
    "description": "Test description"
}
```

### Custom Metrics
```python
# Add custom metrics in test_agent_orchestration()
metrics.update({
    "custom_metric": custom_value,
    "another_metric": another_value
})
```

### New Test Categories
```python
async def test_new_category(self):
    """Test new functionality."""
    self.log("Testing new category...")
    # Your test logic here
    self.log_test_result("new_category", passed, details)
```

## Best Practices

1. **Run tests before deployment** to catch regressions
2. **Monitor performance trends** over time
3. **Test with real data** for accurate results
4. **Use consistent test queries** for comparable results
5. **Review test reports** regularly for insights

## Related Files

- `backend/services/agent_service.py` - Main agent implementation
- `backend/services/search_service.py` - Search tool implementations
- `backend/services/vlm_service.py` - Visual QA tool implementation
- `config.py` - Configuration settings
- `tests/test_agent_smoke.py` - Basic smoke tests
