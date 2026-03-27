import json
import os
import sys
from typing import List, Optional, Dict, Any

try:
    import ollama
except ImportError:
    ollama = None

# Ensure we can import config and other services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def _get_agent_config():
    """Read agent config at call-time for true hot-swappability."""
    try:
        import config
        return {
            "model": getattr(config, "AGENT_MODEL", "qwen3:4B"),
            "max_calls": getattr(config, "AGENT_MAX_TOOL_CALLS", 3),
            "temperature": getattr(config, "AGENT_TEMPERATURE", 0.1),
        }
    except ImportError:
        return {"model": "qwen3:4B", "max_calls": 3, "temperature": 0.1}

from backend.services.search_service import search_service
from backend.services.vlm_service import vlm_service

class AgentService:
    """
    Lightweight tool-calling agent.
    Decomposes user questions into search, counting, or visual QA calls.
    """

    def __init__(self):
        # Tool definitions for Ollama — defined once, reused across calls
        
        # Tool definitions for Ollama
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "timeline_search",
                    "description": "Search for specific events within a video's timeline. Use start_ts/end_ts for time-range queries.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search term (e.g., 'fighting', 'red hoodie')"},
                            "filename": {"type": "string", "description": "Optional filename to restrict search to one video"},
                            "start_ts": {"type": "number", "description": "Optional start time in seconds"},
                            "end_ts": {"type": "number", "description": "Optional end time in seconds"},
                            "limit": {"type": "integer", "description": "Max results to return", "default": 5}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "count_events",
                    "description": "Count how many videos or events match a specific description across the entire archive.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The description to count (e.g., 'man in red hoodie')"},
                            "severity": {"type": "string", "description": "Optional severity filter (low, medium, high)"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "visual_qa",
                    "description": "Perform a deep visual analysis of a specific frame at a given timestamp to answer detailed visual questions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "The video filename"},
                            "timestamp": {"type": "number", "description": "The timestamp in seconds"},
                            "question": {"type": "string", "description": "The visual question (e.g., 'What is the person holding?')"}
                        },
                        "required": ["filename", "timestamp", "question"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cross_video_search",
                    "description": "Find and group matching events across multiple different videos for forensic analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search term"},
                            "severity": {"type": "string", "description": "Optional severity filter"},
                            "limit": {"type": "integer", "description": "Max videos to return", "default": 5}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_video_info",
                    "description": "Get high-level metadata, duration, and summary for a specific video file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "The filename"}
                        },
                        "required": ["filename"]
                    }
                }
            }
        ]

    async def run(self, question: str, filename: Optional[str], history: List[dict]) -> dict:
        """Runs the agentic loop to answer a question."""
        if ollama is None:
            return {
                "answer": "Ollama library not installed. Cannot run agent.",
                "confidence": 0.0,
                "provider": "none",
                "used_sources": []
            }

        # Read config at call-time so env-var changes take effect without restart
        cfg = _get_agent_config()
        model = cfg["model"]
        max_calls = cfg["max_calls"]
        temperature = cfg["temperature"]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Aurora Sentinel Intelligence Agent. You help users analyze surveillance footage. "
                    "Use the provided tools to retrieve data before answering. "
                    "If a time range is mentioned (e.g., 'from 80s to 120s'), use timeline_search with start_ts and end_ts. "
                    "If asked for a count, use count_events. "
                    "Synthesize a clear, professional executive summary based ONLY on the tool results. "
                    "Do NOT wrap your response in <think> tags or include internal reasoning."
                )
            }
        ]
        
        # Add history (last 6 turns)
        for turn in history[-6:]:
            messages.append({"role": turn.get("role"), "content": turn.get("content")})
            
        # Add current question
        messages.append({"role": "user", "content": question})
        
        used_sources = []
        tools_called = []
        
        for iteration in range(max_calls):
            print(f"[Agent] Iteration {iteration+1}/{max_calls} | model={model} | q='{question[:40]}...'")
            
            try:
                response = ollama.chat(
                    model=model,
                    messages=messages,
                    tools=self.tools,
                    options={"temperature": temperature}
                )
                
                # Robust access: ollama lib may return object with attrs OR dict
                if hasattr(response, "message"):
                    message = response.message
                    # Convert to dict for messages list
                    msg_dict = {
                        "role": getattr(message, "role", "assistant"),
                        "content": getattr(message, "content", "") or "",
                    }
                    tool_calls = getattr(message, "tool_calls", None)
                    if tool_calls:
                        msg_dict["tool_calls"] = tool_calls
                else:
                    msg_dict = response.get("message", {})
                    tool_calls = msg_dict.get("tool_calls")
                
                messages.append(msg_dict)
                
                if not tool_calls:
                    # No more tools needed, we have the final answer
                    answer_text = msg_dict.get("content", "")
                    # Strip <think>...</think> blocks from reasoning models
                    import re as _re
                    answer_text = _re.sub(r"<think>.*?</think>", "", answer_text, flags=_re.DOTALL).strip()
                    return {
                        "answer": answer_text,
                        "confidence": 0.85,
                        "provider": f"agent({model})",
                        "used_sources": list(set(used_sources)),
                        "tools_called": tools_called
                    }
                
                # Execute tool calls
                for tool_call in tool_calls:
                    # Handle both dict and object access patterns
                    if hasattr(tool_call, "function"):
                        fn_obj = tool_call.function
                        fn_name = getattr(fn_obj, "name", "")
                        args = getattr(fn_obj, "arguments", {})
                    else:
                        fn_name = tool_call["function"]["name"]
                        args = tool_call["function"]["arguments"]
                    
                    print(f"[Agent] Calling tool: {fn_name}({args})")
                    
                    result = await self._call_tool(fn_name, args, filename)
                    used_sources.append(fn_name)
                    tools_called.append({"tool": fn_name, "args": args})
                    
                    # Safe JSON serialization (handles None, datetime, etc.)
                    try:
                        result_json = json.dumps(result, default=str)
                    except (TypeError, ValueError):
                        result_json = json.dumps({"result": str(result)})
                    
                    messages.append({
                        "role": "tool",
                        "content": result_json,
                    })
                    
            except Exception as e:
                print(f"[Agent] Error in loop: {e}")
                return {
                    "answer": f"I encountered an error while analyzing the request: {str(e)}",
                    "confidence": 0.0,
                    "provider": "agent_error",
                    "used_sources": list(set(used_sources))
                }
                
        # If we hit max iterations, return the last content
        last_content = msg_dict.get("content", "") if 'msg_dict' in dir() else ""
        return {
            "answer": last_content or "I processed your request but reached the maximum tool-call limit.",
            "confidence": 0.7,
            "provider": f"agent({model})",
            "used_sources": list(set(used_sources)),
            "tools_called": tools_called
        }

    async def _call_tool(self, name: str, args: dict, default_filename: Optional[str]) -> Any:
        try:
            filename = args.get("filename") or default_filename
            
            if name == "timeline_search":
                q = args.get("query", "")
                start = args.get("start_ts")
                end = args.get("end_ts")
                limit = args.get("limit", 5)
                
                if start is not None and end is not None:
                    return search_service.range_search(q, filename, start, end, limit)
                else:
                    _, events = search_service.timeline_search(q, filename, target_timestamp=start, limit=limit)
                    return events
                    
            elif name == "count_events":
                return search_service.count_matching(args.get("query", ""), args.get("severity"))
                
            elif name == "visual_qa":
                # We need to resolve path and extract frame
                from backend.api.routers.intelligence import _resolve_video_path, _extract_frame_data_uri
                path = _resolve_video_path(filename)
                ts = args.get("timestamp", 0)
                image_data = _extract_frame_data_uri(path, ts)
                if image_data:
                    return await vlm_service.answer_question(image_data, args.get("question", ""))
                return {"error": "Could not extract frame for visual QA"}
                
            elif name == "cross_video_search":
                return search_service.cross_video_search(args.get("query", ""), limit=args.get("limit", 5), severity=args.get("severity"))
                
            elif name == "get_video_info":
                return search_service.get_video_record(filename)
                
            return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

    @property
    def model(self):
        """Current agent model name (for external inspection / smoke tests)."""
        return _get_agent_config()["model"]

# Singleton
agent_service = AgentService()
