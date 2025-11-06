"""
Tests for Sentiment Analysis functionality.
Includes unit tests with mocks and validation tests with ground truth.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lbs-knowledge-graph'))
sys.path.insert(0, os.path.dirname(__file__))

from src.enrichment.sentiment_analyzer import SentimentAnalyzer
from src.enrichment.models import SentimentScore
from fixtures.ground_truth_sentiment import (
    GROUND_TRUTH_SENTIMENT,
    validate_sentiment_prediction,
    get_sentiments_by_polarity
)


class TestSentimentScore:
    """Test SentimentScore model."""

    def test_sentiment_score_creation(self):
        """Test creating sentiment score."""
        score = SentimentScore(
            polarity="positive",
            score=0.85,
            confidence=0.9,
            magnitude=0.75
        )
        assert score.polarity == "positive"
        assert score.score == 0.85
        assert score.confidence == 0.9

    def test_neutral_sentiment(self):
        """Test neutral sentiment creation."""
        score = SentimentScore.neutral()
        assert score.polarity == "neutral"
        assert score.score == 0.5
        assert score.confidence == 1.0


class TestSentimentAnalyzer:
    """Test SentimentAnalyzer with mocked LLM."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = Mock()
        client.analyze_sentiment = AsyncMock()
        client.analyze_batch = AsyncMock()
        client.get_stats = Mock(return_value={})
        return client

    @pytest.fixture
    def analyzer(self, mock_llm_client):
        """Create sentiment analyzer with mocked client."""
        return SentimentAnalyzer(mock_llm_client)

    @pytest.mark.asyncio
    async def test_analyze_positive_content(self, analyzer, mock_llm_client):
        """Test analyzing positive content."""
        mock_llm_client.analyze_sentiment.return_value = SentimentScore(
            polarity="positive",
            score=0.85,
            confidence=0.9
        )

        item = {
            "id": "test1",
            "text": "This is excellent and amazing content!"
        }

        result = await analyzer.analyze_content_item(item)

        assert result.polarity == "positive"
        assert result.score >= 0.75
        assert result.confidence >= 0.8
        mock_llm_client.analyze_sentiment.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_negative_content(self, analyzer, mock_llm_client):
        """Test analyzing negative content."""
        mock_llm_client.analyze_sentiment.return_value = SentimentScore(
            polarity="negative",
            score=0.25,
            confidence=0.85
        )

        item = {
            "id": "test2",
            "text": "This is terrible and disappointing."
        }

        result = await analyzer.analyze_content_item(item)

        assert result.polarity == "negative"
        assert result.score <= 0.4
        assert result.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_analyze_neutral_content(self, analyzer, mock_llm_client):
        """Test analyzing neutral content."""
        mock_llm_client.analyze_sentiment.return_value = SentimentScore(
            polarity="neutral",
            score=0.5,
            confidence=0.75
        )

        item = {
            "id": "test3",
            "text": "The library is open from 9am to 5pm."
        }

        result = await analyzer.analyze_content_item(item)

        assert result.polarity == "neutral"
        assert 0.4 <= result.score <= 0.6
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_empty_text_handling(self, analyzer):
        """Test handling of empty or very short text."""
        item = {"id": "empty", "text": ""}
        result = await analyzer.analyze_content_item(item)
        assert result.polarity == "neutral"

        item = {"id": "short", "text": "Hi"}
        result = await analyzer.analyze_content_item(item)
        assert result.polarity == "neutral"

    @pytest.mark.asyncio
    async def test_caching(self, analyzer, mock_llm_client):
        """Test that results are cached."""
        mock_llm_client.analyze_sentiment.return_value = SentimentScore(
            polarity="positive",
            score=0.8,
            confidence=0.9
        )

        item = {"id": "cached", "text": "test content"}

        # First call
        await analyzer.analyze_content_item(item)
        assert mock_llm_client.analyze_sentiment.call_count == 1

        # Second call should use cache
        await analyzer.analyze_content_item(item)
        assert mock_llm_client.analyze_sentiment.call_count == 1  # Not called again

    @pytest.mark.asyncio
    async def test_batch_analysis(self, analyzer, mock_llm_client):
        """Test batch sentiment analysis."""
        mock_llm_client.analyze_batch.return_value = [
            SentimentScore("positive", 0.85, 0.9),
            SentimentScore("negative", 0.25, 0.85),
            SentimentScore("neutral", 0.5, 0.75)
        ]

        items = [
            {"id": "1", "text": "Great content", "word_count": 2},
            {"id": "2", "text": "Poor quality", "word_count": 2},
            {"id": "3", "text": "Regular info", "word_count": 2}
        ]

        results = await analyzer.analyze_batch(items, batch_size=3)

        assert len(results) == 3
        assert results[0].sentiment.polarity == "positive"
        assert results[1].sentiment.polarity == "negative"
        assert results[2].sentiment.polarity == "neutral"


