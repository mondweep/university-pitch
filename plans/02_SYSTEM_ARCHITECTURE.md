# System Architecture

## Architecture Overview

The LBS Semantic Knowledge Graph platform follows a modern, modular architecture with three main layers:

1. **Data Layer** - Content extraction, storage, and graph database
2. **Processing Layer** - Semantic analysis, graph construction, and API services
3. **Presentation Layer** - User interfaces, visualizations, and admin tools

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Web UIs    │  │Visualizations│  │ Admin Tools  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Graph API   │  │  LLM Service │  │Search Engine │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │Graph Builder │  │ Normalizer   │  │  Scheduler   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    Crawler   │  │ HTML Parser  │  │ Content Repo │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  M-Graph DB  │  │  Text Store  │  │  Cache Layer │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                    ┌──────────────────┐
                    │   london.edu     │
                    └──────────────────┘
```

---

## Component Architecture

### 1. Data Layer Components

#### 1.1 Web Crawler
**Purpose:** Fetch HTML content from london.edu

**Technology:**
- Node.js + Puppeteer/Playwright
- Headless Chrome for JavaScript rendering
- Proxy support for distributed crawling

**Features:**
- Configurable URL lists and crawl depth
- Robots.txt compliance
- Rate limiting and politeness policies
- Error handling and retry logic
- Session management for auth pages

**Input:**
- URL seed list
- Crawl configuration (depth, rate, filters)

**Output:**
- Raw HTML files
- Fetch metadata (URL, timestamp, status, headers)
- Crawl logs

#### 1.2 HTML Parser
**Purpose:** Convert HTML to structured JSON

**Technology:**
- Cheerio for DOM parsing
- JSDOM for full browser emulation (if needed)
- Custom extraction rules

**Features:**
- DOM tree extraction
- Next.js `__NEXT_DATA__` extraction
- Text content hashing (SHA-256)
- Metadata extraction (title, description, etc.)
- Link extraction and normalization

**Input:**
- Raw HTML files

**Output:**
- `dom.json` - DOM structure with hash placeholders
- `text.json` - Hash-to-text mapping
- `nextjs-data.json` - Next.js page data
- `metadata.json` - Page metadata
- `links.json` - Extracted links

#### 1.3 Content Repository
**Purpose:** Version-controlled storage for extracted content

**Technology:**
- Git for version control
- JSON for structured data
- LFS for large files (images)

**Structure:**
```
content-repo/
├── raw/
│   ├── homepage.html
│   ├── about.html
│   └── ...
├── parsed/
│   ├── homepage/
│   │   ├── dom.json
│   │   ├── text.json
│   │   ├── nextjs-data.json
│   │   ├── metadata.json
│   │   └── links.json
│   └── ...
├── analysis/
│   ├── sentiment.json
│   ├── topics.json
│   └── audiences.json
└── README.md
```

#### 1.4 M-Graph Database
**Purpose:** Store and query knowledge graph

**Technology Options:**
1. **M-Graph DB** (preferred) - Lightweight, serverless
2. **Neo4j Community** - Full-featured graph DB
3. **JSON Graph** - Client-side graph for prototypes
4. **SQLite + Graph Schema** - SQL-based fallback

**Schema:**
- Nodes: Page, Section, ContentItem, Topic, Category, Persona
- Edges: CONTAINS, LINKS_TO, HAS_TOPIC, BELONGS_TO, IS_TYPE

**Queries:**
- Cypher (Neo4j-compatible)
- Custom query DSL for M-Graph DB
- GraphQL API layer

**Indexes:**
- Page URL (unique)
- Content hash (for deduplication)
- Topic name
- Category hierarchy

#### 1.5 Text Store
**Purpose:** Deduplicated text content storage

**Technology:**
- JSON files (hash -> text)
- Optional: Redis for caching frequently accessed text

**Features:**
- Global text index across all pages
- Duplicate detection
- Change tracking
- Full-text search support

#### 1.6 Cache Layer
**Purpose:** Performance optimization

**Technology:**
- Redis for graph query caching
- CDN for static assets
- Browser cache for UI

**Strategies:**
- LRU eviction
- TTL-based expiration
- Cache warming for common queries

---

### 2. Processing Layer Components

#### 2.1 Graph Builder
**Purpose:** Construct knowledge graph from parsed content

**Features:**
- Node creation from domain objects
- Relationship inference
- Taxonomy integration
- Graph validation

**Process:**
1. Read parsed content from repository
2. Create Page nodes
3. Create Section and ContentItem nodes
4. Extract and create Topic/Category nodes
5. Establish relationships
6. Validate graph integrity
7. Write to M-Graph DB

**Input:**
- Parsed content files (JSON)
- Taxonomy definitions

**Output:**
- Populated graph database
- Build report with statistics

#### 2.2 LLM Service
**Purpose:** Semantic analysis using large language models

**Technology:**
- OpenAI GPT-4 API
- Anthropic Claude API
- Fallback: Open-source LLMs (Llama, Mistral)

**Features:**
- Sentiment analysis
- Topic extraction
- Audience classification
- Content summarization
- Relationship discovery

**API:**
```typescript
interface LLMService {
  analyzeSentiment(text: string): SentimentScore;
  extractTopics(text: string, taxonomy?: string[]): Topic[];
  classifyAudience(text: string): Persona[];
  summarize(text: string, maxLength?: number): string;
  findRelationships(text: string, context: Context): Relationship[];
}
```

**Rate Limiting:**
- Token bucket algorithm
- Request queuing
- Batch processing for efficiency

**Cost Optimization:**
- Caching of analysis results
- Incremental analysis (only new content)
- Model selection based on task complexity

#### 2.3 Graph API
**Purpose:** RESTful API for graph operations

**Endpoints:**

**Nodes:**
```
GET    /api/nodes/:id
POST   /api/nodes
PUT    /api/nodes/:id
DELETE /api/nodes/:id
GET    /api/nodes?type=:type&filter=:filter
```

**Edges:**
```
GET    /api/edges/:id
POST   /api/edges
DELETE /api/edges/:id
GET    /api/nodes/:id/edges?type=:type
```

**Queries:**
```
POST   /api/query
  Body: { query: string, params: object }
