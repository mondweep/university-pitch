"""
Persona Enrichment Orchestrator

Master script for persona classification and TARGETS relationship creation.
Coordinates persona classification, node creation, and relationship building.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

from src.graph.mgraph_wrapper import MGraph

from .llm_client import LLMClient
from .persona_classifier import PersonaClassifier
from .targets_builder import TargetsBuilder


class PersonaEnricher:
    """
    Master orchestrator for persona enrichment.

    Workflow:
    1. Initialize LLM client and graph connection
    2. Create Persona nodes
    3. Classify content by target personas
    4. Create TARGETS relationships
    5. Update statistics and generate report
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4o-mini",
        graph_host: str = "localhost",
        graph_port: int = 7687
    ):
        """
        Initialize persona enricher.

        Args:
            api_key: OpenAI API key
            model: LLM model to use
            graph_host: Memgraph host
            graph_port: Memgraph port
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        # Initialize clients
        self.llm_client = LLMClient(api_key=self.api_key, model=self.model)
        self.graph = MGraph(host=graph_host, port=graph_port)

        # Initialize components
        self.classifier = PersonaClassifier(
            llm_client=self.llm_client,
            graph=self.graph,
            min_relevance=0.6,
            batch_size=50
        )

        self.builder = TargetsBuilder(graph=self.graph)

        self.report = {}

    async def enrich_all(self, content_type: str = "both") -> Dict[str, Any]:
        """
        Run complete persona enrichment workflow.

        Args:
            content_type: Type to enrich ('page', 'section', or 'both')

        Returns:
            Enrichment report
        """
        print("=" * 70)
        print("PERSONA ENRICHMENT - Phase 3")
        print("=" * 70)
        print(f"Model: {self.model}")
        print(f"Content type: {content_type}")
        print(f"Min relevance: {self.classifier.min_relevance}")
        print(f"Batch size: {self.classifier.batch_size}")
        print()

        start_time = datetime.now()

        # Step 1: Create Persona nodes
        personas_created = self.builder.create_persona_nodes()

        # Step 2: Classify content
        classifications = await self.classifier.classify_content(content_type=content_type)

        if not classifications:
            print("\n⚠️  No classifications generated. Check content availability.")
            return {"error": "No classifications generated"}

        # Step 3: Create TARGETS relationships
        relationships_created = self.builder.create_targets_relationships(classifications)

        # Step 4: Update statistics
        persona_stats = self.builder.update_persona_statistics()

        # Step 5: Generate report
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.report = self._generate_report(
            personas_created=personas_created,
            classifications=classifications,
            relationships_created=relationships_created,
            persona_stats=persona_stats,
            duration=duration
        )

        # Save report
        self._save_report()

        # Print summary
        self._print_summary()

        return self.report

    def _generate_report(
        self,
        personas_created: int,
        classifications: list,
        relationships_created: int,
        persona_stats: dict,
        duration: float
    ) -> Dict[str, Any]:
        """Generate enrichment report."""

        # Get classifier statistics
        classifier_stats = self.classifier.get_statistics()

        # Get multi-target content
        multi_target_content = self.builder.get_multi_target_content()

        # Get persona overlap matrix
        overlap_matrix = self.builder.get_persona_overlap_matrix()

        # Get journey stage distribution
        journey_distribution = self.builder.get_journey_stage_distribution()

        # Validate relationships
        validation_report = self.builder.validate_relationships()

        return {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "duration_seconds": round(duration, 1),
            "personas": {
                "created": personas_created,
                "distribution": persona_stats
            },
            "classifications": {
                "total": len(classifications),
                "multi_target_count": classifier_stats.get("multi_target_count", 0),
                "multi_target_rate": classifier_stats.get("multi_target_rate", 0),
                "avg_personas_per_content": classifier_stats.get("avg_personas_per_content", 0),
                "avg_relevance": classifier_stats.get("avg_relevance", 0)
            },
            "relationships": {
                "created": relationships_created,
                "avg_per_content": round(relationships_created / len(classifications), 2) if classifications else 0
            },
            "persona_distribution": classifier_stats.get("persona_distribution", {}),
            "primary_persona_distribution": classifier_stats.get("primary_persona_distribution", {}),
            "multi_target_examples": multi_target_content[:10],
            "persona_overlap_matrix": overlap_matrix,
            "journey_stage_distribution": journey_distribution,
            "validation": validation_report,
            "llm_usage": classifier_stats.get("llm_stats", {}),
            "cost_estimate": {
                "total_usd": classifier_stats.get("llm_stats", {}).get("total_cost", 0),
                "per_classification": round(
                    classifier_stats.get("llm_stats", {}).get("total_cost", 0) / len(classifications),
                    4
                ) if classifications else 0
            }
        }

    def _save_report(self):
        """Save report to file."""
        report_dir = "data/reports"
        os.makedirs(report_dir, exist_ok=True)

        # Save full report
        report_path = f"{report_dir}/persona_enrichment_report.json"
        with open(report_path, "w") as f:
            json.dump(self.report, f, indent=2)
        print(f"\n📄 Report saved: {report_path}")

        # Save persona statistics
        stats_path = "data/persona_stats.json"
        stats = {
            "timestamp": self.report["timestamp"],
            "personas": self.report["personas"],
            "classifications": self.report["classifications"],
            "persona_distribution": self.report["persona_distribution"],
            "primary_persona_distribution": self.report["primary_persona_distribution"]
        }

        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"📊 Statistics saved: {stats_path}")

    def _print_summary(self):
        """Print enrichment summary."""
        print("\n" + "=" * 70)
        print("PERSONA ENRICHMENT SUMMARY")
        print("=" * 70)

        print(f"\n⏱️  Duration: {self.report['duration_seconds']}s")
        print(f"\n👥 Personas Created: {self.report['personas']['created']}")

        print(f"\n📊 Classifications:")
        print(f"   Total: {self.report['classifications']['total']}")
        print(f"   Multi-target: {self.report['classifications']['multi_target_count']} ({self.report['classifications']['multi_target_rate']*100:.1f}%)")
        print(f"   Avg personas/content: {self.report['classifications']['avg_personas_per_content']}")
        print(f"   Avg relevance: {self.report['classifications']['avg_relevance']}")

        print(f"\n🎯 Relationships Created: {self.report['relationships']['created']}")

        print(f"\n📈 Persona Distribution:")
        for persona, count in sorted(
            self.report['persona_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"   {persona}: {count}")

        print(f"\n💰 Cost:")
        print(f"   Total: ${self.report['cost_estimate']['total_usd']:.2f}")
        print(f"   Per classification: ${self.report['cost_estimate']['per_classification']:.4f}")

        print(f"\n✅ LLM Usage:")
        llm_stats = self.report['llm_usage']
        print(f"   API calls: {llm_stats.get('api_calls', 0)}")
        print(f"   Total tokens: {llm_stats.get('total_tokens', 0):,}")
        print(f"   Avg tokens/call: {llm_stats.get('avg_tokens_per_call', 0)}")

        print("\n" + "=" * 70)


async def main():
    """Main entry point for persona enrichment."""
    enricher = PersonaEnricher()

    try:
        report = await enricher.enrich_all(content_type="both")

        if "error" in report:
            print(f"\n❌ Enrichment failed: {report['error']}")
            return 1

        print("\n✅ Persona enrichment completed successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Enrichment failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
