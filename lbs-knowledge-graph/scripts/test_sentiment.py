#!/usr/bin/env python3
"""
Test script for sentiment analysis.

Tests sentiment analyzer on sample content items before running full enrichment.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enrichment.llm_client import LLMClient
from src.enrichment.sentiment_analyzer import SentimentAnalyzer


async def test_sentiment_analysis():
    """Test sentiment analysis on sample texts"""

    print("\n" + "=" * 80)
    print("  Sentiment Analysis Test")
    print("=" * 80 + "\n")

    # Load environment variables
    load_dotenv()

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found")
        sys.exit(1)

    # Initialize components
    print("Initializing LLM client...")
    llm_client = LLMClient(api_key=api_key, model="gpt-4o-mini")

    print("Initializing sentiment analyzer...\n")
    analyzer = SentimentAnalyzer(llm_client)

    # Test samples
    samples = [
        {
            "id": "test_1",
            "text": "London Business School offers world-class MBA programs with exceptional faculty and diverse student body.",
            "expected": "positive"
        },
        {
            "id": "test_2",
            "text": "The programme has been cancelled due to insufficient enrolment and budget constraints.",
            "expected": "negative"
        },
        {
            "id": "test_3",
            "text": "The course covers financial accounting, management accounting, and corporate finance.",
            "expected": "neutral"
        },
        {
            "id": "test_4",
            "text": "While the curriculum is rigorous and demanding, students appreciate the excellent career opportunities it provides.",
            "expected": "mixed"
        }
    ]

    print("Testing sentiment analysis on sample texts:\n")

    # Test each sample
    results = []
    for sample in samples:
        print(f"📝 Text: {sample['text'][:80]}...")
        print(f"   Expected: {sample['expected']}")

        sentiment = await analyzer.analyze_content_item(sample)

        print(f"   Result: {sentiment.polarity.value} (score: {sentiment.score:.3f}, confidence: {sentiment.confidence:.3f})")

        match = "✅" if sentiment.polarity.value == sample['expected'] else "⚠️"
        print(f"   {match}\n")

        results.append({
            "text": sample["text"],
            "expected": sample["expected"],
            "result": sentiment.to_dict()
        })

    # Test batch processing
    print("\nTesting batch processing...")
    batch_items = [{"id": f"batch_{i}", "text": s["text"]} for i, s in enumerate(samples)]

    batch_results = await analyzer.analyze_batch(batch_items, batch_size=4)

    print(f"   ✅ Processed {len(batch_results)} items in batch")
    print(f"   ✅ {sum(1 for r in batch_results if r.has_sentiment())} items with successful sentiment")

    # Display stats
    print("\nLLM Statistics:")
    stats = analyzer.get_stats()
    llm_stats = stats["llm_stats"]
    print(f"   API calls: {llm_stats['api_calls']}")
    print(f"   Total tokens: {llm_stats['total_tokens']}")
    print(f"   Total cost: ${llm_stats['total_cost']:.4f}")

    # Test aggregation
    print("\nTesting sentiment aggregation...")
    sentiments = [r.sentiment for r in batch_results if r.sentiment]
    aggregated = analyzer.aggregate_sentiment(sentiments)

    print(f"   Aggregated: {aggregated.polarity.value} (score: {aggregated.score:.3f}, confidence: {aggregated.confidence:.3f})")

    print("\n" + "=" * 80)
    print("  ✅ Sentiment Analysis Test Complete")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_sentiment_analysis())
