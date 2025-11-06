"""
Named Entity Recognition Extractor
Extracts named entities from page and section content using LLM.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from ..llm.llm_client import LLMClient
from .entity_models import Entity, EntityType, EntityStatistics

logger = logging.getLogger(__name__)


class NERExtractor:
    """Extract named entities from text content."""

    def __init__(
        self,
        llm_client: LLMClient,
        confidence_threshold: float = 0.8,
        batch_size: int = 50
    ):
        """
        Initialize NER extractor.

        Args:
            llm_client: LLM client for entity extraction
            confidence_threshold: Minimum confidence for entities (0-1)
            batch_size: Batch size for processing
        """
        self.llm = llm_client
        self.confidence_threshold = confidence_threshold
        self.batch_size = batch_size

        # Entity deduplication cache
        self.entity_cache: Dict[str, Entity] = {}  # normalized_name -> Entity

        logger.info(f"Initialized NERExtractor (threshold={confidence_threshold})")

    async def extract_entities(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> List[Entity]:
        """
        Extract named entities from text.

        Args:
            text: Text to analyze
            context: Optional context (page title, type, etc.)

        Returns:
            List of Entity objects
        """
        if not text or len(text.strip()) < 10:
            return []

        # Call LLM for entity extraction
        result = await self.llm.extract_entities(text, context)

        entities = []
        for entity_data in result.get("entities", []):
            try:
                # Parse entity
                entity = Entity(
                    name=entity_data["name"],
                    type=EntityType.from_string(entity_data["type"]),
                    confidence=entity_data["confidence"],
                    context=entity_data.get("context", "")[:100]
                )

                # Filter by confidence
                if entity.confidence >= self.confidence_threshold:
                    # Normalize and deduplicate
                    entity = self._normalize_and_deduplicate(entity)
                    entities.append(entity)
                else:
                    logger.debug(
                        f"Filtered low-confidence entity: {entity.name} "
                        f"({entity.confidence:.2f})"
                    )

            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid entity data: {entity_data} - {e}")
                continue

        logger.debug(
            f"Extracted {len(entities)} entities from text "
            f"({len(text)} chars)"
        )

        return entities

    async def extract_batch(
        self,
        items: List[Dict]
    ) -> List[List[Entity]]:
        """
        Extract entities from multiple items in batches.

        Args:
            items: List of dicts with 'id', 'text', and optional 'context'

        Returns:
            List of entity lists (one per item)
        """
        logger.info(f"Starting batch NER extraction for {len(items)} items")

        # Prepare batch items
        batch_items = [
            {
                "text": item.get("text", ""),
                "context": item.get("context", {})
            }
            for item in items
        ]

        # Call LLM batch extraction
        results = await self.llm.extract_entities_batch(
            batch_items,
            batch_size=self.batch_size
        )

        # Process results
        all_entities = []
        for idx, result in enumerate(results):
            item_entities = []

            for entity_data in result.get("entities", []):
                try:
                    entity = Entity(
                        name=entity_data["name"],
                        type=EntityType.from_string(entity_data["type"]),
                        confidence=entity_data["confidence"],
                        context=entity_data.get("context", "")[:100]
                    )

                    # Filter and deduplicate
                    if entity.confidence >= self.confidence_threshold:
                        entity = self._normalize_and_deduplicate(entity)

                        # Track source
                        if "id" in items[idx]:
                            entity.source_ids.append(items[idx]["id"])

                        item_entities.append(entity)

                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid entity in item {idx}: {e}")
                    continue

            all_entities.append(item_entities)

        # Calculate statistics
        total_entities = sum(len(entities) for entities in all_entities)
        unique_entities = len(self.entity_cache)

        logger.info(
            f"Batch extraction complete: {total_entities} total entities, "
            f"{unique_entities} unique entities"
        )

        return all_entities

    def _normalize_and_deduplicate(self, entity: Entity) -> Entity:
        """
        Normalize entity name and deduplicate against cache.

        Args:
            entity: Entity to normalize

        Returns:
            Normalized entity (may be merged with cached entity)
        """
        # Check cache for existing entity
        cached_entity = self.entity_cache.get(entity.normalized_name)

        if cached_entity is not None:
            # Check if it's a true match
            if cached_entity.matches(entity):
                # Merge into cached entity
                cached_entity.merge(entity)
                return cached_entity

        # Check for fuzzy matches in cache
        for cached in self.entity_cache.values():
            if cached.matches(entity, threshold=0.85):
                cached.merge(entity)
                return cached

        # New unique entity - add to cache
        self.entity_cache[entity.normalized_name] = entity

        return entity

    def get_unique_entities(self) -> List[Entity]:
        """
        Get all unique entities from cache.

        Returns:
            List of unique entities
        """
        return list(self.entity_cache.values())

    def calculate_statistics(self) -> EntityStatistics:
        """
        Calculate statistics about extracted entities.

        Returns:
            EntityStatistics object
        """
        stats = EntityStatistics()

        entities = self.get_unique_entities()
        stats.unique_entities = len(entities)

        # Count by type
        type_counts = defaultdict(int)
        total_confidence = 0.0
        total_mentions = 0

        for entity in entities:
            type_counts[entity.type] += 1
            total_confidence += entity.confidence
            mention_count = len(entity.source_ids)
            total_mentions += mention_count

        stats.entities_by_type = dict(type_counts)
        stats.total_entities = total_mentions
        stats.mentions_count = total_mentions
        stats.avg_confidence = (
            total_confidence / stats.unique_entities
            if stats.unique_entities > 0 else 0.0
        )

        # Top entities by mentions
        entity_counts = [
            (entity.name, len(entity.source_ids))
            for entity in entities
        ]
        entity_counts.sort(key=lambda x: x[1], reverse=True)
        stats.top_entities = entity_counts[:20]

        return stats

    def reset_cache(self):
        """Clear entity cache."""
        self.entity_cache.clear()
        logger.info("Entity cache reset")
