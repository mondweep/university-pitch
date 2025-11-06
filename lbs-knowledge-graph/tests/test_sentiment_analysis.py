"""
Sentiment Analysis Tests for Phase 3
Tests for sentiment analyzer, batch processing, aggregation
Target: 25+ tests covering all sentiment analysis functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from src.enrichment.sentiment_analyzer import SentimentAnalyzer
from src.enrichment.models import SentimentScore, ContentItemWithSentiment
from tests.fixtures.enrichment_data import (
    mock_sentiment_responses,
    sample_content_items,
    expected_sentiment_results
)


# ==================== Sentiment Analyzer Initialization Tests ====================

@pytest.mark.unit
class TestSentimentAnalyzerInit:
    """Test sentiment analyzer initialization (5 tests)"""

    def test_init_with_llm_client(self):
        """Test initialization with LLM client"""
        mock_client = Mock()
        analyzer = SentimentAnalyzer(mock_client)

        assert analyzer.llm_client == mock_client
        assert isinstance(analyzer.cache, dict)
        assert len(analyzer.cache) == 0

    def test_init_creates_empty_cache(self):
        """Test that cache is initialized empty"""
        mock_client = Mock()
        analyzer = SentimentAnalyzer(mock_client)

        assert hasattr(analyzer, 'cache')
        assert len(analyzer.cache) == 0

    def test_init_requires_llm_client(self):
        """Test that LLM client is required"""
        with pytest.raises(TypeError):
            SentimentAnalyzer()

    def test_init_with_none_client(self):
        """Test initialization with None client"""
        analyzer = SentimentAnalyzer(None)
        assert analyzer.llm_client is None

    def test_analyzer_has_required_methods(self):
        """Test that analyzer has all required methods"""
        mock_client = Mock()
        analyzer = SentimentAnalyzer(mock_client)

        assert hasattr(analyzer, 'analyze_content_item')
        assert hasattr(analyzer, 'analyze_batch')
        assert hasattr(analyzer, 'aggregate_sentiment')


# ==================== Single Item Analysis Tests ====================

@pytest.mark.unit
@pytest.mark.asyncio
class TestSingleItemAnalysis:
    """Test single content item sentiment analysis (8 tests)"""

    async def test_analyze_positive_content(self, mock_sentiment_responses):
        """Test analyzing positive sentiment content"""
        mock_client = AsyncMock()
        mock_client.analyze_sentiment = AsyncMock(return_value=SentimentScore(
            polarity="positive",
            score=0.85,
            confidence=0.92
        ))

        analyzer = SentimentAnalyzer(mock_client)
        item = {
            "id": "test-1",
            "text": "Transform your career with our world-class MBA programme"
        }

        result = await analyzer.analyze_content_item(item)

        assert result.polarity == "positive"
        assert result.score > 0.7
        assert result.confidence > 0.8

    async def test_analyze_negative_content(self, mock_sentiment_responses):
        """Test analyzing negative sentiment content"""
        mock_client = AsyncMock()
        mock_client.analyze_sentiment = AsyncMock(return_value=SentimentScore(
            polarity="negative",
            score=-0.65,
            confidence=0.88
        ))

        analyzer = SentimentAnalyzer(mock_client)
        item = {
            "id": "test-2",
            "text": "High costs and demanding workload present significant challenges"
        }

        result = await analyzer.analyze_content_item(item)

        assert result.polarity == "negative"
        assert result.score < 0.4

    async def test_analyze_neutral_content(self, mock_sentiment_responses):
        """Test analyzing neutral sentiment content"""
        mock_client = AsyncMock()
        mock_client.analyze_sentiment = AsyncMock(return_value=SentimentScore(
            polarity="neutral",
            score=0.05,
            confidence=0.75
        ))

        analyzer = SentimentAnalyzer(mock_client)
        item = {
            "id": "test-3",
            "text": "The programme duration is 15-21 months"
        }

        result = await analyzer.analyze_content_item(item)

        assert result.polarity == "neutral"
        assert 0.4 <= result.score <= 0.6

    async def test_analyze_empty_text(self):
        """Test analyzing empty text"""
        mock_client = AsyncMock()
        analyzer = SentimentAnalyzer(mock_client)

        item = {"id": "test-4", "text": ""}
        result = await analyzer.analyze_content_item(item)

        assert result.polarity == "neutral"

    async def test_analyze_very_short_text(self):
        """Test analyzing very short text"""
        mock_client = AsyncMock()
        analyzer = SentimentAnalyzer(mock_client)

        item = {"id": "test-5", "text": "Hi"}
        result = await analyzer.analyze_content_item(item)

        assert result.polarity == "neutral"

    async def test_caching_works(self):
        """Test that results are cached"""
        mock_client = AsyncMock()
        mock_client.analyze_sentiment = AsyncMock(return_value=SentimentScore(
            polarity="positive",
            score=0.85,
            confidence=0.92
        ))

        analyzer = SentimentAnalyzer(mock_client)
        item = {"id": "test-6", "text": "Great programme"}

        # First call
        result1 = await analyzer.analyze_content_item(item)
        # Second call (should use cache)
        result2 = await analyzer.analyze_content_item(item)

        assert result1 == result2
        assert mock_client.analyze_sentiment.call_count == 1

    async def test_different_items_not_cached(self):
        """Test that different items don't share cache"""
        mock_client = AsyncMock()
        mock_client.analyze_sentiment = AsyncMock(side_effect=[
            SentimentScore(polarity="positive", score=0.85, confidence=0.92),
            SentimentScore(polarity="negative", score=-0.65, confidence=0.88)
        ])

        analyzer = SentimentAnalyzer(mock_client)

        item1 = {"id": "test-7", "text": "Great"}
        item2 = {"id": "test-8", "text": "Terrible"}

        result1 = await analyzer.analyze_content_item(item1)
        result2 = await analyzer.analyze_content_item(item2)

        assert result1.polarity == "positive"
        assert result2.polarity == "negative"
        assert mock_client.analyze_sentiment.call_count == 2

    async def test_returns_correct_data_structure(self):
        """Test that result has correct structure"""
        mock_client = AsyncMock()
        mock_client.analyze_sentiment = AsyncMock(return_value=SentimentScore(
            polarity="positive",
            score=0.85,
            confidence=0.92
        ))

        analyzer = SentimentAnalyzer(mock_client)
        item = {"id": "test-9", "text": "Test content"}

        result = await analyzer.analyze_content_item(item)

        assert hasattr(result, 'polarity')
        assert hasattr(result, 'score')
        assert hasattr(result, 'confidence')


