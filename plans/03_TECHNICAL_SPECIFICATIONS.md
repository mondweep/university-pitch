# Technical Specifications

## 1. System Requirements

### 1.1 Functional Requirements

#### FR1: Content Extraction
- **FR1.1** System SHALL crawl and fetch HTML from london.edu
- **FR1.2** System SHALL parse HTML into structured JSON format
- **FR1.3** System SHALL extract Next.js `__NEXT_DATA__` objects
- **FR1.4** System SHALL hash text content using SHA-256
- **FR1.5** System SHALL detect and track content changes
- **FR1.6** System SHALL store raw and processed content in version control

#### FR2: Knowledge Graph
- **FR2.1** System SHALL construct a graph with nodes (Page, Section, Content, Topic, Category)
- **FR2.2** System SHALL establish relationships (CONTAINS, LINKS_TO, HAS_TOPIC, BELONGS_TO)
- **FR2.3** System SHALL support graph queries in < 500ms
- **FR2.4** System SHALL validate graph integrity on each update
- **FR2.5** System SHALL export graph in multiple formats (JSON, GraphML, Cypher)

#### FR3: Semantic Analysis
- **FR3.1** System SHALL analyze sentiment of content items
- **FR3.2** System SHALL extract topics from text using LLM
- **FR3.3** System SHALL classify content by target audience
- **FR3.4** System SHALL maintain 90%+ accuracy on semantic annotations
- **FR3.5** System SHALL support custom taxonomy definitions

#### FR4: User Interfaces
- **FR4.1** System SHALL provide text-only content view
- **FR4.2** System SHALL provide interactive visualization dashboard
- **FR4.3** System SHALL provide reconstructed static website
- **FR4.4** System SHALL provide topic-based navigation
- **FR4.5** System SHALL provide persona-specific portals
- **FR4.6** System SHALL provide graph exploration interface

#### FR5: Search & Discovery
- **FR5.1** System SHALL support full-text search
- **FR5.2** System SHALL support filtered search (sentiment, topic, audience)
- **FR5.3** System SHALL provide search suggestions and autocomplete
- **FR5.4** System SHALL support combined query filters
- **FR5.5** System SHALL return relevant results in < 1 second

#### FR6: Personalization
- **FR6.1** System SHALL support 5+ user personas
- **FR6.2** System SHALL customize content display per persona
- **FR6.3** System SHALL provide content recommendations
- **FR6.4** System SHALL track user preferences
- **FR6.5** System SHALL support A/B testing of layouts

#### FR7: Administration
- **FR7.1** System SHALL provide tag editing interface
- **FR7.2** System SHALL support bulk operations on nodes
- **FR7.3** System SHALL generate quality reports
- **FR7.4** System SHALL maintain audit trail of changes
- **FR7.5** System SHALL support role-based access control

#### FR8: Automation
- **FR8.1** System SHALL run automated crawls on schedule
- **FR8.2** System SHALL automatically update graph with new content
- **FR8.3** System SHALL automatically commit changes to Git
- **FR8.4** System SHALL send notifications on errors
- **FR8.5** System SHALL support manual trigger of pipeline

---

### 1.2 Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1** Page load time SHALL be < 2 seconds (90th percentile)
- **NFR1.2** API response time SHALL be < 500ms (95th percentile)
- **NFR1.3** Graph queries SHALL complete in < 500ms
- **NFR1.4** Search results SHALL return in < 1 second
- **NFR1.5** System SHALL support 100 concurrent users

#### NFR2: Scalability
- **NFR2.1** System SHALL handle 10,000+ pages
- **NFR2.2** System SHALL support 100,000+ graph nodes
- **NFR2.3** System SHALL process 100+ pages per hour during crawls
- **NFR2.4** Database SHALL support horizontal scaling
- **NFR2.5** Cache hit rate SHALL be > 60%

#### NFR3: Availability
- **NFR3.1** System uptime SHALL be 99.5% (excluding maintenance)
- **NFR3.2** Planned downtime SHALL be < 4 hours per month
- **NFR3.3** Recovery Time Objective (RTO) SHALL be < 4 hours
- **NFR3.4** Recovery Point Objective (RPO) SHALL be < 1 hour
- **NFR3.5** Automated health checks SHALL run every 5 minutes

