#!/usr/bin/env python3
"""
NER Enrichment CLI

Extract named entities from PDF pages and create Entity nodes
and MENTIONS edges in the knowledge graph.

Usage:
    python scripts/enrich_ner.py --graph data/checkpoints/graph_with_topics.json
    python scripts/enrich_ner.py --graph graph.json --max-items 20 --batch-size 5
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "lbs-knowledge-graph" / "src"))

# Import graph and enrichment modules
try:
    from graph.mgraph_compat import MGraph
    from enrichment.ner_enricher import NEREnricher
except ImportError:
    # Try alternative import paths
    sys.path.insert(0, str(project_root / "lbs-knowledge-graph"))
    from src.graph.mgraph_compat import MGraph
    from src.enrichment.ner_enricher import NEREnricher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_graph(graph_path: Path) -> MGraph:
    """
    Load knowledge graph from JSON file.

    Args:
        graph_path: Path to graph JSON file

    Returns:
        MGraph instance
    """
    logger.info(f"📂 Loading graph from {graph_path}")

    if not graph_path.exists():
        logger.error(f"Graph file not found: {graph_path}")
        sys.exit(1)

    graph = MGraph()
    graph.load_from_json(str(graph_path))

    logger.info(f"✅ Graph loaded: {graph.node_count()} nodes, {graph.edge_count()} edges")

    return graph


def save_graph(graph: MGraph, output_path: Path):
    """
    Save enriched graph to JSON file.

    Args:
        graph: MGraph instance
        output_path: Path to save graph
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"💾 Saving enriched graph to {output_path}")
    graph.save_to_json(str(output_path))

    logger.info(f"✅ Graph saved: {graph.node_count()} nodes, {graph.edge_count()} edges")


async def run_enrichment(args):
    """
    Run NER enrichment pipeline.

    Args:
        args: Command line arguments
    """
    start_time = datetime.now()

    # Load graph
    graph = load_graph(args.graph)

    # Get initial stats
    initial_nodes = graph.node_count()
    initial_edges = graph.edge_count()
    initial_entities = len(graph.query(node_type="Entity"))

    logger.info(f"""
📊 Initial Graph State:
- Total Nodes: {initial_nodes:,}
- Total Edges: {initial_edges:,}
- Entity Nodes: {initial_entities:,}
- ContentItem Nodes: {len(graph.query(node_type='ContentItem')):,}
""")

    # Check API key
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OpenAI API key not found. Set OPENAI_API_KEY or use --api-key")
        sys.exit(1)

    # Create enricher
    enricher = NEREnricher(
        graph=graph,
        api_key=api_key,
        model=args.model,
        batch_size=args.batch_size
    )

    # Run enrichment
    logger.info(f"""
🚀 Starting NER Enrichment
- Model: {args.model}
- Batch Size: {args.batch_size}
- Max Items: {args.max_items or 'All'}
""")

    stats = await enricher.enrich_graph(max_items=args.max_items)

    # Get final stats
    final_nodes = graph.node_count()
    final_edges = graph.edge_count()
    final_entities = len(graph.query(node_type="Entity"))

    logger.info(f"""
📊 Final Graph State:
- Total Nodes: {final_nodes:,} (+{final_nodes - initial_nodes})
- Total Edges: {final_edges:,} (+{final_edges - initial_edges})
- Entity Nodes: {final_entities:,} (+{final_entities - initial_entities})
""")

    # Save enriched graph
    output_path = args.output or args.graph.parent / f"{args.graph.stem}_with_ner.json"
    save_graph(graph, output_path)

    # Save statistics
    stats_path = args.stats_output or Path("data/ner_stats.json")
    enricher.save_stats(stats_path)

    # Print summary
    duration = (datetime.now() - start_time).total_seconds()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    NER ENRICHMENT COMPLETE                   ║
╚══════════════════════════════════════════════════════════════╝

📊 Results:
   • Content Items Processed: {stats['content_items_processed']:,}
   • Entities Extracted: {stats['entities_extracted']:,}
   • Unique Entities: {stats['unique_entities']:,}
   • MENTIONS Edges Created: {stats['mentions_created']:,}

💰 Cost:
   • API Calls: {stats['api_calls']:,}
   • Total Tokens: {stats['total_tokens']:,}
   • Total Cost: ${stats['total_cost']:.2f}

⏱️ Performance:
   • Duration: {duration:.1f}s
   • Items/sec: {stats['content_items_processed'] / duration:.1f}

📁 Output:
   • Graph: {output_path}
   • Stats: {stats_path}
""")

    # Get top entities
    entity_stats = enricher.entity_builder.get_entity_stats()
    if entity_stats["top_entities"]:
        print("🏆 Top Entities by Mentions:")
        for i, entity in enumerate(entity_stats["top_entities"][:5], 1):
            print(f"   {i}. {entity['name']} ({entity['type']}): {entity['mentions']} mentions")
        print()

    # Validation report
    validation = enricher.mentions_builder.validate_mentions()
    if validation["errors"]:
        print(f"⚠️  Validation Errors: {len(validation['errors'])}")
        for error in validation["errors"][:5]:
            print(f"   • {error}")
    else:
        print("✅ Validation: All MENTIONS edges valid")

    return stats


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Extract named entities and enrich knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python scripts/enrich_ner.py --graph data/graph.json

  # Test with limited items
  python scripts/enrich_ner.py --graph data/graph.json --max-items 10

  # Use different model and batch size
  python scripts/enrich_ner.py --graph data/graph.json \\
    --model gpt-4o --batch-size 20

  # Specify custom output paths
  python scripts/enrich_ner.py --graph data/graph.json \\
    --output data/graph_with_ner.json \\
    --stats-output data/ner_stats.json
        """
    )

    parser.add_argument(
        "--graph",
        type=Path,
        required=True,
        help="Path to input graph JSON file"
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Path to output graph JSON file (default: {input}_with_ner.json)"
    )

    parser.add_argument(
        "--stats-output",
        type=Path,
        help="Path to stats JSON file (default: data/ner_stats.json)"
    )

    parser.add_argument(
        "--api-key",
        help="OpenAI API key (default: OPENAI_API_KEY env var)"
    )

    parser.add_argument(
        "--model",
        default="gpt-4-turbo",
        choices=["gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"],
        help="OpenAI model to use (default: gpt-4-turbo)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of items to process in parallel (default: 10)"
    )

    parser.add_argument(
        "--max-items",
        type=int,
        help="Maximum content items to process (for testing)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run enrichment
    try:
        stats = asyncio.run(run_enrichment(args))
        sys.exit(0)
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
