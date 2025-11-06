"""
Tests for LLM Client with multi-provider support, caching, and cost tracking.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lbs-knowledge-graph'))

from src.llm.llm_client import LLMClient, TOKEN_COSTS


class TestLLMClientInitialization:
    """Test LLM client initialization and configuration."""

    def test_client_initialization_openai(self):
        """Test OpenAI client initialization."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(provider="openai", model="gpt-3.5-turbo")
            assert client.provider == "openai"
            assert client.model == "gpt-3.5-turbo"
            assert client.cache_ttl == 3600
            assert client.max_retries == 3

    def test_client_initialization_anthropic(self):
        """Test Anthropic client initialization."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            client = LLMClient(provider="anthropic", model="claude-3-sonnet")
            assert client.provider == "anthropic"
            assert client.model == "claude-3-sonnet"

    def test_client_missing_api_key(self):
        """Test error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API_KEY environment variable not set"):
                LLMClient(provider="openai")

    def test_client_unsupported_provider(self):
        """Test error for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClient(provider="invalid-provider")

    def test_custom_configuration(self):
        """Test custom cache TTL, retries, timeout."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(
                provider="openai",
                cache_ttl=7200,
                max_retries=5,
                timeout=120
            )
            assert client.cache_ttl == 7200
            assert client.max_retries == 5
            assert client.timeout == 120


class TestCaching:
    """Test response caching functionality."""

    @pytest.fixture
    def client(self):
        """Create client instance for testing."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            return LLMClient(provider="openai", cache_ttl=60)

    def test_cache_key_generation(self, client):
        """Test cache key generation from prompt."""
        key1 = client._get_cache_key("test prompt", max_tokens=100)
        key2 = client._get_cache_key("test prompt", max_tokens=100)
        key3 = client._get_cache_key("different prompt", max_tokens=100)

        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different inputs = different keys

    def test_cache_update_and_retrieval(self, client):
        """Test caching and retrieving responses."""
        cache_key = "test-key"
        response = {
            "content": "test response",
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "cost": 0.001
        }

        client._update_cache(cache_key, response)
        cached = client._check_cache(cache_key)

        assert cached == response
        assert client.usage_stats["cache_hits"] == 1

    def test_cache_expiration(self, client):
        """Test cache expiration after TTL."""
        client.cache_ttl = 0  # Expire immediately
        cache_key = "test-key"
        response = {"content": "test"}

        client._update_cache(cache_key, response)
        cached = client._check_cache(cache_key)

        assert cached is None  # Should be expired

    def test_cache_clear(self, client):
        """Test clearing cache."""
        client.cache["key1"] = ({"content": "test1"}, datetime.now().timestamp())
        client.cache["key2"] = ({"content": "test2"}, datetime.now().timestamp())

        client.clear_cache()
        assert len(client.cache) == 0


class TestCostCalculation:
    """Test token usage and cost calculations."""

    @pytest.fixture
    def client(self):
        """Create client instance."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            return LLMClient(provider="openai", model="gpt-3.5-turbo")

    def test_cost_calculation_gpt35(self, client):
        """Test cost calculation for GPT-3.5."""
        cost = client._calculate_cost(input_tokens=1000, output_tokens=500)
        expected = (1000/1000 * 0.0005) + (500/1000 * 0.0015)
        assert pytest.approx(cost, 0.0001) == expected

    def test_cost_calculation_gpt4(self):
        """Test cost calculation for GPT-4."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(provider="openai", model="gpt-4")
            cost = client._calculate_cost(input_tokens=1000, output_tokens=500)
            expected = (1000/1000 * 0.03) + (500/1000 * 0.06)
            assert pytest.approx(cost, 0.001) == expected

    def test_cost_estimate(self, client):
        """Test cost estimation before request."""
        estimate = client.get_cost_estimate("This is a test prompt", max_tokens=100)

        assert "estimated_input_tokens" in estimate
        assert "estimated_output_tokens" in estimate
        assert "estimated_cost" in estimate
        assert estimate["estimated_output_tokens"] == 100


class TestCompletionRequests:
    """Test completion request handling."""

    @pytest.fixture
    def client(self):
        """Create client with mocked API."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(provider="openai")
            # Mock the AsyncOpenAI client
            client.client = AsyncMock()
            return client

    @pytest.mark.asyncio
    async def test_successful_completion(self, client):
        """Test successful completion request."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await client.complete("test prompt", max_tokens=100)

        assert result["content"] == "Test response"
        assert result["usage"]["input_tokens"] == 10
        assert result["usage"]["output_tokens"] == 5
        assert "cost" in result
        assert client.usage_stats["requests"] == 1

    @pytest.mark.asyncio
    async def test_completion_with_retry(self, client):
        """Test retry logic on failure."""
        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Success"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        client.client.chat.completions.create = AsyncMock(
            side_effect=[Exception("API Error"), mock_response]
        )

        result = await client.complete("test prompt")
        assert result["content"] == "Success"

    @pytest.mark.asyncio
    async def test_completion_max_retries_exceeded(self, client):
        """Test failure after max retries."""
        client.max_retries = 2
        client.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Persistent error")
        )

        with pytest.raises(Exception, match="Failed after 2 retries"):
            await client.complete("test prompt")

    @pytest.mark.asyncio
    async def test_batch_completion(self, client):
        """Test batch processing of prompts."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        client.client.chat.completions.create = AsyncMock(return_value=mock_response)

        prompts = ["prompt1", "prompt2", "prompt3"]
        results = await client.batch_complete(prompts, batch_size=2)

        assert len(results) == 3
        assert all("content" in r for r in results)