#### NFR4: Security
- **NFR4.1** All data in transit SHALL use TLS 1.3
- **NFR4.2** Sensitive data at rest SHALL be encrypted (AES-256)
- **NFR4.3** API rate limiting SHALL be 1000 requests/hour per user
- **NFR4.4** Authentication SHALL use SSO with MFA
- **NFR4.5** OWASP Top 10 vulnerabilities SHALL be mitigated

#### NFR5: Usability
- **NFR5.1** UI SHALL be responsive (mobile, tablet, desktop)
- **NFR5.2** UI SHALL meet WCAG 2.1 AA accessibility standards
- **NFR5.3** UI SHALL support modern browsers (Chrome, Firefox, Safari, Edge)
- **NFR5.4** Error messages SHALL be user-friendly
- **NFR5.5** Loading states SHALL provide user feedback

#### NFR6: Maintainability
- **NFR6.1** Code SHALL have 80%+ test coverage
- **NFR6.2** Code SHALL follow established style guides
- **NFR6.3** All APIs SHALL have OpenAPI documentation
- **NFR6.4** System SHALL have comprehensive logging
- **NFR6.5** Deployment SHALL be automated via CI/CD

#### NFR7: Reliability
- **NFR7.1** Error rate SHALL be < 1% of requests
- **NFR7.2** System SHALL gracefully handle external API failures
- **NFR7.3** Database backups SHALL be automated daily
- **NFR7.4** Failed jobs SHALL automatically retry (3 attempts)
- **NFR7.5** System SHALL have automated monitoring and alerts

---

## 2. Data Specifications

### 2.1 Page Data Model

```typescript
interface Page {
  id: string;                    // UUID
  url: string;                   // Canonical URL
  title: string;                 // Page title
  description?: string;          // Meta description
  type: PageType;               // homepage, program, faculty, etc.
  language: string;             // ISO 639-1 code
  createdAt: Date;              // First crawl date
  updatedAt: Date;              // Last update date
  hash: string;                 // Content hash for change detection
  metadata: Record<string, any>; // Additional metadata
}

enum PageType {
  Homepage = 'homepage',
  Program = 'program',
  Faculty = 'faculty',
  Research = 'research',
  News = 'news',
  Event = 'event',
  About = 'about',
  Admissions = 'admissions',
  Other = 'other'
}
```

### 2.2 Section Data Model

```typescript
interface Section {
  id: string;                    // UUID
  pageId: string;               // Parent page ID
  type: SectionType;            // hero, content, sidebar, etc.
  heading?: string;             // Section heading
  order: number;                // Display order on page
  contentItems: string[];       // Array of ContentItem IDs
  metadata: Record<string, any>;
}

enum SectionType {
  Hero = 'hero',
  Content = 'content',
  Sidebar = 'sidebar',
  Navigation = 'navigation',
  Footer = 'footer',
  Callout = 'callout',
  Listing = 'listing'
}
```

### 2.3 Content Item Data Model

```typescript
interface ContentItem {
  id: string;                    // UUID
  hash: string;                  // SHA-256 hash of text
  text: string;                  // Actual text content
  type: ContentType;            // paragraph, heading, list, etc.
  sentiment?: SentimentScore;   // LLM-generated sentiment
  topics?: string[];            // LLM-generated topics
  audiences?: string[];         // Target audiences
  metadata: Record<string, any>;
}

enum ContentType {
  Paragraph = 'paragraph',
  Heading = 'heading',
  List = 'list',
  Quote = 'quote',
  Code = 'code',
  Table = 'table'
}

interface SentimentScore {
  polarity: number;             // -1 (negative) to +1 (positive)
  confidence: number;           // 0 to 1
  label: 'positive' | 'neutral' | 'negative';
}
```

### 2.4 Topic Data Model

