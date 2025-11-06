"""
Mentions Edge Builder

Creates MENTIONS edges from ContentItem nodes to Entity nodes,
representing where entities are mentioned in the content.
"""

import logging
from typing import List, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class MentionsBuilder:
    """
    Builds MENTIONS edges in knowledge graph.

    Creates edges from ContentItem -> Entity with mention metadata
    including context, prominence, and confidence.
    """

    def __init__(self, graph, entity_node_builder):
        """
        Initialize mentions builder.

        Args:
            graph: MGraph instance to add edges to
            entity_node_builder: EntityNodeBuilder for ID mapping
        """
        self.graph = graph
        self.entity_node_builder = entity_node_builder
        self.mention_stats = defaultdict(int)

    def add_mentions(self, mentions: List[Dict]) -> Dict[str, int]:
        """
        Add MENTIONS edges to graph.

        Args:
            mentions: List of mention dictionaries from NER extraction

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_mentions": len(mentions),
            "edges_created": 0,
            "errors": 0,
            "by_prominence": defaultdict(int)
        }

        # Group mentions by content_id -> entity_id
        mention_groups = defaultdict(lambda: defaultdict(list))

        for mention in mentions:
            content_id = mention["content_id"]
            temp_entity_id = mention["entity_id"]

            # Get canonical entity ID
            canonical_entity_id = self.entity_node_builder.get_canonical_entity_id(temp_entity_id)

            # Group mentions
            mention_groups[content_id][canonical_entity_id].append(mention)

        # Create edges (one edge per content-entity pair, aggregated)
        for content_id, entities in mention_groups.items():
            for entity_id, entity_mentions in entities.items():
                try:
                    edge_data = self._aggregate_mentions(entity_mentions)

                    self.graph.add_edge(
                        from_node_id=content_id,
                        to_node_id=entity_id,
                        edge_type="MENTIONS",
                        data=edge_data
                    )

                    stats["edges_created"] += 1
                    stats["by_prominence"][edge_data["prominence"]] += 1

                except Exception as e:
                    logger.error(f"Error adding MENTIONS edge {content_id} -> {entity_id}: {e}")
                    stats["errors"] += 1

        logger.info(f"✅ Created {stats['edges_created']} MENTIONS edges from {stats['total_mentions']} mentions")

        return stats

    def _aggregate_mentions(self, mentions: List[Dict]) -> Dict:
        """
        Aggregate multiple mentions into single edge data.

        Args:
            mentions: List of mentions for same content-entity pair

        Returns:
            Aggregated edge data
        """
        # Count mentions
        mention_count = len(mentions)

        # Get first mention context
        first_mention = min(mentions, key=lambda m: m["position"])
        context = first_mention["context"]

        # Calculate average prominence
        prominence_scores = {
            "high": 1.0,
            "medium": 0.6,
            "low": 0.3
        }
        avg_prominence_score = sum(
            prominence_scores.get(m["prominence"], 0.6) for m in mentions
        ) / mention_count

        # Map back to prominence level
        if avg_prominence_score >= 0.7:
            prominence = "high"
        elif avg_prominence_score >= 0.4:
            prominence = "medium"
        else:
            prominence = "low"

        # Get max confidence
        max_confidence = max(m["confidence"] for m in mentions)

        # Get all entity texts (variations)
        entity_texts = list(set(m["entity_text"] for m in mentions))

        return {
            "mention_count": mention_count,
            "context": context[:200],  # Limit context length
            "prominence": prominence,
            "confidence": round(max_confidence, 3),
            "entity_texts": entity_texts,
            "positions": [m["position"] for m in mentions],
            "extracted_by": mentions[0]["extracted_by"]
        }

    def get_mention_stats(self) -> Dict:
        """
        Get mention statistics.

        Returns:
            Dictionary with mention statistics
        """
        return dict(self.mention_stats)

    def validate_mentions(self) -> Dict[str, any]:
        """
        Validate MENTIONS edges in graph.

        Returns:
            Validation report
        """
        report = {
            "valid": True,
            "total_mentions_edges": 0,
            "errors": [],
            "warnings": []
        }

        # Get all MENTIONS edges
        mentions_edges = list(self.graph.get_edges(edge_type="MENTIONS"))
        report["total_mentions_edges"] = len(mentions_edges)

        for edge in mentions_edges:
            # Check source (ContentItem) exists
            source_node = self.graph.get_node(edge.from_node)
            if not source_node:
                report["errors"].append(f"Source ContentItem not found: {edge.from_node}")
                report["valid"] = False
            elif source_node.node_type != "ContentItem":
                report["warnings"].append(
                    f"MENTIONS source is not ContentItem: {edge.from_node} ({source_node.node_type})"
                )

            # Check target (Entity) exists
            target_node = self.graph.get_node(edge.to_node)
            if not target_node:
                report["errors"].append(f"Target Entity not found: {edge.to_node}")
                report["valid"] = False
            elif target_node.node_type != "Entity":
                report["warnings"].append(
                    f"MENTIONS target is not Entity: {edge.to_node} ({target_node.node_type})"
                )

            # Check edge data
            if not edge.data.get("mention_count"):
                report["warnings"].append(f"MENTIONS edge missing mention_count: {edge.from_node} -> {edge.to_node}")

            if not edge.data.get("context"):
                report["warnings"].append(f"MENTIONS edge missing context: {edge.from_node} -> {edge.to_node}")

        return report
