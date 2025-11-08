# LBS Semantic Knowledge Graph Platform

**London Business School - Content Discovery Enhancement**

> 📁 **Project Location**: All source code and development happens in the `/lbs-knowledge-graph` directory. This README provides an overview and navigation to detailed documentation.

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

**Note**: All development happens in the `lbs-knowledge-graph/` subdirectory.

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

## Demonstrating Value to Stakeholders

**Want to see the expected value in action?** We've built interactive demos that showcase the three key benefits:

```bash
cd lbs-knowledge-graph

# Run all demos (20-30 minutes)
python demos/run_all_demos.py

# Or run individually:
python demos/demo_1_enhanced_discovery.py    # 🔍 Topic navigation & search
python demos/demo_2_personalization.py        # 👤 Persona-based content filtering
python demos/demo_3_content_strategy.py       # 📊 Data-driven insights for content teams
```

**What's Demonstrated**:
- ✅ Enhanced content discovery (topic browsing, related content, contextual search)
- ✅ Personalized experiences (5 user personas, tailored recommendations)
- ✅ Data-driven content strategy (health metrics, gap analysis, performance insights)

**Complete Guide**: See [Value Demonstration Guide](lbs-knowledge-graph/docs/VALUE_DEMONSTRATION_GUIDE.md) for detailed usage, audience-specific presentation tips, and how to customize demos.

## Visualizing the Graph

The knowledge graph contains 3,963 nodes and 3,953 edges. We provide multiple visualization tools optimized for different use cases.

**Note**: Commands work from either the repository root or the `lbs-knowledge-graph/` directory (auto-detects location).

### Quick Statistics (Terminal-Based)

```bash
# View graph statistics (no dependencies)
python lbs-knowledge-graph/scripts/visualize_graph_stats.py

# Detailed view with samples
python lbs-knowledge-graph/scripts/visualize_graph_stats.py --verbose
```

**Output**: Node/edge counts, type distributions, most connected nodes

### Interactive HTML Visualization

```bash
# Install visualization library (one-time)
pip install pyvis

# Filtered view (RECOMMENDED - fast and clear)
python lbs-knowledge-graph/scripts/visualize_graph_interactive.py --node-types Page,Section --max-nodes 50

# Focus on specific page
python lbs-knowledge-graph/scripts/visualize_graph_interactive.py --focus-node "alumni_a812cbeb0b88"

# Open in browser
open lbs-knowledge-graph/visualizations/graph_interactive.html  # Mac
xdg-open lbs-knowledge-graph/visualizations/graph_interactive.html  # Linux
```

**Features**:
- Interactive drag-and-drop nodes
- Color-coded by type (Page=red, Section=blue, ContentItem=green)
- Hover for details
- Zoom and pan navigation
- Filter by node type and connection count

**Performance Note**: The full graph (3,963 nodes) is too large to visualize all at once. Use filtered views for best performance.

**Complete Guide**: See [Graph Visualization Guide](lbs-knowledge-graph/docs/GRAPH_VISUALIZATION_GUIDE.md) for detailed instructions, use cases, and troubleshooting.

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

**Current Phase:** Phase 3 (Semantic Enrichment) - ✅ **COMPLETED**

### Progress Summary

| Phase | Status | Completion Date | Documentation |
|-------|--------|----------------|---------------|
| **Phase 1** | ✅ Complete | Nov 5, 2025 | [Phase 1 Status](lbs-knowledge-graph/docs/PHASE_1_COMPLETE_SWARM_REPORT.md) |
| **Phase 2** | ✅ Complete | Nov 6, 2025 | [Phase 2 Status](lbs-knowledge-graph/docs/PHASE_2_COMPLETE_SWARM_REPORT.md) |
| **Phase 3** | ✅ Complete | Nov 7, 2025 | [Phase 3 Status](lbs-knowledge-graph/docs/PHASE_3_COMPLETE_SWARM_REPORT.md) |
| **Phase 4** | 🔜 Next | - | CI/CD Enhancement |

### What We've Built

- **Knowledge Graph**: 3,963 nodes, 3,953 edges representing LBS website structure
- **Semantic Enrichment**: Sentiment analysis & topic extraction pipelines (production-ready)
- **LLM Integration**: OpenRouter API with GPT-3.5-turbo and Claude 3.5 Sonnet
- **Cost Efficiency**: Full enrichment pipeline for ~$14 (tested and validated)

## Documentation

### 📚 Quick Navigation

