import os
import re
from typing import List, Optional

import cv2
from fastapi import APIRouter, BackgroundTasks, HTTPException
from PIL import Image
from pydantic import BaseModel

from backend.services.chat_session_store import InMemoryChatSessionStore
from backend.services.offline_processor import offline_processor
from backend.services.search_service import search_service
from backend.services.vlm_service import vlm_service
from backend.services.agent_service import agent_service

try:
    import config
except Exception:
    config = None

router = APIRouter()

_chat_session_store = InMemoryChatSessionStore(
    ttl_seconds=getattr(config, "CHAT_SESSION_TTL_SECONDS", 1800) if config else 1800,
    max_turns=getattr(config, "CHAT_MAX_TURNS", 12) if config else 12,
)


class SearchQuery(BaseModel):
    query: str
    limit: int = 5


class SearchChatRequest(BaseModel):
    question: str
    filename: Optional[str] = None
    session_id: Optional[str] = None


class SearchResult(BaseModel):
    filename: str
    timestamp: float
    description: str
    score: float
    severity: str
    threats: List[str]
    provider: str
    confidence: float
    timestamp_seconds: Optional[float] = None


def _extract_timestamp_hint(question: str, duration_seconds: Optional[float] = None) -> Optional[float]:
    q = (question or "").lower().strip()

    mmss = re.search(r"\b(\d{1,2}):([0-5]\d)\b", q)
    if mmss:
        return float(int(mmss.group(1)) * 60 + int(mmss.group(2)))

    min_match = re.search(r"\b(\d+)\s*(?:min|mins|minute|minutes)\b", q)
    sec_match = re.search(r"\b(\d+)\s*(?:sec|secs|second|seconds)\b", q)
    if min_match and sec_match:
        return float(int(min_match.group(1)) * 60 + int(sec_match.group(1)))
    if min_match:
        return float(int(min_match.group(1)) * 60)
    if sec_match:
        return float(int(sec_match.group(1)))

    if any(x in q for x in ["beginning", "start", "opening"]):
        return 0.0
    if any(x in q for x in ["end", "ending", "final", "last part"]):
        if duration_seconds is not None and duration_seconds > 1:
            return float(max(0.0, duration_seconds - 1.0))
    return None


def _extract_time_range(question: str) -> Optional[tuple]:
    """Extracts (start, end) tuple from natural language time-range queries."""
    q = (question or "").lower()
    
    # "from 80s to 120s" / "from 80 to 120 seconds" / "80s-120s"
    m = re.search(
        r"\b(\d+)\s*(?:s|sec|secs|second|seconds)?\s*(?:to|-|through)\s*(\d+)\s*(?:s|sec|secs|second|seconds)?\b",
        q,
    )
    if m:
        return float(m.group(1)), float(m.group(2))
    
    # "between 80 and 120 seconds"
    m = re.search(
        r"between\s+(\d+)\s*(?:s|sec|secs|second|seconds)?\s+and\s+(\d+)\s*(?:s|sec|secs|second|seconds)?\b",
        q,
    )
    if m:
        return float(m.group(1)), float(m.group(2))
    
    return None


def _resolve_video_path(filename: Optional[str]) -> Optional[str]:
    if not filename:
        return None
    storage_dirs = [
        os.getenv("STORAGE_DIR", "storage/clips"),
        "storage/recordings",
        "storage/processed",
        "storage/temp",
        "storage/bin",
    ]
    for storage_dir in storage_dirs:
        test_path = os.path.join(storage_dir, filename)
        if os.path.exists(test_path):
            return test_path
    return None


def _video_duration_seconds(video_path: Optional[str]) -> Optional[float]:
    if not video_path or not os.path.exists(video_path):
        return None
    cap = cv2.VideoCapture(video_path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total_frames <= 0:
            return None
        return float(total_frames / fps)
    finally:
        cap.release()


def _extract_frame_data_uri(video_path: Optional[str], timestamp_seconds: Optional[float] = None) -> Optional[str]:
    if not video_path or not os.path.exists(video_path):
        return None

    cap = cv2.VideoCapture(video_path)
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total_frames <= 0:
            return None

        if timestamp_seconds is not None:
            cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, float(timestamp_seconds)) * 1000.0)
        else:
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)

        ret, frame = cap.read()
        if not ret:
            return None

        import base64
        from io import BytesIO

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame)
        buffer = BytesIO()
        pil_img.save(buffer, format="JPEG")
        image_data = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{image_data}"
    finally:
        cap.release()


