"""
Batch processor for efficient LLM-based enrichment tasks.

Optimizations:
- Batches items into groups for single API calls
- Parallel processing with asyncio
- Progress tracking
- Error handling and retry
- Results caching
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Callable
from tqdm.asyncio import tqdm as async_tqdm
from datetime import datetime

from .llm_client import LLMClient
from .prompts import (
    SENTIMENT_BATCH_PROMPT,
    TOPIC_BATCH_PROMPT,
    PERSONA_BATCH_PROMPT,
    NER_BATCH_PROMPT,
    JOURNEY_BATCH_PROMPT,
    format_batch_prompt
)
from .response_parser import ResponseParser


class BatchProcessor:
    """
    Processes large datasets through LLM with batching and parallelization.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        batch_size: int = 50,
        max_concurrent: int = 5,
        cache_results: bool = True
    ):
        """
        Initialize batch processor.

        Args:
            llm_client: LLM client instance
            batch_size: Items per batch (per API call)
            max_concurrent: Maximum concurrent API requests
            cache_results: Whether to cache results
        """
        self.llm_client = llm_client
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.cache_results = cache_results

        self.response_parser = ResponseParser()

        # Results cache
        self.results_cache: Dict[str, Any] = {}

        # Processing stats
        self.stats = {
            "total_items": 0,
            "processed_items": 0,
            "failed_items": 0,
            "batches_processed": 0,
            "cache_hits": 0,
            "start_time": None,
            "end_time": None
        }

    async def process_items(
        self,
        items: List[Dict],
        task_type: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
        **kwargs
    ) -> List[Dict]:
        """
        Process items in optimized batches.

        Args:
            items: List of items to process
            task_type: Type of enrichment task
            max_tokens: Maximum tokens per response
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            List of enriched results
        """
        self.stats["start_time"] = datetime.now()
        self.stats["total_items"] = len(items)

        # Split into batches
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]

        print(f"Processing {len(items)} items in {len(batches)} batches...")

        # Process batches with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_batch_with_limit(batch, batch_idx):
            async with semaphore:
                return await self._process_batch(
                    batch,
                    batch_idx,
                    task_type,
                    max_tokens,
                    temperature,
                    **kwargs
                )

        # Process all batches with progress tracking
        results = []
        for idx, batch in enumerate(batches):
            print(f"Processing batch {idx+1}/{len(batches)}...")
            batch_results = await process_batch_with_limit(batch, idx)
            results.extend(batch_results)

        self.stats["end_time"] = datetime.now()
        self.stats["processed_items"] = len([r for r in results if not r.get("error")])
        self.stats["failed_items"] = len([r for r in results if r.get("error")])

        return results

    async def _process_batch(
        self,
        batch: List[Dict],
        batch_idx: int,
        task_type: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> List[Dict]:
        """
        Process single batch of items.

        Args:
            batch: Batch of items
            batch_idx: Batch index for tracking
            task_type: Type of enrichment task
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            List of results for batch items
        """
        try:
            # Create batch prompt
            prompt = self._create_batch_prompt(batch, task_type)

            # Check cache
            if self.cache_results:
                cache_key = f"{task_type}:{batch_idx}"
                if cache_key in self.results_cache:
                    self.stats["cache_hits"] += 1
                    return self.results_cache[cache_key]

            # Make LLM request
            response = await self.llm_client.complete(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            # Parse response
            results = self._parse_batch_response(
                response["content"],
                batch,
                task_type
            )

            # Update cache
            if self.cache_results:
                self.results_cache[cache_key] = results

            self.stats["batches_processed"] += 1

            return results

        except Exception as e:
            print(f"Error processing batch {batch_idx}: {str(e)}")
            # Return error results for each item
            return [
                {
                    "id": item.get("id", f"item_{i}"),
                    "error": str(e),
                    "success": False
                }
                for i, item in enumerate(batch)
            ]

    def _create_batch_prompt(self, batch: List[Dict], task_type: str) -> str:
        """
        Create prompt for batch of items.

        Args:
            batch: Batch of items
            task_type: Type of enrichment task

        Returns:
            Formatted prompt string
        """
        # Map task type to prompt template
        prompt_map = {
            "sentiment": SENTIMENT_BATCH_PROMPT,
            "topics": TOPIC_BATCH_PROMPT,
            "personas": PERSONA_BATCH_PROMPT,
            "ner": NER_BATCH_PROMPT,
            "entities": NER_BATCH_PROMPT,
            "journey": JOURNEY_BATCH_PROMPT,
            "journey_stages": JOURNEY_BATCH_PROMPT
        }

        if task_type not in prompt_map:
            raise ValueError(f"Unsupported task type: {task_type}")

        template = prompt_map[task_type]
        return format_batch_prompt(template, batch, self.batch_size)

    def _parse_batch_response(
        self,
        response_text: str,
        batch: List[Dict],
        task_type: str
    ) -> List[Dict]:
        """
        Parse batch response into individual results.

        Args:
            response_text: LLM response text
            batch: Original batch items
            task_type: Type of enrichment task

        Returns:
            List of parsed results
        """
        try:
            # Parse JSON response
            parsed = self.response_parser.parse_json_response(response_text)

            if not isinstance(parsed, list):
                raise ValueError("Expected JSON array response")

            # Validate response structure
            validated = self.response_parser.validate_batch_response(
                parsed,
                task_type,
                len(batch)
            )

            # Match results to original items
            results = []
            for item, result in zip(batch, validated):
                results.append({
                    **result,
                    "original_id": item.get("id"),
                    "success": True
                })

            # Handle cases where response length doesn't match batch
            if len(validated) < len(batch):
                for i in range(len(validated), len(batch)):
                    results.append({
                        "id": batch[i].get("id"),
                        "error": "Missing result in batch response",
                        "success": False
                    })

            return results

        except Exception as e:
            print(f"Error parsing batch response: {str(e)}")
            print(f"Response text: {response_text[:500]}...")

            # Return error results
            return [
                {
                    "id": item.get("id", f"item_{i}"),
                    "error": f"Parse error: {str(e)}",
                    "success": False
                }
                for i, item in enumerate(batch)
            ]

    def get_stats(self) -> Dict:
        """Get processing statistics."""
        stats = self.stats.copy()

        if stats["start_time"] and stats["end_time"]:
            duration = (stats["end_time"] - stats["start_time"]).total_seconds()
            stats["duration_seconds"] = duration
            stats["items_per_second"] = stats["processed_items"] / duration if duration > 0 else 0

        stats["success_rate"] = (
            stats["processed_items"] / max(stats["total_items"], 1)
        ) * 100

        return stats

    def reset_stats(self):
        """Reset processing statistics."""
        self.stats = {
            "total_items": 0,
            "processed_items": 0,
            "failed_items": 0,
            "batches_processed": 0,
            "cache_hits": 0,
            "start_time": None,
            "end_time": None
        }

    def clear_cache(self):
        """Clear results cache."""
        self.results_cache.clear()


async def process_with_progress(
    items: List[Dict],
    processor: BatchProcessor,
    task_type: str,
    description: str = "Processing"
) -> List[Dict]:
    """
    Convenience function to process items with progress bar.

    Args:
        items: Items to process
        processor: BatchProcessor instance
        task_type: Type of enrichment task
        description: Progress bar description

    Returns:
        List of results
    """
    print(f"\n{description}...")
    results = await processor.process_items(items, task_type)

    # Print summary
    stats = processor.get_stats()
    print(f"\nCompleted: {stats['processed_items']}/{stats['total_items']} items")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Failed: {stats['failed_items']} items")
    if stats.get('duration_seconds'):
        print(f"Duration: {stats['duration_seconds']:.1f}s")
        print(f"Speed: {stats['items_per_second']:.1f} items/sec")

    return results
