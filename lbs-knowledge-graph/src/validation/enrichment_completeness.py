"""
Enrichment Completeness Checker

Verifies that all content items and pages have been enriched with semantic data.
Target: ≥95% completeness across all enrichment types.
"""

import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict
from dataclasses import dataclass, asdict

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.db_utils import get_db_connection


@dataclass
class CompletenessMetrics:
    """Enrichment completeness metrics"""
    total_content_items: int
    total_pages: int

    # Sentiment enrichment
    sentiment_enriched_items: int
    sentiment_completeness: float

    # Topic enrichment
    topic_enriched_pages: int
    topic_completeness: float

    # Persona enrichment
    persona_enriched_pages: int
    persona_completeness: float

    # Entity enrichment
    entity_enriched_pages: int
    entity_completeness: float

    # Overall completeness
    overall_completeness: float
    passed: bool  # True if overall ≥ 95%


class EnrichmentCompletenessChecker:
    """Checks completeness of semantic enrichment"""

    def __init__(self, db_path: str = "data/lbs_knowledge_graph.db"):
        self.db_path = db_path
        self.target_completeness = 0.95

    def check_completeness(self) -> CompletenessMetrics:
        """
        Check enrichment completeness across all types.

        Returns:
            Completeness metrics for all enrichment types
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Total counts
        cursor.execute("SELECT COUNT(*) FROM content_items")
        total_content_items = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pages")
        total_pages = cursor.fetchone()[0]

        # Sentiment enrichment (content items)
        cursor.execute("""
            SELECT COUNT(*)
            FROM content_items
            WHERE sentiment IS NOT NULL
        """)
        sentiment_enriched = cursor.fetchone()[0]

        # Topic enrichment (pages with topics)
        cursor.execute("""
            SELECT COUNT(DISTINCT page_id)
            FROM has_topic
        """)
        topic_enriched = cursor.fetchone()[0]

        # Persona enrichment (pages with persona targeting)
        cursor.execute("""
            SELECT COUNT(DISTINCT page_id)
            FROM targets
        """)
        persona_enriched = cursor.fetchone()[0]

        # Entity enrichment (pages with entities)
        cursor.execute("""
            SELECT COUNT(DISTINCT page_id)
            FROM entity_graph
        """)
        entity_enriched = cursor.fetchone()[0]

        conn.close()

        # Calculate completeness percentages
        sentiment_completeness = sentiment_enriched / total_content_items if total_content_items > 0 else 0.0
        topic_completeness = topic_enriched / total_pages if total_pages > 0 else 0.0
        persona_completeness = persona_enriched / total_pages if total_pages > 0 else 0.0
        entity_completeness = entity_enriched / total_pages if total_pages > 0 else 0.0

        # Overall completeness (weighted average)
        # Weight: sentiment 40%, topics 25%, personas 20%, entities 15%
        overall_completeness = (
            sentiment_completeness * 0.40 +
            topic_completeness * 0.25 +
            persona_completeness * 0.20 +
            entity_completeness * 0.15
        )

        metrics = CompletenessMetrics(
            total_content_items=total_content_items,
            total_pages=total_pages,
            sentiment_enriched_items=sentiment_enriched,
            sentiment_completeness=sentiment_completeness,
            topic_enriched_pages=topic_enriched,
            topic_completeness=topic_completeness,
            persona_enriched_pages=persona_enriched,
            persona_completeness=persona_completeness,
            entity_enriched_pages=entity_enriched,
            entity_completeness=entity_completeness,
            overall_completeness=overall_completeness,
            passed=(overall_completeness >= self.target_completeness)
        )

        return metrics

    def generate_report(self, metrics: CompletenessMetrics) -> str:
        """Generate human-readable completeness report"""
        report = []
        report.append("\n" + "="*60)
        report.append("ENRICHMENT COMPLETENESS REPORT")
        report.append("="*60)
        report.append(f"\nTotal Content Items: {metrics.total_content_items}")
        report.append(f"Total Pages: {metrics.total_pages}")
        report.append(f"\nTarget Completeness: {self.target_completeness * 100}%")
        report.append(f"Actual Completeness: {metrics.overall_completeness * 100:.2f}%")
        report.append(f"Status: {'✅ PASSED' if metrics.passed else '❌ FAILED'}\n")

        report.append("-"*60)
        report.append("ENRICHMENT TYPE COMPLETENESS")
        report.append("-"*60)

        # Sentiment
        status = "✅" if metrics.sentiment_completeness >= self.target_completeness else "❌"
        report.append(f"{status} Sentiment Analysis:")
        report.append(f"   {metrics.sentiment_enriched_items}/{metrics.total_content_items} items enriched")
        report.append(f"   Completeness: {metrics.sentiment_completeness * 100:.2f}%\n")

        # Topics
        status = "✅" if metrics.topic_completeness >= self.target_completeness else "❌"
        report.append(f"{status} Topic Extraction:")
        report.append(f"   {metrics.topic_enriched_pages}/{metrics.total_pages} pages enriched")
        report.append(f"   Completeness: {metrics.topic_completeness * 100:.2f}%\n")

        # Personas
        status = "✅" if metrics.persona_completeness >= self.target_completeness else "❌"
        report.append(f"{status} Persona Targeting:")
        report.append(f"   {metrics.persona_enriched_pages}/{metrics.total_pages} pages enriched")
        report.append(f"   Completeness: {metrics.persona_completeness * 100:.2f}%\n")

        # Entities
        status = "✅" if metrics.entity_completeness >= self.target_completeness else "❌"
        report.append(f"{status} Entity Extraction:")
        report.append(f"   {metrics.entity_enriched_pages}/{metrics.total_pages} pages enriched")
        report.append(f"   Completeness: {metrics.entity_completeness * 100:.2f}%\n")

        # Recommendations
        report.append("="*60)
        report.append("RECOMMENDATIONS")
        report.append("="*60)
        if metrics.passed:
            report.append("✅ All enrichment types meet completeness target")
        else:
            report.append("❌ Enrichment not complete across all types")
            report.append("\nActions required:")

            if metrics.sentiment_completeness < self.target_completeness:
                missing = metrics.total_content_items - metrics.sentiment_enriched_items
                report.append(f"- Run sentiment analysis on {missing} remaining content items")

            if metrics.topic_completeness < self.target_completeness:
                missing = metrics.total_pages - metrics.topic_enriched_pages
                report.append(f"- Run topic extraction on {missing} remaining pages")

            if metrics.persona_completeness < self.target_completeness:
                missing = metrics.total_pages - metrics.persona_enriched_pages
                report.append(f"- Run persona classification on {missing} remaining pages")

            if metrics.entity_completeness < self.target_completeness:
                missing = metrics.total_pages - metrics.entity_enriched_pages
                report.append(f"- Run entity extraction on {missing} remaining pages")

        report.append("\n" + "="*60 + "\n")

        return "\n".join(report)

    def get_missing_items(self) -> Dict[str, list]:
        """
        Get IDs of items missing enrichment.

        Returns:
            Dictionary with lists of missing IDs for each enrichment type
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        missing = {}

        # Missing sentiment
        cursor.execute("""
            SELECT content_id
            FROM content_items
            WHERE sentiment IS NULL
            LIMIT 100
        """)
        missing['sentiment'] = [row[0] for row in cursor.fetchall()]

        # Missing topics
        cursor.execute("""
            SELECT page_id
            FROM pages
            WHERE page_id NOT IN (SELECT DISTINCT page_id FROM has_topic)
            LIMIT 100
        """)
        missing['topics'] = [row[0] for row in cursor.fetchall()]

        # Missing personas
        cursor.execute("""
            SELECT page_id
            FROM pages
            WHERE page_id NOT IN (SELECT DISTINCT page_id FROM targets)
            LIMIT 100
        """)
        missing['personas'] = [row[0] for row in cursor.fetchall()]

        # Missing entities
        cursor.execute("""
            SELECT page_id
            FROM pages
            WHERE page_id NOT IN (SELECT DISTINCT page_id FROM entity_graph)
            LIMIT 100
        """)
        missing['entities'] = [row[0] for row in cursor.fetchall()]

        conn.close()

        return missing


if __name__ == "__main__":
    checker = EnrichmentCompletenessChecker()

    print("Checking enrichment completeness...")
    metrics = checker.check_completeness()

    report = checker.generate_report(metrics)
    print(report)

    # Save metrics
    output_file = Path("data/validation_results_completeness.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(asdict(metrics), f, indent=2)
    print(f"Results saved to: {output_file}")

    # Get missing items if not complete
    if not metrics.passed:
        print("\nGetting missing item IDs...")
        missing = checker.get_missing_items()

        missing_file = Path("data/missing_enrichments.json")
        with open(missing_file, 'w') as f:
            json.dump(missing, f, indent=2)
        print(f"Missing item IDs saved to: {missing_file}")
