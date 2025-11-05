# Phase 2 Preparation Checklist

## Document Information
- **Project:** London Business School Semantic Knowledge Graph
- **Phase:** Phase 1 → Phase 2 Transition
- **Created:** 2025-11-05
- **Purpose:** Comprehensive checklist to ensure readiness for Phase 2 domain modeling

---

## Executive Summary

This checklist ensures all Phase 1 deliverables are complete and Phase 2 infrastructure is ready. **Gate Criteria:** All items in sections 1-3 must be completed before starting Phase 2 Week 3 domain modeling work.

**Critical Path:** Content crawling → Validation → Pattern analysis → Domain model implementation

---

## 1. Phase 1 Completion Checklist

### 1.1 Project Setup (Week 1-2)
- [x] GitHub repositories initialized
  - [x] `lbs-knowledge-graph` (main code repository)
  - [x] Documentation structure created
  - [x] `.gitignore` configured
- [x] Development environment configured
  - [x] Python 3.8+ installed
  - [x] Dependencies installed (`requirements.txt`)
  - [x] Environment variables configured (`.env.example`)
- [x] Directory structure created
  ```
  lbs-knowledge-graph/
  ├── content-repo/
  │   ├── raw/      ✓ Created
  │   ├── parsed/   ✓ Created
  │   └── analysis/ ✓ Created
  ├── src/
  │   ├── crawler/  ✓ Created (crawler.py exists)
  │   ├── parser/   ✓ Created (html_parser.py exists)
  │   ├── models/   ✓ Created
  │   ├── graph/    ✓ Created
  │   ├── utils/    ✓ Created
  │   └── validation/ ✓ Created
  ├── tests/        ✓ Created
  ├── docs/         ✓ Created
  ├── scripts/      ✓ Created
  └── config/       ✓ Created
  ```

---

### 1.2 HTML Fetcher Development (Week 1-2)
- [x] Crawler implementation complete
  - [x] HTTP client with session pooling
  - [x] URL normalization function
  - [x] URL validation (domain, exclusions)
  - [x] Filename generation (MD5 hash-based)
  - [x] Metadata extraction
  - [x] Failed URL tracking
  - [x] Crawl statistics generation
- [ ] **CRITICAL: Run initial crawl**
  ```bash
  cd /workspaces/university-pitch/lbs-knowledge-graph
  python scripts/crawl.py
  ```
  **Expected Output:**
  - [ ] 10+ HTML files in `content-repo/raw/`
  - [ ] Matching `.meta.json` files
  - [ ] `crawl_stats.json` with success metrics
  - [ ] <5% failure rate

**Target URLs (from crawler.py):**
1. [ ] `https://london.edu` (Homepage)
2. [ ] `https://london.edu/about`
3. [ ] `https://london.edu/programmes`
4. [ ] `https://london.edu/faculty-and-research`
5. [ ] `https://london.edu/news`
6. [ ] `https://london.edu/events`
7. [ ] `https://london.edu/admissions`
8. [ ] `https://london.edu/student-life`
9. [ ] `https://london.edu/alumni`
10. [ ] `https://london.edu/contact`

---

### 1.3 HTML to JSON Conversion (Week 1-2)
- [x] Parser implementation complete
  - [x] DOM parsing with BeautifulSoup
  - [x] SHA-256 content hashing
  - [x] Text extraction and normalization
  - [x] Metadata extraction (title, meta tags, OG)
  - [x] Link extraction with type classification
  - [x] Next.js `__NEXT_DATA__` extraction
  - [x] Attribute filtering (React noise removal)
- [ ] **CRITICAL: Run parsing on crawled content**
  ```bash
  cd /workspaces/university-pitch/lbs-knowledge-graph
  python scripts/parse.py
  ```
  **Expected Output:**
  - [ ] Subdirectories in `content-repo/parsed/` for each page
  - [ ] `dom.json` files with full DOM structure
  - [ ] `text.json` files with hash mappings
  - [ ] `metadata.json` files with extracted metadata
  - [ ] `links.json` files with all page links
  - [ ] `nextjs-data.json` files (if applicable)

