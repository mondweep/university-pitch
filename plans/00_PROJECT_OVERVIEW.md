# LBS Semantic Knowledge Graph - Project Overview

**Project Name:** London Business School Semantic Knowledge Graph Platform
**Target Website:** https://london.edu
**Client:** London Business School
**Created:** November 2025
**Version:** 1.0

## Executive Summary

This project aims to transform London Business School's web presence by implementing a semantic knowledge graph platform that enhances content discovery, navigation, and personalization. By extracting, structuring, and semantically enriching website content, we will create an intelligent layer that serves multiple user personas more effectively.

## Project Goals

1. **Enhanced Content Discovery** - Enable users to find relevant information faster through semantic search and topic-based navigation
2. **Improved Personalization** - Deliver tailored content experiences for different user personas (prospective students, current students, alumni, faculty, researchers)
3. **Semantic Intelligence** - Leverage LLM-driven analysis to extract topics, sentiment, and relationships from content
4. **Administrative Efficiency** - Provide tools for content managers to curate and refine the knowledge graph
5. **Future-Ready Architecture** - Build a platform that can evolve with autonomous AI agents and continuous improvement

## Key Components

### 1. Content Extraction Pipeline
- Automated crawling and HTML parsing of london.edu
- Next.js data extraction
- Content normalization and hash-based change detection
- CI/CD automation for continuous updates

### 2. Semantic Knowledge Graph
- M-Graph DB for lightweight, serverless graph storage
- Node types: Pages, Sections, Content Items, Topics, Categories
- Relationship types: contains, links_to, has_topic, is_of_type
- Semantic enrichment with LLM-generated metadata

### 3. User Interface Prototypes
- Text-only content views
- Interactive visualization dashboards
- Reconstructed static sites
- Ontology-based navigation
- Personalized portals
- Graph exploration interfaces

### 4. Administrative Tools
- Graph curation dashboard
- Manual annotation and override tools
- Quality reports and analytics
- Version control and audit trails

## Technology Stack

### Backend
- **Web Scraping:** Custom Node.js crawler with Puppeteer/Playwright
- **HTML Processing:** Cheerio/JSDOM for DOM parsing
- **Graph Database:** M-Graph DB (lightweight serverless)
- **LLM Integration:** OpenAI GPT-4/Claude for semantic analysis
- **CI/CD:** GitHub Actions

### Frontend
- **Framework:** Pure HTML/CSS/JS or Web Components
- **Visualization:** D3.js, Mermaid.js
- **Build Tool:** Vite or Parcel
- **Styling:** Tailwind CSS or vanilla CSS

### Data Storage
- **Raw Content:** Git-based content repository
- **Structured Data:** JSON files with version control
- **Graph Data:** M-Graph DB or JSON export format

## Project Phases

The project is structured in 10 phases, each building on previous work:

| Phase | Name | Duration | Key Deliverables |
|-------|------|----------|------------------|
| 1 | Data Acquisition | 2 weeks | HTML crawler, content extraction pipeline |
| 2 | Content Parsing | 2 weeks | Domain models, content normalization |
| 3 | Knowledge Graph | 3 weeks | Graph schema, populated database |
| 4 | CI/CD Setup | 1 week | Automated pipeline, version control |
| 5 | UI Prototypes | 4 weeks | Multiple interface modes |
| 6 | Semantic Enrichment | 3 weeks | LLM analysis, topic tagging |
| 7 | Graph-Driven UIs | 3 weeks | Advanced navigation, search |
| 8 | Personalization | 2 weeks | Persona-based views |
| 9 | Admin Tools | 2 weeks | Curation dashboard |
| 10 | Autonomous Agents | 3 weeks | AI-driven optimization |

**Total Duration:** ~25 weeks (~6 months)

## Success Criteria

1. **Coverage:** Successfully extract and structure content from 200+ key pages
2. **Accuracy:** 95%+ accuracy in topic tagging and categorization
3. **Performance:** Page load times < 2 seconds, graph queries < 500ms
4. **User Satisfaction:** Positive feedback from 80%+ of test users
5. **Automation:** 90%+ of updates automated through CI/CD
6. **Personalization:** 5+ distinct persona views with relevant content filtering

## Risk Management

### Technical Risks
- **Site Structure Changes:** Mitigated by flexible parsing and CI/CD monitoring
- **LLM Accuracy:** Mitigated by human review loops and validation
- **Performance:** Mitigated by caching, indexing, and optimization

### Operational Risks
- **Resource Availability:** Clear documentation and modular architecture
- **Scope Creep:** Phased approach with clear deliverables
- **Stakeholder Buy-in:** Regular demos and incremental value delivery

## Team Structure

### Core Team (Recommended)
- **Project Lead** (1) - Overall coordination and stakeholder management
- **Backend Engineers** (2) - Pipeline, graph database, LLM integration
- **Frontend Engineers** (2) - UI prototypes, visualizations
- **Data Scientist** (1) - Semantic analysis, LLM prompt engineering
- **UX Designer** (1) - Interface design, user testing
- **QA Engineer** (1) - Testing, quality assurance

### Extended Team
- **Content Manager** (LBS) - Domain expertise, curation
- **Technical Advisor** (LBS) - IT infrastructure, compliance
- **Stakeholder Representative** (LBS) - Requirements, feedback

## Budget Estimate

### Development Costs (6 months)
- Engineering Team: $300,000 - $400,000
- LLM API Costs: $5,000 - $10,000
- Infrastructure: $2,000 - $5,000
- Tools & Licenses: $3,000 - $5,000

**Total Estimated Budget:** $310,000 - $420,000

### Ongoing Costs (Annual)
- LLM API: $12,000 - $20,000
- Infrastructure: $6,000 - $12,000
- Maintenance: $50,000 - $80,000

## Next Steps

1. **Week 1-2:** Finalize technical architecture and tool selection
2. **Week 3-4:** Set up development environment and repositories
3. **Week 5-6:** Begin Phase 1 (Data Acquisition)
4. **Week 7:** First demo of extracted content
5. **Week 12:** Midpoint review with working graph and basic UI
6. **Week 20:** User testing of personalized experiences
7. **Week 25:** Final delivery and handoff

## Documentation Structure

This planning repository contains the following documents:

```
plans/
├── 00_PROJECT_OVERVIEW.md (this file)
├── 01_IMPLEMENTATION_PLAN.md
├── 02_SYSTEM_ARCHITECTURE.md
├── 03_TECHNICAL_SPECIFICATIONS.md
├── 04_DATA_MODEL_SCHEMA.md
├── 05_API_SPECIFICATIONS.md
├── 06_DEPLOYMENT_PLAN.md
├── 07_TESTING_STRATEGY.md
├── 08_PROJECT_TIMELINE.md
├── 09_TECHNOLOGY_STACK.md
├── 10_RISK_MANAGEMENT.md
└── 11_SUCCESS_METRICS.md
```

## References

- **Original PRD:** `/workspaces/university-pitch/Research/PRD_Using Semantic Knowledge Graphs for London Business School's Content Discovery.md`
- **Target Website:** https://london.edu
- **LBS About:** https://london.edu/about
- **LBS Programs:** https://london.edu/programmes

---

**Prepared by:** Development Team
**Last Updated:** November 2025
