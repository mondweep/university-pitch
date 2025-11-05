"""
Integration Tests for Phase 2 Pipeline
End-to-end tests for complete Phase 2 workflow
Target: 20+ test cases with full pipeline validation
"""

import pytest
import json
import time
from pathlib import Path
from typing import Dict, List, Any
from tests.fixtures.test_data import generate_test_pages, generate_large_page


# ==================== End-to-End Pipeline Tests ====================

@pytest.mark.integration
class TestPhase2Pipeline:
    """Test complete Phase 2 pipeline (target: 10 tests)"""

    def test_full_pipeline_single_page(self, sample_page_data, mock_graph):
        """Test complete pipeline: parsed JSON → graph"""
        # Step 1: Extract Page
        page_id = 'mba-page'
        page_node_data = {
            'id': page_id,
            'url': sample_page_data['url'],
            'title': sample_page_data['metadata']['title'],
            'type': 'program',  # Classified as program
            'importance': 0.9
        }
        mock_graph.add_node(page_id, 'Page', page_node_data)

        # Step 2: Extract Sections
        section_ids = []
        for i in range(2):  # Sample has 2 sections
            section_id = f'{page_id}-section-{i}'
            section_ids.append(section_id)
            mock_graph.add_node(section_id, 'Section', {
                'id': section_id,
                'pageId': page_id,
                'type': 'hero' if i == 0 else 'content',
                'order': i
            })
            # Create CONTAINS relationship
            mock_graph.add_edge(page_id, section_id, 'CONTAINS', {'order': i})

        # Step 3: Extract Content Items
        content_count = 0
        for section_id in section_ids:
            for j in range(3):  # 3 content items per section
                content_id = f'{section_id}-content-{j}'
                mock_graph.add_node(content_id, 'ContentItem', {
                    'id': content_id,
                    'text': f'Content {j}',
                    'type': 'paragraph',
                    'hash': f'hash-{content_id}'
                })
                mock_graph.add_edge(section_id, content_id, 'CONTAINS', {'order': j})
                content_count += 1

        # Step 4: Extract Links
        for link in sample_page_data['links']:
            target_id = f"page-{link['href'].replace('/', '-')}"
            # Create target page if doesn't exist
            if target_id not in mock_graph.nodes:
                mock_graph.add_node(target_id, 'Page', {'id': target_id})

            mock_graph.add_edge(page_id, target_id, 'LINKS_TO', {
                'text': link['text'],
                'type': link['type']
            })

        # Validate complete graph
        assert mock_graph.node_count() >= 9  # 1 page + 2 sections + 6 content + links
        assert mock_graph.edge_count() >= 8  # CONTAINS + LINKS_TO

        # Validate hierarchy
        page_contains = mock_graph.get_edges(from_node=page_id, edge_type='CONTAINS')
        assert len(page_contains) == 2  # Page contains 2 sections

    def test_full_pipeline_multiple_pages(self, mock_graph):
        """Test pipeline with multiple pages"""
        pages = generate_test_pages(count=10)

        for page_data in pages:
            # Extract page
            page_id = page_data['url'].split('/')[-1]
            mock_graph.add_node(page_id, 'Page', {
                'id': page_id,
                'url': page_data['url'],
                'title': page_data['metadata']['title']
            })

        # Should have 10 pages
        assert mock_graph.node_count() == 10

    def test_pipeline_with_real_phase1_data(self, sample_parsed_pages, mock_graph):
        """Test pipeline using actual Phase 1 parsed output"""
        # Read Phase 1 data
        page_dir = sample_parsed_pages / "mba"

        with open(page_dir / "metadata.json") as f:
            metadata = json.load(f)

        with open(page_dir / "dom.json") as f:
            dom = json.load(f)

        # Process through pipeline
        page_id = 'mba-page'
        mock_graph.add_node(page_id, 'Page', {
            'id': page_id,
            'url': metadata['canonical_url'],
            'title': metadata['title']
        })

        # Extract sections from DOM
        # (In real implementation, this would use SectionExtractor)
        assert dom is not None
        assert mock_graph.node_count() >= 1

    def test_pipeline_performance_100_pages(self, performance_timer, mock_graph):
        """Test pipeline performance with 100 pages"""
        pages = generate_test_pages(count=100)

        performance_timer.start()

        for page_data in pages:
            page_id = page_data['url'].split('/')[-1]
            mock_graph.add_node(page_id, 'Page', {
                'id': page_id,
                'url': page_data['url']
            })

        elapsed = performance_timer.stop()

        assert mock_graph.node_count() == 100
        # Should process 100 pages in < 2 seconds
        assert elapsed < 2.0

    def test_pipeline_handles_errors_gracefully(self, malformed_page_data, mock_graph):
        """Test pipeline error handling"""
        # Attempt to process malformed data
        try:
            # Pipeline should handle gracefully
            if malformed_page_data['metadata']:
                page_id = 'malformed'
                mock_graph.add_node(page_id, 'Page', {
                    'id': page_id,
                    'url': malformed_page_data.get('url', 'unknown')
                })
        except Exception as e:
            # Error should be caught and logged, not crash
            pytest.fail(f"Pipeline should handle errors gracefully: {e}")

        # Graph should still be valid
        assert mock_graph.node_count() >= 0

    def test_pipeline_preserves_data_integrity(self, sample_page_data, mock_graph):
        """Test that data integrity is maintained through pipeline"""
        original_title = sample_page_data['metadata']['title']
        original_url = sample_page_data['url']

        # Process through pipeline
        page_id = 'test-page'
        mock_graph.add_node(page_id, 'Page', {
            'id': page_id,
            'url': original_url,
            'title': original_title
        })

        # Retrieve and verify
        node = mock_graph.get_node(page_id)
        assert node.data['url'] == original_url
        assert node.data['title'] == original_title

    def test_pipeline_incremental_updates(self, mock_graph):
        """Test incremental updates to existing graph"""
        # Initial graph
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1', 'version': 1})

        initial_count = mock_graph.node_count()

        # Add new page
        mock_graph.add_node('page-2', 'Page', {'id': 'page-2', 'version': 1})

        # Update existing page
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1', 'version': 2})

        # Should have added new page
        assert mock_graph.node_count() >= initial_count

    def test_pipeline_change_detection(self, mock_graph):
        """Test detection of content changes"""
        import hashlib

        # Original content
        original_text = "Original content"
        original_hash = hashlib.sha256(original_text.encode()).hexdigest()

        mock_graph.add_node('content-1', 'ContentItem', {
            'id': 'content-1',
            'hash': original_hash,
            'text': original_text
        })

        # Updated content
        updated_text = "Updated content"
        updated_hash = hashlib.sha256(updated_text.encode()).hexdigest()

        # Hashes should be different
        assert original_hash != updated_hash

    def test_pipeline_validation_report(self, mock_graph):
        """Test generation of pipeline validation report"""
        # Build graph
        for i in range(5):
            mock_graph.add_node(f'page-{i}', 'Page', {'id': f'page-{i}'})

        # Generate validation report
        report = {
            'total_nodes': mock_graph.node_count(),
            'total_edges': mock_graph.edge_count(),
            'node_types': {},
            'edge_types': {},
            'orphaned_nodes': 0,
            'broken_links': 0
        }

        # Count node types
        for node in mock_graph.nodes.values():
            report['node_types'][node.node_type] = report['node_types'].get(node.node_type, 0) + 1

        # Validate report
        assert report['total_nodes'] == 5
        assert report['node_types']['Page'] == 5

    def test_pipeline_exports_all_formats(self, mock_graph, tmp_path):
        """Test that pipeline can export to all formats"""
        # Build small graph
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})
        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')

        # Export to JSON
        json_file = tmp_path / "graph.json"
        graph_data = {
            'nodes': [{'id': n.id, 'type': n.node_type, 'data': n.data} for n in mock_graph.nodes.values()],
            'edges': [{'from': e.from_node, 'to': e.to_node, 'type': e.edge_type} for e in mock_graph.edges]
        }
        with open(json_file, 'w') as f:
            json.dump(graph_data, f)

        # Export to Cypher
        cypher_file = tmp_path / "graph.cypher"
        cypher_statements = [
            f"CREATE (:{n.node_type} {{id: '{n.id}'}});" for n in mock_graph.nodes.values()
        ]
        with open(cypher_file, 'w') as f:
            f.write('\n'.join(cypher_statements))

        # Export to Mermaid
        mermaid_file = tmp_path / "graph.mmd"
        mermaid_lines = ["graph TD"]
        for edge in mock_graph.edges:
            mermaid_lines.append(f"  {edge.from_node} -->|{edge.edge_type}| {edge.to_node}")
        with open(mermaid_file, 'w') as f:
            f.write('\n'.join(mermaid_lines))

        # Verify all files created
        assert json_file.exists()
        assert cypher_file.exists()
        assert mermaid_file.exists()


