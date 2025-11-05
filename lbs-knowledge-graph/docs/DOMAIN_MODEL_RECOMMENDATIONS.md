# Domain Model Recommendations for Phase 2

## Document Information
- **Project:** London Business School Semantic Knowledge Graph
- **Phase:** Phase 2 Preparation
- **Created:** 2025-11-05
- **Purpose:** Recommendations for domain modeling based on schema analysis and infrastructure review

---

## Executive Summary

This document provides actionable recommendations for implementing the domain model defined in `04_DATA_MODEL_SCHEMA.md`. Based on analysis of the existing crawler/parser infrastructure and anticipated london.edu content patterns, we recommend a **three-tier implementation approach**: Core Entities (Week 3), Relationships (Week 4), and Semantic Enrichment (Week 5-6).

**Key Recommendation:** Implement domain object extraction as a **pipeline of specialized classifiers** rather than monolithic parsing, enabling iterative refinement and A/B testing of classification algorithms.

---

## 1. Implementation Strategy

### 1.1 Three-Tier Approach

```
TIER 1: Core Entity Extraction (Week 3)
├── Page Entity
├── Section Entity
└── ContentItem Entity

TIER 2: Relationship Mapping (Week 4)
├── CONTAINS relationships
├── LINKS_TO relationships
└── Page categorization

TIER 3: Semantic Layer (Week 5-6)
├── Topic Entity
├── Category Entity
├── Persona Entity
└── Semantic relationships (HAS_TOPIC, TARGETS)
```

**Rationale:** This incremental approach allows validation at each tier before adding complexity.

---

### 1.2 Pipeline Architecture

```python
class DomainModelPipeline:
    """
    Orchestrates domain model extraction from parsed JSON

    Flow:
    Parsed JSON -> [Tier 1] -> [Tier 2] -> [Tier 3] -> Graph-Ready Entities
    """

    def __init__(self):
        # Tier 1: Core extractors
        self.page_extractor = PageExtractor()
        self.section_extractor = SectionExtractor()
        self.content_extractor = ContentItemExtractor()

        # Tier 2: Relationship builders
        self.containment_builder = ContainmentRelationshipBuilder()
        self.link_builder = LinkRelationshipBuilder()
        self.categorizer = PageCategorizer()

        # Tier 3: Semantic enrichment
        self.topic_tagger = TopicTagger()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.persona_classifier = PersonaClassifier()

    def process(self, parsed_page: Dict) -> GraphReadyEntities:
        """Execute full pipeline"""
        # Tier 1
        page = self.page_extractor.extract(parsed_page)
        sections = self.section_extractor.extract(parsed_page, page.id)
        content_items = self.content_extractor.extract(parsed_page, sections)

        # Tier 2
        containment_rels = self.containment_builder.build(page, sections, content_items)
        link_rels = self.link_builder.build(parsed_page['links'], page.id)
        page.category = self.categorizer.categorize(page, parsed_page)

        # Tier 3 (optional, can be deferred)
        for item in content_items:
            item.topics = self.topic_tagger.tag(item.text)
            item.sentiment = self.sentiment_analyzer.analyze(item.text)
            item.audiences = self.persona_classifier.classify(item.text, page.type)

        return GraphReadyEntities(
            pages=[page],
            sections=sections,
            content_items=content_items,
            relationships=containment_rels + link_rels
        )
```

---

## 2. Tier 1: Core Entity Extraction

### 2.1 Page Entity Extractor

**Implementation Specification:**

