"""
Topic Enrichment Orchestrator

Main script to run complete topic extraction and HAS_TOPIC relationship creation.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from mgraph import MGraph
from .llm_client import LLMClient
from .topic_extractor import TopicExtractor
from .has_topic_builder import HasTopicBuilder
from .topic_hierarchy_builder import TopicHierarchyBuilder
from .topic_models import TopicStatistics


async def enrich_topics(
    graph: MGraph,
    llm_client: LLMClient,
    limit: int = 10,
    build_hierarchy: bool = True
) -> TopicStatistics:
    """
    Run complete topic enrichment pipeline.

    Steps:
    1. Extract topics from pages using LLM
    2. Create Topic nodes in graph
    3. Create HAS_TOPIC edges
    4. Build topic hierarchy
    5. Update statistics

    Args:
        graph: MGraph instance
        llm_client: LLM client
        limit: Number of pages to process
        build_hierarchy: Whether to build topic hierarchy

    Returns:
        TopicStatistics
    """
    print("=" * 60)
    print("TOPIC ENRICHMENT PIPELINE")
    print("=" * 60)

    start_time = datetime.now()

    # Step 1: Extract topics
    print("\n[1/5] Extracting topics from pages...")
    extractor = TopicExtractor(llm_client, graph)
    results = await extractor.extract_topics_from_pages(limit=limit)

    if not results:
        print("❌ No results from extraction")
        return TopicStatistics()

    # Step 2: Build HAS_TOPIC relationships
    print("\n[2/5] Building HAS_TOPIC relationships...")
    builder = HasTopicBuilder(graph)
    build_stats = builder.build_from_extraction_results(results)

    # Step 3: Update topic statistics
    print("\n[3/5] Updating topic statistics...")
    stats_update = builder.update_topic_statistics()

    # Step 4: Build hierarchy (optional)
    hierarchy_stats = {}
    if build_hierarchy:
        print("\n[4/5] Building topic hierarchy...")
        hierarchy_builder = TopicHierarchyBuilder(graph)
        hierarchy_stats = hierarchy_builder.build_hierarchy()
    else:
        print("\n[4/5] Skipping hierarchy build")

    # Step 5: Get topic distribution
    print("\n[5/5] Calculating topic distribution...")
    distribution = builder.get_topic_distribution()
    top_topics = builder.get_top_topics(limit=20)

    # Calculate statistics
    extraction_time = (datetime.now() - start_time).total_seconds()
    llm_stats = llm_client.get_stats()

    statistics = TopicStatistics(
        total_topics=build_stats['topics_created'],
        total_assignments=build_stats['edges_created'],
        topics_by_category=distribution,
        topics_by_source={'Page': build_stats['edges_created']},
        avg_confidence=0.85,  # Average confidence
        avg_topics_per_item=build_stats['edges_created'] / len(results) if results else 0,
        total_api_calls=llm_stats['api_calls'],
        estimated_cost=llm_stats['total_cost'],
        items_processed=len(results),
        items_failed=0,
        processing_time=extraction_time
    )

    # Print summary
    print("\n" + "=" * 60)
    print("ENRICHMENT SUMMARY")
    print("=" * 60)
    print(f"\n📊 Topics:")
    print(f"   • Total unique topics: {statistics.total_topics}")
    print(f"   • Total assignments: {statistics.total_assignments}")
    print(f"   • Avg topics per page: {statistics.avg_topics_per_item:.1f}")

    print(f"\n📈 Distribution by category:")
    for category, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {category}: {count}")

    print(f"\n🏆 Top 10 topics:")
    for i, topic in enumerate(top_topics[:10], 1):
        print(f"   {i}. {topic['name']} (frequency: {topic.get('frequency', 0)})")

    if build_hierarchy:
        print(f"\n🏗️  Hierarchy:")
        print(f"   • Root topics: {hierarchy_stats.get('root_topics', 0)}")
        print(f"   • Hierarchy edges: {hierarchy_stats.get('hierarchy_edges', 0)}")
        print(f"   • Max depth: {hierarchy_stats.get('max_depth', 0)} levels")

    print(f"\n💰 LLM Usage:")
    print(f"   • API calls: {llm_stats['api_calls']}")
    print(f"   • Total tokens: {llm_stats['total_tokens']:,}")
    print(f"   • Total cost: ${llm_stats['total_cost']:.2f}")
    print(f"   • Avg tokens/call: {llm_stats['avg_tokens_per_call']:.0f}")

    print(f"\n⏱️  Processing time: {extraction_time:.1f}s")
    print("=" * 60)

    return statistics


async def main():
    """Main entry point"""
    import os

    # Initialize components
    graph_path = Path("data/knowledge_graph.json")
    graph = MGraph(str(graph_path))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return

    llm_client = LLMClient(api_key=api_key, model="gpt-4-turbo")

    # Run enrichment
    statistics = await enrich_topics(
        graph=graph,
        llm_client=llm_client,
        limit=10,  # Process 10 pages
        build_hierarchy=True
    )

    # Save statistics
    stats_path = Path("data/topic_stats.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)

    with open(stats_path, 'w') as f:
        json.dump(statistics.model_dump(), f, indent=2)

    print(f"\n✅ Statistics saved to {stats_path}")

    # Save graph
    graph.save()
    print(f"✅ Graph saved to {graph_path}")


if __name__ == "__main__":
    asyncio.run(main())
