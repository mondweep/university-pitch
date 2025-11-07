#!/usr/bin/env python3
"""
Test topic extraction enrichment.

This validates:
- Topic identification accuracy
- LLM prompt effectiveness
- Cost per topic extraction
- Integration with taxonomy
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
from src.enrichment.topic_models import TopicTaxonomy, TopicCategory


def load_sample_pages(graph_path: str, limit: int = 10) -> List[Dict]:
    """Load diverse sample pages from graph with aggregated content."""
    print(f"📂 Loading graph from: {graph_path}")

    graph = MGraph()
    graph.load_from_json(graph_path)

    # Get page nodes
    page_nodes = graph.query(node_type='Page', limit=limit)

    # For each page, aggregate content from ContentItems
    pages = []
    for page_node in page_nodes:
        page_data = page_node.data
        page_id = page_data.get('id')

        # Find related ContentItem nodes (those with page_id prefix)
        content_items = []
        for node in graph.query(node_type='ContentItem', limit=500):
            if node.data.get('id', '').startswith(page_id):
                text = node.data.get('text', '')
                if text and len(text) >= 20:  # Meaningful text only
                    content_items.append(text)

        # Aggregate content
        if content_items:
            aggregated_content = ' '.join(content_items[:50])  # Limit to first 50 items
            pages.append({
                'id': page_id,
                'title': page_data.get('title', 'Untitled'),
                'url': page_data.get('url', ''),
                'content': aggregated_content,
                'num_items': len(content_items)
            })

    print(f"✅ Loaded {len(pages)} pages with aggregated content")
    return pages


def extract_topics_from_page(client: OpenRouterClient, page: Dict) -> Dict:
    """Extract topics from a single page using LLM."""

    # Get predefined topics for reference
    predefined_topics = TopicTaxonomy.get_all_topics()
    topic_list = ", ".join(predefined_topics[:30])  # Show sample

    prompt = f"""Extract the main topics from this London Business School page.

Title: {page['title']}
Content: {page['content'][:800]}

Respond with 3-4 topics in JSON format:
{{
  "topics": [
    {{"name": "Topic Name", "confidence": 0.9, "category": "academic"}},
    {{"name": "Another Topic", "confidence": 0.8, "category": "business"}}
  ],
  "summary": "Brief page summary"
}}

