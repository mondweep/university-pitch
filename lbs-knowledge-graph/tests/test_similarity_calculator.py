"""
Tests for SimilarityCalculator
"""

import pytest
from src.enrichment.similarity_calculator import SimilarityCalculator, SimilarityResult


class TestSimilarityCalculator:
    """Test suite for SimilarityCalculator."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calc = SimilarityCalculator(
            embedding_weight=0.6,
            topic_weight=0.3,
            entity_weight=0.1
        )

    def test_cosine_similarity_identical(self):
        """Test cosine similarity of identical vectors."""
        vec = [1.0, 2.0, 3.0]
        similarity = self.calc.cosine_similarity(vec, vec)
        assert similarity == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity of orthogonal vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = self.calc.cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0)

    def test_cosine_similarity_opposite(self):
        """Test cosine similarity of opposite vectors."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        similarity = self.calc.cosine_similarity(vec1, vec2)
        # Should be 0 (clamped from -1)
        assert similarity == pytest.approx(0.0)

    def test_cosine_similarity_different_dimensions(self):
        """Test error handling for different dimensions."""
        vec1 = [1.0, 2.0]
        vec2 = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError):
            self.calc.cosine_similarity(vec1, vec2)

    def test_jaccard_similarity_identical(self):
        """Test Jaccard similarity of identical sets."""
        set1 = {'a', 'b', 'c'}
        set2 = {'a', 'b', 'c'}
        similarity = self.calc.jaccard_similarity(set1, set2)
        assert similarity == 1.0

    def test_jaccard_similarity_disjoint(self):
        """Test Jaccard similarity of disjoint sets."""
        set1 = {'a', 'b', 'c'}
        set2 = {'d', 'e', 'f'}
        similarity = self.calc.jaccard_similarity(set1, set2)
        assert similarity == 0.0

    def test_jaccard_similarity_partial_overlap(self):
        """Test Jaccard similarity with partial overlap."""
        set1 = {'a', 'b', 'c', 'd'}
        set2 = {'c', 'd', 'e', 'f'}
        # Intersection: {c, d} (2), Union: {a, b, c, d, e, f} (6)
        # Similarity: 2/6 = 0.333...
        similarity = self.calc.jaccard_similarity(set1, set2)
        assert similarity == pytest.approx(2.0 / 6.0)

    def test_topic_similarity(self):
        """Test topic similarity calculation."""
        topics1 = ['topic1', 'topic2', 'topic3']
        topics2 = ['topic2', 'topic3', 'topic4']
        similarity = self.calc.topic_similarity(topics1, topics2)
        # Intersection: {topic2, topic3} (2), Union: 4
        assert similarity == pytest.approx(0.5)

    def test_entity_similarity(self):
        """Test entity similarity calculation."""
        entities1 = ['Person1', 'Org1', 'Location1']
        entities2 = ['Person1', 'Org2', 'Location1']
        similarity = self.calc.entity_similarity(entities1, entities2)
        # Intersection: {Person1, Location1} (2), Union: 4 (Person1, Org1, Org2, Location1)
        assert similarity == pytest.approx(2.0 / 4.0)

    def test_multi_signal_similarity(self):
        """Test multi-signal similarity calculation."""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]  # Identical
        topics1 = ['topic1', 'topic2']
        topics2 = ['topic2', 'topic3']
        entities1 = ['entity1']
        entities2 = ['entity1']

        weighted_sim, breakdown = self.calc.multi_signal_similarity(
            emb1, emb2, topics1, topics2, entities1, entities2
        )

        # Embedding similarity: 1.0
        # Topic similarity: 0.333... (1/3)
        # Entity similarity: 1.0
        # Weighted: 0.6 * 1.0 + 0.3 * 0.333... + 0.1 * 1.0
        expected = 0.6 * 1.0 + 0.3 * (1.0 / 3.0) + 0.1 * 1.0
        assert weighted_sim == pytest.approx(expected)

        # Check breakdown
        assert breakdown['embedding_similarity'] == pytest.approx(1.0)
        assert breakdown['topic_similarity'] == pytest.approx(1.0 / 3.0)
        assert breakdown['entity_similarity'] == pytest.approx(1.0)

    def test_find_similar(self):
        """Test finding similar items."""
        query = [1.0, 0.0, 0.0]
        candidates = {
            'id1': [1.0, 0.0, 0.0],  # Identical (similarity: 1.0)
            'id2': [0.9, 0.1, 0.0],  # Similar (similarity: ~0.99)
            'id3': [0.0, 1.0, 0.0],  # Orthogonal (similarity: 0.0)
            'id4': [0.5, 0.5, 0.0],  # Moderate (similarity: ~0.71)
        }

        results = self.calc.find_similar(
            query,
            candidates,
            top_k=3,
            threshold=0.5
        )

        # Should return top 3 above threshold (excluding orthogonal)
        assert len(results) == 3
        assert results[0].content_id == 'id1'
        assert results[0].similarity == pytest.approx(1.0)

    def test_batch_similarity(self):
        """Test batch similarity calculation."""
        query_data = {
            'embedding': [1.0, 0.0, 0.0],
            'topics': ['topic1', 'topic2'],
            'entities': ['entity1']
        }

        candidates = {
            'id1': {
                'embedding': [1.0, 0.0, 0.0],
                'topics': ['topic1', 'topic2'],
                'entities': ['entity1']
            },
            'id2': {
                'embedding': [0.0, 1.0, 0.0],
                'topics': ['topic3'],
                'entities': ['entity2']
            }
        }

        results = self.calc.batch_similarity(
            'query_id',
            query_data,
            candidates,
            top_k=5,
            threshold=0.5,
            use_multi_signal=True
        )

        # Should find id1 (high similarity) but not id2 (low similarity)
        assert len(results) >= 1
        assert results[0].content_id == 'id1'
        assert results[0].similarity > 0.8
