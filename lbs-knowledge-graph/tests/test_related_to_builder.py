"""
Tests for RelatedToBuilder
"""

import pytest
from src.enrichment.related_to_builder import RelatedToBuilder, RelatedToEdge
from src.graph.mgraph_compat import MGraph


class TestRelatedToBuilder:
    """Test suite for RelatedToBuilder."""

    def setup_method(self):
        """Setup test fixtures."""
        self.graph = MGraph()

        # Create test nodes
        self.graph.add_node('node1', type='Page', title='Page 1')
        self.graph.add_node('node2', type='Page', title='Page 2')
        self.graph.add_node('node3', type='Section', heading='Section 1')

        self.builder = RelatedToBuilder(self.graph)

    def test_create_related_to_edge(self):
        """Test creating a RELATED_TO edge."""
        success = self.builder.create_related_to_edge(
            'node1',
            'node2',
            similarity=0.85,
            similarity_type='embedding',
            metadata={'method': 'cosine'},
            bidirectional=False
        )

        assert success
        edges = self.graph.get_edges('node1', edge_type='RELATED_TO')
        assert len(edges) == 1
        assert edges[0]['target'] == 'node2'
        assert edges[0]['similarity'] == 0.85

    def test_create_bidirectional_edge(self):
        """Test creating bidirectional RELATED_TO edges."""
        success = self.builder.create_related_to_edge(
            'node1',
            'node2',
            similarity=0.85,
            similarity_type='embedding',
            bidirectional=True
        )

        assert success

        # Check forward edge
        forward_edges = self.graph.get_edges('node1', edge_type='RELATED_TO')
        assert len(forward_edges) == 1
        assert forward_edges[0]['target'] == 'node2'

        # Check reverse edge
        reverse_edges = self.graph.get_edges('node2', edge_type='RELATED_TO')
        assert len(reverse_edges) == 1
        assert reverse_edges[0]['target'] == 'node1'

    def test_prevent_self_referential_edge(self):
        """Test that self-referential edges are prevented."""
        success = self.builder.create_related_to_edge(
            'node1',
            'node1',
            similarity=1.0,
            similarity_type='embedding'
        )

        assert not success

    def test_create_batch_edges(self):
        """Test creating multiple edges in batch."""
        edges = [
            RelatedToEdge(
                source_id='node1',
                target_id='node2',
                similarity=0.85,
                similarity_type='embedding',
                metadata={},
                created_at='2025-01-01T00:00:00'
            ),
            RelatedToEdge(
                source_id='node1',
                target_id='node3',
                similarity=0.75,
                similarity_type='topic',
                metadata={},
                created_at='2025-01-01T00:00:00'
            )
        ]

        count = self.builder.create_batch_edges(edges, bidirectional=False)
        assert count == 2

        edges_from_node1 = self.graph.get_edges('node1', edge_type='RELATED_TO')
        assert len(edges_from_node1) == 2

    def test_build_related_graph(self):
        """Test building complete related content graph."""
        similarities = [
            {
                'source_id': 'node1',
                'target_id': 'node2',
                'similarity': 0.85,
                'similarity_type': 'embedding',
                'metadata': {}
            },
            {
                'source_id': 'node2',
                'target_id': 'node3',
                'similarity': 0.60,  # Below threshold
                'similarity_type': 'topic',
                'metadata': {}
            }
        ]

        graph = self.builder.build_related_graph(
            similarities,
            bidirectional=True,
            min_similarity=0.7
        )

        # Should only create edges for similarity >= 0.7
        edges = self.graph.get_edges('node1', edge_type='RELATED_TO')
        assert len(edges) >= 1  # At least the 0.85 edge

        # The 0.60 edge should not exist
        node2_edges = [e for e in self.graph.get_edges('node2', edge_type='RELATED_TO') if e['target'] == 'node3']
        assert len(node2_edges) == 0

    def test_get_related_content(self):
        """Test retrieving related content."""
        # Create edges
        self.builder.create_related_to_edge(
            'node1', 'node2', 0.85, 'embedding', bidirectional=False
        )
        self.builder.create_related_to_edge(
            'node1', 'node3', 0.75, 'topic', bidirectional=False
        )

        # Get related content
        related = self.builder.get_related_content(
            'node1',
            min_similarity=0.7,
            max_results=10
        )

        assert len(related) == 2
        assert related[0]['content_id'] == 'node2'  # Higher similarity first
        assert related[0]['similarity'] == 0.85

    def test_get_related_stats(self):
        """Test getting relationship statistics."""
        # Create some edges
        self.builder.create_related_to_edge(
            'node1', 'node2', 0.85, 'embedding', bidirectional=True
        )
        self.builder.create_related_to_edge(
            'node1', 'node3', 0.75, 'topic', bidirectional=True
        )

        stats = self.builder.get_related_stats()

        assert stats['total_edges'] >= 4  # 2 bidirectional = 4 edges
        assert stats['average_similarity'] > 0
        assert 'embedding' in stats['by_type']
        assert 'topic' in stats['by_type']

    def test_remove_low_similarity_edges(self):
        """Test removing edges below threshold."""
        # Create edges with different similarities
        self.builder.create_related_to_edge(
            'node1', 'node2', 0.85, 'embedding', bidirectional=False
        )
        self.builder.create_related_to_edge(
            'node1', 'node3', 0.60, 'topic', bidirectional=False
        )

        # Remove edges below 0.7
        removed = self.builder.remove_low_similarity_edges(min_similarity=0.7)

        assert removed >= 1  # Should remove the 0.60 edge

        # Check remaining edges
        edges = self.graph.get_edges('node1', edge_type='RELATED_TO')
        for edge in edges:
            assert edge.get('similarity', 0) >= 0.7
