# Data Model and Schema

## Overview

This document defines the complete data model for the LBS Semantic Knowledge Graph platform, including entity relationships, schemas, and data transformation rules.

---

## 1. Entity-Relationship Diagram

```
┌──────────────┐
│   Category   │
│              │◄───┐
└──────────────┘    │
       ▲            │
       │ CHILD_OF   │ BELONGS_TO
       │            │
┌──────────────┐    │
│    Topic     │    │
│              │    │
└──────────────┘    │
       ▲            │
       │            │
       │ HAS_TOPIC  │
       │            │
┌──────────────┐    │
│  ContentItem │    │
│              │    │
└──────────────┘    │
       ▲            │
       │            │
       │ CONTAINS   │
       │            │
┌──────────────┐    │
│   Section    │    │
│              │    │
└──────────────┘    │
       ▲            │
       │            │
       │ CONTAINS   │
       │            │
┌──────────────┐    │
│     Page     ├────┘
│              │
└──────────────┘
       │
       │ LINKS_TO
       ▼
┌──────────────┐
│     Page     │
│              │
└──────────────┘

┌──────────────┐
│   Persona    │◄───── TARGETS ──────┐
│              │                      │
└──────────────┘              ┌──────────────┐
                              │  ContentItem │
                              │              │
                              └──────────────┘
```

---

## 2. Core Entities

### 2.1 Page Entity

**Description:** Represents a webpage from london.edu

**Schema:**
```typescript
interface Page {
  // Core fields
  id: string;                    // UUID v4
  url: string;                   // Canonical URL (unique)
  title: string;                 // Page title
  description?: string;          // Meta description

  // Classification
  type: PageType;               // Page classification
  category?: string;            // Primary category
  language: string;             // ISO 639-1 code (default: 'en')

  // Content tracking
  hash: string;                 // SHA-256 hash of raw HTML
  contentHash: string;          // SHA-256 hash of extracted content
  version: number;              // Version number (incremented on change)

  // Metadata
  createdAt: Date;              // First crawl timestamp
  updatedAt: Date;              // Last update timestamp
  fetchedAt: Date;              // Last fetch timestamp
  publishedAt?: Date;           // Original publish date (if available)

  // SEO & Social
  keywords: string[];           // Meta keywords
  ogImage?: string;             // Open Graph image
  ogDescription?: string;       // Open Graph description

  // Analytics
  importance: number;           // Calculated importance score (0-1)
  depth: number;                // Distance from homepage
  inboundLinks: number;         // Number of pages linking to this
  outboundLinks: number;        // Number of links from this page

  // Custom metadata
  metadata: Record<string, any>;
}

enum PageType {
  Homepage = 'homepage',
  Program = 'program',          // Degree programs (MBA, Masters, etc.)
  Faculty = 'faculty',          // Faculty member profiles
  Research = 'research',        // Research areas, publications
  News = 'news',               // News articles
  Event = 'event',             // Events, webinars
  About = 'about',             // About pages
  Admissions = 'admissions',   // Admissions information
  StudentLife = 'student_life', // Student life and campus
  Alumni = 'alumni',           // Alumni resources
  Contact = 'contact',         // Contact pages
  Other = 'other'              // Uncategorized
}
```

**Indexes:**
- Primary: `id` (UUID, unique)
- Unique: `url`
- Indexed: `type`, `category`, `updatedAt`, `importance`

**Relationships:**
- `Page` --[CONTAINS]--> `Section` (1:many)
- `Page` --[LINKS_TO]--> `Page` (many:many)
- `Page` --[BELONGS_TO]--> `Category` (many:1)

---

### 2.2 Section Entity

**Description:** Represents a section or component within a page

