"""
Persona Classification Validation Module

Validates audience persona targeting accuracy.
Target: ≥75% accuracy for multi-label persona classification.
"""

import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass, asdict

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.db_utils import get_db_connection


@dataclass
class PersonaGroundTruth:
    """Ground truth persona annotation"""
    page_id: str
    url: str
    title: str
    true_personas: List[str]  # List of correct persona types
    annotator: str


@dataclass
class PersonaValidationMetrics:
    """Persona validation metrics"""
    total_pages: int
    accuracy: float  # Exact set match
    hamming_loss: float  # Average label disagreement
    subset_accuracy: float  # Percentage of exact matches
    precision_micro: float
    recall_micro: float
    f1_micro: float
    accuracy_by_persona: Dict[str, float]
    confusion_matrix: Dict[str, Dict[str, int]]  # True -> Predicted counts
    passed: bool  # True if accuracy ≥ 75%


class PersonaValidator:
    """Validates persona classification accuracy"""

    def __init__(self, db_path: str = "data/lbs_knowledge_graph.db"):
        self.db_path = db_path
        self.target_accuracy = 0.75
        self.ground_truth: List[PersonaGroundTruth] = []

    def create_ground_truth_dataset(self, sample_size: int = 50) -> List[PersonaGroundTruth]:
        """
        Create ground truth dataset for persona validation.

        MANUAL STEP REQUIRED: Annotate personas for each page.

        Args:
            sample_size: Number of pages to manually label

        Returns:
            List of ground truth annotations (requires manual labeling)
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Sample pages with persona targeting
        cursor.execute("""
            SELECT DISTINCT p.page_id, p.url, p.title
            FROM pages p
            WHERE EXISTS (
                SELECT 1 FROM targets t WHERE t.page_id = p.page_id
            )
            ORDER BY RANDOM()
            LIMIT ?
        """, (sample_size,))

        pages = cursor.fetchall()
        conn.close()

        # Create template
        ground_truth_template = []
        for page_id, url, title in pages:
            gt = PersonaGroundTruth(
                page_id=page_id,
                url=url,
                title=title,
                true_personas=["LABEL_ME"],  # MANUAL: Replace with correct personas
                annotator="ANNOTATOR_NAME"
            )
            ground_truth_template.append(gt)

        # Save template
        output_file = Path("data/ground_truth_personas_template.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(
                [asdict(gt) for gt in ground_truth_template],
                f,
                indent=2
            )

        print(f"\n{'='*60}")
        print("MANUAL ANNOTATION REQUIRED - PERSONA VALIDATION")
        print(f"{'='*60}")
        print(f"Ground truth template saved to: {output_file}")
        print(f"\nPlease manually label {sample_size} pages:")
        print("1. Open the file")
        print("2. For each page, determine target personas")
        print("3. Personas: prospective_student, current_student, alumni,")
        print("   faculty, researcher, corporate_partner, media, etc.")
        print("4. Multiple personas per page are allowed")
        print("5. Set 'annotator' to your name")
        print("6. Save as 'data/ground_truth_personas.json'")
        print(f"{'='*60}\n")

        return ground_truth_template

    def load_ground_truth(self, filepath: str = "data/ground_truth_personas.json") -> None:
        """Load manually annotated ground truth dataset"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.ground_truth = [PersonaGroundTruth(**item) for item in data]

        # Validate
        for gt in self.ground_truth:
            if "LABEL_ME" in gt.true_personas:
                raise ValueError(f"Ground truth not fully labeled: {gt.page_id}")
            if not gt.true_personas:
                raise ValueError(f"No personas labeled for: {gt.page_id}")

        print(f"Loaded {len(self.ground_truth)} ground truth persona annotations")

    def validate_persona_classification(self) -> PersonaValidationMetrics:
        """
        Validate persona classification accuracy against ground truth.

        Returns:
            Validation metrics for multi-label classification
        """
        if not self.ground_truth:
            raise ValueError("Ground truth dataset not loaded. Call load_ground_truth() first.")

        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Get predicted personas
        predictions = {}
        for gt in self.ground_truth:
            cursor.execute("""
                SELECT persona_type
                FROM targets
                WHERE page_id = ?
            """, (gt.page_id,))

            predictions[gt.page_id] = [row[0] for row in cursor.fetchall()]

        conn.close()

        # Calculate metrics
        exact_matches = 0
        total_label_comparisons = 0
        label_disagreements = 0

        true_positives = 0
        false_positives = 0
        false_negatives = 0

        accuracy_by_persona = {}
        persona_counts = {}
        confusion_matrix = {}

        all_personas = set()

        for gt in self.ground_truth:
            if gt.page_id not in predictions:
                continue

            pred_personas = set(predictions[gt.page_id])
            true_personas = set(gt.true_personas)

            all_personas.update(true_personas)
            all_personas.update(pred_personas)

            # Exact match (subset accuracy)
            if pred_personas == true_personas:
                exact_matches += 1

            # Hamming loss (per-label disagreement)
            all_labels = true_personas | pred_personas
            total_label_comparisons += len(all_labels)
            for label in all_labels:
                if (label in true_personas) != (label in pred_personas):
                    label_disagreements += 1

            # Micro-averaged metrics
            true_positives += len(true_personas & pred_personas)
            false_positives += len(pred_personas - true_personas)
            false_negatives += len(true_personas - pred_personas)

            # Per-persona accuracy
            for persona in all_personas:
                if persona not in persona_counts:
                    persona_counts[persona] = {'correct': 0, 'total': 0}

                persona_counts[persona]['total'] += 1
                if (persona in true_personas) == (persona in pred_personas):
                    persona_counts[persona]['correct'] += 1

            # Confusion matrix
            for true_p in true_personas:
                if true_p not in confusion_matrix:
                    confusion_matrix[true_p] = {}
                for pred_p in pred_personas:
                    confusion_matrix[true_p][pred_p] = confusion_matrix[true_p].get(pred_p, 0) + 1

        # Calculate overall metrics
        subset_accuracy = exact_matches / len(self.ground_truth) if self.ground_truth else 0.0
        hamming_loss = label_disagreements / total_label_comparisons if total_label_comparisons > 0 else 0.0

        precision_micro = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall_micro = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_micro = 2 * (precision_micro * recall_micro) / (precision_micro + recall_micro) if (precision_micro + recall_micro) > 0 else 0.0

        # Per-persona accuracy
        for persona, counts in persona_counts.items():
            accuracy_by_persona[persona] = counts['correct'] / counts['total'] if counts['total'] > 0 else 0.0

        # Use subset accuracy for pass/fail
        metrics = PersonaValidationMetrics(
            total_pages=len(self.ground_truth),
            accuracy=subset_accuracy,
            hamming_loss=hamming_loss,
            subset_accuracy=subset_accuracy,
            precision_micro=precision_micro,
            recall_micro=recall_micro,
            f1_micro=f1_micro,
            accuracy_by_persona=accuracy_by_persona,
            confusion_matrix=confusion_matrix,
            passed=(subset_accuracy >= self.target_accuracy)
        )

        return metrics

    def generate_report(self, metrics: PersonaValidationMetrics) -> str:
        """Generate human-readable validation report"""
        report = []
        report.append("\n" + "="*60)
        report.append("PERSONA CLASSIFICATION VALIDATION REPORT")
        report.append("="*60)
        report.append(f"\nTotal Pages Validated: {metrics.total_pages}")
        report.append(f"\nTarget Accuracy: {self.target_accuracy * 100}%")
        report.append(f"Subset Accuracy (Exact Match): {metrics.subset_accuracy * 100:.2f}%")
        report.append(f"Hamming Loss: {metrics.hamming_loss:.4f}")
        report.append(f"\nPrecision (Micro): {metrics.precision_micro * 100:.2f}%")
        report.append(f"Recall (Micro): {metrics.recall_micro * 100:.2f}%")
        report.append(f"F1 Score (Micro): {metrics.f1_micro * 100:.2f}%")
        report.append(f"\nStatus: {'✅ PASSED' if metrics.passed else '❌ FAILED'}\n")

        report.append("-"*60)
        report.append("ACCURACY BY PERSONA")
        report.append("-"*60)
        for persona, accuracy in sorted(metrics.accuracy_by_persona.items(), key=lambda x: x[1], reverse=True):
            report.append(f"{persona:25} {accuracy*100:6.2f}%")

        # Recommendations
        report.append("\n" + "="*60)
        report.append("RECOMMENDATIONS")
        report.append("="*60)
        if metrics.passed:
            report.append("✅ Persona classification meets accuracy target")
        else:
            report.append("❌ Persona classification below target accuracy")
            report.append("\nSuggested improvements:")
            report.append("- Refine persona classification prompts")
            report.append("- Add more persona-specific indicators to prompts")
            report.append("- Implement persona hierarchy (general -> specific)")
            report.append("- Use ensemble voting for ambiguous content")

        report.append("\n" + "="*60 + "\n")

        return "\n".join(report)


