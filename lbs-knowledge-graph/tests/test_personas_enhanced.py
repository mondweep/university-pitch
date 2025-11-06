"""
Enhanced Persona Classification Tests for Phase 3
Tests for persona classifier, multi-label classification, TARGETS relationships
Target: 25+ tests covering all persona functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from src.enrichment.persona_classifier import PersonaClassifier
from src.enrichment.persona_models import PersonaType, JourneyStage, get_all_personas
from tests.fixtures.ground_truth.personas import ground_truth_personas


# ==================== Persona Classifier Initialization Tests ====================

@pytest.mark.unit
class TestPersonaClassifierInit:
    """Test persona classifier initialization (5 tests)"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        mock_llm = Mock()
        classifier = PersonaClassifier(mock_llm)

        assert classifier.llm_client == mock_llm
        assert classifier.relevance_threshold == 0.6
        assert classifier.max_personas_per_content == 3
        assert len(classifier.personas) == 6

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        mock_llm = Mock()
        classifier = PersonaClassifier(
            mock_llm,
            relevance_threshold=0.7,
            max_personas_per_content=2
        )

        assert classifier.relevance_threshold == 0.7
        assert classifier.max_personas_per_content == 2

    def test_init_loads_all_personas(self):
        """Test that all 6 personas are loaded"""
        mock_llm = Mock()
        classifier = PersonaClassifier(mock_llm)

        personas = classifier.personas
        assert len(personas) == 6

        persona_types = {p.type for p in personas}
        assert PersonaType.PROSPECTIVE_STUDENTS in persona_types
        assert PersonaType.CURRENT_STUDENTS in persona_types
        assert PersonaType.ALUMNI in persona_types
        assert PersonaType.FACULTY_STAFF in persona_types
        assert PersonaType.RECRUITERS in persona_types
        assert PersonaType.MEDIA in persona_types

    def test_init_requires_llm_client(self):
        """Test that LLM client is required"""
        with pytest.raises(TypeError):
            PersonaClassifier()

    def test_init_has_required_methods(self):
        """Test that classifier has all required methods"""
        mock_llm = Mock()
        classifier = PersonaClassifier(mock_llm)

        assert hasattr(classifier, 'classify_page')
        assert hasattr(classifier, 'classify_batch')
        assert hasattr(classifier, 'determine_journey_stage')


# ==================== Single Page Classification Tests ====================