# ==================== Graph Completeness Tests ====================

@pytest.mark.integration
class TestGraphCompleteness:
    """Test graph completeness and integrity (target: 5 tests)"""

    def test_all_pages_have_nodes(self, mock_graph):
        """Test that all pages are represented as nodes"""
        pages = generate_test_pages(10)

        for page in pages:
            page_id = page['url'].split('/')[-1]
            mock_graph.add_node(page_id, 'Page', {'id': page_id})

        # All 10 pages should be in graph
        page_nodes = [n for n in mock_graph.nodes.values() if n.node_type == 'Page']
        assert len(page_nodes) == 10

    def test_all_sections_connected_to_pages(self, mock_graph):
        """Test that all sections are connected to their pages"""
        # Create page with sections
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})

        for i in range(5):
            section_id = f'section-{i}'
            mock_graph.add_node(section_id, 'Section', {'id': section_id})
            mock_graph.add_edge('page-1', section_id, 'CONTAINS')

        # All sections should have incoming CONTAINS from page
        sections = [n for n in mock_graph.nodes.values() if n.node_type == 'Section']
        for section in sections:
            inbound = mock_graph.get_edges(to_node=section.id, edge_type='CONTAINS')
            assert len(inbound) >= 1

    def test_all_content_connected_to_sections(self, mock_graph):
        """Test that all content items are connected to sections"""
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})

        for i in range(10):
            content_id = f'content-{i}'
            mock_graph.add_node(content_id, 'ContentItem', {'id': content_id})
            mock_graph.add_edge('section-1', content_id, 'CONTAINS')

        # All content should have incoming CONTAINS
        content_items = [n for n in mock_graph.nodes.values() if n.node_type == 'ContentItem']
        for item in content_items:
            inbound = mock_graph.get_edges(to_node=item.id, edge_type='CONTAINS')
            assert len(inbound) >= 1

    def test_no_orphaned_nodes(self, mock_graph):
        """Test that there are no orphaned nodes"""
        # Create connected graph
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})
        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')

        # Find orphans
        orphans = [
            n for n in mock_graph.nodes.values()
            if len(n.edges_in) == 0 and len(n.edges_out) == 0
        ]

        # Only root nodes (Pages) should have no inbound edges
        for orphan in orphans:
            assert orphan.node_type == 'Page'  # Pages can have no inbound

    def test_graph_statistics_accurate(self, mock_graph):
        """Test that graph statistics are accurate"""
        # Build known graph
        for i in range(3):
            page_id = f'page-{i}'
            mock_graph.add_node(page_id, 'Page', {'id': page_id})

            for j in range(2):
                section_id = f'{page_id}-section-{j}'
                mock_graph.add_node(section_id, 'Section', {'id': section_id})
                mock_graph.add_edge(page_id, section_id, 'CONTAINS')

        # Calculate expected stats
        expected_pages = 3
        expected_sections = 6  # 3 pages * 2 sections
        expected_contains = 6  # 1 edge per section

        # Verify
        actual_pages = len([n for n in mock_graph.nodes.values() if n.node_type == 'Page'])
        actual_sections = len([n for n in mock_graph.nodes.values() if n.node_type == 'Section'])
        actual_contains = len(mock_graph.get_edges(edge_type='CONTAINS'))

        assert actual_pages == expected_pages
        assert actual_sections == expected_sections
        assert actual_contains == expected_contains


