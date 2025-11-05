#!/bin/bash

# LBS Knowledge Graph - One-Command Project Setup
# This script sets up the complete development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  LBS Knowledge Graph - Setup Script       ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"

# Check prerequisites
echo -e "\n${YELLOW}[1/8]${NC} Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python 3 is required but not installed.${NC}" >&2; exit 1; }
command -v git >/dev/null 2>&1 || { echo -e "${RED}Git is required but not installed.${NC}" >&2; exit 1; }

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python ${PYTHON_VERSION} found"

# Check for Docker (optional)
if command -v docker >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker found"
    DOCKER_AVAILABLE=true
else
    echo -e "${YELLOW}!${NC} Docker not found (optional, but recommended)"
    DOCKER_AVAILABLE=false
fi

# Create virtual environment
echo -e "\n${YELLOW}[2/8]${NC} Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "\n${YELLOW}[3/8]${NC} Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓${NC} Pip upgraded"

# Install dependencies
echo -e "\n${YELLOW}[4/8]${NC} Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓${NC} Core dependencies installed"
else
    echo -e "${YELLOW}!${NC} requirements.txt not found, skipping"
fi

if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
    echo -e "${GREEN}✓${NC} Development dependencies installed"
else
    echo -e "${YELLOW}!${NC} requirements-dev.txt not found, skipping"
fi

# Install pre-commit hooks
echo -e "\n${YELLOW}[5/8]${NC} Installing pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    git init 2>/dev/null || true
    pre-commit install
    echo -e "${GREEN}✓${NC} Pre-commit hooks installed"
else
    echo -e "${YELLOW}!${NC} .pre-commit-config.yaml not found, skipping"
fi

# Create directory structure
echo -e "\n${YELLOW}[6/8]${NC} Creating directory structure..."
mkdir -p data/{raw,parsed,graph,exports,backups}
mkdir -p logs
mkdir -p .cache
mkdir -p validation-results
echo -e "${GREEN}✓${NC} Directories created"

# Set up environment file
echo -e "\n${YELLOW}[7/8]${NC} Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Environment Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
PYTHONPATH=.

# Database
REDIS_URL=redis://localhost:6379
OPENSEARCH_URL=http://localhost:9200

# API Keys (replace with your keys)
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# AWS (for deployment)
AWS_REGION=us-east-1
S3_BUCKET=lbs-kg-content

# Rate Limiting
CRAWLER_DELAY=1.0
MAX_CONCURRENT_REQUESTS=5
EOF
    echo -e "${GREEN}✓${NC} .env file created (please update with your API keys)"
else
    echo -e "${GREEN}✓${NC} .env file already exists"
fi

# Docker setup (optional)
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "\n${YELLOW}[8/8]${NC} Setting up Docker environment..."

    read -p "Do you want to start Docker containers? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose up -d redis opensearch
        echo -e "${GREEN}✓${NC} Docker containers started"
        echo -e "${YELLOW}Waiting for services to be ready...${NC}"
        sleep 10
    else
        echo -e "${YELLOW}!${NC} Skipping Docker setup"
    fi
else
    echo -e "\n${YELLOW}[8/8]${NC} Skipping Docker setup (Docker not available)"
fi

# Run initial tests
echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Running Initial Tests                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"

if [ -d "tests" ]; then
    pytest tests/unit -v --exitfirst || echo -e "${YELLOW}Some tests failed (this is normal for initial setup)${NC}"
else
    echo -e "${YELLOW}No tests directory found${NC}"
fi

# Display summary
echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup Complete!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"

echo -e "\n${GREEN}Next steps:${NC}"
echo -e "  1. Update .env file with your API keys"
echo -e "  2. Activate virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "  3. Run tests: ${YELLOW}./scripts/run_tests.sh${NC}"
echo -e "  4. Start crawler: ${YELLOW}python -m src.crawler.main${NC}"
echo -e "  5. Build graph: ${YELLOW}python scripts/build_graph.py${NC}"

if [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "\n${GREEN}Docker services:${NC}"
    echo -e "  - Redis: ${YELLOW}localhost:6379${NC}"
    echo -e "  - OpenSearch: ${YELLOW}http://localhost:9200${NC}"
    echo -e "  - OpenSearch Dashboards: ${YELLOW}http://localhost:5601${NC}"
fi

echo -e "\n${GREEN}For more information, see:${NC}"
echo -e "  - README.md"
echo -e "  - plans/06_DEPLOYMENT_PLAN.md"
echo -e "  - docs/development.md"

echo -e "\n${GREEN}Happy coding! 🚀${NC}"