```python
from typing import Optional
import uuid
from datetime import datetime
import hashlib

class PageExtractor:
    """Extracts Page entities from parsed JSON"""

    def extract(self, parsed: Dict) -> Page:
        """
        Creates Page entity from parsed data

        Args:
            parsed: Output from HTMLParser.parse_html()
                {
                  'url': str,
                  'metadata': {...},
                  'dom': {...},
                  'links': [...],
                  'text_hashes': {...},
                  'nextjs_data': {...}
                }

        Returns:
            Page entity instance
        """
        metadata = parsed['metadata']
        url = parsed['url']

        # Generate stable UUID from URL
        page_id = self._generate_uuid_from_url(url)

        # Calculate content hash
        content_hash = self._calculate_content_hash(parsed['text_hashes'])

        # Calculate HTML hash (for change detection)
        html_hash = hashlib.sha256(
            str(parsed['dom']).encode()
        ).hexdigest()

        # Infer page type
        page_type = self._infer_page_type(url, metadata, parsed)

        # Extract category from URL or metadata
        category = self._extract_category(url, metadata)

        page = Page(
            id=page_id,
            url=self._normalize_url(url),
            title=metadata.get('title', ''),
            description=metadata.get('description'),
            type=page_type,
            category=category,
            language=metadata.get('language', 'en'),
            hash=html_hash,
            contentHash=content_hash,
            version=1,  # Initial version
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
            fetchedAt=datetime.now(),
            publishedAt=self._extract_publish_date(metadata, parsed),
            keywords=self._extract_keywords(metadata),
            ogImage=metadata.get('og_image'),
            ogDescription=metadata.get('og_description'),
            importance=0.5,  # Default, calculated later
            depth=self._calculate_depth(url),
            inboundLinks=0,  # Populated during link analysis
            outboundLinks=len(parsed['links']),
            metadata=self._extract_custom_metadata(parsed)
        )

        return page

    def _infer_page_type(self, url: str, metadata: Dict, parsed: Dict) -> PageType:
        """
        Multi-signal page type classification

        Priority:
        1. URL pattern matching (highest confidence)
        2. Schema.org markup in metadata
        3. Breadcrumb analysis
        4. Content analysis (title, headings)
        """
        # URL patterns
        if '/programmes/' in url or '/programs/' in url:
            return PageType.Program
        if '/faculty-and-research/faculty/' in url or '/faculty/' in url:
            return PageType.Faculty
        if '/news/' in url or '/insights/' in url:
            return PageType.News
        if '/events/' in url:
            return PageType.Event
        if '/admissions/' in url:
            return PageType.Admissions
        if '/student-life/' in url:
            return PageType.StudentLife
        if '/alumni/' in url:
            return PageType.Alumni
        if '/about/' in url:
            return PageType.About
        if '/contact' in url:
            return PageType.Contact
        if url.endswith('/') and url.count('/') == 3:  # https://domain/
            return PageType.Homepage

        # Schema.org analysis
        if 'schema' in metadata:
            schema_type = metadata['schema'].get('@type')
            if schema_type == 'Course':
                return PageType.Program
            if schema_type == 'Person':
                return PageType.Faculty
            if schema_type == 'NewsArticle':
                return PageType.News
            if schema_type == 'Event':
                return PageType.Event

        # Fallback
        return PageType.Other

    def _calculate_depth(self, url: str) -> int:
        """Calculate distance from homepage (number of / after domain)"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        return len(path_parts)

    def _extract_category(self, url: str, metadata: Dict) -> Optional[str]:
        """Extract primary category from URL structure"""
        from urllib.parse import urlparse
        path_parts = [p for p in urlparse(url).path.split('/') if p]

        if len(path_parts) >= 1:
            return path_parts[0]  # First path segment

        return None

    def _generate_uuid_from_url(self, url: str) -> str:
        """Generate deterministic UUID v5 from URL"""
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # URL namespace
        return str(uuid.uuid5(namespace, url))

    # Additional helper methods...
```

**Testing Checklist:**
- [ ] Correctly identifies all 11 PageType values
- [ ] Generates consistent UUIDs for same URL
- [ ] Handles missing metadata gracefully
- [ ] Calculates depth accurately
- [ ] Extracts keywords from meta tags

---

### 2.2 Section Entity Extractor

**Implementation Specification:**

