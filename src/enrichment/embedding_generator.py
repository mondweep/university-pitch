"""
Embedding Generator for Knowledge Graph Pages

Generates embeddings using OpenAI's text-embedding-ada-002 model.
Handles batching, rate limiting, and caching for efficient processing.
"""

import os
import json
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    model: str = "text-embedding-ada-002"
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    cache_dir: Optional[Path] = None
    api_key: Optional[str] = None


class EmbeddingGenerator:
    """Generate embeddings for knowledge graph pages"""

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Initialize embedding generator

        Args:
            config: Configuration for embedding generation
        """
        self.config = config or EmbeddingConfig()

        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or provide api_key in config."
            )

        if OpenAI is None:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            )

        self.client = OpenAI(api_key=api_key)

        # Setup caching
        if self.config.cache_dir:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file = self.config.cache_dir / "embeddings_cache.json"
            self.cache = self._load_cache()
        else:
            self.cache_file = None
            self.cache = {}

        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0
        }

    def _load_cache(self) -> Dict[str, List[float]]:
        """Load embeddings from cache file"""
        if self.cache_file and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return {}

    def _save_cache(self):
        """Save embeddings to cache file"""
        if self.cache_file:
            try:
                with open(self.cache_file, 'w') as f:
                    json.dump(self.cache, f)
            except Exception as e:
                logger.warning(f"Failed to save cache: {e}")

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()

    def _create_embedding_text(self, page: Dict) -> str:
        """
        Create text representation of page for embedding

        Args:
            page: Page node data

        Returns:
            Text representation combining key fields
        """
        data = page.get("data", {})

        # Combine relevant fields
        parts = []

        if "title" in data:
            parts.append(f"Title: {data['title']}")

        if "description" in data:
            parts.append(f"Description: {data['description']}")

        if "type" in data:
            parts.append(f"Type: {data['type']}")

        # Add topics if available
        topics = data.get("topics", [])
        if topics:
            parts.append(f"Topics: {', '.join(topics)}")

        # Add personas if available
        personas = data.get("personas", [])
        if personas:
            persona_names = [p.get("name", "") for p in personas if isinstance(p, dict)]
            if persona_names:
                parts.append(f"Personas: {', '.join(persona_names)}")

        return " | ".join(parts)

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if failed
        """
        self.stats["total_requests"] += 1

        # Check cache
        cache_key = self._get_cache_key(text)
        if cache_key in self.cache:
            self.stats["cache_hits"] += 1
            return self.cache[cache_key]

        # Generate embedding with retries
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.config.model,
                    input=text
                )

                embedding = response.data[0].embedding

                # Update stats
                self.stats["api_calls"] += 1
                self.stats["total_tokens"] += response.usage.total_tokens
                # text-embedding-ada-002 costs $0.0001 per 1K tokens
                self.stats["estimated_cost"] += (response.usage.total_tokens / 1000) * 0.0001

                # Cache result
                self.cache[cache_key] = embedding
                self._save_cache()

                return embedding

            except Exception as e:
                logger.warning(f"Embedding generation attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Failed to generate embedding after {self.config.max_retries} attempts")
                    return None

        return None

    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (None for failed embeddings)
        """
        embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            logger.info(f"Processing batch {i // self.config.batch_size + 1} "
                       f"({len(batch)} texts)")

            for text in batch:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)

            # Rate limiting delay between batches
            if i + self.config.batch_size < len(texts):
                time.sleep(0.1)

        return embeddings

    def generate_page_embeddings(self, pages: List[Dict]) -> Dict[str, List[float]]:
        """
        Generate embeddings for all pages in graph

        Args:
            pages: List of page nodes from graph

        Returns:
            Dictionary mapping page_id to embedding vector
        """
        logger.info(f"Generating embeddings for {len(pages)} pages")

        # Create texts for all pages
        page_texts = []
        page_ids = []

        for page in pages:
            if page.get("node_type") == "Page":
                text = self._create_embedding_text(page)
                page_texts.append(text)
                page_ids.append(page.get("id"))

        # Generate embeddings
        embeddings = self.generate_embeddings_batch(page_texts)

        # Create result dictionary
        result = {}
        for page_id, embedding in zip(page_ids, embeddings):
            if embedding is not None:
                result[page_id] = embedding

        logger.info(f"Generated {len(result)} embeddings successfully")
        logger.info(f"Stats: {self.get_stats()}")

        return result

    def get_stats(self) -> Dict:
        """Get generation statistics"""
        stats = self.stats.copy()
        stats["cache_hit_rate"] = (
            self.stats["cache_hits"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0
            else 0.0
        )
        return stats


def main():
    """Test embedding generation"""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Sample test data
    test_pages = [
        {
            "id": "test_page_1",
            "node_type": "Page",
            "data": {
                "title": "MBA Programme",
                "description": "Learn about our world-class MBA programme",
                "type": "programme",
                "topics": ["mba", "education", "leadership"]
            }
        },
        {
            "id": "test_page_2",
            "node_type": "Page",
            "data": {
                "title": "Executive Education",
                "description": "Executive development programmes for leaders",
                "type": "programme",
                "topics": ["executive", "leadership", "development"]
            }
        }
    ]

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not set. Please set it to test embedding generation.")
        sys.exit(1)

    # Create generator
    config = EmbeddingConfig(
        cache_dir=Path(".cache/embeddings")
    )
    generator = EmbeddingGenerator(config)

    # Generate embeddings
    embeddings = generator.generate_page_embeddings(test_pages)

    # Print results
    print("\nEmbedding Generation Results:")
    print(f"Pages processed: {len(test_pages)}")
    print(f"Embeddings generated: {len(embeddings)}")
    print(f"\nStats: {json.dumps(generator.get_stats(), indent=2)}")

    # Show sample embedding
    if embeddings:
        sample_id = list(embeddings.keys())[0]
        sample_embedding = embeddings[sample_id]
        print(f"\nSample embedding for {sample_id}:")
        print(f"Dimensions: {len(sample_embedding)}")
        print(f"First 5 values: {sample_embedding[:5]}")


if __name__ == "__main__":
    main()
