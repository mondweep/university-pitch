#!/usr/bin/env python3
"""
Test OpenAI API connectivity before running full enrichment pipeline.

Usage:
    python scripts/test_api_connectivity.py
"""

import os
import sys
from typing import Tuple


def test_api_key() -> Tuple[bool, str]:
    """Check if API key is set and valid format."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return False, "❌ OPENAI_API_KEY not set"

    if not api_key.startswith("sk-"):
        return False, f"❌ Invalid API key format (should start with 'sk-')"

    return True, "✅ API key format valid"


def test_openai_import() -> Tuple[bool, str]:
    """Test if OpenAI library is installed."""
    try:
        import openai
        return True, f"✅ OpenAI library installed (version {openai.__version__})"
    except ImportError:
        return False, "❌ OpenAI library not installed (run: pip install openai)"


def test_api_connectivity() -> Tuple[bool, str]:
    """Test actual API connectivity with a minimal request."""
    try:
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False, "❌ API key not set"

        # Set API key
        openai.api_key = api_key

        # Test with minimal request (cheapest possible)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1,
            temperature=0
        )

        if response and response.choices:
            return True, "✅ API connectivity successful"
        else:
            return False, "❌ API returned empty response"

    except openai.error.AuthenticationError:
        return False, "❌ Invalid API key (authentication failed)"
    except openai.error.RateLimitError:
        return False, "❌ Rate limit exceeded (try again later)"
    except openai.error.APIError as e:
        return False, f"❌ API error: {str(e)}"
    except Exception as e:
        return False, f"❌ Unexpected error: {str(e)}"


def test_models_available() -> Tuple[bool, str]:
    """Check which models are available."""
    try:
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False, "❌ API key not set"

        openai.api_key = api_key

        # Get available models
        models = openai.Model.list()

        # Check for required models
        required_models = [
            "gpt-3.5-turbo",
            "gpt-4-turbo",
            "text-embedding-ada-002"
        ]

        available = []
        missing = []

        for model_id in required_models:
            found = any(m.id == model_id for m in models.data)
            if found:
                available.append(model_id)
            else:
                missing.append(model_id)

        if missing:
            return False, f"❌ Missing models: {', '.join(missing)}"

        return True, f"✅ All required models available: {', '.join(available)}"

    except Exception as e:
        return False, f"❌ Could not fetch models: {str(e)}"


def test_embedding_api() -> Tuple[bool, str]:
    """Test embedding API (used for semantic similarity)."""
    try:
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False, "❌ API key not set"

        openai.api_key = api_key

        # Test embedding generation
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input="test"
        )

        if response and response.data and len(response.data[0].embedding) == 1536:
            return True, "✅ Embedding API works (1536 dimensions)"
        else:
            return False, "❌ Embedding API returned invalid response"

    except Exception as e:
        return False, f"❌ Embedding API error: {str(e)}"


def main():
    """Run all connectivity tests."""
    print("=" * 60)
    print("OpenAI API Connectivity Test")
    print("=" * 60)
    print()

    tests = [
        ("1. API Key Check", test_api_key),
        ("2. OpenAI Library", test_openai_import),
        ("3. API Connectivity", test_api_connectivity),
        ("4. Models Available", test_models_available),
        ("5. Embedding API", test_embedding_api),
    ]

    results = []

    for name, test_func in tests:
        print(f"{name}...", end=" ")
        success, message = test_func()
        print(message)
        results.append(success)

        if not success:
            print(f"\n⚠️  Fix this issue before proceeding\n")

    print()
    print("=" * 60)

    if all(results):
        print("✅✅✅ ALL TESTS PASSED ✅✅✅")
        print()
        print("🚀 Ready to run enrichment pipeline!")
        print()
        print("Next steps:")
        print("  1. Small-scale test: python scripts/test_small_scale.py --pages 1")
        print("  2. Full pipeline: python scripts/full_pipeline.py")
        print()
        sys.exit(0)
    else:
        failed_count = len([r for r in results if not r])
        print(f"❌ {failed_count}/{len(results)} tests failed")
        print()
        print("Please fix the issues above and try again.")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