```python
class SectionExtractor:
    """Extracts Section entities from DOM structure"""

    def extract(self, parsed: Dict, page_id: str) -> List[Section]:
        """
        Creates Section entities from DOM

        Strategy:
        1. Identify major sections in DOM
        2. Classify section type
        3. Extract heading and metadata
        4. Preserve order information
        """
        dom = parsed['dom']
        sections = []

        # Find major container elements
        section_candidates = self._find_section_elements(dom)

        for order, element in enumerate(section_candidates):
            section = Section(
                id=str(uuid.uuid4()),
                pageId=page_id,
                type=self._infer_section_type(element, order),
                component=self._extract_component_name(element),
                heading=self._extract_heading(element),
                subheading=self._extract_subheading(element),
                order=order,
                cssSelector=self._generate_selector(element),
                attributes=self._extract_attributes(element),
                metadata={}
            )
            sections.append(section)

        return sections

    def _find_section_elements(self, dom: Dict) -> List[Dict]:
        """
        Identifies major sections in DOM

        Heuristics:
        - Direct children of <body> or <main>
        - Elements with 'section', 'article', 'aside' tags
        - Divs with specific classes (hero, content, sidebar)
        - Navigation elements
        - Header and footer
        """
        candidates = []

        def traverse(node: Dict, depth: int = 0):
            # Only look at top-level containers
            if depth > 3:
                return

            tag = node.get('tag', '')

            # Section-like tags
            if tag in ['section', 'article', 'aside', 'nav', 'header', 'footer', 'main']:
                candidates.append(node)

            # Divs with semantic classes
            elif tag == 'div':
                attrs = node.get('attributes', {})
                class_attr = attrs.get('class', '')

                semantic_classes = ['hero', 'content', 'sidebar', 'banner', 'wrapper']
                if any(cls in class_attr.lower() for cls in semantic_classes):
                    candidates.append(node)

            # Recurse to children (only if not already a candidate)
            if node not in candidates:
                for child in node.get('children', []):
                    traverse(child, depth + 1)

        traverse(dom)

        return candidates

    def _infer_section_type(self, element: Dict, order: int) -> SectionType:
        """
        Classify section type

        Signals:
        1. HTML tag name
        2. CSS classes
        3. Position (first section likely hero)
        4. Child element patterns
        5. Text content patterns
        """
        tag = element.get('tag', '')
        attrs = element.get('attributes', {})
        class_attr = attrs.get('class', '').lower()

        # Tag-based classification
        if tag == 'nav':
            return SectionType.Navigation
        if tag == 'header':
            return SectionType.Header
        if tag == 'footer':
            return SectionType.Footer

        # Class-based classification
        if 'hero' in class_attr or 'banner' in class_attr:
            return SectionType.Hero
        if 'sidebar' in class_attr or 'aside' in class_attr:
            return SectionType.Sidebar
        if 'cta' in class_attr or 'callout' in class_attr:
            return SectionType.Callout
        if 'gallery' in class_attr or 'carousel' in class_attr:
            return SectionType.Gallery
        if 'testimonial' in class_attr or 'quote' in class_attr:
            return SectionType.Testimonial
        if 'stat' in class_attr or 'metric' in class_attr or 'number' in class_attr:
            return SectionType.Stats
        if 'profile' in class_attr or 'bio' in class_attr:
            return SectionType.Profile
        if 'form' in class_attr:
            return SectionType.Form

        # List detection (multiple similar children)
        children = element.get('children', [])
        if len(children) >= 3:
            # Check if children have similar structure (likely a listing)
            if self._are_similar_children(children):
                return SectionType.Listing

        # Position-based (first non-nav section is often hero)
        if order == 0 or (order == 1 and tag != 'nav'):
            return SectionType.Hero

        # Default
        return SectionType.Content

    def _extract_heading(self, element: Dict) -> Optional[str]:
        """Extract primary heading from section"""
        def find_heading(node: Dict) -> Optional[str]:
            # Look for h1, h2, h3 in direct children
            for child in node.get('children', []):
                if child.get('tag') in ['h1', 'h2', 'h3']:
                    text_hash = child.get('text_hash')
                    if text_hash:
                        return text_hash  # Return hash, resolve later
                # Recurse one level
                heading = find_heading(child)
                if heading:
                    return heading
            return None

        return find_heading(element)

    # Additional helper methods...
```

**Testing Checklist:**
- [ ] Identifies 8+ section types correctly
- [ ] Preserves section order
- [ ] Extracts headings accurately
- [ ] Handles nested sections
- [ ] Generates valid CSS selectors

---

### 2.3 ContentItem Entity Extractor

**Implementation Specification:**

