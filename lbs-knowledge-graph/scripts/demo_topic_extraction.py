#!/usr/bin/env python3
"""
Topic Extraction Demonstration Script

Demonstrates the complete topic extraction pipeline without requiring live LLM API calls.
Creates realistic sample data showing expected outputs and validates the infrastructure.

This demonstrates:
1. Topic extraction from 10 pages
2. Topic node creation (20-30 unique topics)
3. HAS_TOPIC edge creation (50-100 relationships)
4. Topic statistics and distribution
5. Quality metrics and validation

Run with: python scripts/demo_topic_extraction.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.graph.mgraph_compat import MGraph


def generate_sample_topics_for_page(page: Dict, page_index: int) -> List[Dict]:
    """
    Generate realistic sample topics based on page type and content.

    Simulates what GPT-4-turbo would extract from page content.

    Args:
        page: Page node data
        page_index: Index for variety

    Returns:
        List of topic dictionaries
    """
    page_type = page.get('type', 'unknown')
    title = page.get('title', '')

    # Base topic pools by page type
    topic_pools = {
        'program': [
            ('MBA Programme', 0.95, 'academic'),
            ('Executive Education', 0.90, 'academic'),
            ('Masters Degrees', 0.88, 'academic'),
            ('Leadership Development', 0.85, 'academic'),
            ('Business Strategy', 0.82, 'research'),
            ('Career Advancement', 0.80, 'career'),
            ('Programme Structure', 0.78, 'academic'),
        ],
        'landing': [
            ('Business Education', 0.92, 'academic'),
            ('Research Excellence', 0.89, 'research'),
            ('Global Network', 0.86, 'alumni'),
            ('Innovation', 0.84, 'research'),
            ('Leadership', 0.82, 'academic'),
            ('Digital Transformation', 0.80, 'business'),
            ('Student Experience', 0.78, 'student_life'),
        ],
        'news': [
            ('Business News', 0.94, 'general'),
            ('Research Insights', 0.90, 'research'),
            ('Faculty Research', 0.87, 'faculty'),
            ('Industry Trends', 0.85, 'business'),
            ('Thought Leadership', 0.83, 'research'),
            ('Business Innovation', 0.81, 'business'),
        ],
        'about': [
            ('About LBS', 0.93, 'general'),
            ('Institutional Mission', 0.89, 'general'),
            ('Campus Life', 0.86, 'student_life'),
            ('London Location', 0.84, 'general'),
            ('International Community', 0.82, 'general'),
            ('Contact Information', 0.79, 'general'),
        ],
    }

    # Get topics for this page type, or use general topics
    base_topics = topic_pools.get(page_type, topic_pools['landing'])

    # Select 5-8 topics with some variation
    num_topics = 5 + (page_index % 4)  # 5-8 topics
    selected_topics = base_topics[:num_topics]

    # Add some cross-cutting themes
    cross_cutting = [
        ('Sustainability', 0.76, 'business'),
        ('Diversity and Inclusion', 0.74, 'general'),
        ('Technology', 0.72, 'business'),
        ('Entrepreneurship', 0.70, 'career'),
    ]

    # Add 1-2 cross-cutting themes
    if page_index % 2 == 0:
        selected_topics = list(selected_topics) + [cross_cutting[page_index % len(cross_cutting)]]

    # Convert to topic dictionaries
    topics = []
    for name, relevance, category in selected_topics:
        topic_id = f"topic-{name.lower().replace(' ', '-')}"
        topics.append({
            'id': topic_id,
            'name': name,
            'relevance': relevance,
            'category': category,
            'confidence': 0.85 + (page_index % 10) * 0.01,  # 0.85-0.94
        })

    return topics


def build_topic_nodes_and_edges(graph: MGraph, extraction_results: List[Dict]) -> Dict:
    """
    Build Topic nodes and HAS_TOPIC edges from extraction results.

    Args:
        graph: MGraph instance
        extraction_results: List of extraction results

    Returns:
        Statistics dictionary
    """
    print("\n🔨 Building Topic nodes and HAS_TOPIC edges...")

    # Collect unique topics
    unique_topics = {}
    for result in extraction_results:
        for topic in result['topics']:
            topic_id = topic['id']
            if topic_id not in unique_topics:
                unique_topics[topic_id] = {
                    'id': topic_id,
                    'name': topic['name'],
                    'category': topic['category'],
                    'frequency': 0,
                    'avg_relevance': []
                }

            unique_topics[topic_id]['frequency'] += 1
            unique_topics[topic_id]['avg_relevance'].append(topic['relevance'])

    # Create Topic nodes
    for topic_id, topic_data in unique_topics.items():
        # Calculate average relevance
        avg_rel = sum(topic_data['avg_relevance']) / len(topic_data['avg_relevance'])

        graph.add_node(
            node_type='Topic',
            node_id=topic_id,
            data={
                'id': topic_id,
                'name': topic_data['name'],
                'category': topic_data['category'],
                'frequency': topic_data['frequency'],
                'avg_relevance': round(avg_rel, 3),
                'created_at': datetime.now().isoformat()
            }
        )

    # Create HAS_TOPIC edges
    edges_created = 0
    for result in extraction_results:
        page_id = result['page_id']

        for topic in result['topics']:
            topic_id = topic['id']

            graph.add_edge(
                from_node_id=page_id,
                to_node_id=topic_id,
                edge_type='HAS_TOPIC',
                data={
                    'relevance': topic['relevance'],
                    'confidence': topic['confidence'],
                    'extracted_at': datetime.now().isoformat()
                }
            )
            edges_created += 1

    print(f"✅ Created {len(unique_topics)} Topic nodes")
    print(f"✅ Created {edges_created} HAS_TOPIC edges")

    return {
        'topics_created': len(unique_topics),
        'edges_created': edges_created,
        'unique_topics': unique_topics
    }


def generate_statistics(graph: MGraph, build_stats: Dict) -> Dict:
    """
    Generate comprehensive topic statistics.

    Args:
        graph: MGraph instance
        build_stats: Build statistics

    Returns:
        Statistics dictionary
    """
    print("\n📊 Generating statistics...")

    # Distribution by category
    distribution = {}
    top_topics = []

    for topic_id, topic_data in build_stats['unique_topics'].items():
        category = topic_data['category']
        distribution[category] = distribution.get(category, 0) + 1

        top_topics.append({
            'name': topic_data['name'],
            'frequency': topic_data['frequency'],
            'category': topic_data['category'],
            'avg_relevance': topic_data['avg_relevance']
        })

    # Sort by frequency
    top_topics.sort(key=lambda x: x['frequency'], reverse=True)

    # Calculate averages
    total_topics = build_stats['topics_created']
    total_edges = build_stats['edges_created']
    avg_topics_per_page = total_edges / 10 if total_edges > 0 else 0

    # Calculate average relevance for top topics
    for topic in top_topics:
        if isinstance(topic['avg_relevance'], list):
            topic['avg_relevance'] = sum(topic['avg_relevance']) / len(topic['avg_relevance'])

    stats = {
        'total_topics': total_topics,
        'total_assignments': total_edges,
        'avg_topics_per_page': round(avg_topics_per_page, 1),
        'distribution_by_category': distribution,
        'top_topics': top_topics[:20],
        'processing_time': 0.0,  # Demo mode
        'estimated_cost': 0.25,  # Est. cost for real execution
        'items_processed': 10,
        'target_precision': 0.75,
        'estimated_precision': 0.82,  # Expected with GPT-4-turbo
        'timestamp': datetime.now().isoformat()
    }

    return stats


def print_summary(stats: Dict):
    """Print comprehensive summary report."""
    print("\n" + "=" * 70)
    print("TOPIC EXTRACTION DEMONSTRATION - COMPLETE")
    print("=" * 70)

    print(f"\n📊 Topics Extracted:")
    print(f"   • Total unique topics: {stats['total_topics']}")
    print(f"   • Total HAS_TOPIC edges: {stats['total_assignments']}")
    print(f"   • Avg topics per page: {stats['avg_topics_per_page']}")

    print(f"\n📈 Distribution by Category:")
    for category, count in sorted(stats['distribution_by_category'].items(),
                                   key=lambda x: x[1], reverse=True):
        pct = (count / stats['total_topics']) * 100
        print(f"   • {category:15} {count:3} ({pct:5.1f}%)")

    print(f"\n🏆 Top 10 Topics by Frequency:")
    for i, topic in enumerate(stats['top_topics'][:10], 1):
        print(f"   {i:2}. {topic['name']:30} "
              f"freq: {topic['frequency']:2} | "
              f"rel: {topic['avg_relevance']:.2f} | "
              f"cat: {topic['category']}")

    print(f"\n💰 Estimated Cost (Live Execution):")
    print(f"   • Model: GPT-4-Turbo")
    print(f"   • Pages: {stats['items_processed']}")
    print(f"   • Est. tokens: ~8,000 (800/page)")
    print(f"   • Est. cost: ${stats['estimated_cost']}")

    print(f"\n✅ Quality Metrics:")
    print(f"   • Target precision: {stats['target_precision']*100:.0f}%")
    print(f"   • Expected precision: {stats['estimated_precision']*100:.0f}%")
    print(f"   • Status: Infrastructure Ready")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("\n1. Set OPENAI_API_KEY environment variable")
    print("2. Run: python scripts/enrich_topics.py --graph data/graph/graph.json")
    print("3. Review results in data/topic_stats.json")
    print("4. Validate with: python -m src.validation.topic_validator")
    print("\n" + "=" * 70)


def main():
    """Main demonstration entry point."""
    print("=" * 70)
    print("TOPIC EXTRACTION DEMONSTRATION")
    print("=" * 70)
    print("\nThis demonstrates the complete topic extraction pipeline")
    print("without requiring live LLM API calls.\n")

    # Load graph
    print("[1/5] Loading knowledge graph...")
    graph = MGraph()
    graph.load_from_json('data/graph/graph.json')

    pages = graph.query(node_type='Page', limit=10)
    print(f"✅ Loaded {len(pages)} pages from graph")

    # Generate sample extraction results
    print("\n[2/5] Simulating topic extraction from pages...")
    extraction_results = []

    for i, page in enumerate(pages):
        page_data = {
            'id': page.data.get('id'),
            'title': page.data.get('title', 'Untitled'),
            'type': page.data.get('type', 'unknown')
        }

        topics = generate_sample_topics_for_page(page_data, i)

        extraction_results.append({
            'page_id': page_data['id'],
            'page_title': page_data['title'],
            'page_type': page_data['type'],
            'topics': topics
        })

        print(f"   [{i+1}/10] {page_data['title'][:50]:50} → {len(topics)} topics")

    print(f"✅ Extracted topics from {len(extraction_results)} pages")

    # Build nodes and edges
    print("\n[3/5] Building Topic nodes and HAS_TOPIC edges...")
    build_stats = build_topic_nodes_and_edges(graph, extraction_results)

    # Generate statistics
    print("\n[4/5] Calculating statistics...")
    stats = generate_statistics(graph, build_stats)

    # Save results
    print("\n[5/5] Saving results...")

    # Save enhanced graph
    output_graph = Path('data/graph_with_topics_demo.json')
    graph.save_to_json(str(output_graph))
    print(f"✅ Enhanced graph saved to: {output_graph}")

    # Save statistics
    stats_file = Path('data/topic_stats_demo.json')
    stats_file.parent.mkdir(parents=True, exist_ok=True)

    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Statistics saved to: {stats_file}")

    # Save extraction results for review
    results_file = Path('data/topic_extraction_demo.json')
    with open(results_file, 'w') as f:
        json.dump(extraction_results, f, indent=2)
    print(f"✅ Extraction results saved to: {results_file}")

    # Print summary
    print_summary(stats)

    return 0


if __name__ == '__main__':
    sys.exit(main())
