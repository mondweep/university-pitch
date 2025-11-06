"""
Entity Graph Builder

Creates entity nodes and relationships (MENTIONS, AFFILIATED_WITH, LOCATED_AT)
in the knowledge graph from NER extraction results.
"""

from typing import List, Dict, Optional
from datetime import datetime
import uuid

from src.graph.mgraph_compat import MGraph
from .entity_models import Entity, EntityMention, EntityRelationship, NERExtractionResult


class EntityGraphBuilder:
    """
    Builds entity nodes and relationships in the knowledge graph.

    Creates Entity nodes and connects them to ContentItem nodes with
    MENTIONS edges. Also creates inter-entity relationships like
    AFFILIATED_WITH and LOCATED_AT.
    """

    def __init__(self, graph: MGraph):
        """
        Initialize entity graph builder.

        Args:
            graph: MGraph instance for graph operations
        """
        self.graph = graph
        self.entity_cache: Dict[str, str] = {}  # Map canonical names to entity IDs

    def build_entities(self, results: List[NERExtractionResult]) -> Dict[str, int]:
        """
        Build entity nodes and relationships from NER results.

        Args:
            results: List of NER extraction results

        Returns:
            Dictionary with statistics (entities_created, mentions_created, etc.)
        """
        stats = {
            "entities_created": 0,
            "entities_updated": 0,
            "mentions_created": 0,
            "relationships_created": 0
        }

        # Process all entities and merge duplicates
        for result in results:
            for entity in result.entities:
                entity_id = self._create_or_update_entity(entity)
                if entity_id:
                    if entity.id == entity_id:
                        stats["entities_created"] += 1
                    else:
                        stats["entities_updated"] += 1

            # Create mentions (edges from content to entities)
            for mention in result.mentions:
                if self._create_mention(mention):
                    stats["mentions_created"] += 1

            # Create entity relationships
            for relationship in result.relationships:
                if self._create_relationship(relationship):
                    stats["relationships_created"] += 1

        return stats

    def _create_or_update_entity(self, entity: Entity) -> Optional[str]:
        """
        Create entity node or update existing entity.

        Merges entities with the same canonical name by:
        - Combining aliases
        - Incrementing mention count
        - Updating prominence (max)
        """
        # Check if entity already exists (by canonical name)
        canonical = entity.canonical_name

        if canonical in self.entity_cache:
            # Update existing entity
            entity_id = self.entity_cache[canonical]

            # Get existing entity data
            existing = self.graph.get_node(entity_id)
            if not existing:
                return None

            # Merge aliases
            existing_aliases = existing.data.get("aliases", [])
            new_aliases = list(set(existing_aliases + entity.aliases + [entity.name]))

            # Update entity by re-adding with merged data
            merged_data = {
                **existing.data,
                "aliases": new_aliases,
                "mention_count": existing.data.get("mention_count", 0) + 1,
                "prominence": max(existing.data.get("prominence", 0), entity.prominence),
                "metadata": {**existing.data.get("metadata", {}), **entity.metadata}
            }
            self.graph.add_node("Entity", entity_id, merged_data)

            return entity_id
        else:
            # Create new entity
            entity_id = entity.id

            self.graph.add_node(
                "Entity",
                entity_id,
                {
                    "name": entity.name,
                    "entity_type": entity.entity_type.value,
                    "canonical_name": entity.canonical_name,
                    "aliases": entity.aliases,
                    "metadata": entity.metadata,
                    "mention_count": entity.mention_count,
                    "first_mentioned": entity.first_mentioned.isoformat() if entity.first_mentioned else None,
                    "prominence": entity.prominence,
                    "confidence": entity.confidence
                }
            )

            # Cache entity
            self.entity_cache[canonical] = entity_id

            return entity_id

    def _create_mention(self, mention: EntityMention) -> bool:
        """
        Create MENTIONS edge from ContentItem to Entity.

        Args:
            mention: EntityMention object

        Returns:
            True if edge created successfully
        """
        try:
            # Get actual entity ID (may have been merged)
            entity_id = mention.entity_id

            # Check if entity exists in cache (it may have been merged)
            entity_node = self.graph.get_node(entity_id)
            if entity_node:
                canonical = entity_node.data.get("canonical_name")
                if canonical and canonical in self.entity_cache:
                    entity_id = self.entity_cache[canonical]

            self.graph.add_edge(
                mention.content_id,
                entity_id,
                "MENTIONS",
                {
                    "entity_text": mention.entity_text,
                    "context": mention.context,
                    "prominence": mention.prominence,
                    "confidence": mention.confidence,
                    "position": mention.position,
                    "extracted_by": mention.extracted_by,
                    "created_at": datetime.now().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"⚠️  Error creating mention: {e}")
            return False

    def _create_relationship(self, relationship: EntityRelationship) -> bool:
        """
        Create relationship edge between entities.

        Args:
            relationship: EntityRelationship object

        Returns:
            True if edge created successfully
        """
        try:
            # Resolve actual entity IDs (may have been merged)
            from_entity = self.graph.get_node(relationship.from_entity_id)
            to_entity = self.graph.get_node(relationship.to_entity_id)

            if not from_entity or not to_entity:
                return False

            # Get canonical IDs
            from_id = self.entity_cache.get(
                from_entity.data.get("canonical_name"),
                relationship.from_entity_id
            )
            to_id = self.entity_cache.get(
                to_entity.data.get("canonical_name"),
                relationship.to_entity_id
            )

            self.graph.add_edge(
                from_id,
                to_id,
                relationship.relationship_type,
                {
                    "confidence": relationship.confidence,
                    "evidence": relationship.evidence,
                    "metadata": relationship.metadata,
                    "created_at": datetime.now().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"⚠️  Error creating relationship: {e}")
            return False

    def get_entity_stats(self) -> Dict[str, int]:
        """
        Get entity statistics from graph.

        Returns:
            Dictionary with entity counts by type
        """
        stats = {
            "total_entities": 0,
            "PERSON": 0,
            "ORGANIZATION": 0,
            "LOCATION": 0,
            "EVENT": 0
        }

        # Query all entities
        entities = self.graph.query(
            "SELECT id, entity_type FROM nodes WHERE type = 'Entity'"
        )

        for entity in entities:
            stats["total_entities"] += 1
            entity_type = entity.get("entity_type", "UNKNOWN")
            if entity_type in stats:
                stats[entity_type] += 1

        return stats

    def get_top_entities(self, limit: int = 20) -> List[Dict]:
        """
        Get top entities by prominence and mention count.

        Args:
            limit: Number of entities to return

        Returns:
            List of entity dictionaries sorted by prominence
        """
        entities = self.graph.query(
            """
            SELECT id, name, entity_type, canonical_name, mention_count, prominence
            FROM nodes
            WHERE type = 'Entity'
            ORDER BY prominence DESC, mention_count DESC
            LIMIT ?
            """,
            (limit,)
        )

        return entities
