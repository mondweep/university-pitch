# Content Analysis - LBS Knowledge Graph Project

## Document Information
- **Project:** London Business School Semantic Knowledge Graph
- **Phase:** Phase 1 Research (Pre-Phase 2)
- **Created:** 2025-11-05
- **Purpose:** Comprehensive analysis of content patterns to guide Phase 2 domain modeling

---

## Executive Summary

This document analyzes the London Business School (london.edu) website structure and content patterns based on:
1. Review of existing crawler and parser implementations
2. Analysis of schema requirements from `04_DATA_MODEL_SCHEMA.md`
3. Research of typical Next.js university website patterns
4. Preparation recommendations for Phase 2 domain modeling

**Key Finding:** The project infrastructure is well-designed for scalable content extraction with hash-based deduplication, Next.js data extraction capabilities, and robust DOM parsing. Phase 2 should focus on implementing domain-specific classifiers and semantic enrichment pipelines.

---

## 1. Existing Infrastructure Analysis

### 1.1 Crawler Implementation (`src/crawler/crawler.py`)

**Capabilities:**
- ✅ Configurable URL queuing with BFS traversal
- ✅ Politeness delays (2000ms default) and rate limiting
- ✅ URL normalization and validation
- ✅ HTML + metadata extraction (status codes, headers, timestamps)
- ✅ MD5-based filename generation for storage
- ✅ Failed URL tracking and retry capability
- ✅ Statistics tracking (pages/second, success rate)

**Content Patterns Detected:**
```python
# Excluded paths (from crawler.py lines 95-96)
excluded_paths = ['/api/', '/admin/', '/login', '/logout', '/search']

# Excluded file types (lines 100-101)
excluded_extensions = ['.pdf', '.jpg', '.png', '.zip', '.doc', '.xls']

# Initial seed URLs (lines 309-320)
- Homepage: https://london.edu
- About: /about
- Programmes: /programmes
- Faculty & Research: /faculty-and-research
- News: /news
- Events: /events
- Admissions: /admissions
- Student Life: /student-life
- Alumni: /alumni
- Contact: /contact
```

**Analysis:** The crawler is designed for 10+ core page types, suggesting LBS follows a standard university information architecture.

---

### 1.2 Parser Implementation (`src/parser/html_parser.py`)

**Capabilities:**
- ✅ SHA-256 content hashing for deduplication
- ✅ Recursive DOM tree parsing with depth tracking
- ✅ Next.js `__NEXT_DATA__` extraction (line 132-152)
- ✅ Metadata extraction (title, meta tags, OG tags, language)
- ✅ Link extraction with type classification (internal/external/anchor)
- ✅ Text normalization and whitespace cleanup
- ✅ Attribute filtering (removes React noise)

**Content Hash Pattern:**
```python
# Hash generation (lines 31-46)
- Normalizes whitespace before hashing
- Uses SHA-256 for collision resistance
- Tracks hash usage count across pages
- Stores hash-to-text bidirectional mapping
```

**Output Structure:**
```
parsed/
  {page_name}/
    dom.json          # Full DOM tree with text_hash references
    text.json         # hash -> text content mapping
    metadata.json     # Title, meta tags, OG data
    links.json        # All page links with types
    nextjs-data.json  # Next.js server-side data (if present)
```

**Key Insight:** The parser already implements the content hash consolidation required for Phase 2 (Task 2.3 in Implementation Plan).

---

## 2. Expected Content Patterns (london.edu)

### 2.1 Page Type Classification

Based on seed URLs and typical business school structure:

| Page Type | URL Pattern | Expected Sections | Priority |
|-----------|-------------|-------------------|----------|
| Homepage | `/` | Hero, News Carousel, Stats, CTA | High |
| Programme | `/programmes/*` | Overview, Curriculum, Admissions, Faculty | High |
| Faculty Profile | `/faculty-and-research/faculty/*` | Bio, Research, Publications, Courses | High |
| Research Area | `/faculty-and-research/*` | Overview, Projects, Publications | Medium |
| News Article | `/news/*` | Title, Date, Body, Related | Medium |
| Event | `/events/*` | Title, Date, Location, Registration | Medium |
| About | `/about/*` | Mission, History, Leadership | Low |
| Admissions | `/admissions/*` | Requirements, Process, Deadlines | High |
| Student Life | `/student-life/*` | Campus, Clubs, Resources | Medium |
| Alumni | `/alumni/*` | Network, Events, Benefits | Low |
| Contact | `/contact` | Form, Addresses, Directories | Low |

