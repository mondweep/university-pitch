"""
Entity Graph Builder
Creates Entity nodes and MENTIONS relationships in the knowledge graph.
"""

import logging
import uuid
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from ..graph.mgraph_compat import MGraph
from .entity_models import Entity, EntityMention, EntityType

logger = logging.getLogger(__name__)


class EntityGraphBuilder:
    """Build entity nodes and relationships in graph."""

    def __init__(self, graph: MGraph):
        """
        Initialize entity graph builder.

        Args:
            graph: MGraph instance
        """
        self.graph = graph
        self.entity_id_map: Dict[str, str] = {}  # normalized_name -> node_id

        logger.info("Initialized EntityGraphBuilder")

    def create_entity_node(self, entity: Entity) -> str:
        """
        Create or get existing Entity node in graph.

        Args:
            entity: Entity to create

        Returns:
            Entity node ID
        """
        # Check if entity already exists
        if entity.normalized_name in self.entity_id_map:
            existing_id = self.entity_id_map[entity.normalized_name]
            logger.debug(f"Entity already exists: {entity.name} -> {existing_id}")
            return existing_id

        # Create new entity node
        node_id = entity.id or str(uuid.uuid4())

        properties = {
            "name": entity.name,
            "type": entity.type.value,
            "normalized_name": entity.normalized_name,
            "confidence": entity.confidence,
            "aliases": entity.aliases,
            "prominence": entity.prominence,
            "mention_count": len(entity.source_ids)
        }

        # Add metadata
        if entity.metadata:
            properties["metadata"] = entity.metadata

        self.graph.add_node(
            node_id=node_id,
            node_type="Entity",
            properties=properties
        )

        # Cache the ID
        self.entity_id_map[entity.normalized_name] = node_id
        entity.id = node_id

        logger.debug(f"Created Entity node: {entity.name} ({entity.type.value}) -> {node_id}")

        return node_id

    def create_mentions_edge(
        self,
        source_id: str,
        entity_id: str,
        context: str = "",
        position: int = 0,
        confidence: float = 1.0
    ) -> None:
        """
        Create MENTIONS relationship from Page/Section to Entity.

        Args:
            source_id: Source node ID (Page or Section)
            entity_id: Entity node ID
            context: Surrounding text context
            position: Position in source text
            confidence: Confidence score
        """
        properties = {
            "context": context[:200],  # Limit context length
            "position": position,
            "confidence": confidence
        }

        self.graph.add_edge(
            from_id=source_id,
            to_id=entity_id,
            edge_type="MENTIONS",
            properties=properties
        )

        logger.debug(f"Created MENTIONS edge: {source_id} -> {entity_id}")

    def build_entities_from_list(
        self,
        entities: List[Entity],
        source_id: str,
        source_type: str = "Page"
    ) -> List[str]:
        """
        Build entity nodes and mentions edges for a list of entities.

        Args:
            entities: List of entities to build
            source_id: Source node ID
            source_type: Source node type (Page or Section)

        Returns:
            List of created entity node IDs
        """
        entity_ids = []

        for idx, entity in enumerate(entities):
            # Create entity node
            entity_id = self.create_entity_node(entity)
            entity_ids.append(entity_id)

            # Create mentions edge
            self.create_mentions_edge(
                source_id=source_id,
                entity_id=entity_id,
                context=entity.context,
                position=idx,
                confidence=entity.confidence
            )

        logger.info(
            f"Built {len(entity_ids)} entities for {source_type} {source_id}"
        )

        return entity_ids

    def calculate_prominence(self, entity_id: str) -> float:
        """
        Calculate entity prominence score.

        Prominence is based on:
        - Number of mentions (frequency)
        - Number of unique pages mentioning entity
        - Average confidence of mentions

        Args:
            entity_id: Entity node ID

        Returns:
            Prominence score (0-1)
        """
        # Get all MENTIONS edges pointing to this entity
        mentions = self.graph.get_edges_by_type("MENTIONS", to_id=entity_id)

        if not mentions:
            return 0.0

        # Count unique sources (pages)
        unique_sources = set()
        total_confidence = 0.0

        for mention in mentions:
            source_id = mention.get("from_id")
            confidence = mention.get("properties", {}).get("confidence", 1.0)

            if source_id:
                unique_sources.add(source_id)
                total_confidence += confidence

        # Calculate components
        frequency_score = min(len(mentions) / 50.0, 1.0)  # Normalize to max 50 mentions
        diversity_score = min(len(unique_sources) / 20.0, 1.0)  # Normalize to max 20 sources
        confidence_score = total_confidence / len(mentions)

        # Weighted average
        prominence = (
            0.4 * frequency_score +
            0.4 * diversity_score +
            0.2 * confidence_score
        )

        logger.debug(
            f"Prominence for {entity_id}: {prominence:.3f} "
            f"(mentions={len(mentions)}, sources={len(unique_sources)})"
        )

        return prominence

    def update_entity_prominence(self, entity_id: str) -> None:
        """
        Update prominence score for an entity.

        Args:
            entity_id: Entity node ID
        """
        prominence = self.calculate_prominence(entity_id)

        # Update entity node properties
        self.graph.update_node(
            node_id=entity_id,
            properties={"prominence": prominence}
        )

        logger.debug(f"Updated prominence for {entity_id}: {prominence:.3f}")

    def calculate_all_prominences(self) -> None:
        """Calculate and update prominence for all entities."""
        entity_nodes = self.graph.get_nodes_by_type("Entity")

        logger.info(f"Calculating prominence for {len(entity_nodes)} entities")

        for node in entity_nodes:
            entity_id = node.get("id")
            if entity_id:
                self.update_entity_prominence(entity_id)

        logger.info("Prominence calculation complete")

    def get_entity_statistics(self) -> Dict:
        """
        Get statistics about entities in the graph.

        Returns:
            Statistics dictionary
        """
        entity_nodes = self.graph.get_nodes_by_type("Entity")
        mentions_edges = self.graph.get_edges_by_type("MENTIONS")

        # Count by type
        type_counts = defaultdict(int)
        for node in entity_nodes:
            entity_type = node.get("properties", {}).get("type", "UNKNOWN")
            type_counts[entity_type] += 1

        # Get top entities by prominence
        entities_with_prominence = [
            (
                node.get("properties", {}).get("name", "Unknown"),
                node.get("properties", {}).get("prominence", 0.0)
            )
            for node in entity_nodes
        ]
        entities_with_prominence.sort(key=lambda x: x[1], reverse=True)
        top_entities = entities_with_prominence[:20]

        # Count sources mentioning entities
        sources_with_entities = set()
        for edge in mentions_edges:
            source_id = edge.get("from_id")
            if source_id:
                sources_with_entities.add(source_id)

        stats = {
            "total_entities": len(entity_nodes),
            "total_mentions": len(mentions_edges),
            "entities_by_type": dict(type_counts),
            "sources_with_entities": len(sources_with_entities),
            "top_entities": top_entities,
            "avg_mentions_per_entity": (
                len(mentions_edges) / len(entity_nodes)
                if entity_nodes else 0.0
            )
        }

        logger.info(f"Entity statistics: {stats['total_entities']} entities, {stats['total_mentions']} mentions")

        return stats

    def get_entity_distribution(self) -> Dict[str, int]:
        """
        Get distribution of entities across pages.

        Returns:
            Dictionary mapping page_id to entity count
        """
        mentions_edges = self.graph.get_edges_by_type("MENTIONS")

        distribution = defaultdict(int)
        for edge in mentions_edges:
            source_id = edge.get("from_id")
            if source_id:
                distribution[source_id] += 1

        return dict(distribution)

    def export_entities(self, output_path: str) -> None:
        """
        Export entities to JSON file.

        Args:
            output_path: Output file path
        """
        import json

        entity_nodes = self.graph.get_nodes_by_type("Entity")

        entities_data = []
        for node in entity_nodes:
            entities_data.append({
                "id": node.get("id"),
                "properties": node.get("properties", {})
            })

        with open(output_path, 'w') as f:
            json.dump({
                "count": len(entities_data),
                "entities": entities_data
            }, f, indent=2)

        logger.info(f"Exported {len(entities_data)} entities to {output_path}")
