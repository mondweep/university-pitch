"""
LLM Client for Sentiment Analysis

Handles API calls to OpenAI GPT-4 for sentiment analysis.
"""

import os
import json
import asyncio
from typing import Optional, List
from openai import AsyncOpenAI
from .models import SentimentScore, SentimentPolarity


# Sentiment analysis prompt template
SENTIMENT_PROMPT = """Analyze the sentiment of the following text. Return ONLY valid JSON with no additional text:

{
  "polarity": "positive" | "negative" | "neutral" | "mixed",
  "score": 0.0-1.0,
  "confidence": 0.0-1.0
}

Rules:
- score: 0.0 = very negative, 0.5 = neutral, 1.0 = very positive
- confidence: how certain you are about the sentiment
- polarity: overall sentiment classification
- Return ONLY the JSON object, no markdown, no explanations

Text: "{text}"

JSON:"""


class LLMClient:
    """
    Client for OpenAI GPT-4 API for sentiment analysis.

    Handles rate limiting, retries, and cost tracking.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o-mini for cost efficiency)
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")

        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

        self.client = AsyncOpenAI(api_key=self.api_key, timeout=timeout)

        # Cost tracking
        self.total_tokens = 0
        self.total_cost = 0.0
        self.api_calls = 0

        # Model pricing (per 1M tokens)
        self.pricing = {
            "gpt-4o-mini": {"input": 0.150, "output": 0.600},
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00}
        }

    async def analyze_sentiment(self, text: str) -> SentimentScore:
        """
        Analyze sentiment of text using LLM.

        Args:
            text: Text to analyze

        Returns:
            SentimentScore with polarity, score, and confidence

        Raises:
            Exception: If API call fails after retries
        """
        if not text or len(text.strip()) == 0:
            return SentimentScore.neutral()

        # Truncate very long text (max 1000 chars for efficiency)
        text = text[:1000] if len(text) > 1000 else text

        prompt = SENTIMENT_PROMPT.format(text=text.replace('"', '\\"'))

        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a sentiment analysis expert. Return ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistency
                    max_tokens=100,   # Sentiment analysis needs few tokens
                    response_format={"type": "json_object"}
                )

                # Track usage
                self.api_calls += 1
                usage = response.usage
                self.total_tokens += usage.total_tokens

                # Calculate cost
                if self.model in self.pricing:
                    input_cost = (usage.prompt_tokens / 1_000_000) * self.pricing[self.model]["input"]
                    output_cost = (usage.completion_tokens / 1_000_000) * self.pricing[self.model]["output"]
                    self.total_cost += input_cost + output_cost

                # Parse response
                content = response.choices[0].message.content
                data = json.loads(content)

                # Validate and create SentimentScore
                return SentimentScore(
                    polarity=SentimentPolarity(data["polarity"].lower()),
                    score=float(data["score"]),
                    confidence=float(data["confidence"]),
                    magnitude=float(data.get("magnitude", abs(data["score"] - 0.5) * 2))
                )

            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parse error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    # Return neutral sentiment on final failure
                    return SentimentScore.neutral()
                await asyncio.sleep(1 * (attempt + 1))

            except Exception as e:
                print(f"⚠️  API error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 * (attempt + 1))

        return SentimentScore.neutral()

    async def analyze_batch(self, texts: List[str], batch_size: int = 50) -> List[SentimentScore]:
        """
        Analyze sentiment for multiple texts in parallel batches.

        Args:
            texts: List of texts to analyze
            batch_size: Number of texts to process in parallel

        Returns:
            List of SentimentScore objects
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self.analyze_sentiment(text) for text in batch],
                return_exceptions=True
            )

            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"⚠️  Batch error: {result}")
                    results.append(SentimentScore.neutral())
                else:
                    results.append(result)

        return results

    def get_stats(self) -> dict:
        """Get usage statistics"""
        return {
            "api_calls": self.api_calls,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 2),
            "avg_tokens_per_call": round(self.total_tokens / self.api_calls, 1) if self.api_calls > 0 else 0
        }