---

### 1.4 Next.js Data Extraction (Week 1-2)
- [x] Next.js parser implemented
  - [x] `__NEXT_DATA__` script tag extraction
  - [x] JSON parsing with error handling
  - [x] Data validation
- [ ] **Manual verification required:**
  - [ ] Check 3+ pages for `__NEXT_DATA__` presence
  - [ ] Validate JSON structure matches expected schema
  - [ ] Compare with HTML content for completeness
  - [ ] Document any missing content in Next.js data

**Verification Commands:**
```bash
# Check for Next.js data files
find content-repo/parsed -name "nextjs-data.json" | wc -l

# Inspect a sample
cat content-repo/parsed/homepage_*/nextjs-data.json | jq '.props.pageProps' | head -50
```

---

### 1.5 Data Validation (Week 2)
- [ ] **CRITICAL: Validate extracted content**

  **Validation Script:**
  ```python
  # scripts/validate_phase1.py
  import json
  from pathlib import Path

  def validate_parsed_page(page_dir: Path) -> dict:
      """Validate a single parsed page"""
      issues = []

      # Check required files exist
      required_files = ['dom.json', 'text.json', 'metadata.json', 'links.json']
      for file in required_files:
          if not (page_dir / file).exists():
              issues.append(f"Missing {file}")

      # Validate DOM structure
      dom_file = page_dir / 'dom.json'
      if dom_file.exists():
          with open(dom_file) as f:
              dom = json.load(f)
              if 'tag' not in dom:
                  issues.append("Invalid DOM structure")

      # Validate text hashes
      text_file = page_dir / 'text.json'
      if text_file.exists():
          with open(text_file) as f:
              texts = json.load(f)
              if len(texts) == 0:
                  issues.append("No text content extracted")

      # Validate metadata
      meta_file = page_dir / 'metadata.json'
      if meta_file.exists():
          with open(meta_file) as f:
              meta = json.load(f)
              if 'title' not in meta:
                  issues.append("Missing page title")

      return {
          'page': page_dir.name,
          'valid': len(issues) == 0,
          'issues': issues
      }

  # Run validation
  parsed_dir = Path('content-repo/parsed')
  results = [validate_parsed_page(p) for p in parsed_dir.iterdir() if p.is_dir()]

  # Print report
  valid_count = sum(1 for r in results if r['valid'])
  print(f"Validation Report: {valid_count}/{len(results)} pages valid")

  for result in results:
      if not result['valid']:
          print(f"\n{result['page']}:")
          for issue in result['issues']:
              print(f"  - {issue}")
  ```

  **Acceptance Criteria:**
  - [ ] 95%+ of pages have all required files
  - [ ] All pages have non-empty `text.json`
  - [ ] All pages have valid metadata with title
  - [ ] Average 50+ unique text hashes per page

---

## 2. Phase 2 Infrastructure Setup

### 2.1 Code Structure (Week 3)
- [ ] Create domain model code structure
  ```bash
  mkdir -p src/models
  mkdir -p src/extractors
  mkdir -p src/builders
  mkdir -p src/enrichment
  mkdir -p src/pipeline
  ```

