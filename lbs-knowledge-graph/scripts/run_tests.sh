#!/bin/bash

# LBS Knowledge Graph - Test Runner Script
# Runs all tests with coverage and generates reports

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  LBS Knowledge Graph - Test Suite         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

# Parse command line arguments
QUICK=false
UNIT_ONLY=false
INTEGRATION_ONLY=false
COVERAGE=true
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK=true
            shift
            ;;
        --unit)
            UNIT_ONLY=true
            shift
            ;;
        --integration)
            INTEGRATION_ONLY=true
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick           Run quick tests only"
            echo "  --unit            Run unit tests only"
            echo "  --integration     Run integration tests only"
            echo "  --no-coverage     Skip coverage reporting"
            echo "  --verbose, -v     Verbose output"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Virtual environment not activated. Activating...${NC}"
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}Virtual environment not found. Run ./scripts/setup.sh first.${NC}"
        exit 1
    fi
fi

# Create test results directory
mkdir -p test-results

# Build pytest command
PYTEST_CMD="pytest"
PYTEST_ARGS=()

# Select test directory
if [ "$UNIT_ONLY" = true ]; then
    echo -e "\n${YELLOW}Running unit tests only...${NC}"
    PYTEST_ARGS+=("tests/unit")
elif [ "$INTEGRATION_ONLY" = true ]; then
    echo -e "\n${YELLOW}Running integration tests only...${NC}"
    PYTEST_ARGS+=("tests/integration")
elif [ "$QUICK" = true ]; then
    echo -e "\n${YELLOW}Running quick tests only...${NC}"
    PYTEST_ARGS+=("tests/unit" "-m" "not slow")
else
    echo -e "\n${YELLOW}Running all tests...${NC}"
    PYTEST_ARGS+=("tests/")
fi

# Add coverage if enabled
if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS+=(
        "--cov=src"
        "--cov-report=xml"
        "--cov-report=html"
        "--cov-report=term-missing"
    )
fi

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS+=("-vv")
else
    PYTEST_ARGS+=("-v")
fi

# Add JUnit XML for CI
PYTEST_ARGS+=("--junitxml=test-results/junit.xml")

# Add color
PYTEST_ARGS+=("--color=yes")

# Execute tests
echo -e "${BLUE}Command: ${PYTEST_CMD} ${PYTEST_ARGS[*]}${NC}\n"

if $PYTEST_CMD "${PYTEST_ARGS[@]}"; then
    TEST_STATUS=0
    echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  All Tests Passed! ✓                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
else
    TEST_STATUS=$?
    echo -e "\n${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  Some Tests Failed ✗                      ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
fi

# Display coverage report location
if [ "$COVERAGE" = true ]; then
    echo -e "\n${BLUE}Coverage Reports:${NC}"
    echo -e "  HTML: ${YELLOW}htmlcov/index.html${NC}"
    echo -e "  XML:  ${YELLOW}coverage.xml${NC}"

    # Open HTML coverage report if available
    if command -v xdg-open >/dev/null 2>&1; then
        read -p "Open HTML coverage report? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            xdg-open htmlcov/index.html
        fi
    fi
fi

# Display test results location
echo -e "\n${BLUE}Test Results:${NC}"
echo -e "  JUnit XML: ${YELLOW}test-results/junit.xml${NC}"

# Run linting if all tests passed
if [ $TEST_STATUS -eq 0 ] && [ "$QUICK" = false ]; then
    echo -e "\n${YELLOW}Running code quality checks...${NC}"

    # Black
    echo -e "${BLUE}Running black...${NC}"
    black --check src/ tests/ || echo -e "${YELLOW}Black formatting issues found${NC}"

    # isort
    echo -e "${BLUE}Running isort...${NC}"
    isort --check-only src/ tests/ || echo -e "${YELLOW}Import sorting issues found${NC}"

    # flake8
    echo -e "${BLUE}Running flake8...${NC}"
    flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503 || echo -e "${YELLOW}Flake8 issues found${NC}"

    # pylint (only on src/)
    echo -e "${BLUE}Running pylint...${NC}"
    pylint src/ --max-line-length=100 --disable=C0111,R0903 || echo -e "${YELLOW}Pylint issues found${NC}"
fi

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Test Summary                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

# Parse test results
if [ -f "test-results/junit.xml" ]; then
    TESTS=$(grep -oP 'tests="\K[^"]+' test-results/junit.xml | head -1)
    FAILURES=$(grep -oP 'failures="\K[^"]+' test-results/junit.xml | head -1)
    ERRORS=$(grep -oP 'errors="\K[^"]+' test-results/junit.xml | head -1)

    echo -e "Total tests: ${BLUE}${TESTS}${NC}"

    if [ "$FAILURES" -eq 0 ] && [ "$ERRORS" -eq 0 ]; then
        echo -e "Failures: ${GREEN}${FAILURES}${NC}"
        echo -e "Errors: ${GREEN}${ERRORS}${NC}"
    else
        echo -e "Failures: ${RED}${FAILURES}${NC}"
        echo -e "Errors: ${RED}${ERRORS}${NC}"
    fi
fi

exit $TEST_STATUS
