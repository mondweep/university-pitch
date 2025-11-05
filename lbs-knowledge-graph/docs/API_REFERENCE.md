# API Reference
# LBS Knowledge Graph Platform

**Version:** 2.0 (Phase 2)
**Last Updated:** November 5, 2025

---

## Overview

This document provides complete API reference for all Phase 2 components including domain extractors, graph builders, relationship extractors, and utilities.

---

## Table of Contents

1. [Domain Models](#domain-models)
2. [Graph Builder API](#graph-builder-api)
3. [Graph Loader API](#graph-loader-api)
4. [Relationship Extractors](#relationship-extractors)
5. [Parser API](#parser-api)
6. [Validation API](#validation-api)
7. [Usage Examples](#usage-examples)

---

## Domain Models

### Page

**Location:** `src/models/entities.py`

**Description:** Represents a webpage from london.edu with complete metadata and analytics.

```python
from src.models.entities import Page, PageType

class Page(BaseModel):
    # Core fields
    id: str                    # UUID v4 identifier
    url: str                   # Canonical URL (unique)
    title: str                 # Page title
    description: Optional[str] # Meta description

    # Classification
    type: PageType            # Page classification
    category: Optional[str]   # Primary category
    language: str = "en"      # ISO 639-1 language code

    # Content tracking
    hash: str                 # SHA-256 hash of raw HTML
    content_hash: str         # SHA-256 hash of extracted content
    version: int = 1          # Version number

    # Metadata
    created_at: datetime
    updated_at: datetime
    fetched_at: datetime
    published_at: Optional[datetime]

    # SEO & Social
    keywords: List[str] = []
    og_image: Optional[str]
    og_description: Optional[str]

    # Analytics
    importance: float = 0.5   # Score 0-1
    depth: int = 0           # Distance from homepage
    inbound_links: int = 0
    outbound_links: int = 0

    # Custom metadata
    metadata: Dict[str, Any] = {}
```

**Page Types:**
```python
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
```

**Example:**
```python
from datetime import datetime
from src.models.entities import Page, PageType

page = Page(
    id="550e8400-e29b-41d4-a716-446655440000",
    url="https://london.edu/programmes",
    title="Programmes - London Business School",
    type=PageType.Program,
    hash="abc123...",
    content_hash="def456...",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    fetched_at=datetime.now(),
    keywords=["MBA", "Masters", "PhD"],
    importance=0.9,
    depth=1
)
```

---

### Section

**Location:** `src/models/entities.py`

**Description:** Represents a section or component within a page.

```python
class Section(BaseModel):
    # Core fields
    id: str                    # UUID v4 identifier
    page_id: str              # Parent page ID

    # Classification
    type: SectionType         # Section type
    component: Optional[str]  # Component identifier

    # Content
    heading: Optional[str]    # Section heading
    subheading: Optional[str] # Section subheading
    order: int = 0           # Display order (0-indexed)

    # Metadata
    css_selector: Optional[str]
    attributes: Dict[str, str] = {}
    metadata: Dict[str, Any] = {}
```

**Section Types:**
```python
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
```

---

### ContentItem

**Location:** `src/models/entities.py`

**Description:** Represents an atomic piece of content with semantic enrichment.

```python
class ContentItem(BaseModel):
    # Core fields
    id: str                    # UUID v4 identifier
    hash: str                  # SHA-256 content hash

    # Content
    text: str                  # Text content
    type: ContentType         # Content type

    # Semantics (LLM-generated in Phase 6)
    sentiment: Optional[SentimentScore]
    topics: List[str] = []    # Topic IDs
    keywords: List[str] = []
    entities: List[Entity] = []

    # Audience
    audiences: List[str] = [] # Persona IDs
    reading_level: Optional[int]

    # Usage tracking
    page_ids: List[str] = []
    section_ids: List[str] = []
    usage_count: int = 0

    # Metadata
    language: str = "en"
    word_count: int = 0
    char_count: int = 0
    metadata: Dict[str, Any] = {}
```

---

## Graph Builder API

### GraphBuilder

**Location:** `src/graph/graph_builder.py`

**Description:** Builds knowledge graph using MGraph-DB from parsed content.

#### Constructor

```python
from src.graph.graph_builder import GraphBuilder

builder = GraphBuilder()
```

**Attributes:**
- `graph`: MGraph instance
- `schema`: LBSGraphSchema instance
- `batch_size`: int = 1000
- `stats`: Dict with node/edge counts

#### add_pages()

**Description:** Add Page nodes to the graph.

```python
def add_pages(self, pages: List[Dict[str, Any]]) -> None
```

**Parameters:**
- `pages`: List of page dictionaries with metadata

**Returns:** None

**Raises:**
- `ValidationError`: If page data doesn't match schema

**Example:**
```python
pages = [
    {
        'id': '550e8400-e29b-41d4-a716-446655440000',
        'url': 'https://london.edu/programmes',
        'title': 'Programmes',
        'type': 'program',
        'importance': 0.9,
        'created_at': '2025-11-05T00:00:00',
        'updated_at': '2025-11-05T00:00:00'
    }
]

builder.add_pages(pages)
print(f"Nodes created: {builder.stats['nodes_created']}")
```

#### add_sections()

**Description:** Add Section nodes to the graph.

```python
def add_sections(self, sections: List[Dict[str, Any]]) -> None
```

**Parameters:**
- `sections`: List of section dictionaries

**Example:**
```python
sections = [
    {
        'id': '660e8400-e29b-41d4-a716-446655440001',
        'page_id': '550e8400-e29b-41d4-a716-446655440000',
        'type': 'hero',
        'heading': 'Transformative Education',
        'order': 0
    }
]

builder.add_sections(sections)
```

#### add_content_items()

**Description:** Add ContentItem nodes to the graph.

```python
def add_content_items(self, items: List[Dict[str, Any]]) -> None
```

#### create_contains_edges()

**Description:** Create CONTAINS relationship edges.

```python
def create_contains_edges(self, relationships: List[Edge]) -> None
```

**Parameters:**
- `relationships`: List of Edge objects from ContainsRelationshipExtractor

**Example:**
```python
from src.relationships.contains_extractor import ContainsRelationshipExtractor

extractor = ContainsRelationshipExtractor()
edges = extractor.extract_page_sections(page_id, sections)
builder.create_contains_edges(edges)
```

#### get_statistics()

**Description:** Get current graph statistics.

```python
def get_statistics(self) -> Dict[str, Any]
```

**Returns:**
```python
{
    'nodes_created': 100,
    'edges_created': 250,
    'validation_errors': 0,
    'pages': 10,
    'sections': 50,
    'content_items': 40
}
```

#### validate_graph()

**Description:** Validate graph integrity.

```python
def validate_graph(self) -> ValidationReport
```

**Returns:** ValidationReport with issues and recommendations

---

## Graph Loader API

### GraphLoader

**Location:** `src/graph/graph_loader.py`

**Description:** Load graph from files and export to multiple formats.

#### Constructor

```python
from src.graph.graph_loader import GraphLoader

loader = GraphLoader()
```

#### load_from_directory()

**Description:** Load graph data from directory of JSON files.

```python
def load_from_directory(self, path: Path) -> MGraph
```

**Parameters:**
- `path`: Path to directory containing node and edge JSON files

**Returns:** Populated MGraph instance

**Example:**
```python
from pathlib import Path

graph = loader.load_from_directory(Path('content-repo/parsed'))
```

#### export_to_json()

**Description:** Export graph to JSON format.

```python
def export_to_json(self, path: Path, graph: MGraph) -> None
```

**Output Format:**
```json
{
  "nodes": [
    {"id": "...", "type": "Page", "data": {...}},
    {"id": "...", "type": "Section", "data": {...}}
  ],
  "edges": [
    {"source": "...", "target": "...", "type": "CONTAINS", "properties": {...}}
  ]
}
```

#### export_to_graphml()

**Description:** Export graph to GraphML format (Neo4j, Gephi compatible).

```python
def export_to_graphml(self, path: Path, graph: MGraph) -> None
```

#### export_to_cypher()

**Description:** Export graph to Cypher queries (Neo4j).

```python
def export_to_cypher(self, path: Path, graph: MGraph) -> None
```

**Output Example:**
```cypher
CREATE (p:Page {id: '...', url: '...', title: '...'})
CREATE (s:Section {id: '...', page_id: '...', type: 'hero'})
CREATE (p)-[:CONTAINS {order: 0}]->(s)
```

---

## Relationship Extractors

### ContainsRelationshipExtractor

**Location:** `src/relationships/contains_extractor.py`

**Description:** Extract hierarchical CONTAINS relationships.

#### Constructor

```python
from src.relationships.contains_extractor import ContainsRelationshipExtractor

extractor = ContainsRelationshipExtractor()
```

#### extract_page_sections()

**Description:** Extract Page → Section CONTAINS relationships.

```python
def extract_page_sections(
    self,
    page_id: str,
    sections: List[Dict[str, Any]]
) -> List[Edge]
```

**Parameters:**
- `page_id`: Parent page UUID
- `sections`: List of section dictionaries with 'id' and 'order'

**Returns:** List of CONTAINS edges

**Example:**
```python
sections = [
    {'id': 'section-1', 'order': 0, 'required': True},
    {'id': 'section-2', 'order': 1, 'required': False}
]

edges = extractor.extract_page_sections('page-123', sections)

for edge in edges:
    print(f"{edge.source_id} -> {edge.target_id} (order: {edge.properties['order']})")
```

#### extract_section_content()

**Description:** Extract Section → ContentItem CONTAINS relationships.

```python
def extract_section_content(
    self,
    section_id: str,
    items: List[Dict[str, Any]]
) -> List[Edge]
```

#### extract_nested_sections()

**Description:** Extract Section → Section (nested) CONTAINS relationships.

```python
def extract_nested_sections(
    self,
    parent_id: str,
    children: List[Dict[str, Any]]
) -> List[Edge]
```

#### validate_relationships()

**Description:** Validate extracted relationships.

```python
def validate_relationships(self) -> ValidationReport
```

**Returns:**
```python
{
    'valid': True,
    'issues': [],
    'warnings': ['Section X has no content items'],
    'stats': {
        'total_edges': 150,
        'orphans': 0,
        'cycles': 0
    }
}
```

---

## Parser API

### HTMLParser

**Location:** `src/parser/html_parser.py`

**Description:** Parse HTML to structured JSON with normalization.

```python
from src.parser.html_parser import HTMLParser

parser = HTMLParser()
result = parser.parse_html(html_content, url)
```

**parse_html():**
```python
def parse_html(self, html: str, url: str) -> Dict[str, Any]
```

**Returns:**
```python
{
    'metadata': {
        'url': '...',
        'title': '...',
        'description': '...',
        'keywords': [...]
    },
    'dom': {
        'tag': 'html',
        'children': [...]
    },
    'text_hashes': {
        'hash1': 'text content 1',
        'hash2': 'text content 2'
    },
    'links': {
        'internal': [...],
        'external': [...]
    }
}
```

---

## Validation API

### HashConsolidator

**Location:** `src/validation/hash_consolidator.py`

**Description:** Consolidate and deduplicate content hashes.

```python
from src.validation.hash_consolidator import HashConsolidator

consolidator = HashConsolidator()
consolidator.build_global_index(parsed_pages)
duplicates = consolidator.find_duplicates()
stats = consolidator.generate_usage_stats()
```

---

## Usage Examples

### Complete Graph Building Pipeline

```python
from pathlib import Path
from src.graph.graph_builder import GraphBuilder
from src.graph.graph_loader import GraphLoader
from src.relationships.contains_extractor import ContainsRelationshipExtractor
import json

# 1. Initialize builders
builder = GraphBuilder()
contains_extractor = ContainsRelationshipExtractor()

# 2. Load parsed data
parsed_dir = Path('content-repo/parsed')
pages_data = []
sections_data = []
content_data = []

for page_dir in parsed_dir.iterdir():
    if page_dir.is_dir():
        # Load metadata
        with open(page_dir / 'metadata.json') as f:
            metadata = json.load(f)
            pages_data.append(metadata)

        # Load sections (from DOM)
        with open(page_dir / 'dom.json') as f:
            dom = json.load(f)
            # Extract sections...

# 3. Add nodes
builder.add_pages(pages_data)
builder.add_sections(sections_data)
builder.add_content_items(content_data)

# 4. Extract relationships
all_edges = []
for page in pages_data:
    page_sections = [s for s in sections_data if s['page_id'] == page['id']]
    edges = contains_extractor.extract_page_sections(page['id'], page_sections)
    all_edges.extend(edges)

# 5. Create edges
builder.create_contains_edges(all_edges)

# 6. Validate
report = builder.validate_graph()
print(f"Valid: {report.valid}, Issues: {len(report.issues)}")

# 7. Export
loader = GraphLoader()
loader.export_to_json(Path('output/graph.json'), builder.graph)
loader.export_to_cypher(Path('output/graph.cypher'), builder.graph)

# 8. Statistics
stats = builder.get_statistics()
print(f"Nodes: {stats['nodes_created']}, Edges: {stats['edges_created']}")
```

### Query Examples (After Population)

```python
# Find all sections in a page
page_id = "550e8400-e29b-41d4-a716-446655440000"
sections = builder.graph.get_neighbors(page_id, edge_type='CONTAINS')

# Get page by URL
page = builder.graph.find_node(url='https://london.edu/programmes')

# Find content items in a section
section_id = "660e8400-e29b-41d4-a716-446655440001"
content = builder.graph.get_neighbors(section_id, edge_type='CONTAINS')

# Traverse page → section → content
page_node = builder.graph.get_node(page_id)
for section in builder.graph.get_neighbors(page_id, 'CONTAINS'):
    for item in builder.graph.get_neighbors(section['id'], 'CONTAINS'):
        print(f"Content: {item['text'][:50]}...")
```

---

## Error Handling

### Common Exceptions

```python
from pydantic import ValidationError

try:
    builder.add_pages(pages_data)
except ValidationError as e:
    print(f"Validation error: {e}")
    # Fix data and retry

try:
    loader.export_to_json(path, graph)
except IOError as e:
    print(f"Export failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Validation Reports

```python
report = builder.validate_graph()

if not report.valid:
    for issue in report.issues:
        print(f"ERROR: {issue.description}")
        print(f"  Location: {issue.location}")
        print(f"  Recommendation: {issue.recommendation}")

for warning in report.warnings:
    print(f"WARNING: {warning}")
```

---

## Performance Best Practices

1. **Batch Operations**: Use `batch_size` parameter for large datasets
2. **Validation**: Disable strict validation for performance-critical operations
3. **Indexing**: Create indexes before querying
4. **Memory**: Process large graphs in chunks
5. **Caching**: Cache frequently accessed nodes

```python
# Batch processing
builder.batch_size = 5000  # Larger batches for big datasets

# Disable validation temporarily
builder.schema.strict = False
builder.add_pages(large_page_list)
builder.schema.strict = True
```

---

## Type Signatures Reference

```python
# Common types
NodeID = str          # UUID v4
EdgeType = str        # CONTAINS, LINKS_TO, etc.
Timestamp = datetime
Hash = str           # SHA-256 hex

# Function signatures
def add_pages(pages: List[Dict[str, Any]]) -> None: ...
def extract_page_sections(page_id: NodeID, sections: List[Dict]) -> List[Edge]: ...
def validate_graph() -> ValidationReport: ...
def export_to_json(path: Path, graph: MGraph) -> None: ...
```

---

**API Version:** 2.0
**Phase:** 2 (Content Parsing and Domain Modeling)
**Status:** Complete (pending LINKS_TO extractor)
**Last Updated:** November 5, 2025

---

**END OF API REFERENCE**