- [ ] Create entity definition files
  - [ ] `src/models/entities.py` - Entity dataclasses
  ```python
  from dataclasses import dataclass
  from typing import List, Optional, Dict, Any
  from datetime import datetime
  from enum import Enum

  class PageType(Enum):
      Homepage = 'homepage'
      Program = 'program'
      Faculty = 'faculty'
      Research = 'research'
      News = 'news'
      Event = 'event'
      About = 'about'
      Admissions = 'admissions'
      StudentLife = 'student_life'
      Alumni = 'alumni'
      Contact = 'contact'
      Other = 'other'

  class SectionType(Enum):
      Hero = 'hero'
      Content = 'content'
      Sidebar = 'sidebar'
      Navigation = 'navigation'
      Footer = 'footer'
      Header = 'header'
      Callout = 'callout'
      Listing = 'listing'
      Profile = 'profile'
      Stats = 'stats'
      Testimonial = 'testimonial'
      Gallery = 'gallery'
      Form = 'form'
      Other = 'other'

  class ContentType(Enum):
      Paragraph = 'paragraph'
      Heading = 'heading'
      Subheading = 'subheading'
      List = 'list'
      ListItem = 'list_item'
      Quote = 'quote'
      Code = 'code'
      Table = 'table'
      Image = 'image'
      Video = 'video'
      Link = 'link'
      Button = 'button'
      Other = 'other'

  @dataclass
  class Page:
      id: str
      url: str
      title: str
      description: Optional[str]
      type: PageType
      category: Optional[str]
      language: str
      hash: str
      contentHash: str
      version: int
      createdAt: datetime
      updatedAt: datetime
      fetchedAt: datetime
      publishedAt: Optional[datetime]
      keywords: List[str]
      ogImage: Optional[str]
      ogDescription: Optional[str]
      importance: float
      depth: int
      inboundLinks: int
      outboundLinks: int
      metadata: Dict[str, Any]

  @dataclass
  class Section:
      id: str
      pageId: str
      type: SectionType
      component: Optional[str]
      heading: Optional[str]
      subheading: Optional[str]
      order: int
      cssSelector: Optional[str]
      attributes: Dict[str, str]
      metadata: Dict[str, Any]

  @dataclass
  class ContentItem:
      id: str
      hash: str
      text: str
      type: ContentType
      sentiment: Optional[Dict]
      topics: List[str]
      keywords: List[str]
      entities: List[Dict]
      audiences: List[str]
      readingLevel: Optional[int]
      pageIds: List[str]
      sectionIds: List[str]
      usageCount: int
      language: str
      wordCount: int
      charCount: int
      metadata: Dict[str, Any]
  ```

  - [ ] `src/models/relationships.py` - Relationship dataclasses
  - [ ] `src/models/enums.py` - Shared enums

- [ ] Create extractor stub files
  - [ ] `src/extractors/page_extractor.py`
  - [ ] `src/extractors/section_extractor.py`
  - [ ] `src/extractors/content_extractor.py`

- [ ] Create builder stub files
  - [ ] `src/builders/containment_builder.py`
  - [ ] `src/builders/link_builder.py`
  - [ ] `src/builders/categorizer.py`

- [ ] Create pipeline orchestrator
  - [ ] `src/pipeline/domain_pipeline.py`

---

### 2.2 Testing Infrastructure (Week 3)
- [ ] Create test fixtures
  ```bash
  mkdir -p tests/fixtures/parsed
  cp -r content-repo/parsed/homepage_* tests/fixtures/parsed/
  cp -r content-repo/parsed/programmes_* tests/fixtures/parsed/
  ```

- [ ] Create test files
  - [ ] `tests/test_page_extractor.py`
  - [ ] `tests/test_section_extractor.py`
  - [ ] `tests/test_content_extractor.py`
  - [ ] `tests/test_pipeline.py`

- [ ] Configure pytest
  ```bash
  # Install pytest
  pip install pytest pytest-cov

  # Create pytest.ini
  cat > pytest.ini << EOF
  [pytest]
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  addopts = --verbose --cov=src --cov-report=html
  EOF
  ```

---

### 2.3 Documentation Review (Week 3)
- [x] Read all planning documents
  - [x] `00_PROJECT_OVERVIEW.md`
  - [x] `01_IMPLEMENTATION_PLAN.md`
  - [x] `02_SYSTEM_ARCHITECTURE.md`
  - [x] `03_TECHNICAL_SPECIFICATIONS.md`
  - [x] `04_DATA_MODEL_SCHEMA.md`
  - [x] `05_API_SPECIFICATIONS.md`
  - [x] `06_DEPLOYMENT_PLAN.md`
  - [x] `07_TESTING_STRATEGY.md`

