"""
Sentiment Analysis Models for LBS Knowledge Graph

Defines Pydantic models for sentiment analysis results.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SentimentPolarity(str, Enum):
    """Sentiment polarity classification"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class SentimentScore(BaseModel):
    """
    Sentiment analysis result for a content item.

    Attributes:
        polarity: Sentiment classification (positive/negative/neutral/mixed)
        score: Normalized sentiment score (0.0 = very negative, 1.0 = very positive)
        confidence: Confidence in the sentiment analysis (0.0-1.0)
        magnitude: Optional strength of sentiment regardless of polarity
    """
    polarity: SentimentPolarity
    score: float = Field(ge=0.0, le=1.0, description="Sentiment score from 0 (negative) to 1 (positive)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0 to 1")
    magnitude: Optional[float] = Field(None, ge=0.0, le=1.0, description="Strength of sentiment")

    @field_validator('score', 'confidence', 'magnitude')
    @classmethod
    def validate_range(cls, v: Optional[float]) -> Optional[float]:
        """Ensure values are within 0-1 range"""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError(f"Value must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator('polarity', mode='before')
    @classmethod
    def normalize_polarity(cls, v: str) -> str:
        """Normalize polarity string to lowercase"""
        if isinstance(v, str):
            return v.lower()
        return v

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "polarity": self.polarity.value,
            "score": round(self.score, 3),
            "confidence": round(self.confidence, 3),
            "magnitude": round(self.magnitude, 3) if self.magnitude is not None else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SentimentScore':
        """Create from dictionary"""
        return cls(
            polarity=data["polarity"],
            score=data["score"],
            confidence=data["confidence"],
            magnitude=data.get("magnitude")
        )

    @classmethod
    def neutral(cls) -> 'SentimentScore':
        """Create a neutral sentiment score (fallback)"""
        return cls(
            polarity=SentimentPolarity.NEUTRAL,
            score=0.5,
            confidence=0.0,
            magnitude=0.0
        )


class ContentItemWithSentiment(BaseModel):
    """
    Content item with sentiment analysis result.

    Used for batch processing and tracking.
    """
    content_id: str
    text: str
    word_count: int
    sentiment: Optional[SentimentScore] = None
    error: Optional[str] = None

    def has_sentiment(self) -> bool:
        """Check if sentiment analysis was successful"""
        return self.sentiment is not None and self.error is None
