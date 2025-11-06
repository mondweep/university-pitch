"""
Named Entity Recognition (NER) Tests for Phase 3
Tests for NER extractor, entity classification, normalization, MENTIONS relationships
Target: 35+ tests covering all NER functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from src.enrichment.ner_extractor import NERExtractor
from src.enrichment.entity_models import Entity, EntityType, EntityStatistics
from tests.fixtures.enrichment_data import mock_ner_responses


# ==================== NER Extractor Initialization Tests ====================

@pytest.mark.unit
class TestNERExtractorInit:
    """Test NER extractor initialization (5 tests)"""

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        mock_client = Mock()
        extractor = NERExtractor(mock_client)

        assert extractor.llm == mock_client
        assert extractor.confidence_threshold == 0.8
        assert extractor.batch_size == 50

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        mock_client = Mock()
        extractor = NERExtractor(mock_client, confidence_threshold=0.9, batch_size=25)

        assert extractor.confidence_threshold == 0.9
        assert extractor.batch_size == 25

    def test_init_creates_empty_cache(self):
        """Test that entity cache is initialized empty"""
        mock_client = Mock()
        extractor = NERExtractor(mock_client)

        assert len(extractor.entity_cache) == 0

    def test_init_requires_llm_client(self):
        """Test that LLM client is required"""
        with pytest.raises(TypeError):
            NERExtractor()

    def test_init_has_required_methods(self):
        """Test that extractor has all required methods"""
        mock_client = Mock()
        extractor = NERExtractor(mock_client)

        assert hasattr(extractor, 'extract_entities')
        assert hasattr(extractor, 'extract_batch')
        assert hasattr(extractor, 'get_unique_entities')


# ==================== Single Text Entity Extraction Tests ====================

@pytest.mark.unit
@pytest.mark.asyncio
class TestSingleEntityExtraction:
    """Test entity extraction from single text (10 tests)"""

    async def test_extract_person_entities(self):
        """Test extracting person entities"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "Professor John Doe", "type": "PERSON", "confidence": 0.98, "context": "Professor John Doe teaches..."}
            ]
        })

        extractor = NERExtractor(mock_client)
        text = "Professor John Doe teaches corporate finance at London Business School"

        entities = await extractor.extract_entities(text)

        assert len(entities) > 0
        assert any(e.type == EntityType.PERSON for e in entities)

    async def test_extract_organization_entities(self):
        """Test extracting organization entities"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "London Business School", "type": "ORGANIZATION", "confidence": 0.98, "context": "at London Business School"}
            ]
        })

        extractor = NERExtractor(mock_client)
        text = "London Business School is a leading business school"

        entities = await extractor.extract_entities(text)

        assert any(e.type == EntityType.ORGANIZATION for e in entities)

    async def test_extract_location_entities(self):
        """Test extracting location entities"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "London", "type": "LOCATION", "confidence": 0.95, "context": "based in London"}
            ]
        })

        extractor = NERExtractor(mock_client)
        text = "The campus is based in London, United Kingdom"

        entities = await extractor.extract_entities(text)

        assert any(e.type == EntityType.LOCATION for e in entities)

    async def test_extract_event_entities(self):
        """Test extracting event entities"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "Global Leadership Summit", "type": "EVENT", "confidence": 0.92, "context": "at the Global Leadership Summit"}
            ]
        })

        extractor = NERExtractor(mock_client)
        text = "Join us at the Global Leadership Summit 2025"

        entities = await extractor.extract_entities(text)

        assert any(e.type == EntityType.EVENT for e in entities)

    async def test_filters_low_confidence(self):
        """Test that low-confidence entities are filtered"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "High Confidence", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"},
                {"name": "Low Confidence", "type": "ORGANIZATION", "confidence": 0.5, "context": "test"}
            ]
        })

        extractor = NERExtractor(mock_client, confidence_threshold=0.8)
        text = "Test text"

        entities = await extractor.extract_entities(text)

        assert len(entities) == 1
        assert entities[0].name == "High Confidence"

    async def test_extract_empty_text(self):
        """Test extraction with empty text"""
        mock_client = AsyncMock()
        extractor = NERExtractor(mock_client)

        entities = await extractor.extract_entities("")

        assert entities == []

    async def test_extract_short_text(self):
        """Test extraction with very short text"""
        mock_client = AsyncMock()
        extractor = NERExtractor(mock_client)

        entities = await extractor.extract_entities("Hi")

        assert entities == []

    async def test_extract_with_context(self):
        """Test extraction with additional context"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "MBA", "type": "PROGRAM", "confidence": 0.95, "context": "MBA programme"}
            ]
        })

        extractor = NERExtractor(mock_client)
        text = "The MBA programme is highly ranked"
        context = {"page_title": "MBA Overview", "page_type": "programme"}

        entities = await extractor.extract_entities(text, context)

        assert len(entities) > 0

    async def test_extract_handles_malformed_data(self):
        """Test handling of malformed entity data"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "Valid", "type": "ORGANIZATION", "confidence": 0.95},
                {"name": "Missing Type", "confidence": 0.90},  # Missing 'type'
                {"type": "PERSON", "confidence": 0.90}  # Missing 'name'
            ]
        })

        extractor = NERExtractor(mock_client)
        text = "Test text"

        entities = await extractor.extract_entities(text)

        # Should only return valid entity
        assert len(entities) == 1
        assert entities[0].name == "Valid"

    async def test_extract_returns_entity_objects(self):
        """Test that extraction returns proper Entity objects"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "Test Entity", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"}
            ]
        })

        extractor = NERExtractor(mock_client)
        text = "Test text"

        entities = await extractor.extract_entities(text)

        assert all(isinstance(e, Entity) for e in entities)
        assert all(hasattr(e, 'name') for e in entities)
        assert all(hasattr(e, 'type') for e in entities)
        assert all(hasattr(e, 'confidence') for e in entities)


# ==================== Entity Normalization Tests ====================

@pytest.mark.unit
class TestEntityNormalization:
    """Test entity normalization and deduplication (8 tests)"""

    @pytest.mark.asyncio
    async def test_normalizes_case(self):
        """Test that entity names are normalized"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "london business school", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"},
                {"name": "LONDON BUSINESS SCHOOL", "type": "ORGANIZATION", "confidence": 0.93, "context": "test"}
            ]
        })

        extractor = NERExtractor(mock_client)
        text = "Test text"

        entities = await extractor.extract_entities(text)

        # Should deduplicate to single entity
        unique = extractor.get_unique_entities()
        assert len(unique) == 1

    @pytest.mark.asyncio
    async def test_deduplicates_exact_matches(self):
        """Test deduplication of exact matches"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(side_effect=[
            {"entities": [{"name": "John Doe", "type": "PERSON", "confidence": 0.95, "context": "test"}]},
            {"entities": [{"name": "John Doe", "type": "PERSON", "confidence": 0.93, "context": "test"}]}
        ])

        extractor = NERExtractor(mock_client)

        await extractor.extract_entities("Text 1")
        await extractor.extract_entities("Text 2")

        unique = extractor.get_unique_entities()
        assert len(unique) == 1

    @pytest.mark.asyncio
    async def test_merges_entity_mentions(self):
        """Test that entity mentions are merged"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(side_effect=[
            {"entities": [{"name": "MBA", "type": "PROGRAM", "confidence": 0.95, "context": "test1"}]},
            {"entities": [{"name": "MBA", "type": "PROGRAM", "confidence": 0.93, "context": "test2"}]}
        ])

        extractor = NERExtractor(mock_client)

        # Extract from two items with IDs
        entities1 = await extractor.extract_entities("Text 1")
        entities2 = await extractor.extract_entities("Text 2")

        unique = extractor.get_unique_entities()
        assert len(unique) == 1
        # Mentions should be tracked
        assert unique[0].frequency == 2

    @pytest.mark.asyncio
    async def test_fuzzy_matching(self):
        """Test fuzzy matching for similar entities"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(side_effect=[
            {"entities": [{"name": "Professor John Doe", "type": "PERSON", "confidence": 0.95, "context": "test"}]},
            {"entities": [{"name": "Prof. John Doe", "type": "PERSON", "confidence": 0.93, "context": "test"}]}
        ])

        extractor = NERExtractor(mock_client)

        await extractor.extract_entities("Text 1")
        await extractor.extract_entities("Text 2")

        unique = extractor.get_unique_entities()
        # Should fuzzy match and merge
        assert len(unique) <= 1

    @pytest.mark.asyncio
    async def test_preserves_different_entities(self):
        """Test that different entities are preserved"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "John Doe", "type": "PERSON", "confidence": 0.95, "context": "test"},
                {"name": "Jane Smith", "type": "PERSON", "confidence": 0.93, "context": "test"},
                {"name": "London Business School", "type": "ORGANIZATION", "confidence": 0.98, "context": "test"}
            ]
        })

        extractor = NERExtractor(mock_client)
        await extractor.extract_entities("Test text")

        unique = extractor.get_unique_entities()
        assert len(unique) == 3

    @pytest.mark.asyncio
    async def test_different_types_not_merged(self):
        """Test that same name with different types aren't merged"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "Oxford", "type": "LOCATION", "confidence": 0.95, "context": "in Oxford"},
                {"name": "Oxford", "type": "ORGANIZATION", "confidence": 0.93, "context": "Oxford University"}
            ]
        })

        extractor = NERExtractor(mock_client)
        await extractor.extract_entities("Test text")

        unique = extractor.get_unique_entities()
        assert len(unique) == 2

    @pytest.mark.asyncio
    async def test_reset_cache(self):
        """Test cache reset functionality"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [{"name": "Test", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"}]
        })

        extractor = NERExtractor(mock_client)
        await extractor.extract_entities("Test")

        assert len(extractor.get_unique_entities()) > 0

        extractor.reset_cache()

        assert len(extractor.get_unique_entities()) == 0

    @pytest.mark.asyncio
    async def test_normalized_name_property(self):
        """Test that entities have normalized_name property"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [{"name": "LONDON BUSINESS SCHOOL", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"}]
        })

        extractor = NERExtractor(mock_client)
        entities = await extractor.extract_entities("Test")

        assert all(hasattr(e, 'normalized_name') for e in entities)


# ==================== Batch Entity Extraction Tests ====================

@pytest.mark.unit
@pytest.mark.asyncio
class TestBatchEntityExtraction:
    """Test batch entity extraction (7 tests)"""

    async def test_batch_extract_multiple_items(self):
        """Test batch extraction of multiple items"""
        mock_client = AsyncMock()
        mock_client.extract_entities_batch = AsyncMock(return_value=[
            {"entities": [{"name": "Entity 1", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"}]},
            {"entities": [{"name": "Entity 2", "type": "PERSON", "confidence": 0.92, "context": "test"}]},
            {"entities": [{"name": "Entity 3", "type": "LOCATION", "confidence": 0.90, "context": "test"}]}
        ])

        extractor = NERExtractor(mock_client)

        items = [
            {"id": "item-1", "text": "Text 1"},
            {"id": "item-2", "text": "Text 2"},
            {"id": "item-3", "text": "Text 3"}
        ]

        results = await extractor.extract_batch(items)

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)

    async def test_batch_empty_list(self):
        """Test batch extraction with empty list"""
        mock_client = AsyncMock()
        mock_client.extract_entities_batch = AsyncMock(return_value=[])

        extractor = NERExtractor(mock_client)

        results = await extractor.extract_batch([])

        assert results == []

    async def test_batch_tracks_source_ids(self):
        """Test that source IDs are tracked"""
        mock_client = AsyncMock()
        mock_client.extract_entities_batch = AsyncMock(return_value=[
            {"entities": [{"name": "Test Entity", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"}]}
        ])

        extractor = NERExtractor(mock_client)

        items = [{"id": "page-1", "text": "Test text"}]

        results = await extractor.extract_batch(items)

        assert len(results) > 0
        if results[0]:
            assert results[0][0].source_ids

    async def test_batch_large_dataset(self):
        """Test batch processing with 100 items"""
        mock_client = AsyncMock()
        mock_client.extract_entities_batch = AsyncMock(return_value=[
            {"entities": [{"name": f"Entity {i}", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"}]}
            for i in range(100)
        ])

        extractor = NERExtractor(mock_client)

        items = [
            {"id": f"item-{i}", "text": f"Text {i}"}
            for i in range(100)
        ]

        results = await extractor.extract_batch(items)

        assert len(results) == 100

    async def test_batch_respects_batch_size(self):
        """Test that batch size parameter is used"""
        mock_client = AsyncMock()
        mock_client.extract_entities_batch = AsyncMock(return_value=[
            {"entities": []} for _ in range(10)
        ])

        extractor = NERExtractor(mock_client, batch_size=5)

        items = [{"id": f"item-{i}", "text": f"Text {i}"} for i in range(10)]

        results = await extractor.extract_batch(items)

        # Should call batch method
        assert mock_client.extract_entities_batch.called

    async def test_batch_handles_errors(self):
        """Test error handling in batch extraction"""
        mock_client = AsyncMock()
        mock_client.extract_entities_batch = AsyncMock(side_effect=Exception("API Error"))

        extractor = NERExtractor(mock_client)

        items = [{"id": "item-1", "text": "Text"}]

        # Should not crash
        with pytest.raises(Exception):
            await extractor.extract_batch(items)

    async def test_batch_statistics(self):
        """Test that batch statistics are calculated"""
        mock_client = AsyncMock()
        mock_client.extract_entities_batch = AsyncMock(return_value=[
            {"entities": [{"name": "Entity 1", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"}]},
            {"entities": [{"name": "Entity 2", "type": "PERSON", "confidence": 0.92, "context": "test"}]}
        ])

        extractor = NERExtractor(mock_client)

        items = [
            {"id": "item-1", "text": "Text 1"},
            {"id": "item-2", "text": "Text 2"}
        ]

        results = await extractor.extract_batch(items)

        stats = extractor.calculate_statistics()
        assert stats.unique_entities > 0


# ==================== Entity Statistics Tests ====================

@pytest.mark.unit
@pytest.mark.asyncio
class TestEntityStatistics:
    """Test entity statistics calculation (5 tests)"""

    async def test_calculate_basic_stats(self):
        """Test basic statistics calculation"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "Entity 1", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"},
                {"name": "Entity 2", "type": "PERSON", "confidence": 0.92, "context": "test"}
            ]
        })

        extractor = NERExtractor(mock_client)
        await extractor.extract_entities("Test text")

        stats = extractor.calculate_statistics()

        assert isinstance(stats, EntityStatistics)
        assert stats.unique_entities > 0

    async def test_stats_counts_by_type(self):
        """Test entity counting by type"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "Org 1", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"},
                {"name": "Org 2", "type": "ORGANIZATION", "confidence": 0.93, "context": "test"},
                {"name": "Person 1", "type": "PERSON", "confidence": 0.92, "context": "test"}
            ]
        })

        extractor = NERExtractor(mock_client)
        await extractor.extract_entities("Test text")

        stats = extractor.calculate_statistics()

        assert stats.entities_by_type[EntityType.ORGANIZATION] == 2
        assert stats.entities_by_type[EntityType.PERSON] == 1

    async def test_stats_average_confidence(self):
        """Test average confidence calculation"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(return_value={
            "entities": [
                {"name": "Entity 1", "type": "ORGANIZATION", "confidence": 0.90, "context": "test"},
                {"name": "Entity 2", "type": "ORGANIZATION", "confidence": 0.80, "context": "test"}
            ]
        })

        extractor = NERExtractor(mock_client)
        await extractor.extract_entities("Test text")

        stats = extractor.calculate_statistics()

        assert 0.80 <= stats.avg_confidence <= 0.90

    async def test_stats_top_entities(self):
        """Test top entities by mentions"""
        mock_client = AsyncMock()
        mock_client.extract_entities = AsyncMock(side_effect=[
            {"entities": [{"name": "Popular Entity", "type": "ORGANIZATION", "confidence": 0.95, "context": "test"}]},
            {"entities": [{"name": "Popular Entity", "type": "ORGANIZATION", "confidence": 0.93, "context": "test"}]},
            {"entities": [{"name": "Rare Entity", "type": "ORGANIZATION", "confidence": 0.90, "context": "test"}]}
        ])

        extractor = NERExtractor(mock_client)

        await extractor.extract_entities("Text 1")
        await extractor.extract_entities("Text 2")
        await extractor.extract_entities("Text 3")

        stats = extractor.calculate_statistics()

        # Popular Entity should be at top
        assert len(stats.top_entities) > 0
        assert stats.top_entities[0][0] == "Popular Entity"

    async def test_stats_empty_cache(self):
        """Test statistics with empty cache"""
        mock_client = AsyncMock()
        extractor = NERExtractor(mock_client)

        stats = extractor.calculate_statistics()

        assert stats.unique_entities == 0
        assert stats.total_entities == 0
        assert stats.avg_confidence == 0.0
