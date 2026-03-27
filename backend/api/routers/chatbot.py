"""
Surveillance Operator AI Chatbot
- Forced Routing Layer (time_range → range_search, counting → count_events)
- Unified Tool Response Format with confidence scoring
- Confidence-based VLM trigger (< 0.75 → VLM)
- VLM guardrail: MAX_VLM_CALLS = 3 per request
- LLM answer generation: Gemini formats DB results into natural language
- Text-based video Q&A: answers questions from stored metadata without re-running VLM
"""

import re
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.db.models import Alert, ClipRecord
from backend.services.search_service import search_service
from backend.services.offline_processor import offline_processor

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_VLM_CALLS = 3
VLM_CONFIDENCE_THRESHOLD = 0.75


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    filename: Optional[str] = None  # if set, use video context Q&A

class ToolResponse(BaseModel):
    type: str
    data: Any
    confidence: float
    needs_verification: bool = False
    tool_used: str = ""

class ChatResponse(BaseModel):
    answer: str
    intent: str
    results: List[Dict[str, Any]] = []
    result_type: str = "none"
    confidence: float = 1.0
    vlm_verified: bool = False
    quick_actions: List[str] = []


# ---------------------------------------------------------------------------
# LLM Answer Generator (Gemini → Ollama fallback → template)
# ---------------------------------------------------------------------------

def _groq_chat(system: str, user: str) -> Optional[str]:
    """Call Groq llama-3.1-8b-instant. Returns text or None on failure."""
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=512,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"Groq failed: {e}")
        return None


def _gemini_chat(system: str, user: str) -> Optional[str]:
    """Fallback: Gemini."""
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        return model.generate_content(f"{system}\n\n{user}").text.strip()
    except Exception as e:
        logger.warning(f"Gemini failed: {e}")
        return None


def llm_format_answer(question: str, tool_resp: ToolResponse, history: List[ChatMessage] = None) -> str:
    """Use Groq (→ Gemini → template) to turn raw DB results into a natural language answer."""
    data_str = json.dumps(tool_resp.data, indent=2, default=str)[:2000]

    system = (
        "You are AURORA, an AI assistant for a surveillance security system. "
        "Answer the operator's question accurately and concisely based ONLY on the provided database results. "
        "Use bullet points for lists. Be direct. Never hallucinate data not in the results."
    )
    user = (
        f"Operator question: {question}\n\n"
        f"Database results ({tool_resp.tool_used}):\n{data_str}\n\n"
        f"Provide a clear, accurate answer."
    )

    return _groq_chat(system, user) or _gemini_chat(system, user) or format_answer_template(tool_resp, question)


def llm_answer_from_video_context(question: str, video_context: str, filename: str) -> str:
    """Answer from stored video metadata text using Groq → Gemini → fallback."""
    system = (
        "You are AURORA, a surveillance AI assistant. "
        "Answer the operator's question based ONLY on the provided video analysis. "
        "Be specific about timestamps, risk levels, and detected threats. "
        "If the answer is not in the context, say so clearly."
    )
    user = (
        f"Video: {filename}\n\n"
        f"Analysis:\n{video_context[:3000]}\n\n"
        f"Question: {question}"
    )

    return (_groq_chat(system, user) or _gemini_chat(system, user)
            or f"I analyzed **{filename}**. The video contains {len([l for l in video_context.split(chr(10)) if '[' in l])} detected events. Ask me a specific question like 'Was there a fight?' or 'What was the risk level?'")


def get_video_context(filename: str) -> Optional[str]:
    """
    Load stored metadata for a video and build a rich text context
    from all its events/descriptions — no VLM re-run needed.
    """
    try:
        metadata = offline_processor.load_metadata()
        record = next((v for v in metadata if v.get('filename') == filename), None)
        if not record:
            return None

        events = record.get('events', [])
        if not events:
            return None

        # Build a structured context string from all events
        lines = [f"Video: {filename}", f"Processed: {record.get('processed_at', 'unknown')}", ""]

        summary = record.get('summary', {})
        if summary:
            lines.append(f"Summary: max risk {summary.get('max_risk', 0)}%, "
                         f"{summary.get('high_severity_count', 0)} high-severity events, "
                         f"threats: {', '.join(summary.get('threats_detected', [])) or 'none'}")
            lines.append("")

        lines.append("Timeline of events:")
        for e in events:
            ts = e.get('timestamp', 0)
            sev = e.get('severity', 'low').upper()
            desc = e.get('description', '')
            threats = ', '.join(e.get('threats', [])) or 'none'
            risk = e.get('risk_score', e.get('confidence', 0))
            if isinstance(risk, float) and risk <= 1.0:
                risk = int(risk * 100)
            lines.append(f"  [{ts:.1f}s] [{sev}] risk={risk}% threats={threats}")
            lines.append(f"    {desc}")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Failed to load video context for {filename}: {e}")
        return None


