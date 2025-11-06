"""
Topic Hierarchy Builder for Knowledge Graph

Creates SUBTOPIC_OF and RELATED_TOPIC relationships and calculates
topic centrality scores.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass

from ..graph.mgraph_compat import MGraph, MNode

logger = logging.getLogger(__name__)


@dataclass
class TopicRelationship:
    """Topic relationship metadata"""
    source_id: str
    target_id: str
    relationship_type: str  # SUBTOPIC_OF, RELATED_TOPIC
    strength: float  # Relationship strength (0-1)


class TopicHierarchyBuilder:
    """
    Build topic hierarchy in knowledge graph.

    Creates SUBTOPIC_OF relationships (parent-child) and RELATED_TOPIC
    relationships (siblings/related topics).
    """

    def __init__(
        self,
        graph: MGraph,
        similarity_threshold: float = 0.7,
        related_threshold: float = 0.6
    ):
        """
        Initialize hierarchy builder.

        Args:
            graph: Knowledge graph instance
            similarity_threshold: Threshold for SUBTOPIC_OF relationships
            related_threshold: Threshold for RELATED_TOPIC relationships
        """
        self.graph = graph
        self.similarity_threshold = similarity_threshold
        self.related_threshold = related_threshold

        logger.info("Initialized TopicHierarchyBuilder")

    def create_subtopic_edge(
        self,
        child_id: str,
        parent_id: str,
        similarity: float = None
    ) -> None:
        """
        Create SUBTOPIC_OF relationship between topics.

        Args:
            child_id: Child topic ID
            parent_id: Parent topic ID
            similarity: Semantic similarity score (optional)
        """
        # Verify both nodes exist
        child_node = self.graph.get_node(child_id)
        parent_node = self.graph.get_node(parent_id)

        if not child_node:
            logger.warning(f"Child topic not found: {child_id}")
            return

        if not parent_node:
            logger.warning(f"Parent topic not found: {parent_id}")
            return

        # Create edge data
        edge_data = {}
        if similarity is not None:
            edge_data['similarity'] = float(similarity)

        # Add edge to graph
        self.graph.add_edge(
            from_node_id=child_id,
            to_node_id=parent_id,
            edge_type='SUBTOPIC_OF',
            data=edge_data
        )

        logger.debug(
            f"Created SUBTOPIC_OF: '{child_node.data.get('name')}' -> "
            f"'{parent_node.data.get('name')}' (sim={similarity:.3f if similarity else 'N/A'})"
        )

    def create_related_topic_edge(
        self,
        topic1_id: str,
        topic2_id: str,
        similarity: float
    ) -> None:
        """
        Create RELATED_TOPIC relationship between topics.

        Args:
            topic1_id: First topic ID
            topic2_id: Second topic ID
            similarity: Semantic similarity score
        """
        # Verify both nodes exist
        topic1 = self.graph.get_node(topic1_id)
        topic2 = self.graph.get_node(topic2_id)

        if not topic1 or not topic2:
            logger.warning(f"Topic not found: {topic1_id} or {topic2_id}")
            return

        # Create bidirectional edges
        edge_data = {'similarity': float(similarity)}

        self.graph.add_edge(
            from_node_id=topic1_id,
            to_node_id=topic2_id,
            edge_type='RELATED_TOPIC',
            data=edge_data
        )

        self.graph.add_edge(
            from_node_id=topic2_id,
            to_node_id=topic1_id,
            edge_type='RELATED_TOPIC',
            data=edge_data
        )

        logger.debug(
            f"Created RELATED_TOPIC: '{topic1.data.get('name')}' <-> "
            f"'{topic2.data.get('name')}' (sim={similarity:.3f})"
        )

    def build_hierarchy_from_clusters(
        self,
        hierarchy_map: Dict[str, List[str]],
        topic_similarities: Dict[Tuple[str, str], float]
    ) -> int:
        """
        Build hierarchy in graph from clustering results.

        Args:
            hierarchy_map: Dict mapping parent IDs to child ID lists
            topic_similarities: Dict mapping (topic1_id, topic2_id) to similarity

        Returns:
            Number of SUBTOPIC_OF edges created
        """
        edge_count = 0

        for parent_id, child_ids in hierarchy_map.items():
            for child_id in child_ids:
                # Get similarity if available
                similarity = topic_similarities.get((child_id, parent_id))
                if similarity is None:
                    similarity = topic_similarities.get((parent_id, child_id))

                # Create SUBTOPIC_OF edge
                self.create_subtopic_edge(child_id, parent_id, similarity)
                edge_count += 1

        logger.info(f"Created {edge_count} SUBTOPIC_OF relationships")

        return edge_count

    def build_related_topics(
        self,
        topic_ids: List[str],
        topic_similarities: Dict[Tuple[str, str], float]
    ) -> int:
        """
        Build RELATED_TOPIC relationships for sibling/related topics.

        Args:
            topic_ids: List of all topic IDs
            topic_similarities: Dict mapping (topic1_id, topic2_id) to similarity

        Returns:
            Number of RELATED_TOPIC edges created
        """
        edge_count = 0
        processed_pairs = set()

        for i, topic1_id in enumerate(topic_ids):
            for topic2_id in topic_ids[i+1:]:
                # Skip if already processed
                pair = tuple(sorted([topic1_id, topic2_id]))
                if pair in processed_pairs:
                    continue

                # Get similarity
                similarity = topic_similarities.get((topic1_id, topic2_id))
                if similarity is None:
                    similarity = topic_similarities.get((topic2_id, topic1_id))

                if similarity is None:
                    continue

                # Create edge if similarity exceeds threshold
                if similarity >= self.related_threshold:
                    self.create_related_topic_edge(topic1_id, topic2_id, similarity)
                    edge_count += 1
                    processed_pairs.add(pair)

        logger.info(f"Created {edge_count} RELATED_TOPIC relationships")

        return edge_count

    def calculate_centrality(self, topic_id: str) -> float:
        """
        Calculate topic centrality score.

        Centrality measures topic importance based on:
        1. Number of outgoing HAS_TOPIC edges (pages containing topic)
        2. Number of incoming SUBTOPIC_OF edges (subtopics)
        3. Number of RELATED_TOPIC edges (related topics)

        Args:
            topic_id: Topic node ID

        Returns:
            Centrality score (0-1)
        """
        # Get all edges involving this topic
        outgoing_has_topic = len(self.graph.get_edges(to_node_id=topic_id, edge_type='HAS_TOPIC'))
        incoming_subtopic = len(self.graph.get_edges(to_node_id=topic_id, edge_type='SUBTOPIC_OF'))
        related_topics = len(self.graph.get_edges(from_node_id=topic_id, edge_type='RELATED_TOPIC'))

        # Weighted centrality score
        # HAS_TOPIC = 0.5 (most important - frequency in pages)
        # SUBTOPIC_OF = 0.3 (importance as parent topic)
        # RELATED_TOPIC = 0.2 (connectivity to other topics)

        max_has_topic = 10  # Normalize to 10+ pages
        max_subtopics = 5   # Normalize to 5+ subtopics
        max_related = 10    # Normalize to 10+ related topics

        has_topic_score = min(outgoing_has_topic / max_has_topic, 1.0)
        subtopic_score = min(incoming_subtopic / max_subtopics, 1.0)
        related_score = min(related_topics / max_related, 1.0)

        centrality = (
            0.5 * has_topic_score +
            0.3 * subtopic_score +
            0.2 * related_score
        )

        logger.debug(
            f"Centrality for {topic_id}: {centrality:.3f} "
            f"(pages={outgoing_has_topic}, subtopics={incoming_subtopic}, "
            f"related={related_topics})"
        )

        return centrality

    def calculate_all_centralities(self) -> Dict[str, float]:
        """
        Calculate centrality scores for all topics in graph.

        Returns:
            Dictionary mapping topic IDs to centrality scores
        """
        centralities = {}

        # Get all Topic nodes
        topic_nodes = self.graph.query(node_type='Topic')

        for topic in topic_nodes:
            centrality = self.calculate_centrality(topic.id)
            centralities[topic.id] = centrality

            # Update node with centrality score
            topic_data = dict(topic.data)
            topic_data['centrality'] = centrality

            # Re-add node with updated data
            self.graph.add_node(
                node_type='Topic',
                node_id=topic.id,
                data=topic_data
            )

        logger.info(
            f"Calculated centrality for {len(centralities)} topics, "
            f"avg={np.mean(list(centralities.values())):.3f}"
        )

        return centralities

    def get_hierarchy_statistics(self) -> Dict:
        """
        Get statistics about topic hierarchy.

        Returns:
            Dictionary with hierarchy statistics
        """
        # Count nodes and edges
        topic_nodes = self.graph.query(node_type='Topic')
        num_topics = len(topic_nodes)

        # Count hierarchy edges
        subtopic_edges = 0
        related_edges = 0
        root_topics = set()
        child_topics = set()

        for topic in topic_nodes:
            # Count SUBTOPIC_OF edges (as parent)
            children = self.graph.get_edges(to_node_id=topic.id, edge_type='SUBTOPIC_OF')
            if children:
                root_topics.add(topic.id)

            # Count SUBTOPIC_OF edges (as child)
            parents = self.graph.get_edges(from_node_id=topic.id, edge_type='SUBTOPIC_OF')
            if parents:
                child_topics.add(topic.id)
                subtopic_edges += len(parents)

            # Count RELATED_TOPIC edges
            related = self.graph.get_edges(from_node_id=topic.id, edge_type='RELATED_TOPIC')
            related_edges += len(related)

        # Related edges are bidirectional, so divide by 2
        related_edges = related_edges // 2

        stats = {
            'total_topics': num_topics,
            'root_topics': len(root_topics),
            'child_topics': len(child_topics),
            'orphan_topics': num_topics - len(root_topics) - len(child_topics),
            'subtopic_edges': subtopic_edges,
            'related_topic_edges': related_edges,
            'hierarchy_depth': self._calculate_max_depth(),
        }

        logger.info(f"Hierarchy statistics: {stats}")

        return stats

    def _calculate_max_depth(self) -> int:
        """
        Calculate maximum hierarchy depth.

        Returns:
            Maximum depth of topic hierarchy
        """
        topic_nodes = self.graph.query(node_type='Topic')
        max_depth = 0

        for topic in topic_nodes:
            depth = self._get_topic_depth(topic.id)
            max_depth = max(max_depth, depth)

        return max_depth

    def _get_topic_depth(self, topic_id: str, visited: Set[str] = None) -> int:
        """
        Get depth of topic in hierarchy (recursive).

        Args:
            topic_id: Topic node ID
            visited: Set of visited nodes (for cycle detection)

        Returns:
            Depth of topic (0 = root, 1+ = child level)
        """
        if visited is None:
            visited = set()

        if topic_id in visited:
            return 0  # Cycle detected

        visited.add(topic_id)

        # Get parent topics
        parent_edges = self.graph.get_edges(from_node_id=topic_id, edge_type='SUBTOPIC_OF')

        if not parent_edges:
            return 0  # Root topic

        # Get max depth of parents + 1
        max_parent_depth = 0
        for edge in parent_edges:
            parent_depth = self._get_topic_depth(edge.to_node, visited.copy())
            max_parent_depth = max(max_parent_depth, parent_depth)

        return max_parent_depth + 1

    def get_topic_path(self, topic_id: str) -> List[str]:
        """
        Get path from topic to root.

        Args:
            topic_id: Topic node ID

        Returns:
            List of topic IDs from leaf to root
        """
        path = [topic_id]
        visited = set([topic_id])

        current_id = topic_id
        while True:
            # Get parent
            parent_edges = self.graph.get_edges(from_node_id=current_id, edge_type='SUBTOPIC_OF')

            if not parent_edges:
                break  # Reached root

            # Use first parent
            parent_id = parent_edges[0].to_node

            if parent_id in visited:
                logger.warning(f"Cycle detected in topic hierarchy: {parent_id}")
                break

            path.append(parent_id)
            visited.add(parent_id)
            current_id = parent_id

        return path

    def export_hierarchy_mermaid(self, output_path: str) -> None:
        """
        Export topic hierarchy as Mermaid diagram.

        Args:
            output_path: Output file path for Mermaid diagram
        """
        from pathlib import Path

        topic_nodes = self.graph.query(node_type='Topic')

        with open(output_path, 'w') as f:
            f.write("# Topic Hierarchy\n\n")
            f.write("```mermaid\n")
            f.write("graph TD\n")

            # Write nodes
            for topic in topic_nodes:
                name = topic.data.get('name', topic.id)
                freq = topic.data.get('frequency', 0)
                centrality = topic.data.get('centrality', 0)

                label = f"{name}<br/>freq={freq}, cent={centrality:.2f}"
                f.write(f'    {topic.id}["{label}"]\n')

            # Write SUBTOPIC_OF edges
            f.write("\n    %% SUBTOPIC_OF relationships\n")
            for topic in topic_nodes:
                edges = self.graph.get_edges(from_node_id=topic.id, edge_type='SUBTOPIC_OF')
                for edge in edges:
                    similarity = edge.data.get('similarity', 0)
                    f.write(f'    {edge.from_node} -->|SUBTOPIC_OF<br/>{similarity:.2f}| {edge.to_node}\n')

            f.write("```\n")

        logger.info(f"Exported hierarchy diagram to {output_path}")
