"""
Similarity Calculator for Knowledge Graph

Calculates cosine similarity between page embeddings to identify related pages.
Implements efficient similarity computation with configurable thresholds.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SimilarityConfig:
    """Configuration for similarity calculation"""
    similarity_threshold: float = 0.7
    top_k: int = 5
    min_similarity: float = 0.5
    max_similarities_per_page: int = 10


class SimilarityCalculator:
    """Calculate semantic similarity between pages"""

    def __init__(self, config: Optional[SimilarityConfig] = None):
        """
        Initialize similarity calculator

        Args:
            config: Configuration for similarity calculation
        """
        self.config = config or SimilarityConfig()
        self.stats = {
            "total_comparisons": 0,
            "similarities_above_threshold": 0,
            "total_pages": 0
        }

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First embedding vector
            vec2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        # Convert to numpy arrays
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        # Avoid division by zero
        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Ensure result is in [0, 1] range (handle floating point errors)
        return max(0.0, min(1.0, float(similarity)))

    def calculate_pairwise_similarities(
        self,
        embeddings: Dict[str, List[float]]
    ) -> Dict[Tuple[str, str], float]:
        """
        Calculate pairwise similarities between all embeddings

        Args:
            embeddings: Dictionary mapping page_id to embedding vector

        Returns:
            Dictionary mapping (page_id1, page_id2) tuples to similarity scores
        """
        similarities = {}
        page_ids = list(embeddings.keys())

        self.stats["total_pages"] = len(page_ids)

        logger.info(f"Calculating pairwise similarities for {len(page_ids)} pages")

        # Calculate similarities for all pairs
        for i, page_id1 in enumerate(page_ids):
            for page_id2 in page_ids[i + 1:]:
                self.stats["total_comparisons"] += 1

                similarity = self.cosine_similarity(
                    embeddings[page_id1],
                    embeddings[page_id2]
                )

                # Only store similarities above minimum threshold
                if similarity >= self.config.min_similarity:
                    # Store both directions for easier lookup
                    similarities[(page_id1, page_id2)] = similarity
                    similarities[(page_id2, page_id1)] = similarity

                    if similarity >= self.config.similarity_threshold:
                        self.stats["similarities_above_threshold"] += 1

        logger.info(f"Found {len(similarities) // 2} similar page pairs "
                   f"(threshold: {self.config.similarity_threshold})")

        return similarities

    def get_top_similar_pages(
        self,
        page_id: str,
        similarities: Dict[Tuple[str, str], float],
        k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Get top-k most similar pages for a given page

        Args:
            page_id: ID of the page to find similarities for
            similarities: Dictionary of pairwise similarities
            k: Number of top similar pages to return (uses config if None)

        Returns:
            List of (similar_page_id, similarity_score) tuples, sorted by score
        """
        if k is None:
            k = self.config.top_k

        # Find all similarities involving this page
        page_similarities = []
        for (id1, id2), score in similarities.items():
            if id1 == page_id and score >= self.config.similarity_threshold:
                page_similarities.append((id2, score))

        # Sort by similarity score (descending) and return top k
        page_similarities.sort(key=lambda x: x[1], reverse=True)
        return page_similarities[:min(k, self.config.max_similarities_per_page)]

    def get_all_similarities_by_page(
        self,
        embeddings: Dict[str, List[float]]
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Get top similar pages for all pages

        Args:
            embeddings: Dictionary mapping page_id to embedding vector

        Returns:
            Dictionary mapping page_id to list of (similar_page_id, score) tuples
        """
        # Calculate all pairwise similarities
        similarities = self.calculate_pairwise_similarities(embeddings)

        # Get top similarities for each page
        result = {}
        for page_id in embeddings.keys():
            similar_pages = self.get_top_similar_pages(page_id, similarities)
            if similar_pages:
                result[page_id] = similar_pages

        logger.info(f"Found similarities for {len(result)} pages")

        return result

    def calculate_similarity_matrix(
        self,
        embeddings: Dict[str, List[float]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Calculate full similarity matrix

        Args:
            embeddings: Dictionary mapping page_id to embedding vector

        Returns:
            Tuple of (similarity_matrix, page_ids)
        """
        page_ids = list(embeddings.keys())
        n = len(page_ids)

        # Create embedding matrix
        embedding_matrix = np.array([embeddings[pid] for pid in page_ids])

        # Calculate similarity matrix using vectorized operations
        # Normalize embeddings
        norms = np.linalg.norm(embedding_matrix, axis=1, keepdims=True)
        normalized = embedding_matrix / np.where(norms == 0, 1, norms)

        # Calculate cosine similarities
        similarity_matrix = np.dot(normalized, normalized.T)

        # Ensure diagonal is 1.0 and values are in [0, 1]
        np.fill_diagonal(similarity_matrix, 1.0)
        similarity_matrix = np.clip(similarity_matrix, 0.0, 1.0)

        return similarity_matrix, page_ids

    def get_similarity_statistics(
        self,
        similarities: Dict[Tuple[str, str], float]
    ) -> Dict:
        """
        Calculate statistics about similarity distribution

        Args:
            similarities: Dictionary of pairwise similarities

        Returns:
            Dictionary of statistics
        """
        if not similarities:
            return {
                "count": 0,
                "mean": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0
            }

        # Get unique similarities (remove duplicates from bidirectional storage)
        unique_similarities = []
        seen = set()
        for (id1, id2), score in similarities.items():
            pair = tuple(sorted([id1, id2]))
            if pair not in seen:
                seen.add(pair)
                unique_similarities.append(score)

        scores = np.array(unique_similarities)

        return {
            "count": len(scores),
            "mean": float(np.mean(scores)),
            "median": float(np.median(scores)),
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "std": float(np.std(scores)),
            "above_threshold": sum(1 for s in scores if s >= self.config.similarity_threshold)
        }

    def get_stats(self) -> Dict:
        """Get calculation statistics"""
        return self.stats.copy()


def main():
    """Test similarity calculation"""
    import json

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Sample embeddings (would come from EmbeddingGenerator)
    # These are simplified 5-dimensional vectors for testing
    embeddings = {
        "page1": [0.8, 0.6, 0.2, 0.1, 0.3],
        "page2": [0.7, 0.5, 0.3, 0.2, 0.2],  # Similar to page1
        "page3": [0.1, 0.2, 0.8, 0.9, 0.7],  # Different from page1
        "page4": [0.75, 0.55, 0.25, 0.15, 0.25],  # Very similar to page1
    }

    # Create calculator
    config = SimilarityConfig(
        similarity_threshold=0.7,
        top_k=3
    )
    calculator = SimilarityCalculator(config)

    # Calculate similarities
    similarities_by_page = calculator.get_all_similarities_by_page(embeddings)

    # Print results
    print("\nSimilarity Calculation Results:")
    print(f"Total pages: {len(embeddings)}")
    print(f"\nTop similar pages for each page:")

    for page_id, similar_pages in similarities_by_page.items():
        print(f"\n{page_id}:")
        for similar_id, score in similar_pages:
            print(f"  → {similar_id}: {score:.3f}")

    # Calculate full similarity matrix
    similarity_matrix, page_ids = calculator.calculate_similarity_matrix(embeddings)
    print(f"\nSimilarity Matrix:")
    print(f"Pages: {page_ids}")
    print(similarity_matrix)

    # Get statistics
    pairwise = calculator.calculate_pairwise_similarities(embeddings)
    stats = calculator.get_similarity_statistics(pairwise)
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    main()
