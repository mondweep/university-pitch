#!/usr/bin/env python3
"""
Cost Report Generator
Generates comprehensive cost reports from LLM API usage tracking
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse


class CostReportGenerator:
    """Generate comprehensive cost reports"""

    def __init__(self, cost_data_dir: str = "data/costs"):
        self.cost_data_dir = Path(cost_data_dir)
        self.cost_data_dir.mkdir(parents=True, exist_ok=True)

    def load_cost_data(self) -> Dict[str, float]:
        """Load all cost tracking data"""
        breakdown = {}

        if self.cost_data_dir.exists():
            for cost_file in self.cost_data_dir.glob("*.json"):
                try:
                    with open(cost_file) as f:
                        data = json.load(f)
                        task = cost_file.stem

                        # Handle different cost data formats
                        if isinstance(data, dict):
                            if "total_cost" in data:
                                breakdown[task] = data["total_cost"]
                            elif "cost" in data:
                                breakdown[task] = data["cost"]
                            else:
                                # Sum up all numeric values
                                breakdown[task] = sum(
                                    v for v in data.values()
                                    if isinstance(v, (int, float))
                                )
                        else:
                            breakdown[task] = 0.0

                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Could not parse {cost_file}: {e}", file=sys.stderr)

        return breakdown

    def calculate_totals(self, breakdown: Dict[str, float]) -> Dict:
        """Calculate total costs and percentages"""
        total_cost = sum(breakdown.values())
        max_cost = float(os.getenv("MAX_LLM_COST", "50.00"))
        percentage_used = (total_cost / max_cost) * 100 if max_cost > 0 else 0

        # Determine status
        if percentage_used < 80:
            status = "OK"
        elif percentage_used < 95:
            status = "WARNING"
        else:
            status = "CRITICAL"

        return {
            "total_cost": round(total_cost, 2),
            "max_cost": max_cost,
            "percentage_used": round(percentage_used, 1),
            "status": status
        }

    def analyze_by_category(self, breakdown: Dict[str, float]) -> Dict:
        """Categorize costs by enrichment type"""
        categories = {
            "sentiment": 0.0,
            "topics": 0.0,
            "ner": 0.0,
            "personas": 0.0,
            "similarity": 0.0,
            "clustering": 0.0,
            "other": 0.0
        }

        for task, cost in breakdown.items():
            task_lower = task.lower()
            categorized = False

            for category in categories.keys():
                if category in task_lower:
                    categories[category] += cost
                    categorized = True
                    break

            if not categorized:
                categories["other"] += cost

        # Filter out zero categories
        return {k: round(v, 2) for k, v in categories.items() if v > 0}

    def get_top_consumers(self, breakdown: Dict[str, float], limit: int = 5) -> List[Dict]:
        """Get top cost-consuming tasks"""
        sorted_tasks = sorted(
            breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {"task": task, "cost": round(cost, 2)}
            for task, cost in sorted_tasks[:limit]
        ]

    def generate_recommendations(self, report: Dict) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []

        percentage = report["percentage_used"]

        if percentage > 80:
            recommendations.append(
                "⚠️ High budget usage - consider optimizing batch sizes"
            )

        if percentage > 95:
            recommendations.append(
                "🚨 CRITICAL: Budget nearly exhausted - immediate action required"
            )

        # Check category distribution
        if "by_category" in report:
            categories = report["by_category"]
            max_category = max(categories.items(), key=lambda x: x[1])

            if max_category[1] > report["total_cost"] * 0.5:
                recommendations.append(
                    f"💡 {max_category[0]} accounts for >50% of costs - "
                    f"consider optimization or cheaper model"
                )

        if not recommendations:
            recommendations.append("✅ Cost usage is within acceptable limits")

        return recommendations

    def generate_report(self, output_file: Optional[str] = None) -> Dict:
        """Generate complete cost report"""
        breakdown = self.load_cost_data()
        totals = self.calculate_totals(breakdown)
        categories = self.analyze_by_category(breakdown)
        top_consumers = self.get_top_consumers(breakdown)

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_cost": totals["total_cost"],
            "max_cost": totals["max_cost"],
            "percentage_used": totals["percentage_used"],
            "status": totals["status"],
            "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
            "by_category": categories,
            "top_consumers": top_consumers,
            "task_count": len(breakdown)
        }

        # Add recommendations
        report["recommendations"] = self.generate_recommendations(report)

        # Save report
        if output_file:
            output_path = Path(output_file)
        else:
            output_path = Path("cost_report.json")

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def print_summary(self, report: Dict):
        """Print human-readable summary"""
        print("\n" + "="*60)
        print("💰 LLM COST REPORT")
        print("="*60)
        print(f"\nGenerated: {report['generated_at']}")
        print(f"\nTotal Cost: ${report['total_cost']:.2f}")
        print(f"Max Budget: ${report['max_cost']:.2f}")
        print(f"Usage: {report['percentage_used']:.1f}%")
        print(f"Status: {report['status']}")

        if report.get("by_category"):
            print("\n📊 Cost by Category:")
            for category, cost in sorted(
                report["by_category"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                percentage = (cost / report["total_cost"]) * 100
                print(f"  - {category:12s}: ${cost:6.2f} ({percentage:5.1f}%)")

        if report.get("top_consumers"):
            print("\n🔝 Top Cost Consumers:")
            for i, item in enumerate(report["top_consumers"], 1):
                print(f"  {i}. {item['task']:20s}: ${item['cost']:.2f}")

        if report.get("recommendations"):
            print("\n💡 Recommendations:")
            for rec in report["recommendations"]:
                print(f"  {rec}")

        print("\n" + "="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate LLM cost reports"
    )
    parser.add_argument(
        "--cost-dir",
        default="data/costs",
        help="Directory containing cost tracking files"
    )
    parser.add_argument(
        "--output",
        default="cost_report.json",
        help="Output file for JSON report"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output"
    )

    args = parser.parse_args()

    # Generate report
    generator = CostReportGenerator(args.cost_dir)
    report = generator.generate_report(args.output)

    # Print summary unless quiet
    if not args.quiet:
        generator.print_summary(report)

    # Exit with error code if status is critical
    if report["status"] == "CRITICAL":
        sys.exit(1)
    elif report["status"] == "WARNING":
        sys.exit(0)  # Warning but not critical
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
