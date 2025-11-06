"""
Tests for Persona Classification functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lbs-knowledge-graph'))
sys.path.insert(0, os.path.dirname(__file__))

from src.enrichment.persona_classifier import PersonaClassifier, PersonaClassification
from src.enrichment.persona_models import PersonaType, JourneyStage, get_persona_by_name
from fixtures.ground_truth_personas import GROUND_TRUTH_PERSONAS, validate_persona_classification
from fixtures.mock_llm_responses import PERSONA_MOCK_RESPONSES


class TestPersonaClassification:
    """Test PersonaClassification model."""

    def test_classification_creation(self):
        """Test creating persona classification."""
        classification = PersonaClassification(
            content_id="test1",
            content_type="page",
            personas=[{"persona_name": "Prospective Students", "relevance": 0.9}],
            primary_persona="Prospective Students",
            multi_target=False
        )
        assert classification.content_id == "test1"
        assert len(classification.personas) == 1

    def test_to_dict(self):
        """Test converting to dictionary."""
        classification = PersonaClassification(
            content_id="test1",
            content_type="page",
            personas=[],
            primary_persona=None
        )
        data = classification.to_dict()
        assert isinstance(data, dict)
        assert "content_id" in data


class TestPersonaClassifier:
    """Test PersonaClassifier with mocked LLM."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = Mock()
        client.model = "gpt-4o-mini"
        client.client = AsyncMock()
        client.api_calls = 0
        client.total_tokens = 0
        client.total_cost = 0.0
        client.pricing = {"gpt-4o-mini": {"input": 0.00015, "output": 0.0006}}
        client.get_stats = Mock(return_value={})
        return client

    @pytest.fixture
    def mock_graph(self):
        """Create mock graph connection."""
        graph = Mock()
        graph.execute_and_fetch = Mock(return_value=[])
        return graph

    @pytest.fixture
    def classifier(self, mock_llm_client, mock_graph):
        """Create classifier instance."""
        return PersonaClassifier(
            llm_client=mock_llm_client,
            graph=mock_graph,
            min_relevance=0.6,
            batch_size=10
        )

    @pytest.mark.asyncio
    async def test_classify_prospective_students(self, classifier, mock_llm_client):
        """Test classifying content for prospective students."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = PERSONA_MOCK_RESPONSES["prospective_students"]["content"]
        mock_response.usage.prompt_tokens = 120
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 220
        
        mock_llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        item = {
            "id": "test1",
            "title": "MBA Programme",
            "text": "Apply to our MBA programme"
        }
        
        result = await classifier._classify_item(item, "page")
        
        assert result is not None
        assert result.primary_persona is not None
        assert len(result.personas) >= 1
        assert result.personas[0]["persona_name"] == "Prospective Students"

    @pytest.mark.asyncio
    async def test_classify_multi_target(self, classifier, mock_llm_client):
        """Test classifying multi-target content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = PERSONA_MOCK_RESPONSES["multi_target"]["content"]
        mock_response.usage.prompt_tokens = 120
        mock_response.usage.completion_tokens = 150
        mock_response.usage.total_tokens = 270
        
        mock_llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        item = {
            "id": "test2",
            "title": "Programme Info",
            "text": "Information for prospective and current students"
        }
        
        result = await classifier._classify_item(item, "page")
        
        assert result.multi_target == True
        assert len(result.personas) > 1

    @pytest.mark.asyncio
    async def test_relevance_filtering(self, classifier, mock_llm_client):
        """Test filtering personas by minimum relevance."""
        # Mock response with low relevance persona
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"personas": [{"persona": "Alumni", "relevance": 0.4, "is_primary": true, "journey_stage": "retention", "signals": [], "intent": ""}]}'
        mock_response.usage.prompt_tokens = 120
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 220
        
        mock_llm_client.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        item = {"id": "test3", "title": "Test", "text": "content"}
        result = await classifier._classify_item(item, "page")
        
        # Should be filtered out due to low relevance
        assert result is None or len(result.personas) == 0


