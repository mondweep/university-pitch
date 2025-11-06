"""
Phase 3 Master Validation Suite

Orchestrates all Phase 3 validation tests and generates comprehensive quality report.
Validates: sentiment, topics, NER, personas, completeness, and cost.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass, asdict

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.validation.sentiment_validator import SentimentValidator
from src.validation.topic_validator import TopicValidator
from src.validation.ner_validator import NERValidator
from src.validation.persona_validator import PersonaValidator
from src.validation.enrichment_completeness import EnrichmentCompletenessChecker
from src.validation.cost_validator import CostValidator


@dataclass
class Phase3ValidationResults:
    """Aggregated Phase 3 validation results"""
    timestamp: str
    sentiment_passed: bool
    sentiment_accuracy: float
    topic_passed: bool
    topic_precision: float
    ner_passed: bool
    ner_precision: float
    persona_passed: bool
    persona_accuracy: float
    completeness_passed: bool
    completeness_percentage: float
    cost_passed: bool
    total_cost: float
    budget: float
    overall_passed: bool
    pass_count: int
    fail_count: int


class Phase3ValidationSuite:
    """Master validation suite for Phase 3"""

    def __init__(self):
        self.results = {}
        self.validators = {
            'sentiment': SentimentValidator(),
            'topic': TopicValidator(),
            'ner': NERValidator(),
            'persona': PersonaValidator(),
            'completeness': EnrichmentCompletenessChecker(),
            'cost': CostValidator(budget=50.0)
        }

    def run_all_validations(self) -> Phase3ValidationResults:
        """
        Run all Phase 3 validation tests.

        Returns:
            Aggregated validation results
        """
        print("\n" + "="*70)
        print("PHASE 3 VALIDATION SUITE - COMPREHENSIVE QUALITY VALIDATION")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        results = {}

        # 1. Sentiment Validation
        print("="*70)
        print("1/6: SENTIMENT ANALYSIS VALIDATION")
        print("="*70)
        try:
            self.validators['sentiment'].load_ground_truth()
            sentiment_metrics = self.validators['sentiment'].validate_sentiment_accuracy()
            print(self.validators['sentiment'].generate_report(sentiment_metrics))
            results['sentiment'] = {
                'passed': sentiment_metrics.passed,
                'accuracy': sentiment_metrics.accuracy,
                'metrics': {
                    'precision': sentiment_metrics.precision,
                    'recall': sentiment_metrics.recall,
                    'f1_score': sentiment_metrics.f1_score
                }
            }
        except Exception as e:
            print(f"❌ Sentiment validation failed: {e}")
            results['sentiment'] = {'passed': False, 'accuracy': 0.0, 'error': str(e)}

        # 2. Topic Validation
        print("\n" + "="*70)
        print("2/6: TOPIC EXTRACTION VALIDATION")
        print("="*70)
        try:
            self.validators['topic'].load_ground_truth()
            topic_metrics = self.validators['topic'].validate_topic_extraction()
            print(self.validators['topic'].generate_report(topic_metrics))
            results['topic'] = {
                'passed': topic_metrics.passed,
                'precision': topic_metrics.precision,
                'recall': topic_metrics.recall,
                'f1_score': topic_metrics.f1_score
            }
        except Exception as e:
            print(f"❌ Topic validation failed: {e}")
            results['topic'] = {'passed': False, 'precision': 0.0, 'error': str(e)}

        # 3. NER Validation
        print("\n" + "="*70)
        print("3/6: NAMED ENTITY RECOGNITION VALIDATION")
        print("="*70)
        try:
            self.validators['ner'].load_ground_truth()
            ner_metrics = self.validators['ner'].validate_ner_extraction()
            print(self.validators['ner'].generate_report(ner_metrics))
            results['ner'] = {
                'passed': ner_metrics.passed,
                'exact_match_precision': ner_metrics.exact_match_precision,
                'exact_match_recall': ner_metrics.exact_match_recall,
                'type_accuracy': ner_metrics.type_accuracy
            }
        except Exception as e:
            print(f"❌ NER validation failed: {e}")
            results['ner'] = {'passed': False, 'exact_match_precision': 0.0, 'error': str(e)}

        # 4. Persona Validation
        print("\n" + "="*70)
        print("4/6: PERSONA CLASSIFICATION VALIDATION")
        print("="*70)
        try:
            self.validators['persona'].load_ground_truth()
            persona_metrics = self.validators['persona'].validate_persona_classification()
            print(self.validators['persona'].generate_report(persona_metrics))
            results['persona'] = {
                'passed': persona_metrics.passed,
                'subset_accuracy': persona_metrics.subset_accuracy,
                'precision_micro': persona_metrics.precision_micro,
                'recall_micro': persona_metrics.recall_micro,
                'f1_micro': persona_metrics.f1_micro
            }
        except Exception as e:
            print(f"❌ Persona validation failed: {e}")
            results['persona'] = {'passed': False, 'subset_accuracy': 0.0, 'error': str(e)}

        # 5. Completeness Check
        print("\n" + "="*70)
        print("5/6: ENRICHMENT COMPLETENESS CHECK")
        print("="*70)
        try:
            completeness_metrics = self.validators['completeness'].check_completeness()
            print(self.validators['completeness'].generate_report(completeness_metrics))
            results['completeness'] = {
                'passed': completeness_metrics.passed,
                'overall_completeness': completeness_metrics.overall_completeness,
                'sentiment_completeness': completeness_metrics.sentiment_completeness,
                'topic_completeness': completeness_metrics.topic_completeness,
                'persona_completeness': completeness_metrics.persona_completeness,
                'entity_completeness': completeness_metrics.entity_completeness
            }
        except Exception as e:
            print(f"❌ Completeness check failed: {e}")
            results['completeness'] = {'passed': False, 'overall_completeness': 0.0, 'error': str(e)}

        # 6. Cost Validation
        print("\n" + "="*70)
        print("6/6: COST VALIDATION")
        print("="*70)
        try:
            cost_breakdown = self.validators['cost'].validate_costs()
            print(self.validators['cost'].generate_report(cost_breakdown))
            results['cost'] = {
                'passed': cost_breakdown.passed,
                'total_cost': cost_breakdown.total_cost,
                'budget': cost_breakdown.budget,
                'breakdown': {
                    'sentiment': cost_breakdown.sentiment_analysis_cost,
                    'topic': cost_breakdown.topic_extraction_cost,
                    'persona': cost_breakdown.persona_classification_cost,
                    'ner': cost_breakdown.entity_extraction_cost,
                    'embedding': cost_breakdown.embedding_generation_cost
                }
            }
        except Exception as e:
            print(f"❌ Cost validation failed: {e}")
            results['cost'] = {'passed': False, 'total_cost': 0.0, 'error': str(e)}

        # Aggregate results
        self.results = results

        pass_count = sum(1 for v in results.values() if v.get('passed', False))
        fail_count = len(results) - pass_count
        overall_passed = (pass_count == len(results))

        aggregated = Phase3ValidationResults(
            timestamp=datetime.now().isoformat(),
            sentiment_passed=results.get('sentiment', {}).get('passed', False),
            sentiment_accuracy=results.get('sentiment', {}).get('accuracy', 0.0),
            topic_passed=results.get('topic', {}).get('passed', False),
            topic_precision=results.get('topic', {}).get('precision', 0.0),
            ner_passed=results.get('ner', {}).get('passed', False),
            ner_precision=results.get('ner', {}).get('exact_match_precision', 0.0),
            persona_passed=results.get('persona', {}).get('passed', False),
            persona_accuracy=results.get('persona', {}).get('subset_accuracy', 0.0),
            completeness_passed=results.get('completeness', {}).get('passed', False),
            completeness_percentage=results.get('completeness', {}).get('overall_completeness', 0.0),
            cost_passed=results.get('cost', {}).get('passed', False),
            total_cost=results.get('cost', {}).get('total_cost', 0.0),
            budget=results.get('cost', {}).get('budget', 50.0),
            overall_passed=overall_passed,
            pass_count=pass_count,
            fail_count=fail_count
        )

        return aggregated

    def generate_summary_report(self, results: Phase3ValidationResults) -> str:
        """Generate comprehensive summary report"""
        report = []
        report.append("\n" + "="*70)
        report.append("PHASE 3 VALIDATION SUMMARY")
        report.append("="*70)
        report.append(f"Timestamp: {results.timestamp}")
        report.append(f"Overall Status: {'✅ ALL PASSED' if results.overall_passed else '❌ FAILURES DETECTED'}")
        report.append(f"Tests Passed: {results.pass_count}/{results.pass_count + results.fail_count}")
        report.append(f"Tests Failed: {results.fail_count}/{results.pass_count + results.fail_count}\n")

        report.append("-"*70)
        report.append("INDIVIDUAL TEST RESULTS")
        report.append("-"*70)

        tests = [
            ("Sentiment Analysis", results.sentiment_passed, f"{results.sentiment_accuracy*100:.1f}% accuracy"),
            ("Topic Extraction", results.topic_passed, f"{results.topic_precision*100:.1f}% precision"),
            ("NER", results.ner_passed, f"{results.ner_precision*100:.1f}% precision"),
            ("Persona Classification", results.persona_passed, f"{results.persona_accuracy*100:.1f}% accuracy"),
            ("Enrichment Completeness", results.completeness_passed, f"{results.completeness_percentage*100:.1f}% complete"),
            ("Cost Budget", results.cost_passed, f"${results.total_cost:.2f} / ${results.budget:.2f}")
        ]

        for name, passed, metric in tests:
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"{status}  {name:30} {metric}")

        # Phase 3 acceptance criteria
        report.append("\n" + "="*70)
        report.append("PHASE 3 ACCEPTANCE CRITERIA")
        report.append("="*70)

        criteria = [
            ("Sentiment accuracy ≥80%", results.sentiment_accuracy >= 0.80),
            ("Topic precision ≥75%", results.topic_precision >= 0.75),
            ("NER precision ≥85%", results.ner_precision >= 0.85),
            ("Persona accuracy ≥75%", results.persona_accuracy >= 0.75),
            ("Enrichment completeness ≥95%", results.completeness_percentage >= 0.95),
            ("Total cost ≤$50", results.total_cost <= 50.0)
        ]

        for criterion, met in criteria:
            status = "✅" if met else "❌"
            report.append(f"{status}  {criterion}")

        # Overall verdict
        report.append("\n" + "="*70)
        report.append("OVERALL VERDICT")
        report.append("="*70)

        if results.overall_passed:
            report.append("✅ Phase 3 meets ALL acceptance criteria")
            report.append("   Ready for production deployment")
        else:
            report.append("❌ Phase 3 does NOT meet all acceptance criteria")
            report.append("   Additional work required before deployment")

            report.append("\nFailed criteria:")
            for criterion, met in criteria:
                if not met:
                    report.append(f"   - {criterion}")

        report.append("\n" + "="*70 + "\n")

        return "\n".join(report)

    def save_results(self, results: Phase3ValidationResults, output_dir: str = "data") -> None:
        """Save all validation results"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save aggregated results
        results_file = output_path / "phase3_validation_results.json"
        with open(results_file, 'w') as f:
            json.dump(asdict(results), f, indent=2)
        print(f"\nAggregated results saved to: {results_file}")

        # Save detailed results
        detailed_file = output_path / "phase3_validation_detailed.json"
        with open(detailed_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"Detailed results saved to: {detailed_file}")


def main():
    """Main validation entry point"""
    suite = Phase3ValidationSuite()

    # Run all validations
    results = suite.run_all_validations()

    # Generate and print summary
    summary = suite.generate_summary_report(results)
    print(summary)

    # Save results
    suite.save_results(results)

    # Exit code based on results
    exit_code = 0 if results.overall_passed else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