# ==================== Batch Processing Tests ====================

@pytest.mark.unit
@pytest.mark.asyncio
class TestBatchProcessing:
    """Test batch sentiment analysis (7 tests)"""

    async def test_batch_process_multiple_items(self):
        """Test batch processing of multiple items"""
        mock_client = AsyncMock()
        mock_client.analyze_batch = AsyncMock(return_value=[
            SentimentScore(polarity="positive", score=0.85, confidence=0.92),
            SentimentScore(polarity="neutral", score=0.05, confidence=0.75),
            SentimentScore(polarity="negative", score=-0.65, confidence=0.88)
        ])

        analyzer = SentimentAnalyzer(mock_client)
        items = [
            {"id": "item-1", "text": "Great programme", "word_count": 2},
            {"id": "item-2", "text": "Programme details", "word_count": 2},
            {"id": "item-3", "text": "Expensive and difficult", "word_count": 3}
        ]

        results = await analyzer.analyze_batch(items)

        assert len(results) == 3
        assert all(isinstance(r, ContentItemWithSentiment) for r in results)

    async def test_batch_empty_list(self):
        """Test batch processing with empty list"""
        mock_client = AsyncMock()
        analyzer = SentimentAnalyzer(mock_client)

        results = await analyzer.analyze_batch([])

        assert results == []

    async def test_batch_single_item(self):
        """Test batch processing with single item"""
        mock_client = AsyncMock()
        mock_client.analyze_batch = AsyncMock(return_value=[
            SentimentScore(polarity="positive", score=0.85, confidence=0.92)
        ])

        analyzer = SentimentAnalyzer(mock_client)
        items = [{"id": "item-1", "text": "Test", "word_count": 1}]

        results = await analyzer.analyze_batch(items)

        assert len(results) == 1

    async def test_batch_respects_batch_size(self):
        """Test that batch size parameter is respected"""
        mock_client = AsyncMock()
        mock_client.analyze_batch = AsyncMock(return_value=[
            SentimentScore(polarity="neutral", score=0.0, confidence=0.8)
            for _ in range(10)
        ])

        analyzer = SentimentAnalyzer(mock_client)
        items = [
            {"id": f"item-{i}", "text": f"Text {i}", "word_count": 2}
            for i in range(10)
        ]

        results = await analyzer.analyze_batch(items, batch_size=5)

        assert len(results) == 10
        assert mock_client.analyze_batch.call_count == 2

    async def test_batch_progress_callback(self):
        """Test progress callback during batch processing"""
        mock_client = AsyncMock()
        mock_client.analyze_batch = AsyncMock(return_value=[
            SentimentScore(polarity="neutral", score=0.0, confidence=0.8)
            for _ in range(5)
        ])

        analyzer = SentimentAnalyzer(mock_client)
        items = [
            {"id": f"item-{i}", "text": f"Text {i}", "word_count": 2}
            for i in range(5)
        ]

        progress_calls = []
        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        results = await analyzer.analyze_batch(items, progress_callback=progress_callback)

        assert len(progress_calls) > 0
        assert progress_calls[-1] == (5, 5)

    async def test_batch_large_dataset(self):
        """Test batch processing with 100 items"""
        mock_client = AsyncMock()
        mock_client.analyze_batch = AsyncMock(side_effect=[
            [SentimentScore(polarity="neutral", score=0.0, confidence=0.8) for _ in range(50)],
            [SentimentScore(polarity="neutral", score=0.0, confidence=0.8) for _ in range(50)]
        ])

        analyzer = SentimentAnalyzer(mock_client)
        items = [
            {"id": f"item-{i}", "text": f"Text {i}", "word_count": 2}
            for i in range(100)
        ]

        results = await analyzer.analyze_batch(items, batch_size=50)

        assert len(results) == 100

    async def test_batch_preserves_order(self):
        """Test that batch results preserve input order"""
        mock_client = AsyncMock()
        mock_client.analyze_batch = AsyncMock(return_value=[
            SentimentScore(polarity="positive", score=0.85, confidence=0.92),
            SentimentScore(polarity="negative", score=-0.65, confidence=0.88)
        ])

        analyzer = SentimentAnalyzer(mock_client)
        items = [
            {"id": "item-pos", "text": "Great", "word_count": 1},
            {"id": "item-neg", "text": "Bad", "word_count": 1}
        ]

        results = await analyzer.analyze_batch(items)

        assert results[0].content_id == "item-pos"
        assert results[1].content_id == "item-neg"


