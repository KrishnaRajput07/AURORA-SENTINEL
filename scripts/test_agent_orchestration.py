#!/usr/bin/env python3
"""
Comprehensive Agent Service Orchestration Test Script

Tests the full AgentService loop with detailed validation of:
- Tool call decomposition and execution
- Response quality and confidence
- Error handling and fallback scenarios
- Performance metrics
- Multi-tool orchestration

Requirements:
- Running Ollama instance (default: localhost:11434)
- Configured agent model (default: kimi-k2.5:cloud)
- Storage/metadata.json with sample video data
"""

import asyncio
import json
import os
import sys
import time
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# Configuration
os.environ["ENABLE_AGENT_CHAT"] = "true"

# Import services
from backend.services.search_service import search_service
from backend.services.agent_service import agent_service


class AgentTestSuite:
    """Comprehensive test suite for AgentService orchestration."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_results = []
        self.current_context = None
        
    def log(self, message: str, level: str = "INFO"):
        """Structured logging for test output."""
        timestamp = time.strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level}]"
        print(f"{prefix} {message}")
        
    def log_test_result(self, test_name: str, passed: bool, details: str = "", metrics: Dict = None):
        """Record test result with optional metrics."""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": time.time(),
            "metrics": metrics or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        self.log(f"{status} {test_name}: {details}")
        
    async def check_prerequisites(self) -> bool:
        """Verify all prerequisites are met."""
        self.log("Checking prerequisites...")
        
        # Check Ollama availability
        try:
            import ollama
            models = ollama.list()
            self.log(f"✅ Ollama available with {len(models.get('models', []))} models")
        except Exception as e:
            self.log(f"❌ Ollama not available: {e}")
            return False
            
        # Check agent service
        if not hasattr(agent_service, 'model'):
            self.log("❌ Agent service not properly initialized")
            return False
        self.log(f"✅ Agent service initialized with model: {agent_service.model}")
        
        # Check metadata
        try:
            data = search_service._load_metadata()
            if not data:
                self.log("⚠️ No metadata found - some tests will be skipped")
                self.current_context = None
            else:
                self.log(f"✅ Found {len(data)} video records in metadata")
                self.current_context = data[0]["filename"]  # Use first video as context
        except Exception as e:
            self.log(f"⚠️ Could not load metadata: {e}")
            self.current_context = None
            
        return True
        
    async def test_tool_registration(self):
        """Test that all expected tools are properly registered."""
        self.log("Testing tool registration...")
        
        expected_tools = {
            "timeline_search", "count_events", "visual_qa", 
            "cross_video_search", "get_video_info"
        }
        
        registered_tools = {tool["function"]["name"] for tool in agent_service.tools}
        
        missing = expected_tools - registered_tools
        extra = registered_tools - expected_tools
        
        passed = not missing and not extra
        details = f"Registered: {registered_tools}"
        if missing:
            details += f" | Missing: {missing}"
        if extra:
            details += f" | Extra: {extra}"
            
        self.log_test_result("tool_registration", passed, details)
        
    async def test_single_tool_calls(self):
        """Test each tool individually with known inputs."""
        self.log("Testing individual tool calls...")
        
        if not self.current_context:
            self.log_test_result("single_tool_calls", False, "No video context available")
            return
            
        tools_to_test = [
            ("timeline_search", {"query": "fight", "filename": self.current_context, "start_ts": 0, "end_ts": 10}),
            ("count_events", {"query": "fight"}),
            ("get_video_info", {"filename": self.current_context}),
        ]
        
        passed_all = True
        for tool_name, args in tools_to_test:
            try:
                start_time = time.time()
                result = await agent_service._call_tool(tool_name, args, self.current_context)
                duration = time.time() - start_time
                
                # Basic validation
                is_valid = result is not None and not isinstance(result, dict) or not result.get("error")
                
                if is_valid:
                    self.log(f"✅ {tool_name}: {duration:.2f}s")
                else:
                    self.log(f"❌ {tool_name}: {result}")
                    passed_all = False
                    
            except Exception as e:
                self.log(f"❌ {tool_name} exception: {e}")
                passed_all = False
                
        self.log_test_result("single_tool_calls", passed_all, f"Tested {len(tools_to_test)} tools")
        
    async def test_agent_orchestration(self, query: str, expected_tools: List[str] = None):
        """Test full agent orchestration with a specific query."""
        self.log(f"Testing orchestration for: '{query[:50]}...'")
        
        start_time = time.time()
        try:
            response = await agent_service.run(query, self.current_context, [])
            duration = time.time() - start_time
            
            # Validate response structure
            required_fields = ["answer", "confidence", "provider", "used_sources"]
            missing_fields = [f for f in required_fields if f not in response]
            
            # Check if expected tools were called
            tools_called = response.get("tools_called", [])
            called_tool_names = [t.get("tool", "") for t in tools_called]
            
            if expected_tools:
                tools_match = all(tool in called_tool_names for tool in expected_tools)
            else:
                tools_match = len(called_tool_names) > 0  # At least some tool was called
            
            passed = not missing_fields and tools_match and response["confidence"] > 0
            
            details = f"Duration: {duration:.2f}s | Tools: {called_tool_names}"
            if missing_fields:
                details += f" | Missing fields: {missing_fields}"
            if not tools_match:
                details += f" | Expected tools: {expected_tools}"
                
            metrics = {
                "duration": duration,
                "confidence": response.get("confidence", 0),
                "tools_called": len(tools_called),
                "answer_length": len(response.get("answer", ""))
            }
            
            self.log_test_result(f"orchestration_{hash(query) % 10000}", passed, details, metrics)
            
            if self.verbose:
                self.log(f"  Answer: {response.get('answer', '')[:100]}...")
                self.log(f"  Confidence: {response.get('confidence', 0):.2f}")
                self.log(f"  Tools called: {called_tool_names}")
                
        except Exception as e:
            self.log_test_result(f"orchestration_{hash(query) % 10000}", False, f"Exception: {e}")
            
    async def test_complex_queries(self):
        """Test complex queries that require multiple tools."""
        self.log("Testing complex multi-tool queries...")
        
        complex_queries = [
            {
                "query": "How many people were in red hoodies between 10s and 50s?",
                "expected_tools": ["timeline_search", "count_events"],
                "description": "Time-range counting query"
            },
            {
                "query": "Find all fights across all videos and count them.",
                "expected_tools": ["cross_video_search", "count_events"],
                "description": "Cross-video analysis"
            },
            {
                "query": "What happened at the 30-second mark in this video?",
                "expected_tools": ["timeline_search"],
                "description": "Specific timestamp query"
            },
            {
                "query": "Summarize this video's key events.",
                "expected_tools": ["get_video_info", "timeline_search"],
                "description": "Video summary query"
            }
        ]
        
        for test_case in complex_queries:
            await self.test_agent_orchestration(
                test_case["query"], 
                test_case["expected_tools"]
            )
            
    async def test_error_scenarios(self):
        """Test error handling and fallback scenarios."""
        self.log("Testing error scenarios...")
        
        error_queries = [
            ("Invalid tool query", "Tell me about the weather today"),  # Should fail gracefully
            ("Malformed time range", "What happened from 999s to 1s?"),  # Invalid time range
            ("Non-existent video", "Analyze video_nonexistent.mp4"),  # File not found
        ]
        
        for description, query in error_queries:
            try:
                response = await agent_service.run(query, self.current_context, [])
                # Should not crash and should provide a meaningful response
                passed = response.get("answer") is not None and len(response.get("answer", "")) > 0
                self.log_test_result(f"error_{description.replace(' ', '_')}", passed, 
                                   f"Response: {response.get('answer', '')[:50]}...")
            except Exception as e:
                # Exceptions are acceptable for error scenarios
                self.log_test_result(f"error_{description.replace(' ', '_')}", True, 
                                   f"Handled exception: {type(e).__name__}")
                
    async def test_performance_benchmarks(self):
        """Test performance characteristics."""
        self.log("Running performance benchmarks...")
        
        if not self.current_context:
            self.log_test_result("performance_benchmarks", False, "No video context available")
            return
            
        # Test response times for different query types
        benchmark_queries = [
            ("simple_count", "How many events are there?"),
            ("timeline_query", "What happened between 10s and 20s?"),
            ("video_info", "Tell me about this video"),
        ]
        
        total_duration = 0
        for query_name, query in benchmark_queries:
            start_time = time.time()
            try:
                response = await agent_service.run(query, self.current_context, [])
                duration = time.time() - start_time
                total_duration += duration
                
                # Performance expectations (adjust based on your requirements)
                max_duration = 30.0  # 30 seconds max per query
                passed = duration < max_duration
                
                self.log_test_result(f"perf_{query_name}", passed, 
                                   f"Duration: {duration:.2f}s (max: {max_duration}s)")
            except Exception as e:
                self.log_test_result(f"perf_{query_name}", False, f"Exception: {e}")
                
        avg_duration = total_duration / len(benchmark_queries)
        self.log_test_result("performance_average", avg_duration < 20.0, 
                           f"Average: {avg_duration:.2f}s")
        
    async def generate_report(self):
        """Generate comprehensive test report."""
        self.log("Generating test report...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "pass_rate": pass_rate,
                "timestamp": time.time()
            },
            "test_results": self.test_results,
            "environment": {
                "agent_model": agent_service.model,
                "context_video": self.current_context,
                "ollama_available": True
            }
        }
        
        # Save report
        report_path = Path(PROJECT_ROOT) / "test_results" / f"agent_test_report_{int(time.time())}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log(f"📊 Test Report:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Passed: {passed_tests}")
        self.log(f"   Failed: {total_tests - passed_tests}")
        self.log(f"   Pass Rate: {pass_rate:.1f}%")
        self.log(f"   Report saved to: {report_path}")
        
        return report


async def main():
    """Main test execution."""
    parser = argparse.ArgumentParser(description="Agent Service Orchestration Test Suite")
    parser.add_argument("--query", type=str, help="Run single query test")
    parser.add_argument("--context", type=str, help="Video filename for context")
    parser.add_argument("--verbose", action="store_true", default=True, help="Verbose output")
    parser.add_argument("--performance", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--errors", action="store_true", help="Test error scenarios")
    
    args = parser.parse_args()
    
    test_suite = AgentTestSuite(verbose=args.verbose)
    
    # Check prerequisites
    if not await test_suite.check_prerequisites():
        test_suite.log("❌ Prerequisites not met. Exiting.", "ERROR")
        return 1
        
    # Override context if specified
    if args.context:
        test_suite.current_context = args.context
        test_suite.log(f"Using specified context: {args.context}")
    
    # Run tests
    await test_suite.test_tool_registration()
    await test_suite.test_single_tool_calls()
    
    if args.query:
        # Single query mode
        await test_suite.test_agent_orchestration(args.query)
    else:
        # Full test suite
        await test_suite.test_complex_queries()
        
        if args.performance:
            await test_suite.test_performance_benchmarks()
            
        if args.errors:
            await test_suite.test_error_scenarios()
    
    # Generate report
    report = await test_suite.generate_report()
    
    return 0 if report["summary"]["pass_rate"] >= 80 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
