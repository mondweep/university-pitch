# Implementation Plan - Page-by-Page Breakdown

## Overview

This document provides a detailed, page-wise implementation plan for the LBS Semantic Knowledge Graph project. Each phase is broken down into specific pages, tasks, and acceptance criteria.

---

## Phase 1: Data Acquisition and Content Extraction (Weeks 1-2)

### Objective
Gather the initial corpus of LBS website content and convert it into a structured format suitable for analysis.

### Page 1.1: Project Setup
**Tasks:**
- Set up GitHub repositories (Code, Content, UI)
- Configure development environments
- Install dependencies (Node.js, Python, Git)
- Set up version control workflows
- Create project documentation structure

**Deliverables:**
- Three GitHub repositories initialized
- README files with setup instructions
- Development environment configuration files
- Team access and permissions configured

**Acceptance Criteria:**
- ✅ All team members can clone and run the projects
- ✅ CI/CD pipelines are configured
- ✅ Documentation is accessible and complete

---

### Page 1.2: HTML Fetcher Development
**Tasks:**
- Develop HTTP client for fetching LBS pages
- Implement proxy/crawler functionality
- Create URL queue management system
- Add rate limiting and politeness policies
- Implement error handling and retry logic
- Store raw HTML to Content Repository

**Target Pages (Initial Set):**
1. https://london.edu (Homepage)
2. https://london.edu/about
3. https://london.edu/programmes
4. https://london.edu/faculty-and-research
5. https://london.edu/news
6. https://london.edu/events
7. https://london.edu/admissions
8. https://london.edu/student-life
9. https://london.edu/alumni
10. https://london.edu/contact

**Deliverables:**
- Crawler script with configurable URL list
- Raw HTML files saved in `content-repo/raw/`
- Fetch logs and metadata

**Acceptance Criteria:**
- ✅ Successfully fetch 10 target pages
- ✅ Raw HTML saved with consistent naming
- ✅ Fetch metadata includes timestamp, URL, status code
- ✅ No rate limit violations or blocks

---

### Page 1.3: HTML to JSON Conversion
**Tasks:**
- Build HTML parsing service using Cheerio/JSDOM
- Extract DOM structure into JSON representation
- Implement text content hashing (SHA-256)
- Create hash-to-text mapping files
- Normalize HTML (remove scripts, styles, tracking)
- Generate structured output files

**Output Structure:**
```
content-repo/
  raw/
    homepage.html
  parsed/
    homepage/
      dom.json          # DOM structure with hash placeholders
      text.json         # Hash -> text content mapping
      metadata.json     # Page metadata
```

**Deliverables:**
- HTML parsing service
- JSON schema definitions
- Parsed output for 10 pages
- Text hash mapping system

**Acceptance Criteria:**
- ✅ All 10 pages converted to structured JSON
- ✅ Text content extracted and hashed
- ✅ DOM hierarchy preserved in JSON
- ✅ Unique text snippets identified

---

### Page 1.4: Next.js Data Extraction
**Tasks:**
- Parse `__NEXT_DATA__` JSON from page scripts
- Extract page props, state, and metadata
- Identify client-side rendered content
- Merge Next.js data with HTML content
- Handle dynamic content blocks

**Deliverables:**
- Next.js data extraction module
- Combined content files (HTML + Next.js data)
- Documentation of Next.js content structure

**Acceptance Criteria:**
- ✅ Next.js data extracted from all pages
- ✅ Client-side content identified
- ✅ No duplicate content between HTML and Next.js
- ✅ Metadata properly extracted

---

### Page 1.5: Data Validation
**Tasks:**
- Implement validation scripts
- Compare extracted content with source pages
- Identify missing or incomplete content
- Generate validation reports
- Manual review of sample pages

**Deliverables:**
- Validation script
- Validation report for 10 pages
- List of any issues or gaps

**Acceptance Criteria:**
- ✅ 95%+ of visible content captured
- ✅ Major sections present in extracted data
- ✅ No critical content missing
- ✅ Validation report generated

---

## Phase 2: Content Parsing and Domain Modeling (Weeks 3-4)

### Objective
Refine structured content and identify recurring patterns or components in LBS pages.