**Classification Strategy:**
```python
def infer_page_type(url: str, soup: BeautifulSoup) -> PageType:
    """
    URL pattern matching:
    - /programmes/ -> PageType.Program
    - /faculty-and-research/faculty/ -> PageType.Faculty
    - /news/ -> PageType.News
    - /events/ -> PageType.Event

    Fallback to content analysis:
    - Check for schema.org markup
    - Analyze breadcrumb structure
    - Match keywords in title/headings
    """
```

---

### 2.2 Section Type Patterns

Expected component patterns (based on schema `SectionType` enum):

**Hero Sections:**
```html
<!-- Expected patterns -->
<section class="hero">
  <h1>Programme Title</h1>
  <p class="subtitle">Description</p>
  <button>Apply Now</button>
</section>

<div class="banner hero-banner">
  <video />
  <div class="hero-content">...</div>
</div>
```

**Navigation Sections:**
```html
<nav class="main-nav">
  <ul>
    <li><a href="/programmes">Programmes</a></li>
    ...
  </ul>
</nav>

<div class="breadcrumb">
  <a href="/">Home</a> > <a href="/programmes">Programmes</a> > MBA
</div>
```

**Listing Sections:**
```html
<!-- News listings -->
<section class="news-list">
  <article class="news-item">
    <h3>Title</h3>
    <time>Date</time>
    <p>Summary</p>
  </article>
  ...
</section>

<!-- Faculty directory -->
<div class="faculty-grid">
  <div class="faculty-card">...</div>
</div>
```

**Profile Sections:**
```html
<section class="profile">
  <img class="avatar" />
  <h2 class="name">Professor Name</h2>
  <p class="title">Position</p>
  <div class="bio">...</div>
  <ul class="research-interests">...</ul>
</section>
```

**Classification Heuristics:**
```python
def infer_section_type(element: Tag) -> SectionType:
    """
    1. Check element tag and class attributes
    2. Analyze child element patterns
    3. Check position in DOM (first section = likely hero)
    4. Count children (lists vs. single content)
    """
    if element.find('h1') and element.find('button', class_re='cta|apply'):
        return SectionType.Hero

    if element.name == 'nav' or 'nav' in element.get('class', []):
        return SectionType.Navigation

    if len(element.find_all('article')) >= 3:
        return SectionType.Listing

    # ... additional rules
```

---

### 2.3 Next.js Data Patterns

**Expected `__NEXT_DATA__` Structure:**
```json
{
  "props": {
    "pageProps": {
      "page": {
        "title": "MBA Programme",
        "slug": "mba",
        "content": [...],
        "metadata": {
          "description": "...",
          "keywords": ["MBA", "Business School"]
        }
      },
      "posts": [...],           // For news/blog pages
      "faculty": [...],         // For faculty directory
      "programmes": [...]       // For programme listing
    }
  },
  "page": "/programmes/[slug]",
  "query": {"slug": "mba"},
  "buildId": "...",
  "isFallback": false
}
```

**Data Extraction Strategy:**
1. **Priority:** Check `pageProps` for structured content
2. **Validation:** Compare with HTML content for completeness
3. **Enrichment:** Use Next.js data for metadata not in HTML
4. **Deduplication:** Cross-reference text with HTML hashes

---

## 3. Content Pattern Analysis Framework

### 3.1 Pattern Recognition Algorithm

**Phase 2 Implementation Approach:**