**Schema:**
```typescript
interface Section {
  // Core fields
  id: string;                    // UUID v4
  pageId: string;               // Parent page ID

  // Classification
  type: SectionType;            // Section type
  component?: string;           // Component identifier

  // Content
  heading?: string;             // Section heading
  subheading?: string;          // Section subheading
  order: number;                // Display order on page (0-indexed)

  // Metadata
  cssSelector?: string;         // Original CSS selector
  attributes: Record<string, string>; // HTML attributes

  // Custom metadata
  metadata: Record<string, any>;
}

enum SectionType {
  Hero = 'hero',               // Hero/banner section
  Content = 'content',         // Main content area
  Sidebar = 'sidebar',         // Sidebar content
  Navigation = 'navigation',   // Navigation menu
  Footer = 'footer',           // Footer section
  Header = 'header',           // Header section
  Callout = 'callout',        // Call-to-action or callout box
  Listing = 'listing',        // List of items (news, events, etc.)
  Profile = 'profile',        // Profile information
  Stats = 'stats',            // Statistics or metrics
  Testimonial = 'testimonial', // Testimonial or quote
  Gallery = 'gallery',        // Image gallery
  Form = 'form',              // Form section
  Other = 'other'             // Uncategorized
}
```

**Indexes:**
- Primary: `id`
- Indexed: `pageId`, `type`, `order`

**Relationships:**
- `Section` --[CONTAINS]--> `ContentItem` (1:many)
- `Page` --[CONTAINS]--> `Section` (1:many)

---

### 2.3 ContentItem Entity

**Description:** Represents an atomic piece of content (text, image, etc.)

**Schema:**
```typescript
interface ContentItem {
  // Core fields
  id: string;                    // UUID v4
  hash: string;                  // SHA-256 hash of content

  // Content
  text: string;                  // Text content
  type: ContentType;            // Content type

  // Semantics (LLM-generated)
  sentiment?: SentimentScore;   // Sentiment analysis
  topics: string[];             // Topic IDs
  keywords: string[];           // Extracted keywords
  entities: Entity[];           // Named entities

  // Audience
  audiences: string[];          // Persona IDs
  readingLevel?: number;        // Reading level (1-12)

  // Usage tracking
  pageIds: string[];            // Pages using this content
  sectionIds: string[];         // Sections using this content
  usageCount: number;           // Number of times used

  // Metadata
  language: string;             // ISO 639-1 code
  wordCount: number;            // Word count
  charCount: number;            // Character count

  // Custom metadata
  metadata: Record<string, any>;
}

enum ContentType {
  Paragraph = 'paragraph',
  Heading = 'heading',
  Subheading = 'subheading',
  List = 'list',
  ListItem = 'list_item',
  Quote = 'quote',
  Code = 'code',
  Table = 'table',
  Image = 'image',
  Video = 'video',
  Link = 'link',
  Button = 'button',
  Other = 'other'
}

interface SentimentScore {
  polarity: number;             // -1 (negative) to +1 (positive)
  confidence: number;           // 0 to 1
  label: 'positive' | 'neutral' | 'negative';
  magnitude?: number;           // Strength of sentiment (0-1)
}

interface Entity {
  text: string;                 // Entity text
  type: EntityType;             // Entity type
  confidence: number;           // Confidence score (0-1)
}

enum EntityType {
  Person = 'person',
  Organization = 'organization',
  Location = 'location',
  Date = 'date',
  Program = 'program',
  Course = 'course',
  Department = 'department',
  Other = 'other'
}
```

**Indexes:**
- Primary: `id`
- Unique: `hash`
- Indexed: `type`, `usageCount`
- Full-text: `text`, `keywords`

**Relationships:**
- `ContentItem` --[HAS_TOPIC]--> `Topic` (many:many)
- `ContentItem` --[TARGETS]--> `Persona` (many:many)
- `Section` --[CONTAINS]--> `ContentItem` (1:many)

---

### 2.4 Topic Entity

**Description:** Represents a topic or theme

**Schema:**
```typescript
interface Topic {
  // Core fields
  id: string;                    // UUID v4
  name: string;                  // Topic name
  slug: string;                  // URL-friendly slug

  // Classification
  category: string;             // Category ID
  level: number;                // Hierarchy level (0 = root)
  parentId?: string;            // Parent topic ID

  // Description
  description?: string;          // Topic description
  aliases: string[];            // Alternative names

  // Relationships
  relatedTopics: string[];      // Related topic IDs
  subtopics: string[];          // Child topic IDs

  // Metrics
  contentCount: number;         // Number of content items
  pageCount: number;            // Number of pages
  importance: number;           // Calculated importance (0-1)

  // Visualization
  icon?: string;                // Icon identifier
  color?: string;               // Display color (hex)

  // Custom metadata
  metadata: Record<string, any>;
}
```

