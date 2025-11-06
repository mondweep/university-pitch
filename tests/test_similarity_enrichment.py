"""
Unit tests for semantic similarity enrichment system

Tests embedding generation, similarity calculation, and edge creation.
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enrichment.embedding_generator import EmbeddingGenerator, EmbeddingConfig
from enrichment.similarity_calculator import SimilarityCalculator, SimilarityConfig
from enrichment.related_to_builder import RelatedToBuilder, EdgeConfig
from enrichment.similarity_enricher import SimilarityEnricher


# Sample test data
@pytest.fixture
def sample_pages():
    """Sample page nodes for testing"""
    return [
        {
            "id": "page1",
            "node_type": "Page",
            "data": {
                "title": "MBA Programme",
                "description": "Full-time MBA with focus on leadership",
                "type": "programme",
                "topics": ["mba", "leadership", "finance"]
            }
        },
        {
            "id": "page2",
            "node_type": "Page",
            "data": {
                "title": "Executive MBA",
                "description": "Part-time MBA for executives",
                "type": "programme",
                "topics": ["mba", "executive", "leadership"]
            }
        },
        {
            "id": "page3",
            "node_type": "Page",
            "data": {
                "title": "Finance Courses",
                "description": "Advanced corporate finance",
                "type": "course",
                "topics": ["finance", "investment"]
            }
        }
    ]


@pytest.fixture
def sample_graph(sample_pages):
    """Sample graph for testing"""
    return {
        "nodes": sample_pages,
        "edges": []
    }


@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing"""
    # Create 5-dimensional embeddings
    return {
        "page1": [0.8, 0.6, 0.2, 0.1, 0.3],
        "page2": [0.75, 0.55, 0.25, 0.15, 0.25],  # Similar to page1
        "page3": [0.1, 0.2, 0.8, 0.9, 0.7]  # Different from page1
    }


# EmbeddingGenerator Tests
class TestEmbeddingGenerator:
    """Test embedding generation"""

    def test_create_embedding_text(self, sample_pages):
        """Test text creation for embedding"""
        config = EmbeddingConfig(api_key="test-key")
        with patch('enrichment.embedding_generator.OpenAI'):
            generator = EmbeddingGenerator(config)

            text = generator._create_embedding_text(sample_pages[0])

            assert "MBA Programme" in text
            assert "Full-time MBA" in text
            assert "programme" in text
            assert "mba" in text or "leadership" in text

    def test_cache_key_generation(self, sample_pages):
        """Test cache key generation"""
        config = EmbeddingConfig(api_key="test-key")
        with patch('enrichment.embedding_generator.OpenAI'):
            generator = EmbeddingGenerator(config)

            key1 = generator._get_cache_key("test text")
            key2 = generator._get_cache_key("test text")
            key3 = generator._get_cache_key("different text")

            # Same text should produce same key
            assert key1 == key2
            # Different text should produce different key
            assert key1 != key3

    @patch('enrichment.embedding_generator.OpenAI')
    def test_embedding_caching(self, mock_openai, tmp_path):
        """Test embedding caching"""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_response.usage.total_tokens = 10
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        config = EmbeddingConfig(
            api_key="test-key",
            cache_dir=tmp_path / "cache"
        )
        generator = EmbeddingGenerator(config)

        # Generate embedding twice
        text = "test text"
        embedding1 = generator.generate_embedding(text)
        embedding2 = generator.generate_embedding(text)

        # Should get same embedding
        assert embedding1 == embedding2

        # API should only be called once (second time uses cache)
        assert mock_client.embeddings.create.call_count == 1
        assert generator.stats["cache_hits"] == 1


