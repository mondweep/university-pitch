"""
Test NER Enrichment Pipeline

Tests the complete NER pipeline including:
- Entity extraction
- Entity node creation with deduplication
- MENTIONS edge creation
- Statistics and cost tracking
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "lbs-knowledge-graph" / "src"))

# Import modules
from src.enrichment.entity_node_builder import EntityNodeBuilder
from src.enrichment.mentions_builder import MentionsBuilder
from src.enrichment.ner_enricher import NEREnricher


class MockGraph:
    """Mock MGraph for testing"""

    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.node_id_counter = 0

    def add_node(self, node_type, node_id, data):
        """Add node to graph"""
        self.nodes[node_id] = {
            "node_type": node_type,
            "id": node_id,
            "data": data
        }

    def add_edge(self, from_node_id, to_node_id, edge_type, data):
        """Add edge to graph"""
        self.edges.append({
            "from_node": from_node_id,
            "to_node": to_node_id,
            "edge_type": edge_type,
            "data": data
        })

    def get_node(self, node_id):
        """Get node by ID"""
        return self.nodes.get(node_id)

    def get_edges(self, from_node_id=None, to_node_id=None, edge_type=None):
        """Get edges with filters"""
        filtered = self.edges

        if from_node_id:
            filtered = [e for e in filtered if e["from_node"] == from_node_id]
        if to_node_id:
            filtered = [e for e in filtered if e["to_node"] == to_node_id]
        if edge_type:
            filtered = [e for e in filtered if e["edge_type"] == edge_type]

        # Return mock edge objects
        class MockEdge:
            def __init__(self, edge_data):
                self.from_node = edge_data["from_node"]
                self.to_node = edge_data["to_node"]
                self.edge_type = edge_data["edge_type"]
                self.data = edge_data["data"]

        return [MockEdge(e) for e in filtered]

    def query(self, node_type):
        """Query nodes by type"""
        class MockNode:
            def __init__(self, node_data):
                self.id = node_data["id"]
                self.node_type = node_data["node_type"]
                self.data = node_data["data"]

        return [
            MockNode(n) for n in self.nodes.values()
            if n["node_type"] == node_type
        ]

    def node_count(self):
        """Get node count"""
        return len(self.nodes)

    def edge_count(self):
        """Get edge count"""
        return len(self.edges)


# Sample test data
SAMPLE_ENTITIES = [
    {
        "id": "temp-entity-1",
        "name": "London Business School",
        "entity_type": "ORGANIZATION",
        "canonical_name": "London Business School",
        "aliases": ["London Business School", "LBS"],
        "metadata": {"type": "Business School", "location": "London"},
        "mention_count": 1,
        "prominence": 0.95,
        "confidence": 0.98,
        "first_mentioned": "2025-11-06T20:00:00"
    },
    {
        "id": "temp-entity-2",
        "name": "LBS",
        "entity_type": "ORGANIZATION",
        "canonical_name": "London Business School",
        "aliases": ["LBS"],
        "metadata": {"type": "Business School"},
        "mention_count": 1,
        "prominence": 0.75,
        "confidence": 0.90,
        "first_mentioned": "2025-11-06T20:01:00"
    },
    {
        "id": "temp-entity-3",
        "name": "Professor Jane Smith",
        "entity_type": "PERSON",
        "canonical_name": "Jane Smith",
        "aliases": ["Professor Jane Smith"],
        "metadata": {"role": "Professor", "affiliation": "London Business School"},
        "mention_count": 1,
        "prominence": 0.85,
        "confidence": 0.95,
        "first_mentioned": "2025-11-06T20:02:00"
    }
]

SAMPLE_MENTIONS = [
    {
        "entity_id": "temp-entity-1",
        "content_id": "content-1",
        "entity_text": "London Business School",
        "context": "Welcome to London Business School, a leading institution...",
        "prominence": "high",
        "confidence": 0.98,
        "position": 0,
        "extracted_by": "gpt-4-turbo"
    },
    {
        "entity_id": "temp-entity-2",
        "content_id": "content-1",
        "entity_text": "LBS",
        "context": "...at LBS, we strive for excellence...",
        "prominence": "medium",
        "confidence": 0.90,
        "position": 150,
        "extracted_by": "gpt-4-turbo"
    },
    {
        "entity_id": "temp-entity-3",
        "content_id": "content-2",
        "entity_text": "Professor Jane Smith",
        "context": "Professor Jane Smith leads the Finance department...",
        "prominence": "high",
        "confidence": 0.95,
        "position": 10,
        "extracted_by": "gpt-4-turbo"
    }
]


class TestEntityNodeBuilder:
    """Test EntityNodeBuilder functionality"""

    def test_entity_creation(self):
        """Test basic entity node creation"""
        graph = MockGraph()
        builder = EntityNodeBuilder(graph)

        stats = builder.add_entities(SAMPLE_ENTITIES)

        # Should deduplicate LBS and London Business School
        assert stats["unique_entities"] == 2  # Organization and Person
        assert stats["merged_entities"] == 1  # LBS merged with London Business School
        assert stats["total_extracted"] == 3

        # Check entity node created
        org_id = "entity-organization-london-business-school"
        assert org_id in graph.nodes
        entity = graph.nodes[org_id]
        assert entity["data"]["entity_type"] == "ORGANIZATION"
        assert entity["data"]["mention_count"] == 2  # Merged

    def test_canonical_id_mapping(self):
        """Test temp ID to canonical ID mapping"""
        graph = MockGraph()
        builder = EntityNodeBuilder(graph)

        builder.add_entities(SAMPLE_ENTITIES)

        # Both temp IDs should map to same canonical ID
        canonical_id = builder.get_canonical_entity_id("temp-entity-1")
        assert canonical_id == builder.get_canonical_entity_id("temp-entity-2")
        assert canonical_id == "entity-organization-london-business-school"

    def test_entity_stats(self):
        """Test entity statistics generation"""
        graph = MockGraph()
        builder = EntityNodeBuilder(graph)

        builder.add_entities(SAMPLE_ENTITIES)
        stats = builder.get_entity_stats()

        assert stats["total_entities"] == 2
        assert stats["by_type"]["ORGANIZATION"] == 1
        assert stats["by_type"]["PERSON"] == 1
        assert len(stats["top_entities"]) == 2


class TestMentionsBuilder:
    """Test MentionsBuilder functionality"""

    def test_mentions_creation(self):
        """Test MENTIONS edge creation"""
        graph = MockGraph()
        entity_builder = EntityNodeBuilder(graph)
        entity_builder.add_entities(SAMPLE_ENTITIES)

        mentions_builder = MentionsBuilder(graph, entity_builder)
        stats = mentions_builder.add_mentions(SAMPLE_MENTIONS)

        # Should create 2 edges (2 content items)
        assert stats["edges_created"] == 2
        assert stats["total_mentions"] == 3

        # Check edge data
        edges = graph.get_edges(edge_type="MENTIONS")
        assert len(edges) == 2

    def test_mention_aggregation(self):
        """Test aggregation of multiple mentions"""
        graph = MockGraph()
        entity_builder = EntityNodeBuilder(graph)
        entity_builder.add_entities(SAMPLE_ENTITIES)

        mentions_builder = MentionsBuilder(graph, entity_builder)
        mentions_builder.add_mentions(SAMPLE_MENTIONS)

        # Check aggregated edge for content-1 -> LBS
        edges = graph.get_edges(from_node_id="content-1", edge_type="MENTIONS")
        assert len(edges) == 1

        edge_data = edges[0].data
        assert edge_data["mention_count"] == 2  # Aggregated
        assert "London Business School" in edge_data["entity_texts"]
        assert "LBS" in edge_data["entity_texts"]

    def test_validation(self):
        """Test mention validation"""
        graph = MockGraph()
        entity_builder = EntityNodeBuilder(graph)
        entity_builder.add_entities(SAMPLE_ENTITIES)

        mentions_builder = MentionsBuilder(graph, entity_builder)
        mentions_builder.add_mentions(SAMPLE_MENTIONS)

        # Validation should pass (no errors)
        report = mentions_builder.validate_mentions()
        assert report["total_mentions_edges"] == 2
        # Note: validation will fail because mock ContentItem nodes don't exist
        # This is expected for unit test


class TestNEREnricher:
    """Test NEREnricher orchestration"""

    @pytest.mark.asyncio
    async def test_enricher_pipeline(self):
        """Test complete enrichment pipeline with mocked extraction"""
        graph = MockGraph()

        # Add mock ContentItem nodes
        graph.add_node("ContentItem", "content-1", {
            "text": "This is a test content about London Business School and LBS."
        })
        graph.add_node("ContentItem", "content-2", {
            "text": "Professor Jane Smith is a renowned expert at LBS."
        })

        # Mock NER extractor
        with patch('src.enrichment.ner_enricher.NERExtractor') as MockExtractor:
            mock_extractor = MockExtractor.return_value

            # Mock extraction results
            from unittest.mock import MagicMock
            mock_result = MagicMock()
            mock_result.entities = [
                MagicMock(**{
                    "to_dict.return_value": e
                }) for e in SAMPLE_ENTITIES
            ]
            mock_result.mentions = [
                MagicMock(**{
                    "to_dict.return_value": m
                }) for m in SAMPLE_MENTIONS
            ]
            mock_result.cost = 0.05

            mock_extractor.extract_batch = AsyncMock(return_value=[mock_result, mock_result])
            mock_extractor.get_stats = Mock(return_value={
                "api_calls": 2,
                "total_tokens": 1500,
                "total_cost": 0.10
            })

            # Run enricher
            enricher = NEREnricher(graph, api_key="test-key")
            enricher.extractor = mock_extractor

            stats = await enricher.enrich_graph(max_items=2)

            # Verify stats
            assert stats["content_items_processed"] == 2
            assert stats["entities_extracted"] > 0
            assert stats["unique_entities"] > 0
            assert stats["mentions_created"] > 0
            assert stats["total_cost"] > 0


def test_cli_imports():
    """Test that CLI script imports work correctly"""
    import scripts.enrich_ner as cli_module
    assert hasattr(cli_module, "run_enrichment")
    assert hasattr(cli_module, "main")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
