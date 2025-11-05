"""
Embedding Generator for Knowledge Graph Content
Generates embeddings for pages and sections using OpenAI embeddings API.
"""

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tiktoken
import openai
from openai import AsyncOpenAI


logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate and cache embeddings for text content."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize embedding generator.

        Args:
            api_key: OpenAI API key
            model: Embedding model name (default: text-embedding-3-small)
            cache_dir: Directory to cache embeddings
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.cache_dir = cache_dir or Path(".cache/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize tokenizer for text-embedding-3-small
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = 8000  # Safe limit below 8191

        logger.info(f"Initialized EmbeddingGenerator with model: {model}")

    def _get_cache_path(self, text: str) -> Path:
        """Get cache file path for text."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return self.cache_dir / f"{text_hash}.json"

    def _load_from_cache(self, text: str) -> Optional[List[float]]:
        """Load embedding from cache if available."""
        cache_path = self._get_cache_path(text)
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                data = json.load(f)
                logger.debug(f"Loaded embedding from cache: {cache_path.name}")
                return data['embedding']
        return None

    def _save_to_cache(self, text: str, embedding: List[float]) -> None:
        """Save embedding to cache."""
        cache_path = self._get_cache_path(text)
        with open(cache_path, 'w') as f:
            json.dump({
                'text': text[:200],  # Save first 200 chars for reference
                'model': self.model,
                'embedding': embedding
            }, f)
        logger.debug(f"Saved embedding to cache: {cache_path.name}")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def chunk_text(self, text: str, max_tokens: int = 8000) -> List[str]:
        """
        Split text into chunks that fit within token limit.

        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk

        Returns:
            List of text chunks
        """
        tokens = self.encoding.encode(text)

        if len(tokens) <= max_tokens:
            return [text]

        chunks = []
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

        logger.info(f"Split text into {len(chunks)} chunks ({len(tokens)} tokens)")
        return chunks

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Check cache first
        cached = self._load_from_cache(text)
        if cached is not None:
            return cached

        # Check token count
        token_count = self.count_tokens(text)
        if token_count > self.max_tokens:
            logger.warning(f"Text exceeds {self.max_tokens} tokens ({token_count}), chunking...")
            chunks = self.chunk_text(text, self.max_tokens)
            # Average embeddings from chunks
            chunk_embeddings = await self.generate_batch(chunks)
            embedding = [sum(values) / len(values) for values in zip(*chunk_embeddings)]
        else:
            # Generate embedding
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=text
                )
                embedding = response.data[0].embedding
                logger.debug(f"Generated embedding ({token_count} tokens)")
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                raise

        # Cache result
        self._save_to_cache(text, embedding)

        return embedding

    async def generate_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Check cache for each text
            batch_embeddings = []
            texts_to_generate = []
            cached_indices = []

            for idx, text in enumerate(batch):
                cached = self._load_from_cache(text)
                if cached is not None:
                    batch_embeddings.append((idx, cached))
                    cached_indices.append(idx)
                else:
                    texts_to_generate.append((idx, text))

            # Generate embeddings for uncached texts
            if texts_to_generate:
                try:
                    response = await self.client.embeddings.create(
                        model=self.model,
                        input=[text for _, text in texts_to_generate]
                    )

                    for (idx, text), embedding_obj in zip(texts_to_generate, response.data):
                        embedding = embedding_obj.embedding
                        batch_embeddings.append((idx, embedding))
                        self._save_to_cache(text, embedding)

                    logger.info(f"Generated {len(texts_to_generate)} embeddings (batch {i // batch_size + 1})")

                except Exception as e:
                    logger.error(f"Error in batch embedding generation: {e}")
                    raise

            # Sort by original index and extract embeddings
            batch_embeddings.sort(key=lambda x: x[0])
            embeddings.extend([emb for _, emb in batch_embeddings])

        logger.info(f"Generated total {len(embeddings)} embeddings ({len([e for e in embeddings if e])} from API, {len(texts) - len([e for e in embeddings if e])} from cache)")

        return embeddings

    def save_embeddings(
        self,
        embeddings: Dict[str, List[float]],
        path: Path
    ) -> None:
        """
        Save embeddings dictionary to file.

        Args:
            embeddings: Dictionary mapping IDs to embeddings
            path: Output file path
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump({
                'model': self.model,
                'count': len(embeddings),
                'embeddings': embeddings
            }, f, indent=2)

        logger.info(f"Saved {len(embeddings)} embeddings to {path}")

    def load_embeddings(self, path: Path) -> Dict[str, List[float]]:
        """
        Load embeddings from file.

        Args:
            path: Input file path

        Returns:
            Dictionary mapping IDs to embeddings
        """
        with open(path, 'r') as f:
            data = json.load(f)

        logger.info(f"Loaded {data.get('count', 0)} embeddings from {path}")

        return data.get('embeddings', {})

    async def close(self):
        """Close the OpenAI client."""
        await self.client.close()