Categories: academic, research, student_life, business, general
Sample topics: {topic_list[:100]}"""

    try:
        response = client.complete(prompt, max_tokens=400, temperature=0.3)

        # Parse JSON response
        result = json.loads(response)

        # Get cost
        cost = client.get_last_request_cost()

        return {
            'success': True,
            'topics': result.get('topics', []),
            'summary': result.get('summary', ''),
            'cost': cost
        }

    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON parse error: {str(e)}")
        print(f"  Raw response: {response[:200]}")
        return {
            'success': False,
            'error': f"JSON parse error: {str(e)}",
            'raw_response': response[:500],
            'cost': client.get_last_request_cost()
        }

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'cost': 0.0
        }


def analyze_topics(client: OpenRouterClient, pages: List[Dict]) -> Dict:
    """Analyze topics for multiple pages."""

    results = {
        'total_pages': len(pages),
        'successful': 0,
        'failed': 0,
        'total_topics': 0,
        'total_cost': 0.0,
        'total_time': 0.0,
        'page_results': [],
        'topic_distribution': {},
        'category_distribution': {}
    }

    print(f"\n🔄 Processing {len(pages)} pages for topic extraction")

    for i, page in enumerate(pages, 1):
        print(f"\n📄 Page {i}/{len(pages)}: {page['title'][:60]}")

        start_time = time.time()
        extraction = extract_topics_from_page(client, page)
        elapsed = time.time() - start_time

        results['total_cost'] += extraction.get('cost', 0.0)
        results['total_time'] += elapsed

        if extraction['success']:
            results['successful'] += 1
            topics = extraction['topics']
            results['total_topics'] += len(topics)

            # Display topics
            print(f"  ✅ Extracted {len(topics)} topics:")
            for topic in topics:
                name = topic.get('name', 'Unknown')
                conf = topic.get('confidence', 0.0)
                cat = topic.get('category', 'general')
                print(f"     • {name} (confidence: {conf:.2f}, category: {cat})")

                # Track distribution
                results['topic_distribution'][name] = results['topic_distribution'].get(name, 0) + 1
                results['category_distribution'][cat] = results['category_distribution'].get(cat, 0) + 1

            print(f"  💭 Summary: {extraction.get('summary', 'N/A')[:100]}")

            results['page_results'].append({
                'page_id': page['id'],
                'title': page['title'],
                'topics': topics,
                'summary': extraction.get('summary', ''),
                'cost': extraction['cost'],
                'time': elapsed
            })

        else:
            results['failed'] += 1
            print(f"  ❌ Failed: {extraction.get('error', 'Unknown error')}")

            results['page_results'].append({
                'page_id': page['id'],
                'title': page['title'],
                'error': extraction.get('error', 'Unknown'),
                'cost': extraction['cost'],
                'time': elapsed
            })

        print(f"  ⏱️  Time: {elapsed:.2f}s | 💰 Cost: ${extraction['cost']:.6f}")

    return results


def main():
    print("=" * 70)
    print("TOPIC EXTRACTION TEST")
    print("=" * 70)

    # Configuration
    graph_path = "data/graph/graph.json"
    num_pages = 10

    # Initialize client (use Claude for better structured output)
    print("\n🔧 Initializing OpenRouter client...")
    client = OpenRouterClient(model="anthropic/claude-3.5-sonnet")
    print(f"✅ Using model: {client.model}")

    # Load pages
    print("\n" + "=" * 70)
    pages = load_sample_pages(graph_path, limit=num_pages)

    if not pages:
        print("❌ No pages found with content!")
        return

    # Run topic extraction
    print("\n" + "=" * 70)
    print("EXTRACTING TOPICS")
    print("=" * 70)

    start_time = time.time()
    results = analyze_topics(client, pages)
    total_time = time.time() - start_time

    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"\n📊 Processing Summary:")
    print(f"  Total pages: {results['total_pages']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Success rate: {results['successful']/results['total_pages']*100:.1f}%")

    print(f"\n🏷️  Topic Statistics:")
    print(f"  Total topics extracted: {results['total_topics']}")
    print(f"  Average per page: {results['total_topics']/results['successful']:.1f}")
    print(f"  Unique topics: {len(results['topic_distribution'])}")

    if results['topic_distribution']:
        print(f"\n📈 Most Common Topics:")
        sorted_topics = sorted(results['topic_distribution'].items(), key=lambda x: x[1], reverse=True)
        for topic, count in sorted_topics[:10]:
            print(f"  • {topic}: {count} occurrences")

    if results['category_distribution']:
        print(f"\n📁 Category Distribution:")
        for category, count in sorted(results['category_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {category}: {count} topics")

    print(f"\n⚡ Performance:")
    print(f"  Total time: {results['total_time']:.2f}s")
    print(f"  Average per page: {results['total_time']/results['successful']:.2f}s")

    print(f"\n💰 Cost Analysis:")
    print(f"  Total cost: ${results['total_cost']:.6f}")
    print(f"  Cost per page: ${results['total_cost']/results['successful']:.6f}")
    print(f"  Cost per topic: ${results['total_cost']/results['total_topics']:.6f}")
    print(f"  Estimated full graph (3,963 pages): ${results['total_cost']/results['successful']*3963:.2f}")

    # Save detailed results
    output_file = "data/test_results/topic_extraction_test.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump({
            'config': {
                'num_pages': num_pages,
                'model': client.model
            },
            'results': results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")

    print("\n" + "=" * 70)
    print("✅ TOPIC EXTRACTION TEST COMPLETE")
    print("=" * 70)

    # Recommendations
    print("\n💡 Recommendations:")
    if results['successful'] >= 8:
        print("  ✅ Topic extraction working well!")
        print("  ✅ Ready to process full graph")
    else:
        print("  ⚠️  Some extractions failed - review prompts")

    if results['total_cost'] / results['successful'] > 0.05:
        print(f"  ⚠️  High cost per page (${results['total_cost']/results['successful']:.4f})")
        print("  💡 Consider using GPT-3.5-turbo for cost reduction")
    else:
        print(f"  ✅ Good cost efficiency (${results['total_cost']/results['successful']:.4f} per page)")


if __name__ == "__main__":
    main()