GET    /api/search?q=:query&filters=:filters
GET    /api/traverse?start=:nodeId&depth=:depth
```

**Ontology:**
```
GET    /api/ontology
GET    /api/topics
GET    /api/categories
```

**Authentication:**
- JWT tokens for admin operations
- API keys for read operations
- Role-based access control (RBAC)

#### 2.4 Search Engine
**Purpose:** Full-text and semantic search

**Technology:**
- Elasticsearch or Meilisearch
- Vector embeddings for semantic search
- Graph traversal for relationship-based search

**Features:**
- Full-text search on content
- Faceted search (filters)
- Semantic similarity search
- Auto-complete and suggestions
- Search analytics

**Indexing:**
- All text content indexed
- Embeddings for semantic search
- Metadata for filtering
- Real-time updates

#### 2.5 Normalizer
**Purpose:** Clean and standardize extracted content

**Features:**
- Remove HTML artifacts
- Standardize formatting
- Deduplicate content
- Fix encoding issues
- Normalize URLs

#### 2.6 Scheduler
**Purpose:** Automate data pipeline execution

**Technology:**
- GitHub Actions for CI/CD
- Cron jobs for scheduled tasks
- Event-driven triggers

**Jobs:**
- **Crawler Job** - Daily at 2 AM UTC
- **Parser Job** - After crawler completes
- **Graph Rebuild** - After parsing completes
- **LLM Analysis** - Weekly for new content
- **Backup Job** - Daily at 4 AM UTC

---

### 3. Presentation Layer Components

#### 3.1 Web UI Framework
**Purpose:** User-facing interfaces

**Technology:**
- **Option 1:** Pure HTML/CSS/JS (vanilla)
- **Option 2:** Web Components (custom elements)
- **Option 3:** React/Vue/Svelte (if more complex)

**Features:**
- Responsive design (mobile-first)
- Accessibility (WCAG 2.1 AA)
- Performance optimized (< 2s load time)
- Progressive enhancement

**UI Modes:**
1. Text-only view
2. Visualization dashboard
3. Static site reconstruction
4. Graph explorer
5. Persona portals
6. Search interface

#### 3.2 Visualization Library
**Purpose:** Interactive data visualizations

**Technology:**
- D3.js for custom graphs
- Mermaid.js for diagrams
- Chart.js for statistics
- Cytoscape.js for graph visualization

**Visualizations:**
- Site structure graph (force-directed)
- Topic network graph
- Content reuse heatmap
- Statistics dashboards
- Relationship explorer

#### 3.3 Admin Dashboard
**Purpose:** Content curation and management

**Features:**
- Tag editor (add/remove/edit tags)
- Node manager (CRUD on graph nodes)
- Bulk operations
- Quality reports
- Analytics dashboard
- User management

**Authentication:**
- SSO integration (SAML/OAuth)
- Multi-factor authentication
- Audit logging

#### 3.4 Static Site Generator
**Purpose:** Generate static HTML from graph data

**Technology:**
- Custom generator or 11ty/Hugo
- Templating engine (Nunjucks/Handlebars)
- Asset bundling (Webpack/Vite)

**Features:**
- Template-based page generation
- Automatic navigation generation
- SEO optimization
- Sitemap generation
- Multiple theme support

---

## Data Flow Architecture

### 1. Content Acquisition Flow

```
london.edu
    ↓
