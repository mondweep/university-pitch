"""
Tests for Topic Clustering functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lbs-knowledge-graph'))

from src.enrichment.topic_clusterer import TopicClusterer, TopicCluster
from src.enrichment.topic_models import Topic, TopicCategory


class TestClusteringInitialization:
    """Test topic clusterer initialization."""

    @pytest.fixture
    def sample_topics(self):
        return [Topic(f"t{i}", f"Topic {i}", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, []) 
                for i in range(10)]

    def test_initialization(self, sample_topics):
        """Test clusterer initialization."""
        embedding_fn = lambda text: [0.1] * 1536
        clusterer = TopicClusterer(sample_topics, embedding_fn, min_clusters=3, max_clusters=5)
        
        assert clusterer.min_clusters == 3
        assert clusterer.max_clusters == 5
        assert len(clusterer.topics) == 10


class TestEmbeddingGeneration:
    """Test embedding generation for topics."""

    @pytest.fixture
    def clusterer(self):
        topics = [
            Topic("t1", "Finance MBA", TopicCategory.ACADEMIC_PROGRAMMES, 0.9, [], "Finance MBA programme"),
            Topic("t2", "Marketing Strategy", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, [], "Marketing courses")
        ]
        embedding_fn = lambda text: [hash(text) % 100 / 100.0] * 10
        return TopicClusterer(topics, embedding_fn)

    def test_generate_embeddings(self, clusterer):
        """Test embedding generation for all topics."""
        clusterer.generate_embeddings()
        
        assert len(clusterer.embeddings) == 2
        assert all(isinstance(emb, list) for emb in clusterer.embeddings.values())


class TestOptimalClusterCount:
    """Test optimal cluster count selection."""

    @pytest.fixture
    def clusterer_with_embeddings(self):
        topics = [Topic(f"t{i}", f"Topic {i}", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, []) 
                  for i in range(20)]
        embedding_fn = lambda text: list(np.random.rand(10))
        clusterer = TopicClusterer(topics, embedding_fn, min_clusters=3, max_clusters=6)
        clusterer.generate_embeddings()
        return clusterer

    def test_find_optimal_clusters(self, clusterer_with_embeddings):
        """Test finding optimal number of clusters."""
        embeddings_matrix = np.array(list(clusterer_with_embeddings.embeddings.values()))
        
        optimal = clusterer_with_embeddings.find_optimal_clusters(embeddings_matrix)
        
        assert 3 <= optimal <= 6


class TestTopicClustering:
    """Test topic clustering algorithm."""

    @pytest.fixture
    def clusterer(self):
        topics = [
            # Finance cluster
            Topic("t1", "Finance MBA", TopicCategory.ACADEMIC_PROGRAMMES, 0.9, []),
            Topic("t2", "Investment Banking", TopicCategory.ACADEMIC_PROGRAMMES, 0.85, []),
            # Marketing cluster
            Topic("t3", "Marketing Strategy", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, []),
            Topic("t4", "Digital Marketing", TopicCategory.ACADEMIC_PROGRAMMES, 0.75, []),
            # Leadership cluster
            Topic("t5", "Leadership", TopicCategory.STUDENT_LIFE, 0.8, []),
            Topic("t6", "Team Management", TopicCategory.STUDENT_LIFE, 0.75, [])
        ]
        
        def embedding_fn(text):
            # Simple embedding based on keywords
            if "finance" in text.lower() or "investment" in text.lower():
                return [1.0, 0.0, 0.0, 0.0, 0.0]
            elif "marketing" in text.lower():
                return [0.0, 1.0, 0.0, 0.0, 0.0]
            elif "leadership" in text.lower() or "team" in text.lower():
                return [0.0, 0.0, 1.0, 0.0, 0.0]
            return [0.0, 0.0, 0.0, 1.0, 0.0]
        
        return TopicClusterer(topics, embedding_fn, min_clusters=2, max_clusters=4)

    def test_cluster_topics(self, clusterer):
        """Test clustering topics into groups."""
        clusters = clusterer.cluster_topics(n_clusters=3)
        
        assert len(clusters) == 3
        assert all(isinstance(cluster, TopicCluster) for cluster in clusters.values())
        # Total topics should be preserved
        total_topics = sum(len(cluster.topics) for cluster in clusters.values())
        assert total_topics == 6


class TestClusterNaming:
    """Test cluster naming based on topics."""

    @pytest.fixture
    def clusterer(self):
        topics = [Topic(f"t{i}", f"Topic {i}", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, []) 
                  for i in range(5)]
        embedding_fn = lambda text: [0.1] * 10
        return TopicClusterer(topics, embedding_fn)

    def test_name_cluster(self, clusterer):
        """Test generating cluster name from topics."""
        cluster_topics = [
            Topic("t1", "Finance MBA Programme", TopicCategory.ACADEMIC_PROGRAMMES, 0.9, []),
            Topic("t2", "Finance Investment", TopicCategory.ACADEMIC_PROGRAMMES, 0.85, []),
            Topic("t3", "Finance Research", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, [])
        ]
        
        name = clusterer.name_cluster(cluster_topics)
        
        # Should contain "Finance" as it's most common
        assert "finance" in name.lower()


class TestRepresentativeTopics:
    """Test getting representative topics from cluster."""

    @pytest.fixture
    def clusterer(self):
        topics = [Topic(f"t{i}", f"Topic {i}", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, []) 
                  for i in range(5)]
        embedding_fn = lambda text: [0.1] * 10
        return TopicClusterer(topics, embedding_fn)

    def test_get_representative_topics(self, clusterer):
        """Test getting most representative topics."""
        cluster_topics = [
            Topic("t1", "Topic 1", TopicCategory.ACADEMIC_PROGRAMMES, 0.9, [], frequency=10),
            Topic("t2", "Topic 2", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, [], frequency=5),
            Topic("t3", "Topic 3", TopicCategory.ACADEMIC_PROGRAMMES, 0.7, [], frequency=3)
        ]
        
        representative = clusterer._get_representative_topics(cluster_topics, top_n=2)
        
        assert len(representative) == 2
        assert representative[0] == "Topic 1"  # Highest importance & frequency


class TestKeywordExtraction:
    """Test keyword extraction from topic names."""

    @pytest.fixture
    def clusterer(self):
        topics = [Topic(f"t{i}", f"Topic {i}", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, []) 
                  for i in range(5)]
        embedding_fn = lambda text: [0.1] * 10
        return TopicClusterer(topics, embedding_fn)

    def test_extract_keywords(self, clusterer):
        """Test extracting keywords from topics."""
        cluster_topics = [
            Topic("t1", "MBA Finance Programme", TopicCategory.ACADEMIC_PROGRAMMES, 0.9, []),
            Topic("t2", "Finance Investment Banking", TopicCategory.ACADEMIC_PROGRAMMES, 0.85, []),
            Topic("t3", "Corporate Finance", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, [])
        ]
        
        keywords = clusterer._extract_keywords(cluster_topics, top_n=3)
        
        assert "finance" in keywords  # Most common word
        assert len(keywords) <= 3


class TestTopicHierarchy:
    """Test building topic hierarchy."""

    @pytest.fixture
    def clusterer_with_clusters(self):
        topics = [
            Topic("t1", "Topic 1", TopicCategory.ACADEMIC_PROGRAMMES, 0.9, [], frequency=10),
            Topic("t2", "Topic 2", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, [], frequency=5),
            Topic("t3", "Topic 3", TopicCategory.ACADEMIC_PROGRAMMES, 0.7, [], frequency=3),
            Topic("t4", "Topic 4", TopicCategory.RESEARCH_AREAS, 0.6, [], frequency=2)
        ]
        
        embedding_fn = lambda text: list(np.random.rand(5))
        clusterer = TopicClusterer(topics, embedding_fn, min_clusters=2, max_clusters=2)
        clusterer.generate_embeddings()
        clusterer.cluster_topics(n_clusters=2)
        
        return clusterer

    def test_build_hierarchy(self, clusterer_with_clusters):
        """Test building 3-level topic hierarchy."""
        hierarchy = clusterer_with_clusters.build_topic_hierarchy()
        
        assert "root" in hierarchy
        assert "primary" in hierarchy
        assert "specific" in hierarchy
        assert len(hierarchy["root"]) == 2  # 2 clusters

    def test_hierarchy_levels(self, clusterer_with_clusters):
        """Test hierarchy has correct levels."""
        hierarchy = clusterer_with_clusters.build_topic_hierarchy()
        
        # Root topics (level 0)
        assert all(t["level"] == 0 for t in hierarchy["root"])
        # Primary topics (level 1)
        assert all(t["level"] == 1 for t in hierarchy["primary"])
        # Specific topics (level 2)
        assert all(t["level"] == 2 for t in hierarchy["specific"])


class TestClusterStatistics:
    """Test cluster statistics."""

    @pytest.fixture
    def clusterer_with_clusters(self):
        topics = [Topic(f"t{i}", f"Topic {i}", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, []) 
                  for i in range(12)]
        embedding_fn = lambda text: list(np.random.rand(5))
        clusterer = TopicClusterer(topics, embedding_fn, min_clusters=3, max_clusters=3)
        clusterer.generate_embeddings()
        clusterer.cluster_topics(n_clusters=3)
        return clusterer

    def test_get_cluster_stats(self, clusterer_with_clusters):
        """Test cluster statistics calculation."""
        stats = clusterer_with_clusters.get_cluster_stats()
        
        assert "n_clusters" in stats
        assert "total_topics" in stats
        assert "avg_cluster_size" in stats
        assert stats["n_clusters"] == 3
        assert stats["total_topics"] == 12


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
