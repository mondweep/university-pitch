"""
Similarity Calculator for Content Recommendations
Calculates cosine similarity between embeddings and multi-signal similarity.
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """Result of similarity calculation."""
    content_id: str
    similarity: float
    similarity_type: str  # 'embedding', 'topic', 'entity', 'multi'
    metadata: Dict


class SimilarityCalculator:
    """Calculate similarity between content items using multiple signals."""

    def __init__(
        self,
        embedding_weight: float = 0.6,
        topic_weight: float = 0.3,
        entity_weight: float = 0.1
    ):
        """
        Initialize similarity calculator.

        Args:
            embedding_weight: Weight for embedding similarity
            topic_weight: Weight for topic overlap
            entity_weight: Weight for entity overlap
        """
        self.embedding_weight = embedding_weight
        self.topic_weight = topic_weight
        self.entity_weight = entity_weight

        # Validate weights sum to 1
        total = embedding_weight + topic_weight + entity_weight
        if not np.isclose(total, 1.0):
            logger.warning(f"Similarity weights sum to {total}, normalizing...")
            self.embedding_weight /= total
            self.topic_weight /= total
            self.entity_weight /= total

        logger.info(
            f"Initialized SimilarityCalculator "
            f"(emb={self.embedding_weight:.2f}, "
            f"topic={self.topic_weight:.2f}, "
            f"entity={self.entity_weight:.2f})"
        )

    def cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        if not vec1 or not vec2:
            return 0.0

        if len(vec1) != len(vec2):
            raise ValueError(
                f"Vector dimensions mismatch: {len(vec1)} vs {len(vec2)}"
            )

        # Convert to numpy arrays
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Ensure result is in [0, 1] (should be [-1, 1] but we use positive embeddings)
        similarity = max(0.0, min(1.0, similarity))

        return float(similarity)

    def jaccard_similarity(
        self,
        set1: set,
        set2: set
    ) -> float:
        """
        Calculate Jaccard similarity between two sets.

        Args:
            set1: First set
            set2: Second set

        Returns:
            Jaccard similarity score (0-1)
        """
        if not set1 or not set2:
            return 0.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        if union == 0:
            return 0.0

        return intersection / union

    def find_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: Dict[str, List[float]],
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[SimilarityResult]:
        """
        Find most similar content items based on embeddings.

        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: Dictionary of content_id -> embedding
            top_k: Number of top results to return
            threshold: Minimum similarity threshold

        Returns:
            List of similarity results sorted by score
        """
        similarities = []

        for content_id, embedding in candidate_embeddings.items():
            similarity = self.cosine_similarity(query_embedding, embedding)

            if similarity >= threshold:
                similarities.append(
                    SimilarityResult(
                        content_id=content_id,
                        similarity=similarity,
                        similarity_type='embedding',
                        metadata={'method': 'cosine'}
                    )
                )

        # Sort by similarity descending
        similarities.sort(key=lambda x: x.similarity, reverse=True)

        # Return top K
        return similarities[:top_k]

    def topic_similarity(
        self,
        topics1: List[str],
        topics2: List[str]
    ) -> float:
        """
        Calculate topic overlap similarity.

        Args:
            topics1: First list of topic IDs
            topics2: Second list of topic IDs

        Returns:
            Topic similarity score (0-1)
        """
        return self.jaccard_similarity(set(topics1), set(topics2))

    def entity_similarity(
        self,
        entities1: List[str],
        entities2: List[str]
    ) -> float:
        """
        Calculate entity overlap similarity.

        Args:
            entities1: First list of entity names
            entities2: Second list of entity names

        Returns:
            Entity similarity score (0-1)
        """
        return self.jaccard_similarity(set(entities1), set(entities2))

    def multi_signal_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
        topics1: List[str],
        topics2: List[str],
        entities1: Optional[List[str]] = None,
        entities2: Optional[List[str]] = None
    ) -> Tuple[float, Dict]:
        """
        Calculate multi-signal similarity combining embeddings, topics, and entities.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            topics1: First list of topics
            topics2: Second list of topics
            entities1: First list of entities (optional)
            entities2: Second list of entities (optional)

        Returns:
            Tuple of (weighted_similarity, signal_breakdown)
        """
        # Calculate individual similarities
        emb_sim = self.cosine_similarity(embedding1, embedding2)
        topic_sim = self.topic_similarity(topics1, topics2)

        # Entity similarity (optional)
        if entities1 and entities2:
            entity_sim = self.entity_similarity(entities1, entities2)
        else:
            entity_sim = 0.0
            # Redistribute weight if no entities
            total_weight = self.embedding_weight + self.topic_weight
            emb_weight = self.embedding_weight / total_weight
            topic_weight = self.topic_weight / total_weight
            entity_weight = 0.0

        # Use configured weights if entities present
        if entities1 and entities2:
            emb_weight = self.embedding_weight
            topic_weight = self.topic_weight
            entity_weight = self.entity_weight

        # Weighted combination
        weighted_sim = (
            emb_sim * emb_weight +
            topic_sim * topic_weight +
            entity_sim * entity_weight
        )

        # Signal breakdown
        breakdown = {
            'embedding_similarity': emb_sim,
            'topic_similarity': topic_sim,
            'entity_similarity': entity_sim,
            'embedding_weight': emb_weight,
            'topic_weight': topic_weight,
            'entity_weight': entity_weight,
            'weighted_similarity': weighted_sim
        }

        return weighted_sim, breakdown

    def batch_similarity(
        self,
        query_id: str,
        query_data: Dict,
        candidates: Dict[str, Dict],
        top_k: int = 5,
        threshold: float = 0.7,
        use_multi_signal: bool = True
    ) -> List[SimilarityResult]:
        """
        Calculate similarity for a query against multiple candidates.

        Args:
            query_id: Query content ID
            query_data: Query data with embedding, topics, entities
            candidates: Dictionary of candidate_id -> candidate_data
            top_k: Number of top results
            threshold: Minimum similarity threshold
            use_multi_signal: Whether to use multi-signal similarity

        Returns:
            List of similarity results
        """
        similarities = []

        query_embedding = query_data.get('embedding', [])
        query_topics = query_data.get('topics', [])
        query_entities = query_data.get('entities', [])

        for candidate_id, candidate_data in candidates.items():
            # Skip self-similarity
            if candidate_id == query_id:
                continue

            candidate_embedding = candidate_data.get('embedding', [])
            candidate_topics = candidate_data.get('topics', [])
            candidate_entities = candidate_data.get('entities', [])

            if use_multi_signal:
                # Multi-signal similarity
                similarity, breakdown = self.multi_signal_similarity(
                    query_embedding,
                    candidate_embedding,
                    query_topics,
                    candidate_topics,
                    query_entities,
                    candidate_entities
                )

                if similarity >= threshold:
                    similarities.append(
                        SimilarityResult(
                            content_id=candidate_id,
                            similarity=similarity,
                            similarity_type='multi',
                            metadata=breakdown
                        )
                    )
            else:
                # Embedding-only similarity
                similarity = self.cosine_similarity(
                    query_embedding,
                    candidate_embedding
                )

                if similarity >= threshold:
                    similarities.append(
                        SimilarityResult(
                            content_id=candidate_id,
                            similarity=similarity,
                            similarity_type='embedding',
                            metadata={'method': 'cosine'}
                        )
                    )

        # Sort by similarity descending
        similarities.sort(key=lambda x: x.similarity, reverse=True)

        # Return top K
        return similarities[:top_k]

    def approximate_nearest_neighbors(
        self,
        query_embedding: List[float],
        candidate_embeddings: Dict[str, List[float]],
        top_k: int = 10,
        sample_ratio: float = 0.1
    ) -> List[SimilarityResult]:
        """
        Fast approximate nearest neighbors using sampling.

        For large graphs, this provides significant speedup with minimal accuracy loss.

        Args:
            query_embedding: Query embedding
            candidate_embeddings: All candidate embeddings
            top_k: Number of results
            sample_ratio: Fraction of candidates to sample (0-1)

        Returns:
            Approximate top-K similar items
        """
        import random

        # Sample candidates
        n_samples = max(top_k * 10, int(len(candidate_embeddings) * sample_ratio))
        n_samples = min(n_samples, len(candidate_embeddings))

        if n_samples >= len(candidate_embeddings):
            # Use exact search if sample size is close to full size
            return self.find_similar(
                query_embedding,
                candidate_embeddings,
                top_k=top_k,
                threshold=0.0  # No threshold for ANN
            )

        # Random sampling
        sampled_ids = random.sample(list(candidate_embeddings.keys()), n_samples)
        sampled_embeddings = {
            id: candidate_embeddings[id]
            for id in sampled_ids
        }

        # Find similar in sample
        results = self.find_similar(
            query_embedding,
            sampled_embeddings,
            top_k=top_k,
            threshold=0.0
        )

        logger.debug(
            f"ANN search: sampled {n_samples}/{len(candidate_embeddings)} "
            f"candidates, found {len(results)} results"
        )

        return results
