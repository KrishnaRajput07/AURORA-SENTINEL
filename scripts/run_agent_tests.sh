#!/bin/bash
# Quick Agent Service Test Runner
# Usage: ./scripts/run_agent_tests.sh [options]


# # Full test suite
# ./scripts/run_agent_tests.sh

# # Quick test with performance metrics
# ./scripts/run_agent_tests.sh --quick --performance

# # Test specific query
# ./scripts/run_agent_tests.sh --query "How many fights were there?"

# # Single query with context
# python3 scripts/test_agent_orchestration.py --query "What happened at 30s?" --context "fight_0257.mpeg"

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default options
VERBOSE="--verbose"
PERFORMANCE=""
ERRORS=""
QUERY=""
CONTEXT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            VERBOSE=""
            shift
            ;;
        --performance)
            PERFORMANCE="--performance"
            shift
            ;;
        --errors)
            ERRORS="--errors"
            shift
            ;;
        --query)
            QUERY="--query $2"
            shift 2
            ;;
        --context)
            CONTEXT="--context $2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --quick        Run quick tests (no verbose output)"
            echo "  --performance  Include performance benchmarks"
            echo "  --errors       Include error scenario tests"
            echo "  --query TEXT   Test specific query"
            echo "  --context FILE Use specific video as context"
            echo "  --help         Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}🚀 Starting Agent Service Tests...${NC}"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}❌ Ollama is not running on localhost:11434${NC}"
    echo "Please start Ollama first: ollama serve"
    exit 1
fi

# Check if metadata exists
if [ ! -f "storage/metadata.json" ]; then
    echo -e "${YELLOW}⚠️ No metadata.json found - some tests may be skipped${NC}"
fi

# Run the test script
echo -e "${YELLOW}🧪 Running tests...${NC}"
python3 scripts/test_agent_orchestration.py $VERBOSE $PERFORMANCE $ERRORS $QUERY $CONTEXT

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Agent tests passed!${NC}"
else
    echo -e "${RED}❌ Agent tests failed!${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 All tests completed successfully!${NC}"