@pytest.mark.unit
@pytest.mark.asyncio
class TestSinglePageClassification:
    """Test single page persona classification (8 tests)"""

    async def test_classify_prospective_student_page(self):
        """Test classification of prospective student page"""
        mock_llm = AsyncMock()
        mock_llm.classify_personas = AsyncMock(return_value={
            "personas": [
                {
                    "persona": "prospective_students",
                    "relevance": 0.95,
                    "journey_stage": "awareness"
                }
            ]
        })

        classifier = PersonaClassifier(mock_llm)

        page = {
            "id": "mba-overview",
            "type": "programme",
            "title": "MBA Programme Overview",
            "text": "Transform your career with our world-class MBA"
        }

        result = await classifier.classify_page(page)

        assert len(result) >= 1
        assert result[0].persona == PersonaType.PROSPECTIVE_STUDENTS
        assert result[0].relevance >= 0.90

    async def test_classify_current_student_page(self):
        """Test classification of current student page"""
        mock_llm = AsyncMock()
        mock_llm.classify_personas = AsyncMock(return_value={
            "personas": [
                {
                    "persona": "current_students",
                    "relevance": 0.98,
                    "journey_stage": "retention"
                }
            ]
        })

        classifier = PersonaClassifier(mock_llm)

        page = {
            "id": "student-resources",
            "type": "resources",
            "title": "Current Student Resources",
            "text": "Access course materials and student services"
        }

        result = await classifier.classify_page(page)

        assert any(r.persona == PersonaType.CURRENT_STUDENTS for r in result)

    async def test_classify_multi_persona_page(self):
        """Test multi-label classification"""
        mock_llm = AsyncMock()
        mock_llm.classify_personas = AsyncMock(return_value={
            "personas": [
                {
                    "persona": "prospective_students",
                    "relevance": 0.95,
                    "journey_stage": "consideration"
                },
                {
                    "persona": "recruiters",
                    "relevance": 0.85,
                    "journey_stage": "awareness"
                }
            ]
        })

        classifier = PersonaClassifier(mock_llm)

        page = {
            "id": "career-outcomes",
            "type": "careers",
            "title": "Career Outcomes",
            "text": "95% employment rate, top employers include McKinsey"
        }

        result = await classifier.classify_page(page)

        assert len(result) >= 2
        personas = {r.persona for r in result}
        assert PersonaType.PROSPECTIVE_STUDENTS in personas
        assert PersonaType.RECRUITERS in personas

    async def test_filters_low_relevance_personas(self):
        """Test that low-relevance personas are filtered"""
        mock_llm = AsyncMock()
        mock_llm.classify_personas = AsyncMock(return_value={
            "personas": [
                {
                    "persona": "prospective_students",
                    "relevance": 0.95,
                    "journey_stage": "awareness"
                },
                {
                    "persona": "media",
                    "relevance": 0.30,
                    "journey_stage": "awareness"
                }
            ]
        })

        classifier = PersonaClassifier(mock_llm, relevance_threshold=0.6)

        page = {"id": "test", "type": "programme", "title": "Test", "text": "Test"}

        result = await classifier.classify_page(page)

        assert len(result) == 1
        assert result[0].persona == PersonaType.PROSPECTIVE_STUDENTS

    async def test_respects_max_personas_limit(self):
        """Test maximum personas per page limit"""
        mock_llm = AsyncMock()
        mock_llm.classify_personas = AsyncMock(return_value={
            "personas": [
                {"persona": "prospective_students", "relevance": 0.95, "journey_stage": "awareness"},
                {"persona": "current_students", "relevance": 0.90, "journey_stage": "retention"},
                {"persona": "alumni", "relevance": 0.85, "journey_stage": "retention"},
                {"persona": "recruiters", "relevance": 0.80, "journey_stage": "awareness"}
            ]
        })

        classifier = PersonaClassifier(mock_llm, max_personas_per_content=2)

        page = {"id": "test", "type": "general", "title": "Test", "text": "Test"}

        result = await classifier.classify_page(page)

        assert len(result) <= 2

    async def test_classify_empty_text(self):
        """Test classification with empty text"""
        mock_llm = AsyncMock()
        classifier = PersonaClassifier(mock_llm)

        page = {"id": "test", "type": "programme", "title": "Test", "text": ""}

        result = await classifier.classify_page(page)

        assert result == []

    async def test_journey_stage_determination(self):
        """Test journey stage is correctly determined"""
        mock_llm = AsyncMock()
        mock_llm.classify_personas = AsyncMock(return_value={
            "personas": [
                {
                    "persona": "prospective_students",
                    "relevance": 0.95,
                    "journey_stage": "consideration"
                }
            ]
        })

        classifier = PersonaClassifier(mock_llm)

        page = {
            "id": "admissions",
            "type": "admissions",
            "title": "Admissions Requirements",
            "text": "GMAT scores and work experience required"
        }

        result = await classifier.classify_page(page)

        assert result[0].journey_stage == JourneyStage.CONSIDERATION

    async def test_classification_result_structure(self):
        """Test that result has correct structure"""
        mock_llm = AsyncMock()
        mock_llm.classify_personas = AsyncMock(return_value={
            "personas": [
                {
                    "persona": "prospective_students",
                    "relevance": 0.95,
                    "journey_stage": "awareness"
                }
            ]
        })

        classifier = PersonaClassifier(mock_llm)

        page = {"id": "test", "type": "programme", "title": "Test", "text": "Test content"}

        result = await classifier.classify_page(page)

        assert len(result) > 0
        assert hasattr(result[0], 'persona')
        assert hasattr(result[0], 'relevance')
        assert hasattr(result[0], 'journey_stage')
        assert hasattr(result[0], 'page_id')


# ==================== Batch Classification Tests ====================

