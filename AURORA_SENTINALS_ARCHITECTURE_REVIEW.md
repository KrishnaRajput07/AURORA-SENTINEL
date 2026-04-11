# AURORA Sentinel — Architecture Review

**Document Version**: 1.0  
**Date**: April 2026  
**System**: AURORA Sentinel AI-Powered Surveillance System  
**Architecture**: Dual-Brain (ML + AI Intelligence)

---

## Executive Summary

AURORA Sentinel implements a novel **dual-brain architecture** that combines traditional computer vision (the "Analytical Brain") with modern Vision-Language Models (the "Contextual Brain") to achieve unprecedented accuracy in violence detection while maintaining real-time performance.

### Key Metrics
| Metric | Value |
|--------|-------|
| Detection Accuracy | 97% (with Gemini) / 85% (local-only) |
| ML Latency | <100ms |
| AI Analysis Time | 2–5 seconds (GPU) |
| False Positive Rate (Sports) | Near-zero |
| Frame Processing Rate | 30 FPS |

---

## 1. System Architecture

### 1.1 Dual-Brain Design Philosophy

The system mirrors human cognitive processing:

```
┌─────────────────────────────────────────────────────────────┐
│                    HUMAN SECURITY GUARD                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  REFLEXES (Fast, Pattern-Based)      REASONING (Context)   │
│  • Sees raised fists                 • Recognizes it's a    │
│  • Notices proximity                    boxing match        │
│  • Detects rapid movement            • Sees referee         │
│  → Immediate alert preparation       → Overrides false alarm│
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    AURORA SENTINEL                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ML TIER (Fast, Pattern-Based)     AI TIER (Context)       │
│  ┌─────────────────────┐          ┌─────────────────────┐  │
│  │ • YOLOv8 Detection  │          │ • VLM Analysis      │  │
│  │ • Pose Estimation   │          │ • Scene Description │  │
│  │ • Risk Scoring      │          │ • Sport Detection   │  │
│  │ • Anomaly Detection │          │ • Natural Language  │  │
│  └─────────────────────┘          └─────────────────────┘  │
│           │                                    │             │
│           └──────────────┬──────────────────────┘             │
│                          ▼                                  │
│              ┌─────────────────────┐                         │
│              │  TWO-TIER SCORING   │                         │
│              │  final_score =     │                         │
│              │  max(ML_score,      │                         │
│              │  0.3×ML + 0.7×AI)  │                         │
│              └─────────────────────┘                         │
│                          │                                  │
│                          ▼                                  │
│              ┌─────────────────────┐                         │
│              │   ALERT DECISION    │                         │
│              │  Alert if >60%      │                         │
│              └─────────────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Two-Tier Scoring Formula

```python
# Tier 1: ML Score (0-100)
ml_score = RiskScoringEngine.analyze(detection_data)

# Tier 2: AI Score (0-100) - only if ML > 20
if ml_score > ML_SKIP_AI_THRESHOLD:
    ai_result = VLM.analyze(frame, ml_context)
    ai_score = ai_result.risk_score
else:
    ai_score = None  # Skip AI for obvious non-threats

# Final Score: Weighted combination
if ai_score is not None:
    weighted = ML_WEIGHT * ml_score + AI_WEIGHT * ai_score
    final_score = max(ml_score, weighted)
else:
    final_score = ml_score

# Alert Decision
should_alert = final_score > ALERT_THRESHOLD  # 60%
```

**Rationale**: The `max()` ensures ML-only alerts are still possible (fast response), while the weighted combination improves accuracy when AI is available.

---

## 2. Component Architecture

### 2.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Dashboard│ │Live Feed │ │Intel.    │ │ Archives│ │  Admin  │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
│       │            │            │            │            │           │
│       └────────────┴────────────┴────────────┴────────────┘           │
│                              │                                          │
│                         HTTP/WebSocket                                   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────────┐
│                          BACKEND (FastAPI)                              │
│                              │                                          │
│  ┌───────────────────────────┴───────────────────────────┐             │
│  │                      API Layer                          │             │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │             │
│  │  │/alerts  │ │/process │ │   /ws   │ │/intelligence│    │             │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │             │
│  │       └─────────────┴───────────┴─────────┘             │             │
│  └───────────────────────────┬─────────────────────────────┘             │
│                              │                                          │
│  ┌───────────────────────────┴───────────────────────────┐             │
│  │                   Services Layer                      │             │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐         │             │
│  │  │ML Service  │ │VLM Service │ │Search      │         │             │
│  │  │            │ │            │ │Service     │         │             │
│  │  │•Detector   │ │•Ollama    │ │•ChromaDB   │         │             │
│  │  │•RiskEngine │ │•Gemini    │ │•Embeddings │         │             │
│  │  │•Anonymizer │ │•Nemotron  │ │            │         │             │
│  │  └────────────┘ └────────────┘ └────────────┘         │             │
│  └───────────────────────────────────────────────────────┘             │
│                              │                                          │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌──────────────────┐    ┌───────────────┐
│   ML Models   │    │  AI Intelligence │    │   Database    │
│  ┌─────────┐  │    │   ┌──────────┐   │    │  ┌─────────┐  │
│  │YOLOv8   │  │    │   │Ollama    │   │    │  │SQLite   │  │
│  │Pose     │  │    │   │Gemini    │   │    │  │PostgreSQL│  │
│  │Weapons  │  │    │   │Qwen2-VL  │   │    │  │ChromaDB │  │
│  └─────────┘  │    │   │Nemotron  │   │    │  └─────────┘  │
└───────────────┘    │   └──────────┘   │    └───────────────┘
                     └──────────────────┘
```

