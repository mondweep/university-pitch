"""
Entity Node Builder

Creates Entity nodes in the knowledge graph from NER extraction results.
Handles entity deduplication, merging, and canonical name resolution.
"""

import logging
from typing import List, Dict, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class EntityNodeBuilder:
    """
    Builds Entity nodes in knowledge graph with deduplication.

    Features:
    - Entity deduplication by canonical name
    - Alias aggregation
    - Mention count aggregation
    - Prominence score calculation
    """

    def __init__(self, graph):
        """
        Initialize entity node builder.

        Args:
            graph: MGraph instance to add nodes to
        """
        self.graph = graph
        self.entity_map: Dict[str, Dict] = {}  # canonical_name -> entity data
        self.entity_id_map: Dict[str, str] = {}  # temp_id -> canonical_entity_id

    def add_entities(self, entities: List[Dict]) -> Dict[str, int]:
        """
        Add entities to graph with deduplication.

        Args:
            entities: List of entity dictionaries from NER extraction

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_extracted": len(entities),
            "unique_entities": 0,
            "merged_entities": 0,
            "by_type": defaultdict(int)
        }

        for entity in entities:
            entity_type = entity["entity_type"]
            canonical_name = entity["canonical_name"]
            temp_id = entity["id"]

            # Create canonical entity ID
            canonical_id = self._create_entity_id(canonical_name, entity_type)

            # Map temp ID to canonical ID
            self.entity_id_map[temp_id] = canonical_id

            # Check if entity already exists
            if canonical_id in self.entity_map:
                # Merge with existing entity
                self._merge_entity(canonical_id, entity)
                stats["merged_entities"] += 1
            else:
                # Create new entity
                self.entity_map[canonical_id] = {
                    "id": canonical_id,
                    "name": canonical_name,
                    "entity_type": entity_type,
                    "aliases": set([entity["name"]]),
                    "mention_count": entity["mention_count"],
                    "prominence": entity["prominence"],
                    "confidence": entity["confidence"],
                    "metadata": entity.get("metadata", {}),
                    "first_mentioned": entity.get("first_mentioned")
                }
                stats["unique_entities"] += 1
                stats["by_type"][entity_type] += 1

        # Add all entities to graph
        for entity_id, entity_data in self.entity_map.items():
            self._add_entity_node(entity_id, entity_data)

        logger.info(f"✅ Added {stats['unique_entities']} unique entities ({stats['merged_entities']} merged)")

        return stats

    def _create_entity_id(self, canonical_name: str, entity_type: str) -> str:
        """
        Create stable entity ID from canonical name and type.

        Args:
            canonical_name: Normalized entity name
            entity_type: Entity type (PERSON, ORGANIZATION, etc.)

        Returns:
            Entity ID string
        """
        # Create ID: entity-{type}-{normalized-name}
        normalized = canonical_name.lower().replace(" ", "-").replace(".", "")
        return f"entity-{entity_type.lower()}-{normalized}"

    def _merge_entity(self, entity_id: str, new_entity: Dict):
        """
        Merge new entity data with existing entity.

        Args:
            entity_id: Canonical entity ID
            new_entity: New entity data to merge
        """
        existing = self.entity_map[entity_id]

        # Add new alias
        existing["aliases"].add(new_entity["name"])

        # Update mention count
        existing["mention_count"] += new_entity["mention_count"]

        # Update prominence (take max)
        existing["prominence"] = max(existing["prominence"], new_entity["prominence"])

        # Update confidence (take max)
        existing["confidence"] = max(existing["confidence"], new_entity["confidence"])

        # Merge metadata
        for key, value in new_entity.get("metadata", {}).items():
            if key not in existing["metadata"]:
                existing["metadata"][key] = value

    def _add_entity_node(self, entity_id: str, entity_data: Dict):
        """
        Add entity node to graph.

        Args:
            entity_id: Entity ID
            entity_data: Entity properties
        """
        # Convert aliases set to list
        node_data = {
            "id": entity_id,
            "name": entity_data["name"],
            "entity_type": entity_data["entity_type"],
            "aliases": list(entity_data["aliases"]),
            "mention_count": entity_data["mention_count"],
            "prominence": round(entity_data["prominence"], 3),
            "confidence": round(entity_data["confidence"], 3),
            "metadata": entity_data["metadata"],
            "first_mentioned": entity_data.get("first_mentioned")
        }

        try:
            self.graph.add_node(
                node_type="Entity",
                node_id=entity_id,
                data=node_data
            )
        except Exception as e:
            logger.error(f"Error adding entity node {entity_id}: {e}")

    def get_canonical_entity_id(self, temp_id: str) -> str:
        """
        Get canonical entity ID for a temporary extraction ID.

        Args:
            temp_id: Temporary entity ID from extraction

        Returns:
            Canonical entity ID in graph
        """
        return self.entity_id_map.get(temp_id, temp_id)

    def get_entity_stats(self) -> Dict:
        """
        Get entity statistics.

        Returns:
            Dictionary with entity counts by type
        """
        stats = {
            "total_entities": len(self.entity_map),
            "by_type": defaultdict(int),
            "top_entities": []
        }

        # Count by type
        for entity_data in self.entity_map.values():
            stats["by_type"][entity_data["entity_type"]] += 1

        # Get top 10 entities by mention count
        sorted_entities = sorted(
            self.entity_map.values(),
            key=lambda x: x["mention_count"],
            reverse=True
        )[:10]

        stats["top_entities"] = [
            {
                "name": e["name"],
                "type": e["entity_type"],
                "mentions": e["mention_count"],
                "prominence": round(e["prominence"], 2)
            }
            for e in sorted_entities
        ]

        return stats