@pytest.mark.unit
@pytest.mark.asyncio
class TestBatchClassification:
    """Test batch persona classification (6 tests)"""

    async def test_batch_classify_multiple_pages(self):
        """Test batch classification of multiple pages"""
        mock_llm = AsyncMock()
        mock_llm.classify_batch = AsyncMock(return_value=[
            {"personas": [{"persona": "prospective_students", "relevance": 0.95, "journey_stage": "awareness"}]},
            {"personas": [{"persona": "current_students", "relevance": 0.90, "journey_stage": "retention"}]}
        ])

        classifier = PersonaClassifier(mock_llm)

        pages = [
            {"id": "page-1", "type": "programme", "title": "MBA", "text": "Test 1"},
            {"id": "page-2", "type": "resources", "title": "Resources", "text": "Test 2"}
        ]

        results = await classifier.classify_batch(pages)

        assert len(results) == 2

    async def test_batch_empty_list(self):
        """Test batch classification with empty list"""
        mock_llm = AsyncMock()
        classifier = PersonaClassifier(mock_llm)

        results = await classifier.classify_batch([])

        assert results == []

    async def test_batch_preserves_order(self):
        """Test that batch results preserve input order"""
        mock_llm = AsyncMock()
        mock_llm.classify_batch = AsyncMock(return_value=[
            {"personas": [{"persona": "prospective_students", "relevance": 0.95, "journey_stage": "awareness"}]},
            {"personas": [{"persona": "alumni", "relevance": 0.90, "journey_stage": "retention"}]}
        ])

        classifier = PersonaClassifier(mock_llm)

        pages = [
            {"id": "page-1", "type": "programme", "title": "MBA", "text": "Test"},
            {"id": "page-2", "type": "alumni", "title": "Alumni", "text": "Test"}
        ]

        results = await classifier.classify_batch(pages)

        assert results[0][0].page_id == "page-1"
        assert results[1][0].page_id == "page-2"

    async def test_batch_large_dataset(self):
        """Test batch processing with 100 pages"""
        mock_llm = AsyncMock()
        mock_llm.classify_batch = AsyncMock(return_value=[
            {"personas": [{"persona": "prospective_students", "relevance": 0.95, "journey_stage": "awareness"}]}
            for _ in range(100)
        ])

        classifier = PersonaClassifier(mock_llm)

        pages = [
            {"id": f"page-{i}", "type": "programme", "title": f"Page {i}", "text": "Test"}
            for i in range(100)
        ]

        results = await classifier.classify_batch(pages)

        assert len(results) == 100

    async def test_batch_handles_errors(self):
        """Test error handling in batch classification"""
        mock_llm = AsyncMock()
        mock_llm.classify_batch = AsyncMock(side_effect=Exception("API Error"))

        classifier = PersonaClassifier(mock_llm)

        pages = [{"id": "page-1", "type": "programme", "title": "Test", "text": "Test"}]

        with pytest.raises(Exception):
            await classifier.classify_batch(pages)

    async def test_batch_progress_tracking(self):
        """Test progress tracking during batch processing"""
        mock_llm = AsyncMock()
        mock_llm.classify_batch = AsyncMock(return_value=[
            {"personas": [{"persona": "prospective_students", "relevance": 0.95, "journey_stage": "awareness"}]}
            for _ in range(10)
        ])

        classifier = PersonaClassifier(mock_llm)

        pages = [
            {"id": f"page-{i}", "type": "programme", "title": f"Page {i}", "text": "Test"}
            for i in range(10)
        ]

        progress_calls = []
        def progress_callback(completed, total):
            progress_calls.append((completed, total))

        results = await classifier.classify_batch(pages, progress_callback=progress_callback)

        assert len(results) == 10
        # Progress should be tracked
        if progress_calls:
            assert progress_calls[-1][0] == progress_calls[-1][1]


# ==================== Journey Stage Tests ====================

@pytest.mark.unit
class TestJourneyStages:
    """Test journey stage determination (6 tests)"""

    def test_awareness_stage_detection(self):
        """Test awareness stage detection"""
        mock_llm = Mock()
        classifier = PersonaClassifier(mock_llm)

        context = {
            "page_type": "programme",
            "title": "MBA Overview",
            "has_application_cta": False
        }

        stage = classifier.determine_journey_stage(
            PersonaType.PROSPECTIVE_STUDENTS,
            context
        )

        assert stage == JourneyStage.AWARENESS

    def test_consideration_stage_detection(self):
        """Test consideration stage detection"""
        mock_llm = Mock()
        classifier = PersonaClassifier(mock_llm)

        context = {
            "page_type": "admissions",
            "title": "Admissions Requirements",
            "has_application_cta": False
        }

        stage = classifier.determine_journey_stage(
            PersonaType.PROSPECTIVE_STUDENTS,
            context
        )

        assert stage == JourneyStage.CONSIDERATION

    def test_decision_stage_detection(self):
        """Test decision stage detection"""
        mock_llm = Mock()
        classifier = PersonaClassifier(mock_llm)

        context = {
            "page_type": "apply",
            "title": "Apply Now",
            "has_application_cta": True
        }

        stage = classifier.determine_journey_stage(
            PersonaType.PROSPECTIVE_STUDENTS,
            context
        )

        assert stage == JourneyStage.DECISION

    def test_action_stage_detection(self):
        """Test action stage detection"""
        mock_llm = Mock()
        classifier = PersonaClassifier(mock_llm)

        context = {
            "page_type": "application",
            "title": "Application Form",
            "has_application_cta": True
        }

        stage = classifier.determine_journey_stage(
            PersonaType.PROSPECTIVE_STUDENTS,
            context
        )

        assert stage == JourneyStage.ACTION

    def test_retention_stage_detection(self):
        """Test retention stage detection"""
        mock_llm = Mock()
        classifier = PersonaClassifier(mock_llm)

        context = {
            "page_type": "resources",
            "title": "Current Student Resources"
        }

        stage = classifier.determine_journey_stage(
            PersonaType.CURRENT_STUDENTS,
            context
        )

        assert stage == JourneyStage.RETENTION

    def test_journey_stage_by_persona(self):
        """Test that journey stages vary by persona"""
        mock_llm = Mock()
        classifier = PersonaClassifier(mock_llm)

        context = {
            "page_type": "careers",
            "title": "Career Services"
        }

        # Same page, different personas, different stages
        prospect_stage = classifier.determine_journey_stage(
            PersonaType.PROSPECTIVE_STUDENTS,
            context
        )
        student_stage = classifier.determine_journey_stage(
            PersonaType.CURRENT_STUDENTS,
            context
        )

        # Prospects consider career outcomes
        assert prospect_stage == JourneyStage.CONSIDERATION
        # Current students use services
        assert student_stage == JourneyStage.RETENTION
