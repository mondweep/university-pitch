"""
Sentiment Validation Module

Validates sentiment analysis accuracy against ground truth dataset.
Target: ≥80% accuracy with precision, recall, and F1 metrics.
"""

import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import Counter
import random

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.db_utils import get_db_connection


@dataclass
class SentimentGroundTruth:
    """Ground truth sentiment annotation"""
    content_id: str
    text: str
    true_sentiment: str  # 'positive', 'neutral', 'negative'
    true_polarity: float  # -1.0 to 1.0
    annotator: str
    confidence: float


@dataclass
class SentimentValidationMetrics:
    """Sentiment validation metrics"""
    total_items: int
    accuracy: float
    precision: Dict[str, float]
    recall: Dict[str, float]
    f1_score: Dict[str, float]
    confusion_matrix: Dict[Tuple[str, str], int]
    mean_absolute_error: float  # For polarity scores
    passed: bool  # True if accuracy ≥ 80%


class SentimentValidator:
    """Validates sentiment analysis accuracy"""

    def __init__(self, db_path: str = "data/lbs_knowledge_graph.db"):
        self.db_path = db_path
        self.target_accuracy = 0.80
        self.ground_truth: List[SentimentGroundTruth] = []

    def create_ground_truth_dataset(self, sample_size: int = 50) -> List[SentimentGroundTruth]:
        """
        Create ground truth dataset for validation.

        MANUAL STEP REQUIRED: This method creates a template dataset.
        You must manually label the sentiment of each item.

        Args:
            sample_size: Number of content items to manually label

        Returns:
            List of ground truth annotations (requires manual labeling)
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Sample content items with sentiment analysis
        cursor.execute("""
            SELECT content_id, text_content, sentiment
            FROM content_items
            WHERE sentiment IS NOT NULL
            ORDER BY RANDOM()
            LIMIT ?
        """, (sample_size,))

        items = cursor.fetchall()
        conn.close()

        # Create template for manual annotation
        ground_truth_template = []
        for content_id, text, sentiment_json in items:
            # Parse sentiment
            if sentiment_json:
                sentiment_data = json.loads(sentiment_json)
            else:
                sentiment_data = {}

            # Create ground truth template (REQUIRES MANUAL LABELING)
            gt = SentimentGroundTruth(
                content_id=content_id,
                text=text[:500] if text else "",  # First 500 chars for review
                true_sentiment="LABEL_ME",  # MANUAL: Replace with 'positive', 'neutral', or 'negative'
                true_polarity=0.0,  # MANUAL: Replace with -1.0 to 1.0
                annotator="ANNOTATOR_NAME",  # MANUAL: Your name
                confidence=1.0  # MANUAL: Confidence in your label
            )
            ground_truth_template.append(gt)

        # Save template to file for manual annotation
        output_file = Path("data/ground_truth_sentiment_template.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(
                [asdict(gt) for gt in ground_truth_template],
                f,
                indent=2
            )

        print(f"\n{'='*60}")
        print("MANUAL ANNOTATION REQUIRED")
        print(f"{'='*60}")
        print(f"Ground truth template saved to: {output_file}")
        print(f"\nPlease manually label {sample_size} items:")
        print("1. Open the file")
        print("2. For each item, review the text")
        print("3. Set 'true_sentiment' to 'positive', 'neutral', or 'negative'")
        print("4. Set 'true_polarity' to a value from -1.0 to 1.0")
        print("5. Set 'annotator' to your name")
        print("6. Save as 'data/ground_truth_sentiment.json'")
        print(f"{'='*60}\n")

        return ground_truth_template

    def load_ground_truth(self, filepath: str = "data/ground_truth_sentiment.json") -> None:
        """Load manually annotated ground truth dataset"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.ground_truth = [SentimentGroundTruth(**item) for item in data]

        # Validate ground truth
        for gt in self.ground_truth:
            if gt.true_sentiment == "LABEL_ME":
                raise ValueError(f"Ground truth not fully labeled: {gt.content_id}")
            if gt.true_sentiment not in ['positive', 'neutral', 'negative']:
                raise ValueError(f"Invalid sentiment label: {gt.true_sentiment}")
            if not -1.0 <= gt.true_polarity <= 1.0:
                raise ValueError(f"Invalid polarity: {gt.true_polarity}")

        print(f"Loaded {len(self.ground_truth)} ground truth annotations")

    def validate_sentiment_accuracy(self) -> SentimentValidationMetrics:
        """
        Validate sentiment analysis accuracy against ground truth.

        Returns:
            Validation metrics including accuracy, precision, recall, F1
        """
        if not self.ground_truth:
            raise ValueError("Ground truth dataset not loaded. Call load_ground_truth() first.")

        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Get predicted sentiments
        predictions = {}
        for gt in self.ground_truth:
            cursor.execute("""
                SELECT sentiment
                FROM content_items
                WHERE content_id = ?
            """, (gt.content_id,))

            row = cursor.fetchone()
            if row and row[0]:
                sentiment_data = json.loads(row[0])
                predictions[gt.content_id] = sentiment_data

        conn.close()

        # Calculate metrics
        correct = 0
        total = len(self.ground_truth)

        # For precision, recall, F1
        tp = {'positive': 0, 'neutral': 0, 'negative': 0}
        fp = {'positive': 0, 'neutral': 0, 'negative': 0}
        fn = {'positive': 0, 'neutral': 0, 'negative': 0}

        # Confusion matrix
        confusion = {}

        # Polarity MAE
        polarity_errors = []

        for gt in self.ground_truth:
            if gt.content_id not in predictions:
                continue

            pred = predictions[gt.content_id]
            pred_sentiment = pred.get('sentiment', 'neutral')
            pred_polarity = pred.get('polarity', 0.0)

            # Accuracy
            if pred_sentiment == gt.true_sentiment:
                correct += 1

            # Confusion matrix
            key = (gt.true_sentiment, pred_sentiment)
            confusion[key] = confusion.get(key, 0) + 1

            # Precision/Recall/F1
            for label in ['positive', 'neutral', 'negative']:
                if gt.true_sentiment == label and pred_sentiment == label:
                    tp[label] += 1
                elif pred_sentiment == label and gt.true_sentiment != label:
                    fp[label] += 1
                elif gt.true_sentiment == label and pred_sentiment != label:
                    fn[label] += 1

            # Polarity MAE
            polarity_errors.append(abs(pred_polarity - gt.true_polarity))

        # Calculate final metrics
        accuracy = correct / total if total > 0 else 0.0

        precision = {}
        recall = {}
        f1_score = {}

        for label in ['positive', 'neutral', 'negative']:
            # Precision = TP / (TP + FP)
            precision[label] = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0.0

            # Recall = TP / (TP + FN)
            recall[label] = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0.0

            # F1 = 2 * (Precision * Recall) / (Precision + Recall)
            if precision[label] + recall[label] > 0:
                f1_score[label] = 2 * (precision[label] * recall[label]) / (precision[label] + recall[label])
            else:
                f1_score[label] = 0.0

        mae = sum(polarity_errors) / len(polarity_errors) if polarity_errors else 0.0

        metrics = SentimentValidationMetrics(
            total_items=total,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            confusion_matrix=confusion,
            mean_absolute_error=mae,
            passed=(accuracy >= self.target_accuracy)
        )

        return metrics

    def generate_report(self, metrics: SentimentValidationMetrics) -> str:
        """Generate human-readable validation report"""
        report = []
        report.append("\n" + "="*60)
        report.append("SENTIMENT VALIDATION REPORT")
        report.append("="*60)
        report.append(f"\nTotal Items Validated: {metrics.total_items}")
        report.append(f"Target Accuracy: {self.target_accuracy * 100}%")
        report.append(f"Actual Accuracy: {metrics.accuracy * 100:.2f}%")
        report.append(f"Status: {'✅ PASSED' if metrics.passed else '❌ FAILED'}\n")

        report.append("-"*60)
        report.append("PRECISION BY SENTIMENT")
        report.append("-"*60)
        for label, value in metrics.precision.items():
            report.append(f"{label.capitalize():12} {value*100:6.2f}%")

        report.append("\n" + "-"*60)
        report.append("RECALL BY SENTIMENT")
        report.append("-"*60)
        for label, value in metrics.recall.items():
            report.append(f"{label.capitalize():12} {value*100:6.2f}%")

        report.append("\n" + "-"*60)
        report.append("F1 SCORE BY SENTIMENT")
        report.append("-"*60)
        for label, value in metrics.f1_score.items():
            report.append(f"{label.capitalize():12} {value*100:6.2f}%")

        report.append("\n" + "-"*60)
        report.append("CONFUSION MATRIX")
        report.append("-"*60)
        report.append(f"{'True \\ Pred':<15} {'Positive':>10} {'Neutral':>10} {'Negative':>10}")
        for true_label in ['positive', 'neutral', 'negative']:
            row = [f"{true_label.capitalize():<15}"]
            for pred_label in ['positive', 'neutral', 'negative']:
                count = metrics.confusion_matrix.get((true_label, pred_label), 0)
                row.append(f"{count:>10}")
            report.append("".join(row))

        report.append("\n" + "-"*60)
        report.append(f"Mean Absolute Error (Polarity): {metrics.mean_absolute_error:.4f}")
        report.append("-"*60)

        # Recommendations
        report.append("\n" + "="*60)
        report.append("RECOMMENDATIONS")
        report.append("="*60)
        if metrics.passed:
            report.append("✅ Sentiment analysis meets accuracy target")
        else:
            report.append("❌ Sentiment analysis below target accuracy")
            report.append("\nSuggested improvements:")
            report.append("- Review and refine sentiment analysis prompts")
            report.append("- Consider upgrading to GPT-4 for better accuracy")
            report.append("- Implement ensemble voting across multiple models")
            report.append("- Increase training examples in prompts")

        # Identify common errors
        report.append("\n" + "-"*60)
        report.append("COMMON ERRORS")
        report.append("-"*60)
        errors = [(k, v) for k, v in metrics.confusion_matrix.items() if k[0] != k[1]]
        errors.sort(key=lambda x: x[1], reverse=True)
        for (true_label, pred_label), count in errors[:5]:
            report.append(f"Predicted '{pred_label}' when actually '{true_label}': {count} times")

        report.append("\n" + "="*60 + "\n")

        return "\n".join(report)