```typescript
interface Topic {
  id: string;                    // UUID
  name: string;                  // Topic name
  category: string;             // Parent category
  description?: string;          // Topic description
  aliases: string[];            // Alternative names
  relatedTopics: string[];      // Related topic IDs
  contentCount: number;         // Number of content items
}
```

### 2.5 Category Data Model

```typescript
interface Category {
  id: string;                    // UUID
  name: string;                  // Category name
  level: number;                // Hierarchy level (0 = root)
  parentId?: string;            // Parent category ID
  children: string[];           // Child category IDs
  icon?: string;                // Icon identifier
  color?: string;               // Display color (hex)
}
```

### 2.6 Persona Data Model

```typescript
interface Persona {
  id: string;                    // UUID
  name: string;                  // Persona name
  description: string;           // Persona description
  interests: string[];          // Topics of interest
  preferredContent: ContentType[]; // Preferred content types
  priority: number;             // Display priority (1-5)
}

enum PersonaType {
  ProspectiveStudent = 'prospective_student',
  CurrentStudent = 'current_student',
  Alumni = 'alumni',
  Faculty = 'faculty',
  Researcher = 'researcher',
  CorporatePartner = 'corporate_partner',
  Media = 'media'
}
```

---

## 3. API Specifications

### 3.1 RESTful API Endpoints

#### Pages API
```
GET    /api/pages
  Query: ?type=program&limit=20&offset=0
  Response: { pages: Page[], total: number, page: number }

GET    /api/pages/:id
  Response: Page

POST   /api/pages
  Auth: Required (Admin)
  Body: Partial<Page>
  Response: Page

PUT    /api/pages/:id
  Auth: Required (Admin)
  Body: Partial<Page>
  Response: Page

DELETE /api/pages/:id
  Auth: Required (Admin)
  Response: { success: boolean }
```

#### Graph Query API
```
POST   /api/query
  Body: {
    query: string,        // Cypher-like query
    params: object,       // Query parameters
    limit?: number        // Max results
  }
  Response: {
    nodes: Node[],
    edges: Edge[],
    executionTime: number
  }

GET    /api/traverse
  Query: ?start=:nodeId&depth=:depth&direction=:direction
  Response: {
    path: Node[],
    relationships: Edge[]
  }
```

#### Search API
```
GET    /api/search
  Query: ?q=:query&filters=:filters&page=:page&limit=:limit
  Response: {
    results: SearchResult[],
    total: number,
    facets: Facet[],
    suggestions: string[]
  }

interface SearchResult {
  id: string,
  type: 'page' | 'section' | 'content',
  title: string,
  snippet: string,
  url: string,
  score: number,
  highlights: string[]
}
```

#### Topics API
```
GET    /api/topics
  Response: Topic[]

GET    /api/topics/:id
  Response: Topic

GET    /api/topics/:id/content
  Query: ?limit=20
  Response: { content: ContentItem[], total: number }
```

#### Admin API
```
PUT    /api/admin/nodes/:id/tags
  Auth: Required (Admin)
  Body: { tags: string[] }
  Response: Node

POST   /api/admin/bulk-update
  Auth: Required (Admin)
  Body: { nodeIds: string[], updates: object }
  Response: { updated: number, failed: number }

GET    /api/admin/quality-report
  Auth: Required (Admin)
  Response: QualityReport

interface QualityReport {
  orphanedNodes: number,
  missingTags: number,
  brokenLinks: number,
  issues: Issue[]
}
```

### 3.2 GraphQL API (Optional Alternative)

```graphql
type Query {
  page(id: ID!): Page
  pages(type: PageType, limit: Int, offset: Int): PageConnection
  search(query: String!, filters: SearchFilters): SearchResults
  topics: [Topic!]!
  topic(id: ID!): Topic
  traverse(start: ID!, depth: Int!, direction: Direction): Path
}

type Mutation {
  updatePage(id: ID!, input: PageInput!): Page
  addTag(nodeId: ID!, tag: String!): Node
  removeTag(nodeId: ID!, tag: String!): Node
  bulkUpdate(nodeIds: [ID!]!, updates: JSON!): BulkUpdateResult
}

type Subscription {
  pageUpdated(id: ID!): Page
  graphChanged: GraphChange
}
```

