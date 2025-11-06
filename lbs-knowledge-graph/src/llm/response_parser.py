"""
Response Parser for LLM outputs.

Parses and validates LLM JSON responses with Pydantic models for type safety.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# Pydantic Models for Type Safety

class SentimentResult(BaseModel):
    """Sentiment analysis result."""
    sentiment: str = Field(..., pattern="^(positive|negative|neutral)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    score: float = Field(..., ge=-1.0, le=1.0)
    reasoning: Optional[str] = None


class Topic(BaseModel):
    """Individual topic with metadata."""
    name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    keywords: List[str] = []


class TopicExtractionResult(BaseModel):
    """Topic extraction result."""
    topics: List[Topic]

    @validator('topics')
    def validate_topics(cls, v):
        if len(v) > 10:
            logger.warning(f"Too many topics ({len(v)}), truncating to 10")
            return v[:10]
        return v


class Entity(BaseModel):
    """Named entity."""
    text: str
    type: str = Field(..., pattern="^(PERSON|ORGANIZATION|LOCATION|DATE|EVENT|PRODUCT)$")
    confidence: float = Field(..., ge=0.0, le=1.0)


class NERResult(BaseModel):
    """Named entity recognition result."""
    entities: List[Entity]


class PersonaResult(BaseModel):
    """Persona classification result."""
    primary_persona: str
    secondary_personas: List[str] = []
    confidence: float = Field(..., ge=0.0, le=1.0)
    characteristics: List[str] = []


class SimilarityResult(BaseModel):
    """Semantic similarity result."""
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    semantic_overlap: List[str] = []
    key_differences: List[str] = []
    relationship: str = Field(
        ...,
        pattern="^(identical|related|tangentially_related|unrelated)$"
    )


class Category(BaseModel):
    """Content category with confidence."""
    name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class CategorizationResult(BaseModel):
    """Content categorization result."""
    categories: List[Category]
    primary_category: str


class Insight(BaseModel):
    """Individual insight."""
    insight: str
    importance: float = Field(..., ge=0.0, le=1.0)
    category: str = Field(
        ...,
        pattern="^(fact|opinion|recommendation|finding|trend)$"
    )
    evidence: str


class InsightsResult(BaseModel):
    """Key insights extraction result."""
    insights: List[Insight]
    summary: str


class QualityDimensions(BaseModel):
    """Quality assessment dimensions."""
    clarity: float = Field(..., ge=0.0, le=1.0)
    accuracy: float = Field(..., ge=0.0, le=1.0)
    depth: float = Field(..., ge=0.0, le=1.0)
    credibility: float = Field(..., ge=0.0, le=1.0)
    relevance: float = Field(..., ge=0.0, le=1.0)


class QualityResult(BaseModel):
    """Quality assessment result."""
    overall_quality: float = Field(..., ge=0.0, le=1.0)
    dimensions: QualityDimensions
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[str] = []


class RelationshipResult(BaseModel):
    """Relationship inference result."""
    relationship_exists: bool
    relationship_type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    direction: str = Field(
        ...,
        pattern="^(source_to_target|target_to_source|bidirectional)$"
    )
    strength: float = Field(..., ge=0.0, le=1.0)
    reasoning: str


class ResponseParser:
    """
    Parser for LLM responses with validation and error handling.

    Features:
    - JSON extraction from text responses
    - Type validation with Pydantic
    - Graceful handling of malformed responses
    - Support for multiple response formats
    """

    @staticmethod
    def extract_json(response: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response text.

        Handles responses that may contain markdown code blocks or
        additional text around the JSON.

        Args:
            response: Raw LLM response text

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If no valid JSON found
        """
        # Try direct parsing first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from code block
        import re
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try extracting first JSON object
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        match = re.search(json_pattern, response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract valid JSON from response: {response[:200]}...")

    @staticmethod
    def parse_sentiment(response: str) -> Optional[SentimentResult]:
        """
        Parse sentiment analysis response.

        Args:
            response: LLM response text

        Returns:
            Parsed sentiment result or None if parsing fails
        """
        try:
            data = ResponseParser.extract_json(response)
            return SentimentResult(**data)
        except Exception as e:
            logger.error(f"Error parsing sentiment response: {e}")
            return None

    @staticmethod
    def parse_topics(response: str) -> Optional[TopicExtractionResult]:
        """
        Parse topic extraction response.

        Args:
            response: LLM response text

        Returns:
            Parsed topic extraction result or None if parsing fails
        """
        try:
            data = ResponseParser.extract_json(response)
            return TopicExtractionResult(**data)
        except Exception as e:
            logger.error(f"Error parsing topics response: {e}")
            return None

    @staticmethod
    def parse_entities(response: str) -> Optional[NERResult]:
        """
        Parse named entity recognition response.

        Args:
            response: LLM response text

        Returns:
            Parsed NER result or None if parsing fails
        """
        try:
            data = ResponseParser.extract_json(response)
            return NERResult(**data)
        except Exception as e:
            logger.error(f"Error parsing entities response: {e}")
            return None

    @staticmethod
    def parse_persona(response: str) -> Optional[PersonaResult]:
        """
        Parse persona classification response.

        Args:
            response: LLM response text

        Returns:
            Parsed persona result or None if parsing fails
        """
        try:
            data = ResponseParser.extract_json(response)
            return PersonaResult(**data)
        except Exception as e:
            logger.error(f"Error parsing persona response: {e}")
            return None

    @staticmethod
    def parse_similarity(response: str) -> Optional[SimilarityResult]:
        """
        Parse semantic similarity response.

        Args:
            response: LLM response text

        Returns:
            Parsed similarity result or None if parsing fails
        """
        try:
            data = ResponseParser.extract_json(response)
            return SimilarityResult(**data)
        except Exception as e:
            logger.error(f"Error parsing similarity response: {e}")
            return None

    @staticmethod
    def parse_categorization(response: str) -> Optional[CategorizationResult]:
        """
        Parse content categorization response.

        Args:
            response: LLM response text

        Returns:
            Parsed categorization result or None if parsing fails
        """
        try:
            data = ResponseParser.extract_json(response)
            return CategorizationResult(**data)
        except Exception as e:
            logger.error(f"Error parsing categorization response: {e}")
            return None

    @staticmethod
    def parse_insights(response: str) -> Optional[InsightsResult]:
        """
        Parse key insights extraction response.

        Args:
            response: LLM response text

        Returns:
            Parsed insights result or None if parsing fails
        """
        try:
            data = ResponseParser.extract_json(response)
            return InsightsResult(**data)
        except Exception as e:
            logger.error(f"Error parsing insights response: {e}")
            return None

    @staticmethod
    def parse_quality(response: str) -> Optional[QualityResult]:
        """
        Parse quality assessment response.

        Args:
            response: LLM response text

        Returns:
            Parsed quality result or None if parsing fails
        """
        try:
            data = ResponseParser.extract_json(response)
            return QualityResult(**data)
        except Exception as e:
            logger.error(f"Error parsing quality response: {e}")
            return None

    @staticmethod
    def parse_relationship(response: str) -> Optional[RelationshipResult]:
        """
        Parse relationship inference response.

        Args:
            response: LLM response text

        Returns:
            Parsed relationship result or None if parsing fails
        """
        try:
            data = ResponseParser.extract_json(response)
            return RelationshipResult(**data)
        except Exception as e:
            logger.error(f"Error parsing relationship response: {e}")
            return None

    @staticmethod
    def validate_and_clean(
        response: str,
        expected_type: type[BaseModel]
    ) -> Optional[BaseModel]:
        """
        Generic parser with validation for any Pydantic model type.

        Args:
            response: LLM response text
            expected_type: Pydantic model class to parse into

        Returns:
            Parsed and validated model instance or None if parsing fails
        """
        try:
            data = ResponseParser.extract_json(response)
            return expected_type(**data)
        except Exception as e:
            logger.error(f"Error parsing response for {expected_type.__name__}: {e}")
            return None

    @staticmethod
    def parse_batch_responses(
        response: str,
        expected_type: type[BaseModel]
    ) -> List[Optional[BaseModel]]:
        """
        Parse batch response containing multiple JSON objects.

        Args:
            response: Batch LLM response text
            expected_type: Pydantic model class for each item

        Returns:
            List of parsed model instances (None for failed parses)
        """
        # Split by "Item N:" markers
        import re
        item_pattern = r"Item (\d+):\s*(.*?)(?=Item \d+:|$)"
        matches = re.findall(item_pattern, response, re.DOTALL)

        results = []
        for idx_str, item_response in matches:
            parsed = ResponseParser.validate_and_clean(item_response, expected_type)
            results.append(parsed)

            if parsed is None:
                logger.warning(f"Failed to parse batch item {idx_str}")

        return results
