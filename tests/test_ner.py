"""
Tests for Named Entity Recognition (NER) extraction.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lbs-knowledge-graph'))
sys.path.insert(0, os.path.dirname(__file__))

from src.enrichment.ner_extractor import NERExtractor
from src.enrichment.entity_models import Entity, EntityType, EntityMention
from fixtures.ground_truth_ner import GROUND_TRUTH_NER, validate_ner_extraction
from fixtures.mock_llm_responses import NER_MOCK_RESPONSES


class TestNERExtractorInitialization:
    """Test NER extractor initialization."""

    def test_initialization_with_api_key(self):
        """Test initialization with API key."""
        with pytest.raises(ValueError, match="OpenAI API key not provided"):
            NERExtractor(api_key=None)

    def test_initialization_custom_model(self):
        """Test initialization with custom model."""
        extractor = NERExtractor(api_key="test-key", model="gpt-4o")
        assert extractor.model == "gpt-4o"

    def test_initialization_batch_size(self):
        """Test custom batch size."""
        extractor = NERExtractor(api_key="test-key", batch_size=50)
        assert extractor.batch_size == 50


class TestEntityExtraction:
    """Test entity extraction from content."""

    @pytest.fixture
    def mock_extractor(self):
        """Create NER extractor with mocked client."""
        extractor = NERExtractor(api_key="test-key")
        extractor.client = AsyncMock()
        return extractor

    @pytest.mark.asyncio
    async def test_extract_people_and_organizations(self, mock_extractor):
        """Test extracting people and organization entities."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = NER_MOCK_RESPONSES["people_org"]["content"]
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 150
        mock_response.usage.total_tokens = 350
        
        mock_extractor.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await mock_extractor.extract_entities_from_content(
            "test1",
            "Professor Jane Smith at London Business School"
        )
        
        assert len(result.entities) == 2
        # Check person entity
        person = next(e for e in result.entities if e.entity_type == EntityType.PERSON)
        assert "Professor Jane Smith" in person.name
        # Check org entity
        org = next(e for e in result.entities if e.entity_type == EntityType.ORGANIZATION)
        assert "London Business School" in org.name

    @pytest.mark.asyncio
    async def test_extract_locations_and_events(self, mock_extractor):
        """Test extracting location and event entities."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = NER_MOCK_RESPONSES["locations_events"]["content"]
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 150
        mock_response.usage.total_tokens = 350
        
        mock_extractor.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await mock_extractor.extract_entities_from_content(
            "test2",
            "Conference in London next month"
        )
        
        assert len(result.entities) == 2
        # Check types
        types = {e.entity_type for e in result.entities}
        assert EntityType.LOCATION in types
        assert EntityType.EVENT in types

    @pytest.mark.asyncio
    async def test_entity_mentions_created(self, mock_extractor):
        """Test that entity mentions are created."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = NER_MOCK_RESPONSES["people_org"]["content"]
        mock_response.usage.prompt_tokens = 200
        mock_response.usage.completion_tokens = 150
        mock_response.usage.total_tokens = 350
        
        mock_extractor.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await mock_extractor.extract_entities_from_content("test", "text")
        
        assert len(result.mentions) == len(result.entities)
        for mention in result.mentions:
            assert mention.content_id == "test"
            assert mention.prominence in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_cost_tracking(self, mock_extractor):
        """Test that costs are tracked."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"entities": []}'
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        mock_extractor.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        initial_cost = mock_extractor.total_cost
        await mock_extractor.extract_entities_from_content("test", "text")
        
        assert mock_extractor.total_cost > initial_cost
        assert mock_extractor.api_calls == 1


class TestEntityNormalization:
    """Test entity name normalization."""

    @pytest.fixture
    def extractor(self):
        return NERExtractor(api_key="test-key")

    def test_normalize_person_titles(self, extractor):
        """Test removing titles from person names."""
        normalized = extractor.normalize_entity_name("Dr. Jane Smith", EntityType.PERSON)
        assert normalized == "Jane Smith"
        
        normalized = extractor.normalize_entity_name("Professor John Doe", EntityType.PERSON)
        assert normalized == "John Doe"

    def test_normalize_organization_names(self, extractor):
        """Test normalizing organization names."""
        normalized = extractor.normalize_entity_name("London Business School", EntityType.ORGANIZATION)
        assert normalized == "London Business School"


class TestProminenceCalculation:
    """Test prominence scoring based on position."""

    @pytest.fixture
    def extractor(self):
        return NERExtractor(api_key="test-key")

    def test_prominence_early_mention(self, extractor):
        """Test high prominence for early mentions."""
        prominence = extractor._calculate_prominence(position=0, content_length=1000)
        assert prominence >= 0.9

    def test_prominence_late_mention(self, extractor):
        """Test lower prominence for late mentions."""
        prominence = extractor._calculate_prominence(position=900, content_length=1000)
        assert prominence < 0.5

    def test_prominence_mid_mention(self, extractor):
        """Test medium prominence for middle mentions."""
        prominence = extractor._calculate_prominence(position=500, content_length=1000)
        assert 0.5 <= prominence <= 0.8

    def test_prominence_level_conversion(self, extractor):
        """Test converting prominence to level."""
        assert extractor._get_prominence_level(0.9) == "high"
        assert extractor._get_prominence_level(0.5) == "medium"
        assert extractor._get_prominence_level(0.2) == "low"


class TestRelationshipExtraction:
    """Test entity relationship extraction."""

    @pytest.fixture
    def extractor(self):
        return NERExtractor(api_key="test-key")

    def test_person_organization_relationship(self, extractor):
        """Test extracting AFFILIATED_WITH relationship."""
        entities = [
            Entity(
                id="p1",
                name="Jane Smith",
                entity_type=EntityType.PERSON,
                canonical_name="Jane Smith",
                aliases=[],
                metadata={"affiliation": "London Business School"},
                mention_count=1,
                first_mentioned=None,
                prominence=0.9,
                confidence=0.95
            ),
            Entity(
                id="o1",
                name="London Business School",
                entity_type=EntityType.ORGANIZATION,
                canonical_name="London Business School",
                aliases=[],
                metadata={},
                mention_count=1,
                first_mentioned=None,
                prominence=0.9,
                confidence=0.98
            )
        ]
        
        relationships = extractor._extract_relationships(entities, "")
        
        assert len(relationships) > 0
        affiliation_rel = next(
            (r for r in relationships if r.relationship_type == "AFFILIATED_WITH"), 
            None
        )
        assert affiliation_rel is not None

    def test_organization_location_relationship(self, extractor):
        """Test extracting LOCATED_AT relationship."""
        entities = [
            Entity(
                id="o1",
                name="LBS",
                entity_type=EntityType.ORGANIZATION,
                canonical_name="LBS",
                aliases=[],
                metadata={"location": "London"},
                mention_count=1,
                first_mentioned=None,
                prominence=0.9,
                confidence=0.95
            ),
            Entity(
                id="l1",
                name="London",
                entity_type=EntityType.LOCATION,
                canonical_name="London",
                aliases=[],
                metadata={},
                mention_count=1,
                first_mentioned=None,
                prominence=0.9,
                confidence=0.92
            )
        ]
        
        relationships = extractor._extract_relationships(entities, "")
        
        location_rel = next(
            (r for r in relationships if r.relationship_type == "LOCATED_AT"),
            None
        )
        assert location_rel is not None


class TestBatchExtraction:
    """Test batch entity extraction."""

    @pytest.fixture
    def mock_extractor(self):
        extractor = NERExtractor(api_key="test-key", batch_size=2)
        extractor.client = AsyncMock()
        return extractor

    @pytest.mark.asyncio
    async def test_batch_extraction(self, mock_extractor):
        """Test extracting from multiple content items."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"entities": []}'
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        mock_extractor.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        items = [
            {"id": "1", "content": "text1"},
            {"id": "2", "content": "text2"},
            {"id": "3", "content": "text3"}
        ]
        
        results = await mock_extractor.extract_batch(items)
        
        assert len(results) == 3


