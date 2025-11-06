"""
Batch Processor for efficient LLM enrichment operations.

Handles batching, parallel processing, progress tracking, and cost monitoring.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

from .llm_client import LLMClient
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStatistics:
    """Statistics for batch processing run."""

    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_cost: float = 0.0
    batches_processed: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def items_per_second(self) -> float:
        """Calculate processing rate."""
        if self.elapsed_time == 0:
            return 0.0
        return self.processed_items / self.elapsed_time


class BatchProcessor:
    """
    Batch processor for LLM enrichment operations.

    Features:
    - Efficient batching of items for API optimization
    - Parallel processing with configurable concurrency
    - Progress tracking and reporting
    - Cost accumulation and monitoring
    - Automatic retries for failed batches
    - Result validation and quality checks
    """

    def __init__(
        self,
        llm_client: LLMClient,
        batch_size: int = 50,
        max_concurrent: int = 5,
        validation_callback: Optional[Callable[[Dict], bool]] = None
    ):
        """
        Initialize batch processor.

        Args:
            llm_client: LLM client for API calls
            batch_size: Number of items per batch
            max_concurrent: Maximum concurrent API requests
            validation_callback: Optional callback to validate results
        """
        self.llm_client = llm_client
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.validation_callback = validation_callback

        self.stats = ProcessingStatistics()
        self.prompt_templates = PromptTemplates()

    def _create_batch_prompt(
        self,
        items: List[Dict],
        template_name: str,
        **template_kwargs
    ) -> str:
        """
        Create a batched prompt from multiple items.

        Args:
            items: List of items to process
            template_name: Name of prompt template to use
            template_kwargs: Additional template parameters

        Returns:
            Formatted batch prompt
        """
        # Get template method
        template_method = getattr(self.prompt_templates, template_name)

        # Build batch prompt
        batch_prompts = []
        for idx, item in enumerate(items):
            item_prompt = template_method(
                content=item.get('content', ''),
                **template_kwargs
            )
            batch_prompts.append(f"Item {idx + 1}:\n{item_prompt}\n")

        return "\n".join(batch_prompts)

    async def process_batch(
        self,
        items: List[Dict],
        prompt_template: str,
        max_tokens: int = 500,
        **template_kwargs
    ) -> List[Dict]:
        """
        Process a batch of items through LLM.

        Args:
            items: List of items with 'content' field
            prompt_template: Name of prompt template (e.g., 'sentiment_analysis')
            max_tokens: Maximum tokens per completion
            template_kwargs: Additional parameters for prompt template

        Returns:
            List of enriched items with LLM responses
        """
        if not items:
            return []

        results = []

        # Process in batches
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]

            try:
                # Create batch prompt
                batch_prompt = self._create_batch_prompt(
                    batch,
                    prompt_template,
                    **template_kwargs
                )

                # Estimate cost
                estimated_cost = self.llm_client.estimate_cost(batch_prompt, max_tokens)
                logger.info(
                    f"Processing batch {i // self.batch_size + 1} "
                    f"({len(batch)} items, estimated cost: ${estimated_cost:.4f})"
                )

                # Get completion
                response = await self.llm_client.complete(batch_prompt, max_tokens)

                # Parse batch response
                batch_results = self._parse_batch_response(response, batch)

                # Validate results if callback provided
                if self.validation_callback:
                    batch_results = [
                        result for result in batch_results
                        if self.validation_callback(result)
                    ]

                results.extend(batch_results)
                self.stats.processed_items += len(batch_results)
                self.stats.batches_processed += 1

            except Exception as e:
                logger.error(f"Error processing batch {i // self.batch_size + 1}: {e}")
                self.stats.failed_items += len(batch)
                self.stats.errors.append({
                    'batch_index': i // self.batch_size,
                    'error': str(e),
                    'items': batch
                })

                # Add empty results for failed items
                for item in batch:
                    results.append({**item, 'error': str(e)})

        return results

    def _parse_batch_response(
        self,
        response: str,
        original_items: List[Dict]
    ) -> List[Dict]:
        """
        Parse batch response and match with original items.

        Args:
            response: LLM response text
            original_items: Original items in batch

        Returns:
            List of items enriched with LLM responses
        """
        # Split response by item markers
        import re

        item_pattern = r"Item (\d+):\s*(.*?)(?=Item \d+:|$)"
        matches = re.findall(item_pattern, response, re.DOTALL)

        results = []
        for item, (idx_str, item_response) in zip(original_items, matches):
            enriched = {
                **item,
                'llm_response': item_response.strip(),
                'processed_at': datetime.now().isoformat()
            }
            results.append(enriched)

        # If parsing failed, return items with full response
        if len(results) != len(original_items):
            logger.warning(
                f"Batch response parsing mismatch: "
                f"expected {len(original_items)}, got {len(results)}"
            )
            results = [
                {
                    **item,
                    'llm_response': response,
                    'processed_at': datetime.now().isoformat()
                }
                for item in original_items
            ]

        return results

    async def process_items_parallel(
        self,
        items: List[Dict],
        prompt_template: str,
        max_tokens: int = 500,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        **template_kwargs
    ) -> List[Dict]:
        """
        Process items in parallel with progress tracking.

        Args:
            items: List of items to process
            prompt_template: Name of prompt template
            max_tokens: Maximum tokens per completion
            progress_callback: Optional callback for progress updates (processed, total)
            template_kwargs: Additional template parameters

        Returns:
            List of enriched items
        """
        self.stats = ProcessingStatistics(
            total_items=len(items),
            start_time=datetime.now()
        )

        logger.info(f"Starting parallel processing of {len(items)} items")

        # Create batches
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]

        # Process batches with concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_with_semaphore(batch: List[Dict]) -> List[Dict]:
            async with semaphore:
                result = await self.process_batch(
                    batch,
                    prompt_template,
                    max_tokens,
                    **template_kwargs
                )

                # Progress callback
                if progress_callback:
                    progress_callback(self.stats.processed_items, self.stats.total_items)

                return result

        # Process all batches
        batch_results = await asyncio.gather(
            *[process_with_semaphore(batch) for batch in batches],
            return_exceptions=True
        )

        # Flatten results
        results = []
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                logger.error(f"Batch processing error: {batch_result}")
                continue
            results.extend(batch_result)

        self.stats.end_time = datetime.now()

        # Update cost from LLM client
        self.stats.total_cost = self.llm_client.get_statistics()['estimated_cost']

        logger.info(
            f"Processing complete: {self.stats.processed_items}/{self.stats.total_items} items "
            f"({self.stats.success_rate:.1f}% success rate) in {self.stats.elapsed_time:.1f}s. "
            f"Total cost: ${self.stats.total_cost:.2f}"
        )

        return results

    def track_cost(self) -> float:
        """
        Get total API costs for this processor.

        Returns:
            Total cost in USD
        """
        return self.llm_client.get_statistics()['estimated_cost']

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive processing statistics.

        Returns:
            Dictionary with processing statistics
        """
        return {
            'total_items': self.stats.total_items,
            'processed_items': self.stats.processed_items,
            'failed_items': self.stats.failed_items,
            'success_rate': self.stats.success_rate,
            'batches_processed': self.stats.batches_processed,
            'elapsed_time': self.stats.elapsed_time,
            'items_per_second': self.stats.items_per_second,
            'total_cost': self.stats.total_cost,
            'errors': self.stats.errors,
            'llm_statistics': self.llm_client.get_statistics()
        }

    async def retry_failed_items(self, max_retries: int = 3) -> List[Dict]:
        """
        Retry processing failed items from previous run.

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            List of successfully processed items from retries
        """
        if not self.stats.errors:
            logger.info("No failed items to retry")
            return []

        logger.info(f"Retrying {len(self.stats.errors)} failed batches")

        results = []
        for error_info in self.stats.errors:
            failed_items = error_info['items']

            for attempt in range(max_retries):
                try:
                    batch_results = await self.process_batch(
                        failed_items,
                        prompt_template='sentiment_analysis',  # Default
                        max_tokens=500
                    )
                    results.extend(batch_results)
                    logger.info(
                        f"Successfully retried batch (attempt {attempt + 1})"
                    )
                    break

                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Failed to retry batch after {max_retries} attempts: {e}"
                        )
                    else:
                        await asyncio.sleep(2 ** attempt)

        return results
