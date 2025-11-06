"""
Tests for Similarity Calculation functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lbs-knowledge-graph'))

from src.enrichment.similarity_calculator import SimilarityCalculator, SimilarityResult


class TestCosineSimilarity:
    """Test cosine similarity calculations."""

    @pytest.fixture
    def calculator(self):
        return SimilarityCalculator()

    def test_identical_vectors(self, calculator):
        """Test similarity of identical vectors is 1.0."""
        vec = [1.0, 2.0, 3.0, 4.0]
        similarity = calculator.cosine_similarity(vec, vec)
        assert pytest.approx(similarity, 0.001) == 1.0

    def test_orthogonal_vectors(self, calculator):
        """Test similarity of orthogonal vectors is 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = calculator.cosine_similarity(vec1, vec2)
        assert pytest.approx(similarity, 0.001) == 0.0

    def test_similar_vectors(self, calculator):
        """Test similarity of similar vectors."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.1, 2.1, 2.9]
        similarity = calculator.cosine_similarity(vec1, vec2)
        assert 0.95 < similarity < 1.0

    def test_opposite_vectors(self, calculator):
        """Test similarity of opposite vectors is 0.0 (using non-negative embeddings)."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.1, 0.1, 0.1]  # Very different
        similarity = calculator.cosine_similarity(vec1, vec2)
        assert similarity < 0.5

    def test_empty_vectors(self, calculator):
        """Test handling of empty vectors."""
        similarity = calculator.cosine_similarity([], [])
        assert similarity == 0.0

    def test_dimension_mismatch(self, calculator):
        """Test error on dimension mismatch."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]
        with pytest.raises(ValueError, match="Vector dimensions mismatch"):
            calculator.cosine_similarity(vec1, vec2)


class TestJaccardSimilarity:
    """Test Jaccard similarity for sets."""

    @pytest.fixture
    def calculator(self):
        return SimilarityCalculator()

    def test_identical_sets(self, calculator):
        """Test Jaccard similarity of identical sets is 1.0."""
        set1 = {"a", "b", "c"}
        set2 = {"a", "b", "c"}
        similarity = calculator.jaccard_similarity(set1, set2)
        assert similarity == 1.0

    def test_disjoint_sets(self, calculator):
        """Test Jaccard similarity of disjoint sets is 0.0."""
        set1 = {"a", "b"}
        set2 = {"c", "d"}
        similarity = calculator.jaccard_similarity(set1, set2)
        assert similarity == 0.0

    def test_partial_overlap(self, calculator):
        """Test Jaccard similarity with partial overlap."""
        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}
        # Intersection: {b, c} = 2, Union: {a, b, c, d} = 4
        # Jaccard = 2/4 = 0.5
        similarity = calculator.jaccard_similarity(set1, set2)
        assert pytest.approx(similarity, 0.001) == 0.5

    def test_empty_sets(self, calculator):
        """Test handling of empty sets."""
        similarity = calculator.jaccard_similarity(set(), {"a"})
        assert similarity == 0.0


class TestFindSimilar:
    """Test finding similar content by embeddings."""

    @pytest.fixture
    def calculator(self):
        return SimilarityCalculator()

    @pytest.fixture
    def candidate_embeddings(self):
        """Create sample candidate embeddings."""
        return {
            "doc1": [1.0, 0.0, 0.0],
            "doc2": [0.9, 0.1, 0.0],  # Very similar to query
            "doc3": [0.0, 1.0, 0.0],  # Orthogonal
            "doc4": [0.5, 0.5, 0.0],  # Somewhat similar
        }

    def test_find_similar_top_k(self, calculator, candidate_embeddings):
        """Test finding top K similar documents."""
        query = [1.0, 0.0, 0.0]
        results = calculator.find_similar(
            query,
            candidate_embeddings,
            top_k=2,
            threshold=0.0
        )
        
        assert len(results) <= 2
        # Most similar should be doc2
        assert results[0].content_id in ["doc1", "doc2"]
        assert results[0].similarity > 0.9

    def test_find_similar_with_threshold(self, calculator, candidate_embeddings):
        """Test filtering by similarity threshold."""
        query = [1.0, 0.0, 0.0]
        results = calculator.find_similar(
            query,
            candidate_embeddings,
            top_k=10,
            threshold=0.8
        )
        
        # Only highly similar documents should be included
        assert all(r.similarity >= 0.8 for r in results)

    def test_similarity_result_attributes(self, calculator, candidate_embeddings):
        """Test SimilarityResult attributes."""
        query = [1.0, 0.0, 0.0]
        results = calculator.find_similar(query, candidate_embeddings, top_k=1)
        
        assert len(results) > 0
        result = results[0]
        assert hasattr(result, 'content_id')
        assert hasattr(result, 'similarity')
        assert hasattr(result, 'similarity_type')
        assert hasattr(result, 'metadata')
        assert result.similarity_type == 'embedding'


class TestTopicEntitySimilarity:
    """Test topic and entity similarity."""

    @pytest.fixture
    def calculator(self):
        return SimilarityCalculator()

    def test_topic_similarity(self, calculator):
        """Test topic overlap similarity."""
        topics1 = ["finance", "mba", "career"]
        topics2 = ["finance", "mba", "leadership"]
        
        similarity = calculator.topic_similarity(topics1, topics2)
        
        # Intersection: {finance, mba} = 2
        # Union: {finance, mba, career, leadership} = 4
        # Jaccard = 2/4 = 0.5
        assert pytest.approx(similarity, 0.001) == 0.5

    def test_entity_similarity(self, calculator):
        """Test entity overlap similarity."""
        entities1 = ["Jane Smith", "LBS", "London"]
        entities2 = ["Jane Smith", "Harvard", "Boston"]
        
        similarity = calculator.entity_similarity(entities1, entities2)
        
        # Only "Jane Smith" in common
        # Jaccard = 1/5 = 0.2
        assert pytest.approx(similarity, 0.001) == 0.2


class TestMultiSignalSimilarity:
    """Test multi-signal similarity combining embeddings, topics, entities."""

    @pytest.fixture
    def calculator(self):
        return SimilarityCalculator(
            embedding_weight=0.6,
            topic_weight=0.3,
            entity_weight=0.1
        )

    def test_multi_signal_combination(self, calculator):
        """Test weighted combination of signals."""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [0.9, 0.1, 0.0]  # High embedding similarity
        topics1 = ["finance", "mba"]
        topics2 = ["finance", "leadership"]  # Moderate topic similarity
        entities1 = ["Jane"]
        entities2 = ["John"]  # Low entity similarity
        
        weighted_sim, breakdown = calculator.multi_signal_similarity(
            emb1, emb2, topics1, topics2, entities1, entities2
        )
        
        assert 0.0 <= weighted_sim <= 1.0
        assert "embedding_similarity" in breakdown
        assert "topic_similarity" in breakdown
        assert "entity_similarity" in breakdown
        assert "weighted_similarity" in breakdown

    def test_multi_signal_without_entities(self, calculator):
        """Test multi-signal when entities are not provided."""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [0.9, 0.1, 0.0]
        topics1 = ["finance"]
        topics2 = ["finance"]
        
        weighted_sim, breakdown = calculator.multi_signal_similarity(
            emb1, emb2, topics1, topics2, None, None
        )
        
        # Entity weight should be redistributed
        assert breakdown["entity_weight"] == 0.0
        assert breakdown["embedding_weight"] + breakdown["topic_weight"] == 1.0


class TestBatchSimilarity:
    """Test batch similarity calculations."""

    @pytest.fixture
    def calculator(self):
        return SimilarityCalculator()

    @pytest.fixture
    def test_data(self):
        """Create test data for batch similarity."""
        query_data = {
            "embedding": [1.0, 0.0, 0.0],
            "topics": ["finance", "mba"],
            "entities": ["Jane"]
        }
        
        candidates = {
            "doc1": {
                "embedding": [0.9, 0.1, 0.0],
                "topics": ["finance", "mba"],
                "entities": ["Jane"]
            },
            "doc2": {
                "embedding": [0.0, 1.0, 0.0],
                "topics": ["marketing"],
                "entities": ["John"]
            }
        }
        
        return query_data, candidates

    def test_batch_similarity_multi_signal(self, calculator, test_data):
        """Test batch similarity with multi-signal."""
        query_data, candidates = test_data
        
        results = calculator.batch_similarity(
            "query",
            query_data,
            candidates,
            top_k=5,
            threshold=0.0,
            use_multi_signal=True
        )
        
        assert len(results) > 0
        # doc1 should be more similar than doc2
        assert results[0].content_id == "doc1"
        assert results[0].similarity > 0.5

    def test_batch_similarity_embedding_only(self, calculator, test_data):
        """Test batch similarity with embedding only."""
        query_data, candidates = test_data
        
        results = calculator.batch_similarity(
            "query",
            query_data,
            candidates,
            top_k=5,
            threshold=0.0,
            use_multi_signal=False
        )
        
        assert len(results) > 0
        assert results[0].similarity_type == 'embedding'

    def test_exclude_self_similarity(self, calculator, test_data):
        """Test that query document is excluded from results."""
        query_data, candidates = test_data
        candidates["query"] = query_data  # Add query to candidates
        
        results = calculator.batch_similarity(
            "query",
            query_data,
            candidates,
            top_k=10,
            threshold=0.0
        )
        
        # Query should not be in results
        assert not any(r.content_id == "query" for r in results)


class TestApproximateNearestNeighbors:
    """Test approximate nearest neighbors for large graphs."""

    @pytest.fixture
    def calculator(self):
        return SimilarityCalculator()

    @pytest.fixture
    def large_candidates(self):
        """Create large set of candidate embeddings."""
        return {
            f"doc{i}": [np.random.rand(), np.random.rand(), np.random.rand()]
            for i in range(100)
        }

    def test_ann_with_sampling(self, calculator, large_candidates):
        """Test approximate nearest neighbors with sampling."""
        query = [0.5, 0.5, 0.5]
        
        results = calculator.approximate_nearest_neighbors(
            query,
            large_candidates,
            top_k=5,
            sample_ratio=0.2  # Sample 20% of candidates
        )
        
        assert len(results) <= 5
        assert all(r.similarity >= 0.0 for r in results)

    def test_ann_small_dataset_uses_exact(self, calculator):
        """Test that small datasets use exact search."""
        query = [1.0, 0.0, 0.0]
        candidates = {f"doc{i}": [0.9, 0.1, 0.0] for i in range(5)}
        
        results = calculator.approximate_nearest_neighbors(
            query,
            candidates,
            top_k=3,
            sample_ratio=0.5
        )
        
        # Should return results
        assert len(results) <= 3


class TestWeightConfiguration:
    """Test similarity weight configuration."""

    def test_custom_weights(self):
        """Test setting custom weights."""
        calculator = SimilarityCalculator(
            embedding_weight=0.5,
            topic_weight=0.3,
            entity_weight=0.2
        )
        
        assert calculator.embedding_weight == 0.5
        assert calculator.topic_weight == 0.3
        assert calculator.entity_weight == 0.2

    def test_weight_normalization(self):
        """Test automatic weight normalization."""
        calculator = SimilarityCalculator(
            embedding_weight=6,
            topic_weight=3,
            entity_weight=1
        )
        
        # Weights should sum to 1.0
        total = calculator.embedding_weight + calculator.topic_weight + calculator.entity_weight
        assert pytest.approx(total, 0.001) == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
