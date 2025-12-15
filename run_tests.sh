#!/bin/bash

# CarMax Data Classification Platform - Test Runner Script
# This script runs the comprehensive test suite with various options

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CarMax Data Classification Platform${NC}"
echo -e "${BLUE}Test Suite Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update dependencies
echo -e "${BLUE}Installing test dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt
echo -e "${GREEN}Dependencies installed.${NC}"
echo ""

# Default: run all tests
TEST_TYPE="${1:-all}"
VERBOSE="${2:-}"

case "$TEST_TYPE" in
    unit)
        echo -e "${BLUE}Running unit tests only...${NC}"
        pytest tests/unit/ -v $VERBOSE
        ;;

    integration)
        echo -e "${BLUE}Running integration tests only...${NC}"
        pytest tests/integration/ -v $VERBOSE
        ;;

    coverage)
        echo -e "${BLUE}Running all tests with coverage report...${NC}"
        pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml -v
        echo ""
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;

    fast)
        echo -e "${BLUE}Running fast tests (parallel execution)...${NC}"
        pytest -n auto -v
        ;;

    watch)
        echo -e "${BLUE}Running tests in watch mode...${NC}"
        pytest-watch
        ;;

    specific)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify test file or pattern${NC}"
            echo "Usage: ./run_tests.sh specific <test_file_or_pattern>"
            exit 1
        fi
        echo -e "${BLUE}Running specific tests: $2${NC}"
        pytest "$2" -v
        ;;

    all)
        echo -e "${BLUE}Running complete test suite...${NC}"
        pytest -v
        ;;

    help)
        echo "Usage: ./run_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  unit         - Run unit tests only (taxonomy_manager, classification_engine)"
        echo "  integration  - Run integration tests only (Flask API endpoints)"
        echo "  coverage     - Run all tests with HTML coverage report"
        echo "  fast         - Run tests in parallel for speed"
        echo "  specific     - Run specific test file (e.g., ./run_tests.sh specific tests/unit/test_taxonomy_manager.py)"
        echo "  all          - Run complete test suite (default)"
        echo "  help         - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh                    # Run all tests"
        echo "  ./run_tests.sh unit               # Run unit tests only"
        echo "  ./run_tests.sh coverage           # Generate coverage report"
        echo "  ./run_tests.sh specific tests/unit/test_taxonomy_manager.py::TestExcelImport"
        exit 0
        ;;

    *)
        echo -e "${RED}Unknown option: $TEST_TYPE${NC}"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}All tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Some tests failed!${NC}"
    echo -e "${RED}========================================${NC}"
fi

exit $TEST_EXIT_CODE
