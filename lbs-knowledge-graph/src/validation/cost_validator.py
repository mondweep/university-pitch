"""
Cost Validation Module

Validates LLM API costs and tracks budget compliance.
Target: Total cost ≤ $50 for all Phase 3 enrichments.
"""

import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))


@dataclass
class CostBreakdown:
    """Cost breakdown by enrichment type"""
    sentiment_analysis_cost: float
    topic_extraction_cost: float
    persona_classification_cost: float
    entity_extraction_cost: float
    embedding_generation_cost: float
    other_costs: float
    total_cost: float
    budget: float
    passed: bool  # True if total_cost ≤ budget


class CostValidator:
    """Validates API costs and budget compliance"""

    def __init__(self, budget: float = 50.0):
        self.budget = budget
        self.cost_log_path = Path("data/llm_cost_log.json")

    def load_cost_log(self) -> Dict:
        """Load cost log from file"""
        if not self.cost_log_path.exists():
            print(f"⚠️  Cost log not found: {self.cost_log_path}")
            print("Creating empty cost log template...")

            template = {
                "sentiment_analysis": {
                    "model": "gpt-3.5-turbo",
                    "total_requests": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "estimated_cost": 0.0
                },
                "topic_extraction": {
                    "model": "gpt-3.5-turbo",
                    "total_requests": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "estimated_cost": 0.0
                },
                "persona_classification": {
                    "model": "gpt-4-turbo",
                    "total_requests": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "estimated_cost": 0.0
                },
                "entity_extraction": {
                    "model": "gpt-4-turbo",
                    "total_requests": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "estimated_cost": 0.0
                },
                "embedding_generation": {
                    "model": "text-embedding-3-small",
                    "total_requests": 0,
                    "total_tokens": 0,
                    "estimated_cost": 0.0
                },
                "other": {
                    "description": "Miscellaneous API calls",
                    "estimated_cost": 0.0
                },
                "total_cost": 0.0,
                "last_updated": datetime.now().isoformat()
            }

            self.cost_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cost_log_path, 'w') as f:
                json.dump(template, f, indent=2)

            print(f"Template saved to: {self.cost_log_path}")
            print("Please update with actual costs as enrichments run.")

            return template

        with open(self.cost_log_path, 'r') as f:
            return json.load(f)

    def validate_costs(self) -> CostBreakdown:
        """
        Validate API costs against budget.

        Returns:
            Cost breakdown with pass/fail status
        """
        cost_log = self.load_cost_log()

        # Extract costs
        sentiment_cost = cost_log.get('sentiment_analysis', {}).get('estimated_cost', 0.0)
        topic_cost = cost_log.get('topic_extraction', {}).get('estimated_cost', 0.0)
        persona_cost = cost_log.get('persona_classification', {}).get('estimated_cost', 0.0)
        entity_cost = cost_log.get('entity_extraction', {}).get('estimated_cost', 0.0)
        embedding_cost = cost_log.get('embedding_generation', {}).get('estimated_cost', 0.0)
        other_cost = cost_log.get('other', {}).get('estimated_cost', 0.0)

        total_cost = cost_log.get('total_cost', 0.0)

        # Recalculate total if not set
        if total_cost == 0.0:
            total_cost = sentiment_cost + topic_cost + persona_cost + entity_cost + embedding_cost + other_cost

        breakdown = CostBreakdown(
            sentiment_analysis_cost=sentiment_cost,
            topic_extraction_cost=topic_cost,
            persona_classification_cost=persona_cost,
            entity_extraction_cost=entity_cost,
            embedding_generation_cost=embedding_cost,
            other_costs=other_cost,
            total_cost=total_cost,
            budget=self.budget,
            passed=(total_cost <= self.budget)
        )

        return breakdown

    def generate_report(self, breakdown: CostBreakdown) -> str:
        """Generate human-readable cost report"""
        report = []
        report.append("\n" + "="*60)
        report.append("COST VALIDATION REPORT")
        report.append("="*60)
        report.append(f"\nBudget: ${breakdown.budget:.2f}")
        report.append(f"Total Cost: ${breakdown.total_cost:.2f}")
        report.append(f"Remaining: ${breakdown.budget - breakdown.total_cost:.2f}")
        report.append(f"\nStatus: {'✅ PASSED' if breakdown.passed else '❌ FAILED'}\n")

        report.append("-"*60)
        report.append("COST BREAKDOWN BY ENRICHMENT TYPE")
        report.append("-"*60)

        costs = [
            ("Sentiment Analysis", breakdown.sentiment_analysis_cost),
            ("Topic Extraction", breakdown.topic_extraction_cost),
            ("Persona Classification", breakdown.persona_classification_cost),
            ("Entity Extraction (NER)", breakdown.entity_extraction_cost),
            ("Embedding Generation", breakdown.embedding_generation_cost),
            ("Other / Miscellaneous", breakdown.other_costs),
        ]

        for name, cost in costs:
            percentage = (cost / breakdown.total_cost * 100) if breakdown.total_cost > 0 else 0
            report.append(f"{name:30} ${cost:7.2f}  ({percentage:5.1f}%)")

        report.append("-"*60)
        report.append(f"{'TOTAL':30} ${breakdown.total_cost:7.2f}  (100.0%)")

        # Budget utilization
        report.append("\n" + "-"*60)
        report.append("BUDGET UTILIZATION")
        report.append("-"*60)
        utilization = (breakdown.total_cost / breakdown.budget * 100) if breakdown.budget > 0 else 0
        report.append(f"Budget Used: {utilization:.1f}%")

        if utilization > 100:
            report.append(f"⚠️  OVER BUDGET by ${breakdown.total_cost - breakdown.budget:.2f}")
        elif utilization > 90:
            report.append(f"⚠️  Near budget limit")
        else:
            report.append(f"✅ Within budget")

        # Cost efficiency metrics
        report.append("\n" + "-"*60)
        report.append("COST EFFICIENCY")
        report.append("-"*60)

        # Load cost log for detailed metrics
        cost_log = self.load_cost_log()

        for task, data in cost_log.items():
            if task in ['sentiment_analysis', 'topic_extraction', 'persona_classification', 'entity_extraction']:
                if isinstance(data, dict) and 'total_requests' in data:
                    requests = data['total_requests']
                    cost = data['estimated_cost']
                    if requests > 0:
                        cost_per_request = cost / requests
                        report.append(f"{task.replace('_', ' ').title():30} ${cost_per_request:.4f} per request")

        # Recommendations
        report.append("\n" + "="*60)
        report.append("RECOMMENDATIONS")
        report.append("="*60)

        if breakdown.passed:
            report.append("✅ Total cost within budget")
            if utilization > 80:
                report.append("\nCost optimization opportunities:")
                report.append("- Increase caching to reduce duplicate API calls")
                report.append("- Use cheaper models for simple tasks")
                report.append("- Batch requests more aggressively")
        else:
            report.append("❌ Total cost exceeds budget")
            report.append("\nImmediate actions:")
            report.append("- Review and optimize expensive enrichments")
            report.append("- Consider downgrading models (GPT-4 → GPT-3.5)")
            report.append("- Increase cache hit rate")
            report.append("- Reduce enrichment scope if necessary")

        report.append("\n" + "="*60 + "\n")

        return "\n".join(report)

    def save_cost_summary(self, breakdown: CostBreakdown, output_path: str = "data/cost_summary.json") -> None:
        """Save cost summary to file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(asdict(breakdown), f, indent=2)

        print(f"Cost summary saved to: {output_file}")


if __name__ == "__main__":
    validator = CostValidator(budget=50.0)

    print("Validating API costs...")
    breakdown = validator.validate_costs()

    report = validator.generate_report(breakdown)
    print(report)

    # Save summary
    validator.save_cost_summary(breakdown)

    # Save to validation results
    output_file = Path("data/validation_results_cost.json")
    with open(output_file, 'w') as f:
        json.dump(asdict(breakdown), f, indent=2)
    print(f"Validation results saved to: {output_file}")