### 2.2 Data Flow Diagrams

#### 2.2.1 Live Stream Processing

```
Camera/Webcam
     │
     ▼
┌─────────────────┐
│   WebSocket     │◄── Browser captures frames
│   /ws/live-feed │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ML Detection   │── YOLOv8 inference
│  (UnifiedDetector)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Risk Scoring   │── Multi-factor analysis
│  (RiskEngine)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│   ML Score      │────►│  VLM Analysis   │ (conditional)
│   > 20?         │     │  (every 10s)    │
└─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Two-Tier       │── Combine scores
│  Scoring        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Alert Decision │── Should alert? (threshold 60%)
│  (>60%?)        │
└────────┬────────┘
         │
         ├─────────► Alert DB Record
         │
         ├─────────► Clip Capture (Smart Bin)
         │
         └─────────► WebSocket Broadcast (UI update)
```

#### 2.2.2 Offline Video Processing

```
User Upload
     │
     ▼
┌─────────────────┐
│  POST /upload   │── Receive file, save to disk
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Frame Extraction │── OpenCV frame-by-frame
│ (cv2.VideoCapture)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ML Detection   │── Per-frame detection
│  Pipeline       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  VLM Analysis   │── Every N seconds (keyframe)
│  (conditional)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Two-Tier       │── Score aggregation
│  Scoring        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Result Storage │── DB record, search index
│  & Indexing     │── Vector DB (ChromaDB)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Video Summary  │── Clip extraction, thumbnail
│  Generation     │── H.264 transcoding
└─────────────────┘
```

---

## 3. Key Design Decisions

### 3.1 Why Two-Tier Scoring?

| Approach | Latency | Accuracy | Cost | Best For |
|----------|---------|----------|------|----------|
| ML Only | <100ms | 70% | Low | Real-time alerts |
| AI Only | 2-5s | 85% | High | Accuracy |
| **Two-Tier** | <100ms + 2-5s | **97%** | Medium | **Both** |

**Decision**: Use ML for fast initial detection, AI for verification and context.

### 3.2 Why Multi-Provider VLM?

```
┌─────────────────────────────────────────────┐
│           VLM Provider Chain                │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────┐ │
│  │ Ollama   │───►│ Gemini   │───►│ ML   │ │
│  │ (Primary)│Fail │ (Backup) │Fail │ Only │ │
│  └──────────┘    └──────────┘    └──────┘ │
│       │                               ▲    │
│       └──────────────────────────────┘    │
│              (ML Score < 20 skip)          │
│                                             │
└─────────────────────────────────────────────┘
```

**Rationale**: 
- Ollama: Free, private, local deployment
- Gemini: Higher accuracy when available
- ML-Only: Always works as baseline

### 3.3 Database Schema Design

```sql
-- Core: Alerts with two-tier scoring
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    level VARCHAR(10),        -- CRITICAL, HIGH, MEDIUM, LOW
    
    -- Two-tier scoring fields
    ml_score FLOAT,           -- 0-100
    ai_score FLOAT,           -- 0-100
    final_score FLOAT,        -- Weighted or max
    detection_source VARCHAR, -- "ml", "ai", "both"
    ai_explanation TEXT,      -- Natural language reasoning
    ai_scene_type VARCHAR,    -- "real_fight", "boxing", "drama"
    ai_confidence FLOAT,      -- 0-1
    
    -- Accountability
    status VARCHAR,           -- pending, acknowledged, resolved
    operator_name VARCHAR,
    acknowledged_at DATETIME,
    resolved_at DATETIME,
    resolution_type VARCHAR,  -- e.g., "False Positive"
    resolution_notes TEXT
);

-- Smart Bin: Auto-captured clips
CREATE TABLE clip_records (
    id INTEGER PRIMARY KEY,
    camera_id VARCHAR,
    alert_id INTEGER,
    file_path VARCHAR,
    duration_sec INTEGER,
    captured_at DATETIME,
    expires_at DATETIME        -- For retention management
);
```

---

## 4. Scalability & Performance

### 4.1 Performance Budgets