```python
class ContentPatternAnalyzer:
    """Analyzes parsed JSON to identify recurring patterns"""

    def __init__(self, parsed_dir: Path):
        self.parsed_pages = self._load_parsed_pages(parsed_dir)
        self.patterns = {}

    def analyze_dom_patterns(self):
        """Identify common DOM structures"""
        for page in self.parsed_pages:
            # Extract CSS selectors from attributes
            # Cluster similar structures
            # Identify reusable components
            pass

    def analyze_text_patterns(self):
        """Analyze text content patterns"""
        # Word frequency analysis
        # Sentence structure patterns
        # Content type classification (paragraph vs. list vs. heading)
        pass

    def analyze_link_patterns(self):
        """Analyze internal linking structure"""
        # Build adjacency matrix
        # Identify navigation clusters
        # Calculate PageRank-style importance
        pass

    def generate_component_taxonomy(self) -> Dict[str, List[str]]:
        """
        Returns taxonomy of identified components

        Example:
        {
          "Hero": ["hero-section", "banner", "jumbotron"],
          "Navigation": ["main-nav", "breadcrumb", "sidebar-nav"],
          "Listing": ["news-grid", "faculty-list", "programme-cards"]
        }
        """
        pass
```

---

### 3.2 Text Content Analysis

**Hash-Based Content Reuse Analysis:**

```python
def analyze_content_reuse(parsed_dir: Path) -> Dict[str, Any]:
    """
    Analyzes how text content is reused across pages

    Returns:
    {
      "total_unique_texts": 500,
      "total_text_instances": 1500,
      "reuse_ratio": 3.0,
      "most_reused": [
        {"hash": "abc123", "text": "Apply now", "usage_count": 50},
        ...
      ],
      "unique_to_page": {
        "mba_page": 120,  # Number of unique texts
        "homepage": 80
      }
    }
    """
    global_hashes = {}

    for page_dir in parsed_dir.glob('*/'):
        text_file = page_dir / 'text.json'
        if text_file.exists():
            with open(text_file) as f:
                page_hashes = json.load(f)

            for hash_val, text in page_hashes.items():
                if hash_val not in global_hashes:
                    global_hashes[hash_val] = {
                        'text': text,
                        'pages': [],
                        'count': 0
                    }
                global_hashes[hash_val]['pages'].append(page_dir.name)
                global_hashes[hash_val]['count'] += 1

    # Analyze reuse patterns
    ...
```

**Expected Patterns:**
- **High Reuse (50+ instances):** CTAs ("Apply Now", "Learn More"), navigation labels, footer content
- **Medium Reuse (5-50):** Programme descriptions, faculty bio templates
- **Low Reuse (1-5):** Unique page content, news articles, event descriptions

---

## 4. Metadata Extraction Patterns

### 4.1 Meta Tags Analysis

**Expected Meta Structure:**
```html
<head>
  <title>MBA Programme | London Business School</title>
  <meta name="description" content="..."/>
  <meta name="keywords" content="MBA, Business School, London"/>

  <!-- Open Graph -->
  <meta property="og:title" content="MBA Programme"/>
  <meta property="og:type" content="website"/>
  <meta property="og:url" content="https://london.edu/programmes/mba"/>
  <meta property="og:image" content="https://london.edu/images/mba-hero.jpg"/>
  <meta property="og:description" content="..."/>

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image"/>
  <meta name="twitter:site" content="@LondonBSchool"/>

  <!-- Schema.org -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "EducationalOrganization",
    "name": "London Business School",
    ...
  }
  </script>
</head>
```

**Metadata Enrichment Pipeline:**
```python
def extract_structured_data(metadata: Dict) -> Dict:
    """
    Extracts and normalizes structured data

    Priority:
    1. Schema.org JSON-LD (highest confidence)
    2. Open Graph tags
    3. Standard meta tags
    4. Twitter Card tags
    5. HTML title/headings
    """
    structured = {
        'title': metadata.get('og_title') or metadata.get('title'),
        'description': metadata.get('og_description') or metadata.get('description'),
        'canonical_url': metadata.get('canonical_url'),
        'language': metadata.get('language', 'en'),
        'image': metadata.get('og_image'),
        'type': metadata.get('og_type', 'website')
    }

    # Extract schema.org if present
    if 'schema_org' in metadata:
        structured['schema'] = metadata['schema_org']

    return structured
```

---

## 5. Link Graph Analysis

### 5.1 Link Classification Patterns

**From `html_parser.py` (lines 200-232):**

```python
# Link types already extracted:
- internal: /programmes/mba
- external: https://other-site.com
- anchor: #section-id
- relative: ../other-page
```