[Crawler] → Fetch HTML
    ↓
[Storage] → Save to content-repo/raw/
    ↓
[Parser] → Extract structure & content
    ↓
[Normalizer] → Clean and deduplicate
    ↓
[Storage] → Save to content-repo/parsed/
    ↓
[Version Control] → Commit to Git
```

### 2. Graph Construction Flow

```
Parsed Content (JSON)
    ↓
[Domain Mapper] → Map to domain objects
    ↓
[Graph Builder] → Create nodes & edges
    ↓
[Validator] → Check graph integrity
    ↓
[M-Graph DB] → Persist graph
    ↓
[Indexer] → Update search indexes
```

### 3. Semantic Enrichment Flow

```
Content Text
    ↓
[LLM Service] → Analyze sentiment, topics, audience
    ↓
[Enricher] → Add metadata to nodes
    ↓
[M-Graph DB] → Update graph with semantics
    ↓
[Cache] → Warm cache for common queries
```

### 4. User Request Flow

```
User Request (UI)
    ↓
[API Gateway] → Route request
    ↓
[Cache Check] → Check if cached
    ↓ (cache miss)
[Graph API] → Query M-Graph DB
    ↓
[Transformer] → Format response
    ↓
[Cache] → Store result
    ↓
[UI] → Render to user
```

---

## Deployment Architecture

### Development Environment
```
Developer Machine
├── Code Repository (local)
├── Content Repository (submodule)
├── Local M-Graph DB
└── Dev Server (hot reload)
```

### Staging Environment
```
Staging Server
├── Code Repo (staging branch)
├── Content Repo (staging data)
├── Staging M-Graph DB
├── CI/CD Pipeline
└── Test Users
```

### Production Environment
```
Production Infrastructure
├── CDN (Cloudflare/AWS CloudFront)
│   └── Static Assets
├── Web Servers (2+ instances)
│   ├── Load Balancer
│   ├── API Gateway
│   └── UI Application
├── Processing Servers
│   ├── Crawler Service
│   ├── Parser Service
│   ├── LLM Service (with rate limiting)
│   └── Scheduler
├── Data Layer
│   ├── M-Graph DB (primary + replica)
│   ├── Content Storage (S3/equivalent)
│   ├── Redis Cache
│   └── Backup Storage
└── Monitoring
    ├── Application Metrics (Prometheus)
    ├── Logs (ELK Stack)
    ├── Alerts (PagerDuty)
    └── Uptime Monitoring
