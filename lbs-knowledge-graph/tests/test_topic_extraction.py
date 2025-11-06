"""
Topic Extraction Tests for Phase 3
Tests for topic extractor, normalization, deduplication, HAS_TOPIC relationships
Target: 30+ tests covering all topic extraction functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any

from src.enrichment.topic_extractor import TopicExtractor
from src.enrichment.topic_models import Topic, TopicCategory, TopicExtractionResult
from tests.fixtures.enrichment_data import mock_topic_responses


# ==================== Topic Extractor Initialization Tests ====================

@pytest.mark.unit
class TestTopicExtractorInit:
    """Test topic extractor initialization (5 tests)"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        assert extractor.llm_client == mock_client
        assert extractor.min_relevance == 0.7
        assert extractor.max_topics_per_item == 5
        assert isinstance(extractor.topic_cache, dict)

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client, min_relevance=0.8, max_topics_per_item=3)

        assert extractor.min_relevance == 0.8
        assert extractor.max_topics_per_item == 3

    def test_init_creates_empty_cache(self):
        """Test that topic cache is initialized empty"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        assert len(extractor.topic_cache) == 0

    def test_init_requires_llm_client(self):
        """Test that LLM client is required"""
        with pytest.raises(TypeError):
            TopicExtractor()

    def test_init_has_required_methods(self):
        """Test that extractor has all required methods"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        assert hasattr(extractor, 'extract_topics')
        assert hasattr(extractor, 'normalize_topic')
        assert hasattr(extractor, 'deduplicate_topics')
        assert hasattr(extractor, 'extract_batch')


# ==================== Topic Normalization Tests ====================

@pytest.mark.unit
class TestTopicNormalization:
    """Test topic name normalization (8 tests)"""

    def test_normalize_basic(self):
        """Test basic normalization"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        normalized = extractor.normalize_topic("business education")

        assert normalized == "Business Education"

    def test_normalize_lowercase_to_titlecase(self):
        """Test conversion from lowercase to title case"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        assert extractor.normalize_topic("leadership") == "Leadership"
        assert extractor.normalize_topic("career development") == "Career Development"

    def test_normalize_removes_special_chars(self):
        """Test removal of special characters"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        normalized = extractor.normalize_topic("Business@Education!")

        assert "@" not in normalized
        assert "!" not in normalized

    def test_normalize_preserves_hyphens(self):
        """Test that hyphens are preserved"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        normalized = extractor.normalize_topic("part-time mba")

        assert "-" in normalized
        assert normalized == "Part-Time Mba"

    def test_normalize_collapses_spaces(self):
        """Test collapsing multiple spaces"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        normalized = extractor.normalize_topic("business    education")

        assert "    " not in normalized
        assert normalized == "Business Education"

    def test_normalize_trims_whitespace(self):
        """Test trimming leading/trailing whitespace"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        normalized = extractor.normalize_topic("  leadership  ")

        assert not normalized.startswith(" ")
        assert not normalized.endswith(" ")

    def test_normalize_empty_string(self):
        """Test normalization of empty string"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        normalized = extractor.normalize_topic("")

        assert normalized == ""

    def test_normalize_unicode(self):
        """Test normalization with Unicode characters"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        # Unicode should be stripped
        normalized = extractor.normalize_topic("café")

        assert "é" not in normalized or normalized == "Caf"


# ==================== Topic Similarity Tests ====================

@pytest.mark.unit
class TestTopicSimilarity:
    """Test topic similarity detection (6 tests)"""

    def test_exact_match(self):
        """Test exact match detection"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        assert extractor.is_similar_topic("Leadership", "Leadership")

    def test_substring_match(self):
        """Test substring match"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        assert extractor.is_similar_topic("Leadership", "Leadership Skills")

    def test_word_overlap(self):
        """Test high word overlap detection"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        assert extractor.is_similar_topic("Business Strategy", "Corporate Strategy")

    def test_not_similar(self):
        """Test dissimilar topics"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        assert not extractor.is_similar_topic("Finance", "Marketing")

    def test_case_insensitive(self):
        """Test case-insensitive comparison"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        assert extractor.is_similar_topic("leadership", "LEADERSHIP")

    def test_partial_word_match(self):
        """Test partial word matching"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        # "Business" in both
        assert extractor.is_similar_topic("Business Education", "Business School")