class TestGroundTruthValidation:
    """Validate NER extraction against ground truth."""

    def test_ground_truth_structure(self):
        """Test ground truth data structure."""
        assert len(GROUND_TRUTH_NER) >= 5
        for item in GROUND_TRUTH_NER:
            assert "content_id" in item
            assert "expected_entities" in item

    def test_validation_function(self):
        """Test NER validation function."""
        extracted = [
            {"text": "Professor Jane Smith"},
            {"text": "London Business School"}
        ]
        validation = validate_ner_extraction("gt_ner_001", extracted)
        
        assert "valid" in validation
        assert "recall" in validation
        assert "precision" in validation
        assert "f1_score" in validation


class TestErrorHandling:
    """Test error handling and retry logic."""

    @pytest.fixture
    def mock_extractor(self):
        extractor = NERExtractor(api_key="test-key", max_retries=2)
        extractor.client = AsyncMock()
        return extractor

    @pytest.mark.asyncio
    async def test_json_parse_error_retry(self, mock_extractor):
        """Test retry on JSON parse error."""
        mock_extractor.client.chat.completions.create = AsyncMock(
            side_effect=[
                MagicMock(choices=[MagicMock(message=MagicMock(content="invalid json"))]),
                MagicMock(
                    choices=[MagicMock(message=MagicMock(content='{"entities": []}'))],
                    usage=MagicMock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
                )
            ]
        )
        
        # Should retry and eventually succeed
        result = await mock_extractor.extract_entities_from_content("test", "text")
        assert result is not None

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_extractor):
        """Test handling max retries exceeded."""
        mock_extractor.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Persistent error")
        )
        
        result = await mock_extractor.extract_entities_from_content("test", "text")
        # Should return empty result instead of raising
        assert result.content_id == "test"
        assert len(result.entities) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