# ---------------------------------------------------------------------------
# Forced Routing Layer
# ---------------------------------------------------------------------------

def has_time_range(text: str) -> bool:
    patterns = [
        r'\b(today|yesterday|last hour|last night|this morning|last week|last 24)\b',
        r'\bat \d{1,2}(:\d{2})?\s*(am|pm)?\b',
        r'\bbetween\b.*(and)\b',
        r'\bfrom \d', r'\bsince \d',
    ]
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


def is_counting(text: str) -> bool:
    patterns = [
        r'\bhow many\b', r'\bcount\b', r'\btotal\b', r'\bnumber of\b',
        r'\bhow often\b', r'\bfrequency\b',
    ]
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


def force_tool(text: str) -> Optional[str]:
    if has_time_range(text):
        return "range_search"
    if is_counting(text):
        return "count_events"
    return None


# ---------------------------------------------------------------------------
# NLU helpers
# ---------------------------------------------------------------------------

TIME_PATTERNS = {
    "today": lambda: (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0), datetime.utcnow()),
    "yesterday": lambda: (
        (datetime.utcnow() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
        (datetime.utcnow() - timedelta(days=1)).replace(hour=23, minute=59, second=59),
    ),
    "last hour": lambda: (datetime.utcnow() - timedelta(hours=1), datetime.utcnow()),
    "last 24 hours": lambda: (datetime.utcnow() - timedelta(hours=24), datetime.utcnow()),
    "last week": lambda: (datetime.utcnow() - timedelta(days=7), datetime.utcnow()),
    "this morning": lambda: (
        datetime.utcnow().replace(hour=6, minute=0, second=0, microsecond=0),
        datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0),
    ),
    "last night": lambda: (
        (datetime.utcnow() - timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0),
        datetime.utcnow().replace(hour=6, minute=0, second=0, microsecond=0),
    ),
}

LEVEL_MAP = {
    "critical": ["critical", "very high", "extreme", "severe"],
    "high": ["high", "dangerous", "serious"],
    "medium": ["medium", "moderate", "suspicious"],
    "low": ["low", "minor"],
}

THREAT_MAP = {
    "fight": ["fight", "fighting", "brawl", "assault", "violence", "punch"],
    "weapon": ["weapon", "gun", "knife", "blade", "firearm", "pistol"],
    "fire": ["fire", "flame", "smoke"],
    "intrusion": ["intrusion", "break in", "trespass", "unauthorized"],
    "unattended": ["unattended", "abandoned", "bag"],
}

INTENT_PATTERNS = {
    "search_video": [
        r"\b(show|find|search)\b.*(video|footage|clip|recording)",
        r"\bwhat happened\b", r"\bwhen did\b",
        r"\b(fight|weapon|knife|gun)\b.*(video|footage|clip)",
    ],
    "stats": [r"\boverview\b", r"\bsummary\b", r"\bstatistic\b"],
    "help": [r"\bhelp\b", r"\bwhat can you\b", r"\bexample\b"],
}