class TestUsageStatistics:
    """Test usage statistics tracking."""

    @pytest.fixture
    def client(self):
        """Create client instance."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            return LLMClient(provider="openai")

    def test_initial_stats(self, client):
        """Test initial statistics are zero."""
        stats = client.get_usage_stats()
        assert stats["requests"] == 0
        assert stats["cache_hits"] == 0
        assert stats["total_cost"] == 0.0

    def test_stats_after_requests(self, client):
        """Test statistics update after requests."""
        client.usage_stats["requests"] = 10
        client.usage_stats["cache_hits"] = 3
        client.usage_stats["total_cost"] = 0.05

        stats = client.get_usage_stats()
        assert stats["cache_hit_rate"] == 30.0
        assert stats["average_cost_per_request"] == 0.005

    def test_reset_stats(self, client):
        """Test resetting statistics."""
        client.usage_stats["requests"] = 10
        client.usage_stats["total_cost"] = 1.0

        client.reset_stats()
        stats = client.get_usage_stats()
        assert stats["requests"] == 0
        assert stats["total_cost"] == 0.0


class TestProviderSpecificBehavior:
    """Test provider-specific functionality."""

    @pytest.mark.asyncio
    async def test_openai_request_format(self):
        """Test OpenAI-specific request format."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(provider="openai")
            client.client = AsyncMock()

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5

            client.client.chat.completions.create = AsyncMock(return_value=mock_response)

            await client.complete("test", max_tokens=100, temperature=0.7)

            # Verify call format
            call_args = client.client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-3.5-turbo"
            assert call_args[1]["messages"][0]["role"] == "user"
            assert call_args[1]["max_tokens"] == 100
            assert call_args[1]["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_anthropic_request_format(self):
        """Test Anthropic-specific request format."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            client = LLMClient(provider="anthropic", model="claude-3-sonnet")
            client.client = AsyncMock()

            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = "Response"
            mock_response.usage.input_tokens = 10
            mock_response.usage.output_tokens = 5

            client.client.messages.create = AsyncMock(return_value=mock_response)

            await client.complete("test", max_tokens=100)

            # Verify call format
            call_args = client.client.messages.create.call_args
            assert call_args[1]["model"] == "claude-3-sonnet"
            assert call_args[1]["max_tokens"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
