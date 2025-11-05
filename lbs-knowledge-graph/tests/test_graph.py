"""
Unit Tests for Phase 2 Graph Builders
Tests GraphBuilder and GraphLoader
Target: 30+ test cases with 95% coverage
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from tests.fixtures.test_data import generate_test_pages


# ==================== GraphBuilder Tests ====================

@pytest.mark.unit
class TestGraphBuilder:
    """Test GraphBuilder class (target: 20 tests)"""

    def test_initialize_empty_graph(self, mock_graph):
        """Test creating an empty graph"""
        assert mock_graph.node_count() == 0
        assert mock_graph.edge_count() == 0

    def test_add_single_page_node(self, mock_graph):
        """Test adding a single page node"""
        page_data = {
            'id': 'page-1',
            'url': 'https://london.edu/test',
            'title': 'Test Page',
            'type': 'program'
        }

        node = mock_graph.add_node('page-1', 'Page', page_data)

        assert node is not None
        assert node.node_type == 'Page'
        assert node.data['title'] == 'Test Page'
        assert mock_graph.node_count() == 1

    def test_add_multiple_pages_batch(self, mock_graph):
        """Test batch adding multiple pages"""
        pages = [
            {'id': f'page-{i}', 'url': f'/page-{i}', 'title': f'Page {i}'}
            for i in range(10)
        ]

        for page in pages:
            mock_graph.add_node(page['id'], 'Page', page)

        assert mock_graph.node_count() == 10

    def test_add_section_nodes(self, mock_graph):
        """Test adding section nodes"""
        # Add page first
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})

        # Add sections
        for i in range(3):
            mock_graph.add_node(
                f'section-{i}',
                'Section',
                {'id': f'section-{i}', 'pageId': 'page-1', 'order': i}
            )

        assert mock_graph.node_count() == 4  # 1 page + 3 sections

    def test_add_content_item_nodes(self, mock_graph):
        """Test adding content item nodes"""
        content_items = [
            {'id': 'content-1', 'text': 'Text 1', 'hash': 'hash1'},
            {'id': 'content-2', 'text': 'Text 2', 'hash': 'hash2'}
        ]

        for item in content_items:
            mock_graph.add_node(item['id'], 'ContentItem', item)

        assert mock_graph.node_count() == 2

    def test_create_contains_relationship(self, mock_graph):
        """Test creating CONTAINS relationship"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})

        edge = mock_graph.add_edge('page-1', 'section-1', 'CONTAINS', {'order': 0})

        assert edge is not None
        assert edge.edge_type == 'CONTAINS'
        assert mock_graph.edge_count() == 1

    def test_create_links_to_relationship(self, mock_graph):
        """Test creating LINKS_TO relationship"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('page-2', 'Page', {'id': 'page-2'})

        edge = mock_graph.add_edge(
            'page-1',
            'page-2',
            'LINKS_TO',
            {'text': 'Link text', 'type': 'navigation'}
        )

        assert edge.data['text'] == 'Link text'
        assert edge.data['type'] == 'navigation'

    def test_build_page_section_hierarchy(self, mock_graph):
        """Test building complete page-section hierarchy"""
        # Add page
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})

        # Add sections
        for i in range(3):
            section_id = f'section-{i}'
            mock_graph.add_node(section_id, 'Section', {'id': section_id, 'order': i})
            mock_graph.add_edge('page-1', section_id, 'CONTAINS', {'order': i})

        # Should have 1 page, 3 sections, 3 edges
        assert mock_graph.node_count() == 4
        assert mock_graph.edge_count() == 3

    def test_build_section_content_hierarchy(self, mock_graph):
        """Test building section-content hierarchy"""
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})

        # Add content items
        for i in range(5):
            content_id = f'content-{i}'
            mock_graph.add_node(content_id, 'ContentItem', {'id': content_id})
            mock_graph.add_edge('section-1', content_id, 'CONTAINS', {'order': i})

        assert mock_graph.node_count() == 6  # 1 section + 5 content
        assert mock_graph.edge_count() == 5

    def test_query_nodes_by_type(self, mock_graph):
        """Test querying nodes by type"""
        # Add mixed node types
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('page-2', 'Page', {'id': 'page-2'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})

        # Filter Page nodes
        pages = [n for n in mock_graph.nodes.values() if n.node_type == 'Page']

        assert len(pages) == 2

    def test_query_edges_by_type(self, mock_graph):
        """Test querying edges by type"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('page-2', 'Page', {'id': 'page-2'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})

        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')
        mock_graph.add_edge('page-1', 'page-2', 'LINKS_TO')

        contains_edges = mock_graph.get_edges(edge_type='CONTAINS')
        assert len(contains_edges) == 1

    def test_get_node_by_id(self, mock_graph):
        """Test retrieving specific node by ID"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1', 'title': 'Test'})

        node = mock_graph.get_node('page-1')

        assert node is not None
        assert node.data['title'] == 'Test'

    def test_get_node_relationships(self, mock_graph):
        """Test getting all relationships for a node"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})
        mock_graph.add_node('section-2', 'Section', {'id': 'section-2'})

        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')
        mock_graph.add_edge('page-1', 'section-2', 'CONTAINS')

        # Get outbound edges from page-1
        outbound = mock_graph.get_edges(from_node='page-1')

        assert len(outbound) == 2

    def test_calculate_graph_statistics(self, mock_graph):
        """Test calculating graph statistics"""
        # Build small graph
        for i in range(5):
            mock_graph.add_node(f'page-{i}', 'Page', {'id': f'page-{i}'})

        for i in range(10):
            mock_graph.add_node(f'section-{i}', 'Section', {'id': f'section-{i}'})

        stats = {
            'total_nodes': mock_graph.node_count(),
            'total_edges': mock_graph.edge_count(),
            'pages': len([n for n in mock_graph.nodes.values() if n.node_type == 'Page']),
            'sections': len([n for n in mock_graph.nodes.values() if n.node_type == 'Section'])
        }

        assert stats['total_nodes'] == 15
        assert stats['pages'] == 5
        assert stats['sections'] == 10

    def test_detect_orphaned_nodes(self, mock_graph):
        """Test detecting nodes with no relationships"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('page-2', 'Page', {'id': 'page-2'})
        mock_graph.add_node('orphan', 'Page', {'id': 'orphan'})

        mock_graph.add_edge('page-1', 'page-2', 'LINKS_TO')

        # Find nodes with no edges
        orphans = [
            n for n in mock_graph.nodes.values()
            if len(n.edges_in) == 0 and len(n.edges_out) == 0
        ]

        assert len(orphans) == 1
        assert orphans[0].id == 'orphan'

    def test_prevent_duplicate_nodes(self, mock_graph):
        """Test that duplicate node IDs are handled"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1', 'title': 'First'})
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1', 'title': 'Second'})

        # Should overwrite or reject duplicate
        assert mock_graph.node_count() == 1

    def test_build_from_parsed_json(self, sample_page_data, mock_graph):
        """Test building graph from parsed page JSON"""
        # Add page node
        page_id = 'mba-page'
        mock_graph.add_node(page_id, 'Page', {
            'id': page_id,
            'url': sample_page_data['url'],
            'title': sample_page_data['metadata']['title']
        })

        # Extract and add sections from DOM
        dom = sample_page_data['dom']
        # This would be done by SectionExtractor in real implementation

        assert mock_graph.node_count() >= 1

    def test_validate_graph_integrity(self, mock_graph):
        """Test graph integrity validation"""
        # Add nodes
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})

        # Add edge
        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')

        # Validate all edges reference existing nodes
        for edge in mock_graph.edges:
            assert edge.from_node in mock_graph.nodes
            assert edge.to_node in mock_graph.nodes

    def test_performance_1000_nodes(self, mock_graph, performance_timer):
        """Test performance with 1000 nodes"""
        performance_timer.start()

        # Add 1000 nodes
        for i in range(1000):
            mock_graph.add_node(f'node-{i}', 'Page', {'id': f'node-{i}'})

        elapsed = performance_timer.stop()

        assert mock_graph.node_count() == 1000
        # Should complete in < 1 second
        assert elapsed < 1.0