**New to the project? Start here:**
1. 📋 [Project Overview](plans/00_PROJECT_OVERVIEW.md) - What we're building and why
2. 📊 [Current Status](#progress-summary) - Where we are now (see above)
3. 🧪 [Testing Guide](lbs-knowledge-graph/docs/TESTING_GUIDE.md) - How to test the system
4. 🚀 [Quick Start Testing](lbs-knowledge-graph/docs/QUICK_START_TESTING.md) - 5-minute setup

**Phase Completion Reports:**
- ✅ [Phase 1: Data Acquisition](lbs-knowledge-graph/docs/PHASE_1_COMPLETE_SWARM_REPORT.md) - Web crawling & content extraction (3,963 nodes)
- ✅ [Phase 2: Domain Modeling](lbs-knowledge-graph/docs/PHASE_2_COMPLETE_SWARM_REPORT.md) - Graph construction (3,953 edges)
- ✅ [Phase 3: Semantic Enrichment](lbs-knowledge-graph/docs/PHASE_3_COMPLETE_SWARM_REPORT.md) - LLM integration & topic extraction

**Testing & Validation:**
- 🧪 [Enrichment Test Results](lbs-knowledge-graph/docs/ENRICHMENT_TEST_RESULTS.md) - **Production-ready validation** (100% success rate)
- 📊 [Sentiment Analysis Tests](lbs-knowledge-graph/docs/SENTIMENT_TEST_SUCCESS.md) - $0.15 for full graph
- 🏷️ [Topic Extraction Tests](lbs-knowledge-graph/docs/TOPIC_EXTRACTION_RESULTS.md) - $13.73 for full graph
- 🔍 [Infrastructure Test Results](lbs-knowledge-graph/docs/INFRASTRUCTURE_TEST_RESULTS.md) - System health check
- ✅ [Infrastructure Fixes Complete](lbs-knowledge-graph/docs/INFRASTRUCTURE_FIXES_COMPLETE.md) - 100% test collection

**API & Integration:**
- 🤖 [Using Claude Instead of OpenAI](lbs-knowledge-graph/docs/USING_CLAUDE_INSTEAD_OF_OPENAI.md) - API provider options
- 🔌 [OpenRouter Demo Ready](lbs-knowledge-graph/docs/OPENROUTER_DEMO_READY.md) - Production API integration
- 🆓 [Free Embedding Options](lbs-knowledge-graph/docs/FREE_EMBEDDING_OPTIONS.md) - Local embeddings (Sentence-Transformers)
- 📦 [Demo Ready Embeddings](lbs-knowledge-graph/docs/DEMO_READY_EMBEDDINGS.md) - Embeddings validation

**Detailed Testing Guides:**
- 📋 [Testing Guide (20,000+ words)](lbs-knowledge-graph/docs/TESTING_GUIDE.md) - Comprehensive 4-level testing strategy
- ⚡ [Quick Start Testing](lbs-knowledge-graph/docs/QUICK_START_TESTING.md) - Get started in 5 minutes
- ✅ [Test Execution Checklist](lbs-knowledge-graph/docs/TEST_EXECUTION_CHECKLIST.md) - Step-by-step testing tracker

**Visualization & Exploration:**
- 🎨 [Graph Visualization Guide](lbs-knowledge-graph/docs/GRAPH_VISUALIZATION_GUIDE.md) - **Complete guide to visualizing the 3,963-node graph**
  - Terminal statistics viewer (no dependencies)
  - Interactive HTML visualization (pyvis)
  - Filtering and performance optimization
  - Use cases and troubleshooting

**Value Demonstration:**
- 💎 [Value Demonstration Guide](lbs-knowledge-graph/docs/VALUE_DEMONSTRATION_GUIDE.md) - **How to demonstrate expected value to stakeholders**
  - 3 interactive demos (enhanced discovery, personalization, content strategy)
  - Audience-specific presentation strategies
  - Key metrics and talking points
  - Customization guide

### 📁 Planning Documents

Comprehensive planning documentation in `/plans`:

- [00_PROJECT_OVERVIEW.md](plans/00_PROJECT_OVERVIEW.md) - Executive summary
- [01_IMPLEMENTATION_PLAN.md](plans/01_IMPLEMENTATION_PLAN.md) - Detailed implementation (10 phases, 25 weeks)
- [02_SYSTEM_ARCHITECTURE.md](plans/02_SYSTEM_ARCHITECTURE.md) - Technical architecture (AWS serverless)
- [03_TECHNICAL_SPECIFICATIONS.md](plans/03_TECHNICAL_SPECIFICATIONS.md) - Technical specs
- [04_DATA_MODEL_SCHEMA.md](plans/04_DATA_MODEL_SCHEMA.md) - Data models (Page, Section, ContentItem)
- [05_API_SPECIFICATIONS.md](plans/05_API_SPECIFICATIONS.md) - API documentation
- [06_DEPLOYMENT_PLAN.md](plans/06_DEPLOYMENT_PLAN.md) - AWS deployment strategy
- [07_TESTING_STRATEGY.md](plans/07_TESTING_STRATEGY.md) - Testing approach
- [08_PROJECT_TIMELINE.md](plans/08_PROJECT_TIMELINE.md) - Project timeline
- [09_MGRAPH_INTEGRATION_GUIDE.md](plans/09_MGRAPH_INTEGRATION_GUIDE.md) - MGraph database guide

## Enrichment Pipelines (Production Ready)

We've successfully tested and validated two enrichment pipelines:

### 1. Sentiment Analysis ✅
- **Model**: GPT-3.5-turbo via OpenRouter
- **Success Rate**: 100% (17 items tested)
- **Cost**: $0.000038 per item → $0.15 for full graph
- **Performance**: 2.3 items/second
- **Status**: Production ready

### 2. Topic Extraction ✅
- **Model**: Claude 3.5 Sonnet via OpenRouter
- **Success Rate**: 100% (10 pages tested)
- **Cost**: $0.003464 per page → $13.73 for full graph
- **Topics**: 3.6 avg per page, 27 unique topics identified
- **Status**: Production ready

**Total Cost Estimate**: ~$14 for complete enrichment of 3,963 pages

See [Enrichment Test Results](lbs-knowledge-graph/docs/ENRICHMENT_TEST_RESULTS.md) for full details.

### Running Enrichment Tests

**Note**: Run these commands from the `lbs-knowledge-graph/` directory.

```bash
# Test sentiment analysis (17 items)
python scripts/test_sentiment_scale.py

# Test topic extraction (10 pages)
python scripts/test_topic_extraction.py

# View detailed results
cat data/test_results/sentiment_scale_test.json | jq .
cat data/test_results/topic_extraction_test.json | jq .
```

## Testing

**Note**: Run these commands from the `lbs-knowledge-graph/` directory.

**Quick Start** (recommended for newcomers):
```bash
# 5-minute quick start
pytest tests/ -v --tb=short -k "not slow"
```

**Comprehensive Testing** (4 levels):
```bash
# Level 1: Infrastructure (no API key needed)
pytest tests/unit -v -m "not integration"
python scripts/validate_graph.py --graph data/graph/graph.json

# Level 2: Integration (small-scale, $0.10-$0.25)
python scripts/test_small_scale.py --pages 5

# Level 3: Full Pipeline (complete enrichment, ~$14)
python scripts/run_enrichment_pipeline.py --enrichments sentiment,topics

# Level 4: Manual Validation
# See docs/TESTING_GUIDE.md for detailed checklist
```

**Test Coverage**:
```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html

# Current status: 431 tests collectible, 1 minor fixture issue
```

See [TESTING_GUIDE.md](lbs-knowledge-graph/docs/TESTING_GUIDE.md) for comprehensive testing documentation.

## Deployment

See [06_DEPLOYMENT_PLAN.md](plans/06_DEPLOYMENT_PLAN.md) for complete deployment instructions.

**Quick Deploy to AWS Lambda:**
```bash
./scripts/deploy-lambda.sh graph-query
```

## Contributing

This is a London Business School project. For internal team contributions:

1. **Setup Git Hooks** (first time only):
   ```bash
   cd lbs-knowledge-graph
   ./scripts/setup-git-hooks.sh
   ```
   This installs a pre-commit hook that reminds you to update README.md when needed.

2. Create feature branch from `main`
3. Implement changes with tests
4. Ensure all tests pass (`pytest`)
5. **Update README.md** if you:
   - Add new documentation files
   - Complete a phase
   - Add new test scripts or enrichments
   - Make major feature changes
6. Submit pull request for review
7. Merge after approval

**Note**: The pre-commit hook will remind you if README updates are needed. See [Git Hooks Guide](lbs-knowledge-graph/docs/GIT_HOOKS_GUIDE.md) for details.

## License

MIT License

Copyright (c) 2025 London Business School

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Support

- **Technical Documentation:** `/plans` directory
- **Issue Tracker:** [Project Issues]
- **Team Contact:** [Project Lead]

---

**Built with ❤️ for London Business School**