**Enhanced Link Analysis for Phase 2:**

```python
class LinkGraphBuilder:
    """Builds graph of page relationships based on links"""

    def build_adjacency_matrix(self, pages: List[Dict]) -> np.ndarray:
        """Creates adjacency matrix for PageRank calculation"""
        pass

    def classify_link_intent(self, link: Dict, context: str) -> LinkIntent:
        """
        Classifies link purpose:
        - Navigation (main menu, breadcrumb)
        - Reference (inline citation)
        - Related (related content widget)
        - CTA (call-to-action button)
        - External (external resource)
        """
        if 'nav' in context or 'menu' in context:
            return LinkIntent.Navigation
        if 'breadcrumb' in context:
            return LinkIntent.Navigation
        if 'related' in context or 'also-read' in context:
            return LinkIntent.Related
        if 'btn' in context or 'cta' in context:
            return LinkIntent.CTA
        return LinkIntent.Reference

    def calculate_page_importance(self) -> Dict[str, float]:
        """
        Calculates importance scores using:
        1. Inbound link count
        2. PageRank algorithm
        3. Depth from homepage
        4. Link anchor text analysis
        """
        pass
```

**Expected Link Patterns:**
```
Homepage -> [Programmes, About, News, Events, Admissions]
  |
  +-> Programmes -> [MBA, Masters, PhD, Executive Ed]
        |
        +-> MBA -> [Curriculum, Admissions, Faculty, Alumni]
              |
              +-> Curriculum -> [Core Courses, Electives, Specializations]
```

---

## 6. Content Type Detection

### 6.1 Automatic Content Type Classification

**From Schema (`ContentType` enum):**
- Paragraph, Heading, Subheading, List, ListItem
- Quote, Code, Table
- Image, Video, Link, Button

**Detection Algorithm:**

```python
def infer_content_type(element: Tag, text: str) -> ContentType:
    """
    Multi-signal content type detection

    Signals:
    1. HTML tag name (h1/h2/p/ul/blockquote)
    2. CSS classes (code-block, quote, table)
    3. Text patterns (starts with number = list item?)
    4. Parent context (inside <ul> = list item)
    5. Text length (short = heading, long = paragraph)
    """
    tag_mapping = {
        'h1': ContentType.Heading,
        'h2': ContentType.Subheading,
        'h3': ContentType.Subheading,
        'p': ContentType.Paragraph,
        'li': ContentType.ListItem,
        'blockquote': ContentType.Quote,
        'pre': ContentType.Code,
        'code': ContentType.Code,
        'table': ContentType.Table,
        'img': ContentType.Image,
        'video': ContentType.Video,
        'button': ContentType.Button,
        'a': ContentType.Link
    }

    if element.name in tag_mapping:
        return tag_mapping[element.name]

    # Fallback to text analysis
    if len(text) < 50 and not text.endswith('.'):
        return ContentType.Heading

    if element.parent and element.parent.name == 'ul':
        return ContentType.ListItem

    return ContentType.Paragraph
```

---

## 7. Recommendations for Phase 2

### 7.1 Immediate Actions

**Week 1: Content Crawling**
1. ✅ Run crawler with initial 10 seed URLs
2. ✅ Validate HTML extraction completeness
3. ✅ Check for rate limiting issues
4. ✅ Review failed URLs and adjust crawler

**Week 2: Pattern Analysis**
1. ✅ Run parser on all crawled pages
2. ✅ Analyze text hash statistics
3. ✅ Identify common DOM patterns
4. ✅ Extract Next.js data structures
5. ✅ Build component taxonomy

---

### 7.2 Domain Modeling Priorities

**High Priority (Week 3-4):**
1. **Page Type Classifier**
   - Implement URL pattern matching
   - Add content-based classification fallback
   - Validate against 10 sample pages

2. **Section Type Classifier**
   - CSS class pattern matching
   - DOM structure analysis
   - Position-based inference (first section = hero)

3. **Content Item Extractor**
   - Implement content type detection
   - Extract text with context preservation
   - Link content to sections