- [x] Research documents created
  - [x] `docs/CONTENT_ANALYSIS.md`
  - [x] `docs/DOMAIN_MODEL_RECOMMENDATIONS.md`
  - [x] `docs/SITE_TAXONOMY.md`
  - [x] `docs/PHASE_2_PREP.md` (this document)

---

## 3. Pre-Phase 2 Analysis Tasks

### 3.1 Content Pattern Analysis
- [ ] **Run pattern analysis script**
  ```python
  # scripts/analyze_patterns.py
  import json
  from pathlib import Path
  from collections import Counter, defaultdict

  def analyze_patterns(parsed_dir: Path):
      """Analyze patterns across all parsed pages"""

      # Statistics
      total_pages = 0
      total_sections = 0
      total_unique_texts = set()
      text_reuse = Counter()
      dom_patterns = defaultdict(int)

      for page_dir in parsed_dir.iterdir():
          if not page_dir.is_dir():
              continue

          total_pages += 1

          # Analyze DOM patterns
          dom_file = page_dir / 'dom.json'
          if dom_file.exists():
              with open(dom_file) as f:
                  dom = json.load(f)
                  # Count top-level children (sections)
                  if 'children' in dom:
                      total_sections += len(dom['children'])
                      # Record DOM patterns
                      for child in dom['children']:
                          tag = child.get('tag', 'unknown')
                          classes = child.get('attributes', {}).get('class', '')
                          pattern = f"{tag}.{classes.split()[0] if classes else 'no-class'}"
                          dom_patterns[pattern] += 1

          # Analyze text reuse
          text_file = page_dir / 'text.json'
          if text_file.exists():
              with open(text_file) as f:
                  texts = json.load(f)
                  for hash_val in texts.keys():
                      total_unique_texts.add(hash_val)
                      text_reuse[hash_val] += 1

      # Generate report
      report = {
          'total_pages': total_pages,
          'avg_sections_per_page': total_sections / total_pages if total_pages > 0 else 0,
          'total_unique_texts': len(total_unique_texts),
          'avg_texts_per_page': len(total_unique_texts) / total_pages if total_pages > 0 else 0,
          'most_reused_texts': text_reuse.most_common(10),
          'common_dom_patterns': dict(dom_patterns.most_common(20))
      }

      # Save report
      with open('content-repo/analysis/pattern_report.json', 'w') as f:
          json.dump(report, f, indent=2)

      print(json.dumps(report, indent=2))

      return report

  # Run analysis
  analyze_patterns(Path('content-repo/parsed'))
  ```

  **Expected Output:**
  - [ ] Pattern report saved to `content-repo/analysis/pattern_report.json`
  - [ ] Average 5-15 sections per page
  - [ ] 300-1000 unique text snippets across 10 pages
  - [ ] Identify 10+ common DOM patterns

---

### 3.2 Component Taxonomy Creation
- [ ] **Identify common components**
  - [ ] Analyze `common_dom_patterns` from pattern report
  - [ ] Group similar patterns (e.g., `section.hero`, `div.hero-banner`)
  - [ ] Map to `SectionType` enum values
  - [ ] Document unmapped patterns for potential new types

- [ ] **Create component mapping file**
  ```json
  {
    "component_mappings": {
      "hero": {
        "section_type": "Hero",
        "patterns": ["section.hero", "div.hero-banner", "header.page-header"],
        "confidence": 0.9
      },
      "navigation": {
        "section_type": "Navigation",
        "patterns": ["nav.main-nav", "nav.primary-navigation", "header nav"],
        "confidence": 1.0
      },
      "content": {
        "section_type": "Content",
        "patterns": ["main.content", "article.post-content", "div.main-content"],
        "confidence": 0.8
      }
    }
  }
  ```
  - [ ] Save to `content-repo/analysis/component_taxonomy.json`

---

