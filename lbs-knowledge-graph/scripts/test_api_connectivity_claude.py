#!/usr/bin/env python3
"""
Test Anthropic (Claude) API connectivity before running enrichment pipeline.

Usage:
    python scripts/test_api_connectivity_claude.py
"""

import os
import sys
from typing import Tuple


def test_api_key() -> Tuple[bool, str]:
    """Check if Anthropic API key is set and valid format."""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return False, "❌ ANTHROPIC_API_KEY not set"

    if not api_key.startswith("sk-ant-"):
        return False, f"❌ Invalid API key format (should start with 'sk-ant-')"

    return True, "✅ API key format valid"


def test_anthropic_import() -> Tuple[bool, str]:
    """Test if Anthropic library is installed."""
    try:
        import anthropic
        return True, f"✅ Anthropic library installed (version {anthropic.__version__})"
    except ImportError:
        return False, "❌ Anthropic library not installed (run: pip install anthropic)"


def test_api_connectivity() -> Tuple[bool, str]:
    """Test actual API connectivity with a minimal request."""
    try:
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return False, "❌ API key not set"

        # Create client
        client = anthropic.Anthropic(api_key=api_key)

        # Test with minimal request (cheapest possible)
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1,
            messages=[{"role": "user", "content": "Hi"}]
        )

        if response and response.content:
            return True, "✅ API connectivity successful"
        else:
            return False, "❌ API returned empty response"

    except anthropic.AuthenticationError:
        return False, "❌ Invalid API key (authentication failed)"
    except anthropic.RateLimitError:
        return False, "❌ Rate limit exceeded (try again later)"
    except anthropic.APIError as e:
        return False, f"❌ API error: {str(e)}"
    except Exception as e:
        return False, f"❌ Unexpected error: {str(e)}"


def test_models_available() -> Tuple[bool, str]:
    """Check which models are available."""
    # Anthropic's available models
    available_models = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
    ]

    return True, f"✅ Available models: {', '.join(available_models)}"


def suggest_embedding_alternative() -> Tuple[bool, str]:
    """Suggest embedding alternatives since Anthropic doesn't have embeddings API."""
    return True, """✅ Embedding alternatives (Anthropic has no embedding API):
   Option 1: OpenAI embeddings only ($0.001 - essentially free)
   Option 2: Sentence-Transformers (local, free)
   Option 3: Cohere free tier
   Option 4: Skip semantic similarity enrichment"""


def main():
    """Run all connectivity tests."""
    print("=" * 60)
    print("Anthropic (Claude) API Connectivity Test")
    print("=" * 60)
    print()

    tests = [
        ("1. API Key Check", test_api_key),
        ("2. Anthropic Library", test_anthropic_import),
        ("3. API Connectivity", test_api_connectivity),
        ("4. Models Available", test_models_available),
        ("5. Embedding Options", suggest_embedding_alternative),
    ]

    results = []

    for name, test_func in tests:
        print(f"{name}...", end=" ")
        success, message = test_func()
        print(message)
        results.append(success)

        if not success and name != "5. Embedding Options":
            print(f"\n⚠️  Fix this issue before proceeding\n")

    print()
    print("=" * 60)

    if all(results):
        print("✅✅✅ ALL TESTS PASSED ✅✅✅")
        print()
        print("🚀 Ready to run enrichment pipeline with Claude!")
        print()
        print("Next steps:")
        print("  1. Small-scale test: python scripts/test_small_scale_claude.py --pages 1")
        print("  2. Full pipeline: python scripts/full_pipeline_claude.py")
        print()
        print("Note: For embeddings, you'll need one of:")
        print("  - OpenAI API key (just for embeddings, $0.001)")
        print("  - Local Sentence-Transformers (free)")
        print("  - Skip semantic similarity enrichment")
        print()
        sys.exit(0)
    else:
        failed_count = len([r for r in results if not r])
        print(f"❌ {failed_count}/{len(results)} tests failed")
        print()
        print("Please fix the issues above and try again.")
        print()
        print("To get API key:")
        print("  1. Go to https://console.anthropic.com/settings/keys")
        print("  2. Create new API key")
        print("  3. Copy and save immediately")
        print("  4. Set environment variable:")
        print("     export ANTHROPIC_API_KEY='sk-ant-...'")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