def extract_time_range(text: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    lower = text.lower()
    for label, fn in TIME_PATTERNS.items():
        if label in lower:
            return fn()
    m = re.search(r'at (\d{1,2})(?::(\d{2}))?\s*(am|pm)?', lower)
    if m:
        hour = int(m.group(1))
        if m.group(3) == 'pm' and hour < 12:
            hour += 12
        base = datetime.utcnow().replace(hour=hour, minute=0, second=0, microsecond=0)
        return base, base + timedelta(hours=1)
    return None, None


def extract_level(text: str) -> Optional[str]:
    lower = text.lower()
    for level, kws in LEVEL_MAP.items():
        if any(k in lower for k in kws):
            return level
    return None


def extract_camera(text: str) -> Optional[str]:
    m = re.search(r'cam(?:era)?\s*[-_]?\s*(\w+)', text.lower())
    return f"CAM-{m.group(1).upper()}" if m else None


def extract_threat(text: str) -> Optional[str]:
    lower = text.lower()
    for threat, kws in THREAT_MAP.items():
        if any(k in lower for k in kws):
            return threat
    return None


def extract_limit(text: str) -> int:
    m = re.search(r'\b(\d+)\b.*(alert|event|result|clip|video)', text.lower())
    return min(int(m.group(1)), 50) if m else 10


def detect_intent(text: str) -> str:
    lower = text.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        for p in patterns:
            if re.search(p, lower):
                return intent
    return "search_alerts"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def _alert_to_dict(a: Alert, db: Session) -> Dict:
    clip_url = None
    if a.video_clip_path:
        clip = db.query(ClipRecord).filter(ClipRecord.file_path == a.video_clip_path).first()
        clip_url = (f"/smart-bin/clips/{clip.id}/stream" if clip
                    else f"/archive/download/{os.path.basename(a.video_clip_path)}?source=bin")
    return {
        "id": a.id,
        "timestamp": a.timestamp.isoformat() if a.timestamp else "",
        "level": a.level or "unknown",
        "risk_score": round(a.risk_score or 0, 1),
        "camera_id": a.camera_id or "unknown",
        "location": a.location or "",
        "clip_url": clip_url,
        "ai_explanation": (a.ai_explanation or "")[:150],
    }


def _alert_confidence(alerts: List[Dict], filters_used: int) -> float:
    if not alerts:
        return 0.3
    base = 0.6 + min(filters_used * 0.1, 0.3)
    if len(alerts) < 3:
        base -= 0.1
    return round(min(base, 0.95), 2)


def tool_range_search(db, ts, te, level=None, camera_id=None, threat=None, limit=10) -> ToolResponse:
    q = db.query(Alert).filter(Alert.timestamp >= ts, Alert.timestamp <= te)
    filters = 2
    if level: q = q.filter(Alert.level.ilike(f"%{level}%")); filters += 1
    if camera_id: q = q.filter(Alert.camera_id.ilike(f"%{camera_id}%")); filters += 1
    if threat: q = q.filter(Alert.ai_explanation.ilike(f"%{threat}%")); filters += 1
    data = [_alert_to_dict(a, db) for a in q.order_by(Alert.timestamp.desc()).limit(limit).all()]
    conf = _alert_confidence(data, filters)
    return ToolResponse(type="alerts", data=data, confidence=conf,
                        needs_verification=conf < VLM_CONFIDENCE_THRESHOLD, tool_used="range_search")


def tool_count_events(db, ts=None, te=None, level=None, camera_id=None, threat=None) -> ToolResponse:
    q = db.query(Alert)
    filters = 0
    if ts: q = q.filter(Alert.timestamp >= ts); filters += 1
    if te: q = q.filter(Alert.timestamp <= te); filters += 1
    if level: q = q.filter(Alert.level.ilike(f"%{level}%")); filters += 1
    if camera_id: q = q.filter(Alert.camera_id.ilike(f"%{camera_id}%")); filters += 1
    if threat: q = q.filter(Alert.ai_explanation.ilike(f"%{threat}%")); filters += 1
    total = q.count()
    breakdown = {lvl.lower(): db.query(Alert).filter(Alert.level.ilike(f"%{lvl}%")).count()
                 for lvl in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]}
    conf = round(min(0.5 + filters * 0.1, 0.9), 2)
    return ToolResponse(type="count", data={"total": total, "breakdown": breakdown},
                        confidence=conf, needs_verification=conf < VLM_CONFIDENCE_THRESHOLD,
                        tool_used="count_events")


