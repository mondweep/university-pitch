#!/usr/bin/env python3
"""
Topic Enrichment Orchestration Script

Runs complete topic extraction and HAS_TOPIC relationship building pipeline:
1. Extract 5-10 topics per page using LLM (GPT-4-Turbo)
2. Create Topic nodes in graph
3. Build HAS_TOPIC relationships
4. Cluster topics into hierarchical groups
5. Build topic hierarchy with CHILD_OF edges
6. Calculate statistics and generate reports
7. Validate topic quality and coverage

Usage:
    python scripts/enrich_topics.py --graph data/graph/graph.json --limit 10

Environment:
    OPENAI_API_KEY - Required for LLM topic extraction
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mgraph import MGraph
from src.llm.llm_client import LLMClient
from src.enrichment.topic_extractor import TopicExtractor
from src.enrichment.has_topic_builder import HasTopicBuilder
from src.enrichment.topic_hierarchy_builder import TopicHierarchyBuilder
from src.enrichment.topic_cluster_enricher import TopicClusterEnricher
from src.validation.topic_validator import TopicValidator


def setup_logging(log_level: str = 'INFO') -> None:
    """Configure logging."""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/enrich_topics.log')
        ]
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Extract topics and build HAS_TOPIC relationships'
    )

    parser.add_argument(
        '--graph',
        type=str,
        default='data/graph/graph.json',
        help='Input graph JSON file (default: data/graph/graph.json)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of pages to process (default: 10)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4-turbo',
        choices=['gpt-4-turbo', 'gpt-3.5-turbo'],
        help='LLM model for topic extraction (default: gpt-4-turbo)'
    )

    parser.add_argument(
        '--relevance-threshold',
        type=float,
        default=0.7,
        help='Minimum relevance score to keep topic (default: 0.7)'
    )

    parser.add_argument(
        '--build-hierarchy',
        action='store_true',
        default=True,
        help='Build topic hierarchy with CHILD_OF edges'
    )

    parser.add_argument(
        '--skip-clustering',
        action='store_true',
        help='Skip topic clustering step'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Output directory for results (default: data)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    return parser.parse_args()


async def run_topic_enrichment(
    graph: MGraph,
    llm_client: LLMClient,
    args
) -> Dict:
    """
    Run complete topic enrichment pipeline.

    Steps:
    1. Extract topics from pages using LLM
    2. Create Topic nodes in graph
    3. Build HAS_TOPIC relationships
    4. Update topic statistics
    5. Build topic hierarchy (optional)
    6. Run topic clustering (optional)
    7. Validate results
    8. Generate reports

    Args:
        graph: MGraph instance
        llm_client: LLM client for topic extraction
        args: Command line arguments

    Returns:
        Dictionary of statistics and results
    """
    logger = logging.getLogger(__name__)

    print("\n" + "=" * 70)
    print("TOPIC ENRICHMENT PIPELINE - Phase 3")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  • Graph: {args.graph}")
    print(f"  • Pages to process: {args.limit}")
    print(f"  • LLM model: {args.model}")
    print(f"  • Relevance threshold: {args.relevance_threshold}")
    print(f"  • Build hierarchy: {args.build_hierarchy}")
    print(f"  • Run clustering: {not args.skip_clustering}")
    print()

    start_time = datetime.now()
    results = {
        'success': False,
        'start_time': start_time.isoformat(),
        'steps_completed': []
    }

    try:
        # Step 1: Extract topics from pages
        print("\n[STEP 1/7] Extracting topics from pages using LLM...")
        print("-" * 70)

        extractor = TopicExtractor(
            llm_client=llm_client,
            graph=graph,
            relevance_threshold=args.relevance_threshold,
            max_topics_per_page=10,
            min_topics_per_page=5
        )

        extraction_results = await extractor.extract_topics_from_pages(
            limit=args.limit
        )

        if not extraction_results:
            logger.error("No topics extracted from pages")
            results['error'] = "No topics extracted"
            return results

        results['extraction_results'] = len(extraction_results)
        results['steps_completed'].append('extraction')

        print(f"✅ Extracted topics from {len(extraction_results)} pages")

        # Get extraction statistics
        extractor_stats = extractor.get_stats()
        print(f"   • Unique topics discovered: {extractor_stats['unique_topics']}")

        # Step 2: Build HAS_TOPIC relationships
        print("\n[STEP 2/7] Building HAS_TOPIC relationships...")
        print("-" * 70)

        builder = HasTopicBuilder(graph)
        build_stats = builder.build_from_extraction_results(extraction_results)

        results['topics_created'] = build_stats['topics_created']
        results['edges_created'] = build_stats['edges_created']
        results['steps_completed'].append('relationships')

        print(f"✅ Created {build_stats['topics_created']} Topic nodes")
        print(f"✅ Created {build_stats['edges_created']} HAS_TOPIC edges")

        # Step 3: Update topic statistics
        print("\n[STEP 3/7] Updating topic statistics...")
        print("-" * 70)

        stats_update = builder.update_topic_statistics()

        results['topics_updated'] = stats_update.get('topics_updated', 0)
        results['steps_completed'].append('statistics')

        print(f"✅ Updated statistics for {stats_update.get('topics_updated', 0)} topics")

        # Step 4: Get topic distribution
        print("\n[STEP 4/7] Calculating topic distribution...")
        print("-" * 70)

        distribution = builder.get_topic_distribution()
        top_topics = builder.get_top_topics(limit=20)

        results['distribution'] = distribution
        results['top_topics'] = top_topics
        results['steps_completed'].append('distribution')

        print(f"✅ Topics by category:")
        for category, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {category}: {count}")

        print(f"\n   Top 10 topics by frequency:")
        for i, topic in enumerate(top_topics[:10], 1):
            print(f"   {i}. {topic['name']} (frequency: {topic.get('frequency', 0)})")

        # Step 5: Build topic hierarchy (optional)
        hierarchy_stats = {}
        if args.build_hierarchy:
            print("\n[STEP 5/7] Building topic hierarchy...")
            print("-" * 70)

            hierarchy_builder = TopicHierarchyBuilder(graph)
            hierarchy_stats = hierarchy_builder.build_hierarchy()

            results['hierarchy'] = hierarchy_stats
            results['steps_completed'].append('hierarchy')

            print(f"✅ Hierarchy built:")
            print(f"   • Root topics: {hierarchy_stats.get('root_topics', 0)}")
            print(f"   • Hierarchy edges: {hierarchy_stats.get('hierarchy_edges', 0)}")
            print(f"   • Max depth: {hierarchy_stats.get('max_depth', 0)} levels")
        else:
            print("\n[STEP 5/7] Skipping hierarchy build (disabled)")
            results['steps_completed'].append('hierarchy_skipped')

        # Step 6: Run topic clustering (optional)
        cluster_stats = {}
        if not args.skip_clustering:
            print("\n[STEP 6/7] Running topic clustering...")
            print("-" * 70)

            enricher = TopicClusterEnricher(
                graph_path=args.graph,
                openai_api_key=llm_client.api_key
            )

            async with enricher:
                cluster_results = await enricher.run(
                    output_dir=args.output_dir,
                    reports_dir='docs'
                )

                cluster_stats = cluster_results
                results['clustering'] = cluster_stats
                results['steps_completed'].append('clustering')

            print(f"✅ Clustering completed:")
            print(f"   • Clusters created: {cluster_stats.get('clusters_created', 0)}")
            print(f"   • Subtopic edges: {cluster_stats.get('subtopic_edges', 0)}")
            print(f"   • Related edges: {cluster_stats.get('related_edges', 0)}")
        else:
            print("\n[STEP 6/7] Skipping clustering (disabled)")
            results['steps_completed'].append('clustering_skipped')

        # Step 7: Validate results
        print("\n[STEP 7/7] Validating results...")
        print("-" * 70)

        validator = TopicValidator(graph)
        validation_report = validator.validate()

        results['validation'] = validation_report
        results['steps_completed'].append('validation')

        print(f"✅ Validation completed:")
        print(f"   • Topics validated: {validation_report.get('total_topics', 0)}")
        print(f"   • Coverage: {validation_report.get('coverage_pct', 0):.1f}%")
        print(f"   • Avg quality score: {validation_report.get('avg_quality_score', 0):.2f}")

        # Calculate final statistics
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        llm_stats = llm_client.get_stats()

        results.update({
            'success': True,
            'end_time': end_time.isoformat(),
            'processing_time_seconds': processing_time,
            'pages_processed': len(extraction_results),
            'avg_topics_per_page': build_stats['edges_created'] / len(extraction_results) if extraction_results else 0,
            'llm_api_calls': llm_stats['api_calls'],
            'llm_total_tokens': llm_stats['total_tokens'],
            'llm_total_cost': llm_stats['total_cost'],
            'llm_avg_tokens_per_call': llm_stats['avg_tokens_per_call']
        })

        # Print final summary
        print("\n" + "=" * 70)
        print("ENRICHMENT SUMMARY")
        print("=" * 70)

        print(f"\n📊 Topics:")
        print(f"   • Total unique topics: {results['topics_created']}")
        print(f"   • Total HAS_TOPIC edges: {results['edges_created']}")
        print(f"   • Avg topics per page: {results['avg_topics_per_page']:.1f}")

        if hierarchy_stats:
            print(f"\n🏗️  Hierarchy:")
            print(f"   • Root topics: {hierarchy_stats.get('root_topics', 0)}")
            print(f"   • Hierarchy depth: {hierarchy_stats.get('max_depth', 0)} levels")

        if cluster_stats:
            print(f"\n🔗 Clustering:")
            print(f"   • Clusters: {cluster_stats.get('clusters_created', 0)}")
            print(f"   • Relationships: {cluster_stats.get('subtopic_edges', 0) + cluster_stats.get('related_edges', 0)}")

        print(f"\n💰 LLM Usage:")
        print(f"   • Model: {args.model}")
        print(f"   • API calls: {llm_stats['api_calls']}")
        print(f"   • Total tokens: {llm_stats['total_tokens']:,}")
        print(f"   • Total cost: ${llm_stats['total_cost']:.2f}")
        print(f"   • Avg tokens/call: {llm_stats['avg_tokens_per_call']:.0f}")

        print(f"\n⏱️  Processing:")
        print(f"   • Total time: {processing_time:.1f}s")
        print(f"   • Avg time per page: {processing_time / len(extraction_results):.1f}s")

        print(f"\n✅ Validation:")
        print(f"   • Coverage: {validation_report.get('coverage_pct', 0):.1f}%")
        print(f"   • Quality score: {validation_report.get('avg_quality_score', 0):.2f}/1.0")

        print("\n" + "=" * 70)

        return results

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        results['success'] = False
        results['error'] = str(e)
        return results


async def main():
    """Main entry point."""
    args = parse_args()

    # Setup logging
    Path('logs').mkdir(exist_ok=True)
    setup_logging(args.log_level)

    logger = logging.getLogger(__name__)

    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        print("\n❌ Error: OPENAI_API_KEY not found in environment")
        print("   Please set it: export OPENAI_API_KEY='your-key-here'")
        return 1

    # Verify graph file exists
    graph_path = Path(args.graph)
    if not graph_path.exists():
        logger.error(f"Graph file not found: {graph_path}")
        print(f"\n❌ Error: Graph file not found: {graph_path}")
        return 1

    try:
        # Initialize components
        logger.info(f"Loading graph from {graph_path}")
        graph = MGraph(str(graph_path))

        logger.info(f"Initializing LLM client with model: {args.model}")
        llm_client = LLMClient(
            api_key=api_key,
            model=args.model
        )

        # Run enrichment pipeline
        results = await run_topic_enrichment(graph, llm_client, args)

        if not results['success']:
            logger.error(f"Pipeline failed: {results.get('error', 'Unknown error')}")
            print(f"\n❌ Pipeline failed: {results.get('error', 'Unknown error')}")
            return 1

        # Save results
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save statistics
        stats_file = output_dir / 'topic_stats.json'
        with open(stats_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Statistics saved to {stats_file}")
        print(f"\n📄 Statistics saved to: {stats_file}")

        # Save enriched graph
        graph.save()
        logger.info(f"Graph saved to {graph_path}")
        print(f"💾 Graph saved to: {graph_path}")

        print("\n✅ Topic enrichment completed successfully!")

        return 0

    except Exception as e:
        logger.error(f"Execution error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
