"""
Tests for Topic Extraction and Analysis functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lbs-knowledge-graph'))
sys.path.insert(0, os.path.dirname(__file__))

from src.enrichment.topic_analysis import TopicAnalyzer, TopicInsight
from src.enrichment.topic_models import Topic, TopicCategory
from fixtures.ground_truth_topics import GROUND_TRUTH_TOPICS, validate_topic_extraction


class TestTopicFrequencyDistribution:
    """Test topic frequency calculations."""

    @pytest.fixture
    def sample_topics(self):
        """Create sample topics."""
        return [
            Topic("t1", "Finance", TopicCategory.ACADEMIC_PROGRAMMES, 0.9, ["finance"]),
            Topic("t2", "MBA", TopicCategory.ACADEMIC_PROGRAMMES, 0.85, ["mba"]),
            Topic("t3", "Research", TopicCategory.RESEARCH_AREAS, 0.8, ["research"])
        ]

    @pytest.fixture
    def page_topics(self):
        """Create sample page-topic mappings."""
        return {
            "page1": ["t1", "t2"],
            "page2": ["t1", "t3"],
            "page3": ["t2"],
            "page4": ["t1", "t2", "t3"]
        }

    def test_frequency_calculation(self, sample_topics, page_topics):
        """Test topic frequency distribution calculation."""
        analyzer = TopicAnalyzer(sample_topics, page_topics)
        frequency = analyzer.calculate_frequency_distribution()

        assert frequency["t1"] == 3  # Finance appears 3 times
        assert frequency["t2"] == 3  # MBA appears 3 times
        assert frequency["t3"] == 2  # Research appears 2 times

    def test_frequency_empty_pages(self, sample_topics):
        """Test frequency with no pages."""
        analyzer = TopicAnalyzer(sample_topics, {})
        frequency = analyzer.calculate_frequency_distribution()
        assert len(frequency) == 0


class TestTopicCoOccurrence:
    """Test topic co-occurrence matrix calculations."""

    @pytest.fixture
    def sample_topics(self):
        return [
            Topic("t1", "Finance", TopicCategory.ACADEMIC_PROGRAMMES, 0.9, []),
            Topic("t2", "MBA", TopicCategory.ACADEMIC_PROGRAMMES, 0.85, []),
            Topic("t3", "Research", TopicCategory.RESEARCH_AREAS, 0.8, [])
        ]

    @pytest.fixture
    def page_topics(self):
        return {
            "page1": ["t1", "t2"],
            "page2": ["t1", "t2"],
            "page3": ["t2", "t3"],
            "page4": ["t1", "t2", "t3"]
        }

    def test_co_occurrence_calculation(self, sample_topics, page_topics):
        """Test co-occurrence matrix calculation."""
        analyzer = TopicAnalyzer(sample_topics, page_topics)
        co_occurrence = analyzer.calculate_co_occurrence_matrix(min_support=2)

        # t1 and t2 appear together 3 times
        assert co_occurrence.get(("t1", "t2"), 0) == 3
        # t2 and t3 appear together 2 times
        assert co_occurrence.get(("t2", "t3"), 0) == 2

    def test_min_support_filtering(self, sample_topics, page_topics):
        """Test minimum support filtering."""
        analyzer = TopicAnalyzer(sample_topics, page_topics)
        
        # High min_support should filter out low co-occurrences
        co_occurrence = analyzer.calculate_co_occurrence_matrix(min_support=3)
        assert len(co_occurrence) == 1  # Only t1-t2 with count 3


class TestTrendingTopics:
    """Test trending topic identification."""

    @pytest.fixture
    def trending_setup(self):
        topics = [
            Topic("t1", "Finance", TopicCategory.ACADEMIC_PROGRAMMES, 0.9, []),
            Topic("t2", "MBA", TopicCategory.ACADEMIC_PROGRAMMES, 0.85, []),
            Topic("t3", "Alumni", TopicCategory.STUDENT_LIFE, 0.7, [])
        ]
        page_topics = {
            f"page{i}": ["t1"] for i in range(10)  # Finance very frequent
        } | {
            f"page{i}": ["t2"] for i in range(10, 15)  # MBA moderately frequent
        } | {
            "page15": ["t3"]  # Alumni infrequent
        }
        return topics, page_topics

    def test_trending_identification(self, trending_setup):
        """Test identification of trending topics."""
        topics, page_topics = trending_setup
        analyzer = TopicAnalyzer(topics, page_topics)
        
        trending = analyzer.identify_trending_topics(top_n=3)
        
        assert len(trending) == 3
        # Top trending should be Finance (high frequency * high importance)
        assert trending[0].topic_name == "Finance"
        assert trending[0].frequency == 10
        assert trending[0].trend in ["rising", "stable"]

    def test_trend_classification(self, trending_setup):
        """Test trend classification (rising/stable/declining)."""
        topics, page_topics = trending_setup
        analyzer = TopicAnalyzer(topics, page_topics)
        
        trending = analyzer.identify_trending_topics(top_n=3)
        
        # Check trend classifications exist
        trends = [t.trend for t in trending]
        assert all(trend in ["rising", "stable", "declining"] for trend in trends)


class TestTopicCoverage:
    """Test topic coverage metrics."""

    @pytest.fixture
    def coverage_setup(self):
        topics = [Topic(f"t{i}", f"Topic{i}", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, []) 
                  for i in range(10)]
        page_topics = {
            "page1": ["t0", "t1", "t2"],
            "page2": ["t0"],
            "page3": ["t1", "t2", "t3", "t4"],
            "page4": []  # No topics
        }
        return topics, page_topics

    def test_coverage_calculation(self, coverage_setup):
        """Test topic coverage metrics calculation."""
        topics, page_topics = coverage_setup
        analyzer = TopicAnalyzer(topics, page_topics)
        
        coverage = analyzer.calculate_topic_coverage()
        
        assert coverage["total_pages"] == 4
        assert coverage["total_topics"] == 10
        assert coverage["avg_topics_per_page"] == 2.0  # (3+1+4+0)/4
        assert coverage["pages_without_topics"] == 1

    def test_empty_graph_coverage(self):
        """Test coverage with no pages."""
        analyzer = TopicAnalyzer([], {})
        coverage = analyzer.calculate_topic_coverage()
        
        assert coverage["total_pages"] == 0
        assert coverage["avg_topics_per_page"] == 0


class TestTopicReport:
    """Test comprehensive topic report generation."""

    @pytest.fixture
    def report_setup(self):
        topics = [
            Topic("t1", "Finance", TopicCategory.ACADEMIC_PROGRAMMES, 0.9, []),
            Topic("t2", "MBA", TopicCategory.ACADEMIC_PROGRAMMES, 0.85, []),
            Topic("t3", "Research", TopicCategory.RESEARCH_AREAS, 0.8, [])
        ]
        page_topics = {
            "page1": ["t1", "t2"],
            "page2": ["t1", "t3"],
            "page3": ["t2", "t3"]
        }
        return topics, page_topics

    def test_report_generation(self, report_setup):
        """Test complete topic report generation."""
        topics, page_topics = report_setup
        analyzer = TopicAnalyzer(topics, page_topics)
        
        report = analyzer.generate_topic_report()
        
        assert "summary" in report
        assert "frequency_distribution" in report
        assert "category_distribution" in report
        assert "co_occurrence" in report
        assert "trending_topics" in report
        assert "coverage" in report

    def test_report_summary(self, report_setup):
        """Test report summary section."""
        topics, page_topics = report_setup
        analyzer = TopicAnalyzer(topics, page_topics)
        
        report = analyzer.generate_topic_report()
        summary = report["summary"]
        
        assert summary["total_topics"] == 3
        assert summary["total_pages"] == 3
        assert summary["avg_topics_per_page"] == 2.0


class TestHeatmapExport:
    """Test heatmap data export for visualization."""

    @pytest.fixture
    def heatmap_setup(self):
        topics = [Topic(f"t{i}", f"Topic{i}", TopicCategory.ACADEMIC_PROGRAMMES, 0.8, []) 
                  for i in range(5)]
        page_topics = {
            f"page{i}": [f"t{j}" for j in range(3)] for i in range(10)
        }
        return topics, page_topics

    def test_heatmap_export(self, heatmap_setup):
        """Test heatmap data export."""
        topics, page_topics = heatmap_setup
        analyzer = TopicAnalyzer(topics, page_topics)
        
        topic_names, matrix = analyzer.export_heatmap_data(top_n=5)
        
        assert len(topic_names) == 5
        assert matrix.shape == (5, 5)
        # Diagonal should have frequencies
        assert all(matrix[i, i] > 0 for i in range(5))


class TestGroundTruthValidation:
    """Test topic extraction against ground truth."""

    def test_ground_truth_validation_structure(self):
        """Test ground truth data structure."""
        assert len(GROUND_TRUTH_TOPICS) >= 5
        for item in GROUND_TRUTH_TOPICS:
            assert "page_id" in item
            assert "expected_topics" in item
            assert "expected_topic_count_min" in item

    def test_validate_topic_extraction_function(self):
        """Test validation function."""
        # Test valid extraction
        validation = validate_topic_extraction(
            "gt_topic_001",
            [{"name": "MBA Programme"}, {"name": "Business Education"}, {"name": "Career Development"}]
        )
        assert "valid" in validation
        assert "recall" in validation

    def test_topic_count_validation(self):
        """Test topic count falls within expected range."""
        extracted = [{"name": "MBA Programme"}, {"name": "Business Education"}]
        validation = validate_topic_extraction("gt_topic_001", extracted)
        
        # Should validate against expected count range
        assert "topic_count_valid" in validation

    def test_recall_calculation(self):
        """Test recall calculation in validation."""
        # Perfect match
        validation = validate_topic_extraction(
            "gt_topic_001",
            [{"name": "MBA Programme"}, {"name": "Business Education"}, {"name": "Career Development"}]
        )
        assert validation["recall"] == 1.0

        # Partial match
        validation = validate_topic_extraction(
            "gt_topic_001",
            [{"name": "MBA Programme"}]
        )
        assert 0 < validation["recall"] < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
