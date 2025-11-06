"""
Topic Clusterer for Knowledge Graph Enrichment

Clusters topics into hierarchical groups using embeddings and hierarchical clustering.
No LLM calls - pure embedding-based clustering for $0 cost.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from collections import Counter
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

from .topic_models import Topic

logger = logging.getLogger(__name__)


@dataclass
class TopicCluster:
    """A cluster of related topics."""
    id: str
    name: str
    topics: List[Topic]
    centroid: Optional[List[float]] = None
    size: int = 0
    representative_topics: List[str] = None
    keywords: List[str] = None


class TopicClusterer:
    """
    Cluster topics into hierarchical groups using embeddings.

    Features:
    - Hierarchical clustering with Ward linkage
    - Automatic optimal cluster count selection
    - Cluster naming from representative topics
    - No LLM calls = $0 cost
    """

    def __init__(
        self,
        topics: List[Topic],
        embedding_generator,
        min_clusters: int = 5,
        max_clusters: int = 10
    ):
        """
        Initialize topic clusterer.

        Args:
            topics: List of Topic objects to cluster
            embedding_generator: Function to generate embeddings
            min_clusters: Minimum number of clusters
            max_clusters: Maximum number of clusters
        """
        self.topics = topics
        self.embedding_generator = embedding_generator
        self.min_clusters = min_clusters
        self.max_clusters = max_clusters

        self.embeddings: Dict[str, List[float]] = {}
        self.clusters: Dict[str, TopicCluster] = {}

        logger.info(
            f"Initialized TopicClusterer with {len(topics)} topics "
            f"(target: {min_clusters}-{max_clusters} clusters)"
        )

    def generate_embeddings(self) -> None:
        """Generate embeddings for all topic names."""
        logger.info(f"Generating embeddings for {len(self.topics)} topics...")

        for topic in self.topics:
            # Use topic name for embedding
            text = topic.name

            # Add description for better context if available
            if topic.description:
                text = f"{topic.name}: {topic.description}"

            # Generate embedding
            embedding = self.embedding_generator(text)
            self.embeddings[topic.id] = embedding

        logger.info(f"Generated {len(self.embeddings)} embeddings")

    def find_optimal_clusters(
        self,
        embeddings_matrix: np.ndarray
    ) -> int:
        """
        Find optimal number of clusters using silhouette score.

        Args:
            embeddings_matrix: Matrix of embeddings (n_topics x embedding_dim)

        Returns:
            Optimal number of clusters
        """
        logger.info("Finding optimal cluster count...")

        best_score = -1
        best_n_clusters = self.min_clusters

        for n_clusters in range(self.min_clusters, self.max_clusters + 1):
            # Skip if we have fewer topics than clusters
            if n_clusters > len(self.topics):
                break

            # Perform clustering
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage='ward'
            )
            labels = clustering.fit_predict(embeddings_matrix)

            # Calculate silhouette score
            score = silhouette_score(embeddings_matrix, labels)

            logger.debug(f"n_clusters={n_clusters}, silhouette={score:.3f}")

            if score > best_score:
                best_score = score
                best_n_clusters = n_clusters

        logger.info(
            f"Optimal cluster count: {best_n_clusters} "
            f"(silhouette score: {best_score:.3f})"
        )

        return best_n_clusters

    def cluster_topics(
        self,
        n_clusters: Optional[int] = None
    ) -> Dict[str, TopicCluster]:
        """
        Cluster topics using hierarchical clustering.

        Args:
            n_clusters: Number of clusters (auto-detect if None)

        Returns:
            Dictionary of cluster_id -> TopicCluster
        """
        if not self.embeddings:
            self.generate_embeddings()

        # Convert embeddings to matrix
        topic_ids = list(self.embeddings.keys())
        embeddings_matrix = np.array([
            self.embeddings[topic_id]
            for topic_id in topic_ids
        ])

        logger.info(f"Embeddings matrix shape: {embeddings_matrix.shape}")

        # Find optimal cluster count if not specified
        if n_clusters is None:
            n_clusters = self.find_optimal_clusters(embeddings_matrix)

        # Perform hierarchical clustering
        logger.info(f"Clustering {len(self.topics)} topics into {n_clusters} clusters...")

        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage='ward'
        )
        labels = clustering.fit_predict(embeddings_matrix)

        # Organize topics by cluster
        clusters_dict: Dict[int, List[Topic]] = {}
        for topic_id, label in zip(topic_ids, labels):
            if label not in clusters_dict:
                clusters_dict[label] = []

            # Find topic object
            topic = next(t for t in self.topics if t.id == topic_id)
            clusters_dict[label].append(topic)

        # Create TopicCluster objects
        self.clusters = {}
        for cluster_id, cluster_topics in clusters_dict.items():
            # Calculate cluster centroid
            cluster_embeddings = [
                self.embeddings[t.id] for t in cluster_topics
            ]
            centroid = np.mean(cluster_embeddings, axis=0).tolist()

            # Generate cluster name
            cluster_name = self.name_cluster(cluster_topics)

            # Get representative topics (most frequent)
            representative = self._get_representative_topics(cluster_topics)

            # Extract keywords from topic names
            keywords = self._extract_keywords(cluster_topics)

            cluster = TopicCluster(
                id=f"cluster-{cluster_id}",
                name=cluster_name,
                topics=cluster_topics,
                centroid=centroid,
                size=len(cluster_topics),
                representative_topics=representative,
                keywords=keywords
            )

            self.clusters[cluster.id] = cluster

            logger.info(
                f"Cluster {cluster_id}: '{cluster_name}' "
                f"({len(cluster_topics)} topics)"
            )

        return self.clusters

    def name_cluster(self, topics: List[Topic]) -> str:
        """
        Generate cluster name from topics.

        Uses most frequent category and common words in topic names.

        Args:
            topics: List of topics in cluster

        Returns:
            Cluster name
        """
        # Get most common category
        categories = [t.category.value for t in topics]
        category_counts = Counter(categories)
        most_common_category = category_counts.most_common(1)[0][0]

        # Get most common words in topic names (excluding common words)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}

        all_words = []
        for topic in topics:
            words = topic.name.lower().split()
            all_words.extend([w for w in words if w not in stopwords])

        word_counts = Counter(all_words)

        # Get top 2-3 most common words
        if word_counts:
            top_words = [word for word, _ in word_counts.most_common(3)]
            cluster_name = ' '.join(top_words).title()
        else:
            cluster_name = most_common_category.replace('_', ' ').title()

        return cluster_name

    def _get_representative_topics(
        self,
        topics: List[Topic],
        top_n: int = 5
    ) -> List[str]:
        """
        Get most representative topics from cluster.

        Args:
            topics: Topics in cluster
            top_n: Number of representative topics

        Returns:
            List of topic names
        """
        # Sort by importance/frequency
        sorted_topics = sorted(
            topics,
            key=lambda t: (t.importance, t.frequency),
            reverse=True
        )

        return [t.name for t in sorted_topics[:top_n]]

    def _extract_keywords(
        self,
        topics: List[Topic],
        top_n: int = 10
    ) -> List[str]:
        """
        Extract keywords from topic names.

        Args:
            topics: Topics in cluster
            top_n: Number of keywords

        Returns:
            List of keywords
        """
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is'
        }

        all_words = []
        for topic in topics:
            # Split topic name into words
            words = topic.name.lower().split()
            all_words.extend([w for w in words if w not in stopwords])

        # Count word frequencies
        word_counts = Counter(all_words)

        # Return top N
        return [word for word, _ in word_counts.most_common(top_n)]

    def build_topic_hierarchy(
        self,
        clusters: Optional[Dict[str, TopicCluster]] = None
    ) -> Dict:
        """
        Build 3-level topic hierarchy from clusters.

        Hierarchy:
        - Level 0: Root categories (from clusters)
        - Level 1: Primary topics (most important in cluster)
        - Level 2: Specific topics (remaining topics)

        Args:
            clusters: Topic clusters (uses self.clusters if None)

        Returns:
            Hierarchy dictionary
        """
        if clusters is None:
            clusters = self.clusters

        hierarchy = {
            'root': [],
            'primary': [],
            'specific': []
        }

        logger.info("Building 3-level topic hierarchy...")

        for cluster in clusters.values():
            # Level 0: Root (cluster itself)
            root_topic = {
                'id': cluster.id,
                'name': cluster.name,
                'level': 0,
                'topic_count': cluster.size,
                'keywords': cluster.keywords,
                'children': []
            }

            # Sort topics by importance
            sorted_topics = sorted(
                cluster.topics,
                key=lambda t: (t.importance, t.frequency),
                reverse=True
            )

            # Determine primary topic threshold (top 30% or at least 2)
            primary_count = max(2, int(len(sorted_topics) * 0.3))

            # Level 1: Primary topics
            primary_topics = sorted_topics[:primary_count]
            for topic in primary_topics:
                primary = {
                    'id': topic.id,
                    'name': topic.name,
                    'level': 1,
                    'parent_id': cluster.id,
                    'category': topic.category.value,
                    'importance': topic.importance,
                    'frequency': topic.frequency
                }
                hierarchy['primary'].append(primary)
                root_topic['children'].append(topic.id)

            # Level 2: Specific topics
            specific_topics = sorted_topics[primary_count:]
            for topic in specific_topics:
                specific = {
                    'id': topic.id,
                    'name': topic.name,
                    'level': 2,
                    'parent_id': cluster.id,
                    'category': topic.category.value,
                    'importance': topic.importance,
                    'frequency': topic.frequency
                }
                hierarchy['specific'].append(specific)
                root_topic['children'].append(topic.id)

            hierarchy['root'].append(root_topic)

        logger.info(
            f"Hierarchy built: {len(hierarchy['root'])} root, "
            f"{len(hierarchy['primary'])} primary, "
            f"{len(hierarchy['specific'])} specific topics"
        )

        return hierarchy

    def get_cluster_stats(self) -> Dict:
        """Get clustering statistics."""
        if not self.clusters:
            return {}

        cluster_sizes = [c.size for c in self.clusters.values()]

        return {
            'n_clusters': len(self.clusters),
            'total_topics': len(self.topics),
            'avg_cluster_size': np.mean(cluster_sizes),
            'min_cluster_size': min(cluster_sizes),
            'max_cluster_size': max(cluster_sizes),
            'cluster_names': [c.name for c in self.clusters.values()]
        }