```python
class ContentItemExtractor:
    """Extracts ContentItem entities from sections"""

    def extract(self, parsed: Dict, sections: List[Section]) -> List[ContentItem]:
        """
        Creates ContentItem entities from parsed text hashes

        Strategy:
        1. Use text_hashes from parsed JSON
        2. Map hashes to sections via DOM traversal
        3. Classify content type
        4. Preserve context (parent section, page)
        """
        text_hashes = parsed['text_hashes']
        content_items = []

        # Create ContentItem for each unique hash
        for text_hash, text in text_hashes.items():
            # Find which sections use this hash
            section_ids = self._find_sections_using_hash(
                text_hash, sections, parsed['dom']
            )

            item = ContentItem(
                id=str(uuid.uuid4()),
                hash=text_hash,
                text=text,
                type=self._infer_content_type(text, text_hash, parsed['dom']),
                sentiment=None,  # Populated in Tier 3
                topics=[],        # Populated in Tier 3
                keywords=[],      # Populated in Tier 3
                entities=[],      # Populated in Tier 3
                audiences=[],     # Populated in Tier 3
                readingLevel=None,
                pageIds=[],       # Populated during relationship building
                sectionIds=section_ids,
                usageCount=len(section_ids),
                language=parsed['metadata'].get('language', 'en'),
                wordCount=len(text.split()),
                charCount=len(text),
                metadata={}
            )

            content_items.append(item)

        return content_items

    def _infer_content_type(self, text: str, text_hash: str, dom: Dict) -> ContentType:
        """
        Classify content type

        Signals:
        1. Associated HTML tag (from DOM)
        2. Text length and structure
        3. Text patterns (bullets, numbers)
        4. Parent context
        """
        # Find element with this text_hash in DOM
        element = self._find_element_by_hash(dom, text_hash)

        if element:
            tag = element.get('tag', '')

            # Tag-based mapping
            tag_map = {
                'h1': ContentType.Heading,
                'h2': ContentType.Subheading,
                'h3': ContentType.Subheading,
                'h4': ContentType.Subheading,
                'p': ContentType.Paragraph,
                'li': ContentType.ListItem,
                'blockquote': ContentType.Quote,
                'pre': ContentType.Code,
                'code': ContentType.Code,
                'button': ContentType.Button,
                'a': ContentType.Link
            }

            if tag in tag_map:
                return tag_map[tag]

        # Text-based analysis
        if len(text) < 50:
            # Short text
            if text.isupper():
                return ContentType.Heading
            if not text.endswith(('.', '!', '?')):
                return ContentType.Heading

        # List patterns
        if text.strip().startswith(('•', '-', '*', '▪')):
            return ContentType.ListItem
        if len(text) > 0 and text[0].isdigit() and text[1:3] in ['. ', ') ']:
            return ContentType.ListItem

        # Paragraph by default
        return ContentType.Paragraph

    def _find_sections_using_hash(
        self, text_hash: str, sections: List[Section], dom: Dict
    ) -> List[str]:
        """
        Find which sections contain this text hash

        Returns list of section IDs
        """
        section_ids = []

        for section in sections:
            # Check if hash appears in section's DOM subtree
            if self._hash_in_subtree(text_hash, section, dom):
                section_ids.append(section.id)

        return section_ids

    # Additional helper methods...
```

**Testing Checklist:**
- [ ] Creates items for all unique text hashes
- [ ] Correctly identifies 12+ content types
- [ ] Maps items to sections accurately
- [ ] Calculates word/char counts
- [ ] Handles empty or malformed text

---

## 3. Tier 2: Relationship Mapping

### 3.1 Relationship Builders

**CONTAINS Relationships:**

```python
class ContainmentRelationshipBuilder:
    """Builds hierarchical CONTAINS relationships"""

    def build(
        self, page: Page, sections: List[Section], content_items: List[ContentItem]
    ) -> List[ContainsRelationship]:
        """
        Creates CONTAINS edges:
        - Page -> Section (ordered)
        - Section -> ContentItem (ordered)
        """
        relationships = []

        # Page -> Section
        for section in sections:
            relationships.append(ContainsRelationship(
                source_id=page.id,
                source_type='Page',
                target_id=section.id,
                target_type='Section',
                order=section.order,
                required=section.type in [SectionType.Header, SectionType.Navigation],
                conditional=None
            ))

        # Section -> ContentItem
        for item in content_items:
            for i, section_id in enumerate(item.sectionIds):
                relationships.append(ContainsRelationship(
                    source_id=section_id,
                    source_type='Section',
                    target_id=item.id,
                    target_type='ContentItem',
                    order=i,  # Order within section
                    required=False,
                    conditional=None
                ))

        return relationships
```

**LINKS_TO Relationships:**