```

---

## Security Architecture

### 1. Authentication & Authorization
- **User Auth:** SSO with LBS identity provider
- **API Auth:** JWT tokens with expiration
- **Service Auth:** mTLS for inter-service communication

### 2. Data Security
- **At Rest:** Encryption of sensitive data (AES-256)
- **In Transit:** TLS 1.3 for all communications
- **Secrets:** Environment variables, never in code
- **Backup:** Encrypted backups with access controls

### 3. Network Security
- **Firewall:** Restrict access to internal services
- **DDoS Protection:** CDN-level protection
- **Rate Limiting:** API rate limits per user/IP
- **CORS:** Strict CORS policies

### 4. Application Security
- **Input Validation:** Sanitize all user inputs
- **XSS Protection:** Content Security Policy (CSP)
- **CSRF Protection:** CSRF tokens
- **SQL Injection:** Parameterized queries only
- **Dependency Scanning:** Regular security audits

---

## Scalability Architecture

### Horizontal Scaling
- **Web Servers:** Auto-scaling based on load
- **Processing Servers:** Job queue with workers
- **Database:** Read replicas for scaling reads

### Vertical Scaling
- **Database:** Upgrade instance size as needed
- **Cache:** Increase Redis memory
- **Compute:** Upgrade server specs

### Performance Optimization
- **Caching Strategy:**
  - L1: Browser cache (static assets)
  - L2: CDN cache (pages, images)
  - L3: Redis cache (API responses)
  - L4: Database query cache

- **Database Optimization:**
  - Indexing on common query fields
  - Query optimization and profiling
  - Partitioning for large tables
  - Denormalization where needed

- **Code Optimization:**
  - Minification and bundling
  - Lazy loading of components
  - Server-side rendering for SEO
  - Async/await for non-blocking I/O

---

## Monitoring & Observability

### Metrics
- **Application Metrics:**
  - Request rate, error rate, duration (RED)
  - CPU, memory, disk usage
  - API endpoint performance

- **Business Metrics:**
  - Pages crawled per day
  - Graph nodes/edges count
  - LLM API costs
  - User engagement (page views, searches)

### Logging
- **Structured Logging:** JSON format
- **Log Levels:** DEBUG, INFO, WARN, ERROR
- **Centralized:** ELK Stack or CloudWatch
- **Retention:** 90 days for production logs

### Alerts
- **Critical:**
  - Service down
  - Database connection failure
  - Disk space < 10%

- **Warning:**
  - High error rate (> 5%)
  - Slow queries (> 1s)
  - Low cache hit rate (< 60%)

### Dashboards
- **Operations Dashboard:**
  - System health
  - Service status
  - Recent alerts

- **Analytics Dashboard:**
  - Content statistics
  - User behavior
  - Search analytics

---

## Disaster Recovery

### Backup Strategy
- **Frequency:**
  - Database: Daily full, hourly incremental
  - Content: Daily snapshot
  - Code: Git (automatic)

- **Retention:**
  - Daily backups: 30 days
  - Weekly backups: 90 days
  - Monthly backups: 1 year

### Recovery Procedures
- **RTO (Recovery Time Objective):** 4 hours
- **RPO (Recovery Point Objective):** 1 hour
- **Failover:**
  - Automatic DB failover to replica
  - Manual service failover
  - DNS-based traffic routing

### Testing
- **Backup Testing:** Monthly restore test
- **Disaster Recovery Drill:** Quarterly
- **Incident Response:** Documented runbooks

---

## Integration Points

### External Systems
- **London.edu:** Source website (read-only)
- **LBS SSO:** Authentication provider
- **LLM APIs:** OpenAI/Anthropic (third-party)
- **CDN:** Cloudflare/AWS (infrastructure)
- **Email:** SendGrid for notifications

### APIs Consumed
- OpenAI API (semantic analysis)
- LBS SSO API (authentication)
- GitHub API (CI/CD, content repo)

### APIs Provided
- Graph API (REST/GraphQL)
- Search API (REST)
- Webhook API (for integrations)

---

## Technology Stack Summary

| Layer | Component | Technology |
|-------|-----------|------------|
| **Data** | Crawler | Node.js + Puppeteer |
| | Parser | Cheerio/JSDOM |
| | Storage | Git + JSON |
| | Graph DB | M-Graph DB / Neo4j |
| | Cache | Redis |
| **Processing** | API | Node.js + Express |
| | LLM | OpenAI/Claude APIs |
| | Search | Elasticsearch |
| | Scheduler | GitHub Actions |
| **Presentation** | Frontend | HTML/CSS/JS or React |
| | Visualization | D3.js, Cytoscape.js |
| | Static Gen | 11ty or custom |
| **Infrastructure** | Hosting | AWS / GCP / Azure |
| | CDN | Cloudflare |
| | Monitoring | Prometheus + Grafana |
| | Logging | ELK Stack |

---

**Document Version:** 1.0
**Last Updated:** November 2025
**Next Review:** Phase 3 completion
