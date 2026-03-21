# Model Availability Tracking

## Overview

The model availability tracking system implements a circuit breaker pattern to prevent repeated calls to failing AI models. This improves system resilience and performance by:

1. Tracking consecutive failures for each model
2. Temporarily disabling models after repeated failures
3. Automatically re-enabling models after a cooldown period
4. Providing status information for monitoring and health checks

## Configuration

- **Max Consecutive Failures**: 3 (configurable via `ModelAvailabilityTracker.MAX_CONSECUTIVE_FAILURES`)
- **Cooldown Period**: 5 minutes / 300 seconds (configurable via `ModelAvailabilityTracker.COOLDOWN_SECONDS`)

## Tracked Models

The system tracks availability for three AI models:

1. **Qwen2-VL** (`qwen2vl`) - Primary GPU-accelerated vision-language model
2. **Nemotron** (`nemotron`) - Secondary verification model using embeddings
3. **Ollama** (`ollama`) - Local fallback model

## How It Works

### Success Recording

When a model successfully completes an operation:
```python
from model_availability import get_tracker

tracker = get_tracker()
tracker.record_success('qwen2vl')
```

This:
- Resets consecutive failure count to 0
- Marks the model as available
- Increments total success count
- Records timestamp of last success

### Failure Recording

When a model fails:
```python
tracker.record_failure('qwen2vl', error=exception)
```

This:
- Increments consecutive failure count
- Increments total failure count
- Records timestamp of last failure
- If consecutive failures >= 3, marks model as unavailable

### Availability Checking

Before attempting to use a model:
```python
if tracker.is_available('qwen2vl'):
    # Proceed with model
    result = analyze_with_qwen2vl(...)
else:
    # Skip to next model
    logger.info("Qwen2-VL unavailable, trying fallback")
```

If a model is unavailable:
- Returns `False` during cooldown period
- After cooldown elapses, automatically returns `True` and resets consecutive failures
- Allows the system to retry the model

### Status Reporting

Get detailed status for monitoring:
```python
# Single model
status = tracker.get_status('qwen2vl')
# Returns:
# {
#     'name': 'Qwen2-VL',
#     'available': True,
#     'consecutive_failures': 0,
#     'total_failures': 5,
#     'total_successes': 120,
#     'last_failure_time': '2024-01-15T10:30:00',
#     'last_success_time': '2024-01-15T10:35:00',
#     'time_since_failure_seconds': 300.5,
#     'time_since_success_seconds': 5.2,
#     'cooldown_remaining_seconds': None
# }

# All models
all_status = tracker.get_all_status()
```

## Integration Points

### AI Router (`aiRouter_enhanced.py`)

The tracker is integrated into all model analysis functions:

- `analyze_with_qwen2vl()` - Checks availability before analysis
- `analyze_with_ollama()` - Checks availability before analysis
- Nemotron verification in `analyze_image()` - Checks availability before verification

Each function:
1. Checks `tracker.is_available(model_name)` before attempting
2. Records success with `tracker.record_success(model_name)` on completion
3. Records failure with `tracker.record_failure(model_name, error)` on exception

### Health Check Endpoint (`backend/api/main.py`)

The `/health` endpoint includes model availability status:

```python
GET /health

Response:
{
    "status": "healthy",
    "models_loaded": true,
    "gpu_available": true,
    "database": "connected",
    "ai_models": {
        "qwen2vl": {
            "name": "Qwen2-VL",
            "available": true,
            "consecutive_failures": 0,
            "total_failures": 2,
            "total_successes": 150,
            ...
        },
        "nemotron": { ... },
        "ollama": { ... }
    },
    "optional_features": { ... }
}
```

## Benefits

1. **Improved Resilience**: System continues functioning even when individual models fail
2. **Reduced Latency**: Skips unavailable models instead of waiting for timeouts
3. **Automatic Recovery**: Models automatically become available after cooldown
4. **Monitoring**: Health checks provide visibility into model status
5. **Resource Efficiency**: Avoids repeated calls to failing models

## Example Scenarios

### Scenario 1: Temporary Network Issue

1. Qwen2-VL fails 3 times due to network issue
2. Model marked unavailable, system uses Ollama fallback
3. After 5 minutes, network recovers
4. Next analysis attempt checks availability, finds cooldown elapsed
5. Qwen2-VL becomes available again, system retries successfully

### Scenario 2: Model Initialization Failure

1. Nemotron fails to load at startup (3 consecutive failures)
2. Model marked unavailable
3. System continues with Qwen2-VL only (no verification)
4. After 5 minutes, system retries Nemotron initialization
5. If successful, verification resumes

### Scenario 3: Intermittent Failures

1. Ollama has 2 failures, then 1 success
2. Consecutive failures reset to 0
3. Model remains available throughout
4. Total failure count tracked for monitoring

## Testing

Unit tests: `tests/unit/test_model_availability.py`
- Tests circuit breaker logic
- Tests cooldown behavior
- Tests independent model tracking

Integration tests: `tests/integration/test_health_check_with_model_status.py`
- Tests health check integration
- Tests status reporting
- Tests analysis flow with unavailable models

## Future Enhancements

Potential improvements:
- Configurable thresholds per model
- Exponential backoff for cooldown periods
- Metrics export for monitoring systems
- Manual override to force model availability
- Notification system for sustained failures
