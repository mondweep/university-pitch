"""
Topic Hierarchy Builder

Builds parent-child topic relationships based on cluster analysis
and semantic similarity. Creates CHILD_OF edges.
"""

import json
import logging
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TopicRelationship:
    """Represents a parent-child relationship between topics."""
    parent_id: str
    child_id: str
    confidence: float
    relationship_type: str  # 'cluster_based' or 'similarity_based'


class TopicHierarchyBuilder:
    """
    Build topic hierarchy by creating CHILD_OF edges.

    Strategies:
    1. Cluster-based: Cluster centroid as parent
    2. Similarity-based: High co-occurrence as parent
    3. Frequency-based: Common topics as parents

    Output:
    - CHILD_OF edges with confidence scores
    - 2-3 level hierarchy
    - Mermaid diagram visualization
    """

    def __init__(
        self,
        confidence_threshold: float = 0.6,
        max_depth: int = 3
    ):
        """
        Initialize hierarchy builder.

        Args:
            confidence_threshold: Minimum confidence for CHILD_OF edge
            max_depth: Maximum hierarchy depth
        """
        self.confidence_threshold = confidence_threshold
        self.max_depth = max_depth

        self.topics: Dict[str, Dict] = {}
        self.clusters: List[Dict] = []
        self.relationships: List[TopicRelationship] = []
        self.topic_depths: Dict[str, int] = {}

    def load_topics_and_clusters(
        self,
        graph: Dict,
        clusters: List[Dict]
    ) -> None:
        """
        Load topics and cluster information.

        Args:
            graph: Graph dict with nodes and edges
            clusters: List of cluster dicts from TopicClusterAnalyzer
        """
        logger.info("Loading topics and clusters for hierarchy building...")

        # Extract topics
        for node in graph['nodes']:
            if node.get('node_type') == 'Topic':
                topic_id = node['id']
                self.topics[topic_id] = node.get('data', {})

        self.clusters = clusters

        logger.info(f"Loaded {len(self.topics)} topics and {len(self.clusters)} clusters")

    def build_hierarchy(self) -> List[TopicRelationship]:
        """
        Build complete topic hierarchy.

        Steps:
        1. Create cluster-based parent-child relationships
        2. Add similarity-based relationships
        3. Ensure no cycles
        4. Calculate confidence scores
        5. Filter by threshold

        Returns:
            List of TopicRelationship objects
        """
        logger.info("Building topic hierarchy...")

        # Strategy 1: Cluster centroids as parents
        self._build_cluster_hierarchy()

        # Strategy 2: High-frequency topics as parents
        self._build_frequency_hierarchy()

        # Remove cycles and calculate depths
        self._remove_cycles()
        self._calculate_depths()

        # Filter by confidence
        self.relationships = [
            rel for rel in self.relationships
            if rel.confidence >= self.confidence_threshold
        ]

        logger.info(f"Built hierarchy with {len(self.relationships)} CHILD_OF edges")

        return self.relationships

    def _build_cluster_hierarchy(self) -> None:
        """Build hierarchy where cluster centroid is parent of cluster members."""
        logger.info("Building cluster-based hierarchy...")

        for cluster in self.clusters:
            centroid = cluster.get('centroid_topic')
            topics = cluster.get('topics', [])
            coherence = cluster.get('coherence_score', 0.5)

            if not centroid or len(topics) < 2:
                continue

            # Centroid is parent of all other topics in cluster
            for topic_id in topics:
                if topic_id != centroid:
                    # Confidence based on cluster coherence
                    confidence = 0.7 + (coherence * 0.3)  # 0.7-1.0 range

                    relationship = TopicRelationship(
                        parent_id=centroid,
                        child_id=topic_id,
                        confidence=confidence,
                        relationship_type='cluster_based'
                    )
                    self.relationships.append(relationship)

        logger.info(f"Created {len(self.relationships)} cluster-based relationships")

    def _build_frequency_hierarchy(self) -> None:
        """Build hierarchy based on topic frequency (common -> specific)."""
        logger.info("Building frequency-based hierarchy...")

        # Get topics sorted by frequency
        topic_freq = []
        for topic_id, topic_data in self.topics.items():
            freq = topic_data.get('frequency', 0)
            topic_freq.append((topic_id, freq))

        topic_freq.sort(key=lambda x: x[1], reverse=True)

        # Top 20% most frequent topics can be parents
        n_parents = max(1, len(topic_freq) // 5)
        parent_topics = {tid for tid, _ in topic_freq[:n_parents]}

        # Check if any child topics don't have cluster-based parents
        existing_children = {rel.child_id for rel in self.relationships}

        for topic_id, freq in topic_freq[n_parents:]:
            if topic_id in existing_children:
                continue  # Already has a parent

            # Find most similar parent from high-frequency topics
            best_parent = None
            best_similarity = 0

            for parent_id in parent_topics:
                if parent_id == topic_id:
                    continue

                # Simple similarity based on name overlap
                similarity = self._calculate_name_similarity(topic_id, parent_id)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_parent = parent_id

            if best_parent and best_similarity > 0.3:
                relationship = TopicRelationship(
                    parent_id=best_parent,
                    child_id=topic_id,
                    confidence=0.5 + (best_similarity * 0.3),
                    relationship_type='similarity_based'
                )
                self.relationships.append(relationship)

        logger.info(f"Total relationships: {len(self.relationships)}")

    def _calculate_name_similarity(self, topic1_id: str, topic2_id: str) -> float:
        """Calculate simple name-based similarity between topics."""
        name1 = self.topics.get(topic1_id, {}).get('name', '').lower()
        name2 = self.topics.get(topic2_id, {}).get('name', '').lower()

        if not name1 or not name2:
            return 0.0

        # Check for substring containment
        if name1 in name2 or name2 in name1:
            return 0.8

        # Check for word overlap
        words1 = set(name1.split())
        words2 = set(name2.split())

        if not words1 or not words2:
            return 0.0

        overlap = len(words1 & words2)
        union = len(words1 | words2)

        return overlap / union if union > 0 else 0.0

    def _remove_cycles(self) -> None:
        """Remove cycles from hierarchy graph."""
        logger.info("Checking for cycles...")

        # Build adjacency list
        children: Dict[str, List[str]] = defaultdict(list)
        for rel in self.relationships:
            children[rel.parent_id].append(rel.child_id)

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        cycles_found = []

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for child in children.get(node, []):
                if child not in visited:
                    dfs(child, path[:])
                elif child in rec_stack:
                    # Cycle detected
                    cycle_start = path.index(child)
                    cycle = path[cycle_start:] + [child]
                    cycles_found.append(cycle)

            rec_stack.remove(node)

        for topic_id in self.topics.keys():
            if topic_id not in visited:
                dfs(topic_id, [])

        if cycles_found:
            logger.warning(f"Found {len(cycles_found)} cycles, removing edges...")
            # Remove lowest confidence edges in cycles
            for cycle in cycles_found:
                min_conf = float('inf')
                min_edge = None

                for i in range(len(cycle) - 1):
                    parent, child = cycle[i], cycle[i+1]
                    for rel in self.relationships:
                        if rel.parent_id == parent and rel.child_id == child:
                            if rel.confidence < min_conf:
                                min_conf = rel.confidence
                                min_edge = rel

                if min_edge:
                    self.relationships.remove(min_edge)

        logger.info("Cycle removal complete")

    def _calculate_depths(self) -> None:
        """Calculate depth of each topic in hierarchy."""
        # Build adjacency lists
        children: Dict[str, List[str]] = defaultdict(list)
        parents: Dict[str, List[str]] = defaultdict(list)

        for rel in self.relationships:
            children[rel.parent_id].append(rel.child_id)
            parents[rel.child_id].append(rel.parent_id)

        # Find root topics (no parents)
        roots = [tid for tid in self.topics.keys() if tid not in parents]

        if not roots:
            # Use most frequent topic as root
            max_freq = -1
            root = None
            for tid, data in self.topics.items():
                freq = data.get('frequency', 0)
                if freq > max_freq:
                    max_freq = freq
                    root = tid
            if root:
                roots = [root]

        # BFS to calculate depths
        queue = [(root, 0) for root in roots]
        visited = set()

        while queue:
            topic_id, depth = queue.pop(0)

            if topic_id in visited:
                continue

            visited.add(topic_id)
            self.topic_depths[topic_id] = depth

            # Add children to queue
            for child in children.get(topic_id, []):
                if child not in visited and depth + 1 < self.max_depth:
                    queue.append((child, depth + 1))

    def export_hierarchy(self) -> Dict:
        """
        Export hierarchy for visualization.

        Returns:
            Dictionary with hierarchy structure and statistics
        """
        return {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'n_relationships': len(self.relationships),
                'n_topics': len(self.topics),
                'max_depth': max(self.topic_depths.values()) if self.topic_depths else 0
            },
            'relationships': [
                {
                    'parent_id': rel.parent_id,
                    'parent_name': self.topics.get(rel.parent_id, {}).get('name', 'Unknown'),
                    'child_id': rel.child_id,
                    'child_name': self.topics.get(rel.child_id, {}).get('name', 'Unknown'),
                    'confidence': float(rel.confidence),
                    'type': rel.relationship_type
                }
                for rel in self.relationships
            ],
            'depths': {
                topic_id: {
                    'depth': depth,
                    'name': self.topics.get(topic_id, {}).get('name', 'Unknown')
                }
                for topic_id, depth in self.topic_depths.items()
            },
            'statistics': {
                'avg_confidence': sum(r.confidence for r in self.relationships) / len(self.relationships) if self.relationships else 0,
                'cluster_based': sum(1 for r in self.relationships if r.relationship_type == 'cluster_based'),
                'similarity_based': sum(1 for r in self.relationships if r.relationship_type == 'similarity_based'),
                'root_topics': sum(1 for d in self.topic_depths.values() if d == 0)
            }
        }

    def generate_mermaid(self) -> str:
        """
        Generate Mermaid diagram of topic hierarchy.

        Returns:
            Mermaid diagram string
        """
        lines = ["graph TD"]

        # Add nodes
        for topic_id in self.topic_depths.keys():
            name = self.topics.get(topic_id, {}).get('name', 'Unknown')
            depth = self.topic_depths[topic_id]

            # Sanitize ID for Mermaid
            safe_id = topic_id.replace('-', '_').replace(' ', '_')

            # Style based on depth
            if depth == 0:
                lines.append(f"    {safe_id}[{name}]:::root")
            elif depth == 1:
                lines.append(f"    {safe_id}[{name}]:::level1")
            else:
                lines.append(f"    {safe_id}[{name}]:::level2")

        # Add edges
        for rel in self.relationships:
            parent_safe = rel.parent_id.replace('-', '_').replace(' ', '_')
            child_safe = rel.child_id.replace('-', '_').replace(' ', '_')
            conf = f"{rel.confidence:.2f}"

            lines.append(f"    {parent_safe} -->|{conf}| {child_safe}")

        # Add styles
        lines.extend([
            "",
            "    classDef root fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px",
            "    classDef level1 fill:#4ecdc4,stroke:#0e918c,stroke-width:2px",
            "    classDef level2 fill:#95e1d3,stroke:#38ada9,stroke-width:1px"
        ])

        return "\n".join(lines)