**Indexes:**
- Primary: `id`
- Unique: `slug`
- Indexed: `category`, `level`, `name`, `importance`

**Relationships:**
- `Topic` --[CHILD_OF]--> `Topic` (many:1)
- `Topic` --[BELONGS_TO]--> `Category` (many:1)
- `ContentItem` --[HAS_TOPIC]--> `Topic` (many:many)

---

### 2.5 Category Entity

**Description:** Represents a high-level category in the taxonomy

**Schema:**
```typescript
interface Category {
  // Core fields
  id: string;                    // UUID v4
  name: string;                  // Category name
  slug: string;                  // URL-friendly slug

  // Hierarchy
  level: number;                // Hierarchy level (0 = root)
  parentId?: string;            // Parent category ID
  children: string[];           // Child category IDs
  path: string[];               // Full path from root (IDs)

  // Description
  description?: string;          // Category description

  // Visualization
  icon?: string;                // Icon identifier
  color?: string;               // Display color (hex)
  order: number;                // Display order

  // Metrics
  topicCount: number;           // Number of topics
  pageCount: number;            // Number of pages

  // Custom metadata
  metadata: Record<string, any>;
}
```

**Indexes:**
- Primary: `id`
- Unique: `slug`
- Indexed: `level`, `parentId`, `order`

**Relationships:**
- `Category` --[CHILD_OF]--> `Category` (many:1)
- `Topic` --[BELONGS_TO]--> `Category` (many:1)
- `Page` --[BELONGS_TO]--> `Category` (many:1)

---

### 2.6 Persona Entity

**Description:** Represents a user persona/audience type

**Schema:**
```typescript
interface Persona {
  // Core fields
  id: string;                    // UUID v4
  name: string;                  // Persona name
  slug: string;                  // URL-friendly slug
  type: PersonaType;            // Persona type

  // Description
  description: string;           // Persona description
  demographics?: Demographics;   // Demographic info

  // Interests
  interests: string[];          // Topic IDs
  preferredContent: ContentType[]; // Preferred content types
  excludedContent: ContentType[]; // Excluded content types

  // Behavior
  goals: string[];              // User goals
  painPoints: string[];         // Pain points

  // Visualization
  avatar?: string;              // Avatar URL
  color?: string;               // Display color (hex)
  priority: number;             // Display priority (1-5)

  // Metrics
  contentCount: number;         // Number of content items
  pageCount: number;            // Number of pages

  // Custom metadata
  metadata: Record<string, any>;
}

enum PersonaType {
  ProspectiveStudent = 'prospective_student',
  CurrentStudent = 'current_student',
  Alumni = 'alumni',
  Faculty = 'faculty',
  Researcher = 'researcher',
  CorporatePartner = 'corporate_partner',
  Media = 'media',
  Recruiter = 'recruiter',
  Donor = 'donor'
}

interface Demographics {
  ageRange?: string;            // e.g., "25-35"
  location?: string[];          // Locations
  occupation?: string[];        // Occupations
  education?: string[];         // Education levels
}
```

**Indexes:**
- Primary: `id`
- Unique: `slug`
- Indexed: `type`, `priority`

**Relationships:**
- `ContentItem` --[TARGETS]--> `Persona` (many:many)

---

## 3. Relationship Types

### 3.1 CONTAINS

**Description:** Hierarchical containment relationship

**Properties:**
```typescript
interface ContainsRelationship {
  order: number;                // Display order
  required?: boolean;           // Is this item required?
  conditional?: string;         // Condition for display
}
```

**Examples:**
- `Page` --[CONTAINS {order: 0}]--> `Section`
- `Section` --[CONTAINS {order: 1}]--> `ContentItem`

---

### 3.2 LINKS_TO

**Description:** Hyperlink relationship between pages

**Properties:**
```typescript
interface LinksToRelationship {
  text: string;                 // Link anchor text
  type: LinkType;               // Link type
  position?: number;            // Position on source page
  context?: string;             // Surrounding context
}

enum LinkType {
  Navigation = 'navigation',    // Navigation link
  Internal = 'internal',        // Internal content link
  Reference = 'reference',      // Reference/citation
  Related = 'related',          // Related content
  External = 'external'         // External link (rare)
}
```

