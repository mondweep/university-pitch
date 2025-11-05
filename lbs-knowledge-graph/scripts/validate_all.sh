#!/bin/bash

# LBS Knowledge Graph - Comprehensive Validation Script
# Runs all validation checks on data, schema, and graph structure

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  LBS Knowledge Graph - Validation Suite   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

# Parse arguments
QUICK=false
FAIL_FAST=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK=true
            shift
            ;;
        --fail-fast)
            FAIL_FAST=true
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
            echo "  --quick       Skip time-consuming validations"
            echo "  --fail-fast   Stop on first validation error"
            echo "  --verbose     Show detailed output"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Create results directory
mkdir -p validation-results

# Track overall status
OVERALL_STATUS=0
VALIDATIONS_RUN=0
VALIDATIONS_PASSED=0
VALIDATIONS_FAILED=0

# Helper function to run validation
run_validation() {
    local name=$1
    local command=$2
    local output_file=$3

    VALIDATIONS_RUN=$((VALIDATIONS_RUN + 1))

    echo -e "\n${YELLOW}[${VALIDATIONS_RUN}]${NC} ${name}..."

    if [ "$VERBOSE" = true ]; then
        if eval "$command" | tee "$output_file"; then
            echo -e "${GREEN}✓${NC} ${name} passed"
            VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗${NC} ${name} failed"
            VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
            OVERALL_STATUS=1

            if [ "$FAIL_FAST" = true ]; then
                echo -e "${RED}Stopping due to --fail-fast${NC}"
                exit 1
            fi
            return 1
        fi
    else
        if eval "$command" > "$output_file" 2>&1; then
            echo -e "${GREEN}✓${NC} ${name} passed"
            VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗${NC} ${name} failed (see ${output_file})"
            VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
            OVERALL_STATUS=1

            if [ "$FAIL_FAST" = true ]; then
                echo -e "${RED}Stopping due to --fail-fast${NC}"
                cat "$output_file"
                exit 1
            fi
            return 1
        fi
    fi
}

# 1. Validate Schema Definitions
run_validation \
    "Schema validation" \
    "python scripts/validate_schema.py --schema-dir ./src/schema" \
    "validation-results/schema.log"

# 2. Validate Data Files
if [ -d "data/parsed" ]; then
    run_validation \
        "Data file validation" \
        "python scripts/validate_data.py --data-dir ./data/parsed --schema-dir ./src/schema" \
        "validation-results/data.log"
fi

# 3. Validate Graph Structure
if [ -f "data/graph/latest.json" ]; then
    run_validation \
        "Graph structure validation" \
        "python scripts/validate_graph.py --graph ./data/graph/latest.json" \
        "validation-results/graph.log"
elif [ -f "data/graph.json" ]; then
    run_validation \
        "Graph structure validation" \
        "python scripts/validate_graph.py --graph ./data/graph.json" \
        "validation-results/graph.log"
fi

# 4. Check for Duplicate Content
if [ -d "data/parsed" ]; then
    run_validation \
        "Duplicate content check" \
        "python scripts/check_duplicates.py --data-dir ./data/parsed" \
        "validation-results/duplicates.log"
fi

# 5. Validate URLs (quick mode skips actual HTTP requests)
if [ -f "data/urls.txt" ]; then
    if [ "$QUICK" = true ]; then
        run_validation \
            "URL format validation (quick)" \
            "python scripts/validate_urls.py --url-file ./data/urls.txt --quick" \
            "validation-results/urls.log"
    else
        run_validation \
            "URL validation (with HTTP checks)" \
            "python scripts/validate_urls.py --url-file ./data/urls.txt --timeout 10" \
            "validation-results/urls.log"
    fi
fi

# 6. Check Data Consistency
run_validation \
    "Data consistency check" \
    "python scripts/check_consistency.py --data-dir ./data" \
    "validation-results/consistency.log"

# 7. Validate JSON Syntax
if [ -d "data" ]; then
    echo -e "\n${YELLOW}[${VALIDATIONS_RUN}]${NC} JSON syntax validation..."
    VALIDATIONS_RUN=$((VALIDATIONS_RUN + 1))

    JSON_FILES=$(find data -name "*.json" 2>/dev/null || true)
    JSON_ERRORS=0

    for file in $JSON_FILES; do
        if ! python -m json.tool "$file" > /dev/null 2>&1; then
            echo -e "${RED}✗${NC} Invalid JSON: $file"
            JSON_ERRORS=$((JSON_ERRORS + 1))
        fi
    done

    if [ $JSON_ERRORS -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All JSON files valid"
        VALIDATIONS_PASSED=$((VALIDATIONS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Found $JSON_ERRORS invalid JSON files"
        VALIDATIONS_FAILED=$((VALIDATIONS_FAILED + 1))
        OVERALL_STATUS=1
    fi
fi

# 8. Check Graph Metrics (if not quick mode)
if [ "$QUICK" = false ] && [ -f "data/graph/latest.json" ]; then
    run_validation \
        "Graph metrics analysis" \
        "python scripts/analyze_graph_metrics.py --graph ./data/graph/latest.json" \
        "validation-results/metrics.log"
fi

# 9. Validate Relationships
if [ -f "data/graph/latest.json" ]; then
    run_validation \
        "Relationship validation" \
        "python scripts/validate_relationships.py --graph ./data/graph/latest.json" \
        "validation-results/relationships.log"
fi

# 10. Security Check
run_validation \
    "Security check (secrets detection)" \
    "python scripts/check_secrets.py --data-dir ./data" \
    "validation-results/security.log"

# Generate comprehensive report
echo -e "\n${YELLOW}Generating validation report...${NC}"
python scripts/generate_validation_report.py \
    --results-dir ./validation-results \
    --output ./validation-results/report.html \
    --format html

if [ -f "validation-results/report.html" ]; then
    echo -e "${GREEN}✓${NC} Validation report generated: validation-results/report.html"
fi

# Generate JSON summary
python scripts/generate_validation_report.py \
    --results-dir ./validation-results \
    --output ./validation-results/summary.json \
    --format json

# Display summary
echo -e "\n${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Validation Summary                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"

echo -e "\nTotal validations: ${BLUE}${VALIDATIONS_RUN}${NC}"
echo -e "Passed: ${GREEN}${VALIDATIONS_PASSED}${NC}"
echo -e "Failed: ${RED}${VALIDATIONS_FAILED}${NC}"

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  All Validations Passed! ✓                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
else
    echo -e "\n${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  Some Validations Failed ✗                ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}"

    echo -e "\n${YELLOW}Check detailed logs in:${NC}"
    echo -e "  validation-results/*.log"
    echo -e "  validation-results/report.html"
fi

# Open report if available (Linux only)
if [ $OVERALL_STATUS -ne 0 ] && [ -f "validation-results/report.html" ]; then
    if command -v xdg-open >/dev/null 2>&1; then
        read -p "Open validation report? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            xdg-open validation-results/report.html
        fi
    fi
fi

exit $OVERALL_STATUS
