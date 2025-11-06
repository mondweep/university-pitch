#!/usr/bin/env python3
"""
Cost Budget Monitoring Script

Checks enrichment pipeline costs against budget limits and fails the build if exceeded.
Sends alerts when approaching limit (90%).
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class CostSummary:
    """Cost summary statistics"""
    total_cost: float
    budget_limit: float
    usage_percentage: float
    budget_exceeded: bool
    budget_warning: bool
    cost_breakdown: Dict[str, float]


def load_cost_log(log_file: Path) -> Dict[str, Any]:
    """Load cost log from enrichment run"""
    if not log_file.exists():
        print(f"⚠️  Cost log not found: {log_file}")
        return {
            "total_cost": 0.0,
            "operations": []
        }

    with open(log_file, 'r') as f:
        return json.load(f)


def calculate_total_cost(cost_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate total cost and breakdown by operation type"""
    breakdown = {}

    for operation in cost_data.get('operations', []):
        op_type = operation.get('operation_type', 'unknown')
        cost = operation.get('cost', 0.0)
        breakdown[op_type] = breakdown.get(op_type, 0.0) + cost

    # Add direct total if available
    if 'total_cost' in cost_data:
        breakdown['total'] = cost_data['total_cost']
    else:
        breakdown['total'] = sum(breakdown.values())

    return breakdown


def check_budget(cost_log_path: Path, budget_limit: float) -> CostSummary:
    """Check if costs are within budget"""
    cost_data = load_cost_log(cost_log_path)
    breakdown = calculate_total_cost(cost_data)
    total_cost = breakdown.get('total', 0.0)

    usage_percentage = (total_cost / budget_limit) * 100 if budget_limit > 0 else 0
    budget_exceeded = total_cost > budget_limit
    budget_warning = usage_percentage >= 90.0 and not budget_exceeded

    return CostSummary(
        total_cost=total_cost,
        budget_limit=budget_limit,
        usage_percentage=usage_percentage,
        budget_exceeded=budget_exceeded,
        budget_warning=budget_warning,
        cost_breakdown=breakdown
    )


def print_summary(summary: CostSummary, output_format: str = 'text'):
    """Print cost summary in specified format"""
    if output_format == 'github':
        print_github_actions_output(summary)
    elif output_format == 'json':
        print_json_output(summary)
    else:
        print_text_output(summary)


def print_text_output(summary: CostSummary):
    """Print human-readable text output"""
    print("\n" + "="*60)
    print("💰 COST BUDGET SUMMARY")
    print("="*60)
    print(f"\nTotal Cost:      ${summary.total_cost:.2f}")
    print(f"Budget Limit:    ${summary.budget_limit:.2f}")
    print(f"Usage:           {summary.usage_percentage:.1f}%")
    print(f"Remaining:       ${summary.budget_limit - summary.total_cost:.2f}")

    print("\n📊 Cost Breakdown:")
    for op_type, cost in summary.cost_breakdown.items():
        if op_type != 'total':
            percentage = (cost / summary.total_cost * 100) if summary.total_cost > 0 else 0
            print(f"  • {op_type:20s}: ${cost:8.2f} ({percentage:5.1f}%)")

    print("\n" + "-"*60)

    if summary.budget_exceeded:
        print("❌ BUDGET EXCEEDED!")
        print(f"   Cost exceeds budget by ${summary.total_cost - summary.budget_limit:.2f}")
    elif summary.budget_warning:
        print("⚠️  BUDGET WARNING!")
        print(f"   Approaching budget limit ({summary.usage_percentage:.1f}% used)")
    else:
        print("✅ WITHIN BUDGET")
        print(f"   {100 - summary.usage_percentage:.1f}% budget remaining")

    print("="*60 + "\n")


def print_json_output(summary: CostSummary):
    """Print JSON output"""
    output = {
        "total_cost": summary.total_cost,
        "budget_limit": summary.budget_limit,
        "usage_percentage": summary.usage_percentage,
        "budget_exceeded": summary.budget_exceeded,
        "budget_warning": summary.budget_warning,
        "remaining": summary.budget_limit - summary.total_cost,
        "cost_breakdown": summary.cost_breakdown
    }
    print(json.dumps(output, indent=2))


def print_github_actions_output(summary: CostSummary):
    """Print GitHub Actions compatible output"""
    # Print text summary
    print_text_output(summary)

    # Set output variables for GitHub Actions
    print(f"::set-output name=total_cost::{summary.total_cost}")
    print(f"::set-output name=budget_limit::{summary.budget_limit}")
    print(f"::set-output name=usage_percentage::{summary.usage_percentage:.1f}")
    print(f"::set-output name=budget_exceeded::{str(summary.budget_exceeded).lower()}")
    print(f"::set-output name=budget_warning::{str(summary.budget_warning).lower()}")

    # Set environment variables
    print(f"CURRENT_COST={summary.total_cost:.2f}")
    print(f"COST_PERCENTAGE={summary.usage_percentage:.1f}")

    # Add annotations
    if summary.budget_exceeded:
        print(f"::error::Budget exceeded! Cost: ${summary.total_cost:.2f}, Limit: ${summary.budget_limit:.2f}")
    elif summary.budget_warning:
        print(f"::warning::Approaching budget limit! Usage: {summary.usage_percentage:.1f}%")


def send_alert(summary: CostSummary, alert_type: str):
    """Send alert notification (placeholder for future integration)"""
    # Future: Integration with Slack, email, or other notification systems
    pass


def main():
    parser = argparse.ArgumentParser(description='Check enrichment pipeline cost budget')
    parser.add_argument('--limit', type=float, required=True,
                       help='Cost budget limit in USD')
    parser.add_argument('--log-file', type=str, default='logs/enrichment_cost.json',
                       help='Path to cost log file')
    parser.add_argument('--output-format', choices=['text', 'json', 'github'],
                       default='text', help='Output format')
    parser.add_argument('--fail-on-exceeded', action='store_true', default=True,
                       help='Exit with error code if budget exceeded')
    parser.add_argument('--warning-threshold', type=float, default=90.0,
                       help='Warning threshold percentage (default: 90%%)')

    args = parser.parse_args()

    # Convert log file path to Path object
    log_file = Path(args.log_file)

    # Check budget
    summary = check_budget(log_file, args.limit)

    # Print summary
    print_summary(summary, args.output_format)

    # Send alerts if needed
    if summary.budget_exceeded or summary.budget_warning:
        send_alert(summary, 'exceeded' if summary.budget_exceeded else 'warning')

    # Exit with error code if budget exceeded
    if args.fail_on_exceeded and summary.budget_exceeded:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