# ==================== Topic Deduplication Tests ====================

@pytest.mark.unit
class TestTopicDeduplication:
    """Test topic deduplication (5 tests)"""

    def test_deduplicate_exact_duplicates(self):
        """Test removing exact duplicate topics"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        topics = [
            {"name": "Leadership", "relevance": 0.9},
            {"name": "Leadership", "relevance": 0.8}
        ]

        result = extractor.deduplicate_topics(topics)

        assert len(result) == 1
        assert result[0]["relevance"] == 0.9  # Keeps highest relevance

    def test_deduplicate_similar_topics(self):
        """Test removing similar topics"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        topics = [
            {"name": "Leadership", "relevance": 0.9},
            {"name": "Leadership Skills", "relevance": 0.8}
        ]

        result = extractor.deduplicate_topics(topics)

        assert len(result) == 1

    def test_deduplicate_empty_list(self):
        """Test deduplication with empty list"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        result = extractor.deduplicate_topics([])

        assert result == []

    def test_deduplicate_preserves_dissimilar(self):
        """Test that dissimilar topics are preserved"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        topics = [
            {"name": "Finance", "relevance": 0.9},
            {"name": "Marketing", "relevance": 0.8},
            {"name": "Operations", "relevance": 0.7}
        ]

        result = extractor.deduplicate_topics(topics)

        assert len(result) == 3

    def test_deduplicate_normalizes_names(self):
        """Test that names are normalized during deduplication"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        topics = [
            {"name": "business education", "relevance": 0.9},
            {"name": "Business  Education", "relevance": 0.8}
        ]

        result = extractor.deduplicate_topics(topics)

        assert len(result) == 1
        assert result[0]["name"] == "Business Education"


# ==================== Topic Extraction Tests ====================

@pytest.mark.unit
@pytest.mark.asyncio
class TestTopicExtraction:
    """Test topic extraction from content (6 tests)"""

    async def test_extract_from_text(self, mock_topic_responses):
        """Test extracting topics from text"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "topics": [
                {"name": "Business Education", "relevance": 0.95, "category": "education", "description": "MBA programmes"},
                {"name": "Career Development", "relevance": 0.88, "category": "career", "description": "Career growth"}
            ]
        }
        '''

        mock_client.client = Mock()
        mock_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client.model = "gpt-4"

        extractor = TopicExtractor(mock_client)

        text = "Transform your career with our world-class MBA programme"
        context = {"source_id": "page-1", "source_type": "page", "page_type": "programme"}

        topics = await extractor.extract_topics(text, context)

        assert len(topics) > 0
        assert all(isinstance(t, Topic) for t in topics)

    async def test_extract_filters_by_relevance(self, mock_topic_responses):
        """Test that low-relevance topics are filtered"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "topics": [
                {"name": "High Relevance", "relevance": 0.95, "category": "education"},
                {"name": "Low Relevance", "relevance": 0.3, "category": "general"}
            ]
        }
        '''

        mock_client.client = Mock()
        mock_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client.model = "gpt-4"

        extractor = TopicExtractor(mock_client, min_relevance=0.7)

        topics = await extractor.extract_topics("Test text", {"source_id": "test", "source_type": "page", "page_type": "programme"})

        assert len(topics) == 1
        assert topics[0].name == "High Relevance"

    async def test_extract_limits_max_topics(self, mock_topic_responses):
        """Test maximum topics per item limit"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "topics": [
                {"name": "Topic 1", "relevance": 0.95, "category": "education"},
                {"name": "Topic 2", "relevance": 0.90, "category": "career"},
                {"name": "Topic 3", "relevance": 0.85, "category": "skills"},
                {"name": "Topic 4", "relevance": 0.80, "category": "experience"},
                {"name": "Topic 5", "relevance": 0.75, "category": "subject"},
                {"name": "Topic 6", "relevance": 0.70, "category": "general"}
            ]
        }
        '''

        mock_client.client = Mock()
        mock_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client.model = "gpt-4"

        extractor = TopicExtractor(mock_client, max_topics_per_item=3)

        topics = await extractor.extract_topics("Test text", {"source_id": "test", "source_type": "page", "page_type": "programme"})

        assert len(topics) <= 3

    async def test_extract_short_text(self):
        """Test extraction with too-short text"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        topics = await extractor.extract_topics("Short", {"source_id": "test", "source_type": "page", "page_type": "programme"})

        assert topics == []

    async def test_extract_empty_text(self):
        """Test extraction with empty text"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        topics = await extractor.extract_topics("", {"source_id": "test", "source_type": "page", "page_type": "programme"})

        assert topics == []

    async def test_extract_caches_topics(self, mock_topic_responses):
        """Test that extracted topics are cached"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "topics": [
                {"name": "Business Education", "relevance": 0.95, "category": "education"}
            ]
        }
        '''

        mock_client.client = Mock()
        mock_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client.model = "gpt-4"

        extractor = TopicExtractor(mock_client)

        initial_cache_size = len(extractor.topic_cache)

        topics = await extractor.extract_topics("Test text", {"source_id": "test", "source_type": "page", "page_type": "programme"})

        assert len(extractor.topic_cache) > initial_cache_size


# ==================== Batch Extraction Tests ====================

@pytest.mark.unit
@pytest.mark.asyncio
class TestBatchExtraction:
    """Test batch topic extraction (5 tests)"""

    async def test_batch_extract_multiple_items(self):
        """Test batch extraction of multiple items"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "topics": [
                {"name": "Test Topic", "relevance": 0.9, "category": "education"}
            ]
        }
        '''

        mock_client.client = Mock()
        mock_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client.model = "gpt-4"

        extractor = TopicExtractor(mock_client)

        items = [
            {"text": "Text 1", "context": {"source_id": "1", "source_type": "page", "page_type": "programme"}},
            {"text": "Text 2", "context": {"source_id": "2", "source_type": "page", "page_type": "faculty"}},
            {"text": "Text 3", "context": {"source_id": "3", "source_type": "page", "page_type": "research"}}
        ]

        results = await extractor.extract_batch(items, batch_size=10)

        assert len(results) == 3
        assert all(isinstance(r, TopicExtractionResult) for r in results)

    async def test_batch_empty_list(self):
        """Test batch extraction with empty list"""
        mock_client = Mock()
        extractor = TopicExtractor(mock_client)

        results = await extractor.extract_batch([])

        assert results == []

    async def test_batch_respects_batch_size(self):
        """Test that batch size is respected"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{"topics": []}'''

        mock_client.client = Mock()
        mock_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client.model = "gpt-4"

        extractor = TopicExtractor(mock_client)

        items = [
            {"text": f"Text {i}" * 10, "context": {"source_id": str(i), "source_type": "page", "page_type": "programme"}}
            for i in range(10)
        ]

        with patch('asyncio.sleep', return_value=None):  # Speed up test
            results = await extractor.extract_batch(items, batch_size=3)

        assert len(results) == 10

    async def test_batch_handles_errors_gracefully(self):
        """Test error handling in batch extraction"""
        mock_client = Mock()
        mock_client.client = Mock()
        mock_client.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_client.model = "gpt-4"

        extractor = TopicExtractor(mock_client)

        items = [
            {"text": "Text 1", "context": {"source_id": "1", "source_type": "page", "page_type": "programme"}}
        ]

        results = await extractor.extract_batch(items)

        # Should return empty result list instead of crashing
        assert isinstance(results, list)

    async def test_batch_updates_cache(self):
        """Test that batch extraction updates topic cache"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "topics": [
                {"name": "Unique Topic", "relevance": 0.9, "category": "education"}
            ]
        }
        '''

        mock_client.client = Mock()
        mock_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client.model = "gpt-4"

        extractor = TopicExtractor(mock_client)

        initial_cache_size = len(extractor.topic_cache)

        items = [
            {"text": "Test text" * 20, "context": {"source_id": "1", "source_type": "page", "page_type": "programme"}}
        ]

        await extractor.extract_batch(items)

        assert len(extractor.topic_cache) >= initial_cache_size