**Examples:**
- `Page(homepage)` --[LINKS_TO {text: "Programmes", type: "navigation"}]--> `Page(programmes)`

---

### 3.3 HAS_TOPIC

**Description:** Content is about a topic

**Properties:**
```typescript
interface HasTopicRelationship {
  confidence: number;           // LLM confidence (0-1)
  source: 'llm' | 'manual' | 'rule';
  method?: string;              // Extraction method
  extractedAt: Date;            // When extracted
}
```

**Examples:**
- `ContentItem` --[HAS_TOPIC {confidence: 0.95, source: "llm"}]--> `Topic(Finance)`

---

### 3.4 BELONGS_TO

**Description:** Entity belongs to a category

**Properties:**
```typescript
interface BelongsToRelationship {
  primary: boolean;             // Is this the primary category?
  source: 'manual' | 'inferred' | 'llm';
}
```

**Examples:**
- `Page(mba)` --[BELONGS_TO {primary: true}]--> `Category(Programs)`
- `Topic(Finance)` --[BELONGS_TO]--> `Category(Subjects)`

---

### 3.5 TARGETS

**Description:** Content targets a specific persona

**Properties:**
```typescript
interface TargetsRelationship {
  relevance: number;            // Relevance score (0-1)
  source: 'llm' | 'manual' | 'rule';
}
```

**Examples:**
- `ContentItem` --[TARGETS {relevance: 0.9}]--> `Persona(ProspectiveStudent)`

---

### 3.6 CHILD_OF

**Description:** Hierarchical parent-child relationship

**Properties:**
```typescript
interface ChildOfRelationship {
  order?: number;               // Order among siblings
}
```

**Examples:**
- `Topic(MBA)` --[CHILD_OF]--> `Topic(Programs)`
- `Category(Masters)` --[CHILD_OF]--> `Category(Programs)`

---

## 4. Graph Schema Diagram

```
Graph Schema (Cypher Notation)

// Nodes
(:Page {id, url, title, type, hash, createdAt, updatedAt})
(:Section {id, pageId, type, heading, order})
(:ContentItem {id, hash, text, type, sentiment, topics, audiences})
(:Topic {id, name, slug, category, level, contentCount})
(:Category {id, name, slug, level, parentId})
(:Persona {id, name, type, description, priority})

// Relationships
(:Page)-[:CONTAINS {order}]->(:Section)
(:Section)-[:CONTAINS {order}]->(:ContentItem)
(:Page)-[:LINKS_TO {text, type}]->(:Page)
(:Page)-[:BELONGS_TO {primary}]->(:Category)
(:ContentItem)-[:HAS_TOPIC {confidence, source}]->(:Topic)
(:ContentItem)-[:TARGETS {relevance}]->(:Persona)
(:Topic)-[:CHILD_OF {order}]->(:Topic)
(:Topic)-[:BELONGS_TO]->(:Category)
(:Category)-[:CHILD_OF {order}]->(:Category)
```

---

## 5. Data Transformation Rules

### 5.1 HTML to Page

```typescript
function htmlToPage(html: string, url: string): Page {
  const $ = cheerio.load(html);

  return {
    id: generateUUID(),
    url: normalizeURL(url),
    title: $('title').text() || $('h1').first().text(),
    description: $('meta[name="description"]').attr('content'),
    type: inferPageType(url, $),
    language: $('html').attr('lang') || 'en',
    hash: hashContent(html),
    contentHash: hashContent(extractContent($)),
    version: 1,
    createdAt: new Date(),
    updatedAt: new Date(),
    fetchedAt: new Date(),
    keywords: extractKeywords($),
    ogImage: $('meta[property="og:image"]').attr('content'),
    ogDescription: $('meta[property="og:description"]').attr('content'),
    importance: calculateImportance(url),
    depth: calculateDepth(url),
    inboundLinks: 0,
    outboundLinks: $('a[href^="/"], a[href^="https://london.edu"]').length,
    metadata: extractMetadata($)
  };
}
```

### 5.2 HTML to Sections