**Medium Priority (Week 5):**
4. **Metadata Normalizer**
   - Extract all meta tags
   - Normalize across formats (OG, Twitter, Schema.org)
   - Handle missing/incomplete metadata

5. **Link Graph Builder**
   - Build page adjacency matrix
   - Calculate importance scores
   - Classify link intents

**Low Priority (Week 6):**
6. **Content Deduplication**
   - Global hash index
   - Reuse statistics
   - Content versioning

---

### 7.3 Data Quality Checklist

**Before Phase 3 (Graph Construction):**

- [ ] **Coverage:** All 10 target pages crawled successfully
- [ ] **Completeness:** 95%+ of visible content extracted
- [ ] **Accuracy:** Page types correctly classified (manual review)
- [ ] **Consistency:** All pages follow same JSON schema
- [ ] **Deduplication:** Text hashes properly consolidated
- [ ] **Next.js Data:** Extracted and merged where present
- [ ] **Metadata:** Complete for all pages
- [ ] **Links:** All internal links captured

---

## 8. Pattern Examples (To Be Populated After Crawl)

### 8.1 Common Section Patterns

```json
{
  "pattern_name": "Hero Section",
  "frequency": 10,
  "pages": ["homepage", "mba", "masters"],
  "dom_structure": {
    "tag": "section",
    "attributes": {"class": "hero hero-section"},
    "children": [
      {"tag": "h1", "text_hash": "..."},
      {"tag": "p", "text_hash": "..."},
      {"tag": "button", "text_hash": "..."}
    ]
  }
}
```

*(This section will be expanded after actual crawl)*

---

### 8.2 Content Reuse Patterns

```json
{
  "hash": "a1b2c3d4e5f6...",
  "text": "Apply Now",
  "type": "Button CTA",
  "usage_count": 47,
  "pages": ["homepage", "mba", "masters", "phd", ...],
  "sections": ["hero", "cta-block", "footer"]
}
```

*(This section will be expanded after actual parsing)*

---

## 9. Next Steps

### Phase 2 Kickoff Actions:

1. **Run Initial Crawl**
   ```bash
   cd lbs-knowledge-graph
   python scripts/crawl.py
   python scripts/parse.py
   ```

2. **Analyze Results**
   - Review `content-repo/parsed/` structure
   - Run pattern analysis scripts
   - Generate statistics report

3. **Validate Domain Models**
   - Compare actual content with schema expectations
   - Adjust `PageType` and `SectionType` enums if needed
   - Document any unexpected patterns

4. **Prepare for Phase 3**
   - Finalize graph schema based on actual data
   - Select M-Graph DB or alternative
   - Design ingestion pipeline

---

## Appendices

### A. File Paths Reference

```
lbs-knowledge-graph/
├── content-repo/
│   ├── raw/                    # HTML files + metadata
│   │   ├── homepage_abc123.html
│   │   ├── homepage_abc123.html.meta.json
│   │   └── ...
│   ├── parsed/                 # Structured JSON
│   │   ├── homepage_abc123/
│   │   │   ├── dom.json
│   │   │   ├── text.json
│   │   │   ├── metadata.json
│   │   │   ├── links.json
│   │   │   └── nextjs-data.json
│   │   └── ...
│   └── analysis/               # Pattern analysis results
│       ├── component_taxonomy.json
│       ├── reuse_statistics.json
│       └── link_graph.json
├── src/
│   ├── crawler/crawler.py
│   ├── parser/html_parser.py
│   └── validation/             # To be created in Phase 2
└── docs/
    ├── CONTENT_ANALYSIS.md     # This document
    ├── DOMAIN_MODEL_RECOMMENDATIONS.md
    ├── SITE_TAXONOMY.md
    └── PHASE_2_PREP.md
```

### B. Reference Documents

- **Schema:** `/workspaces/university-pitch/plans/04_DATA_MODEL_SCHEMA.md`
- **Implementation Plan:** `/workspaces/university-pitch/plans/01_IMPLEMENTATION_PLAN.md`
- **System Architecture:** `/workspaces/university-pitch/plans/02_SYSTEM_ARCHITECTURE.md`

---

**Document Version:** 1.0
**Status:** Pre-Crawl Analysis
**Next Update:** After Phase 1 crawl completion