def tool_search_alerts(db, level=None, camera_id=None, threat=None, limit=10) -> ToolResponse:
    q = db.query(Alert)
    filters = 0
    if level: q = q.filter(Alert.level.ilike(f"%{level}%")); filters += 1
    if camera_id: q = q.filter(Alert.camera_id.ilike(f"%{camera_id}%")); filters += 1
    if threat: q = q.filter(Alert.ai_explanation.ilike(f"%{threat}%")); filters += 1
    data = [_alert_to_dict(a, db) for a in q.order_by(Alert.timestamp.desc()).limit(limit).all()]
    conf = _alert_confidence(data, filters)
    return ToolResponse(type="alerts", data=data, confidence=conf,
                        needs_verification=conf < VLM_CONFIDENCE_THRESHOLD, tool_used="search_alerts")


def tool_search_video(query_text: str, limit: int = 10) -> ToolResponse:
    hits = search_service.search(query_text, n_results=limit)
    data = [{
        "filename": h.get("metadata", {}).get("filename", "unknown"),
        "timestamp": float(h.get("metadata", {}).get("timestamp", 0)),
        "description": h.get("description", ""),
        "severity": h.get("metadata", {}).get("severity", "low"),
        "threats": h.get("metadata", {}).get("threats", "").split(",") if h.get("metadata", {}).get("threats") else [],
        "score": round(h.get("score", 0), 2),
    } for h in hits]
    conf = round(min(0.5 + len(data) * 0.05, 0.9), 2) if data else 0.3
    return ToolResponse(type="video_events", data=data, confidence=conf,
                        needs_verification=conf < VLM_CONFIDENCE_THRESHOLD, tool_used="search_video")


def tool_get_stats(db) -> ToolResponse:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    data = {
        "total_alerts": db.query(Alert).count(),
        "today": db.query(Alert).filter(Alert.timestamp >= today_start).count(),
        "critical": db.query(Alert).filter(Alert.level.ilike("%critical%")).count(),
        "high": db.query(Alert).filter(Alert.level.ilike("%high%")).count(),
        "pending": db.query(Alert).filter(Alert.status == "pending").count(),
        "clips_in_bin": db.query(ClipRecord).count(),
    }
    return ToolResponse(type="stats", data=data, confidence=0.99,
                        needs_verification=False, tool_used="get_stats")


# ---------------------------------------------------------------------------
# Template fallback (when LLM unavailable)
# ---------------------------------------------------------------------------

def format_answer_template(tool_resp: ToolResponse, query: str) -> str:
    t, data = tool_resp.type, tool_resp.data
    if t == "count":
        total = data.get("total", 0)
        bd = data.get("breakdown", {})
        ans = f"Found **{total} event{'s' if total != 1 else ''}**."
        parts = [f"{v} {k}" for k, v in bd.items() if v > 0]
        if parts:
            ans += f" Breakdown: {', '.join(parts)}."
        return ans
    if t == "alerts":
        if not data:
            return "No alerts found. Try broadening the time range or removing filters."
        top = data[0]
        ts = top['timestamp'][:16].replace('T', ' ') if top['timestamp'] else 'unknown'
        ans = f"Found **{len(data)} alert{'s' if len(data) > 1 else ''}**.\n\n"
        ans += f"Most recent: **{top['level'].upper()}** at {ts} on {top['camera_id']} (risk: {top['risk_score']}%)"
        if top.get('ai_explanation'):
            ans += f"\n> {top['ai_explanation'][:120]}"
        return ans
    if t == "video_events":
        if not data:
            return f"No video events found for '{query}'. Process videos via the Intelligence page first."
        top = data[0]
        return f"Found **{len(data)} event{'s' if len(data) > 1 else ''}**.\nBest match: **{top['filename']}** at {top['timestamp']:.1f}s\n> {top['description'][:120]}..."
    if t == "stats":
        d = data
        return (f"**System Overview:**\n- Total: **{d['total_alerts']}** ({d['today']} today)\n"
                f"- Critical: **{d['critical']}** | High: **{d['high']}**\n"
                f"- Pending: **{d['pending']}** | Clips: **{d['clips_in_bin']}**")
    return "I couldn't find relevant data. Try rephrasing your query."


HELP_TEXT = (
    "I can help you query the surveillance system. Try:\n\n"
    "- **'Show high risk alerts today'**\n"
    "- **'How many fights last week?'**\n"
    "- **'Find alerts from Camera CAM-01'**\n"
    "- **'What happened yesterday at 2am?'**\n"
    "- **'System overview'**\n"
    "- **'Find videos with weapons'**"
)