### Page 2.1: Pattern Recognition
**Tasks:**
- Analyze JSON structures across all pages
- Identify common elements (header, footer, nav)
- Detect content components (hero, listings, profiles)
- Cluster similar structural patterns
- Create component taxonomy

**Deliverables:**
- Component identification report
- Pattern taxonomy document
- Component template definitions

**Acceptance Criteria:**
- ✅ 10+ reusable components identified
- ✅ Components categorized and documented
- ✅ Pattern matching algorithm developed

---

### Page 2.2: Domain Object Modeling
**Tasks:**
- Define domain-specific objects (Course, Faculty, Program, etc.)
- Map HTML components to domain objects
- Create object schemas
- Implement object extraction logic
- Validate object instances

**Domain Objects:**
1. **Page** - Base object for all pages
2. **Program** - Degree programs (MBA, Masters, PhD)
3. **Faculty** - Faculty member profiles
4. **Course** - Individual courses
5. **Research** - Research areas and publications
6. **News** - News articles
7. **Event** - Events and webinars
8. **Section** - Page sections
9. **ContentBlock** - Reusable content blocks

**Deliverables:**
- Domain object schemas (JSON Schema or TypeScript)
- Object extraction modules
- Sample object instances

**Acceptance Criteria:**
- ✅ All domain objects defined with schemas
- ✅ Object extraction working for 80%+ of content
- ✅ Validation passes for extracted objects

---

### Page 2.3: Content Hash Consolidation
**Tasks:**
- Build unified text hash index
- Identify duplicate content across pages
- Create hash usage statistics
- Implement change detection logic
- Generate content reuse report

**Deliverables:**
- Global hash index file
- Duplicate content report
- Change detection system

**Acceptance Criteria:**
- ✅ All unique text snippets indexed
- ✅ Duplicate content identified
- ✅ Reuse statistics generated

---

### Page 2.4: Structure Normalization
**Tasks:**
- Clean JSON representations (remove noise)
- Standardize element IDs and classes
- Remove tracking scripts and dynamic IDs
- Abstract page-specific variations
- Create normalized schema

**Deliverables:**
- Normalization scripts
- Normalized JSON output
- Before/after comparison

**Acceptance Criteria:**
- ✅ Noise elements removed
- ✅ Consistent structure across pages
- ✅ Change detection more accurate

---

### Page 2.5: Preliminary Ontologies
**Tasks:**
- Extract site navigation structure
- Identify top-level categories
- Map pages to categories
- Create initial taxonomy
- Document ontology decisions

**Initial Taxonomy:**
- Programs
  - MBA
  - Masters
  - PhD
  - Executive Education
- Faculty & Research
  - Departments
  - Research Centers
  - Publications
- Admissions
  - Requirements
  - Process
  - Financial Aid
- Student Life
  - Campus
  - Clubs
  - Resources
- About
  - Mission
  - History
  - Leadership

**Deliverables:**
- Initial taxonomy document
- Page-to-category mappings
- Ontology visualization

**Acceptance Criteria:**
- ✅ All pages categorized
- ✅ Taxonomy covers major sections
- ✅ Categories align with site structure

---

## Phase 3: Knowledge Graph Construction (Weeks 5-7)

### Objective
Represent website content and relationships as a graph data structure.

### Page 3.1: Graph Schema Design
**Tasks:**
- Define node types and properties
- Define relationship types
- Create graph schema documentation
- Design indexing strategy
- Plan query patterns

**Node Types:**
```
Page {
  id: string
  url: string
  title: string
  type: string (homepage, program, faculty, etc.)
  lastUpdated: timestamp
}

Section {
  id: string
  type: string (hero, content, sidebar, etc.)
  heading: string
  order: number
}

ContentItem {
  id: string
  hash: string
  text: string
  type: string (paragraph, heading, list, etc.)
}

Topic {
  id: string
  name: string
  category: string
}

Category {
  id: string
  name: string
  level: number
}
```

**Relationship Types:**
- `CONTAINS` (Page -> Section, Section -> ContentItem)
- `LINKS_TO` (Page -> Page)
- `HAS_TOPIC` (ContentItem -> Topic)
- `BELONGS_TO` (Page -> Category)
- `IS_TYPE` (Section -> ComponentType)
- `REFERENCES` (ContentItem -> Page)

