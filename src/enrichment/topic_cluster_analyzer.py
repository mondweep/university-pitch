"""
Topic Cluster Analyzer

Clusters topics by co-occurrence patterns using hierarchical clustering.
Works directly with JSON graph format without external dependencies.
"""

import json
import logging
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import numpy as np
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TopicCluster:
    """Represents a cluster of related topics."""
    id: str
    name: str
    topics: List[str]  # List of topic IDs
    coherence_score: float
    centroid_topic: str  # Most central topic ID


class TopicClusterAnalyzer:
    """
    Analyze topic co-occurrence and create clusters.

    Uses hierarchical clustering with Ward linkage based on
    co-occurrence frequency.

    Steps:
    1. Build co-occurrence matrix from HAS_TOPIC edges
    2. Calculate pairwise similarity (Jaccard)
    3. Apply hierarchical clustering
    4. Create cluster nodes with coherence scores
    """

    def __init__(
        self,
        n_clusters: int = 5,
        min_cluster_size: int = 2,
        similarity_threshold: float = 0.3
    ):
        """
        Initialize cluster analyzer.

        Args:
            n_clusters: Target number of clusters (3-5 recommended)
            min_cluster_size: Minimum topics per cluster
            similarity_threshold: Minimum similarity for clustering
        """
        self.n_clusters = n_clusters
        self.min_cluster_size = min_cluster_size
        self.similarity_threshold = similarity_threshold

        self.topics: Dict[str, Dict] = {}
        self.pages_per_topic: Dict[str, Set[str]] = defaultdict(set)
        self.co_occurrence: Dict[Tuple[str, str], int] = {}
        self.similarity_matrix: np.ndarray = None
        self.clusters: List[TopicCluster] = []

    def load_topics_from_graph(self, graph: Dict) -> None:
        """
        Load topics and build co-occurrence matrix from graph.

        Args:
            graph: Graph dict with 'nodes' and 'edges' keys
        """
        logger.info("Loading topics from graph...")

        # Extract Topic nodes
        for node in graph['nodes']:
            if node.get('node_type') == 'Topic':
                topic_id = node['id']
                self.topics[topic_id] = node.get('data', {})

        logger.info(f"Found {len(self.topics)} topics")

        # Build co-occurrence from HAS_TOPIC edges
        for edge in graph['edges']:
            if edge.get('edge_type') == 'HAS_TOPIC':
                page_id = edge['from']
                topic_id = edge['to']
                self.pages_per_topic[topic_id].add(page_id)

        logger.info(f"Built page-topic mappings for {len(self.pages_per_topic)} topics")

        # Calculate co-occurrence
        self._calculate_co_occurrence()

    def _calculate_co_occurrence(self) -> None:
        """Calculate co-occurrence matrix between topics."""
        logger.info("Calculating topic co-occurrence...")

        topic_ids = list(self.topics.keys())
        n_topics = len(topic_ids)

        for i, topic1 in enumerate(topic_ids):
            for j, topic2 in enumerate(topic_ids[i+1:], start=i+1):
                # Count pages where both topics appear
                pages1 = self.pages_per_topic[topic1]
                pages2 = self.pages_per_topic[topic2]
                co_count = len(pages1 & pages2)

                if co_count > 0:
                    self.co_occurrence[(topic1, topic2)] = co_count
                    self.co_occurrence[(topic2, topic1)] = co_count

        logger.info(f"Found {len(self.co_occurrence)} co-occurrence pairs")

    def build_similarity_matrix(self) -> np.ndarray:
        """
        Build similarity matrix using Jaccard similarity.

        Returns:
            NxN similarity matrix where N = number of topics
        """
        logger.info("Building similarity matrix...")

        topic_ids = list(self.topics.keys())
        n_topics = len(topic_ids)

        # Initialize similarity matrix
        similarity = np.zeros((n_topics, n_topics))

        for i, topic1 in enumerate(topic_ids):
            for j, topic2 in enumerate(topic_ids):
                if i == j:
                    similarity[i, j] = 1.0
                else:
                    # Jaccard similarity
                    pages1 = self.pages_per_topic[topic1]
                    pages2 = self.pages_per_topic[topic2]

                    intersection = len(pages1 & pages2)
                    union = len(pages1 | pages2)

                    if union > 0:
                        similarity[i, j] = intersection / union

        self.similarity_matrix = similarity
        logger.info(f"Built {n_topics}x{n_topics} similarity matrix")

        return similarity

    def cluster_topics(self) -> List[TopicCluster]:
        """
        Cluster topics using hierarchical clustering.

        Returns:
            List of TopicCluster objects
        """
        logger.info("Clustering topics...")

        if self.similarity_matrix is None:
            self.build_similarity_matrix()

        topic_ids = list(self.topics.keys())
        n_topics = len(topic_ids)

        if n_topics < self.min_cluster_size:
            logger.warning(f"Too few topics ({n_topics}) for clustering")
            # Create single cluster
            cluster = TopicCluster(
                id="cluster_0",
                name="All Topics",
                topics=topic_ids,
                coherence_score=1.0,
                centroid_topic=topic_ids[0] if topic_ids else None
            )
            self.clusters = [cluster]
            return self.clusters

        # Use simple agglomerative clustering
        # Convert similarity to distance
        distance_matrix = 1 - self.similarity_matrix

        # Perform clustering (simplified hierarchical)
        cluster_assignments = self._hierarchical_clustering(
            distance_matrix,
            n_clusters=min(self.n_clusters, n_topics)
        )

        # Build cluster objects
        self.clusters = []
        for cluster_id in range(max(cluster_assignments) + 1):
            cluster_topic_ids = [
                topic_ids[i] for i, c in enumerate(cluster_assignments)
                if c == cluster_id
            ]

            if len(cluster_topic_ids) >= self.min_cluster_size or cluster_id == 0:
                # Calculate coherence (average intra-cluster similarity)
                coherence = self._calculate_coherence(cluster_topic_ids)

                # Find centroid (most connected topic in cluster)
                centroid = self._find_centroid(cluster_topic_ids)

                # Generate cluster name from centroid topic
                cluster_name = self._generate_cluster_name(cluster_topic_ids)

                cluster = TopicCluster(
                    id=f"cluster_{cluster_id}",
                    name=cluster_name,
                    topics=cluster_topic_ids,
                    coherence_score=coherence,
                    centroid_topic=centroid
                )
                self.clusters.append(cluster)

        logger.info(f"Created {len(self.clusters)} clusters")

        return self.clusters

    def _hierarchical_clustering(
        self,
        distance_matrix: np.ndarray,
        n_clusters: int
    ) -> List[int]:
        """
        Simple hierarchical clustering implementation.

        Args:
            distance_matrix: NxN distance matrix
            n_clusters: Target number of clusters

        Returns:
            Cluster assignment for each topic
        """
        n_topics = distance_matrix.shape[0]

        # Initialize each topic as its own cluster
        clusters = [[i] for i in range(n_topics)]

        # Merge clusters until we have n_clusters
        while len(clusters) > n_clusters:
            # Find two closest clusters
            min_dist = float('inf')
            merge_i, merge_j = 0, 1

            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # Average linkage
                    dist = 0
                    count = 0
                    for ii in clusters[i]:
                        for jj in clusters[j]:
                            dist += distance_matrix[ii, jj]
                            count += 1

                    avg_dist = dist / count if count > 0 else float('inf')

                    if avg_dist < min_dist:
                        min_dist = avg_dist
                        merge_i, merge_j = i, j

            # Merge clusters
            clusters[merge_i].extend(clusters[merge_j])
            clusters.pop(merge_j)

        # Create assignment array
        assignments = [0] * n_topics
        for cluster_id, cluster in enumerate(clusters):
            for topic_idx in cluster:
                assignments[topic_idx] = cluster_id

        return assignments

    def _calculate_coherence(self, topic_ids: List[str]) -> float:
        """Calculate cluster coherence (average intra-cluster similarity)."""
        if len(topic_ids) < 2:
            return 1.0

        topic_id_to_idx = {tid: i for i, tid in enumerate(self.topics.keys())}

        similarities = []
        for i, topic1 in enumerate(topic_ids):
            for topic2 in topic_ids[i+1:]:
                idx1 = topic_id_to_idx[topic1]
                idx2 = topic_id_to_idx[topic2]
                similarities.append(self.similarity_matrix[idx1, idx2])

        return np.mean(similarities) if similarities else 0.0

    def _find_centroid(self, topic_ids: List[str]) -> str:
        """Find most central topic in cluster (highest avg similarity)."""
        if not topic_ids:
            return None

        if len(topic_ids) == 1:
            return topic_ids[0]

        topic_id_to_idx = {tid: i for i, tid in enumerate(self.topics.keys())}

        max_avg_sim = -1
        centroid = topic_ids[0]

        for topic in topic_ids:
            idx = topic_id_to_idx[topic]
            # Calculate average similarity to other topics in cluster
            sims = [
                self.similarity_matrix[idx, topic_id_to_idx[other]]
                for other in topic_ids if other != topic
            ]
            avg_sim = np.mean(sims) if sims else 0

            if avg_sim > max_avg_sim:
                max_avg_sim = avg_sim
                centroid = topic

        return centroid

    def _generate_cluster_name(self, topic_ids: List[str]) -> str:
        """Generate descriptive cluster name from topics."""
        if not topic_ids:
            return "Empty Cluster"

        # Use centroid topic name
        centroid = self._find_centroid(topic_ids)
        if centroid and centroid in self.topics:
            topic_name = self.topics[centroid].get('name', 'Unknown')
            return f"{topic_name} & Related"

        return "Topic Cluster"

    def export_clusters(self) -> Dict:
        """
        Export cluster data for visualization.

        Returns:
            Dictionary with cluster statistics and data
        """
        return {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'n_clusters': len(self.clusters),
                'n_topics': len(self.topics),
                'similarity_threshold': self.similarity_threshold
            },
            'clusters': [
                {
                    'id': cluster.id,
                    'name': cluster.name,
                    'topics': cluster.topics,
                    'topic_names': [
                        self.topics[tid].get('name', 'Unknown')
                        for tid in cluster.topics
                    ],
                    'coherence_score': float(cluster.coherence_score),
                    'centroid_topic': cluster.centroid_topic,
                    'size': len(cluster.topics)
                }
                for cluster in self.clusters
            ],
            'statistics': {
                'avg_cluster_size': np.mean([len(c.topics) for c in self.clusters]),
                'avg_coherence': np.mean([c.coherence_score for c in self.clusters]),
                'min_cluster_size': min([len(c.topics) for c in self.clusters]) if self.clusters else 0,
                'max_cluster_size': max([len(c.topics) for c in self.clusters]) if self.clusters else 0
            }
        }
