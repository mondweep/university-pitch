#!/usr/bin/env python3
"""
Topic Clustering and Hierarchy Enrichment CLI

Orchestrates Phase 3 topic clustering pipeline:
1. Load graph with topics (requires prior topic extraction)
2. Cluster topics by co-occurrence patterns
3. Build parent-child topic hierarchy
4. Create CHILD_OF edges in graph
5. Generate visualizations (Mermaid diagrams)
6. Export enriched graph and statistics

Usage:
    python scripts/enrich_topic_clusters.py --graph data/checkpoints/graph_with_similarity.json
    python scripts/enrich_topic_clusters.py --graph data/graph.json --clusters 5 --output-dir docs

Cost: $0 (pure graph analysis, no API calls)
Time: ~1 minute for 20-30 topics
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enrichment.topic_cluster_enricher import TopicClusterEnricher


def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """Configure logging."""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'

    # Create logs directory if it doesn't exist
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / 'enrich_topic_clusters.log')
        ]
    )

    return logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Cluster topics and build hierarchy in knowledge graph',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage with default parameters
    python scripts/enrich_topic_clusters.py --graph data/graph.json

    # Custom number of clusters
    python scripts/enrich_topic_clusters.py --graph data/graph.json --clusters 5

    # Custom output directory
    python scripts/enrich_topic_clusters.py --graph data/graph.json --output-dir docs

    # All parameters
    python scripts/enrich_topic_clusters.py \\
        --graph data/graph.json \\
        --clusters 5 \\
        --confidence 0.6 \\
        --similarity 0.3 \\
        --output-dir docs \\
        --output-graph data/graph_with_clusters.json

Notes:
    - Requires prior topic extraction (Topic nodes must exist in graph)
    - Cost: $0 (pure graph analysis)
    - Time: ~1 minute for 20-30 topics
    - Generates: Mermaid diagrams, statistics JSON, enriched graph
        """
    )

    parser.add_argument(
        '--graph',
        type=str,
        required=True,
        help='Input graph JSON file with Topic nodes (required)'
    )

    parser.add_argument(
        '--clusters',
        type=int,
        default=5,
        help='Target number of clusters (default: 5, recommended: 3-5)'
    )

    parser.add_argument(
        '--confidence',
        type=float,
        default=0.6,
        help='Minimum confidence threshold for CHILD_OF edges (default: 0.6)'
    )

    parser.add_argument(
        '--similarity',
        type=float,
        default=0.3,
        help='Minimum similarity threshold for clustering (default: 0.3)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='docs',
        help='Output directory for visualizations and reports (default: docs)'
    )

    parser.add_argument(
        '--output-graph',
        type=str,
        default='data/graph_with_clusters.json',
        help='Output path for enriched graph (default: data/graph_with_clusters.json)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    return parser.parse_args()


def validate_input_graph(graph_path: str, logger: logging.Logger) -> bool:
    """
    Validate that input graph exists and contains Topic nodes.

    Args:
        graph_path: Path to graph JSON
        logger: Logger instance

    Returns:
        True if valid, False otherwise
    """
    # Check file exists
    if not Path(graph_path).exists():
        logger.error(f"Input graph not found: {graph_path}")
        return False

    # Load and check for Topic nodes
    try:
        with open(graph_path, 'r') as f:
            graph = json.load(f)

        n_topics = sum(
            1 for node in graph.get('nodes', [])
            if node.get('node_type') == 'Topic'
        )

        if n_topics == 0:
            logger.error(
                f"No Topic nodes found in graph. "
                f"Please run topic extraction first: "
                f"python scripts/enrich_topics.py --graph {graph_path}"
            )
            return False

        logger.info(f"Input graph validated: {n_topics} Topic nodes found")
        return True

    except Exception as e:
        logger.error(f"Failed to validate input graph: {e}")
        return False


def generate_summary_report(stats: dict, output_dir: str, logger: logging.Logger) -> None:
    """
    Generate human-readable summary report.

    Args:
        stats: Pipeline statistics dictionary
        output_dir: Output directory for report
        logger: Logger instance
    """
    output_path = Path(output_dir) / 'TOPIC_HIERARCHY.md'

    with open(output_path, 'w') as f:
        f.write("# Topic Hierarchy Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        # Summary
        f.write("## Summary\n\n")

        if stats.get('success'):
            clustering = stats.get('clustering', {})
            hierarchy = stats.get('hierarchy', {})

            f.write(f"✅ **Pipeline Status:** COMPLETE\n\n")
            f.write(f"- **Duration:** {stats['duration_seconds']:.2f} seconds\n")
            f.write(f"- **Clusters Created:** {clustering.get('n_clusters', 0)}\n")
            f.write(f"- **Average Cluster Size:** {clustering.get('avg_cluster_size', 0):.2f} topics\n")
            f.write(f"- **Average Coherence:** {clustering.get('avg_coherence', 0):.3f}\n")
            f.write(f"- **Hierarchy Edges:** {hierarchy.get('n_relationships', 0)} CHILD_OF edges\n")
            f.write(f"- **Maximum Depth:** {hierarchy.get('max_depth', 0)} levels\n")
            f.write(f"- **Average Confidence:** {hierarchy.get('avg_confidence', 0):.3f}\n\n")

            # Files generated
            f.write("## Generated Files\n\n")
            files = stats.get('files_generated', {})
            for file_type, file_path in files.items():
                f.write(f"- `{file_path}` - {file_type}\n")
            f.write("\n")

            # Visualization
            f.write("## Topic Hierarchy Visualization\n\n")
            mermaid_path = files.get('mermaid')
            if mermaid_path and Path(mermaid_path).exists():
                with open(mermaid_path, 'r') as mmd:
                    f.write("```mermaid\n")
                    f.write(mmd.read())
                    f.write("\n```\n\n")
            else:
                f.write("*Mermaid diagram not available*\n\n")

            # Next steps
            f.write("## Next Steps\n\n")
            f.write("1. Review topic hierarchy and validate relationships\n")
            f.write("2. Visualize enriched graph using Mermaid rendering\n")
            f.write("3. Proceed to next Phase 3 enrichments (NER, personas, etc.)\n")

        else:
            f.write(f"❌ **Pipeline Status:** FAILED\n\n")
            f.write(f"**Error:** {stats.get('error', 'Unknown error')}\n\n")

    logger.info(f"Generated summary report: {output_path}")


def main() -> int:
    """Main execution function."""
    args = parse_args()
    logger = setup_logging(args.log_level)

    logger.info("=" * 70)
    logger.info("TOPIC CLUSTERING & HIERARCHY ENRICHMENT")
    logger.info("=" * 70)
    logger.info(f"Input graph: {args.graph}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Output graph: {args.output_graph}")
    logger.info(f"Target clusters: {args.clusters}")
    logger.info(f"Confidence threshold: {args.confidence}")
    logger.info(f"Similarity threshold: {args.similarity}")
    logger.info("=" * 70)

    # Validate input
    if not validate_input_graph(args.graph, logger):
        return 1

    try:
        # Initialize enricher
        enricher = TopicClusterEnricher(
            n_clusters=args.clusters,
            confidence_threshold=args.confidence,
            similarity_threshold=args.similarity
        )

        # Run pipeline
        stats = enricher.run_pipeline(
            graph_path=args.graph,
            output_dir=args.output_dir,
            output_graph=args.output_graph
        )

        # Generate summary report
        generate_summary_report(stats, args.output_dir, logger)

        if stats.get('success'):
            logger.info("✅ Topic clustering enrichment complete!")
            return 0
        else:
            logger.error(f"❌ Pipeline failed: {stats.get('error')}")
            return 1

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
