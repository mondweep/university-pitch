#!/usr/bin/env python3
"""
Mock Sentiment Analysis Test

Tests the sentiment analysis pipeline without making real API calls.
Useful for verifying setup and logic without consuming API credits.
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enrichment.models import SentimentScore, SentimentPolarity, ContentItemWithSentiment
from src.enrichment.sentiment_analyzer import SentimentAnalyzer


class MockLLMClient:
    """Mock LLM client for testing without API calls"""

    def __init__(self):
        self.api_calls = 0
        self.total_tokens = 0
        self.total_cost = 0.0

    async def analyze_sentiment(self, text: str) -> SentimentScore:
        """Mock sentiment analysis based on simple keyword matching"""
        self.api_calls += 1
        self.total_tokens += len(text.split()) * 2  # Rough estimate

        text_lower = text.lower()

        # Simple keyword-based sentiment
        positive_keywords = ['excellent', 'great', 'outstanding', 'best', 'amazing', 'wonderful']
        negative_keywords = ['poor', 'bad', 'terrible', 'worst', 'disappointing']

        positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)

        # Calculate sentiment
        if positive_count > negative_count:
            polarity = "positive"
            score = 0.7 + min(0.3, positive_count * 0.1)
            confidence = 0.8
        elif negative_count > positive_count:
            polarity = "negative"
            score = 0.3 - min(0.3, negative_count * 0.1)
            confidence = 0.8
        else:
            polarity = "neutral"
            score = 0.5
            confidence = 0.6

        magnitude = abs(score - 0.5) * 2

        return SentimentScore(
            polarity=SentimentPolarity(polarity),
            score=score,
            confidence=confidence,
            magnitude=magnitude
        )

    async def analyze_batch(self, texts: list, batch_size: int = 50) -> list:
        """Mock batch analysis"""
        results = []
        for text in texts:
            sentiment = await self.analyze_sentiment(text)
            results.append(sentiment)
        return results

    def get_stats(self) -> dict:
        """Get mock usage statistics"""
        self.total_cost = (self.total_tokens / 1_000_000) * 0.75  # Mock cost
        return {
            "api_calls": self.api_calls,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 2),
            "avg_tokens_per_call": round(self.total_tokens / self.api_calls, 1) if self.api_calls > 0 else 0
        }


async def test_single_item():
    """Test single content item analysis"""
    print("\n" + "=" * 80)
    print("  Test 1: Single Item Analysis")
    print("=" * 80 + "\n")

    mock_client = MockLLMClient()
    analyzer = SentimentAnalyzer(mock_client)

    test_cases = [
        {
            "id": "test_1",
            "text": "The MBA program offers excellent opportunities for career growth.",
            "expected": "positive"
        },
        {
            "id": "test_2",
            "text": "The application process is straightforward and well-documented.",
            "expected": "neutral"
        },
        {
            "id": "test_3",
            "text": "Some students found the course load overwhelming and stressful.",
            "expected": "negative"
        }
    ]

    for test_case in test_cases:
        sentiment = await analyzer.analyze_content_item(test_case)
        match = "✅" if sentiment.polarity.value == test_case["expected"] else "❌"
        print(f"{match} {test_case['id']}: {sentiment.polarity.value} (score: {sentiment.score:.2f}, confidence: {sentiment.confidence:.2f})")
        print(f"   Text: {test_case['text'][:80]}...")

    stats = analyzer.get_stats()
    print(f"\n   Stats: {stats['llm_stats']['api_calls']} calls, {stats['llm_stats']['total_tokens']} tokens")


async def test_batch_processing():
    """Test batch processing"""
    print("\n" + "=" * 80)
    print("  Test 2: Batch Processing")
    print("=" * 80 + "\n")

    mock_client = MockLLMClient()
    analyzer = SentimentAnalyzer(mock_client)

    # Create test batch
    test_items = [
        {"id": f"item_{i}", "text": f"This is test content item {i} with great opportunities.", "word_count": 10}
        for i in range(100)
    ]

    print(f"   Processing {len(test_items)} items in batches of 50...")

    progress_count = 0

    def progress_callback(current, total):
        nonlocal progress_count
        progress_count = current
        percent = (current / total) * 100
        print(f"\r   Progress: {current}/{total} ({percent:.1f}%)", end="", flush=True)

    results = await analyzer.analyze_batch(
        test_items,
        batch_size=50,
        progress_callback=progress_callback
    )

    print()  # New line after progress

    # Analyze results
    positive = sum(1 for r in results if r.sentiment.polarity.value == "positive")
    neutral = sum(1 for r in results if r.sentiment.polarity.value == "neutral")
    negative = sum(1 for r in results if r.sentiment.polarity.value == "negative")

    print(f"\n   Results:")
    print(f"      Positive: {positive} ({positive/len(results)*100:.1f}%)")
    print(f"      Neutral: {neutral} ({neutral/len(results)*100:.1f}%)")
    print(f"      Negative: {negative} ({negative/len(results)*100:.1f}%)")

    stats = analyzer.get_stats()
    print(f"\n   Stats: {stats['llm_stats']['api_calls']} calls, ${stats['llm_stats']['total_cost']:.2f}")


async def test_aggregation():
    """Test sentiment aggregation"""
    print("\n" + "=" * 80)
    print("  Test 3: Sentiment Aggregation")
    print("=" * 80 + "\n")

    mock_client = MockLLMClient()
    analyzer = SentimentAnalyzer(mock_client)

    # Create child sentiments
    child_sentiments = [
        SentimentScore(polarity="positive", score=0.8, confidence=0.9, magnitude=0.6),
        SentimentScore(polarity="positive", score=0.7, confidence=0.85, magnitude=0.4),
        SentimentScore(polarity="neutral", score=0.5, confidence=0.7, magnitude=0.0),
        SentimentScore(polarity="positive", score=0.75, confidence=0.88, magnitude=0.5),
    ]

    # Test equal weight aggregation
    aggregated = analyzer.aggregate_sentiment(child_sentiments)
    print(f"   Equal Weight Aggregation:")
    print(f"      Polarity: {aggregated.polarity.value}")
    print(f"      Score: {aggregated.score:.3f}")
    print(f"      Confidence: {aggregated.confidence:.3f}")
    print(f"      Magnitude: {aggregated.magnitude:.3f}")

    # Test weighted aggregation (by word count)
    weights = [100, 50, 25, 75]  # Word counts
    weighted_aggregated = analyzer.aggregate_sentiment(child_sentiments, weights)
    print(f"\n   Weighted Aggregation (by word count):")
    print(f"      Polarity: {weighted_aggregated.polarity.value}")
    print(f"      Score: {weighted_aggregated.score:.3f}")
    print(f"      Confidence: {weighted_aggregated.confidence:.3f}")
    print(f"      Magnitude: {weighted_aggregated.magnitude:.3f}")

    # Test mixed sentiment detection
    mixed_sentiments = [
        SentimentScore(polarity="positive", score=0.9, confidence=0.9, magnitude=0.8),
        SentimentScore(polarity="negative", score=0.2, confidence=0.85, magnitude=0.6),
        SentimentScore(polarity="positive", score=0.85, confidence=0.88, magnitude=0.7),
        SentimentScore(polarity="negative", score=0.15, confidence=0.9, magnitude=0.7),
    ]

    mixed_aggregated = analyzer.aggregate_sentiment(mixed_sentiments)
    print(f"\n   Mixed Sentiment Detection:")
    print(f"      Polarity: {mixed_aggregated.polarity.value}")
    print(f"      Score: {mixed_aggregated.score:.3f}")
    print(f"      Confidence: {mixed_aggregated.confidence:.3f}")

    if mixed_aggregated.polarity.value == "mixed":
        print("      ✅ Correctly detected mixed sentiment")
    else:
        print("      ⚠️  Mixed sentiment not detected (high variance may be threshold-dependent)")


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("  Mock Sentiment Analysis Tests")
    print("  (No API calls - Testing logic only)")
    print("=" * 80)

    try:
        await test_single_item()
        await test_batch_processing()
        await test_aggregation()

        print("\n" + "=" * 80)
        print("  ✅ ALL TESTS COMPLETED")
        print("=" * 80 + "\n")

        print("  Next Steps:")
        print("    1. Set OPENAI_API_KEY in .env file")
        print("    2. Run: python scripts/test_sentiment_setup.py")
        print("    3. Run: python scripts/enrich_sentiment.py")
        print()

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