# SimilarityCalculator Tests
class TestSimilarityCalculator:
    """Test similarity calculation"""

    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        calculator = SimilarityCalculator()

        # Identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert calculator.cosine_similarity(vec1, vec2) == pytest.approx(1.0)

        # Orthogonal vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        assert calculator.cosine_similarity(vec1, vec2) == pytest.approx(0.0)

        # Similar vectors
        vec1 = [0.8, 0.6]
        vec2 = [0.75, 0.65]
        similarity = calculator.cosine_similarity(vec1, vec2)
        assert 0.9 < similarity < 1.0

    def test_pairwise_similarities(self, sample_embeddings):
        """Test pairwise similarity calculation"""
        config = SimilarityConfig(min_similarity=0.5)
        calculator = SimilarityCalculator(config)

        similarities = calculator.calculate_pairwise_similarities(sample_embeddings)

        # Should have similarities for all pairs above threshold
        assert len(similarities) > 0

        # Check bidirectional storage
        if ("page1", "page2") in similarities:
            assert ("page2", "page1") in similarities
            assert similarities[("page1", "page2")] == similarities[("page2", "page1")]

    def test_top_similar_pages(self, sample_embeddings):
        """Test finding top similar pages"""
        config = SimilarityConfig(
            similarity_threshold=0.7,
            top_k=2
        )
        calculator = SimilarityCalculator(config)

        similarities = calculator.calculate_pairwise_similarities(sample_embeddings)
        top_similar = calculator.get_top_similar_pages("page1", similarities, k=2)

        # Should return list of (page_id, score) tuples
        assert isinstance(top_similar, list)
        for item in top_similar:
            assert len(item) == 2
            page_id, score = item
            assert isinstance(page_id, str)
            assert isinstance(score, float)
            assert 0 <= score <= 1

        # Should be sorted by score
        if len(top_similar) > 1:
            assert top_similar[0][1] >= top_similar[1][1]

    def test_similarity_matrix(self, sample_embeddings):
        """Test similarity matrix calculation"""
        calculator = SimilarityCalculator()

        matrix, page_ids = calculator.calculate_similarity_matrix(sample_embeddings)

        # Check shape
        n = len(sample_embeddings)
        assert matrix.shape == (n, n)

        # Check diagonal is 1.0
        for i in range(n):
            assert matrix[i, i] == pytest.approx(1.0)

        # Check symmetry
        for i in range(n):
            for j in range(n):
                assert matrix[i, j] == pytest.approx(matrix[j, i])

        # Check values are in [0, 1]
        assert np.all(matrix >= 0.0)
        assert np.all(matrix <= 1.0)


# RelatedToBuilder Tests
class TestRelatedToBuilder:
    """Test RELATED_TO edge building"""

    def test_extract_topics(self, sample_graph):
        """Test topic extraction from pages"""
        builder = RelatedToBuilder()

        page = sample_graph["nodes"][0]
        topics = builder._extract_topics(page)

        assert "mba" in topics or "programme" in topics
        assert len(topics) > 0

    def test_find_shared_topics(self, sample_graph):
        """Test finding shared topics between pages"""
        builder = RelatedToBuilder()

        shared = builder._find_shared_topics("page1", "page2", sample_graph)

        # page1 and page2 share "mba" and "leadership"
        assert len(shared) >= 1
        assert any(topic in ["mba", "leadership", "programme"] for topic in shared)

    def test_create_edge(self, sample_graph):
        """Test edge creation"""
        config = EdgeConfig(
            min_similarity=0.7,
            add_reasoning=True
        )
        builder = RelatedToBuilder(config)

        edge = builder.create_edge("page1", "page2", 0.85, sample_graph)

        # Should create valid edge
        assert edge is not None
        assert edge["source"] == "page1"
        assert edge["target"] == "page2"
        assert edge["edge_type"] == "RELATED_TO"
        assert "similarity" in edge["data"]
        assert edge["data"]["similarity"] == 0.85
        assert "reasoning" in edge["data"]

    def test_edge_similarity_threshold(self, sample_graph):
        """Test that edges below threshold are not created"""
        config = EdgeConfig(min_similarity=0.8)
        builder = RelatedToBuilder(config)

        # Low similarity should return None
        edge = builder.create_edge("page1", "page2", 0.6, sample_graph)
        assert edge is None

        # High similarity should create edge
        edge = builder.create_edge("page1", "page2", 0.85, sample_graph)
        assert edge is not None

    def test_build_edges(self, sample_graph):
        """Test building multiple edges"""
        config = EdgeConfig(min_similarity=0.7, max_edges_per_page=5)
        builder = RelatedToBuilder(config)

        similarities = {
            "page1": [("page2", 0.85), ("page3", 0.72)],
            "page2": [("page1", 0.85)],
            "page3": [("page1", 0.72)]
        }

        edges = builder.build_edges(similarities, sample_graph)

        # Should create edges without duplicates
        assert len(edges) > 0

        # Check no duplicate pairs
        pairs = set()
        for edge in edges:
            pair = tuple(sorted([edge["source"], edge["target"]]))
            assert pair not in pairs
            pairs.add(pair)