```python
class LinkRelationshipBuilder:
    """Builds LINKS_TO relationships between pages"""

    def build(self, links: List[Dict], source_page_id: str) -> List[LinksToRelationship]:
        """
        Creates LINKS_TO edges from link data

        Args:
            links: Output from HTMLParser.extract_links()
            source_page_id: ID of source page
        """
        relationships = []

        for position, link in enumerate(links):
            # Only process internal links
            if link['type'] != 'internal':
                continue

            # Generate target page ID from URL
            target_url = self._resolve_url(link['href'])
            target_page_id = self._generate_uuid_from_url(target_url)

            # Classify link type
            link_type = self._classify_link_type(link, position)

            relationships.append(LinksToRelationship(
                source_id=source_page_id,
                target_id=target_page_id,
                text=link['text'],
                type=link_type,
                position=position,
                context=None  # Could extract surrounding text
            ))

        return relationships

    def _classify_link_type(self, link: Dict, position: int) -> LinkType:
        """Classify link intent"""
        text_lower = link['text'].lower()

        # Navigation links (common patterns)
        nav_keywords = ['home', 'about', 'programmes', 'admissions', 'contact']
        if any(kw in text_lower for kw in nav_keywords):
            return LinkType.Navigation

        # CTA links
        cta_keywords = ['apply', 'register', 'download', 'learn more']
        if any(kw in text_lower for kw in cta_keywords):
            return LinkType.Reference  # Or create new CTA type

        # Related content (usually later on page)
        if position > 10 and ('related' in text_lower or 'read more' in text_lower):
            return LinkType.Related

        return LinkType.Internal
```

---

## 4. Tier 3: Semantic Enrichment

### 4.1 LLM Integration Strategy

**Recommendation:** Use **batch processing** to minimize API calls and costs.

```python
class SemanticEnricher:
    """Coordinates LLM-based semantic enrichment"""

    def __init__(self, llm_client):
        self.llm = llm_client

    def enrich_batch(self, content_items: List[ContentItem]) -> List[ContentItem]:
        """
        Batch process content items for semantic enrichment

        Processes:
        1. Topic extraction (all items)
        2. Sentiment analysis (paragraphs only)
        3. Entity extraction (paragraphs, quotes)
        4. Audience classification (page-level)
        """
        # Batch by type for efficiency
        paragraphs = [item for item in content_items if item.type == ContentType.Paragraph]
        headings = [item for item in content_items if item.type == ContentType.Heading]

        # Process paragraphs (highest value)
        enriched_paragraphs = self._enrich_paragraphs(paragraphs)

        # Process headings (topic extraction only)
        enriched_headings = self._enrich_headings(headings)

        # Merge results
        results = {**enriched_paragraphs, **enriched_headings}

        # Update content items
        for item in content_items:
            if item.id in results:
                item.topics = results[item.id]['topics']
                item.sentiment = results[item.id].get('sentiment')
                item.entities = results[item.id].get('entities', [])
                item.keywords = results[item.id].get('keywords', [])

        return content_items

    def _enrich_paragraphs(self, paragraphs: List[ContentItem]) -> Dict:
        """Use LLM to analyze paragraphs"""
        # Prepare batch prompt
        batch_texts = [p.text for p in paragraphs]

        prompt = f"""
        Analyze the following text excerpts from a business school website.
        For each excerpt, provide:
        1. Topics (max 3): Main subjects discussed
        2. Sentiment: positive/neutral/negative with confidence
        3. Keywords (max 5): Important terms
        4. Entities: Named entities (people, programs, locations)

        Excerpts:
        {json.dumps(batch_texts, indent=2)}

        Respond with JSON array matching input order.
        """

        response = self.llm.complete(prompt)
        # Parse and return
        ...
```

**Cost Optimization:**
- Process only Paragraphs, Headings, and Quotes (skip buttons, links)
- Batch up to 50 items per API call
- Cache results by content hash
- Defer sentiment analysis to post-MVP phase

---

## 5. Implementation Recommendations

### 5.1 Week 3: Core Entity Extraction

**Day 1-2: Page Extractor**
- [ ] Implement `PageExtractor` class
- [ ] Test on 10 crawled pages
- [ ] Validate PageType classification (manual review)
- [ ] Refine URL patterns if needed

**Day 3-4: Section Extractor**
- [ ] Implement `SectionExtractor` class
- [ ] Test section detection on diverse pages
- [ ] Validate SectionType classification
- [ ] Adjust heuristics based on results