**Deliverables:**
- Graph schema specification
- Node and edge type definitions
- Property schemas
- Query pattern documentation

**Acceptance Criteria:**
- ✅ Complete schema covers all content
- ✅ Relationships capture site structure
- ✅ Schema is extensible for future needs

---

### Page 3.2: M-Graph DB Setup
**Tasks:**
- Evaluate graph database options
- Configure M-Graph DB
- Set up local/cloud environment
- Create database initialization scripts
- Implement backup/restore procedures

**Database Options Evaluated:**
1. M-Graph DB (preferred - lightweight, serverless)
2. Neo4j Community
3. JSON-based graph (client-side)
4. SQLite with graph schema

**Deliverables:**
- Database configuration
- Connection utilities
- Initialization scripts
- Backup procedures

**Acceptance Criteria:**
- ✅ Database operational
- ✅ CRUD operations working
- ✅ Query performance acceptable
- ✅ Data persistence confirmed

---

### Page 3.3: Graph Population
**Tasks:**
- Develop graph ingestion scripts
- Create nodes for all pages
- Create section and content nodes
- Establish relationships
- Import taxonomy data
- Validate graph integrity

**Population Process:**
1. Create Page nodes (10 pages)
2. Create Section nodes (~50-100 sections)
3. Create ContentItem nodes (~500-1000 items)
4. Create Topic/Category nodes (~50 topics)
5. Create CONTAINS relationships
6. Create LINKS_TO relationships
7. Create HAS_TOPIC relationships
8. Create BELONGS_TO relationships

**Deliverables:**
- Graph ingestion scripts
- Populated graph database
- Population report and statistics

**Acceptance Criteria:**
- ✅ All pages represented as nodes
- ✅ All content extracted as nodes
- ✅ Relationships properly established
- ✅ No orphaned nodes

---

### Page 3.4: Query Testing
**Tasks:**
- Write sample graph queries
- Test traversal patterns
- Validate relationship accuracy
- Optimize query performance
- Document common queries

**Sample Queries:**
```cypher
// Find all pages linking to a specific page
MATCH (p1:Page)-[:LINKS_TO]->(p2:Page {url: 'https://london.edu/programmes'})
RETURN p1

// Get content about specific topic
MATCH (c:ContentItem)-[:HAS_TOPIC]->(t:Topic {name: 'Finance'})
RETURN c

// Find all faculty pages
MATCH (p:Page {type: 'faculty'})-[:CONTAINS]->(s:Section)
RETURN p, s

// Get navigation paths
MATCH path = (p1:Page)-[:LINKS_TO*1..3]->(p2:Page)
RETURN path
```

**Deliverables:**
- Query test suite
- Query performance report
- Optimization recommendations

**Acceptance Criteria:**
- ✅ All test queries execute successfully
- ✅ Query performance < 500ms
- ✅ Results match expected data
- ✅ No missing relationships found

---

### Page 3.5: Graph Visualization
**Tasks:**
- Create simple graph visualization
- Visualize site structure
- Show content relationships
- Generate graph statistics
- Create exploration interface

**Deliverables:**
- Graph visualization prototype
- Site structure diagram
- Statistics dashboard

**Acceptance Criteria:**
- ✅ Graph visually navigable
- ✅ Relationships clear and accurate
- ✅ Statistics meaningful

---

## Phase 4: Continuous Integration (Weeks 8)

### Page 4.1: CI Pipeline Setup
**Tasks:**
- Create GitHub Actions workflows
- Configure scheduled crawls
- Set up automated extraction
- Implement change detection
- Configure notifications

**Deliverables:**
- `.github/workflows/crawler.yml`
- CI/CD configuration
- Automated pipeline

**Acceptance Criteria:**
- ✅ Pipeline runs on schedule
- ✅ Changes detected and committed
- ✅ Notifications working

---

### Page 4.2: Version Control Integration
**Tasks:**
- Configure Git automation
- Implement commit strategies
- Set up branching workflow
- Create change logs
- Document version history

**Deliverables:**
- Git automation scripts
- Commit message templates
- Change log format

**Acceptance Criteria:**
- ✅ Changes tracked in Git
- ✅ History browsable
- ✅ Rollback possible

---

### Page 4.3: Graph Update Automation
**Tasks:**
- Automate graph rebuild
- Implement incremental updates
- Handle deletions
- Validate graph after updates
- Deploy updated graph