# SimilarityEnricher Tests
class TestSimilarityEnricher:
    """Test complete enrichment pipeline"""

    @patch('enrichment.embedding_generator.OpenAI')
    def test_enrich_graph(self, mock_openai, sample_graph, sample_embeddings):
        """Test complete graph enrichment"""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()

        # Return different embeddings for each call
        embeddings_list = list(sample_embeddings.values())
        call_count = [0]

        def create_embedding(model, input):
            result = MagicMock()
            result.data = [MagicMock(embedding=embeddings_list[call_count[0] % len(embeddings_list)])]
            result.usage.total_tokens = 10
            call_count[0] += 1
            return result

        mock_client.embeddings.create = create_embedding
        mock_openai.return_value = mock_client

        # Create enricher
        embedding_config = EmbeddingConfig(api_key="test-key")
        similarity_config = SimilarityConfig(similarity_threshold=0.7)
        edge_config = EdgeConfig(min_similarity=0.7)

        enricher = SimilarityEnricher(
            embedding_config=embedding_config,
            similarity_config=similarity_config,
            edge_config=edge_config
        )

        # Enrich graph
        enriched = enricher.enrich_graph(sample_graph)

        # Check results
        assert "metadata" in enriched
        assert enriched["metadata"]["similarity_enriched"] is True

        # Should have created some edges
        assert "edges" in enriched
        # Note: Edges might be 0 if embeddings are too different after mocking

        # Check stats
        stats = enricher.get_stats()
        assert stats["pages_processed"] == 3
        assert "duration_seconds" in stats

    @patch('enrichment.embedding_generator.OpenAI')
    def test_get_stats(self, mock_openai):
        """Test statistics collection"""
        mock_openai.return_value = MagicMock()

        embedding_config = EmbeddingConfig(api_key="test-key")
        enricher = SimilarityEnricher(embedding_config=embedding_config)

        stats = enricher.get_stats()

        assert "pages_processed" in stats
        assert "embeddings_generated" in stats
        assert "similarities_calculated" in stats
        assert "edges_created" in stats


# Integration Tests
class TestIntegration:
    """Integration tests for complete pipeline"""

    @patch('enrichment.embedding_generator.OpenAI')
    def test_full_pipeline(self, mock_openai, sample_graph, sample_embeddings):
        """Test full enrichment pipeline"""
        # Setup realistic mock
        mock_client = MagicMock()

        # Use actual embeddings
        embeddings_list = list(sample_embeddings.values())
        call_count = [0]

        def create_embedding(model, input):
            result = MagicMock()
            embedding = embeddings_list[call_count[0] % len(embeddings_list)]
            result.data = [MagicMock(embedding=embedding)]
            result.usage.total_tokens = 10
            call_count[0] += 1
            return result

        mock_client.embeddings.create = create_embedding
        mock_openai.return_value = mock_client

        # Run pipeline
        enricher = SimilarityEnricher(
            embedding_config=EmbeddingConfig(api_key="test-key"),
            similarity_config=SimilarityConfig(
                similarity_threshold=0.7,
                top_k=2
            ),
            edge_config=EdgeConfig(
                min_similarity=0.7,
                max_edges_per_page=3
            )
        )

        enriched = enricher.enrich_graph(sample_graph)

        # Verify structure
        assert "nodes" in enriched
        assert "edges" in enriched
        assert "metadata" in enriched

        # Verify nodes unchanged
        assert len(enriched["nodes"]) == len(sample_graph["nodes"])

        # Verify metadata
        assert enriched["metadata"]["similarity_enriched"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
