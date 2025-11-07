#!/usr/bin/env python3
"""
Test sentiment analysis at scale (100 items).

This validates:
- Cost estimation accuracy
- Performance at scale
- Batch processing efficiency
- Result quality consistency
"""

import sys
import time
import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.openrouter_client import OpenRouterClient
from src.graph.mgraph_compat import MGraph


def load_sample_content(graph_path: str, limit: int = 100) -> List[Dict]:
    """Load sample content items from graph."""
    print(f"📂 Loading graph from: {graph_path}")

    graph = MGraph()
    graph.load_from_json(graph_path)

    # Get ContentItem nodes with text (minimum 50 chars for meaningful analysis)
    items = []
    content_nodes = graph.query(node_type='ContentItem', limit=limit * 3)

    for node in content_nodes:
        node_data = node.data
        text = node_data.get('text', '')

        # Filter for meaningful content (at least 50 characters)
        if text and len(text) >= 50:
            items.append({
                'id': node_data.get('id'),
                'text': text,
                'word_count': node_data.get('word_count', 0),
                'content_type': node_data.get('content_type', 'unknown')
            })

            if len(items) >= limit:
                break

    print(f"✅ Loaded {len(items)} content items with meaningful text")
    return items


def batch_sentiment_analysis(client: OpenRouterClient, items: List[Dict], batch_size: int = 10) -> Dict:
    """Run sentiment analysis in batches."""

    results = {
        'total_processed': 0,
        'sentiments': {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0},
        'total_cost': 0.0,
        'total_time': 0.0,
        'batch_results': [],
        'errors': []
    }

    # Process in batches
    num_batches = (len(items) + batch_size - 1) // batch_size
    print(f"\n🔄 Processing {len(items)} items in {num_batches} batches of {batch_size}")

    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(items))
        batch = items[start_idx:end_idx]

        print(f"\n📦 Batch {batch_num + 1}/{num_batches} (items {start_idx + 1}-{end_idx})")

        batch_start = time.time()
        batch_cost = 0.0
        batch_results = []

        for item in batch:
            try:
                # Analyze sentiment
                prompt = f"""Analyze the sentiment of this text about London Business School.
Respond with ONLY one word: POSITIVE, NEGATIVE, or NEUTRAL.

Text: {item['text'][:300]}"""

                response = client.complete(prompt, max_tokens=10)
                sentiment = response.strip().upper()

                if sentiment not in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
                    sentiment = 'NEUTRAL'  # Default if unclear

                # Track result
                results['sentiments'][sentiment] += 1
                results['total_processed'] += 1

                # Get cost from last request
                cost = client.get_last_request_cost()
                batch_cost += cost
                results['total_cost'] += cost

                batch_results.append({
                    'item_id': item['id'],
                    'text_preview': item['text'][:60],
                    'sentiment': sentiment,
                    'cost': cost
                })

            except Exception as e:
                print(f"  ❌ Error on item {item['id']}: {str(e)}")
                results['errors'].append({
                    'item_id': item['id'],
                    'error': str(e)
                })

        batch_time = time.time() - batch_start
        results['total_time'] += batch_time

        results['batch_results'].append({
            'batch_num': batch_num + 1,
            'items': len(batch),
            'cost': batch_cost,
            'time': batch_time,
            'items_per_second': len(batch) / batch_time if batch_time > 0 else 0
        })

        print(f"  ⏱️  Time: {batch_time:.2f}s ({len(batch)/batch_time:.1f} items/sec)")
        print(f"  💰 Cost: ${batch_cost:.6f}")

    return results


def main():
    print("=" * 70)
    print("SENTIMENT ANALYSIS SCALE TEST (100 items)")
    print("=" * 70)

    # Configuration
    graph_path = "data/graph/graph.json"
    num_items = 100
    batch_size = 10

    # Initialize client
    print("\n🔧 Initializing OpenRouter client...")
    client = OpenRouterClient(model="openai/gpt-3.5-turbo")
    print(f"✅ Using model: {client.model}")

    # Load content items
    print("\n" + "=" * 70)
    items = load_sample_content(graph_path, limit=num_items)

    if not items:
        print("❌ No content items found with text!")
        return

    # Run sentiment analysis
    print("\n" + "=" * 70)
    print("RUNNING SENTIMENT ANALYSIS")
    print("=" * 70)

    start_time = time.time()
    results = batch_sentiment_analysis(client, items, batch_size=batch_size)
    total_time = time.time() - start_time

    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\n📊 Processing Summary:")
    print(f"  Total items: {results['total_processed']}")
    print(f"  Errors: {len(results['errors'])}")
    print(f"  Success rate: {results['total_processed']/(results['total_processed']+len(results['errors']))*100:.1f}%")

    print(f"\n💭 Sentiment Distribution:")
    total = results['total_processed']
    for sentiment, count in results['sentiments'].items():
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {sentiment:8s}: {count:3d} ({pct:5.1f}%)")

    print(f"\n⚡ Performance:")
    print(f"  Total time: {results['total_time']:.2f}s")
    print(f"  Average per item: {results['total_time']/results['total_processed']:.3f}s")
    print(f"  Throughput: {results['total_processed']/results['total_time']:.2f} items/sec")

    print(f"\n💰 Cost Analysis:")
    print(f"  Total cost: ${results['total_cost']:.6f}")
    print(f"  Cost per item: ${results['total_cost']/results['total_processed']:.6f}")
    print(f"  Estimated full graph (3,963 pages): ${results['total_cost']/results['total_processed']*3963:.2f}")

    print(f"\n📦 Batch Performance:")
    for batch in results['batch_results']:
        print(f"  Batch {batch['batch_num']}: {batch['items']} items, "
              f"{batch['time']:.2f}s, ${batch['cost']:.6f}, "
              f"{batch['items_per_second']:.1f} items/sec")

    # Save detailed results
    output_file = "data/test_results/sentiment_scale_test.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump({
            'config': {
                'num_items': num_items,
                'batch_size': batch_size,
                'model': client.model
            },
            'results': results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")

    print("\n" + "=" * 70)
    print("✅ SCALE TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