**Deliverables:**
- Graph update scripts
- Deployment automation
- Validation checks

**Acceptance Criteria:**
- ✅ Graph updates automatically
- ✅ No data loss
- ✅ Validation passes

---

## Phase 5: UI Prototypes (Weeks 9-12)

### Page 5.1: Text-Only View
**Tasks:**
- Create text rendering component
- Implement Markdown conversion
- Build simple page viewer
- Add content navigation
- Test with LLMs

**Deliverables:**
- Text view UI component
- Sample pages rendered
- LLM-friendly format

**Acceptance Criteria:**
- ✅ All content visible as text
- ✅ Readable and navigable
- ✅ No content hidden

---

### Page 5.2: Visualization Dashboard
**Tasks:**
- Design dashboard layout
- Implement site map graph (D3.js)
- Create component reuse charts
- Add content statistics
- Build interactive features

**Visualizations:**
1. Site map graph
2. Component reuse bar chart
3. Content statistics tables
4. Category distribution pie chart
5. Link density heatmap

**Deliverables:**
- Interactive dashboard
- Multiple visualization types
- Export capabilities

**Acceptance Criteria:**
- ✅ All visualizations working
- ✅ Interactivity functional
- ✅ Performance acceptable

---

### Page 5.3: Static Site Reconstruction
**Tasks:**
- Build static site generator
- Create basic HTML templates
- Implement styling
- Add navigation
- Deploy static site

**Deliverables:**
- Static site generator
- Basic styled pages
- Deployed preview site

**Acceptance Criteria:**
- ✅ Pages render correctly
- ✅ Navigation works
- ✅ Content matches source

---

## Phase 6: Semantic Enrichment (Weeks 13-15)

### Page 6.1: Sentiment Analysis
**Tasks:**
- Integrate LLM API
- Implement sentiment analysis
- Score content items
- Store sentiment data
- Validate accuracy

**Deliverables:**
- Sentiment analysis module
- Sentiment scores for all content
- Validation report

**Acceptance Criteria:**
- ✅ All content analyzed
- ✅ 90%+ accuracy
- ✅ Scores stored in graph

---

### Page 6.2: Topic Tagging
**Tasks:**
- Define topic taxonomy
- Implement topic extraction
- Tag all content
- Create topic nodes
- Validate tags

**Topics:**
- Finance
- Marketing
- Strategy
- Entrepreneurship
- Leadership
- Data Science
- Sustainability
- Innovation
- Global Business

**Deliverables:**
- Topic tagging system
- Tagged content
- Topic validation report

**Acceptance Criteria:**
- ✅ All content tagged
- ✅ Tags accurate and relevant
- ✅ Topics in graph

---

### Page 6.3: Audience Classification
**Tasks:**
- Define audience personas
- Classify content by audience
- Add audience annotations
- Create persona nodes
- Validate classifications

**Personas:**
- Prospective Students
- Current Students
- Alumni
- Faculty
- Researchers
- Corporate Partners
- Media

**Deliverables:**
- Audience classifier
- Classified content
- Persona nodes in graph

**Acceptance Criteria:**
- ✅ Content classified
- ✅ 85%+ accuracy
- ✅ Personas in graph

---

## Phase 7: Graph-Driven UIs (Weeks 16-18)

### Page 7.1: Ontology Navigation
**Tasks:**
- Build topic browsing UI
- Create page-level outlines
- Implement tag navigation
- Add visual graph explorer
- Test user flows

**Deliverables:**
- Topic browser
- Tag navigation
- Graph explorer

**Acceptance Criteria:**
- ✅ Topics browsable
- ✅ Navigation intuitive
- ✅ Graph explorable

---

### Page 7.2: Filtered Search
**Tasks:**
- Implement search backend
- Add sentiment filters
- Add audience filters
- Create combined queries
- Build results UI

**Deliverables:**
- Search engine
- Filter controls
- Results display

**Acceptance Criteria:**
- ✅ Search functional
- ✅ Filters work correctly
- ✅ Results relevant

---

### Page 7.3: Graph Query Interface
**Tasks:**
- Build query console
- Create interactive graph GUI
- Add debugging tools
- Implement export
- Document query language