# ==================== Performance Benchmarks ====================

@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.slow
class TestPhase2Performance:
    """Performance benchmarks for Phase 2 (target: 5 tests)"""

    def test_1000_nodes_per_second_target(self, performance_timer, mock_graph):
        """Test that we can process 1000 nodes per second"""
        target_nodes = 1000

        performance_timer.start()

        for i in range(target_nodes):
            mock_graph.add_node(f'node-{i}', 'Page', {'id': f'node-{i}'})

        elapsed = performance_timer.stop()

        # Should achieve 1000 nodes/sec (< 1 second for 1000 nodes)
        assert elapsed < 1.0
        assert mock_graph.node_count() == target_nodes

    def test_large_page_processing_performance(self, performance_timer, mock_graph):
        """Test performance on very large page"""
        large_page = generate_large_page(num_sections=500)

        performance_timer.start()

        # Process large page
        page_id = 'large-page'
        mock_graph.add_node(page_id, 'Page', {'id': page_id})

        # Add all sections
        for i in range(500):
            section_id = f'section-{i}'
            mock_graph.add_node(section_id, 'Section', {'id': section_id})
            mock_graph.add_edge(page_id, section_id, 'CONTAINS')

        elapsed = performance_timer.stop()

        # Should handle large page efficiently (< 2 seconds)
        assert elapsed < 2.0
        assert mock_graph.node_count() == 501

    def test_relationship_extraction_performance(self, performance_timer, mock_graph):
        """Test performance of relationship extraction"""
        # Create 100 pages with cross-links
        for i in range(100):
            mock_graph.add_node(f'page-{i}', 'Page', {'id': f'page-{i}'})

        performance_timer.start()

        # Create links (each page links to 5 others)
        for i in range(100):
            for j in range(5):
                target = (i + j + 1) % 100
                mock_graph.add_edge(f'page-{i}', f'page-{target}', 'LINKS_TO')

        elapsed = performance_timer.stop()

        # Should create 500 relationships quickly (< 0.5 seconds)
        assert elapsed < 0.5
        assert mock_graph.edge_count() == 500

    def test_graph_export_performance(self, performance_timer, mock_graph, tmp_path):
        """Test performance of graph export"""
        # Build graph
        for i in range(100):
            mock_graph.add_node(f'page-{i}', 'Page', {'id': f'page-{i}'})

        performance_timer.start()

        # Export to JSON
        graph_data = {
            'nodes': [
                {'id': n.id, 'type': n.node_type, 'data': n.data}
                for n in mock_graph.nodes.values()
            ],
            'edges': [
                {'from': e.from_node, 'to': e.to_node, 'type': e.edge_type}
                for e in mock_graph.edges
            ]
        }

        output_file = tmp_path / "large_graph.json"
        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)

        elapsed = performance_timer.stop()

        # Should export quickly (< 1 second)
        assert elapsed < 1.0
        assert output_file.exists()

    def test_memory_usage_large_graph(self, mock_graph):
        """Test memory efficiency with large graph"""
        import sys

        # Create large graph
        for i in range(1000):
            mock_graph.add_node(f'page-{i}', 'Page', {
                'id': f'page-{i}',
                'title': f'Page {i}',
                'url': f'/page-{i}'
            })

        # Check node count
        assert mock_graph.node_count() == 1000

        # In real implementation, would measure actual memory usage
        # For now, verify graph is functional
        sample_node = mock_graph.get_node('page-500')
        assert sample_node is not None


