# MGraph-DB Integration Guide

## Overview

This document provides comprehensive guidance on integrating **MGraph-DB** (https://github.com/owasp-sbot/MGraph-DB) into the LBS Semantic Knowledge Graph platform.

**MGraph-DB** is a Python-based, in-memory graph database designed specifically for GenAI, semantic web, and serverless deployments—making it the ideal choice for this project.

---

## 1. Why MGraph-DB?

### 1.1 Key Advantages for LBS Project

✅ **Serverless-Optimized**
- Fast cold starts (<1 second)
- Minimal memory footprint
- No database server infrastructure
- Perfect for AWS Lambda deployment

✅ **Performance**
- O(1) lookups with multi-dimensional indexing
- In-memory operations for fast graph traversal
- Optimized for knowledge graph workloads

✅ **Multi-Format Export**
- JSON (native persistence)
- GraphML (visualization tools like Gephi)
- Cypher (Neo4j compatibility)
- Mermaid (documentation diagrams)
- RDF/Turtle (semantic web integration)
- DOT (Graphviz)

✅ **Type-Safe**
- Runtime type validation
- Schema enforcement
- Property-level type checking
- Prevents data corruption

✅ **Python-Native**
- Easy integration with LLM APIs (OpenAI, Claude)
- Rich Python ecosystem
- Simple deployment
- Clear, pythonic API

✅ **Lightweight**
- No external dependencies (core)
- Easy installation
- Fast setup
- Minimal configuration

---

## 2. Installation and Setup

### 2.1 Basic Installation

```bash
# Install MGraph-DB
pip install mgraph-db

# Or install from source
git clone https://github.com/owasp-sbot/MGraph-DB.git
cd MGraph-DB
poetry install
```

### 2.2 Project Integration

**requirements.txt:**
```
mgraph-db>=1.0.0
boto3>=1.28.0           # For S3 integration
pydantic>=2.0.0         # For data validation
```

**Project Structure:**
```
lbs-knowledge-graph/
├── src/
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── builder.py       # Graph construction
│   │   ├── querier.py       # Query operations
│   │   ├── schema.py        # Graph schema
│   │   └── exporters.py     # Export utilities
│   ├── models/
│   │   ├── nodes.py         # Node type definitions
│   │   └── edges.py         # Edge type definitions
│   └── utils/
│       ├── mgraph_loader.py # S3 loading utilities
│       └── validation.py    # Schema validation
```

---

## 3. Core Implementation

### 3.1 Graph Schema Definition

```python
# src/graph/schema.py

from mgraph_db import MGraph, MNode, MEdge
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class PageNode(BaseModel):
    """Page node schema"""
    id: str = Field(..., description="Unique page ID")
    url: str = Field(..., description="Page URL")
    title: str = Field(..., description="Page title")
    type: str = Field(..., description="Page type")
    importance: float = Field(default=0.5, ge=0, le=1)

class TopicNode(BaseModel):
    """Topic node schema"""
    id: str
    name: str
    category: str
    importance: float = Field(default=0.5, ge=0, le=1)

class HasTopicEdge(BaseModel):
    """HAS_TOPIC relationship schema"""
    confidence: float = Field(..., ge=0, le=1)
    source: str = Field(default="llm")  # llm, manual, rule

class LBSGraphSchema:
    """Graph schema definition"""

    NODE_TYPES = {
        'Page': PageNode,
        'Section': BaseModel,  # Define as needed
        'ContentItem': BaseModel,
        'Topic': TopicNode,
        'Category': BaseModel,
        'Persona': BaseModel
    }

    EDGE_TYPES = {
        'CONTAINS': BaseModel,
        'LINKS_TO': BaseModel,
        'HAS_TOPIC': HasTopicEdge,
        'BELONGS_TO': BaseModel,
        'TARGETS': BaseModel
    }
```

### 3.2 Graph Builder

```python
# src/graph/builder.py

from mgraph_db import MGraph
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class LBSGraphBuilder:
    """Build LBS knowledge graph using MGraph-DB"""

    def __init__(self):
        self.graph = MGraph()

    def build_from_pages(self, pages: List[Dict[str, Any]]) -> MGraph:
        """
        Build graph from parsed page data

        Args:
            pages: List of page dictionaries

        Returns:
            Populated MGraph instance
        """
        logger.info(f"Building graph from {len(pages)} pages")

        # Add Page nodes
        for page in pages:
            self._add_page_node(page)

        # Add Section and Content nodes
        for page in pages:
            self._add_page_content(page)

        # Create links between pages
        self._create_page_links(pages)

        logger.info(f"Graph built: {self.graph.node_count()} nodes, "
                   f"{self.graph.edge_count()} edges")

        return self.graph

    def _add_page_node(self, page: Dict[str, Any]) -> None:
        """Add a Page node to the graph"""
        try:
            self.graph.add_node(
                node_type='Page',
                node_id=page['id'],
                data={
                    'url': page['url'],
                    'title': page['title'],
                    'type': page.get('type', 'other'),
                    'importance': page.get('importance', 0.5),
                    'created_at': page.get('createdAt'),
                    'updated_at': page.get('updatedAt')
                }
            )
        except Exception as e:
            logger.error(f"Error adding page node {page['id']}: {e}")

    def _add_page_content(self, page: Dict[str, Any]) -> None:
        """Add sections and content items for a page"""
        page_id = page['id']

        # Add sections
        for section in page.get('sections', []):
            section_id = section['id']

            # Create Section node
            self.graph.add_node(
                node_type='Section',
                node_id=section_id,
                data={
                    'type': section['type'],
                    'heading': section.get('heading'),
                    'order': section['order']
                }
            )

            # Create CONTAINS edge from Page to Section
            self.graph.add_edge(
                from_node_id=page_id,
                to_node_id=section_id,
                edge_type='CONTAINS',
                data={'order': section['order']}
            )

            # Add content items
            for content in section.get('content_items', []):
                self._add_content_item(section_id, content)

    def _add_content_item(self, section_id: str, content: Dict[str, Any]) -> None:
        """Add a ContentItem node"""
        content_id = content['id']

        self.graph.add_node(
            node_type='ContentItem',
            node_id=content_id,
            data={
                'hash': content['hash'],
                'text': content['text'],
                'type': content['type'],
                'word_count': content.get('word_count', 0)
            }
        )

        # CONTAINS edge from Section to ContentItem
        self.graph.add_edge(
            from_node_id=section_id,
            to_node_id=content_id,
            edge_type='CONTAINS',
            data={'order': content.get('order', 0)}
        )

    def _create_page_links(self, pages: List[Dict[str, Any]]) -> None:
        """Create LINKS_TO edges between pages"""
        for page in pages:
            page_id = page['id']

            for link in page.get('links', []):
                target_id = link.get('target_id')

                if target_id and self.graph.get_node(target_id):
                    self.graph.add_edge(
                        from_node_id=page_id,
                        to_node_id=target_id,
                        edge_type='LINKS_TO',
                        data={
                            'text': link.get('text', ''),
                            'type': link.get('type', 'internal')
                        }
                    )

    def add_topics(self, topics: List[Dict[str, Any]]) -> None:
        """Add Topic nodes to the graph"""
        for topic in topics:
            self.graph.add_node(
                node_type='Topic',
                node_id=topic['id'],
                data={
                    'name': topic['name'],
                    'slug': topic['slug'],
                    'category': topic['category'],
                    'importance': topic.get('importance', 0.5)
                }
            )

    def enrich_with_topics(self, content_topics: Dict[str, List[str]]) -> None:
        """
        Add HAS_TOPIC edges from content to topics

        Args:
            content_topics: Dict mapping content_id -> [topic_ids]
        """
        for content_id, topic_data in content_topics.items():
            if not self.graph.get_node(content_id):
                continue

            for topic_info in topic_data:
                topic_id = topic_info['id']
                confidence = topic_info.get('confidence', 0.8)

                if self.graph.get_node(topic_id):
                    self.graph.add_edge(
                        from_node_id=content_id,
                        to_node_id=topic_id,
                        edge_type='HAS_TOPIC',
                        data={
                            'confidence': confidence,
                            'source': 'llm'
                        }
                    )

    def export_all_formats(self, output_dir: str = './exports') -> None:
        """Export graph to all supported formats"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        # JSON (primary format for loading)
        self.graph.save_to_json(f'{output_dir}/graph.json')

        # GraphML (for Gephi, Neo4j import)
        self.graph.export_graphml(f'{output_dir}/graph.graphml')

        # Cypher (for Neo4j)
        self.graph.export_cypher(f'{output_dir}/graph.cypher')

        # Mermaid (for documentation)
        self.graph.export_mermaid(f'{output_dir}/graph.mmd')

        # DOT (for Graphviz)
        self.graph.export_dot(f'{output_dir}/graph.dot')

        logger.info(f"Exported graph to {output_dir} in multiple formats")
```

### 3.3 Graph Querier

```python
# src/graph/querier.py

from mgraph_db import MGraph
from typing import List, Dict, Any, Optional

class LBSGraphQuerier:
    """Query operations for LBS knowledge graph"""

    def __init__(self, graph: MGraph):
        self.graph = graph

    def get_pages_by_type(self, page_type: str, limit: int = 20) -> List[Dict]:
        """Get all pages of a specific type"""
        result = self.graph.query(
            node_type='Page',
            filters={'type': page_type},
            limit=limit
        )

        return [node.data for node in result]

    def get_page_with_content(self, page_id: str) -> Dict[str, Any]:
        """
        Get a page with all its content (sections and items)

        Returns:
            {
                'page': {...},
                'sections': [...]
            }
        """
        # Get page node
        page = self.graph.get_node(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")

        # Traverse to get sections
        sections = self.graph.traverse(
            start_node_id=page_id,
            edge_type='CONTAINS',
            depth=1  # Just get direct sections
        )

        result = {
            'page': page.data,
            'sections': []
        }

        # For each section, get its content
        for section_node in sections:
            section_data = section_node.data.copy()

            # Get content items for this section
            content_items = self.graph.traverse(
                start_node_id=section_node.id,
                edge_type='CONTAINS',
                depth=1
            )

            section_data['content'] = [item.data for item in content_items]
            result['sections'].append(section_data)

        return result

    def find_by_topic(self, topic_name: str, limit: int = 50) -> List[Dict]:
        """Find all content related to a topic"""
        # Find topic node
        topic_results = self.graph.query(
            node_type='Topic',
            filters={'name': topic_name}
        )

        if not topic_results:
            return []

        topic_node = topic_results[0]

        # Traverse backwards to find content
        content_nodes = self.graph.traverse_reverse(
            start_node_id=topic_node.id,
            edge_type='HAS_TOPIC',
            depth=1
        )

        return [node.data for node in content_nodes[:limit]]

    def get_related_pages(self, page_id: str, max_depth: int = 2) -> List[Dict]:
        """
        Find pages related to the given page via links

        Args:
            page_id: Starting page ID
            max_depth: Maximum link depth (default: 2)

        Returns:
            List of related page data
        """
        # Traverse outbound links
        related = self.graph.traverse(
            start_node_id=page_id,
            edge_type='LINKS_TO',
            depth=max_depth
        )

        # Also traverse inbound links
        referrers = self.graph.traverse_reverse(
            start_node_id=page_id,
            edge_type='LINKS_TO',
            depth=1
        )

        # Combine and deduplicate
        all_related = set()
        for node in list(related) + list(referrers):
            if node.id != page_id:  # Exclude self
                all_related.add(node.id)

        return [self.graph.get_node(node_id).data
                for node_id in all_related
                if self.graph.get_node(node_id)]

    def search_content(self,
                      query: str,
                      filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Search content items by text (simple substring match)

        For production, use Elasticsearch for full-text search,
        and use this for graph-based result enhancement.
        """
        content_nodes = self.graph.query(node_type='ContentItem')

        results = []
        for node in content_nodes:
            text = node.data.get('text', '').lower()

            if query.lower() in text:
                # Apply filters if provided
                if filters:
                    matches = all(
                        node.data.get(k) == v
                        for k, v in filters.items()
                    )
                    if not matches:
                        continue

                results.append(node.data)

        return results

    def get_topic_statistics(self) -> Dict[str, Any]:
        """Get statistics about topics in the graph"""
        topic_nodes = self.graph.query(node_type='Topic')

        stats = {
            'total_topics': len(topic_nodes),
            'topics': []
        }

        for topic in topic_nodes:
            # Count content with this topic
            content_count = len(
                self.graph.traverse_reverse(
                    start_node_id=topic.id,
                    edge_type='HAS_TOPIC',
                    depth=1
                )
            )

            stats['topics'].append({
                'id': topic.id,
                'name': topic.data['name'],
                'content_count': content_count,
                'importance': topic.data.get('importance', 0.5)
            })

        # Sort by content count
        stats['topics'].sort(key=lambda x: x['content_count'], reverse=True)

        return stats

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get overall graph statistics"""
        return {
            'total_nodes': self.graph.node_count(),
            'total_edges': self.graph.edge_count(),
            'nodes_by_type': {
                'Page': len(self.graph.query(node_type='Page')),
                'Section': len(self.graph.query(node_type='Section')),
                'ContentItem': len(self.graph.query(node_type='ContentItem')),
                'Topic': len(self.graph.query(node_type='Topic')),
            },
            'avg_degree': (
                (2 * self.graph.edge_count()) / self.graph.node_count()
                if self.graph.node_count() > 0 else 0
            )
        }
```

---

## 4. AWS Lambda Integration

### 4.1 Lambda Function with MGraph

```python
# lambda/graph_query/handler.py

import json
import boto3
from mgraph_db import MGraph
from src.graph.querier import LBSGraphQuerier

# Global variable for Lambda warm starts
graph = None
querier = None

def load_graph_from_s3():
    """Load graph from S3 (cached in Lambda memory)"""
    global graph, querier

    if graph is not None:
        return querier  # Already loaded

    s3 = boto3.client('s3')

    # Download graph JSON from S3
    response = s3.get_object(
        Bucket='lbs-kg-content',
        Key='graph/latest.json'
    )

    # Load into MGraph
    graph = MGraph()
    graph.load_from_json_string(response['Body'].read().decode('utf-8'))

    querier = LBSGraphQuerier(graph)

    return querier

def lambda_handler(event, context):
    """Lambda handler for graph queries"""

    # Load graph (or use cached version)
    querier = load_graph_from_s3()

    # Parse request
    query_params = event.get('queryStringParameters', {})
    operation = query_params.get('operation', 'get_pages')

    # Execute operation
    if operation == 'get_pages':
        page_type = query_params.get('type', 'program')
        limit = int(query_params.get('limit', 20))
        results = querier.get_pages_by_type(page_type, limit)

    elif operation == 'get_page':
        page_id = query_params.get('id')
        if not page_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing page ID'})
            }
        results = querier.get_page_with_content(page_id)

    elif operation == 'find_by_topic':
        topic = query_params.get('topic')
        results = querier.find_by_topic(topic)

    elif operation == 'stats':
        results = querier.get_graph_statistics()

    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Unknown operation: {operation}'})
        }

    # Return response
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(results, default=str)
    }
```

### 4.2 Lambda Deployment

```bash
# Package Lambda function
cd lambda/graph_query
pip install -r requirements.txt -t package/
cp handler.py package/
cd package
zip -r ../deployment.zip .

# Deploy to Lambda
aws lambda update-function-code \
  --function-name lbs-kg-graph-query \
  --zip-file fileb://deployment.zip
```

---

## 5. Export and Interoperability

### 5.1 Export to Neo4j

```python
# scripts/export_to_neo4j.py

from mgraph_db import MGraph
from neo4j import GraphDatabase

def export_mgraph_to_neo4j(mgraph: MGraph, neo4j_uri: str, auth: tuple):
    """Export MGraph to Neo4j database"""

    driver = GraphDatabase.driver(neo4j_uri, auth=auth)

    with driver.session() as session:
        # Export nodes
        for node in mgraph.all_nodes():
            session.run(
                f"""
                CREATE (n:{node.node_type} $props)
                """,
                props={**node.data, 'mgraph_id': node.id}
            )

        # Export edges
        for edge in mgraph.all_edges():
            session.run(
                f"""
                MATCH (a {{mgraph_id: $from_id}})
                MATCH (b {{mgraph_id: $to_id}})
                CREATE (a)-[r:{edge.edge_type} $props]->(b)
                """,
                from_id=edge.from_node,
                to_id=edge.to_node,
                props=edge.data
            )

    driver.close()
    print("Export to Neo4j complete")

# Usage
graph = MGraph()
graph.load_from_json('graph.json')

export_mgraph_to_neo4j(
    graph,
    neo4j_uri='bolt://localhost:7687',
    auth=('neo4j', 'password')
)
```

### 5.2 Export for Visualization

```python
# scripts/export_for_viz.py

from mgraph_db import MGraph

def export_for_gephi(graph: MGraph, output_file: str):
    """Export to GraphML for Gephi visualization"""
    graph.export_graphml(output_file)
    print(f"Exported to {output_file} for Gephi")

def export_for_d3(graph: MGraph, output_file: str):
    """Export to JSON for D3.js visualization"""
    import json

    # Convert to D3-friendly format
    data = {
        'nodes': [
            {'id': node.id, 'group': node.node_type, **node.data}
            for node in graph.all_nodes()
        ],
        'links': [
            {'source': edge.from_node, 'target': edge.to_node,
             'type': edge.edge_type, **edge.data}
            for edge in graph.all_edges()
        ]
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Exported to {output_file} for D3.js")
```

---

## 6. Best Practices

### 6.1 Performance Optimization

```python
# Use indexing for fast lookups
graph.create_index('Page', 'url')  # Index by URL
graph.create_index('Topic', 'name')  # Index by topic name

# Batch operations
with graph.batch_mode():
    for page in pages:
        graph.add_node('Page', data=page)
```

### 6.2 Error Handling

```python
def safe_graph_operation(func):
    """Decorator for safe graph operations"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Graph operation failed: {e}")
            # Optionally: rollback, retry, or alert
            raise
    return wrapper

@safe_graph_operation
def add_node_safe(graph, node_type, data):
    return graph.add_node(node_type, data=data)
```

### 6.3 Validation

```python
from pydantic import ValidationError

def validate_and_add_node(graph: MGraph, node_type: str, data: Dict):
    """Validate data before adding to graph"""
    schema = LBSGraphSchema.NODE_TYPES.get(node_type)

    if not schema:
        raise ValueError(f"Unknown node type: {node_type}")

    try:
        # Validate with Pydantic
        validated_data = schema(**data)
        graph.add_node(node_type, data=validated_data.dict())
    except ValidationError as e:
        logger.error(f"Validation failed for {node_type}: {e}")
        raise
```

---

## 7. Migration Path from Other Graph DBs

### 7.1 From Neo4j to MGraph

```python
from neo4j import GraphDatabase
from mgraph_db import MGraph

def migrate_from_neo4j(neo4j_uri: str, auth: tuple) -> MGraph:
    """Migrate from Neo4j to MGraph"""

    driver = GraphDatabase.driver(neo4j_uri, auth=auth)
    graph = MGraph()

    with driver.session() as session:
        # Export nodes
        result = session.run("MATCH (n) RETURN n, labels(n) as labels")

        for record in result:
            node = record['n']
            labels = record['labels']
            node_type = labels[0] if labels else 'Unknown'

            graph.add_node(
                node_type=node_type,
                node_id=str(node.id),
                data=dict(node)
            )

        # Export relationships
        result = session.run(
            "MATCH (a)-[r]->(b) RETURN id(a) as from, type(r) as type, "
            "id(b) as to, properties(r) as props"
        )

        for record in result:
            graph.add_edge(
                from_node_id=str(record['from']),
                to_node_id=str(record['to']),
                edge_type=record['type'],
                data=record['props']
            )

    driver.close()
    return graph
```

---

## 8. Testing with MGraph

```python
# tests/test_mgraph_integration.py

import pytest
from mgraph_db import MGraph

@pytest.fixture
def sample_graph():
    """Create a sample graph for testing"""
    graph = MGraph()

    # Add test nodes
    graph.add_node('Page', node_id='p1', data={'title': 'Test Page'})
    graph.add_node('Topic', node_id='t1', data={'name': 'Test Topic'})

    # Add edge
    graph.add_edge('p1', 't1', 'HAS_TOPIC', {'confidence': 0.9})

    return graph

def test_node_creation(sample_graph):
    """Test node creation"""
    node = sample_graph.get_node('p1')
    assert node is not None
    assert node.data['title'] == 'Test Page'

def test_edge_creation(sample_graph):
    """Test edge creation"""
    edges = sample_graph.get_edges(from_node_id='p1', to_node_id='t1')
    assert len(edges) == 1
    assert edges[0].edge_type == 'HAS_TOPIC'

def test_persistence(sample_graph, tmp_path):
    """Test save and load"""
    file_path = tmp_path / "test_graph.json"

    # Save
    sample_graph.save_to_json(str(file_path))

    # Load
    new_graph = MGraph()
    new_graph.load_from_json(str(file_path))

    # Verify
    assert new_graph.node_count() == sample_graph.node_count()
    assert new_graph.get_node('p1').data['title'] == 'Test Page'
```

---

## 9. Resources

### Official Documentation
- **GitHub:** https://github.com/owasp-sbot/MGraph-DB
- **PyPI:** https://pypi.org/project/mgraph-db/

### NotebookLM Resource
- **Notebook:** https://notebooklm.google.com/notebook/176509f4-485a-4003-adf0-1d7601cbbb33

### Community
- GitHub Issues for support and feature requests
- Contributions welcome via pull requests

---

**Document Version:** 1.0
**Last Updated:** November 2025
**MGraph-DB Version:** Latest from repository