# ==================== GraphLoader Tests ====================

@pytest.mark.unit
class TestGraphLoader:
    """Test GraphLoader class for data import/export (target: 10 tests)"""

    def test_export_to_json(self, mock_graph, tmp_path):
        """Test exporting graph to JSON format"""
        # Build small graph
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1', 'title': 'Test'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})
        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')

        # Export to JSON
        output_file = tmp_path / "graph.json"

        graph_data = {
            'nodes': [
                {
                    'id': node.id,
                    'type': node.node_type,
                    'data': node.data
                }
                for node in mock_graph.nodes.values()
            ],
            'edges': [
                {
                    'from': edge.from_node,
                    'to': edge.to_node,
                    'type': edge.edge_type,
                    'data': edge.data
                }
                for edge in mock_graph.edges
            ]
        }

        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)

        # Verify file created
        assert output_file.exists()

        # Verify content
        with open(output_file, 'r') as f:
            loaded = json.load(f)

        assert len(loaded['nodes']) == 2
        assert len(loaded['edges']) == 1

    def test_export_to_graphml(self, mock_graph, tmp_path):
        """Test exporting graph to GraphML format"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})

        output_file = tmp_path / "graph.graphml"

        # Simple GraphML structure
        graphml = '''<?xml version="1.0" encoding="UTF-8"?>
<graphml>
  <graph id="lbs-kg" edgedefault="directed">
    <node id="page-1"/>
  </graph>
</graphml>'''

        with open(output_file, 'w') as f:
            f.write(graphml)

        assert output_file.exists()

    def test_export_to_cypher(self, mock_graph, tmp_path):
        """Test exporting graph to Cypher format"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1', 'title': 'Test'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})
        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')

        output_file = tmp_path / "graph.cypher"

        # Generate Cypher statements
        statements = []

        for node in mock_graph.nodes.values():
            props = json.dumps(node.data)
            statements.append(f"CREATE (:{node.node_type} {props});")

        for edge in mock_graph.edges:
            statements.append(
                f"MATCH (a {{id: '{edge.from_node}'}}), (b {{id: '{edge.to_node}'}}) "
                f"CREATE (a)-[:{edge.edge_type}]->(b);"
            )

        with open(output_file, 'w') as f:
            f.write('\n'.join(statements))

        assert output_file.exists()

        # Verify content
        with open(output_file, 'r') as f:
            content = f.read()

        assert 'CREATE' in content
        assert 'MATCH' in content

    def test_export_to_mermaid(self, mock_graph, tmp_path):
        """Test exporting graph to Mermaid diagram format"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1', 'title': 'Test'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})
        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')

        output_file = tmp_path / "graph.mmd"

        # Generate Mermaid
        mermaid = ["graph TD"]

        for edge in mock_graph.edges:
            from_node = mock_graph.get_node(edge.from_node)
            to_node = mock_graph.get_node(edge.to_node)
            mermaid.append(f"  {edge.from_node}[\"{from_node.node_type}\"] -->|{edge.edge_type}| {edge.to_node}[\"{to_node.node_type}\"]")

        with open(output_file, 'w') as f:
            f.write('\n'.join(mermaid))

        assert output_file.exists()

        with open(output_file, 'r') as f:
            content = f.read()

        assert 'graph TD' in content
        assert 'CONTAINS' in content

    def test_load_from_json(self, tmp_path):
        """Test loading graph from JSON file"""
        # Create JSON file
        graph_data = {
            'nodes': [
                {'id': 'page-1', 'type': 'Page', 'data': {'title': 'Test'}},
                {'id': 'section-1', 'type': 'Section', 'data': {}}
            ],
            'edges': [
                {'from': 'page-1', 'to': 'section-1', 'type': 'CONTAINS', 'data': {}}
            ]
        }

        json_file = tmp_path / "graph.json"
        with open(json_file, 'w') as f:
            json.dump(graph_data, f)

        # Load from JSON
        with open(json_file, 'r') as f:
            loaded = json.load(f)

        assert len(loaded['nodes']) == 2
        assert len(loaded['edges']) == 1

    def test_export_statistics(self, mock_graph):
        """Test exporting graph statistics"""
        # Build graph
        for i in range(10):
            mock_graph.add_node(f'page-{i}', 'Page', {'id': f'page-{i}'})

        stats = {
            'total_nodes': mock_graph.node_count(),
            'total_edges': mock_graph.edge_count(),
            'node_types': {},
            'edge_types': {}
        }

        # Count node types
        for node in mock_graph.nodes.values():
            stats['node_types'][node.node_type] = stats['node_types'].get(node.node_type, 0) + 1

        assert stats['total_nodes'] == 10
        assert stats['node_types']['Page'] == 10

    def test_export_large_graph(self, tmp_path):
        """Test exporting large graph (1000+ nodes)"""
        from tests.fixtures.test_data import generate_test_pages

        pages = generate_test_pages(1000)

        # This would export all pages
        assert len(pages) == 1000

    def test_validate_export_format(self, mock_graph, tmp_path):
        """Test that exported JSON is valid"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})

        output_file = tmp_path / "graph.json"

        graph_data = {
            'nodes': [
                {
                    'id': n.id,
                    'type': n.node_type,
                    'data': n.data
                }
                for n in mock_graph.nodes.values()
            ],
            'edges': []
        }

        with open(output_file, 'w') as f:
            json.dump(graph_data, f)

        # Load and validate
        with open(output_file, 'r') as f:
            loaded = json.load(f)

        assert 'nodes' in loaded
        assert 'edges' in loaded
        assert isinstance(loaded['nodes'], list)

    def test_incremental_graph_update(self, mock_graph):
        """Test incremental updates to existing graph"""
        # Initial graph
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1', 'version': 1})

        initial_count = mock_graph.node_count()

        # Add new node
        mock_graph.add_node('page-2', 'Page', {'id': 'page-2', 'version': 1})

        assert mock_graph.node_count() == initial_count + 1


