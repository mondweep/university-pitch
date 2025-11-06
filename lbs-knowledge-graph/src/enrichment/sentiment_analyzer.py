"""
Sentiment Analyzer for Knowledge Graph Content

Analyzes sentiment for Page, Section, and ContentItem entities.
"""

import asyncio
from typing import List, Dict, Optional
from .models import SentimentScore, ContentItemWithSentiment
from .llm_client import LLMClient


class SentimentAnalyzer:
    """
    Analyzes sentiment for content items using LLM.

    Features:
    - Single content item analysis
    - Batch processing for efficiency
    - Sentiment aggregation for hierarchies
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize sentiment analyzer.

        Args:
            llm_client: LLM client for API calls
        """
        self.llm_client = llm_client
        self.cache: Dict[str, SentimentScore] = {}

    async def analyze_content_item(self, item: Dict) -> SentimentScore:
        """
        Analyze sentiment for a single content item.

        Args:
            item: Content item dictionary with 'id', 'text', etc.

        Returns:
            SentimentScore with polarity, score, and confidence
        """
        content_id = item.get("id", "")
        text = item.get("text", "")

        # Check cache
        if content_id in self.cache:
            return self.cache[content_id]

        # Skip empty or very short text
        if not text or len(text.strip()) < 5:
            return SentimentScore.neutral()

        # Analyze sentiment
        sentiment = await self.llm_client.analyze_sentiment(text)

        # Cache result
        self.cache[content_id] = sentiment

        return sentiment

    async def analyze_batch(
        self,
        items: List[Dict],
        batch_size: int = 50,
        progress_callback: Optional[callable] = None
    ) -> List[ContentItemWithSentiment]:
        """
        Analyze sentiment for multiple content items in batches.

        Args:
            items: List of content item dictionaries
            batch_size: Number of items to process in parallel
            progress_callback: Optional callback for progress updates

        Returns:
            List of ContentItemWithSentiment objects
        """
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            # Extract texts
            texts = [item.get("text", "") for item in batch]

            # Analyze in parallel
            sentiments = await self.llm_client.analyze_batch(texts, batch_size=batch_size)

            # Create results
            for item, sentiment in zip(batch, sentiments):
                results.append(ContentItemWithSentiment(
                    content_id=item.get("id", ""),
                    text=item.get("text", ""),
                    word_count=item.get("word_count", 0),
                    sentiment=sentiment
                ))

            # Progress callback
            if progress_callback:
                progress_callback(len(results), len(items))

        return results

    def aggregate_sentiment(
        self,
        scores: List[SentimentScore],
        weights: Optional[List[float]] = None
    ) -> SentimentScore:
        """
        Aggregate child sentiment scores to parent (weighted average).

        Args:
            scores: List of child sentiment scores
            weights: Optional weights for each score (default: equal weights)

        Returns:
            Aggregated SentimentScore
        """
        if not scores:
            return SentimentScore.neutral()

        # Filter out neutral scores with zero confidence (failed analyses)
        valid_scores = [s for s in scores if s.confidence > 0.0]

        if not valid_scores:
            return SentimentScore.neutral()

        # Default to equal weights
        if weights is None:
            weights = [1.0] * len(valid_scores)
        else:
            # Ensure weights match valid scores
            weights = weights[:len(valid_scores)]

        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            return SentimentScore.neutral()

        weights = [w / total_weight for w in weights]

        # Weighted average of scores
        avg_score = sum(s.score * w for s, w in zip(valid_scores, weights))

        # Weighted average of confidence
        avg_confidence = sum(s.confidence * w for s, w in zip(valid_scores, weights))

        # Weighted average of magnitude (if available)
        magnitudes = [s.magnitude for s in valid_scores if s.magnitude is not None]
        avg_magnitude = None
        if magnitudes:
            avg_magnitude = sum(m * w for m, w in zip(magnitudes, weights))

        # Determine polarity from score
        if avg_score >= 0.6:
            polarity = "positive"
        elif avg_score <= 0.4:
            polarity = "negative"
        else:
            polarity = "neutral"

        # Check for mixed sentiment (high variance)
        score_variance = sum(w * (s.score - avg_score) ** 2 for s, w in zip(valid_scores, weights))
        if score_variance > 0.1:  # High variance threshold
            polarity = "mixed"

        return SentimentScore(
            polarity=polarity,
            score=avg_score,
            confidence=avg_confidence,
            magnitude=avg_magnitude
        )

    def get_stats(self) -> dict:
        """Get analyzer statistics"""
        return {
            "cached_items": len(self.cache),
            "llm_stats": self.llm_client.get_stats()
        }
