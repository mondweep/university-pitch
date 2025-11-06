#!/usr/bin/env python3
"""
Similarity Enrichment Script
Orchestrates the complete similarity calculation and RELATED_TO relationship building.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enrichment.embedding_generator import EmbeddingGenerator
from enrichment.similarity_calculator import SimilarityCalculator
from enrichment.similarity_enricher import SimilarityEnricher
from graph.graph_loader import GraphLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/similarity_enrichment.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Run similarity enrichment pipeline."""

    logger.info("=" * 80)
    logger.info("SIMILARITY ENRICHMENT PIPELINE")
    logger.info("=" * 80)

    start_time = datetime.now()

    # Configuration
    config = {
        'api_key': os.getenv('OPENAI_API_KEY'),
        'embedding_model': 'text-embedding-3-small',
        'graph_path': 'data/graph/graph.json',
        'output_dir': 'data/enrichment/similarity',
        'top_k': 5,
        'threshold': 0.7,
        'use_multi_signal': True,
        'use_ann': True,
        'node_types': ['Page']
    }

    # Validate API key
    if not config['api_key']:
        logger.error("OPENAI_API_KEY environment variable not set")
        logger.error("Please set: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)

    logger.info("Configuration:")
    for key, value in config.items():
        if key != 'api_key':
            logger.info(f"  {key}: {value}")

    # Create output directory
    output_dir = Path(config['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Load graph
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1: Loading knowledge graph")
    logger.info("=" * 80)

    graph_loader = GraphLoader()
    graph = graph_loader.load(config['graph_path'])

    logger.info(f"Loaded graph with {len(graph.get_all_nodes())} nodes")

    # Count nodes by type
    node_counts = {}
    for node_id in graph.get_all_nodes():
        node = graph.get_node(node_id)
        node_type = node.get('type', 'Unknown')
        node_counts[node_type] = node_counts.get(node_type, 0) + 1

    logger.info("Node counts by type:")
    for node_type, count in sorted(node_counts.items()):
        logger.info(f"  {node_type}: {count}")

    # Step 2: Initialize embedding generator
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Initializing embedding generator")
    logger.info("=" * 80)

    embedding_gen = EmbeddingGenerator(
        api_key=config['api_key'],
        model=config['embedding_model']
    )

    logger.info(f"Initialized with model: {config['embedding_model']}")

    # Step 3: Initialize similarity calculator
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: Initializing similarity calculator")
    logger.info("=" * 80)

    similarity_calc = SimilarityCalculator(
        embedding_weight=0.6,
        topic_weight=0.3,
        entity_weight=0.1
    )

    # Step 4: Initialize similarity enricher
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: Initializing similarity enricher")
    logger.info("=" * 80)

    enricher = SimilarityEnricher(
        graph=graph,
        embedding_generator=embedding_gen,
        similarity_calculator=similarity_calc,
        top_k=config['top_k'],
        threshold=config['threshold'],
        use_multi_signal=config['use_multi_signal']
    )

    # Step 5: Run enrichment
    logger.info("\n" + "=" * 80)
    logger.info("STEP 5: Running similarity enrichment")
    logger.info("=" * 80)

    try:
        results = await enricher.enrich(
            node_types=config['node_types'],
            use_ann=config['use_ann'],
            export_results=True,
            output_dir=output_dir
        )

        # Step 6: Display results
        logger.info("\n" + "=" * 80)
        logger.info("STEP 6: Enrichment Results")
        logger.info("=" * 80)

        logger.info(f"Nodes processed: {results['nodes_processed']}")
        logger.info(f"Similarities calculated: {results['similarities_calculated']}")
        logger.info(f"Edges created: {results['edges_created']}")
        logger.info(f"Duration: {results['duration_seconds']:.1f}s")

        logger.info("\nStatistics:")
        stats = results['statistics']
        logger.info(f"  Total RELATED_TO edges: {stats['total_edges']}")
        logger.info(f"  Average similarity: {stats['average_similarity']:.3f}")
        logger.info(f"  Min similarity: {stats['min_similarity']:.3f}")
        logger.info(f"  Max similarity: {stats['max_similarity']:.3f}")

        logger.info("\nEdges by similarity type:")
        for sim_type, count in stats['by_type'].items():
            logger.info(f"  {sim_type}: {count}")

        # Step 7: Save enriched graph
        logger.info("\n" + "=" * 80)
        logger.info("STEP 7: Saving enriched graph")
        logger.info("=" * 80)

        enriched_graph_path = Path('data/graph/graph_with_similarity.json')
        enriched_graph_path.parent.mkdir(parents=True, exist_ok=True)

        graph_loader.save(graph, str(enriched_graph_path))

        logger.info(f"Saved enriched graph to: {enriched_graph_path}")

        # Calculate cost estimate
        logger.info("\n" + "=" * 80)
        logger.info("Cost Estimate")
        logger.info("=" * 80)

        # Estimate tokens (rough approximation)
        avg_text_length = 200  # chars per node
        tokens_per_node = avg_text_length / 4  # rough token estimate
        total_tokens = results['nodes_processed'] * tokens_per_node

        # OpenAI text-embedding-3-small pricing: $0.00002 per 1K tokens
        cost_per_1k_tokens = 0.00002
        estimated_cost = (total_tokens / 1000) * cost_per_1k_tokens

        logger.info(f"Estimated tokens: {total_tokens:,.0f}")
        logger.info(f"Estimated cost: ${estimated_cost:.4f}")

        # Success summary
        duration = (datetime.now() - start_time).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("SIMILARITY ENRICHMENT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total duration: {duration:.1f}s")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Enriched graph: {enriched_graph_path}")

        logger.info("\n✅ Similarity enrichment completed successfully!")

    except Exception as e:
        logger.error(f"\n❌ Error during enrichment: {e}", exc_info=True)
        sys.exit(1)

    finally:
        # Cleanup
        await embedding_gen.close()


if __name__ == '__main__':
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)

    # Run async main
    asyncio.run(main())