class TestSentimentAggregation:
    """Test sentiment aggregation functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mock client."""
        mock_client = Mock()
        return SentimentAnalyzer(mock_client)

    def test_aggregate_positive_sentiments(self, analyzer):
        """Test aggregating multiple positive sentiments."""
        scores = [
            SentimentScore("positive", 0.85, 0.9),
            SentimentScore("positive", 0.80, 0.85),
            SentimentScore("positive", 0.90, 0.95)
        ]

        result = analyzer.aggregate_sentiment(scores)

        assert result.polarity == "positive"
        assert 0.80 <= result.score <= 0.90
        assert result.confidence >= 0.85

    def test_aggregate_mixed_sentiments(self, analyzer):
        """Test aggregating mixed sentiments."""
        scores = [
            SentimentScore("positive", 0.80, 0.9),
            SentimentScore("negative", 0.30, 0.85),
            SentimentScore("neutral", 0.50, 0.75)
        ]

        result = analyzer.aggregate_sentiment(scores)

        # Should be mixed or neutral due to high variance
        assert result.polarity in ["mixed", "neutral"]

    def test_aggregate_with_weights(self, analyzer):
        """Test weighted sentiment aggregation."""
        scores = [
            SentimentScore("positive", 0.90, 0.95),  # High weight
            SentimentScore("negative", 0.20, 0.85)   # Low weight
        ]
        weights = [0.8, 0.2]

        result = analyzer.aggregate_sentiment(scores, weights)

        # Should be closer to positive due to higher weight
        assert result.score > 0.6

    def test_aggregate_empty_list(self, analyzer):
        """Test aggregating empty list returns neutral."""
        result = analyzer.aggregate_sentiment([])
        assert result.polarity == "neutral"

    def test_filter_invalid_scores(self, analyzer):
        """Test filtering out invalid scores (zero confidence)."""
        scores = [
            SentimentScore("positive", 0.85, 0.9),
            SentimentScore("neutral", 0.5, 0.0),  # Invalid
            SentimentScore("negative", 0.25, 0.85)
        ]

        result = analyzer.aggregate_sentiment(scores)

        # Should only consider valid scores
        assert result.confidence > 0.0


class TestGroundTruthValidation:
    """Test sentiment analysis against ground truth labels."""

    @pytest.fixture
    def analyzer_with_mock(self):
        """Create analyzer with predictable responses."""
        mock_client = Mock()

        async def mock_analyze(text):
            # Simple heuristic for testing
            positive_words = ["excellent", "outstanding", "great", "amazing", "unparalleled"]
            negative_words = ["terrible", "poor", "disappointing", "limited", "challenges"]

            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)

            if pos_count > neg_count:
                return SentimentScore("positive", 0.85, 0.9)
            elif neg_count > pos_count:
                return SentimentScore("negative", 0.25, 0.85)
            elif pos_count == neg_count and pos_count > 0:
                return SentimentScore("mixed", 0.55, 0.75)
            else:
                return SentimentScore("neutral", 0.5, 0.75)

        mock_client.analyze_sentiment = mock_analyze
        return SentimentAnalyzer(mock_client)

    @pytest.mark.asyncio
    async def test_positive_examples_accuracy(self, analyzer_with_mock):
        """Test accuracy on positive examples from ground truth."""
        positive_examples = get_sentiments_by_polarity("positive")
        correct = 0

        for example in positive_examples[:5]:  # Test first 5
            item = {"id": example["id"], "text": example["text"]}
            result = await analyzer_with_mock.analyze_content_item(item)

            validation = validate_sentiment_prediction(
                example["id"],
                result.polarity,
                result.score
            )

            if validation.get("polarity_correct"):
                correct += 1

        accuracy = correct / 5
        assert accuracy >= 0.6, f"Positive sentiment accuracy too low: {accuracy}"

    @pytest.mark.asyncio
    async def test_neutral_examples_accuracy(self, analyzer_with_mock):
        """Test accuracy on neutral examples from ground truth."""
        neutral_examples = get_sentiments_by_polarity("neutral")
        correct = 0

        for example in neutral_examples[:5]:
            item = {"id": example["id"], "text": example["text"]}
            result = await analyzer_with_mock.analyze_content_item(item)

            validation = validate_sentiment_prediction(
                example["id"],
                result.polarity,
                result.score
            )

            if validation.get("polarity_correct"):
                correct += 1

        accuracy = correct / 5
        assert accuracy >= 0.6, f"Neutral sentiment accuracy too low: {accuracy}"

    @pytest.mark.asyncio
    async def test_score_ranges(self, analyzer_with_mock):
        """Test that sentiment scores fall within expected ranges."""
        test_cases = [
            ("Excellent and outstanding work!", 0.75, 1.0),
            ("Terrible and disappointing results.", 0.0, 0.4),
            ("The course meets on Tuesdays.", 0.4, 0.6)
        ]

        for text, min_score, max_score in test_cases:
            item = {"id": "test", "text": text}
            result = await analyzer_with_mock.analyze_content_item(item)
            assert min_score <= result.score <= max_score, \
                f"Score {result.score} outside range [{min_score}, {max_score}] for: {text}"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mock client."""
        mock_client = Mock()
        mock_client.analyze_sentiment = AsyncMock()
        mock_client.get_stats = Mock(return_value={})
        return SentimentAnalyzer(mock_client)

    @pytest.mark.asyncio
    async def test_very_long_text(self, analyzer):
        """Test handling of very long text."""
        analyzer.llm_client.analyze_sentiment.return_value = SentimentScore(
            "neutral", 0.5, 0.75
        )

        long_text = "word " * 10000  # Very long text
        item = {"id": "long", "text": long_text}

        result = await analyzer.analyze_content_item(item)
        assert result is not None

    @pytest.mark.asyncio
    async def test_special_characters(self, analyzer):
        """Test handling of special characters."""
        analyzer.llm_client.analyze_sentiment.return_value = SentimentScore(
            "neutral", 0.5, 0.75
        )

        special_text = "Test @#$% with &*() special chars"
        item = {"id": "special", "text": special_text}

        result = await analyzer.analyze_content_item(item)
        assert result is not None

    def test_statistics_tracking(self, analyzer):
        """Test that analyzer tracks statistics."""
        stats = analyzer.get_stats()
        assert "cached_items" in stats
        assert "llm_stats" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
