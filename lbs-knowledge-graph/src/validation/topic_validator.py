"""
Topic Validation Module

Validates topic extraction accuracy and relevance.
Target: ≥75% precision with manual validation of extracted topics.
"""

import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.db_utils import get_db_connection


@dataclass
class TopicGroundTruth:
    """Ground truth topic annotation"""
    page_id: str
    url: str
    title: str
    true_topics: List[str]  # List of correct topic names
    annotator: str


@dataclass
class TopicValidationMetrics:
    """Topic validation metrics"""
    total_pages: int
    total_topics_extracted: int
    total_topics_ground_truth: int
    precision: float  # TP / (TP + FP)
    recall: float     # TP / (TP + FN)
    f1_score: float
    precision_at_k: Dict[int, float]  # Precision@K for K=1,3,5
    false_positives: List[Tuple[str, str]]  # (page_id, wrong_topic)
    false_negatives: List[Tuple[str, str]]  # (page_id, missed_topic)
    passed: bool  # True if precision ≥ 75%


class TopicValidator:
    """Validates topic extraction accuracy"""

    def __init__(self, db_path: str = "data/lbs_knowledge_graph.db"):
        self.db_path = db_path
        self.target_precision = 0.75
        self.ground_truth: List[TopicGroundTruth] = []

    def create_ground_truth_dataset(self, sample_size: int = 30) -> List[TopicGroundTruth]:
        """
        Create ground truth dataset for topic validation.

        MANUAL STEP REQUIRED: This method creates a template dataset.
        You must manually label the correct topics for each page.

        Args:
            sample_size: Number of pages to manually label

        Returns:
            List of ground truth annotations (requires manual labeling)
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Sample pages with topic extraction
        cursor.execute("""
            SELECT DISTINCT p.page_id, p.url, p.title
            FROM pages p
            JOIN has_topic ht ON p.page_id = ht.page_id
            ORDER BY RANDOM()
            LIMIT ?
        """, (sample_size,))

        pages = cursor.fetchall()

        # For each page, get extracted topics
        ground_truth_template = []
        for page_id, url, title in pages:
            cursor.execute("""
                SELECT t.name
                FROM topics t
                JOIN has_topic ht ON t.topic_id = ht.topic_id
                WHERE ht.page_id = ?
                ORDER BY ht.relevance DESC
                LIMIT 10
            """, (page_id,))

            extracted_topics = [row[0] for row in cursor.fetchall()]

            # Create template for manual annotation
            gt = TopicGroundTruth(
                page_id=page_id,
                url=url,
                title=title,
                true_topics=["LABEL_ME"],  # MANUAL: Replace with correct topics
                annotator="ANNOTATOR_NAME"
            )
            ground_truth_template.append(gt)

        conn.close()

        # Save template to file for manual annotation
        output_file = Path("data/ground_truth_topics_template.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(
                [asdict(gt) for gt in ground_truth_template],
                f,
                indent=2
            )

        print(f"\n{'='*60}")
        print("MANUAL ANNOTATION REQUIRED - TOPIC VALIDATION")
        print(f"{'='*60}")
        print(f"Ground truth template saved to: {output_file}")
        print(f"\nPlease manually label {sample_size} pages:")
        print("1. Open the file")
        print("2. For each page, review the URL and title")
        print("3. Replace 'true_topics' with a list of correct topics")
        print("4. Topics should be relevant, accurate, and complete")
        print("5. Set 'annotator' to your name")
        print("6. Save as 'data/ground_truth_topics.json'")
        print(f"{'='*60}\n")

        return ground_truth_template

    def load_ground_truth(self, filepath: str = "data/ground_truth_topics.json") -> None:
        """Load manually annotated ground truth dataset"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.ground_truth = [TopicGroundTruth(**item) for item in data]

        # Validate ground truth
        for gt in self.ground_truth:
            if "LABEL_ME" in gt.true_topics:
                raise ValueError(f"Ground truth not fully labeled: {gt.page_id}")
            if not gt.true_topics:
                raise ValueError(f"No topics labeled for: {gt.page_id}")

        print(f"Loaded {len(self.ground_truth)} ground truth topic annotations")

    def validate_topic_extraction(self) -> TopicValidationMetrics:
        """
        Validate topic extraction accuracy against ground truth.

        Returns:
            Validation metrics including precision, recall, F1
        """
        if not self.ground_truth:
            raise ValueError("Ground truth dataset not loaded. Call load_ground_truth() first.")

        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Get predicted topics for each page
        predictions = {}
        for gt in self.ground_truth:
            cursor.execute("""
                SELECT t.name, ht.relevance
                FROM topics t
                JOIN has_topic ht ON t.topic_id = ht.topic_id
                WHERE ht.page_id = ?
                ORDER BY ht.relevance DESC
            """, (gt.page_id,))

            predictions[gt.page_id] = [row[0] for row in cursor.fetchall()]

        conn.close()

        # Calculate metrics
        true_positives = 0
        false_positives_list = []
        false_negatives_list = []

        total_extracted = 0
        total_ground_truth = 0

        precision_at_k = {1: [], 3: [], 5: []}

        for gt in self.ground_truth:
            if gt.page_id not in predictions:
                continue

            pred_topics = predictions[gt.page_id]
            true_topics = set(gt.true_topics)

            total_extracted += len(pred_topics)
            total_ground_truth += len(true_topics)

            # Calculate TP, FP, FN
            for topic in pred_topics:
                if topic in true_topics:
                    true_positives += 1
                else:
                    false_positives_list.append((gt.page_id, topic))

            for topic in true_topics:
                if topic not in pred_topics:
                    false_negatives_list.append((gt.page_id, topic))

            # Precision@K
            for k in [1, 3, 5]:
                if len(pred_topics) >= k:
                    top_k = set(pred_topics[:k])
                    hits = len(top_k & true_topics)
                    precision_at_k[k].append(hits / k)

        # Calculate overall metrics
        precision = true_positives / total_extracted if total_extracted > 0 else 0.0
        recall = true_positives / total_ground_truth if total_ground_truth > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Average Precision@K
        avg_precision_at_k = {
            k: sum(scores) / len(scores) if scores else 0.0
            for k, scores in precision_at_k.items()
        }

        metrics = TopicValidationMetrics(
            total_pages=len(self.ground_truth),
            total_topics_extracted=total_extracted,
            total_topics_ground_truth=total_ground_truth,
            precision=precision,
            recall=recall,
            f1_score=f1,
            precision_at_k=avg_precision_at_k,
            false_positives=false_positives_list[:20],  # Top 20
            false_negatives=false_negatives_list[:20],
            passed=(precision >= self.target_precision)
        )

        return metrics

    def generate_report(self, metrics: TopicValidationMetrics) -> str:
        """Generate human-readable validation report"""
        report = []
        report.append("\n" + "="*60)
        report.append("TOPIC EXTRACTION VALIDATION REPORT")
        report.append("="*60)
        report.append(f"\nTotal Pages Validated: {metrics.total_pages}")
        report.append(f"Topics Extracted: {metrics.total_topics_extracted}")
        report.append(f"Ground Truth Topics: {metrics.total_topics_ground_truth}")
        report.append(f"\nTarget Precision: {self.target_precision * 100}%")
        report.append(f"Actual Precision: {metrics.precision * 100:.2f}%")
        report.append(f"Recall: {metrics.recall * 100:.2f}%")
        report.append(f"F1 Score: {metrics.f1_score * 100:.2f}%")
        report.append(f"\nStatus: {'✅ PASSED' if metrics.passed else '❌ FAILED'}\n")

        report.append("-"*60)
        report.append("PRECISION@K (Average)")
        report.append("-"*60)
        for k, value in sorted(metrics.precision_at_k.items()):
            report.append(f"Precision@{k}: {value*100:6.2f}%")

        report.append("\n" + "-"*60)
        report.append("FALSE POSITIVES (Sample)")
        report.append("-"*60)
        report.append("Topics extracted but not in ground truth:")
        for page_id, topic in metrics.false_positives[:10]:
            report.append(f"  Page {page_id}: {topic}")

        report.append("\n" + "-"*60)
        report.append("FALSE NEGATIVES (Sample)")
        report.append("-"*60)
        report.append("Topics in ground truth but not extracted:")
        for page_id, topic in metrics.false_negatives[:10]:
            report.append(f"  Page {page_id}: {topic}")

        # Recommendations
        report.append("\n" + "="*60)
        report.append("RECOMMENDATIONS")
        report.append("="*60)
        if metrics.passed:
            report.append("✅ Topic extraction meets precision target")
        else:
            report.append("❌ Topic extraction below target precision")
            report.append("\nSuggested improvements:")
            report.append("- Refine topic extraction prompts with more examples")
            report.append("- Implement topic taxonomy mapping")
            report.append("- Use hierarchical topic models")
            report.append("- Increase relevance threshold (filter low-confidence topics)")

        report.append("\n" + "="*60 + "\n")

        return "\n".join(report)


if __name__ == "__main__":
    validator = TopicValidator()

    # Step 1: Create ground truth template
    print("Creating ground truth template for manual topic annotation...")
    validator.create_ground_truth_dataset(sample_size=30)

    # Step 2: Load manually annotated ground truth
    try:
        print("\nAttempting to load ground truth dataset...")
        validator.load_ground_truth()

        # Step 3: Validate topic extraction
        print("Validating topic extraction accuracy...")
        metrics = validator.validate_topic_extraction()

        # Step 4: Generate report
        report = validator.generate_report(metrics)
        print(report)

        # Save metrics to file
        output_file = Path("data/validation_results_topics.json")
        with open(output_file, 'w') as f:
            json.dump({
                'total_pages': metrics.total_pages,
                'total_topics_extracted': metrics.total_topics_extracted,
                'total_topics_ground_truth': metrics.total_topics_ground_truth,
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1_score': metrics.f1_score,
                'precision_at_k': metrics.precision_at_k,
                'passed': metrics.passed
            }, f, indent=2)
        print(f"Results saved to: {output_file}")

    except FileNotFoundError:
        print("\n⚠️  Ground truth dataset not found.")
        print("Please complete manual annotation first.")
        print("See data/ground_truth_topics_template.json")
