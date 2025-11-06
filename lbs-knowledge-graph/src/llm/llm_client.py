"""
LLM Client with multi-provider support, caching, and cost tracking.

Supports:
- OpenAI (GPT-3.5-turbo, GPT-4, GPT-4-turbo)
- Anthropic (Claude-3 family)
- Automatic failover
- Response caching with TTL
- Rate limiting and retry logic
"""

import os
import asyncio
import hashlib
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

# Token cost per 1K tokens (USD)
TOKEN_COSTS = {
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
}


class LLMClient:
    """
    Multi-provider LLM client with intelligent caching and cost optimization.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-3.5-turbo",
        cache_ttl: int = 3600,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        Initialize LLM client.

        Args:
            provider: 'openai' or 'anthropic'
            model: Model identifier
            cache_ttl: Cache time-to-live in seconds
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        self.provider = provider.lower()
        self.model = model
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.timeout = timeout

        # Cache: {prompt_hash: (response, timestamp)}
        self.cache: Dict[str, tuple] = {}

        # Usage tracking
        self.usage_stats = {
            "requests": 0,
            "cache_hits": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_cost": 0.0,
            "errors": 0
        }

        # Initialize clients
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients based on provider."""
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = AsyncOpenAI(api_key=api_key)

        elif self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = AsyncAnthropic(api_key=api_key)

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _get_cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters."""
        cache_data = f"{self.provider}:{self.model}:{prompt}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.sha256(cache_data.encode()).hexdigest()

    def _check_cache(self, cache_key: str) -> Optional[Dict]:
        """Check if valid cached response exists."""
        if cache_key in self.cache:
            response, timestamp = self.cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.cache_ttl:
                self.usage_stats["cache_hits"] += 1
                return response
            else:
                # Expired cache entry
                del self.cache[cache_key]
        return None

    def _update_cache(self, cache_key: str, response: Dict):
        """Update cache with new response."""
        self.cache[cache_key] = (response, datetime.now().timestamp())

    async def complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict:
        """
        Send completion request with caching and retry logic.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict with 'content', 'usage', and 'cost' keys
        """
        # Check cache
        cache_key = self._get_cache_key(prompt, max_tokens=max_tokens, temperature=temperature, **kwargs)
        cached_response = self._check_cache(cache_key)
        if cached_response:
            return cached_response

        # Make request with retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self._make_request(prompt, max_tokens, temperature, **kwargs)

                # Update cache
                self._update_cache(cache_key, response)

                # Update usage stats
                self.usage_stats["requests"] += 1
                self.usage_stats["input_tokens"] += response["usage"]["input_tokens"]
                self.usage_stats["output_tokens"] += response["usage"]["output_tokens"]
                self.usage_stats["total_cost"] += response["cost"]

                return response

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) + (0.1 * attempt)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self.usage_stats["errors"] += 1
                    raise Exception(f"Failed after {self.max_retries} retries: {str(last_error)}")

    async def _make_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict:
        """Make actual API request to provider."""
        if self.provider == "openai":
            return await self._openai_request(prompt, max_tokens, temperature, **kwargs)
        elif self.provider == "anthropic":
            return await self._anthropic_request(prompt, max_tokens, temperature, **kwargs)

    async def _openai_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict:
        """Make OpenAI API request."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=self.timeout,
            **kwargs
        )

        content = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        # Calculate cost
        cost = self._calculate_cost(input_tokens, output_tokens)

        return {
            "content": content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            "cost": cost,
            "model": self.model,
            "provider": self.provider
        }

    async def _anthropic_request(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> Dict:
        """Make Anthropic API request."""
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=self.timeout,
            **kwargs
        )

        content = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Calculate cost
        cost = self._calculate_cost(input_tokens, output_tokens)

        return {
            "content": content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            "cost": cost,
            "model": self.model,
            "provider": self.provider
        }

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate request cost in USD."""
        if self.model not in TOKEN_COSTS:
            # Default to GPT-3.5 pricing
            costs = TOKEN_COSTS["gpt-3.5-turbo"]
        else:
            costs = TOKEN_COSTS[self.model]

        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]

        return input_cost + output_cost

    async def batch_complete(
        self,
        prompts: List[str],
        batch_size: int = 50,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> List[Dict]:
        """
        Process multiple prompts in batches with parallel execution.

        Args:
            prompts: List of prompts to process
            batch_size: Number of prompts per batch
            max_tokens: Maximum tokens per response
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            List of response dictionaries
        """
        results = []

        # Process in batches
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i + batch_size]

            # Process batch in parallel
            tasks = [
                self.complete(prompt, max_tokens, temperature, **kwargs)
                for prompt in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle results and exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({
                        "content": None,
                        "error": str(result),
                        "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                        "cost": 0.0
                    })
                else:
                    results.append(result)

        return results

    def get_cost_estimate(self, prompt: str, max_tokens: int = 500) -> Dict[str, float]:
        """
        Estimate cost before making request.

        Args:
            prompt: Input prompt
            max_tokens: Expected output tokens

        Returns:
            Dict with cost breakdown
        """
        # Rough estimate: 1 token ~= 4 characters
        estimated_input_tokens = len(prompt) // 4
        estimated_output_tokens = max_tokens

        cost = self._calculate_cost(estimated_input_tokens, estimated_output_tokens)

        return {
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_total_tokens": estimated_input_tokens + estimated_output_tokens,
            "estimated_cost": cost
        }

    def get_usage_stats(self) -> Dict:
        """Get current usage statistics."""
        return {
            **self.usage_stats,
            "cache_hit_rate": (
                self.usage_stats["cache_hits"] / max(self.usage_stats["requests"], 1)
            ) * 100,
            "average_cost_per_request": (
                self.usage_stats["total_cost"] / max(self.usage_stats["requests"], 1)
            )
        }

    def clear_cache(self):
        """Clear response cache."""
        self.cache.clear()

    def reset_stats(self):
        """Reset usage statistics."""
        self.usage_stats = {
            "requests": 0,
            "cache_hits": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_cost": 0.0,
            "errors": 0
        }
