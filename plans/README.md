# LBS Semantic Knowledge Graph - Planning Documents

**Project:** London Business School Semantic Knowledge Graph Platform
**Target Website:** https://london.edu
**Version:** 1.0
**Last Updated:** November 2025

---

## 📋 Overview

This directory contains comprehensive planning documentation for the LBS Semantic Knowledge Graph project. These documents provide detailed specifications, architectures, timelines, and implementation guidance for building a semantic knowledge graph platform that enhances content discovery and navigation for London Business School's website.

**Key Features:**
- Semantic knowledge graph using **MGraph-DB**
- LLM-driven content enrichment
- Multiple user interface prototypes
- Personalized content delivery
- Advanced search and discovery
- Administrative curation tools

**Technologies:**
- **Graph Database:** MGraph-DB (Python, serverless-optimized)
- **Backend:** Python 3.11, AWS Lambda, ECS Fargate
- **Frontend:** HTML/CSS/JS or React
- **LLM:** OpenAI GPT-4 or Anthropic Claude
- **Visualization:** D3.js, Cytoscape.js
- **Infrastructure:** AWS (serverless-first)

---

## 📚 Document Index

### Core Planning Documents

| # | Document | Purpose | Audience | Status |
|---|----------|---------|----------|--------|
| 00 | [Project Overview](./00_PROJECT_OVERVIEW.md) | Executive summary, goals, team structure | All stakeholders | ✅ Complete |
| 01 | [Implementation Plan](./01_IMPLEMENTATION_PLAN.md) | Phase-by-phase, page-by-page implementation | Development team | ✅ Complete |
| 02 | [System Architecture](./02_SYSTEM_ARCHITECTURE.md) | Technical architecture, components, data flow | Architects, developers | ✅ Complete |
| 03 | [Technical Specifications](./03_TECHNICAL_SPECIFICATIONS.md) | Requirements, data models, APIs | Developers, QA | ✅ Complete |
| 04 | [Data Model & Schema](./04_DATA_MODEL_SCHEMA.md) | Graph schema, entities, relationships | Data architects | ✅ Complete |
| 05 | [API Specifications](./05_API_SPECIFICATIONS.md) | REST/GraphQL APIs, endpoints, formats | Frontend & backend | ✅ Complete |
| 06 | [Deployment Plan](./06_DEPLOYMENT_PLAN.md) | Infrastructure, CI/CD, serverless architecture | DevOps, operations | ✅ Complete |
| 07 | [Testing Strategy](./07_TESTING_STRATEGY.md) | Testing levels, frameworks, quality gates | QA, developers | ✅ Complete |
| 08 | [Project Timeline](./08_PROJECT_TIMELINE.md) | 25-week timeline, milestones, resources | PM, stakeholders | ✅ Complete |
| 09 | [MGraph Integration](./09_MGRAPH_INTEGRATION_GUIDE.md) | MGraph-DB integration, code examples | Developers | ✅ Complete |

---

## 🎯 Quick Start Guide

### For Project Managers
1. Start with [00_PROJECT_OVERVIEW](./00_PROJECT_OVERVIEW.md) for executive summary
2. Review [08_PROJECT_TIMELINE](./08_PROJECT_TIMELINE.md) for schedule and milestones
3. Check [01_IMPLEMENTATION_PLAN](./01_IMPLEMENTATION_PLAN.md) for detailed phase breakdown

### For Architects & Tech Leads
1. Read [02_SYSTEM_ARCHITECTURE](./02_SYSTEM_ARCHITECTURE.md) for overall design
2. Study [04_DATA_MODEL_SCHEMA](./04_DATA_MODEL_SCHEMA.md) for graph structure
3. Review [09_MGRAPH_INTEGRATION_GUIDE](./09_MGRAPH_INTEGRATION_GUIDE.md) for MGraph details

### For Developers
1. Begin with [03_TECHNICAL_SPECIFICATIONS](./03_TECHNICAL_SPECIFICATIONS.md)
2. Reference [05_API_SPECIFICATIONS](./05_API_SPECIFICATIONS.md) for API contracts
3. Follow [09_MGRAPH_INTEGRATION_GUIDE](./09_MGRAPH_INTEGRATION_GUIDE.md) for graph database
4. Use [07_TESTING_STRATEGY](./07_TESTING_STRATEGY.md) for testing approach

### For DevOps Engineers
1. Study [06_DEPLOYMENT_PLAN](./06_DEPLOYMENT_PLAN.md) for infrastructure
2. Review [02_SYSTEM_ARCHITECTURE](./02_SYSTEM_ARCHITECTURE.md) for component layout
3. Check [08_PROJECT_TIMELINE](./08_PROJECT_TIMELINE.md) for deployment schedule

---

## 🗺️ Document Roadmap