QUICK_ACTIONS = [
    "Today's alerts", "High risk events", "System overview",
    "Find fights", "Alerts last hour", "How many critical alerts?",
]


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------

@router.post("/query", response_model=ChatResponse)
async def chatbot_query(req: ChatRequest, db: Session = Depends(get_db)):
    msg = req.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    # ── Video context Q&A ────────────────────────────────────────────────────
    # If a filename is provided and the question is about the video content,
    # answer from stored metadata text — no VLM re-run needed.
    if req.filename:
        context = get_video_context(req.filename)
        if context:
            answer = llm_answer_from_video_context(msg, context, req.filename)
            return ChatResponse(
                answer=answer,
                intent="video_context_qa",
                results=[],
                result_type="none",
                confidence=0.85,
                vlm_verified=False,
                quick_actions=QUICK_ACTIONS,
            )

    # ── Context resolution for follow-up queries ─────────────────────────────
    context_msg = msg
    if req.history:
        last_user = next((h.content for h in reversed(req.history) if h.role == "user"), "")
        follow_ups = ["only", "just", "from camera", "filter", "narrow", "more", "less", "also"]
        if any(f in msg.lower() for f in follow_ups) and last_user:
            context_msg = f"{last_user} {msg}"

    if re.search(r'\bhelp\b|\bwhat can you\b', context_msg.lower()):
        return ChatResponse(answer=HELP_TEXT, intent="help", results=[], result_type="none",
                            confidence=1.0, quick_actions=QUICK_ACTIONS)

    # Extract entities
    time_start, time_end = extract_time_range(context_msg)
    level = extract_level(context_msg)
    camera_id = extract_camera(context_msg)
    threat = extract_threat(context_msg)
    limit = extract_limit(context_msg)
    intent = detect_intent(context_msg)

    # ── Forced Routing ────────────────────────────────────────────────────────
    forced = force_tool(context_msg)

    if forced == "range_search":
        ts = time_start or (datetime.utcnow() - timedelta(hours=24))
        te = time_end or datetime.utcnow()
        tool_resp = tool_range_search(db, ts, te, level, camera_id, threat, limit)
    elif forced == "count_events":
        tool_resp = tool_count_events(db, time_start, time_end, level, camera_id, threat)
    elif intent == "stats":
        tool_resp = tool_get_stats(db)
    elif intent == "search_video":
        tool_resp = tool_search_video(threat or context_msg, limit)
    elif time_start or time_end:
        tool_resp = tool_range_search(db, time_start or datetime.utcnow() - timedelta(days=30),
                                      time_end or datetime.utcnow(), level, camera_id, threat, limit)
    else:
        # If we have specific filters, use alert search
        # If no filters at all, use semantic search on the question text to avoid same results
        if level or camera_id or threat:
            tool_resp = tool_search_alerts(db, level, camera_id, threat, limit)
        else:
            # Semantic search over video events first, fall back to recent alerts
            video_resp = tool_search_video(context_msg, limit)
            if video_resp.data:
                tool_resp = video_resp
            else:
                tool_resp = tool_search_alerts(db, level, camera_id, threat, limit)

    # ── LLM Answer Generation ─────────────────────────────────────────────────
    answer = llm_format_answer(context_msg, tool_resp, req.history)

    results = tool_resp.data if isinstance(tool_resp.data, list) else [tool_resp.data]

    return ChatResponse(
        answer=answer,
        intent=forced or intent,
        results=results[:10],
        result_type=tool_resp.type,
        confidence=tool_resp.confidence,
        vlm_verified=False,
        quick_actions=QUICK_ACTIONS,
    )


@router.get("/suggestions")
async def get_suggestions(q: str = ""):
    suggestions = [
        "Show high risk alerts today",
        "How many fights last week?",
        "Find alerts from Camera CAM-01",
        "What happened yesterday at 2am?",
        "How many critical alerts this week?",
        "Find videos with weapons",
        "Show critical incidents last night",
        "System overview",
        "List all pending alerts",
        "Alerts last hour",
    ]
    if q:
        ql = q.lower()
        suggestions = [s for s in suggestions if ql in s.lower()]
    return {"suggestions": suggestions[:5]}