```typescript
function htmlToSections(html: string, pageId: string): Section[] {
  const $ = cheerio.load(html);
  const sections: Section[] = [];

  // Find main content sections
  $('main section, article, .content-block').each((index, elem) => {
    sections.push({
      id: generateUUID(),
      pageId,
      type: inferSectionType($(elem)),
      component: $(elem).attr('class')?.split(' ')[0],
      heading: $(elem).find('h1, h2, h3').first().text(),
      order: index,
      cssSelector: generateSelector(elem),
      attributes: extractAttributes(elem),
      metadata: {}
    });
  });

  return sections;
}
```

### 5.3 Text to ContentItems

```typescript
function textToContentItems(text: string, sectionId: string): ContentItem[] {
  const items: ContentItem[] = [];

  // Split by paragraphs
  const paragraphs = text.split('\n\n').filter(p => p.trim());

  for (const para of paragraphs) {
    const hash = hashText(para);
    items.push({
      id: generateUUID(),
      hash,
      text: para,
      type: inferContentType(para),
      topics: [],
      keywords: [],
      entities: [],
      audiences: [],
      pageIds: [],
      sectionIds: [sectionId],
      usageCount: 1,
      language: detectLanguage(para),
      wordCount: countWords(para),
      charCount: para.length,
      metadata: {}
    });
  }

  return items;
}
```

### 5.4 LLM Response to Semantic Data

```typescript
async function enrichContentWithLLM(item: ContentItem): Promise<ContentItem> {
  // Sentiment analysis
  const sentimentResponse = await llm.analyzeSentiment(item.text);
  item.sentiment = parseSentiment(sentimentResponse);

  // Topic extraction
  const topicsResponse = await llm.extractTopics(item.text);
  item.topics = parseTopics(topicsResponse);

  // Audience classification
  const audienceResponse = await llm.classifyAudience(item.text);
  item.audiences = parseAudiences(audienceResponse);

  // Named entity recognition
  const entitiesResponse = await llm.extractEntities(item.text);
  item.entities = parseEntities(entitiesResponse);

  return item;
}
```

---

## 6. Data Validation Rules

### 6.1 Page Validation

```typescript
const pageSchema = z.object({
  id: z.string().uuid(),
  url: z.string().url().regex(/^https:\/\/london\.edu/),
  title: z.string().min(1).max(200),
  description: z.string().max(500).optional(),
  type: z.nativeEnum(PageType),
  language: z.string().length(2),
  hash: z.string().length(64), // SHA-256
  contentHash: z.string().length(64),
  version: z.number().int().positive(),
  createdAt: z.date(),
  updatedAt: z.date(),
  fetchedAt: z.date(),
  importance: z.number().min(0).max(1),
  depth: z.number().int().min(0),
  inboundLinks: z.number().int().min(0),
  outboundLinks: z.number().int().min(0)
});
```

### 6.2 Content Item Validation

```typescript
const contentItemSchema = z.object({
  id: z.string().uuid(),
  hash: z.string().length(64),
  text: z.string().min(1).max(10000),
  type: z.nativeEnum(ContentType),
  sentiment: z.object({
    polarity: z.number().min(-1).max(1),
    confidence: z.number().min(0).max(1),
    label: z.enum(['positive', 'neutral', 'negative'])
  }).optional(),
  topics: z.array(z.string().uuid()),
  audiences: z.array(z.string().uuid()),
  usageCount: z.number().int().min(0),
  wordCount: z.number().int().min(0),
  charCount: z.number().int().min(0)
});
```

---

## 7. Migration Scripts

### 7.1 Initial Data Load

```sql
-- Create all nodes
UNWIND $pages AS page
CREATE (p:Page)
SET p = page

UNWIND $sections AS section
CREATE (s:Section)
SET s = section

UNWIND $contentItems AS item
CREATE (c:ContentItem)
SET c = item

-- Create relationships
UNWIND $contains AS rel
MATCH (parent {id: rel.parentId})
MATCH (child {id: rel.childId})
CREATE (parent)-[:CONTAINS {order: rel.order}]->(child)

UNWIND $linksTo AS rel
MATCH (source:Page {id: rel.sourceId})
MATCH (target:Page {id: rel.targetId})
CREATE (source)-[:LINKS_TO {text: rel.text, type: rel.type}]->(target)
```

---

**Document Version:** 1.0
**Last Updated:** November 2025