if __name__ == "__main__":
    validator = PersonaValidator()

    # Step 1: Create ground truth template
    print("Creating ground truth template for persona validation...")
    validator.create_ground_truth_dataset(sample_size=50)

    # Step 2: Load ground truth
    try:
        print("\nAttempting to load ground truth dataset...")
        validator.load_ground_truth()

        # Step 3: Validate persona classification
        print("Validating persona classification...")
        metrics = validator.validate_persona_classification()

        # Step 4: Generate report
        report = validator.generate_report(metrics)
        print(report)

        # Save metrics
        output_file = Path("data/validation_results_personas.json")
        with open(output_file, 'w') as f:
            json.dump({
                'total_pages': metrics.total_pages,
                'subset_accuracy': metrics.subset_accuracy,
                'hamming_loss': metrics.hamming_loss,
                'precision_micro': metrics.precision_micro,
                'recall_micro': metrics.recall_micro,
                'f1_micro': metrics.f1_micro,
                'accuracy_by_persona': metrics.accuracy_by_persona,
                'passed': metrics.passed
            }, f, indent=2)
        print(f"Results saved to: {output_file}")

    except FileNotFoundError:
        print("\n⚠️  Ground truth dataset not found.")
        print("Please complete manual annotation first.")
        print("See data/ground_truth_personas_template.json")
