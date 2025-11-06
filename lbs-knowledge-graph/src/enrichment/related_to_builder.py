"""
RELATED_TO Relationship Builder
Creates RELATED_TO edges between similar content in the knowledge graph.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from ..graph.mgraph_compat import MGraph

logger = logging.getLogger(__name__)


@dataclass
class RelatedToEdge:
    """RELATED_TO relationship data."""
    source_id: str
    target_id: str
    similarity: float
    similarity_type: str  # 'embedding', 'topic', 'entity', 'multi'
    metadata: Dict
    created_at: str


class RelatedToBuilder:
    """Build RELATED_TO relationships in knowledge graph."""

    def __init__(self, graph: MGraph):
        """
        Initialize builder with graph.

        Args:
            graph: MGraph instance
        """
        self.graph = graph
        logger.info("Initialized RelatedToBuilder")

    def create_related_to_edge(
        self,
        source_id: str,
        target_id: str,
        similarity: float,
        similarity_type: str,
        metadata: Optional[Dict] = None,
        bidirectional: bool = True
    ) -> bool:
        """
        Create RELATED_TO edge between two content items.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            similarity: Similarity score (0-1)
            similarity_type: Type of similarity calculation
            metadata: Additional metadata
            bidirectional: Create edge in both directions

        Returns:
            True if successful
        """
        if source_id == target_id:
            logger.warning("Cannot create self-referential RELATED_TO edge")
            return False

        # Validate nodes exist
        source_node = self.graph.get_node(source_id)
        target_node = self.graph.get_node(target_id)

        if not source_node:
            logger.error(f"Source node not found: {source_id}")
            return False

        if not target_node:
            logger.error(f"Target node not found: {target_id}")
            return False

        # Prepare edge data
        edge_data = {
            'similarity': similarity,
            'similarity_type': similarity_type,
            'created_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }

        try:
            # Create forward edge
            self.graph.add_edge(
                source_id,
                target_id,
                'RELATED_TO',
                **edge_data
            )

            logger.debug(
                f"Created RELATED_TO: {source_id} -> {target_id} "
                f"(similarity={similarity:.3f}, type={similarity_type})"
            )

            # Create reverse edge if bidirectional
            if bidirectional:
                self.graph.add_edge(
                    target_id,
                    source_id,
                    'RELATED_TO',
                    **edge_data
                )

                logger.debug(
                    f"Created RELATED_TO: {target_id} -> {source_id} "
                    f"(similarity={similarity:.3f}, type={similarity_type})"
                )

            return True

        except Exception as e:
            logger.error(f"Error creating RELATED_TO edge: {e}")
            return False

    def create_batch_edges(
        self,
        edges: List[RelatedToEdge],
        bidirectional: bool = True
    ) -> int:
        """
        Create multiple RELATED_TO edges in batch.

        Args:
            edges: List of edge data
            bidirectional: Create edges in both directions

        Returns:
            Number of successfully created edges
        """
        success_count = 0

        for edge in edges:
            success = self.create_related_to_edge(
                edge.source_id,
                edge.target_id,
                edge.similarity,
                edge.similarity_type,
                edge.metadata,
                bidirectional=bidirectional
            )

            if success:
                success_count += 1

        logger.info(
            f"Created {success_count}/{len(edges)} RELATED_TO edges "
            f"({'bidirectional' if bidirectional else 'unidirectional'})"
        )

        return success_count

    def build_related_graph(
        self,
        similarities: List[Dict],
        bidirectional: bool = True,
        min_similarity: float = 0.7
    ) -> MGraph:
        """
        Build complete related content graph from similarity results.

        Args:
            similarities: List of similarity results
            bidirectional: Create edges in both directions
            min_similarity: Minimum similarity threshold

        Returns:
            Updated graph with RELATED_TO edges
        """
        logger.info(
            f"Building related content graph from {len(similarities)} similarities"
        )

        # Filter by threshold
        filtered = [
            s for s in similarities
            if s.get('similarity', 0) >= min_similarity
        ]

        logger.info(
            f"Filtered to {len(filtered)} similarities above threshold {min_similarity}"
        )

        # Convert to RelatedToEdge objects
        edges = []
        for sim in filtered:
            edge = RelatedToEdge(
                source_id=sim['source_id'],
                target_id=sim['target_id'],
                similarity=sim['similarity'],
                similarity_type=sim.get('similarity_type', 'embedding'),
                metadata=sim.get('metadata', {}),
                created_at=datetime.utcnow().isoformat()
            )
            edges.append(edge)

        # Create edges
        created = self.create_batch_edges(edges, bidirectional=bidirectional)

        logger.info(f"Successfully created {created} RELATED_TO edges")

        return self.graph

    def get_related_content(
        self,
        content_id: str,
        min_similarity: float = 0.7,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Get related content for a given content item.

        Args:
            content_id: Content node ID
            min_similarity: Minimum similarity threshold
            max_results: Maximum number of results

        Returns:
            List of related content with similarity scores
        """
        # Get all RELATED_TO edges from this node
        edges = self.graph.get_edges(content_id, edge_type='RELATED_TO')

        # Extract related content
        related = []
        for edge in edges:
            if edge.get('similarity', 0) >= min_similarity:
                related.append({
                    'content_id': edge['target'],
                    'similarity': edge['similarity'],
                    'similarity_type': edge.get('similarity_type', 'unknown'),
                    'metadata': edge.get('metadata', {})
                })

        # Sort by similarity descending
        related.sort(key=lambda x: x['similarity'], reverse=True)

        # Limit results
        return related[:max_results]

    def get_related_stats(self) -> Dict:
        """
        Get statistics about RELATED_TO relationships.

        Returns:
            Dictionary with statistics
        """
        # Count all RELATED_TO edges
        all_edges = []
        for node_id in self.graph.get_all_nodes():
            edges = self.graph.get_edges(node_id, edge_type='RELATED_TO')
            all_edges.extend(edges)

        if not all_edges:
            return {
                'total_edges': 0,
                'average_similarity': 0.0,
                'min_similarity': 0.0,
                'max_similarity': 0.0,
                'by_type': {}
            }

        # Calculate statistics
        similarities = [e.get('similarity', 0) for e in all_edges]
        types = {}

        for edge in all_edges:
            sim_type = edge.get('similarity_type', 'unknown')
            types[sim_type] = types.get(sim_type, 0) + 1

        stats = {
            'total_edges': len(all_edges),
            'average_similarity': sum(similarities) / len(similarities),
            'min_similarity': min(similarities),
            'max_similarity': max(similarities),
            'by_type': types
        }

        logger.info(f"Related content stats: {stats}")

        return stats

    def remove_low_similarity_edges(
        self,
        min_similarity: float = 0.7
    ) -> int:
        """
        Remove RELATED_TO edges below similarity threshold.

        Args:
            min_similarity: Minimum similarity to keep

        Returns:
            Number of removed edges
        """
        removed = 0

        for node_id in self.graph.get_all_nodes():
            edges = self.graph.get_edges(node_id, edge_type='RELATED_TO')

            for edge in edges:
                if edge.get('similarity', 0) < min_similarity:
                    try:
                        self.graph.remove_edge(
                            edge['source'],
                            edge['target'],
                            'RELATED_TO'
                        )
                        removed += 1
                    except Exception as e:
                        logger.error(f"Error removing edge: {e}")

        logger.info(
            f"Removed {removed} RELATED_TO edges below threshold {min_similarity}"
        )

        return removed

    def export_edges(self, output_path: str) -> None:
        """
        Export RELATED_TO edges to JSON file.

        Args:
            output_path: Output file path
        """
        import json
        from pathlib import Path

        edges = []

        for node_id in self.graph.get_all_nodes():
            node_edges = self.graph.get_edges(node_id, edge_type='RELATED_TO')

            for edge in node_edges:
                edges.append({
                    'source_id': edge['source'],
                    'target_id': edge['target'],
                    'similarity': edge.get('similarity', 0),
                    'similarity_type': edge.get('similarity_type', 'unknown'),
                    'metadata': edge.get('metadata', {}),
                    'created_at': edge.get('created_at', '')
                })

        # Write to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump({
                'edge_count': len(edges),
                'edges': edges
            }, f, indent=2)

        logger.info(f"Exported {len(edges)} RELATED_TO edges to {output_path}")
