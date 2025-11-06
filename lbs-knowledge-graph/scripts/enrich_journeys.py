#!/usr/bin/env python3
"""
Journey Enrichment Master Script

Orchestrates Phase 3 journey mapping:
1. Loads graph with persona TARGETS relationships
2. Analyzes journeys for all 6 personas
3. Creates NEXT_STEP edges (~300 edges expected)
4. Generates journey visualizations
5. Exports enriched graph

Usage:
    python scripts/enrich_journeys.py
    python scripts/enrich_journeys.py --graph data/graph/graph_enriched.json
    python scripts/enrich_journeys.py --output data/checkpoints/
"""

import sys
import logging
from pathlib import Path
import argparse
from datetime import datetime

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.enrichment.journey_enricher import JourneyEnricher
from src.enrichment.journey_models import get_persona_ids, get_persona_name


def setup_logging(log_dir: Path):
    """Configure logging"""
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"journey_enrichment_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)


def generate_journey_visualizations(enricher: JourneyEnricher, output_dir: Path):
    """Generate Mermaid visualizations for persona journeys"""
    logger = logging.getLogger(__name__)
    logger.info("\n📊 Generating journey visualizations")

    doc_path = output_dir.parent / "docs" / "PERSONA_JOURNEYS.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    with open(doc_path, 'w') as f:
        # Write header
        f.write("# Persona Journey Maps\n\n")
        f.write("**Generated:** " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        f.write("This document shows typical content pathways for each target audience persona.\n\n")
        f.write("---\n\n")

        # Write journey for each persona
        for persona_id in get_persona_ids():
            journey = enricher.get_journey(persona_id)
            if not journey:
                continue

            f.write(f"## {journey.persona_name}\n\n")

            # Journey metrics
            f.write("**Journey Metrics:**\n\n")
            f.write(f"- Total Pages: {journey.page_count}\n")
            f.write(f"- Typical Paths: {journey.path_count}\n")
            f.write(f"- Average Path Length: {journey.avg_path_length:.1f} pages\n")
            f.write(f"- Overall Completion Rate: {journey.overall_completion_rate:.1%}\n\n")

            # Entry points
            f.write("**Top Entry Points:**\n\n")
            for ep in journey.get_top_entry_points():
                f.write(f"- **{ep.page_title}** ({ep.entry_rate:.1%} of entries)\n")
                f.write(f"  - Stage: {ep.stage.value}\n")
                f.write(f"  - URL: `{ep.page_url}`\n")
            f.write("\n")

            # Conversion points
            f.write("**Key Conversion Points:**\n\n")
            for cp in journey.get_top_conversion_points():
                f.write(f"- **{cp.page_title}** ({cp.conversion_rate:.1%} conversion rate)\n")
                f.write(f"  - Stage: {cp.stage.value}\n")
                f.write(f"  - URL: `{cp.page_url}`\n")
            f.write("\n")

            # Journey stages
            f.write("**Journey Stages:**\n\n")
            for stage, info in journey.stages.items():
                f.write(f"- **{stage.value.upper()}**: {len(info.page_ids)} pages\n")
            f.write("\n")

            # Typical paths as Mermaid diagram
            f.write("**Typical Pathways:**\n\n")
            f.write("```mermaid\n")
            f.write("graph LR\n")

            # Add nodes and edges for top 3 paths
            path_nodes = set()
            for idx, path in enumerate(journey.get_most_common_paths(3)):
                # Add nodes
                for page_id in path.page_sequence:
                    if page_id not in path_nodes:
                        # Simplify page ID for display
                        label = page_id.replace('page-', '').replace('-', ' ').title()[:20]
                        f.write(f"    {page_id}[\"{label}\"]\n")
                        path_nodes.add(page_id)

                # Add edges
                for i in range(len(path.page_sequence) - 1):
                    from_page = path.page_sequence[i]
                    to_page = path.page_sequence[i + 1]
                    prob = path.transition_probs[i] if i < len(path.transition_probs) else 0.5

                    # Edge with probability label
                    f.write(f"    {from_page} -->|{prob:.0%}| {to_page}\n")

            f.write("```\n\n")

            # Path details
            f.write("**Path Details:**\n\n")
            for idx, path in enumerate(journey.get_most_common_paths(3), 1):
                f.write(f"{idx}. **Path {idx}** (Frequency: {path.frequency}, Completion: {path.completion_rate:.1%})\n")
                for i, page_id in enumerate(path.page_sequence):
                    stage = path.stage_labels[i] if i < len(path.stage_labels) else None
                    stage_label = f" ({stage.value})" if stage else ""
                    f.write(f"   - {page_id}{stage_label}\n")
                f.write("\n")

            f.write("---\n\n")

    logger.info(f"  ✅ Journey visualizations: {doc_path}")
    return doc_path


def generate_analysis_report(enricher: JourneyEnricher, output_dir: Path):
    """Generate journey analysis report"""
    logger = logging.getLogger(__name__)
    logger.info("\n📋 Generating analysis report")

    report_path = output_dir / "journey_analysis_report.md"

    with open(report_path, 'w') as f:
        stats = enricher.get_statistics()

        f.write("# Journey Enrichment Analysis Report\n\n")
        f.write("**Generated:** " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        f.write("---\n\n")

        # Executive summary
        f.write("## Executive Summary\n\n")
        f.write(f"- **Personas Analyzed:** {stats['personas_analyzed']}\n")
        f.write(f"- **Total Entry Points:** {stats['total_entry_points']}\n")
        f.write(f"- **Total Conversion Points:** {stats['total_conversion_points']}\n")
        f.write(f"- **NEXT_STEP Edges Created:** {stats['total_next_step_edges']}\n")
        f.write(f"- **Start Time:** {stats['start_time']}\n")
        f.write(f"- **End Time:** {stats['end_time']}\n\n")

        # Per-persona summary
        f.write("## Persona Summaries\n\n")

        for persona_id in get_persona_ids():
            journey = enricher.get_journey(persona_id)
            if not journey:
                continue

            f.write(f"### {journey.persona_name}\n\n")
            f.write(f"- **Pages in Journey:** {journey.page_count}\n")
            f.write(f"- **Entry Points:** {len(journey.entry_points)}\n")
            f.write(f"- **Conversion Points:** {len(journey.conversion_points)}\n")
            f.write(f"- **Journey Stages:** {len(journey.stages)}\n")
            f.write(f"- **Typical Paths:** {len(journey.typical_paths)}\n")
            f.write(f"- **Avg Path Length:** {journey.avg_path_length:.1f} pages\n")
            f.write(f"- **Completion Rate:** {journey.overall_completion_rate:.1%}\n\n")

        # Errors
        if stats.get('errors'):
            f.write("## Errors & Warnings\n\n")
            for error in stats['errors']:
                f.write(f"- {error}\n")
            f.write("\n")

        f.write("---\n\n")
        f.write("**Status:** ✅ Journey enrichment complete\n")

    logger.info(f"  ✅ Analysis report: {report_path}")
    return report_path


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Enrich knowledge graph with persona journeys")
    parser.add_argument(
        '--graph',
        type=str,
        default=str(PROJECT_ROOT / 'data' / 'graph' / 'graph.json'),
        help='Path to input graph file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=str(PROJECT_ROOT / 'data' / 'checkpoints'),
        help='Output directory for enriched graph'
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        default=str(PROJECT_ROOT / 'logs'),
        help='Directory for log files'
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(Path(args.log_dir))

    logger.info("=" * 80)
    logger.info("JOURNEY ENRICHMENT - PHASE 3")
    logger.info("=" * 80)
    logger.info(f"Input graph: {args.graph}")
    logger.info(f"Output directory: {args.output}")
    logger.info("=" * 80)

    # Initialize enricher
    enricher = JourneyEnricher(
        graph_path=args.graph,
        output_dir=args.output
    )

    # Execute enrichment
    success = enricher.enrich()

    if not success:
        logger.error("❌ Journey enrichment failed")
        sys.exit(1)

    # Generate visualizations
    try:
        viz_path = generate_journey_visualizations(enricher, Path(args.output))
        logger.info(f"✅ Journey visualizations: {viz_path}")
    except Exception as e:
        logger.error(f"⚠️  Visualization generation failed: {e}")

    # Generate analysis report
    try:
        report_path = generate_analysis_report(enricher, Path(args.output))
        logger.info(f"✅ Analysis report: {report_path}")
    except Exception as e:
        logger.error(f"⚠️  Report generation failed: {e}")

    logger.info("\n" + "=" * 80)
    logger.info("✅ JOURNEY ENRICHMENT COMPLETE")
    logger.info("=" * 80)

    # Print summary
    stats = enricher.get_statistics()
    logger.info(f"\nPersonas analyzed: {stats['personas_analyzed']}")
    logger.info(f"NEXT_STEP edges created: {stats['total_next_step_edges']}")
    logger.info(f"\nExpected edges: ~300")
    logger.info(f"Actual edges: {stats['total_next_step_edges']}")

    if stats['total_next_step_edges'] >= 250:
        logger.info("✅ Edge count meets expectations")
    else:
        logger.warning("⚠️  Edge count below expectations")


if __name__ == '__main__':
    main()
