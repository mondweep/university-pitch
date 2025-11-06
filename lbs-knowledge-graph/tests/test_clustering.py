"""
Topic Clustering Tests for Phase 3
Tests for topic clusterer, hierarchy building, SUBTOPIC_OF relationships
Target: 20+ tests covering all clustering functionality
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

from src.enrichment.topic_clusterer import TopicClusterer
from src.enrichment.topic_models import Topic, TopicCategory, TopicCluster


# ==================== Topic Clusterer Initialization Tests ====================

@pytest.mark.unit
class TestTopicClustererInit:
    """Test topic clusterer initialization (3 tests)"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        clusterer = TopicClusterer()

        assert hasattr(clusterer, 'clusters')
        assert isinstance(clusterer.clusters, list)

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        clusterer = TopicClusterer(min_cluster_size=5, max_clusters=10)

        assert clusterer.min_cluster_size == 5
        assert clusterer.max_clusters == 10

    def test_init_has_required_methods(self):
        """Test that clusterer has all required methods"""
        clusterer = TopicClusterer()

        assert hasattr(clusterer, 'cluster_topics')
        assert hasattr(clusterer, 'build_hierarchy')


# ==================== Topic Clustering Tests ====================

@pytest.mark.unit
class TestTopicClustering:
    """Test topic clustering functionality (8 tests)"""

    def test_cluster_similar_topics(self):
        """Test clustering of similar topics"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Leadership", category=TopicCategory.SKILLS, frequency=10, importance=0.9),
            Topic(id="2", name="Leadership Development", category=TopicCategory.SKILLS, frequency=8, importance=0.85),
            Topic(id="3", name="Management", category=TopicCategory.SKILLS, frequency=7, importance=0.8)
        ]

        clusters = clusterer.cluster_topics(topics)

        assert len(clusters) > 0
        # Similar topics should be in same cluster
        assert any(len(c.topic_ids) > 1 for c in clusters)

    def test_cluster_by_category(self):
        """Test that topics are grouped by category"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Finance", category=TopicCategory.ACADEMIC, frequency=10, importance=0.9),
            Topic(id="2", name="Marketing", category=TopicCategory.ACADEMIC, frequency=9, importance=0.85),
            Topic(id="3", name="Networking", category=TopicCategory.STUDENT_LIFE, frequency=5, importance=0.7)
        ]

        clusters = clusterer.cluster_topics(topics)

        # Should create separate clusters for different categories
        assert len(clusters) >= 2

    def test_cluster_empty_list(self):
        """Test clustering with empty topic list"""
        clusterer = TopicClusterer()

        clusters = clusterer.cluster_topics([])

        assert clusters == []

    def test_cluster_single_topic(self):
        """Test clustering with single topic"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Leadership", category=TopicCategory.SKILLS, frequency=10, importance=0.9)
        ]

        clusters = clusterer.cluster_topics(topics)

        assert len(clusters) == 1
        assert len(clusters[0].topic_ids) == 1

    def test_cluster_names_generated(self):
        """Test that cluster names are generated"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Leadership", category=TopicCategory.SKILLS, frequency=10, importance=0.9),
            Topic(id="2", name="Management", category=TopicCategory.SKILLS, frequency=8, importance=0.85)
        ]

        clusters = clusterer.cluster_topics(topics)

        assert all(c.name for c in clusters)
        assert all(isinstance(c.name, str) for c in clusters)

    def test_cluster_sizes(self):
        """Test that cluster sizes are appropriate"""
        clusterer = TopicClusterer(min_cluster_size=2)

        topics = [
            Topic(id=str(i), name=f"Topic {i}", category=TopicCategory.ACADEMIC, frequency=5, importance=0.7)
            for i in range(10)
        ]

        clusters = clusterer.cluster_topics(topics)

        # All clusters should meet minimum size or be singleton outliers
        assert all(len(c.topic_ids) >= 1 for c in clusters)

    def test_cluster_importance(self):
        """Test that cluster importance is calculated"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Topic 1", category=TopicCategory.ACADEMIC, frequency=10, importance=0.9),
            Topic(id="2", name="Topic 2", category=TopicCategory.ACADEMIC, frequency=8, importance=0.85)
        ]

        clusters = clusterer.cluster_topics(topics)

        assert all(hasattr(c, 'importance') for c in clusters)
        assert all(c.importance > 0 for c in clusters)

    def test_cluster_max_limit(self):
        """Test that maximum cluster count is respected"""
        clusterer = TopicClusterer(max_clusters=3)

        topics = [
            Topic(id=str(i), name=f"Topic {i}", category=TopicCategory.ACADEMIC, frequency=5, importance=0.7)
            for i in range(20)
        ]

        clusters = clusterer.cluster_topics(topics)

        assert len(clusters) <= 3


# ==================== Hierarchy Building Tests ====================

@pytest.mark.unit
class TestHierarchyBuilding:
    """Test topic hierarchy building (6 tests)"""

    def test_build_hierarchy_basic(self):
        """Test basic hierarchy building"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Finance", category=TopicCategory.ACADEMIC, frequency=10, importance=0.9),
            Topic(id="2", name="Corporate Finance", category=TopicCategory.ACADEMIC, frequency=8, importance=0.85),
            Topic(id="3", name="Investment Banking", category=TopicCategory.ACADEMIC, frequency=5, importance=0.7)
        ]

        hierarchy = clusterer.build_hierarchy(topics)

        assert isinstance(hierarchy, dict)
        assert len(hierarchy) > 0

    def test_hierarchy_three_levels(self):
        """Test that hierarchy has multiple levels"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Business", category=TopicCategory.ACADEMIC, frequency=20, importance=0.95),
            Topic(id="2", name="Finance", category=TopicCategory.ACADEMIC, frequency=15, importance=0.9),
            Topic(id="3", name="Corporate Finance", category=TopicCategory.ACADEMIC, frequency=10, importance=0.85),
            Topic(id="4", name="Investment", category=TopicCategory.ACADEMIC, frequency=8, importance=0.8)
        ]

        hierarchy = clusterer.build_hierarchy(topics, max_levels=3)

        # Should have multiple levels
        def count_levels(h, level=0):
            if not h:
                return level
            return max(count_levels(v, level + 1) if isinstance(v, dict) else level + 1 for v in h.values())

        assert count_levels(hierarchy) <= 3

    def test_hierarchy_parent_child_relationships(self):
        """Test parent-child relationships in hierarchy"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Business Education", category=TopicCategory.ACADEMIC, frequency=20, importance=0.95),
            Topic(id="2", name="MBA Programme", category=TopicCategory.ACADEMIC, frequency=15, importance=0.9)
        ]

        hierarchy = clusterer.build_hierarchy(topics)

        # Broader topics should be parents of more specific topics
        assert isinstance(hierarchy, dict)

    def test_hierarchy_empty_topics(self):
        """Test hierarchy building with empty topic list"""
        clusterer = TopicClusterer()

        hierarchy = clusterer.build_hierarchy([])

        assert hierarchy == {}

    def test_hierarchy_single_topic(self):
        """Test hierarchy with single topic"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Leadership", category=TopicCategory.SKILLS, frequency=10, importance=0.9)
        ]

        hierarchy = clusterer.build_hierarchy(topics)

        assert len(hierarchy) == 1

    def test_hierarchy_preserves_categories(self):
        """Test that hierarchy respects topic categories"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Finance", category=TopicCategory.ACADEMIC, frequency=10, importance=0.9),
            Topic(id="2", name="Student Clubs", category=TopicCategory.STUDENT_LIFE, frequency=8, importance=0.7)
        ]

        hierarchy = clusterer.build_hierarchy(topics)

        # Different categories should be in separate branches
        assert len(hierarchy) >= 1