### Phase 1-2 (Weeks 1-4): Data Acquisition
**Primary Documents:**
- [01_IMPLEMENTATION_PLAN](./01_IMPLEMENTATION_PLAN.md) - Phases 1-2
- [03_TECHNICAL_SPECIFICATIONS](./03_TECHNICAL_SPECIFICATIONS.md) - Data specs
- [07_TESTING_STRATEGY](./07_TESTING_STRATEGY.md) - Unit tests

### Phase 3-4 (Weeks 5-8): Graph Construction
**Primary Documents:**
- [04_DATA_MODEL_SCHEMA](./04_DATA_MODEL_SCHEMA.md) - Graph design
- [09_MGRAPH_INTEGRATION_GUIDE](./09_MGRAPH_INTEGRATION_GUIDE.md) - Implementation
- [06_DEPLOYMENT_PLAN](./06_DEPLOYMENT_PLAN.md) - CI/CD setup

### Phase 5-7 (Weeks 9-18): User Interfaces
**Primary Documents:**
- [02_SYSTEM_ARCHITECTURE](./02_SYSTEM_ARCHITECTURE.md) - UI architecture
- [05_API_SPECIFICATIONS](./05_API_SPECIFICATIONS.md) - API integration
- [03_TECHNICAL_SPECIFICATIONS](./03_TECHNICAL_SPECIFICATIONS.md) - UI specs

### Phase 8-10 (Weeks 19-25): Polish & Launch
**Primary Documents:**
- [08_PROJECT_TIMELINE](./08_PROJECT_TIMELINE.md) - Launch checklist
- [06_DEPLOYMENT_PLAN](./06_DEPLOYMENT_PLAN.md) - Production deployment
- [07_TESTING_STRATEGY](./07_TESTING_STRATEGY.md) - E2E testing

---

## 📊 Key Project Metrics

### Scope
- **Pages:** 200+ key pages initially, expandable to 1000+
- **Graph Nodes:** 5,000+ nodes (Pages, Sections, Content, Topics)
- **Topics:** 50+ semantic topics
- **Personas:** 5+ user personas

### Timeline
- **Duration:** 25 weeks (~6 months)
- **Team Size:** 6-8 people
- **Phases:** 10 phases

### Budget
- **Development:** $310,000 - $420,000 (6 months)
- **Monthly Ops:** $434 - $634/month (serverless architecture)
- **Infrastructure:** AWS serverless (Lambda, S3, ElastiCache)

### Technology Stack
- **Graph DB:** MGraph-DB (Python, in-memory, O(1) lookups)
- **LLM:** OpenAI GPT-4 or Anthropic Claude
- **Backend:** Python 3.11, AWS Lambda, ECS Fargate
- **Frontend:** HTML/CSS/JS or React, D3.js
- **Storage:** S3, ElastiCache Serverless
- **Search:** OpenSearch Serverless

---

## 🔗 External Resources

### MGraph-DB
- **GitHub:** https://github.com/owasp-sbot/MGraph-DB
- **NotebookLM:** https://notebooklm.google.com/notebook/176509f4-485a-4003-adf0-1d7601cbbb33
- **Documentation:** See [09_MGRAPH_INTEGRATION_GUIDE](./09_MGRAPH_INTEGRATION_GUIDE.md)

### LBS Website
- **Target:** https://london.edu
- **About:** https://london.edu/about
- **Programmes:** https://london.edu/programmes

### Original Requirements
- **PRD:** `/workspaces/university-pitch/Research/PRD_Using Semantic Knowledge Graphs for London Business School's Content Discovery.md`

---

## 📖 Document Summaries

### [00_PROJECT_OVERVIEW.md](./00_PROJECT_OVERVIEW.md)
**What:** Executive summary of the entire project
**Includes:** Goals, components, technology stack, team structure, budget, success criteria
**Read Time:** 10 minutes
**Key Sections:** Executive Summary, Project Goals, Technology Stack, Budget

### [01_IMPLEMENTATION_PLAN.md](./01_IMPLEMENTATION_PLAN.md)
**What:** Detailed, page-by-page implementation breakdown
**Includes:** 10 phases, 40+ pages of tasks, acceptance criteria, deliverables
**Read Time:** 30 minutes
**Key Sections:** Phase breakdowns, Task lists, Checklists

### [02_SYSTEM_ARCHITECTURE.md](./02_SYSTEM_ARCHITECTURE.md)
**What:** Complete technical architecture
**Includes:** Component diagrams, data flows, deployment architecture, technology decisions
**Read Time:** 25 minutes
**Key Sections:** Architecture diagrams, Component descriptions, Integration points

### [03_TECHNICAL_SPECIFICATIONS.md](./03_TECHNICAL_SPECIFICATIONS.md)
**What:** Detailed technical requirements
**Includes:** Functional/non-functional requirements, data models, API specs, file formats
**Read Time:** 30 minutes
**Key Sections:** Requirements, Data specifications, Processing specs

### [04_DATA_MODEL_SCHEMA.md](./04_DATA_MODEL_SCHEMA.md)
**What:** Complete graph schema and data model
**Includes:** Entity definitions, relationships, TypeScript interfaces, validation rules
**Read Time:** 25 minutes
**Key Sections:** Entity models, Relationships, Graph schema, Validation

