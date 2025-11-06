"""
Cost tracking and budget management for LLM operations.

Features:
- Per-enrichment-type cost tracking
- Budget alerts
- Usage reports
- Optimization recommendations
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class CostTracker:
    """
    Track and manage LLM API costs with budget controls.
    """

    def __init__(
        self,
        budget_limit: float = 50.0,
        alert_threshold: float = 0.8,
        save_path: Optional[str] = None
    ):
        """
        Initialize cost tracker.

        Args:
            budget_limit: Maximum budget in USD
            alert_threshold: Alert when usage reaches this fraction of budget
            save_path: Path to save cost data (JSON)
        """
        self.budget_limit = budget_limit
        self.alert_threshold = alert_threshold
        self.save_path = save_path

        # Cost tracking by enrichment type
        self.costs: Dict[str, Dict] = {
            "sentiment": {"requests": 0, "tokens": 0, "cost": 0.0},
            "topics": {"requests": 0, "tokens": 0, "cost": 0.0},
            "personas": {"requests": 0, "tokens": 0, "cost": 0.0},
            "entities": {"requests": 0, "tokens": 0, "cost": 0.0},
            "journey": {"requests": 0, "tokens": 0, "cost": 0.0},
            "similarity": {"requests": 0, "tokens": 0, "cost": 0.0},
            "other": {"requests": 0, "tokens": 0, "cost": 0.0}
        }

        # Session tracking
        self.session_start = datetime.now()
        self.total_cost = 0.0
        self.alerts_sent = []

        # Load existing data if available
        if save_path and Path(save_path).exists():
            self.load_from_file(save_path)

    def track_request(
        self,
        enrichment_type: str,
        cost: float,
        input_tokens: int = 0,
        output_tokens: int = 0
    ):
        """
        Track a single request's cost.

        Args:
            enrichment_type: Type of enrichment
            cost: Request cost in USD
            input_tokens: Input token count
            output_tokens: Output token count
        """
        # Normalize enrichment type
        if enrichment_type not in self.costs:
            enrichment_type = "other"

        # Update tracking
        self.costs[enrichment_type]["requests"] += 1
        self.costs[enrichment_type]["tokens"] += input_tokens + output_tokens
        self.costs[enrichment_type]["cost"] += cost

        self.total_cost += cost

        # Check budget alert
        self._check_budget_alert()

        # Auto-save if path configured
        if self.save_path:
            self.save_to_file(self.save_path)

    def _check_budget_alert(self):
        """Check if budget alert should be triggered."""
        usage_ratio = self.total_cost / self.budget_limit

        if usage_ratio >= self.alert_threshold:
            alert_msg = (
                f"⚠️ Budget Alert: ${self.total_cost:.2f} / ${self.budget_limit:.2f} "
                f"({usage_ratio*100:.1f}% used)"
            )

            # Only alert once per threshold
            if alert_msg not in self.alerts_sent:
                print(f"\n{alert_msg}\n")
                self.alerts_sent.append(alert_msg)

    def get_total_cost(self) -> float:
        """Get total cost across all enrichment types."""
        return self.total_cost

    def get_cost_by_type(self, enrichment_type: str) -> Dict:
        """
        Get cost breakdown for specific enrichment type.

        Args:
            enrichment_type: Type of enrichment

        Returns:
            Dict with cost breakdown
        """
        if enrichment_type not in self.costs:
            return {"requests": 0, "tokens": 0, "cost": 0.0}

        return self.costs[enrichment_type].copy()

    def get_cost_report(self) -> Dict:
        """
        Generate comprehensive cost report.

        Returns:
            Dict with detailed cost breakdown
        """
        # Calculate session duration
        duration = (datetime.now() - self.session_start).total_seconds()

        # Calculate per-type percentages
        type_breakdown = {}
        for etype, data in self.costs.items():
            if data["cost"] > 0:
                type_breakdown[etype] = {
                    **data,
                    "percentage": (data["cost"] / max(self.total_cost, 0.01)) * 100,
                    "avg_cost_per_request": data["cost"] / max(data["requests"], 1)
                }

        return {
            "total_cost": self.total_cost,
            "budget_limit": self.budget_limit,
            "budget_remaining": max(self.budget_limit - self.total_cost, 0),
            "budget_used_percentage": (self.total_cost / self.budget_limit) * 100,
            "session_duration_seconds": duration,
            "session_start": self.session_start.isoformat(),
            "type_breakdown": type_breakdown,
            "total_requests": sum(d["requests"] for d in self.costs.values()),
            "total_tokens": sum(d["tokens"] for d in self.costs.values()),
            "alerts": self.alerts_sent
        }

    def print_report(self):
        """Print formatted cost report."""
        report = self.get_cost_report()

        print("\n" + "="*60)
        print("LLM COST REPORT")
        print("="*60)

        print(f"\n💰 Total Cost: ${report['total_cost']:.2f}")
        print(f"📊 Budget: ${report['budget_limit']:.2f}")
        print(f"✅ Remaining: ${report['budget_remaining']:.2f}")
        print(f"📈 Used: {report['budget_used_percentage']:.1f}%")

        print(f"\n📊 Total Requests: {report['total_requests']}")
        print(f"🔤 Total Tokens: {report['total_tokens']:,}")

        if report['type_breakdown']:
            print("\n📋 Cost by Enrichment Type:")
            print("-" * 60)

            for etype, data in sorted(
                report['type_breakdown'].items(),
                key=lambda x: x[1]['cost'],
                reverse=True
            ):
                print(f"\n{etype.upper()}:")
                print(f"  Requests: {data['requests']}")
                print(f"  Tokens: {data['tokens']:,}")
                print(f"  Cost: ${data['cost']:.2f} ({data['percentage']:.1f}%)")
                print(f"  Avg per request: ${data['avg_cost_per_request']:.4f}")

        # Optimization recommendations
        print("\n💡 Optimization Recommendations:")
        self._print_recommendations(report)

        print("\n" + "="*60 + "\n")

    def _print_recommendations(self, report: Dict):
        """Print optimization recommendations based on usage."""
        recommendations = []

        # Check if over budget
        if report['total_cost'] > report['budget_limit']:
            recommendations.append(
                "⚠️ Over budget! Consider reducing batch sizes or using cheaper models."
            )

        # Check for expensive operations
        for etype, data in report['type_breakdown'].items():
            if data['percentage'] > 40:
                recommendations.append(
                    f"⚠️ {etype} accounts for {data['percentage']:.1f}% of costs. "
                    "Consider caching or optimizing prompts."
                )

            if data['avg_cost_per_request'] > 0.05:
                recommendations.append(
                    f"💡 {etype} has high per-request cost (${data['avg_cost_per_request']:.4f}). "
                    "Consider switching to a cheaper model."
                )

        # Check token usage
        total_tokens = report['total_tokens']
        if total_tokens > 1_000_000:
            recommendations.append(
                "💡 High token usage detected. Consider reducing prompt length or output tokens."
            )

        # Check request count
        if report['total_requests'] > 100:
            avg_cost = report['total_cost'] / report['total_requests']
            if avg_cost > 0.01:
                recommendations.append(
                    "💡 High average cost per request. Increase batch size to reduce costs."
                )

        if not recommendations:
            recommendations.append("✅ Cost usage is well optimized!")

        for rec in recommendations:
            print(f"  {rec}")

    def estimate_completion_cost(
        self,
        items_remaining: int,
        enrichment_type: str
    ) -> Dict:
        """
        Estimate cost to complete remaining items.

        Args:
            items_remaining: Number of items left to process
            enrichment_type: Type of enrichment

        Returns:
            Dict with cost estimates
        """
        if enrichment_type not in self.costs:
            enrichment_type = "other"

        type_data = self.costs[enrichment_type]

        if type_data["requests"] == 0:
            return {
                "estimated_cost": 0.0,
                "warning": "No historical data for cost estimation"
            }

        # Calculate average cost per item (assuming batch processing)
        avg_cost_per_item = type_data["cost"] / max(type_data["requests"], 1)

        estimated_cost = avg_cost_per_item * items_remaining

        return {
            "items_remaining": items_remaining,
            "enrichment_type": enrichment_type,
            "avg_cost_per_item": avg_cost_per_item,
            "estimated_cost": estimated_cost,
            "projected_total": self.total_cost + estimated_cost,
            "will_exceed_budget": (self.total_cost + estimated_cost) > self.budget_limit
        }

    def save_to_file(self, path: str):
        """
        Save cost data to JSON file.

        Args:
            path: File path to save to
        """
        data = {
            "session_start": self.session_start.isoformat(),
            "budget_limit": self.budget_limit,
            "total_cost": self.total_cost,
            "costs": self.costs,
            "alerts": self.alerts_sent
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, path: str):
        """
        Load cost data from JSON file.

        Args:
            path: File path to load from
        """
        with open(path, 'r') as f:
            data = json.load(f)

        self.session_start = datetime.fromisoformat(data["session_start"])
        self.budget_limit = data["budget_limit"]
        self.total_cost = data["total_cost"]
        self.costs = data["costs"]
        self.alerts_sent = data.get("alerts", [])

    def reset(self):
        """Reset all cost tracking data."""
        for etype in self.costs:
            self.costs[etype] = {"requests": 0, "tokens": 0, "cost": 0.0}

        self.session_start = datetime.now()
        self.total_cost = 0.0
        self.alerts_sent = []
