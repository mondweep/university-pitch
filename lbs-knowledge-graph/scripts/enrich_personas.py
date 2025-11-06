#!/usr/bin/env python3
"""
Master script for persona enrichment of LBS Knowledge Graph.
Orchestrates persona classification and TARGETS relationship creation.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.llm_client import LLMClient
from src.enrichment.persona_enricher import PersonaEnricher
from src.enrichment.persona_models import get_all_personas


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/persona_enrichment.log')
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main enrichment workflow."""
    parser = argparse.ArgumentParser(description='Enrich knowledge graph with persona targeting')
    parser.add_argument(
        '--graph',
        type=Path,
        default=Path('output/graph/graph.json'),
        help='Input graph JSON file'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('output/enriched'),
        help='Output directory for enriched graph'
    )
    parser.add_argument(
        '--provider',
        choices=['anthropic', 'openai'],
        default='anthropic',
        help='LLM provider'
    )
    parser.add_argument(
        '--model',
        type=str,
        help='LLM model name (default: provider default)'
    )
    parser.add_argument(
        '--relevance-threshold',
        type=float,
        default=0.6,
        help='Minimum relevance score (0-1)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without making API calls'
    )

    args = parser.parse_args()

    # Validate input
    if not args.graph.exists():
        logger.error(f"Graph file not found: {args.graph}")
        sys.exit(1)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir.parent / 'logs').mkdir(parents=True, exist_ok=True)

    logger.info("=" * 80)
    logger.info("LBS Knowledge Graph - Persona Enrichment")
    logger.info("=" * 80)
    logger.info(f"Input graph: {args.graph}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"LLM provider: {args.provider}")
    logger.info(f"Model: {args.model or 'default'}")
    logger.info(f"Relevance threshold: {args.relevance_threshold}")
    logger.info("")

    # Display personas
    logger.info("Target Personas:")
    for persona in get_all_personas():
        logger.info(f"  - {persona.name} ({persona.type.value})")
        logger.info(f"    Priority: {persona.priority}, Goals: {len(persona.goals)}")
    logger.info("")

    if args.dry_run:
        logger.info("DRY RUN - No API calls will be made")
        return

    try:
        # Initialize LLM client
        logger.info("Initializing LLM client...")
        llm_client = LLMClient(
            provider=args.provider,
            model=args.model,
            max_retries=3,
            timeout=60
        )

        # Initialize enricher
        logger.info("Initializing persona enricher...")
        enricher = PersonaEnricher(
            llm_client=llm_client,
            graph_path=args.graph,
            output_dir=args.output_dir,
            relevance_threshold=args.relevance_threshold
        )

        # Enrich graph
        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 1: Load and Analyze Graph")
        logger.info("=" * 80)
        enricher.load_graph()

        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 2: Classify Pages by Persona")
        logger.info("=" * 80)
        start_time = datetime.now()
        page_results = await enricher.enrich_pages()
        page_duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Page classification completed in {page_duration:.1f}s")
        logger.info(f"  Classified: {len(page_results)} pages")
        logger.info(f"  Total targets: {sum(len(r['targets']) for r in page_results)}")
        logger.info(f"  Avg personas/page: {sum(len(r['targets']) for r in page_results) / len(page_results):.2f}")

        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 3: Classify Sections by Persona")
        logger.info("=" * 80)
        start_time = datetime.now()
        section_results = await enricher.enrich_sections()
        section_duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Section classification completed in {section_duration:.1f}s")
        logger.info(f"  Classified: {len(section_results)} sections")
        logger.info(f"  Total targets: {sum(len(r['targets']) for r in section_results)}")
        logger.info(f"  Avg personas/section: {sum(len(r['targets']) for r in section_results) / len(section_results):.2f}")

        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 4: Build Persona Graph")
        logger.info("=" * 80)
        all_results = page_results + section_results
        graph = enricher.builder.build_persona_graph(all_results)
        logger.info(f"Persona graph built:")
        logger.info(f"  Total nodes: {graph.node_count()}")
        logger.info(f"  Total edges: {graph.edge_count()}")
        logger.info(f"  Persona nodes: {len(enricher.builder.persona_nodes)}")

        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 5: Export Results")
        logger.info("=" * 80)

        # Export graph
        graph_path = enricher.export_graph()
        logger.info(f"✓ Exported enriched graph: {graph_path}")

        # Generate report
        report_path = args.output_dir / "persona_report.json"
        report = enricher.generate_report(report_path)
        logger.info(f"✓ Generated persona report: {report_path}")

        # Display summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("ENRICHMENT SUMMARY")
        logger.info("=" * 80)

        summary = enricher.get_summary()
        logger.info(f"Graph Statistics:")
        logger.info(f"  Total nodes: {summary['graph']['total_nodes']}")
        logger.info(f"  Total edges: {summary['graph']['total_edges']}")
        logger.info(f"  Persona nodes: {summary['graph']['personas']}")
        logger.info(f"  TARGETS edges: {summary['graph']['targets_edges']}")

        logger.info("")
        logger.info("Persona Distribution:")
        for persona_id, stats in summary['persona_distribution'].items():
            logger.info(f"  {stats['name']}: {stats['content_count']} content, {stats['page_count']} pages")

        logger.info("")
        logger.info("LLM Usage:")
        usage = summary['llm_usage']
        logger.info(f"  Total requests: {usage.get('total_requests', 0)}")
        logger.info(f"  API calls: {usage.get('api_calls', 0)}")
        logger.info(f"  Cached responses: {usage.get('cached_responses', 0)}")
        logger.info(f"  Cache hit rate: {usage.get('cache_hit_rate', 0) * 100:.1f}%")
        logger.info(f"  Input tokens: {usage.get('total_input_tokens', 0):,}")
        logger.info(f"  Output tokens: {usage.get('total_output_tokens', 0):,}")
        logger.info(f"  Estimated cost: ${usage.get('estimated_cost', 0):.2f}")

        logger.info("")
        logger.info("=" * 80)
        logger.info("PERSONA ENRICHMENT COMPLETE!")
        logger.info("=" * 80)

        # Close LLM client
        await llm_client.close()

        return 0

    except Exception as e:
        logger.error(f"Enrichment failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
