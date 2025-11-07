"""
OpenRouter LLM client - Access to 100+ models through one API.

OpenRouter provides unified access to:
- Claude models (Anthropic)
- GPT models (OpenAI)
- Llama, Mistral, and many more

Perfect for demos and production with competitive pricing.
"""

import os
from typing import List, Optional, Dict, Any
import json


class OpenRouterClient:
    """
    OpenRouter API client with OpenAI-compatible interface.

    OpenRouter uses OpenAI's API format but with access to many providers.

    Examples:
        # Use Claude
        client = OpenRouterClient(model="anthropic/claude-3.5-sonnet")
        response = client.complete("Summarize this text...")

        # Use GPT-4
        client = OpenRouterClient(model="openai/gpt-4-turbo")
        response = client.complete("Analyze sentiment...")

        # Automatic model selection
        client = OpenRouterClient(model="auto")  # Cheapest & fastest
        response = client.complete("Simple task...")
    """

    # Recommended models with pricing (per 1M tokens)
    MODELS = {
        # Claude models (Anthropic)
        "anthropic/claude-3.5-sonnet": {
            "input": 3.0,
            "output": 15.0,
            "context": 200000,
            "use_case": "Complex analysis, best quality"
        },
        "anthropic/claude-3-5-haiku-20241022": {
            "input": 0.8,
            "output": 4.0,
            "context": 200000,
            "use_case": "Fast tasks, sentiment analysis"
        },

        # OpenAI models
        "openai/gpt-4-turbo": {
            "input": 10.0,
            "output": 30.0,
            "context": 128000,
            "use_case": "Complex reasoning"
        },
        "openai/gpt-3.5-turbo": {
            "input": 0.5,
            "output": 1.5,
            "context": 16000,
            "use_case": "Simple tasks, very cheap"
        },

        # Special options
        "auto": {
            "input": 0.0,
            "output": 0.0,
            "context": None,
            "use_case": "Automatic selection (cheapest/fastest)"
        },
    }

    def __init__(
        self,
        model: str = "anthropic/claude-3-5-haiku-20241022",
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        site_url: str = "https://github.com/lbs-knowledge-graph",
        app_name: str = "LBS Knowledge Graph"
    ):
        """
        Initialize OpenRouter client.

        Args:
            model: Model name (see MODELS dict for options)
            api_key: OpenRouter API key (or use OPENROUTER_API_KEY env var)
            base_url: OpenRouter API base URL
            site_url: Your site URL (for rankings/credits)
            app_name: Your app name (for rankings)
        """
        self.model = model
        self.base_url = base_url
        self.site_url = site_url
        self.app_name = app_name

        # Get API key
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not found. "
                "Set OPENROUTER_API_KEY environment variable or pass api_key parameter"
            )

        # Initialize OpenAI client with OpenRouter endpoint
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI library required for OpenRouter. "
                "Install with: pip install openai"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers={
                "HTTP-Referer": self.site_url,
                "X-Title": self.app_name,
            }
        )

        # Track last request for cost calculation
        self.last_request_tokens = {'input': 0, 'output': 0}
        self.last_request_cost = 0.0

    def complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate completion for prompt.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            **kwargs: Additional OpenAI parameters

        Returns:
            Generated text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        # Track usage and cost
        if hasattr(response, 'usage') and response.usage:
            self.last_request_tokens = {
                'input': response.usage.prompt_tokens,
                'output': response.usage.completion_tokens
            }
            self.last_request_cost = self.estimate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
        else:
            # Fallback estimation if usage not provided
            self.last_request_tokens = {
                'input': self.count_tokens(prompt),
                'output': max_tokens // 2  # Rough estimate
            }
            self.last_request_cost = self.estimate_cost(
                self.last_request_tokens['input'],
                self.last_request_tokens['output']
            )

        return response.choices[0].message.content

    def get_last_request_cost(self) -> float:
        """Get cost of last API request."""
        return self.last_request_cost

    def batch_complete(
        self,
        prompts: List[str],
        max_tokens: int = 500,
        temperature: float = 0.7,
        show_progress: bool = True
    ) -> List[str]:
        """
        Generate completions for multiple prompts.

        Args:
            prompts: List of prompts
            max_tokens: Maximum tokens per completion
            temperature: Sampling temperature
            show_progress: Show progress

        Returns:
            List of generated texts
        """
        results = []

        for i, prompt in enumerate(prompts):
            if show_progress and i % 10 == 0:
                print(f"  Processing {i}/{len(prompts)}...")

            result = self.complete(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            results.append(result)

        return results

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        if self.model not in self.MODELS:
            # Unknown model, use average pricing
            return (input_tokens * 2.0 + output_tokens * 6.0) / 1_000_000

        model_info = self.MODELS[self.model]
        input_cost = (input_tokens / 1_000_000) * model_info["input"]
        output_cost = (output_tokens / 1_000_000) * model_info["output"]

        return input_cost + output_cost

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation).

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4

    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a model.

        Args:
            model: Model name (uses current model if None)

        Returns:
            Model information dict
        """
        model = model or self.model
        return self.MODELS.get(model, {
            "input": "Unknown",
            "output": "Unknown",
            "context": "Unknown",
            "use_case": "Custom model"
        })

    @classmethod
    def list_models(cls) -> None:
        """Print available models and pricing."""
        print("Available OpenRouter Models:")
        print("=" * 70)

        for model_name, info in cls.MODELS.items():
            if model_name == "auto":
                print(f"\n🤖 {model_name}")
            elif "claude" in model_name:
                print(f"\n🔵 {model_name}")
            elif "gpt" in model_name:
                print(f"\n🟢 {model_name}")
            else:
                print(f"\n⚪ {model_name}")

            print(f"   Input:  ${info['input']}/1M tokens")
            print(f"   Output: ${info['output']}/1M tokens")
            print(f"   Context: {info['context']} tokens" if info['context'] else "   Context: Dynamic")
            print(f"   Use: {info['use_case']}")

        print()


# Convenience function for quick usage
def complete_with_openrouter(
    prompt: str,
    model: str = "anthropic/claude-3-5-haiku-20241022",
    max_tokens: int = 500
) -> str:
    """
    Quick completion with OpenRouter.

    Args:
        prompt: Input prompt
        model: Model name
        max_tokens: Maximum tokens

    Returns:
        Generated text
    """
    client = OpenRouterClient(model=model)
    return client.complete(prompt, max_tokens=max_tokens)


if __name__ == "__main__":
    # Test and show available models
    print("OpenRouter Client Test")
    print("=" * 70)
    print()

    # Show models
    OpenRouterClient.list_models()

    # Test connection
    try:
        print("\nTesting connection...")
        client = OpenRouterClient(model="anthropic/claude-3-5-haiku-20241022")

        response = client.complete(
            "Say 'Hello from OpenRouter!' in one sentence.",
            max_tokens=50
        )

        print(f"✅ Response: {response}")
        print()
        print("✅ OpenRouter is working!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print()
        print("Make sure OPENROUTER_API_KEY is set:")
        print("  export OPENROUTER_API_KEY='sk-or-v1-...'")