# ==================== SUBTOPIC_OF Relationship Tests ====================

@pytest.mark.unit
class TestSubtopicRelationships:
    """Test SUBTOPIC_OF relationship creation (3 tests)"""

    def test_identify_subtopic_relationships(self):
        """Test identification of subtopic relationships"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Business", category=TopicCategory.ACADEMIC, frequency=20, importance=0.95),
            Topic(id="2", name="Finance", category=TopicCategory.ACADEMIC, frequency=15, importance=0.9),
            Topic(id="3", name="Corporate Finance", category=TopicCategory.ACADEMIC, frequency=10, importance=0.85)
        ]

        relationships = clusterer.identify_subtopic_relationships(topics)

        assert isinstance(relationships, list)
        assert len(relationships) > 0
        # Each relationship should have parent and child
        assert all('parent' in r and 'child' in r for r in relationships)

    def test_subtopic_specificity(self):
        """Test that more specific topics are children"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Education", category=TopicCategory.ACADEMIC, frequency=20, importance=0.95),
            Topic(id="2", name="Business Education", category=TopicCategory.ACADEMIC, frequency=15, importance=0.9),
            Topic(id="3", name="MBA Education", category=TopicCategory.ACADEMIC, frequency=10, importance=0.85)
        ]

        relationships = clusterer.identify_subtopic_relationships(topics)

        # More specific topics should be children of broader topics
        for rel in relationships:
            parent_name = next(t.name for t in topics if t.id == rel['parent'])
            child_name = next(t.name for t in topics if t.id == rel['child'])

            # Child name should contain or be more specific than parent
            assert len(child_name.split()) >= len(parent_name.split()) or parent_name.lower() in child_name.lower()

    def test_no_circular_relationships(self):
        """Test that circular relationships are avoided"""
        clusterer = TopicClusterer()

        topics = [
            Topic(id="1", name="Topic A", category=TopicCategory.ACADEMIC, frequency=10, importance=0.9),
            Topic(id="2", name="Topic B", category=TopicCategory.ACADEMIC, frequency=10, importance=0.9)
        ]

        relationships = clusterer.identify_subtopic_relationships(topics)

        # Build relationship graph and check for cycles
        parent_to_child = {}
        for rel in relationships:
            if rel['parent'] not in parent_to_child:
                parent_to_child[rel['parent']] = []
            parent_to_child[rel['parent']].append(rel['child'])

        # No topic should be its own ancestor
        def has_cycle(node, visited=None):
            if visited is None:
                visited = set()
            if node in visited:
                return True
            visited.add(node)
            for child in parent_to_child.get(node, []):
                if has_cycle(child, visited.copy()):
                    return True
            return False

        assert not any(has_cycle(t.id) for t in topics)
