#!/usr/bin/env python3
"""
Test script to verify sentiment analysis setup before running enrichment.

Checks:
1. Environment variables are set
2. Graph file exists and is valid
3. All required modules are importable
4. API key is valid (optional test call)
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_status(check: str, passed: bool, message: str = ""):
    """Print check status with icon"""
    icon = "✅" if passed else "❌"
    status = "PASSED" if passed else "FAILED"
    print(f"   {icon} {check}: {status}")
    if message:
        print(f"      {message}")


def main():
    """Run setup checks"""

    print("\n" + "=" * 80)
    print("  Sentiment Analysis Setup Verification")
    print("=" * 80 + "\n")

    all_passed = True

    # Check 1: Environment variables
    print("📋 Checking Environment Variables...")
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "sk-...":
        print_status("OPENAI_API_KEY", True, f"Key found: {api_key[:10]}...{api_key[-4:]}")
    else:
        print_status("OPENAI_API_KEY", False, "Not set or using placeholder")
        all_passed = False
        print("\n      Set your API key:")
        print("      1. Edit lbs-knowledge-graph/.env")
        print("      2. Replace placeholder with: OPENAI_API_KEY=sk-your-key-here")
        print("      Or export: export OPENAI_API_KEY='sk-your-key-here'\n")

    # Check 2: Graph file
    print("\n📊 Checking Graph Files...")
    project_root = Path(__file__).parent.parent
    graph_path = project_root / "data" / "graph" / "graph.json"

    if graph_path.exists():
        with open(graph_path, "r", encoding="utf-8") as f:
            graph = json.load(f)

        node_count = len(graph.get("nodes", []))
        edge_count = len(graph.get("edges", []))

        # Count content items
        content_items = [
            node for node in graph["nodes"]
            if node.get("node_type") == "ContentItem"
        ]

        print_status("Graph file", True, f"{node_count} nodes, {edge_count} edges")
        print(f"      ContentItems to analyze: {len(content_items)}")

        # Estimate
        if len(content_items) > 0:
            avg_tokens = 150
            total_tokens = len(content_items) * avg_tokens
            cost_estimate = (total_tokens / 1_000_000) * (0.150 + 0.600)
            print(f"      Estimated cost: ${cost_estimate:.2f}")
    else:
        print_status("Graph file", False, f"Not found: {graph_path}")
        all_passed = False

    # Check 3: Module imports
    print("\n📦 Checking Module Imports...")

    try:
        from src.enrichment.llm_client import LLMClient
        print_status("LLMClient", True)
    except ImportError as e:
        print_status("LLMClient", False, str(e))
        all_passed = False

    try:
        from src.enrichment.sentiment_analyzer import SentimentAnalyzer
        print_status("SentimentAnalyzer", True)
    except ImportError as e:
        print_status("SentimentAnalyzer", False, str(e))
        all_passed = False

    try:
        from src.enrichment.sentiment_enricher import SentimentEnricher
        print_status("SentimentEnricher", True)
    except ImportError as e:
        print_status("SentimentEnricher", False, str(e))
        all_passed = False

    try:
        from src.enrichment.models import SentimentScore, SentimentPolarity
        print_status("Models", True)
    except ImportError as e:
        print_status("Models", False, str(e))
        all_passed = False

    # Check 4: Output directories
    print("\n📁 Checking Output Directories...")
    output_dir = project_root / "data" / "graph"
    validation_dir = project_root / "data" / "validation"

    if output_dir.exists():
        print_status("Output directory", True, str(output_dir))
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        print_status("Output directory", True, f"Created: {output_dir}")

    if validation_dir.exists():
        print_status("Validation directory", True, str(validation_dir))
    else:
        validation_dir.mkdir(parents=True, exist_ok=True)
        print_status("Validation directory", True, f"Created: {validation_dir}")

    # Final summary
    print("\n" + "=" * 80)
    if all_passed:
        print("  ✅ ALL CHECKS PASSED - Ready to run sentiment enrichment!")
        print("=" * 80 + "\n")
        print("  Run sentiment enrichment:")
        print("    cd /workspaces/university-pitch/lbs-knowledge-graph")
        print("    python scripts/enrich_sentiment.py")
        print()
        print("  Then validate results:")
        print("    python scripts/validate_sentiment.py")
        print()
    else:
        print("  ❌ SOME CHECKS FAILED - Please fix issues above")
        print("=" * 80 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
