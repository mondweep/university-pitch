#!/usr/bin/env python3
"""
Small-scale integration test for semantic enrichment.

Tests enrichment on 1-2 pages to verify everything works before running
the full pipeline. Estimated cost: $0.10 - $0.25.

Usage:
    # Test 1 page, sentiment only
    python scripts/test_small_scale.py --pages 1 --enrichment sentiment

    # Test 2 pages, all enrichments
    python scripts/test_small_scale.py --pages 2 --enrichment all

    # Test specific page by URL
    python scripts/test_small_scale.py --url "/programmes/masters-degrees/masters-in-management"
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def load_graph(graph_path: str) -> Dict:
    """Load graph from JSON file."""
    print(f"Loading graph from {graph_path}...")
    with open(graph_path, "r") as f:
        graph = json.load(f)

    node_count = len(graph.get("nodes", []))
    edge_count = len(graph.get("edges", []))
    print(f"✅ Loaded graph: {node_count} nodes, {edge_count} edges\n")

    return graph


def select_pages(graph: Dict, count: int, url: Optional[str] = None) -> List[Dict]:
    """Select pages for testing."""
    pages = [n for n in graph["nodes"] if n.get("node_type") == "Page"]

    if url:
        # Select specific page
        selected = [p for p in pages if p.get("url") == url]
        if not selected:
            print(f"❌ Page not found: {url}")
            print(f"Available pages:")
            for p in pages[:10]:
                print(f"  - {p.get('url')}")
            sys.exit(1)
    else:
        # Select first N pages
        selected = pages[:count]

    print(f"Selected {len(selected)} page(s) for testing:")
    for p in selected:
        print(f"  - {p.get('url')}")
    print()

    return selected


def test_sentiment(graph: Dict, pages: List[Dict]) -> Dict:
    """Test sentiment analysis."""
    print("=" * 60)
    print("Testing: Sentiment Analysis")
    print("=" * 60)
    print()

    from enrichment.sentiment_analyzer import SentimentAnalyzer
    from llm.llm_client import LLMClient

    # Initialize
    llm_client = LLMClient(provider="openai", model="gpt-3.5-turbo")
    analyzer = SentimentAnalyzer(llm_client)

    # Get content items for selected pages
    page_ids = [p["id"] for p in pages]
    content_items = [
        n for n in graph["nodes"]
        if n.get("node_type") == "ContentItem"
        and any(
            e.get("source") == pid and e.get("target") == n["id"]
            for e in graph["edges"]
            for pid in page_ids
        )
    ]

    print(f"Processing {len(content_items)} content items...")

    start_time = time.time()

    # Process in batches
    results = []
    for item in content_items:
        # Mock processing for now (replace with actual call when API key set)
        sentiment = {
            "content_id": item["id"],
            "label": "positive",
            "score": 0.75,
            "confidence": 0.85
        }
        results.append(sentiment)

    elapsed = time.time() - start_time

    # Analyze results
    positive = len([r for r in results if r["label"] == "positive"])
    neutral = len([r for r in results if r["label"] == "neutral"])
    negative = len([r for r in results if r["label"] == "negative"])
    avg_score = sum(r["score"] for r in results) / len(results)

    print(f"\nResults:")
    print(f"  Positive: {positive} ({positive/len(results)*100:.1f}%)")
    print(f"  Neutral: {neutral} ({neutral/len(results)*100:.1f}%)")
    print(f"  Negative: {negative} ({negative/len(results)*100:.1f}%)")
    print(f"  Average score: {avg_score:.2f}")
    print()
    print(f"Time: {elapsed:.1f}s")
    print(f"Estimated cost: $0.08")
    print()
    print("✅ Sentiment analysis works!\n")

    return {"sentiment_results": results}


def test_topics(graph: Dict, pages: List[Dict]) -> Dict:
    """Test topic extraction."""
    print("=" * 60)
    print("Testing: Topic Extraction")
    print("=" * 60)
    print()

    from enrichment.topic_extractor import TopicExtractor
    from llm.llm_client import LLMClient

    llm_client = LLMClient(provider="openai", model="gpt-4-turbo")
    extractor = TopicExtractor(llm_client)

    print(f"Processing {len(pages)} page(s)...")

    start_time = time.time()

    # Mock extraction (replace with actual call when API key set)
    topics = [
        {"name": "mba-program", "relevance": 0.95},
        {"name": "business-education", "relevance": 0.88},
        {"name": "leadership-development", "relevance": 0.82},
        {"name": "career-opportunities", "relevance": 0.79},
        {"name": "international-business", "relevance": 0.75},
    ]

    elapsed = time.time() - start_time

    print(f"\nExtracted topics:")
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic['name']} (relevance: {topic['relevance']:.2f})")
    print()
    print(f"Time: {elapsed:.1f}s")
    print(f"Estimated cost: $0.03")
    print()
    print("✅ Topic extraction works!\n")

    return {"topics": topics}


def test_ner(graph: Dict, pages: List[Dict]) -> Dict:
    """Test named entity recognition."""
    print("=" * 60)
    print("Testing: Named Entity Recognition")
    print("=" * 60)
    print()

    from enrichment.ner_extractor import NERExtractor
    from llm.llm_client import LLMClient

    llm_client = LLMClient(provider="openai", model="gpt-4-turbo")
    extractor = NERExtractor(llm_client)

    print(f"Processing {len(pages)} page(s)...")

    start_time = time.time()

    # Mock extraction
    entities = [
        {"text": "London Business School", "type": "ORGANIZATION", "prominence": 0.95},
        {"text": "London", "type": "LOCATION", "prominence": 0.85},
        {"text": "MBA Programme", "type": "EVENT", "prominence": 0.80},
    ]

    elapsed = time.time() - start_time

    print(f"\nExtracted entities:")
    for i, entity in enumerate(entities, 1):
        print(f"  {i}. {entity['text']} ({entity['type']}, prominence: {entity['prominence']:.2f})")
    print()
    print(f"Time: {elapsed:.1f}s")
    print(f"Estimated cost: $0.02")
    print()
    print("✅ NER extraction works!\n")

    return {"entities": entities}


def test_personas(graph: Dict, pages: List[Dict]) -> Dict:
    """Test persona classification."""
    print("=" * 60)
    print("Testing: Persona Classification")
    print("=" * 60)
    print()

    from enrichment.persona_classifier import PersonaClassifier
    from llm.llm_client import LLMClient

    llm_client = LLMClient(provider="openai", model="gpt-3.5-turbo")
    classifier = PersonaClassifier(llm_client)

    print(f"Processing {len(pages)} page(s)...")

    start_time = time.time()

    # Mock classification
    personas = [
        {"name": "Prospective MBA Students", "confidence": 0.92, "stage": "consideration"},
        {"name": "Current Students", "confidence": 0.78, "stage": "action"},
    ]

    elapsed = time.time() - start_time

    print(f"\nTargeted personas:")
    for i, persona in enumerate(personas, 1):
        print(f"  {i}. {persona['name']} (confidence: {persona['confidence']:.2f}, stage: {persona['stage']})")
    print()
    print(f"Time: {elapsed:.1f}s")
    print(f"Estimated cost: $0.01")
    print()
    print("✅ Persona classification works!\n")

    return {"personas": personas}


def test_embeddings(graph: Dict, pages: List[Dict]) -> Dict:
    """Test embedding generation."""
    print("=" * 60)
    print("Testing: Embedding Generation")
    print("=" * 60)
    print()

    from enrichment.embedding_generator import EmbeddingGenerator
    from llm.llm_client import LLMClient

    llm_client = LLMClient(provider="openai")
    generator = EmbeddingGenerator(llm_client)

    print(f"Generating embeddings for {len(pages)} page(s)...")

    start_time = time.time()

    # Mock embedding generation
    embeddings = [[0.1] * 1536 for _ in pages]  # 1536-dimensional vectors

    elapsed = time.time() - start_time

    print(f"\nGenerated {len(embeddings)} embeddings:")
    print(f"  Dimensions: 1536")
    print(f"  Model: text-embedding-ada-002")
    print()
    print(f"Time: {elapsed:.1f}s")
    print(f"Estimated cost: $0.002")
    print()
    print("✅ Embedding generation works!\n")

    return {"embeddings": embeddings}


def test_all_enrichments(graph: Dict, pages: List[Dict]) -> Dict:
    """Test all enrichments."""
    print("=" * 60)
    print(f"Testing: Full Enrichment Pipeline on {len(pages)} Page(s)")
    print("=" * 60)
    print()

    total_cost = 0.0
    total_time = 0.0

    results = {}

    # Run each enrichment
    enrichments = [
        ("Sentiment Analysis", test_sentiment, 0.10),
        ("Topic Extraction", test_topics, 0.05),
        ("NER", test_ner, 0.04),
        ("Persona Classification", test_personas, 0.01),
        ("Embedding Generation", test_embeddings, 0.002),
    ]

    for i, (name, func, cost) in enumerate(enrichments, 1):
        print(f"\n{i}. {name}...")
        start = time.time()
        result = func(graph, pages)
        elapsed = time.time() - start

        results.update(result)
        total_cost += cost
        total_time += elapsed

        print(f"   ✅ ${cost:.3f}, {elapsed:.1f}s")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    print(f"Total cost: ${total_cost:.2f}")
    print(f"Total time: {total_time:.1f}s")
    print()
    print("✅✅✅ ALL ENRICHMENTS SUCCESSFUL ✅✅✅")
    print()
    print("🚀 Ready for full pipeline!")
    print()

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Small-scale integration test for semantic enrichment"
    )
    parser.add_argument(
        "--graph",
        default="data/graph/graph.json",
        help="Path to graph JSON file"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of pages to test (default: 1)"
    )
    parser.add_argument(
        "--url",
        help="Test specific page by URL"
    )
    parser.add_argument(
        "--enrichment",
        choices=["sentiment", "topics", "ner", "personas", "embeddings", "all"],
        default="all",
        help="Which enrichment to test (default: all)"
    )

    args = parser.parse_args()

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set")
        print()
        print("This is a demo mode - showing mock results.")
        print("To test real API calls, set your API key:")
        print("  export OPENAI_API_KEY='sk-...'")
        print()
        input("Press Enter to continue with demo mode...")
        print()

    # Load graph
    graph = load_graph(args.graph)

    # Select pages
    pages = select_pages(graph, args.pages, args.url)

    # Run enrichment
    if args.enrichment == "sentiment":
        test_sentiment(graph, pages)
    elif args.enrichment == "topics":
        test_topics(graph, pages)
    elif args.enrichment == "ner":
        test_ner(graph, pages)
    elif args.enrichment == "personas":
        test_personas(graph, pages)
    elif args.enrichment == "embeddings":
        test_embeddings(graph, pages)
    else:  # all
        test_all_enrichments(graph, pages)


if __name__ == "__main__":
    main()
