#!/usr/bin/env python3
"""
Master Pipeline for Building LBS Knowledge Graph

Orchestrates the complete graph building process:
1. Load parsed data from Phase 1
2. Build knowledge graph with MGraph-DB
3. Validate graph integrity
4. Export to multiple formats
5. Generate statistics and reports
"""

import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from graph.graph_loader import GraphLoader


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/graph_build.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class GraphBuildPipeline:
    """
    Master pipeline for graph construction
    """

    def __init__(self, parsed_dir: Path, output_dir: Path):
        self.parsed_dir = Path(parsed_dir)
        self.output_dir = Path(output_dir)
        self.loader = None
        self.stats = {
            'start_time': None,
            'end_time': None,
            'duration_seconds': 0,
            'pages_loaded': 0,
            'graph_stats': {},
            'validation': {},
            'exports': {}
        }

    def run(self) -> Dict:
        """
        Execute complete pipeline

        Returns:
            Pipeline execution report
        """
        logger.info("=" * 80)
        logger.info("LBS KNOWLEDGE GRAPH - BUILD PIPELINE")
        logger.info("=" * 80)

        self.stats['start_time'] = datetime.now().isoformat()
        start = time.time()

        try:
            # Step 1: Load parsed data
            logger.info("\n[1/5] Loading parsed data...")
            pages = self._load_data()

            # Step 2: Build graph
            logger.info("\n[2/5] Building knowledge graph...")
            graph = self._build_graph(pages)

            # Step 3: Validate graph
            logger.info("\n[3/5] Validating graph integrity...")
            validation = self._validate_graph()

            # Step 4: Export graph
            logger.info("\n[4/5] Exporting graph to multiple formats...")
            exports = self._export_graph()

            # Step 5: Generate statistics
            logger.info("\n[5/5] Generating statistics...")
            statistics = self._generate_statistics()

            # Finalize
            end = time.time()
            self.stats['end_time'] = datetime.now().isoformat()
            self.stats['duration_seconds'] = round(end - start, 2)

            self._print_summary()
            self._save_report()

            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE COMPLETE")
            logger.info("=" * 80)

            return self.stats

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise

    def _load_data(self) -> list:
        """Load parsed data from repository"""
        self.loader = GraphLoader(self.parsed_dir)
        pages = self.loader.load_parsed_data()

        self.stats['pages_loaded'] = len(pages)
        logger.info(f"✓ Loaded {len(pages)} pages")

        return pages

    def _build_graph(self, pages: list):
        """Build knowledge graph"""
        graph = self.loader.build_complete_graph(pages)

        logger.info(f"✓ Graph built: {graph.node_count()} nodes, {graph.edge_count()} edges")

        return graph

    def _validate_graph(self) -> Dict:
        """Validate graph integrity"""
        validation = self.loader.validate_graph()

        self.stats['validation'] = validation

        if validation['valid']:
            logger.info("✓ Graph validation PASSED")
        else:
            logger.warning(f"✗ Graph validation FAILED with {len(validation['errors'])} errors")
            for error in validation['errors'][:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")

        if validation['warnings']:
            logger.warning(f"⚠ {len(validation['warnings'])} warnings")
            for warning in validation['warnings'][:5]:  # Show first 5 warnings
                logger.warning(f"  - {warning}")

        return validation

    def _export_graph(self) -> Dict:
        """Export graph to multiple formats"""
        exports = self.loader.save_graph(self.output_dir)

        self.stats['exports'] = {fmt: str(path) for fmt, path in exports.items()}

        logger.info(f"✓ Exported to {len(exports)} formats:")
        for fmt, path in exports.items():
            file_size = path.stat().st_size / 1024  # KB
            logger.info(f"  - {fmt.upper()}: {path.name} ({file_size:.1f} KB)")

        return exports

    def _generate_statistics(self) -> Dict:
        """Generate graph statistics"""
        statistics = self.loader.builder.get_statistics()

        self.stats['graph_stats'] = statistics

        logger.info("✓ Graph Statistics:")
        logger.info(f"  Total Nodes: {statistics['total_nodes']}")
        logger.info(f"  Total Edges: {statistics['total_edges']}")
        logger.info(f"  Average Degree: {statistics['avg_degree']:.2f}")

        logger.info("  Nodes by Type:")
        for node_type, count in statistics['nodes_by_type'].items():
            logger.info(f"    - {node_type}: {count}")

        logger.info("  Build Statistics:")
        for key, value in statistics['build_stats'].items():
            logger.info(f"    - {key}: {value}")

        return statistics

    def _print_summary(self):
        """Print pipeline summary"""
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {self.stats['duration_seconds']}s")
        logger.info(f"Pages Loaded: {self.stats['pages_loaded']}")
        logger.info(f"Nodes Created: {self.stats['graph_stats']['total_nodes']}")
        logger.info(f"Edges Created: {self.stats['graph_stats']['total_edges']}")
        logger.info(f"Validation: {'PASSED' if self.stats['validation']['valid'] else 'FAILED'}")
        logger.info(f"Exports: {len(self.stats['exports'])} formats")

        # Performance metrics
        if self.stats['duration_seconds'] > 0:
            nodes_per_sec = self.stats['graph_stats']['total_nodes'] / self.stats['duration_seconds']
            logger.info(f"Performance: {nodes_per_sec:.1f} nodes/second")

    def _save_report(self):
        """Save pipeline report to file"""
        report_file = self.output_dir / 'build_report.json'

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)

        logger.info(f"✓ Report saved to {report_file}")


def main():
    """Main entry point"""
    # Paths
    base_dir = Path(__file__).parent.parent
    parsed_dir = base_dir / 'content-repo' / 'parsed'
    output_dir = base_dir / 'data' / 'graph'

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if parsed data exists
    if not parsed_dir.exists() or not any(parsed_dir.iterdir()):
        logger.error(f"No parsed data found in {parsed_dir}")
        logger.error("Please run Phase 1 parser first")
        sys.exit(1)

    # Run pipeline
    pipeline = GraphBuildPipeline(parsed_dir, output_dir)

    try:
        stats = pipeline.run()

        # Print final status
        print("\n" + "=" * 80)
        print("✓ GRAPH BUILD COMPLETE")
        print("=" * 80)
        print(f"Output directory: {output_dir}")
        print(f"Graph file: {output_dir / 'graph.json'}")
        print(f"Statistics: {stats['graph_stats']['total_nodes']} nodes, {stats['graph_stats']['total_edges']} edges")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