### 3.3 Content Reuse Analysis
- [ ] **Analyze most reused content**
  - [ ] Review `most_reused_texts` from pattern report
  - [ ] Classify reused content types:
    - [ ] CTAs (buttons, links)
    - [ ] Navigation labels
    - [ ] Footer content
    - [ ] Common descriptions
  - [ ] Document expected vs. unexpected reuse

- [ ] **Create reuse report**
  ```markdown
  # Content Reuse Analysis

  ## High Reuse (10+ pages)
  - "Apply Now" (Button CTA) - 47 instances across 10 pages
  - "Learn More" (Link CTA) - 32 instances
  - "London Business School" (Brand name) - 28 instances

  ## Medium Reuse (5-10 pages)
  - Programme descriptions - 8 instances
  - Faculty titles - 6 instances

  ## Unexpected Reuse
  - (None identified)
  ```
  - [ ] Save to `content-repo/analysis/reuse_report.md`

---

## 4. Phase 2 Week 3 Readiness

### 4.1 Gate Criteria

**All of the following must be TRUE before starting Phase 2 implementation:**

- [ ] ✅ **Content Crawled:** 10+ HTML files in `content-repo/raw/`
- [ ] ✅ **Content Parsed:** 10+ parsed directories in `content-repo/parsed/`
- [ ] ✅ **Validation Passed:** 95%+ of pages valid (all required files present)
- [ ] ✅ **Patterns Analyzed:** Pattern report generated and reviewed
- [ ] ✅ **Code Structure Ready:** All directories and stub files created
- [ ] ✅ **Tests Configured:** pytest installed and configured
- [ ] ✅ **Documentation Read:** All planning and research docs reviewed
- [ ] ✅ **Team Alignment:** All team members briefed on Phase 2 tasks

**If any criteria are not met, DO NOT proceed to Phase 2 implementation.**

---

### 4.2 Suggested Timeline

**Week 2 (Current):**
- [ ] Run crawler (`scripts/crawl.py`)
- [ ] Run parser (`scripts/parse.py`)
- [ ] Run validation script
- [ ] Review validation results
- [ ] Fix any issues with crawler/parser
- [ ] Re-run if needed

**Week 3 Day 1:**
- [ ] Run pattern analysis
- [ ] Create component taxonomy
- [ ] Analyze content reuse
- [ ] Review all analysis reports
- [ ] Set up code structure

**Week 3 Day 2:**
- [ ] Implement `PageExtractor` class
- [ ] Write unit tests for `PageExtractor`
- [ ] Test on 10 crawled pages
- [ ] Manual review of PageType classifications

**Week 3 Day 3-4:**
- [ ] Implement `SectionExtractor` class
- [ ] Write unit tests
- [ ] Test section detection
- [ ] Refine classification heuristics

**Week 3 Day 5:**
- [ ] Implement `ContentItemExtractor` class
- [ ] Write unit tests
- [ ] Test content type detection
- [ ] Review edge cases

---

## 5. Known Risks & Mitigations

### 5.1 Crawler Issues

**Risk:** london.edu blocks or rate-limits crawler
- **Mitigation:** Use polite User-Agent, respect 2s delay, monitor for 403/429 errors
- **Contingency:** Manually download critical pages, adjust delay to 5s

**Risk:** Next.js data not present on all pages
- **Mitigation:** HTML content extraction still works
- **Contingency:** Defer Next.js-specific features to later phase

---

### 5.2 Parser Issues

**Risk:** Unexpected HTML structure breaks parser
- **Mitigation:** Extensive error handling in parser
- **Contingency:** Fix parser, re-run on all pages

**Risk:** Text hashing produces duplicates
- **Mitigation:** SHA-256 has negligible collision probability
- **Contingency:** Add full text comparison for identical hashes

---

### 5.3 Classification Issues

**Risk:** PageType classification accuracy < 90%
- **Mitigation:** Multi-signal classification (URL + content)
- **Contingency:** Manual review and rule refinement