---

## 4. Database Specifications

### 4.1 Graph Schema (Cypher Notation)

```cypher
// Node Types
(:Page {
  id: string,
  url: string,
  title: string,
  type: string,
  hash: string,
  createdAt: datetime,
  updatedAt: datetime
})

(:Section {
  id: string,
  type: string,
  heading: string,
  order: number
})

(:ContentItem {
  id: string,
  hash: string,
  text: string,
  type: string
})

(:Topic {
  id: string,
  name: string,
  category: string
})

(:Category {
  id: string,
  name: string,
  level: number
})

(:Persona {
  id: string,
  name: string,
  type: string
})

// Relationship Types
(:Page)-[:CONTAINS {order: number}]->(:Section)
(:Section)-[:CONTAINS {order: number}]->(:ContentItem)
(:Page)-[:LINKS_TO {text: string}]->(:Page)
(:Page)-[:BELONGS_TO]->(:Category)
(:ContentItem)-[:HAS_TOPIC {confidence: float}]->(:Topic)
(:ContentItem)-[:TARGETS]->(:Persona)
(:Topic)-[:CHILD_OF]->(:Topic)
(:Category)-[:CHILD_OF]->(:Category)
```

### 4.2 Indexes

```cypher
// Unique indexes
CREATE CONSTRAINT ON (p:Page) ASSERT p.url IS UNIQUE;
CREATE CONSTRAINT ON (p:Page) ASSERT p.id IS UNIQUE;
CREATE CONSTRAINT ON (t:Topic) ASSERT t.id IS UNIQUE;

// Performance indexes
CREATE INDEX ON :Page(type);
CREATE INDEX ON :Page(updatedAt);
CREATE INDEX ON :ContentItem(hash);
CREATE INDEX ON :Topic(name);
CREATE INDEX ON :Category(level);
```

### 4.3 JSON Storage Format

```json
{
  "pages": {
    "page-uuid-1": {
      "id": "page-uuid-1",
      "url": "https://london.edu/programmes",
      "title": "Programmes",
      "type": "program",
      "sections": ["section-uuid-1", "section-uuid-2"]
    }
  },
  "sections": {
    "section-uuid-1": {
      "id": "section-uuid-1",
      "type": "hero",
      "heading": "Our Programmes",
      "contentItems": ["content-uuid-1"]
    }
  },
  "contentItems": {
    "content-uuid-1": {
      "id": "content-uuid-1",
      "hash": "abc123...",
      "text": "London Business School offers...",
      "topics": ["topic-uuid-1"],
      "sentiment": { "polarity": 0.8, "label": "positive" }
    }
  },
  "topics": {
    "topic-uuid-1": {
      "id": "topic-uuid-1",
      "name": "MBA",
      "category": "Programs"
    }
  }
}
```

---

## 5. Processing Specifications

### 5.1 Crawling Rules

```yaml
crawler:
  user_agent: "LBS-KnowledgeGraph-Bot/1.0"
  respect_robots_txt: true
  crawl_delay: 2000ms          # 2 second delay between requests
  max_concurrent_requests: 5
  timeout: 30000ms
  retry_attempts: 3
  retry_delay: 5000ms

  allowed_domains:
    - london.edu

  excluded_paths:
    - /api/*
    - /admin/*
    - /login
    - /logout

  max_depth: 5
  max_pages: 10000
```

### 5.2 LLM Processing Specs

```yaml
llm:
  provider: openai              # or anthropic
  model: gpt-4-turbo
  temperature: 0.3              # Low for consistency
  max_tokens: 2000

  rate_limits:
    requests_per_minute: 60
    tokens_per_minute: 150000

  retry_policy:
    max_attempts: 3
    backoff: exponential
    initial_delay: 1000ms
    max_delay: 10000ms

  caching:
    enabled: true
    ttl: 86400                  # 24 hours
    strategy: content_hash
```

### 5.3 Semantic Analysis Prompts