**Deliverables:**
- Query console
- Interactive explorer
- Documentation

**Acceptance Criteria:**
- ✅ Queries executable
- ✅ Results displayed
- ✅ Export working

---

## Phase 8: Personalization (Weeks 19-20)

### Page 8.1: Persona Portals
**Tasks:**
- Design persona dashboards
- Aggregate relevant content
- Build portal pages
- Add persona switcher
- Test with users

**Deliverables:**
- 5+ persona portals
- Content aggregation logic
- Persona switcher

**Acceptance Criteria:**
- ✅ Portals functional
- ✅ Content relevant
- ✅ Switching works

---

### Page 8.2: Dynamic Customization
**Tasks:**
- Implement page personalization
- Add content reordering
- Create recommendation engine
- Build preference system
- Test variations

**Deliverables:**
- Personalization engine
- Recommendations
- A/B test framework

**Acceptance Criteria:**
- ✅ Pages customize
- ✅ Recommendations relevant
- ✅ Performance good

---

## Phase 9: Admin Tools (Weeks 21-22)

### Page 9.1: Curation Dashboard
**Tasks:**
- Build admin interface
- Add tag editing
- Create node management
- Implement bulk operations
- Add version control

**Deliverables:**
- Admin dashboard
- CRUD operations
- Bulk editing tools

**Acceptance Criteria:**
- ✅ Dashboard functional
- ✅ Edits save correctly
- ✅ Permissions work

---

### Page 9.2: Quality Reports
**Tasks:**
- Generate quality metrics
- Identify orphaned content
- Flag anomalies
- Create reports
- Add alerting

**Deliverables:**
- Quality report system
- Automated checks
- Alert notifications

**Acceptance Criteria:**
- ✅ Reports generated
- ✅ Issues identified
- ✅ Alerts working

---

## Phase 10: Autonomous Agents (Weeks 23-25)

### Page 10.1: Content Agents
**Tasks:**
- Develop content suggestion agent
- Implement gap analysis
- Create automated tagging
- Build improvement suggestions
- Test agent accuracy

**Deliverables:**
- Content agent system
- Suggestion reports
- Automated improvements

**Acceptance Criteria:**
- ✅ Agent suggests content
- ✅ Gaps identified
- ✅ Improvements helpful

---

### Page 10.2: Optimization Agents
**Tasks:**
- Build A/B testing agent
- Implement UX optimization
- Create performance monitoring
- Add learning feedback loop
- Document improvements

**Deliverables:**
- Optimization agents
- Performance reports
- Learning system

**Acceptance Criteria:**
- ✅ Optimizations suggested
- ✅ Performance improved
- ✅ Learning working

---

## Implementation Checklist

### Phase 1 (Weeks 1-2)
- [ ] Project setup complete
- [ ] 10 pages crawled
- [ ] HTML to JSON conversion working
- [ ] Next.js data extracted
- [ ] Validation passed

### Phase 2 (Weeks 3-4)
- [ ] Patterns identified
- [ ] Domain objects defined
- [ ] Content normalized
- [ ] Taxonomy created

### Phase 3 (Weeks 5-7)
- [ ] Graph schema designed
- [ ] Database set up
- [ ] Graph populated
- [ ] Queries tested

### Phase 4 (Week 8)
- [ ] CI pipeline working
- [ ] Version control integrated
- [ ] Graph updates automated

### Phase 5 (Weeks 9-12)
- [ ] Text view built
- [ ] Dashboard created
- [ ] Static site generated

### Phase 6 (Weeks 13-15)
- [ ] Sentiment analysis done
- [ ] Topics tagged
- [ ] Audiences classified

### Phase 7 (Weeks 16-18)
- [ ] Ontology navigation built
- [ ] Search implemented
- [ ] Graph explorer created

### Phase 8 (Weeks 19-20)
- [ ] Persona portals ready
- [ ] Personalization working

### Phase 9 (Weeks 21-22)
- [ ] Admin dashboard built
- [ ] Quality reports generated

### Phase 10 (Weeks 23-25)
- [ ] Content agents deployed
- [ ] Optimization working
- [ ] Project complete

---

**Total Pages Planned:** 40+
**Total Tasks:** 200+
**Total Duration:** 25 weeks
**Target Launch:** Month 6
