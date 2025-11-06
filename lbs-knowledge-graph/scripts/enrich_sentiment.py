#!/usr/bin/env python3
"""
Master script for sentiment enrichment of LBS Knowledge Graph.

This script:
1. Loads the graph from Phase 2
2. Initializes LLM client and sentiment analyzer
3. Processes all content items in batches
4. Tracks progress and costs
5. Exports enriched graph
6. Generates sentiment statistics report
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enrichment.llm_client import LLMClient
from src.enrichment.sentiment_analyzer import SentimentAnalyzer
from src.enrichment.sentiment_enricher import SentimentEnricher


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_progress(current: int, total: int):
    """Print progress bar"""
    percent = (current / total) * 100
    bar_length = 50
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"\r   Progress: [{bar}] {current}/{total} ({percent:.1f}%)", end="", flush=True)


async def main():
    """Main enrichment workflow"""

    print_header("LBS Knowledge Graph - Sentiment Enrichment")

    # Load environment variables
    load_dotenv()

    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        print("   Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)

    # Paths
    project_root = Path(__file__).parent.parent
    graph_path = project_root / "data" / "graph" / "graph.json"
    output_path = project_root / "data" / "graph" / "graph_with_sentiment.json"
    report_path = project_root / "data" / "graph" / "sentiment_report.json"

    # Check if graph exists
    if not graph_path.exists():
        print(f"❌ ERROR: Graph not found at {graph_path}")
        print("   Please run Phase 2 graph construction first.")
        sys.exit(1)

    # Step 1: Load graph
    print_header("Step 1: Loading Graph")
    print(f"   Loading graph from: {graph_path}")

    with open(graph_path, "r", encoding="utf-8") as f:
        graph = json.load(f)

    print(f"   ✅ Loaded graph with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges")

    # Step 2: Initialize components
    print_header("Step 2: Initializing Components")

    print("   Initializing LLM client (gpt-4o-mini)...")
    llm_client = LLMClient(
        api_key=api_key,
        model="gpt-4o-mini",  # Cost-efficient model
        max_retries=3,
        timeout=30
    )
    print("   ✅ LLM client ready")

    print("   Initializing sentiment analyzer...")
    sentiment_analyzer = SentimentAnalyzer(llm_client)
    print("   ✅ Sentiment analyzer ready")

    print("   Initializing sentiment enricher...")
    sentiment_enricher = SentimentEnricher(graph, sentiment_analyzer)
    print("   ✅ Sentiment enricher ready")

    # Count content items
    content_items = sentiment_enricher.get_content_items()
    print(f"\n   📊 Found {len(content_items)} ContentItem nodes to analyze")

    # Estimate cost
    avg_tokens_per_item = 150  # Rough estimate
    total_tokens_estimate = len(content_items) * avg_tokens_per_item
    cost_estimate = (total_tokens_estimate / 1_000_000) * (0.150 + 0.600)  # gpt-4o-mini pricing
    print(f"   💰 Estimated cost: ${cost_estimate:.2f} (based on {total_tokens_estimate:,} tokens)")

    # Confirm
    print("\n   ⚠️  This will make API calls to OpenAI.")
    confirm = input("   Continue? (y/n): ")
    if confirm.lower() != "y":
        print("   Aborted.")
        sys.exit(0)

    # Step 3: Run sentiment enrichment
    print_header("Step 3: Running Sentiment Analysis")

    start_time = datetime.now()

    # Run enrichment with progress tracking
    enriched_graph = await sentiment_enricher.enrich_graph(
        batch_size=50,
        progress_callback=lambda current, total: print_progress(current, total)
    )

    print()  # New line after progress bar

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n   ⏱️  Completed in {duration:.1f} seconds")

    # Step 4: Display statistics
    print_header("Step 4: Statistics")

    stats = sentiment_enricher.get_statistics()
    llm_stats = sentiment_analyzer.get_stats()

    print(f"   Content Items:")
    print(f"      Total: {stats['content_items']}")
    print(f"      With sentiment: {stats['content_with_sentiment']}")

    print(f"\n   Sections:")
    print(f"      Total: {stats['sections']}")
    print(f"      With sentiment: {stats['sections_with_sentiment']}")

    print(f"\n   Pages:")
    print(f"      Total: {stats['pages']}")
    print(f"      With sentiment: {stats['pages_with_sentiment']}")

    print(f"\n   Sentiment Distribution:")
    dist = stats['sentiment_distribution']
    print(f"      Positive: {dist['positive']}")
    print(f"      Negative: {dist['negative']}")
    print(f"      Neutral: {dist['neutral']}")
    print(f"      Mixed: {dist['mixed']}")

    print(f"\n   Averages:")
    print(f"      Sentiment score: {stats['average_sentiment_score']:.3f}")
    print(f"      Confidence: {stats['average_confidence']:.3f}")

    print(f"\n   API Usage:")
    print(f"      API calls: {llm_stats['llm_stats']['api_calls']}")
    print(f"      Total tokens: {llm_stats['llm_stats']['total_tokens']:,}")
    print(f"      Avg tokens/call: {llm_stats['llm_stats']['avg_tokens_per_call']:.1f}")
    print(f"      Total cost: ${llm_stats['llm_stats']['total_cost']:.2f}")

    # Step 5: Export enriched graph
    print_header("Step 5: Exporting Results")

    print(f"   Exporting enriched graph to: {output_path}")
    sentiment_enricher.export_graph(output_path)

    # Generate full report
    report = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration,
        "graph_stats": stats,
        "api_stats": llm_stats,
        "files": {
            "input_graph": str(graph_path),
            "output_graph": str(output_path)
        }
    }

    print(f"   Exporting report to: {report_path}")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print_header("✅ Sentiment Enrichment Complete!")

    print(f"   Enriched graph: {output_path}")
    print(f"   Report: {report_path}")
    print(f"   Total cost: ${llm_stats['llm_stats']['total_cost']:.2f}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
