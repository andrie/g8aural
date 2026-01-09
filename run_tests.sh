#!/bin/bash
# Test runner script for g8aural
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh unit         # Run unit tests only
#   ./run_tests.sh integration  # Run integration tests only
#   ./run_tests.sh music_theory # Run music theory tests only
#   ./run_tests.sh slow         # Run slow tests only
#   ./run_tests.sh coverage     # Run with coverage report

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install it with: pip install pytest"
    exit 1
fi

# Parse command line argument
MODE=${1:-all}

case $MODE in
    unit)
        echo -e "${GREEN}Running unit tests...${NC}"
        pytest -v -m unit
        ;;
    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        pytest -v -m integration
        ;;
    music_theory)
        echo -e "${GREEN}Running music theory tests...${NC}"
        pytest -v -m music_theory
        ;;
    slow)
        echo -e "${GREEN}Running slow tests...${NC}"
        pytest -v -m slow
        ;;
    coverage)
        echo -e "${GREEN}Running tests with coverage...${NC}"
        if ! command -v pytest-cov &> /dev/null; then
            echo -e "${RED}Error: pytest-cov is not installed${NC}"
            echo "Install it with: pip install pytest-cov"
            exit 1
        fi
        pytest -v --cov=modules --cov=handlers --cov=state --cov=ui --cov=config \
               --cov-report=html --cov-report=term
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    fast)
        echo -e "${GREEN}Running fast tests (unit only)...${NC}"
        pytest -v -m "unit and not slow"
        ;;
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        pytest -v
        ;;
    *)
        echo -e "${RED}Unknown test mode: $MODE${NC}"
        echo "Usage: ./run_tests.sh [unit|integration|music_theory|slow|coverage|fast|all]"
        exit 1
        ;;
esac

# Print summary
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

exit $EXIT_CODE