if __name__ == "__main__":
    validator = SentimentValidator()

    # Step 1: Create ground truth template (requires manual annotation)
    print("Creating ground truth template for manual annotation...")
    validator.create_ground_truth_dataset(sample_size=50)

    # Step 2: Load manually annotated ground truth (after manual labeling)
    try:
        print("\nAttempting to load ground truth dataset...")
        validator.load_ground_truth()

        # Step 3: Validate sentiment accuracy
        print("Validating sentiment analysis accuracy...")
        metrics = validator.validate_sentiment_accuracy()

        # Step 4: Generate report
        report = validator.generate_report(metrics)
        print(report)

        # Save metrics to file
        output_file = Path("data/validation_results_sentiment.json")
        with open(output_file, 'w') as f:
            json.dump({
                'total_items': metrics.total_items,
                'accuracy': metrics.accuracy,
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1_score': metrics.f1_score,
                'confusion_matrix': {f"{k[0]}->{k[1]}": v for k, v in metrics.confusion_matrix.items()},
                'mean_absolute_error': metrics.mean_absolute_error,
                'passed': metrics.passed
            }, f, indent=2)
        print(f"Results saved to: {output_file}")

    except FileNotFoundError:
        print("\n⚠️  Ground truth dataset not found.")
        print("Please complete manual annotation first.")
        print("See data/ground_truth_sentiment_template.json")
