#!/usr/bin/env python3
"""
CLI script to enrich knowledge graph with semantic similarity relationships

Generates embeddings, calculates similarities, and creates RELATED_TO edges
between semantically similar pages in the knowledge graph.

Usage:
    python scripts/enrich_similarity.py --graph data/graph.json
    python scripts/enrich_similarity.py --graph data/graph.json --output data/enriched_graph.json
    python scripts/enrich_similarity.py --graph data/graph.json --threshold 0.8 --top-k 10
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enrichment.similarity_enricher import SimilarityEnricher
from enrichment.embedding_generator import EmbeddingConfig
from enrichment.similarity_calculator import SimilarityConfig
from enrichment.related_to_builder import EdgeConfig


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Enrich knowledge graph with semantic similarity relationships"
    )

    # Input/Output
    parser.add_argument(
        "--graph",
        type=Path,
        required=True,
        help="Path to input graph JSON file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to save enriched graph (default: adds _with_similarity suffix)"
    )
    parser.add_argument(
        "--stats",
        type=Path,
        help="Path to save statistics JSON (default: data/similarity_stats.json)"
    )

    # Embedding configuration
    parser.add_argument(
        "--model",
        default="text-embedding-ada-002",
        help="OpenAI embedding model (default: text-embedding-ada-002)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for embedding generation (default: 100)"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".cache/embeddings"),
        help="Directory for embedding cache (default: .cache/embeddings)"
    )

    # Similarity configuration
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Minimum similarity threshold for creating edges (default: 0.7)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of top similar pages to link per page (default: 5)"
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.5,
        help="Minimum similarity to consider (default: 0.5)"
    )

    # Edge configuration
    parser.add_argument(
        "--max-edges",
        type=int,
        default=5,
        help="Maximum edges per page (default: 5)"
    )
    parser.add_argument(
        "--require-shared-topics",
        action="store_true",
        help="Only create edges between pages with shared topics"
    )
    parser.add_argument(
        "--min-shared-topics",
        type=int,
        default=1,
        help="Minimum number of shared topics (default: 1)"
    )
    parser.add_argument(
        "--no-reasoning",
        action="store_true",
        help="Don't generate reasoning for edges"
    )

    # Other options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without saving results"
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("Starting similarity enrichment")
    logger.info(f"Input graph: {args.graph}")

    # Validate input file
    if not args.graph.exists():
        logger.error(f"Input graph file not found: {args.graph}")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Add _with_similarity suffix
        output_path = args.graph.parent / f"{args.graph.stem}_with_similarity.json"

    logger.info(f"Output graph: {output_path}")

    # Determine stats path
    if args.stats:
        stats_path = args.stats
    else:
        stats_path = Path("data/similarity_stats.json")

    logger.info(f"Statistics: {stats_path}")

    # Check for API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        logger.error(
            "OPENAI_API_KEY environment variable not set. "
            "Please set it to use OpenAI embeddings."
        )
        sys.exit(1)

    # Create configurations
    embedding_config = EmbeddingConfig(
        model=args.model,
        batch_size=args.batch_size,
        cache_dir=args.cache_dir
    )

    similarity_config = SimilarityConfig(
        similarity_threshold=args.threshold,
        top_k=args.top_k,
        min_similarity=args.min_similarity,
        max_similarities_per_page=args.max_edges
    )

    edge_config = EdgeConfig(
        min_similarity=args.threshold,
        max_edges_per_page=args.max_edges,
        require_shared_topics=args.require_shared_topics,
        min_shared_topics=args.min_shared_topics,
        add_reasoning=not args.no_reasoning
    )

    # Create enricher
    enricher = SimilarityEnricher(
        embedding_config=embedding_config,
        similarity_config=similarity_config,
        edge_config=edge_config
    )

    try:
        if args.dry_run:
            logger.info("DRY RUN - No files will be saved")

            # Load and process graph
            with open(args.graph, 'r') as f:
                graph = json.load(f)

            enriched_graph = enricher.enrich_graph(graph)

            # Print summary
            enricher.print_summary()

        else:
            # Process and save
            enriched_graph = enricher.enrich_graph_from_file(
                input_path=args.graph,
                output_path=output_path,
                stats_path=stats_path
            )

            # Print summary
            enricher.print_summary()

            logger.info(f"\n✓ Enriched graph saved to: {output_path}")
            logger.info(f"✓ Statistics saved to: {stats_path}")

        logger.info("\nSimilarity enrichment completed successfully!")

    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during enrichment: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