class TestPersonaParsingAndValidation:
    """Test persona result parsing and validation."""

    @pytest.fixture
    def classifier(self):
        mock_client = Mock()
        mock_graph = Mock()
        return PersonaClassifier(mock_client, mock_graph)

    def test_parse_valid_persona(self, classifier):
        """Test parsing valid persona result."""
        results = [{
            "persona": "Prospective Students",
            "relevance": 0.9,
            "is_primary": True,
            "journey_stage": "consideration",
            "signals": ["mba", "apply"],
            "intent": "Inform about programmes"
        }]
        
        parsed = classifier.parse_persona_results(results)
        
        assert len(parsed) == 1
        assert parsed[0]["persona_name"] == "Prospective Students"
        assert parsed[0]["relevance"] == 0.9
        assert parsed[0]["journey_stage"] == "consideration"

    def test_parse_invalid_persona_name(self, classifier):
        """Test handling invalid persona name."""
        results = [{
            "persona": "Invalid Persona",
            "relevance": 0.9,
            "is_primary": True,
            "journey_stage": "awareness",
            "signals": [],
            "intent": ""
        }]
        
        parsed = classifier.parse_persona_results(results)
        
        # Should be filtered out
        assert len(parsed) == 0

    def test_identify_primary_persona(self, classifier):
        """Test identifying primary persona."""
        personas = [
            {"persona_id": "p1", "relevance": 0.85, "is_primary": False},
            {"persona_id": "p2", "relevance": 0.92, "is_primary": False}
        ]
        
        primary = classifier.identify_primary_persona(personas)
        
        # Should be highest relevance
        assert primary == "p2"

    def test_primary_persona_explicitly_marked(self, classifier):
        """Test explicitly marked primary persona."""
        personas = [
            {"persona_id": "p1", "relevance": 0.85, "is_primary": True},
            {"persona_id": "p2", "relevance": 0.92, "is_primary": False}
        ]
        
        primary = classifier.identify_primary_persona(personas)
        
        # Should respect explicit marking
        assert primary == "p1"


class TestStatistics:
    """Test statistics calculation."""

    @pytest.fixture
    def classifier_with_data(self):
        mock_client = Mock()
        mock_graph = Mock()
        classifier = PersonaClassifier(mock_client, mock_graph)
        
        # Add mock classifications
        classifier.classifications = [
            PersonaClassification(
                content_id="1",
                content_type="page",
                personas=[
                    {"persona_name": "Prospective Students", "relevance": 0.9},
                    {"persona_name": "Current Students", "relevance": 0.7}
                ],
                primary_persona="Prospective Students",
                multi_target=True
            ),
            PersonaClassification(
                content_id="2",
                content_type="page",
                personas=[
                    {"persona_name": "Alumni", "relevance": 0.85}
                ],
                primary_persona="Alumni",
                multi_target=False
            )
        ]
        classifier.total_processed = 2
        classifier.multi_target_count = 1
        
        return classifier

    def test_get_statistics(self, classifier_with_data):
        """Test statistics calculation."""
        stats = classifier_with_data.get_statistics()
        
        assert stats["total_classified"] == 2
        assert stats["multi_target_count"] == 1
        assert stats["multi_target_rate"] == 0.5
        assert "persona_distribution" in stats
        assert "avg_personas_per_content" in stats


class TestGroundTruthValidation:
    """Validate persona classification against ground truth."""

    def test_ground_truth_structure(self):
        """Test ground truth data structure."""
        assert len(GROUND_TRUTH_PERSONAS) >= 5
        for item in GROUND_TRUTH_PERSONAS:
            assert "content_id" in item
            assert "expected_personas" in item
            assert "expected_primary" in item

    def test_validation_function(self):
        """Test persona validation function."""
        personas = [{"persona_name": "Prospective Students"}]
        validation = validate_persona_classification(
            "gt_persona_001",
            personas,
            "Prospective Students"
        )
        
        assert "valid" in validation
        assert "primary_correct" in validation
        assert "recall" in validation

    def test_multi_target_detection(self):
        """Test multi-target content detection."""
        personas = [
            {"persona_name": "Prospective Students"},
            {"persona_name": "Current Students"}
        ]
        validation = validate_persona_classification(
            "gt_persona_005",
            personas,
            "Prospective Students"
        )
        
        assert "multi_target_correct" in validation


class TestJourneyStageMapping:
    """Test journey stage mapping."""

    @pytest.fixture
    def classifier(self):
        mock_client = Mock()
        mock_graph = Mock()
        return PersonaClassifier(mock_client, mock_graph)

    def test_journey_stage_parsing(self, classifier):
        """Test parsing journey stages."""
        results = [{
            "persona": "Prospective Students",
            "relevance": 0.9,
            "is_primary": True,
            "journey_stage": "consideration",
            "signals": [],
            "intent": ""
        }]
        
        parsed = classifier.parse_persona_results(results)
        
        assert parsed[0]["journey_stage"] == "consideration"

    def test_invalid_journey_stage(self, classifier):
        """Test handling invalid journey stage."""
        results = [{
            "persona": "Prospective Students",
            "relevance": 0.9,
            "is_primary": True,
            "journey_stage": "invalid_stage",
            "signals": [],
            "intent": ""
        }]
        
        parsed = classifier.parse_persona_results(results)
        
        # Should default to awareness
        assert parsed[0]["journey_stage"] == "awareness"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