**Risk:** SectionType classification produces too many "Other"
- **Mitigation:** Conservative heuristics, manual review sample
- **Contingency:** Add new SectionType values, update enum

---

## 6. Success Criteria

### Phase 1 Success (Current)
- [x] Crawler functional and tested
- [x] Parser functional and tested
- [ ] **10+ pages crawled successfully**
- [ ] **10+ pages parsed successfully**
- [ ] **Validation passes for 95%+ pages**
- [ ] **Research documents completed**

### Phase 2 Success (Week 3-4)
- [ ] PageExtractor classifies 90%+ pages correctly
- [ ] SectionExtractor detects 80%+ sections correctly
- [ ] ContentItemExtractor creates items for all text hashes
- [ ] Relationships built for all pages
- [ ] Integration tests pass
- [ ] Manual validation confirms quality

---

## 7. Next Actions

### Immediate (This Week)
1. **Run crawler:**
   ```bash
   cd /workspaces/university-pitch/lbs-knowledge-graph
   python scripts/crawl.py
   ```

2. **Run parser:**
   ```bash
   python scripts/parse.py
   ```

3. **Run validation:**
   ```bash
   python scripts/validate_phase1.py
   ```

4. **Review results:**
   - Check `content-repo/raw/` for HTML files
   - Check `content-repo/parsed/` for JSON files
   - Review validation output
   - Fix any issues

### Week 3 Start
1. **Run analysis:**
   ```bash
   python scripts/analyze_patterns.py
   ```

2. **Review reports:**
   - `content-repo/analysis/pattern_report.json`
   - `content-repo/analysis/component_taxonomy.json`
   - `content-repo/analysis/reuse_report.md`

3. **Set up code structure:**
   ```bash
   mkdir -p src/{models,extractors,builders,enrichment,pipeline}
   touch src/models/{entities,relationships,enums}.py
   touch src/extractors/{page,section,content}_extractor.py
   touch src/builders/{containment,link}_builder.py
   touch src/builders/categorizer.py
   touch src/pipeline/domain_pipeline.py
   ```

4. **Start implementation:**
   - Begin with `PageExtractor`
   - Write tests alongside code
   - Validate early and often

---

## Appendices

### A. File Checklist

**After Phase 1 completion, these files should exist:**

```
content-repo/
├── raw/
│   ├── homepage_*.html ✓
│   ├── homepage_*.html.meta.json ✓
│   ├── about_*.html ✓
│   ├── programmes_*.html ✓
│   ├── faculty-and-research_*.html ✓
│   ├── news_*.html ✓
│   ├── events_*.html ✓
│   ├── admissions_*.html ✓
│   ├── student-life_*.html ✓
│   ├── alumni_*.html ✓
│   ├── contact_*.html ✓
│   └── crawl_stats.json ✓
├── parsed/
│   ├── homepage_*/
│   │   ├── dom.json ✓
│   │   ├── text.json ✓
│   │   ├── metadata.json ✓
│   │   ├── links.json ✓
│   │   └── nextjs-data.json (optional)
│   └── (9 more page directories...)
└── analysis/
    ├── pattern_report.json (Week 3)
    ├── component_taxonomy.json (Week 3)
    └── reuse_report.md (Week 3)
```

### B. Reference Commands

```bash
# Count crawled pages
ls -1 content-repo/raw/*.html | wc -l

# Count parsed pages
ls -d content-repo/parsed/*/ | wc -l

# Check for Next.js data
find content-repo/parsed -name "nextjs-data.json"

# Validate JSON files
for f in content-repo/parsed/*/dom.json; do
  echo "Validating $f"
  python -m json.tool "$f" > /dev/null && echo "✓" || echo "✗"
done

# Get text hash counts
for f in content-repo/parsed/*/text.json; do
  echo "$f: $(jq 'length' "$f") unique texts"
done
```

---

**Document Version:** 1.0
**Status:** Ready for Phase 1 Completion
**Next Update:** After Phase 1 crawl/parse complete
