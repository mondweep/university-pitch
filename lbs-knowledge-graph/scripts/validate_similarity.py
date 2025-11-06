#!/usr/bin/env python3
"""
Similarity Validation Script
Validates RELATED_TO relationships and calculates precision metrics.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enrichment.similarity_validator import SimilarityValidator
from graph.graph_loader import GraphLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run similarity validation."""

    logger.info("=" * 80)
    logger.info("SIMILARITY VALIDATION")
    logger.info("=" * 80)

    # Configuration
    config = {
        'graph_path': 'data/graphs/lbs-kg-with-similarity.json',
        'output_dir': 'data/enrichment/similarity',
        'sample_size': 20,
        'min_similarity': 0.7,
        'automated': True  # Set to False for interactive validation
    }

    logger.info("Configuration:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")

    # Load graph
    logger.info("\nLoading graph with RELATED_TO relationships...")
    graph_loader = GraphLoader()

    try:
        graph = graph_loader.load(config['graph_path'])
        logger.info(f"Loaded graph with {len(graph.get_all_nodes())} nodes")
    except FileNotFoundError:
        logger.error(f"Graph file not found: {config['graph_path']}")
        logger.error("Please run enrich_similarity.py first")
        sys.exit(1)

    # Initialize validator
    logger.info("\nInitializing validator...")
    validator = SimilarityValidator(
        graph=graph,
        min_similarity=config['min_similarity']
    )

    # Sample relationships
    logger.info("\nSampling relationships for validation...")
    relationships = validator.sample_relationships(
        sample_size=config['sample_size']
    )

    if not relationships:
        logger.warning("No relationships found to validate")
        sys.exit(0)

    logger.info(f"Sampled {len(relationships)} relationships")

    # Validate
    logger.info("\nStarting validation...")

    if config['automated']:
        # Automated validation (for testing)
        logger.info("Running automated validation...")
        results = validator.validate_automated(relationships)
    else:
        # Interactive validation (manual)
        logger.info("Running interactive validation...")
        results = validator.validate_interactive(relationships)

    # Export results
    output_dir = Path(config['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    validations_path = output_dir / 'similarity_validations.json'
    validator.export_validations(str(validations_path))

    report_path = output_dir / 'similarity_validation_report.txt'
    validator.generate_report(str(report_path))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Precision: {results['precision']:.2%}")
    logger.info(f"Target: {results['target_precision']:.2%}")
    logger.info(f"Status: {'✅ PASSED' if results['meets_target'] else '❌ FAILED'}")
    logger.info(f"\nResults saved to:")
    logger.info(f"  Validations: {validations_path}")
    logger.info(f"  Report: {report_path}")

    if results['meets_target']:
        logger.info("\n✅ Similarity validation passed!")
        sys.exit(0)
    else:
        logger.warning("\n⚠️  Similarity validation below target")
        logger.warning("Review incorrect relationships in the report")
        sys.exit(1)


if __name__ == '__main__':
    main()
