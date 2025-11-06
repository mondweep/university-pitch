#!/usr/bin/env python3
"""
Master Script: Topic Clustering and Hierarchy Enrichment

Orchestrates Phase 3 topic clustering pipeline:
1. Load graph with topics from Phase 2
2. Generate topic embeddings
3. Cluster topics hierarchically
4. Build parent-child topic hierarchy
5. Create SUBTOPIC_OF and RELATED_TOPIC edges
6. Calculate topic centrality scores
7. Generate analysis reports and visualizations
8. Export enriched graph

Usage:
    python scripts/enrich_topic_clusters.py --graph data/graph/graph.json
"""

import asyncio
import argparse
import logging
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.enrichment.topic_cluster_enricher import TopicClusterEnricher


def setup_logging(log_level: str = 'INFO') -> None:
    """Configure logging."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/enrich_topic_clusters.log')
        ]
    )


def load_env_vars() -> dict:
    """Load environment variables from .env file."""
    env_vars = {}

    env_file = project_root / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

    return env_vars


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Enrich knowledge graph with topic clusters and hierarchy'
    )

    parser.add_argument(
        '--graph',
        type=str,
        default='data/graph/graph.json',
        help='Input graph JSON file (default: data/graph/graph.json)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/graph',
        help='Output directory for enriched graph (default: data/graph)'
    )

    parser.add_argument(
        '--reports-dir',
        type=str,
        default='docs',
        help='Output directory for reports (default: docs)'
    )

    parser.add_argument(
        '--similarity-threshold',
        type=float,
        default=0.7,
        help='Similarity threshold for SUBTOPIC_OF edges (default: 0.7)'
    )

    parser.add_argument(
        '--related-threshold',
        type=float,
        default=0.6,
        help='Similarity threshold for RELATED_TOPIC edges (default: 0.6)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    return parser.parse_args()


async def generate_visualization_report(
    output_path: str,
    results: dict,
    enricher: TopicClusterEnricher
) -> None:
    """
    Generate comprehensive visualization report in Markdown.

    Args:
        output_path: Output file path
        results: Pipeline results
        enricher: TopicClusterEnricher instance
    """
    from pathlib import Path

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write("# Topic Hierarchy and Clustering Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        # Summary statistics
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total Topics**: {results['topics_processed']}\n")
        f.write(f"- **Topic Clusters**: {results['clusters_created']}\n")
        f.write(f"- **Root Topics**: {results['root_topics']}\n")
        f.write(f"- **Hierarchy Depth**: {results['hierarchy_depth']}\n")
        f.write(f"- **SUBTOPIC_OF Edges**: {results['subtopic_edges']}\n")
        f.write(f"- **RELATED_TOPIC Edges**: {results['related_edges']}\n")
        f.write(f"- **Trending Topics**: {results['trending_topics']}\n")
        f.write(f"- **Niche Topics**: {results['niche_topics']}\n\n")

        # Topic hierarchy diagram
        f.write("## Topic Hierarchy\n\n")
        f.write("Topic hierarchy showing parent-child relationships:\n\n")

        # Include Mermaid diagram from topic_hierarchy.mmd
        hierarchy_mmd = output_path.parent / 'topic_hierarchy.mmd'
        if hierarchy_mmd.exists():
            with open(hierarchy_mmd) as mmd_file:
                mmd_content = mmd_file.read()
                # Extract just the mermaid block
                if '```mermaid' in mmd_content:
                    f.write(mmd_content)
                else:
                    f.write("```mermaid\n")
                    f.write(mmd_content)
                    f.write("\n```\n")
        else:
            f.write("*Hierarchy diagram not generated*\n")

        f.write("\n")

        # Analysis results
        f.write("## Topic Analysis\n\n")

        # Load analysis report
        analysis_json = output_path.parent / 'topic_analysis.json'
        if analysis_json.exists():
            with open(analysis_json) as json_file:
                analysis = json.load(json_file)

                # Distribution
                f.write("### Distribution\n\n")
                dist = analysis.get('distribution', {})
                f.write(f"- Total topics: {dist.get('total_topics', 0)}\n")
                f.write(f"- Average frequency: {dist.get('avg_frequency', 0):.2f}\n")
                f.write(f"- Median frequency: {dist.get('median_frequency', 0):.2f}\n")
                f.write(f"- Unique topics (freq=1): {dist.get('unique_topics', 0)}\n")
                f.write(f"- Common topics (freq≥5): {dist.get('common_topics', 0)}\n\n")

                # Diversity
                f.write("### Diversity\n\n")
                div = analysis.get('diversity', {})
                f.write(f"- Topic coverage: {div.get('topic_coverage', 0):.1%}\n")
                f.write(f"- Avg topics per page: {div.get('avg_topics_per_page', 0):.2f}\n")
                f.write(f"- Normalized entropy: {div.get('normalized_entropy', 0):.3f}\n\n")

                # Trending topics
                f.write("### Top 10 Trending Topics\n\n")
                trending = analysis.get('trending_topics', [])[:10]
                if trending:
                    f.write("| Rank | Topic | Frequency | Centrality | Co-occurrence |\n")
                    f.write("|------|-------|-----------|------------|---------------|\n")
                    for i, topic in enumerate(trending, 1):
                        f.write(
                            f"| {i} | {topic['name']} | {topic['frequency']} | "
                            f"{topic['centrality']:.3f} | {topic['co_occurrence']} |\n"
                        )
                else:
                    f.write("*No trending topics found*\n")

                f.write("\n")

                # Niche topics
                f.write("### Top 10 Niche Topics\n\n")
                niche = analysis.get('niche_topics', [])[:10]
                if niche:
                    f.write("| Rank | Topic | Frequency | Position | Centrality |\n")
                    f.write("|------|-------|-----------|----------|------------|\n")
                    for i, topic in enumerate(niche, 1):
                        f.write(
                            f"| {i} | {topic['name']} | {topic['frequency']} | "
                            f"{topic['avg_position']:.2f} | {topic['centrality']:.3f} |\n"
                        )
                else:
                    f.write("*No niche topics found*\n")

        f.write("\n")

        # Files generated
        f.write("## Generated Files\n\n")
        f.write("- `data/graph/graph_enriched.json` - Enriched graph (JSON format)\n")
        f.write("- `data/graph/graph_enriched.cypher` - Cypher script for Neo4j\n")
        f.write("- `data/graph/graph_enriched.graphml` - GraphML for Gephi\n")
        f.write("- `data/graph/graph_enriched.mmd` - Mermaid diagram\n")
        f.write("- `docs/topic_analysis.json` - Topic analysis report\n")
        f.write("- `docs/topic_hierarchy.mmd` - Topic hierarchy diagram\n")
        f.write("- `docs/TOPIC_HIERARCHY.md` - This report\n\n")

        # Next steps
        f.write("## Next Steps\n\n")
        f.write("1. Review topic hierarchy and validate relationships\n")
        f.write("2. Visualize enriched graph in Gephi or Neo4j\n")
        f.write("3. Proceed to Phase 4: Semantic enrichment with entity extraction\n")

    logging.info(f"Generated visualization report: {output_path}")


async def main():
    """Main execution function."""
    args = parse_args()

    # Setup logging
    Path('logs').mkdir(exist_ok=True)
    setup_logging(args.log_level)

    logger = logging.getLogger(__name__)

    # Load environment variables
    env_vars = load_env_vars()

    # Get OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY') or env_vars.get('OPENAI_API_KEY')

    if not openai_api_key:
        logger.error("OPENAI_API_KEY not found in environment or .env file")
        sys.exit(1)

    # Verify input graph exists
    graph_path = Path(args.graph)
    if not graph_path.exists():
        logger.error(f"Input graph not found: {graph_path}")
        sys.exit(1)

    logger.info(f"Input graph: {graph_path}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Reports directory: {args.reports_dir}")
    logger.info(f"Similarity threshold: {args.similarity_threshold}")
    logger.info(f"Related threshold: {args.related_threshold}")

    # Create enricher
    enricher = TopicClusterEnricher(
        graph_path=str(graph_path),
        openai_api_key=openai_api_key,
        similarity_threshold=args.similarity_threshold,
        related_threshold=args.related_threshold
    )

    # Run enrichment pipeline
    async with enricher:
        results = await enricher.run(
            output_dir=args.output_dir,
            reports_dir=args.reports_dir
        )

        if results['success']:
            # Generate visualization report
            report_path = Path(args.reports_dir) / 'TOPIC_HIERARCHY.md'
            await generate_visualization_report(
                str(report_path),
                results,
                enricher
            )

            logger.info("✅ Phase 3 completed successfully!")
            logger.info(f"📊 Report: {report_path}")

            return 0
        else:
            logger.error(f"❌ Phase 3 failed: {results.get('error', 'Unknown error')}")
            return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
