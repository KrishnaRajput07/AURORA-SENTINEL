import asyncio
import os
import sys
import json

# Add project root to path
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# Mock config to enable agent
os.environ["ENABLE_AGENT_CHAT"] = "true"
os.environ["AGENT_MODEL"] = "qwen3:4B"

from backend.services.search_service import search_service
from backend.services.agent_service import agent_service

async def test_search_tools():
    print("--- Testing Range Search ---")
    # We need a real video record for this; let's check what's in metadata
    data = search_service._load_metadata()
    if not data:
        print("Skipping: No metadata found for range search test.")
    else:
        video = data[0]
        filename = video["filename"]
        print(f"Testing range search on {filename} (0s to 10s)...")
        results = search_service.range_search("anything", filename, 0, 10)
        print(f"Found {len(results)} events in range.")
        for r in results:
            print(f"  [{r['timestamp']}s] {r['description'][:50]}")

    print("\n--- Testing Count Matching ---")
    count_res = search_service.count_matching("fighting")
    print(f"Global fight count: {count_res['total_events']} events in {count_res['total_videos']} videos.")

async def test_agent_loop():
    print("\n--- Testing Agent Tool Decomposition ---")
    question = "What happened from 80s to 130s in the latest video?"
    
    # We'll mock the 'ollama.chat' if we don't want to run the real heavy model here,
    # but since the user has Ollama running, let's try a real (but small) call if possible,
    # OR just verify the tool registry.
    
    print(f"Question: {question}")
    print(f"Agent Model: {agent_service.model}")
    print(f"Tools Registered: {[t['function']['name'] for t in agent_service.tools]}")
    
    # Check tool call mapping
    from backend.api.routers.intelligence import _extract_time_range
    time_range = _extract_time_range(question)
    print(f"Extracted Time Range: {time_range}")
    assert time_range == (80.0, 130.0)
    print("✅ Time range extraction verified.")

if __name__ == "__main__":
    asyncio.run(test_search_tools())
    asyncio.run(test_agent_loop())
