"""
Journey Enricher - Orchestrates Persona Journey Mapping

Main orchestrator for Phase 3:
- Loads graph with persona TARGETS relationships
- Analyzes journeys for all 6 personas
- Creates NEXT_STEP edges
- Generates journey maps
- Exports enriched graph
"""

import logging
from pathlib import Path
from typing import Dict, List
import json
from datetime import datetime

from src.graph.mgraph_wrapper import MGraph
from src.enrichment.journey_analyzer import JourneyAnalyzer
from src.enrichment.next_step_builder import NextStepBuilder
from src.enrichment.journey_models import Journey, get_persona_ids


logger = logging.getLogger(__name__)


class JourneyEnricher:
    """Orchestrates journey mapping and graph enrichment"""

    def __init__(self, graph_path: str, output_dir: str):
        """
        Initialize journey enricher

        Args:
            graph_path: Path to input graph file
            output_dir: Directory for output files
        """
        self.graph_path = Path(graph_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.graph: Optional[MGraph] = None
        self.analyzer: Optional[JourneyAnalyzer] = None
        self.builder: Optional[NextStepBuilder] = None

        self.journeys: Dict[str, Journey] = {}
        self.stats = {
            'start_time': None,
            'end_time': None,
            'personas_analyzed': 0,
            'total_entry_points': 0,
            'total_conversion_points': 0,
            'total_next_step_edges': 0,
            'errors': []
        }

    def enrich(self) -> bool:
        """
        Execute complete journey enrichment workflow

        Returns:
            True if enrichment completed successfully
        """
        self.stats['start_time'] = datetime.utcnow().isoformat()
        logger.info("=" * 80)
        logger.info("Starting Journey Enrichment - Phase 3")
        logger.info("=" * 80)

        try:
            # Step 1: Load graph
            if not self._load_graph():
                return False

            # Step 2: Initialize components
            self._initialize_components()

            # Step 3: Analyze journeys for all personas
            if not self._analyze_all_journeys():
                return False

            # Step 4: Create NEXT_STEP edges
            if not self._create_next_step_edges():
                return False

            # Step 5: Validate enrichment
            if not self._validate_enrichment():
                return False

            # Step 6: Export enriched graph
            if not self._export_enriched_graph():
                return False

            # Step 7: Generate journey reports
            if not self._generate_reports():
                return False

            self.stats['end_time'] = datetime.utcnow().isoformat()
            logger.info("=" * 80)
            logger.info("✅ Journey Enrichment Complete")
            logger.info("=" * 80)
            self._print_summary()

            return True

        except Exception as e:
            logger.error(f"❌ Journey enrichment failed: {e}", exc_info=True)
            self.stats['errors'].append(str(e))
            return False

    def _load_graph(self) -> bool:
        """Load knowledge graph from file"""
        logger.info(f"\n📂 Loading graph from: {self.graph_path}")

        try:
            if not self.graph_path.exists():
                logger.error(f"  Graph file not found: {self.graph_path}")
                return False

            # Determine format from extension
            if self.graph_path.suffix == '.json':
                self.graph = MGraph()
                self.graph.load_from_json(str(self.graph_path))
            elif self.graph_path.suffix == '.pkl':
                self.graph = MGraph.load(str(self.graph_path))
            else:
                logger.error(f"  Unsupported graph format: {self.graph_path.suffix}")
                return False

            # Verify persona nodes exist
            persona_count = self._count_personas()
            if persona_count == 0:
                logger.error("  No Persona nodes found in graph")
                logger.error("  Please run Phase 3 Persona Classifier first")
                return False

            logger.info(f"  ✅ Graph loaded: {persona_count} personas")
            return True

        except Exception as e:
            logger.error(f"  ❌ Failed to load graph: {e}")
            return False

    def _initialize_components(self):
        """Initialize analyzer and builder"""
        logger.info("\n🔧 Initializing components")

        self.analyzer = JourneyAnalyzer(self.graph)
        self.builder = NextStepBuilder(self.graph)

        logger.info("  ✅ JourneyAnalyzer initialized")
        logger.info("  ✅ NextStepBuilder initialized")

    def _analyze_all_journeys(self) -> bool:
        """Analyze journeys for all personas"""
        logger.info("\n🔍 Analyzing persona journeys")

        persona_ids = get_persona_ids()
        logger.info(f"  Found {len(persona_ids)} personas to analyze")

        for persona_id in persona_ids:
            try:
                logger.info(f"\n  📊 Analyzing: {persona_id}")

                journey = self.analyzer.analyze_persona_journey(persona_id)

                self.journeys[persona_id] = journey
                self.stats['personas_analyzed'] += 1
                self.stats['total_entry_points'] += len(journey.entry_points)
                self.stats['total_conversion_points'] += len(journey.conversion_points)

                logger.info(f"    ✅ Entry points: {len(journey.entry_points)}")
                logger.info(f"    ✅ Conversion points: {len(journey.conversion_points)}")
                logger.info(f"    ✅ Journey stages: {len(journey.stages)}")
                logger.info(f"    ✅ Typical paths: {len(journey.typical_paths)}")

            except Exception as e:
                logger.error(f"    ❌ Failed to analyze {persona_id}: {e}")
                self.stats['errors'].append(f"Analysis failed for {persona_id}: {e}")

        logger.info(f"\n  ✅ Analyzed {self.stats['personas_analyzed']} personas")
        return True

    def _create_next_step_edges(self) -> bool:
        """Create NEXT_STEP relationships for all journeys"""
        logger.info("\n🔗 Creating NEXT_STEP relationships")

        total_edges = 0

        for persona_id, journey in self.journeys.items():
            try:
                edges_created = self.builder.build_next_steps_for_journey(journey)
                total_edges += edges_created

                logger.info(f"    {persona_id}: {edges_created} edges")

            except Exception as e:
                logger.error(f"    ❌ Failed for {persona_id}: {e}")
                self.stats['errors'].append(f"NEXT_STEP creation failed for {persona_id}: {e}")

        self.stats['total_next_step_edges'] = total_edges
        logger.info(f"\n  ✅ Created {total_edges} NEXT_STEP edges")

        return True

    def _validate_enrichment(self) -> bool:
        """Validate journey enrichment"""
        logger.info("\n✓ Validating enrichment")

        try:
            # Validate NEXT_STEP edges
            validation = self.builder.validate_next_steps()

            logger.info(f"  Total NEXT_STEP edges: {validation['total_next_step_edges']}")
            logger.info(f"  Invalid probabilities: {validation['invalid_probabilities']}")
            logger.info(f"  Missing persona_id: {validation['missing_persona_id']}")

            if not validation['valid']:
                logger.warning("  ⚠️  Some validation checks failed")
                return False

            logger.info("  ✅ All validation checks passed")
            return True

        except Exception as e:
            logger.error(f"  ❌ Validation failed: {e}")
            return False

    def _export_enriched_graph(self) -> bool:
        """Export enriched graph to files"""
        logger.info("\n💾 Exporting enriched graph")

        try:
            # Export to JSON
            json_path = self.output_dir / "graph_enriched_journeys.json"
            self.graph.export_to_json(str(json_path))
            logger.info(f"  ✅ Exported JSON: {json_path}")

            # Export to GraphML
            graphml_path = self.output_dir / "graph_enriched_journeys.graphml"
            self.graph.export_to_graphml(str(graphml_path))
            logger.info(f"  ✅ Exported GraphML: {graphml_path}")

            # Export to Cypher
            cypher_path = self.output_dir / "graph_enriched_journeys.cypher"
            self.graph.export_to_cypher(str(cypher_path))
            logger.info(f"  ✅ Exported Cypher: {cypher_path}")

            return True

        except Exception as e:
            logger.error(f"  ❌ Export failed: {e}")
            return False

    def _generate_reports(self) -> bool:
        """Generate journey analysis reports"""
        logger.info("\n📊 Generating reports")

        try:
            # Journey summaries
            summaries_path = self.output_dir / "journey_summaries.json"
            self._export_journey_summaries(summaries_path)
            logger.info(f"  ✅ Journey summaries: {summaries_path}")

            # Statistics report
            stats_path = self.output_dir / "journey_stats.json"
            self._export_statistics(stats_path)
            logger.info(f"  ✅ Statistics: {stats_path}")

            return True

        except Exception as e:
            logger.error(f"  ❌ Report generation failed: {e}")
            return False

    def _export_journey_summaries(self, path: Path):
        """Export journey summaries to JSON"""
        summaries = {}

        for persona_id, journey in self.journeys.items():
            summaries[persona_id] = {
                'persona_name': journey.persona_name,
                'page_count': journey.page_count,
                'path_count': journey.path_count,
                'entry_points': [
                    {
                        'page_id': ep.page_id,
                        'title': ep.page_title,
                        'entry_rate': ep.entry_rate
                    }
                    for ep in journey.get_top_entry_points()
                ],
                'conversion_points': [
                    {
                        'page_id': cp.page_id,
                        'title': cp.page_title,
                        'conversion_rate': cp.conversion_rate
                    }
                    for cp in journey.get_top_conversion_points()
                ],
                'stages': {
                    stage.value: len(info.page_ids)
                    for stage, info in journey.stages.items()
                },
                'avg_path_length': journey.avg_path_length,
                'overall_completion_rate': journey.overall_completion_rate
            }

        with open(path, 'w') as f:
            json.dump(summaries, f, indent=2)

    def _export_statistics(self, path: Path):
        """Export enrichment statistics"""
        with open(path, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def _count_personas(self) -> int:
        """Count persona nodes in graph"""
        query = "MATCH (p:Persona) RETURN count(p) as count"
        result = self.graph.execute_query(query)
        return result[0]['count'] if result else 0

    def _print_summary(self):
        """Print enrichment summary"""
        logger.info("\n" + "=" * 80)
        logger.info("JOURNEY ENRICHMENT SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Personas analyzed: {self.stats['personas_analyzed']}")
        logger.info(f"Total entry points: {self.stats['total_entry_points']}")
        logger.info(f"Total conversion points: {self.stats['total_conversion_points']}")
        logger.info(f"NEXT_STEP edges created: {self.stats['total_next_step_edges']}")

        if self.stats['errors']:
            logger.warning(f"\nErrors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                logger.warning(f"  - {error}")

        logger.info("=" * 80)

    def get_journey(self, persona_id: str) -> Optional[Journey]:
        """Get journey for a specific persona"""
        return self.journeys.get(persona_id)

    def get_all_journeys(self) -> Dict[str, Journey]:
        """Get all analyzed journeys"""
        return self.journeys

    def get_statistics(self) -> Dict:
        """Get enrichment statistics"""
        return self.stats
