#!/usr/bin/env python3
"""
Test OpenRouter connectivity and available models.

Usage:
    python scripts/test_openrouter.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.openrouter_client import OpenRouterClient


def test_connection():
    """Test basic OpenRouter connection."""
    print("=" * 70)
    print("OpenRouter Connection Test")
    print("=" * 70)
    print()

    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        print("❌ No API key found!")
        print()
        print("Please set one of:")
        print("  export OPENROUTER_API_KEY='sk-or-v1-...'")
        print("  export OPEN_ROUTER_API_KEY='sk-or-v1-...'")
        print()
        print("Or add to .env file:")
        print("  OPENROUTER_API_KEY=sk-or-v1-...")
        return False

    print(f"✅ API key found: {api_key[:20]}...")
    print()

    return True


def test_models():
    """Test different models."""
    print("=" * 70)
    print("Testing Models")
    print("=" * 70)
    print()

    test_cases = [
        {
            "model": "anthropic/claude-3-5-haiku-20241022",
            "prompt": "In one sentence, what is sentiment analysis?",
            "name": "Claude 3.5 Haiku (Fast & Cheap)"
        },
        {
            "model": "anthropic/claude-3.5-sonnet",
            "prompt": "In one sentence, what is a knowledge graph?",
            "name": "Claude 3.5 Sonnet (Best Quality)"
        },
    ]

    results = []

    for test in test_cases:
        print(f"\nTesting: {test['name']}")
        print(f"Model: {test['model']}")
        print(f"Prompt: {test['prompt']}")
        print()

        try:
            client = OpenRouterClient(model=test['model'])

            import time
            start = time.time()
            response = client.complete(test['prompt'], max_tokens=100)
            elapsed = time.time() - start

            print(f"✅ Response ({elapsed:.2f}s): {response}")

            # Estimate cost
            input_tokens = client.count_tokens(test['prompt'])
            output_tokens = client.count_tokens(response)
            cost = client.estimate_cost(input_tokens, output_tokens)

            print(f"   Tokens: {input_tokens} in, {output_tokens} out")
            print(f"   Cost: ${cost:.6f}")

            results.append({
                "model": test['model'],
                "success": True,
                "time": elapsed,
                "cost": cost
            })

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "model": test['model'],
                "success": False,
                "error": str(e)
            })

    return results


def show_recommendations(results):
    """Show model recommendations."""
    print()
    print("=" * 70)
    print("Recommendations for LBS Knowledge Graph")
    print("=" * 70)
    print()

    print("For your demo, I recommend:")
    print()

    print("1. Sentiment Analysis (3,743 items):")
    print("   Model: anthropic/claude-3-5-haiku-20241022")
    print("   Reason: Fast and cheap for simple classification")
    print("   Cost: ~$0.60")
    print()

    print("2. Topic Extraction (10 pages):")
    print("   Model: anthropic/claude-3.5-sonnet")
    print("   Reason: Better quality for complex extraction")
    print("   Cost: ~$0.35")
    print()

    print("3. NER (10 pages):")
    print("   Model: anthropic/claude-3.5-sonnet")
    print("   Reason: Better entity recognition")
    print("   Cost: ~$0.30")
    print()

    print("4. Persona Classification (10 pages):")
    print("   Model: anthropic/claude-3-5-haiku-20241022")
    print("   Reason: Simple multi-label classification")
    print("   Cost: ~$0.08")
    print()

    print("5. Embeddings:")
    print("   Model: Sentence-Transformers (local)")
    print("   Reason: Free, fast, no API needed")
    print("   Cost: $0.00")
    print()

    print("=" * 70)
    print("Total estimated cost: ~$1.33")
    print("=" * 70)


def main():
    """Main test function."""
    print()
    print("🚀 OpenRouter API Test")
    print()

    # Test connection
    if not test_connection():
        sys.exit(1)

    # Show available models
    print()
    OpenRouterClient.list_models()

    # Test models
    results = test_models()

    # Show recommendations
    show_recommendations(results)

    # Summary
    print()
    print("✅ OpenRouter is ready to use!")
    print()
    print("Next steps:")
    print("  1. Update enrichment scripts to use OpenRouter")
    print("  2. Run small-scale test: python scripts/test_small_scale.py --pages 1")
    print("  3. Run full demo: python scripts/full_pipeline.py")
    print()


if __name__ == "__main__":
    main()