### [05_API_SPECIFICATIONS.md](./05_API_SPECIFICATIONS.md)
**What:** Complete API documentation
**Includes:** REST endpoints, GraphQL schema, request/response formats, error codes
**Read Time:** 35 minutes
**Key Sections:** Endpoint specs, Examples, Error handling, Rate limiting

### [06_DEPLOYMENT_PLAN.md](./06_DEPLOYMENT_PLAN.md)
**What:** Infrastructure and deployment strategy
**Includes:** Serverless architecture, CI/CD pipelines, monitoring, cost estimates
**Read Time:** 30 minutes
**Key Sections:** Infrastructure architecture, CI/CD, Monitoring, Costs

### [07_TESTING_STRATEGY.md](./07_TESTING_STRATEGY.md)
**What:** Comprehensive testing approach
**Includes:** Unit, integration, E2E testing, performance testing, quality gates
**Read Time:** 25 minutes
**Key Sections:** Test levels, Frameworks, CI integration, Coverage requirements

### [08_PROJECT_TIMELINE.md](./08_PROJECT_TIMELINE.md)
**What:** 25-week project timeline
**Includes:** Phase schedules, milestones, resource allocation, risk management
**Read Time:** 20 minutes
**Key Sections:** Timeline overview, Phase details, Milestones, Resource allocation

### [09_MGRAPH_INTEGRATION_GUIDE.md](./09_MGRAPH_INTEGRATION_GUIDE.md)
**What:** MGraph-DB integration guide
**Includes:** Setup, code examples, Lambda integration, export formats, best practices
**Read Time:** 30 minutes
**Key Sections:** Installation, Implementation, AWS Lambda, Best practices

---

## 🎨 Visual Aids

### Architecture Diagram
See [02_SYSTEM_ARCHITECTURE.md](./02_SYSTEM_ARCHITECTURE.md) for detailed diagrams of:
- Overall system architecture
- Data flow diagrams
- Deployment architecture
- Component interactions

### Timeline Visualization
See [08_PROJECT_TIMELINE.md](./08_PROJECT_TIMELINE.md) for:
- 25-week timeline visualization
- Phase dependencies
- Resource allocation
- Critical path

### Graph Schema
See [04_DATA_MODEL_SCHEMA.md](./04_DATA_MODEL_SCHEMA.md) for:
- Entity-relationship diagram
- Graph schema (Cypher notation)
- Data transformation flows

---

## ✅ Implementation Checklist

### Pre-Project
- [ ] Review all planning documents
- [ ] Secure stakeholder approvals
- [ ] Provision AWS accounts
- [ ] Obtain LLM API access
- [ ] Assemble team
- [ ] Set up development environments

### Phase 1-2 (Weeks 1-4)
- [ ] HTML crawler operational
- [ ] Content extraction pipeline working
- [ ] Domain model validated
- [ ] Content repository initialized

### Phase 3-4 (Weeks 5-8)
- [ ] MGraph-DB integrated
- [ ] Knowledge graph populated (500+ nodes)
- [ ] CI/CD pipeline operational
- [ ] Automated crawls scheduled

### Phase 5-7 (Weeks 9-18)
- [ ] 3+ UI prototypes built
- [ ] Semantic enrichment complete (90%+ accuracy)
- [ ] Advanced UIs operational
- [ ] Graph query interface working

### Phase 8-10 (Weeks 19-25)
- [ ] Personalization for 5+ personas
- [ ] Admin tools operational
- [ ] Autonomous agents deployed
- [ ] Production launch successful

---

## 📞 Contact & Support

### Project Team
- **Project Lead:** [TBD]
- **Technical Architect:** [TBD]
- **LBS Stakeholder:** [TBD]

### Documentation Updates
- **Version:** 1.0
- **Last Updated:** November 2025
- **Next Review:** Project kickoff

### Questions?
For questions about these planning documents:
1. Check the relevant document's detailed content
2. Review the [00_PROJECT_OVERVIEW](./00_PROJECT_OVERVIEW.md) for high-level context
3. Contact the project lead

---

## 📝 Document Change Log

| Date | Document | Changes | Author |
|------|----------|---------|--------|
| Nov 2025 | All | Initial creation | Development Team |
| [TBD] | - | - | - |

---

## 🚀 Next Steps

1. **Week 0:** Review and approve all planning documents
2. **Week 1:** Project kickoff, team onboarding
3. **Week 1-2:** Begin Phase 1 (Data Acquisition)
4. **Week 7:** First major demo (Knowledge Graph)
5. **Week 12:** Midpoint review (UI Prototypes)
6. **Week 25:** **Production Launch** 🎉

---

**Ready to build the future of content discovery for London Business School!**

---

*This README serves as the master index for all planning documentation. For detailed information, refer to the individual documents listed above.*
