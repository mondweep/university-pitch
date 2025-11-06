"""
Topic Clusterer for Knowledge Graph

Clusters similar topics using hierarchical clustering and identifies
topic parent-child relationships.
"""

import logging
import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class Topic:
    """Topic node representation"""
    id: str
    name: str
    frequency: int
    embedding: Optional[List[float]] = None
    category: Optional[str] = None
    level: int = 0  # Hierarchy level: 0 = root, 1+ = subtopic


@dataclass
class TopicCluster:
    """Topic cluster representation"""
    cluster_id: int
    topics: List[Topic]
    centroid_topic: Topic  # Most central topic in cluster
    avg_similarity: float  # Average intra-cluster similarity
    size: int


class TopicClusterer:
    """
    Cluster similar topics using hierarchical clustering.

    Uses topic embeddings to measure semantic similarity and creates
    topic hierarchies with parent-child relationships.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.7,
        min_cluster_size: int = 2,
        max_cluster_size: int = 20
    ):
        """
        Initialize topic clusterer.

        Args:
            similarity_threshold: Minimum similarity for clustering (0-1)
            min_cluster_size: Minimum topics per cluster
            max_cluster_size: Maximum topics per cluster
        """
        self.similarity_threshold = similarity_threshold
        self.min_cluster_size = min_cluster_size
        self.max_cluster_size = max_cluster_size

        logger.info(
            f"Initialized TopicClusterer with similarity_threshold={similarity_threshold}"
        )

    def _compute_similarity_matrix(self, topics: List[Topic]) -> np.ndarray:
        """
        Compute pairwise cosine similarity matrix for topics.

        Args:
            topics: List of topics with embeddings

        Returns:
            NxN similarity matrix
        """
        embeddings = np.array([t.embedding for t in topics])
        similarity = cosine_similarity(embeddings)

        logger.debug(f"Computed {similarity.shape[0]}x{similarity.shape[1]} similarity matrix")

        return similarity

    def _hierarchical_clustering(
        self,
        topics: List[Topic],
        similarity_matrix: np.ndarray
    ) -> np.ndarray:
        """
        Perform hierarchical clustering on topics.

        Args:
            topics: List of topics
            similarity_matrix: Pairwise similarity matrix

        Returns:
            Cluster labels for each topic
        """
        # Convert similarity to distance
        distance_matrix = 1 - similarity_matrix

        # Ensure distance matrix is valid
        np.fill_diagonal(distance_matrix, 0)
        distance_matrix = np.clip(distance_matrix, 0, 1)

        # Convert to condensed distance matrix for linkage
        condensed_distances = squareform(distance_matrix, checks=False)

        # Perform hierarchical clustering (average linkage)
        linkage_matrix = linkage(condensed_distances, method='average')

        # Cut tree at similarity threshold
        threshold = 1 - self.similarity_threshold
        cluster_labels = fcluster(linkage_matrix, threshold, criterion='distance')

        logger.info(f"Created {len(set(cluster_labels))} clusters")

        return cluster_labels

    def _create_clusters(
        self,
        topics: List[Topic],
        cluster_labels: np.ndarray,
        similarity_matrix: np.ndarray
    ) -> List[TopicCluster]:
        """
        Create TopicCluster objects from clustering results.

        Args:
            topics: List of topics
            cluster_labels: Cluster assignment for each topic
            similarity_matrix: Pairwise similarity matrix

        Returns:
            List of TopicCluster objects
        """
        clusters = []
        unique_labels = set(cluster_labels)

        for label in unique_labels:
            # Get topics in this cluster
            cluster_indices = np.where(cluster_labels == label)[0]
            cluster_topics = [topics[i] for i in cluster_indices]

            # Skip if cluster is too small
            if len(cluster_topics) < self.min_cluster_size:
                logger.debug(f"Skipping cluster {label} (size {len(cluster_topics)} < {self.min_cluster_size})")
                continue

            # Split if cluster is too large
            if len(cluster_topics) > self.max_cluster_size:
                logger.warning(f"Cluster {label} size {len(cluster_topics)} exceeds max {self.max_cluster_size}, splitting...")
                # Recursively cluster large clusters
                sub_similarity = similarity_matrix[np.ix_(cluster_indices, cluster_indices)]
                sub_labels = self._hierarchical_clustering(cluster_topics, sub_similarity)
                sub_clusters = self._create_clusters(cluster_topics, sub_labels, sub_similarity)
                clusters.extend(sub_clusters)
                continue

            # Calculate average intra-cluster similarity
            cluster_sim_matrix = similarity_matrix[np.ix_(cluster_indices, cluster_indices)]
            avg_similarity = np.mean(cluster_sim_matrix[np.triu_indices_from(cluster_sim_matrix, k=1)])

            # Find centroid topic (most similar to all others)
            mean_similarities = cluster_sim_matrix.mean(axis=1)
            centroid_idx = mean_similarities.argmax()
            centroid_topic = cluster_topics[centroid_idx]

            cluster = TopicCluster(
                cluster_id=len(clusters) + 1,
                topics=cluster_topics,
                centroid_topic=centroid_topic,
                avg_similarity=float(avg_similarity),
                size=len(cluster_topics)
            )

            clusters.append(cluster)

            logger.info(
                f"Cluster {cluster.cluster_id}: {cluster.size} topics, "
                f"centroid='{centroid_topic.name}', "
                f"similarity={avg_similarity:.3f}"
            )

        return clusters

    def cluster_topics(self, topics: List[Topic]) -> List[TopicCluster]:
        """
        Cluster similar topics using hierarchical clustering.

        Args:
            topics: List of topics with embeddings

        Returns:
            List of topic clusters
        """
        if len(topics) < 2:
            logger.warning("Less than 2 topics, skipping clustering")
            return []

        # Filter topics with embeddings
        valid_topics = [t for t in topics if t.embedding is not None]
        if len(valid_topics) < 2:
            logger.error("Less than 2 topics with embeddings")
            return []

        logger.info(f"Clustering {len(valid_topics)} topics...")

        # Compute similarity matrix
        similarity_matrix = self._compute_similarity_matrix(valid_topics)

        # Perform hierarchical clustering
        cluster_labels = self._hierarchical_clustering(valid_topics, similarity_matrix)

        # Create cluster objects
        clusters = self._create_clusters(valid_topics, cluster_labels, similarity_matrix)

        logger.info(f"Created {len(clusters)} topic clusters")

        return clusters

    def build_hierarchy(self, topics: List[Topic]) -> Dict[str, List[str]]:
        """
        Build parent-child topic hierarchy.

        Uses frequency to determine hierarchy level:
        - High frequency = more general (parent)
        - Low frequency = more specific (child)

        Args:
            topics: List of topics with embeddings

        Returns:
            Dictionary mapping parent topic IDs to list of child topic IDs
        """
        hierarchy = {}

        # Sort topics by frequency (descending)
        sorted_topics = sorted(topics, key=lambda t: t.frequency, reverse=True)

        # Top 20% are root topics
        root_count = max(1, len(sorted_topics) // 5)
        root_topics = sorted_topics[:root_count]

        # Compute similarity matrix
        if len(topics) < 2:
            return hierarchy

        similarity_matrix = self._compute_similarity_matrix(topics)
        topic_index = {t.id: i for i, t in enumerate(topics)}

        # Assign root topics (level 0)
        for topic in root_topics:
            topic.level = 0
            hierarchy[topic.id] = []

        # Assign children to most similar root topic
        for topic in sorted_topics[root_count:]:
            topic_idx = topic_index[topic.id]

            # Find most similar root topic
            max_sim = -1
            best_parent = None

            for root_topic in root_topics:
                root_idx = topic_index[root_topic.id]
                sim = similarity_matrix[topic_idx, root_idx]

                if sim > max_sim and sim >= self.similarity_threshold:
                    max_sim = sim
                    best_parent = root_topic

            # Assign parent-child relationship
            if best_parent:
                topic.level = 1
                hierarchy[best_parent.id].append(topic.id)
                logger.debug(f"'{topic.name}' -> '{best_parent.name}' (sim={max_sim:.3f})")
            else:
                # No parent found, make it a root topic
                topic.level = 0
                hierarchy[topic.id] = []
                logger.debug(f"'{topic.name}' promoted to root (no parent found)")

        # Report hierarchy stats
        total_children = sum(len(children) for children in hierarchy.values())
        logger.info(
            f"Built topic hierarchy: {len(hierarchy)} root topics, "
            f"{total_children} child topics"
        )

        return hierarchy

    def identify_root_topics(
        self,
        topics: List[Topic],
        top_n: int = 20
    ) -> List[Topic]:
        """
        Identify top-level (most general) topics.

        Root topics are identified by:
        1. High frequency (appear in many pages)
        2. High centrality (similar to many other topics)

        Args:
            topics: List of topics
            top_n: Number of root topics to return

        Returns:
            List of root topics
        """
        if len(topics) <= top_n:
            return topics

        # Compute frequency score (normalized)
        max_freq = max(t.frequency for t in topics)
        freq_scores = {t.id: t.frequency / max_freq for t in topics}

        # Compute centrality score (average similarity to all topics)
        similarity_matrix = self._compute_similarity_matrix(topics)
        centrality_scores = {
            topics[i].id: similarity_matrix[i].mean()
            for i in range(len(topics))
        }

        # Combined score (frequency + centrality)
        combined_scores = {
            t.id: 0.6 * freq_scores[t.id] + 0.4 * centrality_scores[t.id]
            for t in topics
        }

        # Sort by combined score
        sorted_topics = sorted(
            topics,
            key=lambda t: combined_scores[t.id],
            reverse=True
        )

        root_topics = sorted_topics[:top_n]

        logger.info(
            f"Identified {len(root_topics)} root topics from {len(topics)} total topics"
        )

        for i, topic in enumerate(root_topics[:5], 1):
            logger.info(
                f"  {i}. {topic.name} (freq={topic.frequency}, "
                f"score={combined_scores[topic.id]:.3f})"
            )

        return root_topics

    def get_clustering_statistics(self, clusters: List[TopicCluster]) -> Dict:
        """
        Calculate clustering quality statistics.

        Args:
            clusters: List of topic clusters

        Returns:
            Dictionary with clustering statistics
        """
        if not clusters:
            return {}

        cluster_sizes = [c.size for c in clusters]
        similarities = [c.avg_similarity for c in clusters]

        stats = {
            'num_clusters': len(clusters),
            'total_topics': sum(cluster_sizes),
            'avg_cluster_size': np.mean(cluster_sizes),
            'min_cluster_size': min(cluster_sizes),
            'max_cluster_size': max(cluster_sizes),
            'avg_similarity': np.mean(similarities),
            'min_similarity': min(similarities),
            'max_similarity': max(similarities),
        }

        logger.info(f"Clustering statistics: {stats}")

        return stats
