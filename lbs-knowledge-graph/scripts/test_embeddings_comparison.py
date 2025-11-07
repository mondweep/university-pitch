#!/usr/bin/env python3
"""
Compare free embedding options for demonstration.

Tests all three providers:
1. Sentence-Transformers (local)
2. Cohere (API)
3. Voyage AI (API)

Usage:
    # Test local only (no API keys needed)
    python scripts/test_embeddings_comparison.py --local

    # Test all providers (requires API keys)
    export COHERE_API_KEY="..."
    export VOYAGE_API_KEY="..."
    python scripts/test_embeddings_comparison.py --all

    # Test specific provider
    python scripts/test_embeddings_comparison.py --provider cohere
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enrichment.free_embeddings import FreeEmbedder


# Test texts (representative of LBS content)
TEST_TEXTS = [
    "London Business School offers world-class MBA programmes with global perspective",
    "LBS provides excellent business education for aspiring leaders",
    "Master of Business Administration degree at London Business School",
    "Executive education programmes for senior professionals",
    "The weather forecast predicts rain tomorrow afternoon",
    "Python programming language for data analysis",
]


def test_provider(provider: str, api_key: str = None):
    """Test a specific embedding provider."""
    print(f"\n{'=' * 60}")
    print(f"Testing: {provider.upper()}")
    print(f"{'=' * 60}\n")

    try:
        # Initialize
        start_init = time.time()
        embedder = FreeEmbedder(provider=provider, api_key=api_key)
        init_time = time.time() - start_init

        # Get info
        info = embedder.info()
        print(f"Model: {info['model']}")
        print(f"Dimensions: {info['dimensions']}")
        print(f"Initialization: {init_time:.2f}s")
        print()

        # Generate embeddings
        print(f"Generating embeddings for {len(TEST_TEXTS)} texts...")
        start_embed = time.time()
        embeddings = embedder.embed(TEST_TEXTS, show_progress=False)
        embed_time = time.time() - start_embed

        print(f"✅ Generated {len(embeddings)} embeddings in {embed_time:.2f}s")
        print(f"   Shape: {embeddings.shape}")
        print(f"   Speed: {len(TEST_TEXTS) / embed_time:.1f} texts/second")
        print()

        # Calculate similarities
        print("Semantic similarities:")
        pairs = [
            (0, 1, "MBA programme vs Business education"),
            (0, 2, "MBA programme vs MBA degree"),
            (0, 3, "MBA programme vs Executive education"),
            (0, 4, "MBA programme vs Weather"),
            (0, 5, "MBA programme vs Python"),
        ]

        for idx1, idx2, description in pairs:
            sim = embedder.similarity(embeddings[idx1], embeddings[idx2])
            emoji = "🟢" if sim > 0.7 else "🟡" if sim > 0.4 else "🔴"
            print(f"  {emoji} {description}: {sim:.3f}")

        print()

        # Find top similar pairs
        print("Top similar pairs (threshold: 0.6):")
        similar_pairs = embedder.batch_similarity(embeddings, threshold=0.6)

        if similar_pairs:
            for idx1, idx2, sim in similar_pairs[:5]:
                text1 = TEST_TEXTS[idx1][:50] + "..." if len(TEST_TEXTS[idx1]) > 50 else TEST_TEXTS[idx1]
                text2 = TEST_TEXTS[idx2][:50] + "..." if len(TEST_TEXTS[idx2]) > 50 else TEST_TEXTS[idx2]
                print(f"  {sim:.3f}: Text {idx1} ↔ Text {idx2}")
                print(f"         '{text1}'")
                print(f"         '{text2}'")
        else:
            print("  (No pairs above threshold)")

        print()

        return {
            "provider": provider,
            "success": True,
            "init_time": init_time,
            "embed_time": embed_time,
            "speed": len(TEST_TEXTS) / embed_time,
            "dimensions": info['dimensions'],
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print()
        return {
            "provider": provider,
            "success": False,
            "error": str(e)
        }


def print_comparison(results):
    """Print comparison table."""
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60 + "\n")

    # Filter successful results
    successful = [r for r in results if r["success"]]

    if not successful:
        print("❌ No successful tests to compare")
        return

    # Print table
    print(f"{'Provider':<20} {'Init':<10} {'Embed':<10} {'Speed':<15} {'Dims':<10}")
    print("-" * 65)

    for r in successful:
        print(
            f"{r['provider']:<20} "
            f"{r['init_time']:.2f}s     "
            f"{r['embed_time']:.2f}s    "
            f"{r['speed']:.1f} texts/s   "
            f"{r['dimensions']:<10}"
        )

    print()

    # Recommendations
    print("📊 Recommendations:")
    print()

    # Find fastest
    fastest = min(successful, key=lambda x: x['embed_time'])
    print(f"⚡ Fastest: {fastest['provider']} ({fastest['embed_time']:.2f}s)")

    # Find local
    local = [r for r in successful if r['provider'] == 'local']
    if local:
        print(f"🏠 Local (no API): {local[0]['provider']} ({local[0]['embed_time']:.2f}s)")

    # Best for demo
    if local:
        print(f"\n✨ Best for demo: Sentence-Transformers (local)")
        print(f"   - No API keys needed")
        print(f"   - Unlimited usage")
        print(f"   - {local[0]['speed']:.1f} texts/second")
        print(f"   - Works offline")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Compare free embedding options"
    )
    parser.add_argument(
        "--provider",
        choices=["local", "cohere", "voyage"],
        help="Test specific provider"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Test local only (no API keys)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Test all providers (requires API keys)"
    )

    args = parser.parse_args()

    # Determine which providers to test
    providers = []

    if args.provider:
        providers = [args.provider]
    elif args.local:
        providers = ["local"]
    elif args.all:
        providers = ["local", "cohere", "voyage"]
    else:
        # Default: test local
        providers = ["local"]

    print("=" * 60)
    print("Free Embedding Comparison Test")
    print("=" * 60)
    print()
    print(f"Testing {len(providers)} provider(s): {', '.join(providers)}")
    print(f"Test texts: {len(TEST_TEXTS)}")
    print()

    # Test each provider
    results = []

    for provider in providers:
        # Get API key from environment if needed
        api_key = None
        if provider == "cohere":
            api_key = os.getenv("COHERE_API_KEY")
            if not api_key:
                print(f"\n⚠️  Skipping {provider}: COHERE_API_KEY not set")
                continue
        elif provider == "voyage":
            api_key = os.getenv("VOYAGE_API_KEY")
            if not api_key:
                print(f"\n⚠️  Skipping {provider}: VOYAGE_API_KEY not set")
                continue

        result = test_provider(provider, api_key)
        results.append(result)

    # Print comparison
    if len(results) > 1:
        print_comparison(results)

    # Final recommendation
    print("=" * 60)
    print("✅ Testing Complete!")
    print("=" * 60)
    print()

    if any(r["success"] for r in results):
        print("Next steps:")
        print("  1. Choose your preferred provider")
        print("  2. Update enrichment scripts to use it")
        print("  3. Run small-scale test: python scripts/test_small_scale.py --pages 1")
        print()

        # Check if local was successful
        local_success = any(r["provider"] == "local" and r["success"] for r in results)
        if local_success:
            print("💡 Tip: For demos, use Sentence-Transformers (local)")
            print("   - Install: pip install sentence-transformers")
            print("   - No API keys needed!")
            print()
    else:
        print("❌ All tests failed. Check errors above.")
        print()


if __name__ == "__main__":
    main()