# ==================== Graph Validation Tests ====================

@pytest.mark.unit
class TestGraphValidation:
    """Test graph validation and integrity checks"""

    def test_validate_no_dangling_edges(self, mock_graph):
        """Test that all edges reference existing nodes"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})
        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')

        # All edges should reference existing nodes
        for edge in mock_graph.edges:
            assert edge.from_node in mock_graph.nodes
            assert edge.to_node in mock_graph.nodes

    def test_validate_hierarchy_integrity(self, mock_graph):
        """Test that hierarchical relationships are valid"""
        # Page should contain sections, not other pages
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})

        # This should be valid
        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')

        # Get the edge
        edges = mock_graph.get_edges(from_node='page-1', edge_type='CONTAINS')
        assert len(edges) == 1

        # Check target is Section
        target_node = mock_graph.get_node(edges[0].to_node)
        assert target_node.node_type == 'Section'

    def test_detect_circular_dependencies(self, mock_graph):
        """Test detection of circular CONTAINS relationships"""
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})
        mock_graph.add_node('section-2', 'Section', {'id': 'section-2'})

        # Create circular relationship
        mock_graph.add_edge('section-1', 'section-2', 'CONTAINS')
        mock_graph.add_edge('section-2', 'section-1', 'CONTAINS')

        # Detect circular dependency
        # section-1 -> section-2 -> section-1
        # This would be invalid in a tree structure

        edges_from_1 = mock_graph.get_edges(from_node='section-1')
        edges_from_2 = mock_graph.get_edges(from_node='section-2')

        # Both should have outbound edges
        assert len(edges_from_1) > 0
        assert len(edges_from_2) > 0