**Day 5: ContentItem Extractor**
- [ ] Implement `ContentItemExtractor` class
- [ ] Test content type detection
- [ ] Validate hash-to-section mapping
- [ ] Review edge cases (empty sections, nested content)

---

### 5.2 Week 4: Relationship Mapping

**Day 1-2: Containment Relationships**
- [ ] Implement `ContainmentRelationshipBuilder`
- [ ] Generate Page->Section edges
- [ ] Generate Section->ContentItem edges
- [ ] Validate relationship completeness

**Day 3-4: Link Relationships**
- [ ] Implement `LinkRelationshipBuilder`
- [ ] Generate LINKS_TO edges
- [ ] Calculate inbound link counts
- [ ] Build page importance scores (PageRank)

**Day 5: Categorization**
- [ ] Implement `PageCategorizer`
- [ ] Extract categories from URL structure
- [ ] Create Category entities
- [ ] Validate category taxonomy

---

### 5.3 Week 5-6: Semantic Enrichment (Optional MVP)

**Defer to Post-MVP if time-constrained:**
- Topic tagging
- Sentiment analysis
- Persona classification
- Entity extraction

**Minimal Viable Approach:**
- Use rule-based topic extraction (keyword matching)
- Skip sentiment analysis initially
- Use page type as proxy for audience targeting
- Defer entity extraction

---

## 6. Data Quality Assurance

### 6.1 Validation Pipeline

```python
class DomainModelValidator:
    """Validates extracted entities and relationships"""

    def validate_page(self, page: Page) -> ValidationReport:
        """Validate Page entity"""
        issues = []

        # Required fields
        if not page.title:
            issues.append("Missing title")
        if not page.url:
            issues.append("Missing URL")
        if page.type == PageType.Other:
            issues.append(f"Page type not classified: {page.url}")

        # Hash validation
        if len(page.hash) != 64:
            issues.append(f"Invalid hash length: {len(page.hash)}")

        # Depth validation
        if page.depth < 0 or page.depth > 10:
            issues.append(f"Unusual depth: {page.depth}")

        return ValidationReport(entity_type='Page', entity_id=page.id, issues=issues)

    def validate_section(self, section: Section, page: Page) -> ValidationReport:
        """Validate Section entity"""
        issues = []

        # Required fields
        if not section.pageId:
            issues.append("Missing pageId")
        if section.type == SectionType.Other:
            issues.append("Section type not classified")

        # Order validation
        if section.order < 0:
            issues.append(f"Invalid order: {section.order}")

        return ValidationReport(entity_type='Section', entity_id=section.id, issues=issues)

    def validate_content_item(self, item: ContentItem) -> ValidationReport:
        """Validate ContentItem entity"""
        issues = []

        # Required fields
        if not item.text:
            issues.append("Missing text")
        if not item.hash:
            issues.append("Missing hash")
        if item.type == ContentType.Other:
            issues.append("Content type not classified")

        # Usage validation
        if item.usageCount == 0:
            issues.append("Usage count is 0")
        if len(item.sectionIds) != item.usageCount:
            issues.append("Section IDs don't match usage count")

        return ValidationReport(entity_type='ContentItem', entity_id=item.id, issues=issues)

    def validate_all(self, entities: GraphReadyEntities) -> ValidationSummary:
        """Run all validations"""
        reports = []

        for page in entities.pages:
            reports.append(self.validate_page(page))

        for section in entities.sections:
            page = entities.get_page_by_id(section.pageId)
            reports.append(self.validate_section(section, page))

        for item in entities.content_items:
            reports.append(self.validate_content_item(item))

        return ValidationSummary(reports)
```

---

## 7. Performance Considerations

### 7.1 Optimization Strategies

**Parallel Processing:**
```python
from concurrent.futures import ProcessPoolExecutor

def process_pages_parallel(parsed_pages: List[Dict]) -> List[GraphReadyEntities]:
    """Process pages in parallel"""
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = executor.map(pipeline.process, parsed_pages)
    return list(results)
```

**Caching:**
```python
from functools import lru_cache

class PageExtractor:
    @lru_cache(maxsize=1000)
    def _infer_page_type(self, url: str, metadata_str: str, parsed_str: str) -> PageType:
        """Cache page type inference results"""
        # Convert to hashable types for caching
        ...
```

