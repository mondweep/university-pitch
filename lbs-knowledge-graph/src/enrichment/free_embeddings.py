"""
Free embedding alternatives for demonstrations.

Supports three free/open-source embedding providers:
1. Sentence-Transformers (local, unlimited, no API key)
2. Cohere (free tier: 100 calls/month)
3. Voyage AI (free tier: $25 credit)
"""

import os
from typing import List, Optional
import numpy as np


class FreeEmbedder:
    """
    Unified interface for free embedding providers.

    Examples:
        # Local embeddings (recommended for demo)
        embedder = FreeEmbedder(provider="local")
        embeddings = embedder.embed(["text 1", "text 2"])

        # Cohere (best quality)
        embedder = FreeEmbedder(provider="cohere", api_key="...")
        embeddings = embedder.embed(["text 1", "text 2"])

        # Voyage AI (fast & high quality)
        embedder = FreeEmbedder(provider="voyage", api_key="...")
        embeddings = embedder.embed(["text 1", "text 2"])
    """

    def __init__(
        self,
        provider: str = "local",
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize embedder.

        Args:
            provider: One of "local", "cohere", "voyage"
            model: Model name (optional, uses defaults)
            api_key: API key (optional, reads from env)
        """
        self.provider = provider.lower()
        self.model_name = model
        self.api_key = api_key

        if self.provider == "local":
            self._init_local()
        elif self.provider == "cohere":
            self._init_cohere()
        elif self.provider == "voyage":
            self._init_voyage()
        else:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Choose from: local, cohere, voyage"
            )

    def _init_local(self):
        """Initialize Sentence-Transformers (local)."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "Sentence-Transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        # Default to best small model
        if not self.model_name:
            self.model_name = "all-MiniLM-L6-v2"

        print(f"Loading local model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        self.dimensions = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded ({self.dimensions} dimensions)")

    def _init_cohere(self):
        """Initialize Cohere API."""
        try:
            import cohere
        except ImportError:
            raise ImportError(
                "Cohere not installed. "
                "Install with: pip install cohere"
            )

        # Get API key
        api_key = self.api_key or os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError(
                "COHERE_API_KEY not found. "
                "Set environment variable or pass api_key parameter"
            )

        self.client = cohere.Client(api_key)

        # Default model
        if not self.model_name:
            self.model_name = "embed-english-v3.0"

        self.dimensions = 1024
        print(f"✅ Cohere initialized ({self.dimensions} dimensions)")

    def _init_voyage(self):
        """Initialize Voyage AI."""
        try:
            import voyageai
        except ImportError:
            raise ImportError(
                "Voyage AI not installed. "
                "Install with: pip install voyageai"
            )

        # Get API key
        api_key = self.api_key or os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise ValueError(
                "VOYAGE_API_KEY not found. "
                "Set environment variable or pass api_key parameter"
            )

        self.client = voyageai.Client(api_key)

        # Default model
        if not self.model_name:
            self.model_name = "voyage-2"

        self.dimensions = 1024
        print(f"✅ Voyage AI initialized ({self.dimensions} dimensions)")

    def embed(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for texts.

        Args:
            texts: List of texts to embed
            batch_size: Batch size (provider-specific defaults used if None)
            show_progress: Show progress bar (local only)

        Returns:
            numpy array of shape (len(texts), dimensions)
        """
        if self.provider == "local":
            return self._embed_local(texts, batch_size, show_progress)
        elif self.provider == "cohere":
            return self._embed_cohere(texts, batch_size)
        elif self.provider == "voyage":
            return self._embed_voyage(texts, batch_size)

    def _embed_local(
        self,
        texts: List[str],
        batch_size: Optional[int],
        show_progress: bool
    ) -> np.ndarray:
        """Generate embeddings with Sentence-Transformers."""
        if batch_size is None:
            batch_size = 32

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )

        return embeddings

    def _embed_cohere(
        self,
        texts: List[str],
        batch_size: Optional[int]
    ) -> np.ndarray:
        """Generate embeddings with Cohere."""
        if batch_size is None:
            batch_size = 96  # Cohere's max

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            response = self.client.embed(
                texts=batch,
                model=self.model_name,
                input_type='search_document'
            )

            all_embeddings.extend(response.embeddings)

            if i + batch_size < len(texts):
                print(f"  Processed {i + batch_size}/{len(texts)}...")

        return np.array(all_embeddings)

    def _embed_voyage(
        self,
        texts: List[str],
        batch_size: Optional[int]
    ) -> np.ndarray:
        """Generate embeddings with Voyage AI."""
        if batch_size is None:
            batch_size = 128  # Voyage's recommended

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            result = self.client.embed(
                texts=batch,
                model=self.model_name
            )

            all_embeddings.extend(result.embeddings)

            if i + batch_size < len(texts):
                print(f"  Processed {i + batch_size}/{len(texts)}...")

        return np.array(all_embeddings)

    def similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1, higher = more similar)
        """
        return np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )

    def batch_similarity(
        self,
        embeddings: np.ndarray,
        threshold: float = 0.7
    ) -> List[tuple]:
        """
        Find all pairs above similarity threshold.

        Args:
            embeddings: Array of embeddings (n_texts, dimensions)
            threshold: Minimum similarity to report

        Returns:
            List of (index1, index2, similarity) tuples
        """
        from sklearn.metrics.pairwise import cosine_similarity

        # Calculate all pairwise similarities
        similarities = cosine_similarity(embeddings)

        # Find pairs above threshold (excluding diagonal)
        pairs = []
        n = len(embeddings)

        for i in range(n):
            for j in range(i + 1, n):
                sim = similarities[i, j]
                if sim >= threshold:
                    pairs.append((i, j, float(sim)))

        # Sort by similarity (highest first)
        pairs.sort(key=lambda x: x[2], reverse=True)

        return pairs

    def info(self) -> dict:
        """Get information about current configuration."""
        return {
            "provider": self.provider,
            "model": self.model_name,
            "dimensions": self.dimensions,
            "local": self.provider == "local",
            "requires_api": self.provider in ["cohere", "voyage"]
        }


# Convenience functions for quick usage

def embed_local(texts: List[str], model: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """
    Quick local embedding (recommended for demos).

    Args:
        texts: Texts to embed
        model: Sentence-Transformers model name

    Returns:
        Embeddings array
    """
    embedder = FreeEmbedder(provider="local", model=model)
    return embedder.embed(texts)


def embed_cohere(texts: List[str], api_key: Optional[str] = None) -> np.ndarray:
    """
    Quick Cohere embedding.

    Args:
        texts: Texts to embed
        api_key: Cohere API key (or use COHERE_API_KEY env var)

    Returns:
        Embeddings array
    """
    embedder = FreeEmbedder(provider="cohere", api_key=api_key)
    return embedder.embed(texts)


def embed_voyage(texts: List[str], api_key: Optional[str] = None) -> np.ndarray:
    """
    Quick Voyage AI embedding.

    Args:
        texts: Texts to embed
        api_key: Voyage API key (or use VOYAGE_API_KEY env var)

    Returns:
        Embeddings array
    """
    embedder = FreeEmbedder(provider="voyage", api_key=api_key)
    return embedder.embed(texts)


if __name__ == "__main__":
    # Quick test
    print("Testing FreeEmbedder...")
    print()

    test_texts = [
        "London Business School offers excellent MBA programmes",
        "LBS provides world-class business education",
        "The weather is nice today"
    ]

    # Test local embeddings
    print("1. Testing local embeddings (Sentence-Transformers)...")
    embedder = FreeEmbedder(provider="local")
    embeddings = embedder.embed(test_texts, show_progress=False)

    print(f"   Shape: {embeddings.shape}")
    print(f"   Similarity (MBA vs Business): {embedder.similarity(embeddings[0], embeddings[1]):.3f}")
    print(f"   Similarity (MBA vs Weather): {embedder.similarity(embeddings[0], embeddings[2]):.3f}")
    print()

    print("✅ Local embeddings work!")
