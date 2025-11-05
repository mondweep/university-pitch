# LBS Semantic Knowledge Graph Platform

**London Business School - Content Discovery Enhancement**

## Overview

This project implements a semantic knowledge graph for London Business School's website (london.edu) to enhance content discovery, navigation, and personalization.

**Key Features:**
- 🕸️ Semantic knowledge graph using MGraph-DB
- 🤖 LLM-driven content enrichment (GPT-4/Claude)
- 🎨 Multiple UI prototypes for content exploration
- 👥 Personalized content delivery for different user personas
- 🔍 Advanced search and topic-based navigation
- 🛠️ Administrative curation tools

## Technology Stack

- **Graph Database:** MGraph-DB (Python, in-memory, serverless-optimized)
- **Backend:** Python 3.11, AWS Lambda, ECS Fargate
- **LLM:** OpenAI GPT-4 or Anthropic Claude
- **Frontend:** HTML/CSS/JS with D3.js visualization
- **Infrastructure:** AWS (serverless-first)
- **Storage:** S3, ElastiCache Serverless
- **Search:** OpenSearch Serverless

## Project Structure

```
lbs-knowledge-graph/
├── src/                      # Source code
│   ├── crawler/             # Web crawler for london.edu
│   ├── parser/              # HTML to JSON parser
│   ├── graph/               # MGraph-DB integration
│   ├── models/              # Data models
│   └── utils/               # Utilities
├── content-repo/            # Extracted content (Git-versioned)
│   ├── raw/                 # Raw HTML files
│   ├── parsed/              # Parsed JSON files
│   └── analysis/            # LLM analysis results
├── tests/                   # Test suites
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/                # End-to-end tests
├── scripts/                 # Utility scripts
├── config/                  # Configuration files
└── docs/                    # Documentation

```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- AWS CLI configured
- OpenAI or Anthropic API key

### Installation

```bash
# Clone repository
git clone <repository-url>
cd lbs-knowledge-graph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Running the Crawler

```bash
# Crawl 10 pages from london.edu
python scripts/crawl.py --urls urls.txt --limit 10

# Parse HTML to JSON
python scripts/parse.py --input content-repo/raw --output content-repo/parsed
```

### Building the Graph

```bash
# Build knowledge graph from parsed content
python scripts/build_graph.py --input content-repo/parsed --output graph/

# Export to multiple formats
python scripts/export_graph.py --format json,graphml,cypher
```

## Development Phases

This project follows a 10-phase, 25-week implementation plan:

| Phase | Duration | Focus |
|-------|----------|-------|
| 1 | Weeks 1-2 | Data Acquisition & Content Extraction |
| 2 | Weeks 3-4 | Content Parsing & Domain Modeling |
| 3 | Weeks 5-7 | Knowledge Graph Construction |
| 4 | Week 8 | CI/CD Setup |
| 5 | Weeks 9-12 | UI Prototypes |
| 6 | Weeks 13-15 | Semantic Enrichment (LLM) |
| 7 | Weeks 16-18 | Graph-Driven UIs |
| 8 | Weeks 19-20 | Personalization |
| 9 | Weeks 21-22 | Admin Tools |
| 10 | Weeks 23-25 | Autonomous Agents & Launch |

**Current Phase:** Phase 1 (Data Acquisition) - ✅ **COMPLETED**

**Phase 1 Status:** All deliverables complete, CI/CD operational, ready for Phase 2
**Completion Date:** November 5, 2025
**Documentation:** See `/docs/PHASE_1_STATUS.md` and `/docs/PHASE_1_CHECKLIST.md`

## Documentation

Comprehensive planning documentation is available in `/plans`:

- [00_PROJECT_OVERVIEW.md](/plans/00_PROJECT_OVERVIEW.md) - Executive summary
- [01_IMPLEMENTATION_PLAN.md](/plans/01_IMPLEMENTATION_PLAN.md) - Detailed implementation
- [02_SYSTEM_ARCHITECTURE.md](/plans/02_SYSTEM_ARCHITECTURE.md) - Technical architecture
- [03_TECHNICAL_SPECIFICATIONS.md](/plans/03_TECHNICAL_SPECIFICATIONS.md) - Technical specs
- [04_DATA_MODEL_SCHEMA.md](/plans/04_DATA_MODEL_SCHEMA.md) - Data models
- [05_API_SPECIFICATIONS.md](/plans/05_API_SPECIFICATIONS.md) - API documentation
- [06_DEPLOYMENT_PLAN.md](/plans/06_DEPLOYMENT_PLAN.md) - Deployment strategy
- [07_TESTING_STRATEGY.md](/plans/07_TESTING_STRATEGY.md) - Testing approach
- [08_PROJECT_TIMELINE.md](/plans/08_PROJECT_TIMELINE.md) - Project timeline
- [09_MGRAPH_INTEGRATION_GUIDE.md](/plans/09_MGRAPH_INTEGRATION_GUIDE.md) - MGraph guide

## Testing

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run all tests with coverage
pytest --cov=src --cov-report=html
```

## Deployment

See [06_DEPLOYMENT_PLAN.md](/plans/06_DEPLOYMENT_PLAN.md) for complete deployment instructions.

**Quick Deploy to AWS Lambda:**
```bash
./scripts/deploy-lambda.sh graph-query
```

## Contributing

This is a London Business School project. For internal team contributions:

1. Create feature branch from `main`
2. Implement changes with tests
3. Ensure all tests pass (`pytest`)
4. Submit pull request for review
5. Merge after approval

## License

Proprietary - London Business School

## Support

- **Technical Documentation:** `/plans` directory
- **Issue Tracker:** [Project Issues]
- **Team Contact:** [Project Lead]

---

**Built with ❤️ for London Business School**