**Incremental Processing:**
```python
def process_incremental(new_pages: List[Dict], existing_db: Database):
    """Only process new or changed pages"""
    for page_data in new_pages:
        url = page_data['url']
        content_hash = calculate_hash(page_data['text_hashes'])

        # Check if page exists and unchanged
        existing = existing_db.get_page_by_url(url)
        if existing and existing.contentHash == content_hash:
            continue  # Skip unchanged page

        # Process changed/new page
        entities = pipeline.process(page_data)
        existing_db.update(entities)
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# test_page_extractor.py
def test_page_type_classification():
    extractor = PageExtractor()

    # Test Programme page
    parsed = load_fixture('mba_page.json')
    page = extractor.extract(parsed)
    assert page.type == PageType.Program

    # Test Faculty page
    parsed = load_fixture('faculty_profile.json')
    page = extractor.extract(parsed)
    assert page.type == PageType.Faculty

    # Test Homepage
    parsed = load_fixture('homepage.json')
    page = extractor.extract(parsed)
    assert page.type == PageType.Homepage

def test_uuid_generation():
    extractor = PageExtractor()

    # Same URL should generate same UUID
    uuid1 = extractor._generate_uuid_from_url('https://london.edu/programmes/mba')
    uuid2 = extractor._generate_uuid_from_url('https://london.edu/programmes/mba')
    assert uuid1 == uuid2

    # Different URLs should generate different UUIDs
    uuid3 = extractor._generate_uuid_from_url('https://london.edu/programmes/masters')
    assert uuid1 != uuid3
```

### 8.2 Integration Tests

```python
def test_full_pipeline():
    """Test complete pipeline on real crawled page"""
    # Load real parsed page
    parsed = load_real_page('homepage_abc123')

    # Run pipeline
    pipeline = DomainModelPipeline()
    entities = pipeline.process(parsed)

    # Validate results
    assert len(entities.pages) == 1
    assert len(entities.sections) > 0
    assert len(entities.content_items) > 0
    assert len(entities.relationships) > 0

    # Check relationships
    page = entities.pages[0]
    page_sections = [r for r in entities.relationships
                     if r.source_id == page.id and r.target_type == 'Section']
    assert len(page_sections) == len(entities.sections)
```

---

## 9. Next Steps

### Phase 2 Kickoff Checklist:

**Week 3: Core Entities**
- [ ] Implement `PageExtractor`
- [ ] Implement `SectionExtractor`
- [ ] Implement `ContentItemExtractor`
- [ ] Write unit tests for each extractor
- [ ] Run on 10 crawled pages
- [ ] Manual validation of results
- [ ] Refine classifiers based on results

**Week 4: Relationships**
- [ ] Implement `ContainmentRelationshipBuilder`
- [ ] Implement `LinkRelationshipBuilder`
- [ ] Implement `PageCategorizer`
- [ ] Write integration tests
- [ ] Generate relationship statistics
- [ ] Validate relationship completeness

**Week 5: Validation & Refinement**
- [ ] Implement `DomainModelValidator`
- [ ] Run validation on all entities
- [ ] Fix classification errors
- [ ] Optimize performance
- [ ] Generate quality report
- [ ] Prepare for Phase 3 (Graph Construction)

---

## Appendices

### A. Code Structure

```
src/
├── models/
│   ├── entities.py          # Entity dataclasses (Page, Section, etc.)
│   ├── relationships.py     # Relationship dataclasses
│   └── enums.py            # PageType, SectionType, ContentType enums
├── extractors/
│   ├── page_extractor.py
│   ├── section_extractor.py
│   └── content_extractor.py
├── builders/
│   ├── containment_builder.py
│   ├── link_builder.py
│   └── categorizer.py
├── enrichment/
│   ├── topic_tagger.py
│   ├── sentiment_analyzer.py
│   └── persona_classifier.py
├── validation/
│   └── validator.py
└── pipeline.py              # DomainModelPipeline orchestrator
```

### B. Reference Documents

- **Schema:** `/workspaces/university-pitch/plans/04_DATA_MODEL_SCHEMA.md`
- **Content Analysis:** `./CONTENT_ANALYSIS.md`
- **Implementation Plan:** `/workspaces/university-pitch/plans/01_IMPLEMENTATION_PLAN.md`

---

**Document Version:** 1.0
**Status:** Phase 2 Preparation
**Next Update:** After Week 3 implementation