def _timeline_to_context_lines(timeline_events: List[dict]) -> List[str]:
    lines = []
    for event in timeline_events:
        ts = round(float(event.get("timestamp", 0) or 0), 2)
        sev = event.get("severity", "low")
        desc = (event.get("description", "") or "").strip()
        if desc:
            lines.append(f"- [{ts}s][{sev}] {desc}")
    return lines


def _timeline_payload(timeline_events: List[dict]) -> List[dict]:
    payload = []
    for event in timeline_events:
        payload.append(
            {
                "timestamp": round(float(event.get("timestamp", 0) or 0), 2),
                "description": event.get("description", ""),
                "severity": event.get("severity", "low"),
                "provider": event.get("provider", "unknown"),
                "confidence": float(event.get("confidence", 0) or 0),
                "score": float(event.get("score", 0) or 0),
            }
        )
    return payload


def _should_visual_fallback(question: str, timeline_events: List[dict]) -> bool:
    q = (question or "").lower()
    if not timeline_events:
        return True
    visual_terms = [
        "see",
        "look",
        "color",
        "wearing",
        "holding",
        "face",
        "what does",
        "who is",
    ]
    return any(term in q for term in visual_terms)


@router.post("/index")
async def trigger_indexing(background_tasks: BackgroundTasks):
    """Scans metadata.json and updates the Vector DB."""
    try:
        background_tasks.add_task(search_service.index_metadata)
        return {"status": "Indexing started in background"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def trigger_processing(background_tasks: BackgroundTasks):
    """Scans storage/recordings and runs VLM analysis on new videos."""
    try:
        background_tasks.add_task(offline_processor.scan_and_process)
        return {"status": "Offline Processing started in background"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[SearchResult])
async def search_archive(q: str, limit: int = 5, filename: Optional[str] = None):
    """Semantic search for archived timeline events."""
    try:
        results = search_service.search(q, limit, filename=filename)

        response = []
        for hit in results:
            meta = hit.get("metadata", {})
            threats_list = meta.get("threats", "").split(",") if meta.get("threats") else []
            response.append(
                {
                    "filename": meta.get("filename", "unknown"),
                    "timestamp": float(meta.get("timestamp", 0)),
                    "description": hit["description"],
                    "score": hit["score"],
                    "severity": meta.get("severity", "low"),
                    "threats": threats_list,
                    "provider": meta.get("provider", "unknown"),
                    "confidence": float(meta.get("confidence", 0)),
                }
            )
        return response
    except Exception as e:
        print(f"Search API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cross-search")
async def cross_video_search(q: str, limit: int = 5, severity: Optional[str] = None):
    """Search across videos and group results by filename."""
    try:
        return search_service.cross_video_search(query=q, limit=limit, severity=severity)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest")
async def get_latest_insights():
    """
    Returns the most recent AI insights from metadata.json.
    """
    try:
        data = offline_processor.load_metadata()
        if not data:
            return []

        data.sort(key=lambda x: x.get("processed_at", ""), reverse=True)

        recent_videos = []
        for vid in data[:20]:
            events = vid.get("events", [])
            summary_obj = vid.get("video_summary", {})
            summary_text = ""
            summary_provider = "summary"
            summary_confidence = 0.0

            if isinstance(summary_obj, dict):
                summary_text = (summary_obj.get("text") or "").strip()
                summary_provider = summary_obj.get("provider", summary_provider)
                summary_confidence = float(summary_obj.get("confidence", 0) or 0)
            elif isinstance(summary_obj, str):
                summary_text = summary_obj.strip()

            main_summary = summary_text or "No description available"
            severity = "low"
            threats = []
            confidence = summary_confidence
            provider = summary_provider

            if events:
                main_event = events[0]
                if not summary_text:
                    main_summary = main_event.get("description", main_summary)
                    confidence = float(main_event.get("confidence", confidence) or 0)
                    provider = main_event.get("provider", provider)
                severity = main_event.get("severity", severity)
                threats = main_event.get("threats", threats)

            recent_videos.append(
                {
                    "filename": vid.get("filename", "unknown"),
                    "processed_at": vid.get("processed_at", ""),
                    "description": main_summary,
                    "severity": severity,
                    "threats": threats,
                    "confidence": confidence,
                    "provider": provider,
                    "timestamp": 0.0,
                    "event_count": len(events),
                }
            )

        return recent_videos
    except Exception as e:
        print(f"Error fetching latest: {e}")
        return []


@router.get("/recent")
async def get_recent_videos():
    """Alias for /latest for compatibility."""
    return await get_latest_insights()


@router.post("/chat")
async def intelligence_chat(req: SearchChatRequest):
    """
    Timeline-aware conversational chat.
    - deterministic timeline/RAG path by default
    - optional visual fallback at relevant timestamp
    - feature-flagged agent-style tool loop
    """
    try:
        session_id = _chat_session_store.get_or_create_session_id(req.session_id)
        _chat_session_store.append_turn(session_id, "user", req.question)
        chat_history = _chat_session_store.get_history(session_id)

        # Resolve filename fallback to latest video.
        if not req.filename:
            data = offline_processor.load_metadata()
            if data:
                latest = max(data, key=lambda x: x.get("processed_at", ""))
                req.filename = latest.get("filename")

        video_path = _resolve_video_path(req.filename)
        duration_seconds = _video_duration_seconds(video_path)
        target_timestamp = _extract_timestamp_hint(req.question, duration_seconds)
        timeline_limit = getattr(config, "CHAT_TIMELINE_LIMIT", 5) if config else 5

        timeline_filename, timeline_events = search_service.timeline_search(
            query=req.question,
            filename=req.filename,
            target_timestamp=target_timestamp,
            limit=timeline_limit,
        )
        if not req.filename and timeline_filename:
            req.filename = timeline_filename
            video_path = _resolve_video_path(req.filename)
            duration_seconds = _video_duration_seconds(video_path)
            target_timestamp = _extract_timestamp_hint(req.question, duration_seconds)

        answer_mode = "timeline_rag"
        provider = "metadata"
        confidence = 0.4
        used_sources: List[str] = []
        answer = ""

        context_lines = _timeline_to_context_lines(timeline_events)
        timeline_payload = _timeline_payload(timeline_events)

        # Check for time-range queries (benefits both agent and deterministic paths)
        time_range = _extract_time_range(req.question)

        enable_agent = bool(getattr(config, "ENABLE_AGENT_CHAT", False)) if config else False
        if enable_agent:
            # Full Agent Tool Loop path (Option B)
            agent_result = await agent_service.run(
                question=req.question,
                filename=req.filename,
                history=chat_history
            )
            
            answer = agent_result.get("answer", "")
            confidence = agent_result.get("confidence", 0.0)
            provider = agent_result.get("provider", "agent")
            used_sources = agent_result.get("used_sources", [])
            answer_mode = "agent_tool_loop"
        else:
            # Deterministic path: use range_search if time range detected
            if time_range and req.filename:
                start_ts, end_ts = time_range
                range_events = search_service.range_search(
                    query=req.question,
                    filename=req.filename,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    limit=timeline_limit,
                )
                if range_events:
                    timeline_events = range_events
                    context_lines = _timeline_to_context_lines(range_events)
                    timeline_payload = _timeline_payload(range_events)
                    used_sources.append("range_search")

            if context_lines:
                result = vlm_service.answer_with_context(
                    question=req.question,
                    context_blocks=context_lines,
                    history=chat_history,
                )
                answer = result.get("answer", "")
                provider = result.get("provider", "metadata")
                confidence = float(result.get("confidence", 0.7))
                used_sources.append("timeline_search")

            if _should_visual_fallback(req.question, timeline_events):
                frame_timestamp = target_timestamp
                if frame_timestamp is None and timeline_events:
                    frame_timestamp = float(timeline_events[0].get("timestamp", 0))
                image_data = _extract_frame_data_uri(video_path, frame_timestamp)
                if image_data:
                    visual = await vlm_service.answer_question(image_data, req.question)
                    visual_answer = visual.get("answer", "")
                    if visual_answer and (not answer or float(visual.get("confidence", 0)) > confidence):
                        answer = visual_answer
                        provider = visual.get("provider", provider)
                        confidence = float(visual.get("confidence", confidence))
                        answer_mode = "visual_qa"
                        used_sources.append("visual_qa")

        if not answer:
            if context_lines:
                answer = " ".join(line.strip("- ").strip() for line in context_lines[:3])
                confidence = max(confidence, 0.45)
                provider = "timeline_fallback"
                used_sources.append("timeline_fallback")
            else:
                answer_mode = "no_data"
                answer = "Please upload or process a video first, then ask again."
                confidence = 0.0
                provider = "none"

        _chat_session_store.append_turn(session_id, "assistant", answer)
        used_sources = list(dict.fromkeys(used_sources))

        return {
            "answer": answer,
            "confidence": confidence,
            "provider": provider,
            "source": answer_mode,
            "answer_mode": answer_mode,
            "filename": req.filename,
            "session_id": session_id,
            "timeline": timeline_payload,
            "used_sources": used_sources,
        }
    except Exception as e:
        print(f"[CHAT] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