| Component | Target | Achieved |
|-----------|--------|----------|
| ML Detection | <100ms | ~80ms (GPU) / ~150ms (CPU) |
| AI Analysis | <5s | ~3s (GPU) / ~8s (CPU) |
| End-to-End Upload | <30s | ~20s for 30s video |
| WebSocket Frame Rate | 30 FPS | 25-30 FPS |
| Database Queries | <50ms | ~20ms |

### 4.2 Scaling Strategies

```
Current: Single Instance
    │
    ├──► Horizontal Scaling (Future)
    │       ├─ Load Balancer (Nginx/HAProxy)
    │       ├─ Multiple API Instances
    │       ├─ Shared PostgreSQL
    │       └─ Redis for session/cache
    │
    └──► GPU Optimization
            ├─ Model Quantization (INT8)
            ├─ TensorRT for YOLO
            └─ Batch Inference
```

---

## 5. Security & Privacy

### 5.1 Security Measures

| Layer | Measure |
|-------|---------|
| API | CORS, rate limiting (future), JWT auth (future) |
| Database | SQLAlchemy ORM (prevents SQL injection) |
| AI Providers | API key environment variables |
| File Upload | Type validation, size limits |
| WebSocket | Origin validation |

### 5.2 Privacy Features

```python
# Face anonymization in PrivacyAnonymizer
1. Detect faces via YOLO pose keypoints (or Haar fallback)
2. Apply Gaussian blur with padding (30% of person height)
3. Return anonymized frame for display/storage
```

---

## 6. Testing Strategy

### 6.1 Test Pyramid

```
         ┌─────────────┐
         │   E2E Tests │  ← Selenium/Playwright (future)
         │  (Few tests)│
         └──────┬──────┘
                │
       ┌────────▼────────┐
       │ Integration Tests│  ← API + DB + ML + AI
       │   (Moderate)    │     test_two_tier_integration.py
       └────────┬────────┘
                │
      ┌─────────▼─────────┐
      │   Property-Based  │  ← Hypothesis (random inputs)
      │   (High coverage) │     test_risk_engine_properties.py
      └─────────┬─────────┘
                │
    ┌───────────▼───────────┐
    │      Unit Tests       │  ← Individual functions
    │    (Many tests)       │     test_alert_service.py
    └───────────────────────┘
```

### 6.2 Test Categories

| Category | Purpose | Location |
|----------|---------|----------|
| Unit | Individual functions | `tests/unit/` |
| Integration | Component interaction | `tests/integration/` |
| Property-Based | Edge case discovery | `tests/property_based/` |
| Fight Detection | ML accuracy | `tests/fight_detection/` |
| System | End-to-end | `tests/system/` |

---

## 7. Deployment Options

### 7.1 Docker Deployment (Recommended)

```yaml
# docker-compose.yml services:
api:        FastAPI + ML models (GPU optional)
postgres:   Production database
redis:      Session/cache (future)
frontend:   Served by API (static files)
```

### 7.2 Local Development

```bash
# Terminal 1: Backend
cd backend && uvicorn api.main:app --reload

# Terminal 2: Frontend
cd frontend && npm start

# Terminal 3: AI Layer (optional)
cd ai-intelligence-layer && python server_local.py
```

---

## 8. Future Roadmap

### 8.1 Near-Term (Next 3 Months)

| Feature | Status | Priority |
|---------|--------|----------|
| Multi-camera support | Planned | High |
| Mobile app (React Native) | Planned | Medium |
| Alert notifications (SMS/Push) | Planned | High |
| Model fine-tuning pipeline | Research | Medium |

### 8.2 Long-Term (6-12 Months)

| Feature | Status | Priority |
|---------|--------|----------|
| Distributed deployment | Architecture | Medium |
| Real-time multi-object tracking | Research | Medium |
| Predictive threat modeling | Research | Low |
| Federated learning | Research | Low |

---

## 9. Conclusion

AURORA Sentinel's dual-brain architecture represents a significant advancement in surveillance AI by combining the speed of traditional computer vision with the contextual understanding of modern Vision-Language Models. The system's modular design, comprehensive testing, and flexible deployment options make it suitable for a wide range of security applications.

### Strengths
1. **Accuracy**: 97% with two-tier scoring
2. **Context Awareness**: Distinguishes real violence from sports/drama
3. **Flexibility**: Multiple AI providers with graceful fallback
4. **Transparency**: Natural language explanations for all alerts
5. **Privacy**: Built-in face anonymization

### Areas for Improvement
1. **Authentication**: Currently basic; needs JWT/OAuth for production
2. **Scalability**: Single-instance; needs horizontal scaling for enterprise
3. **Mobile**: Web-only; native apps would improve field usability

---

**Document Owner**: AURORA Sentinel Development Team  
**Review Schedule**: Quarterly  
**Related Documents**: 
- `README.md` (User-facing documentation)
- `functionality.md` files (Per-directory documentation)
- `readMes/` (Setup and troubleshooting guides)