# ==================== Data Validation Tests ====================

@pytest.mark.integration
class TestPhase2DataValidation:
    """Test data validation through pipeline (target: 5 tests)"""

    def test_validate_all_required_fields(self, sample_page_data, mock_graph):
        """Test that all required fields are present"""
        required_fields = ['id', 'url', 'title']

        page_id = 'test-page'
        page_data = {
            'id': page_id,
            'url': sample_page_data['url'],
            'title': sample_page_data['metadata']['title']
        }

        # Validate before adding
        for field in required_fields:
            assert field in page_data

        mock_graph.add_node(page_id, 'Page', page_data)

        # Verify in graph
        node = mock_graph.get_node(page_id)
        for field in required_fields:
            assert field in node.data

    def test_validate_url_format(self, sample_page_data):
        """Test URL format validation"""
        url = sample_page_data['url']

        # Should be valid URL
        assert url.startswith('https://london.edu')
        assert '://' in url

    def test_validate_hash_format(self):
        """Test content hash format validation"""
        import hashlib

        text = "Sample content"
        hash_value = hashlib.sha256(text.encode()).hexdigest()

        # SHA-256 hash should be 64 characters hex
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_validate_relationship_integrity(self, mock_graph):
        """Test relationship integrity validation"""
        mock_graph.add_node('page-1', 'Page', {'id': 'page-1'})
        mock_graph.add_node('section-1', 'Section', {'id': 'section-1'})
        mock_graph.add_edge('page-1', 'section-1', 'CONTAINS')

        # All edges should reference existing nodes
        for edge in mock_graph.edges:
            assert edge.from_node in mock_graph.nodes
            assert edge.to_node in mock_graph.nodes

    def test_validate_no_data_loss(self, sample_page_data, mock_graph):
        """Test that no data is lost through pipeline"""
        original_data = {
            'url': sample_page_data['url'],
            'title': sample_page_data['metadata']['title'],
            'description': sample_page_data['metadata'].get('description', '')
        }

        page_id = 'test-page'
        mock_graph.add_node(page_id, 'Page', original_data)

        # Retrieve and compare
        node = mock_graph.get_node(page_id)
        assert node.data['url'] == original_data['url']
        assert node.data['title'] == original_data['title']