# ==================== Sentiment Aggregation Tests ====================

@pytest.mark.unit
class TestSentimentAggregation:
    """Test sentiment aggregation for hierarchies (5 tests)"""

    def test_aggregate_empty_list(self):
        """Test aggregation with empty list"""
        mock_client = Mock()
        analyzer = SentimentAnalyzer(mock_client)

        result = analyzer.aggregate_sentiment([])

        assert result.polarity == "neutral"

    def test_aggregate_single_score(self):
        """Test aggregation with single score"""
        mock_client = Mock()
        analyzer = SentimentAnalyzer(mock_client)

        scores = [SentimentScore(polarity="positive", score=0.85, confidence=0.92)]
        result = analyzer.aggregate_sentiment(scores)

        assert result.polarity == "positive"
        assert result.score == 0.85

    def test_aggregate_multiple_positive(self):
        """Test aggregation of multiple positive scores"""
        mock_client = Mock()
        analyzer = SentimentAnalyzer(mock_client)

        scores = [
            SentimentScore(polarity="positive", score=0.85, confidence=0.92),
            SentimentScore(polarity="positive", score=0.75, confidence=0.88),
            SentimentScore(polarity="positive", score=0.90, confidence=0.95)
        ]

        result = analyzer.aggregate_sentiment(scores)

        assert result.polarity == "positive"
        assert result.score > 0.6

    def test_aggregate_mixed_sentiment(self):
        """Test aggregation of mixed positive/negative scores"""
        mock_client = Mock()
        analyzer = SentimentAnalyzer(mock_client)

        scores = [
            SentimentScore(polarity="positive", score=0.85, confidence=0.92),
            SentimentScore(polarity="negative", score=-0.65, confidence=0.88),
            SentimentScore(polarity="positive", score=0.70, confidence=0.85)
        ]

        result = analyzer.aggregate_sentiment(scores)

        # Should detect mixed sentiment due to variance
        assert result.polarity in ["mixed", "neutral", "positive"]

    def test_aggregate_with_weights(self):
        """Test weighted aggregation"""
        mock_client = Mock()
        analyzer = SentimentAnalyzer(mock_client)

        scores = [
            SentimentScore(polarity="positive", score=0.85, confidence=0.92),
            SentimentScore(polarity="neutral", score=0.05, confidence=0.75)
        ]
        weights = [0.8, 0.2]  # Weight first score more heavily

        result = analyzer.aggregate_sentiment(scores, weights)

        # Result should be closer to first (positive) score
        assert result.score > 0.5