**Sentiment Analysis:**
```
Analyze the sentiment of the following text and provide a score from -1 (very negative) to +1 (very positive), along with a label (positive, neutral, or negative) and confidence level (0-1).

Text: {text}

Respond in JSON format:
{
  "polarity": 0.7,
  "label": "positive",
  "confidence": 0.85
}
```

**Topic Extraction:**
```
Extract the main topics from the following text. Focus on business school-relevant topics such as programs, research areas, departments, and business concepts.

Text: {text}

Provide up to 5 topics. Respond in JSON format:
{
  "topics": ["Finance", "MBA", "Leadership"]
}
```

**Audience Classification:**
```
Identify the target audience for this content. Options: prospective_student, current_student, alumni, faculty, researcher, corporate_partner, media.

Text: {text}

You may select multiple audiences. Respond in JSON format:
{
  "audiences": ["prospective_student", "alumni"]
}
```

---

## 6. File Format Specifications

### 6.1 DOM JSON Format

```json
{
  "version": "1.0",
  "url": "https://london.edu/programmes",
  "timestamp": "2025-11-01T12:00:00Z",
  "dom": {
    "tag": "html",
    "attributes": { "lang": "en" },
    "children": [
      {
        "tag": "head",
        "children": [...]
      },
      {
        "tag": "body",
        "children": [
          {
            "tag": "main",
            "children": [
              {
                "tag": "h1",
                "text": "{{hash:abc123}}",
                "textHash": "abc123..."
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 6.2 Text Hash Format

```json
{
  "version": "1.0",
  "hashes": {
    "abc123...": "London Business School offers world-class programmes...",
    "def456...": "Our MBA is ranked #1 in Europe...",
    "ghi789...": "Apply now for September 2026 intake"
  }
}
```

### 6.3 Graph Export Format (JSON)

```json
{
  "version": "1.0",
  "exported": "2025-11-01T12:00:00Z",
  "graph": {
    "nodes": [
      {
        "id": "page-1",
        "labels": ["Page"],
        "properties": {
          "url": "https://london.edu",
          "title": "Home"
        }
      }
    ],
    "edges": [
      {
        "id": "edge-1",
        "type": "LINKS_TO",
        "source": "page-1",
        "target": "page-2",
        "properties": {}
      }
    ]
  }
}
```

---

## 7. Interface Specifications

### 7.1 UI Component Specifications

#### Search Component
```typescript
interface SearchProps {
  placeholder?: string;
  filters?: FilterConfig[];
  onSearch: (query: string, filters: Filters) => void;
  suggestions?: string[];
  debounce?: number;           // Default: 300ms
}

interface FilterConfig {
  name: string;
  type: 'select' | 'multiselect' | 'range' | 'toggle';
  options?: string[];
  default?: any;
}
```

#### Graph Visualizer Component
```typescript
interface GraphVisualizerProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  layout?: 'force' | 'hierarchical' | 'circular' | 'grid';
  interactive?: boolean;
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  zoom?: boolean;
  height?: number;
}
```

#### Tag Editor Component
```typescript
interface TagEditorProps {
  nodeId: string;
  tags: string[];
  suggestions?: string[];
  onSave: (tags: string[]) => Promise<void>;
  readonly?: boolean;
  maxTags?: number;
}
```

---

## 8. Testing Specifications

### 8.1 Unit Test Requirements
- **Coverage:** 80% minimum
- **Framework:** Jest or Mocha
- **Mocking:** Mock external APIs and databases
- **Assertions:** Clear, descriptive test names

### 8.2 Integration Test Requirements
- **API Tests:** Test all endpoints with real database
- **E2E Tests:** Playwright or Cypress for UI testing
- **Performance:** Load testing with JMeter or K6
- **Data:** Use test fixtures and factories

### 8.3 Test Data
```yaml
test_pages:
  - url: https://london.edu
    expected_sections: 5
    expected_links: 20
  - url: https://london.edu/programmes
    expected_sections: 8
    expected_content_items: 50
```

---

**Document Version:** 1.0
**Last Updated:** November 2025
