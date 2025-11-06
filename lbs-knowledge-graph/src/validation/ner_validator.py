"""
Named Entity Recognition (NER) Validation Module

Validates entity extraction accuracy and type classification.
Target: ≥85% precision for entity extraction and classification.
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
class EntityGroundTruth:
    """Ground truth entity annotation"""
    page_id: str
    url: str
    title: str
    true_entities: List[Dict[str, str]]  # List of {text, type}
    annotator: str


@dataclass
class NERValidationMetrics:
    """NER validation metrics"""
    total_entities_extracted: int
    total_entities_ground_truth: int
    exact_match_precision: float  # Exact text + type match
    exact_match_recall: float
    partial_match_precision: float  # Text match, any type
    type_accuracy: float  # Correct type when entity found
    precision_by_type: Dict[str, float]
    recall_by_type: Dict[str, float]
    extraction_errors: List[Tuple[str, str]]  # (page_id, issue)
    passed: bool  # True if exact_match_precision ≥ 85%


class NERValidator:
    """Validates named entity recognition accuracy"""

    def __init__(self, db_path: str = "data/lbs_knowledge_graph.db"):
        self.db_path = db_path
        self.target_precision = 0.85
        self.ground_truth: List[EntityGroundTruth] = []

    def create_ground_truth_dataset(self, sample_size: int = 30) -> List[EntityGroundTruth]:
        """
        Create ground truth dataset for NER validation.

        MANUAL STEP REQUIRED: Annotate entities for each page.

        Args:
            sample_size: Number of pages to manually label

        Returns:
            List of ground truth annotations (requires manual labeling)
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Sample pages with entities
        cursor.execute("""
            SELECT DISTINCT p.page_id, p.url, p.title
            FROM pages p
            WHERE EXISTS (
                SELECT 1 FROM entity_graph eg WHERE eg.page_id = p.page_id
            )
            ORDER BY RANDOM()
            LIMIT ?
        """, (sample_size,))

        pages = cursor.fetchall()
        conn.close()

        # Create template for manual annotation
        ground_truth_template = []
        for page_id, url, title in pages:
            gt = EntityGroundTruth(
                page_id=page_id,
                url=url,
                title=title,
                true_entities=[
                    {"text": "ENTITY_TEXT", "type": "PERSON|ORGANIZATION|LOCATION|PROGRAM|etc"}
                ],  # MANUAL: Replace with correct entities
                annotator="ANNOTATOR_NAME"
            )
            ground_truth_template.append(gt)

        # Save template
        output_file = Path("data/ground_truth_entities_template.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(
                [asdict(gt) for gt in ground_truth_template],
                f,
                indent=2
            )

        print(f"\n{'='*60}")
        print("MANUAL ANNOTATION REQUIRED - NER VALIDATION")
        print(f"{'='*60}")
        print(f"Ground truth template saved to: {output_file}")
        print(f"\nPlease manually label entities for {sample_size} pages:")
        print("1. Open the file")
        print("2. For each page, identify ALL entities")
        print("3. For each entity, provide:")
        print("   - text: The exact entity text")
        print("   - type: Entity type (PERSON, ORGANIZATION, LOCATION, etc.)")
        print("4. Set 'annotator' to your name")
        print("5. Save as 'data/ground_truth_entities.json'")
        print(f"{'='*60}\n")

        return ground_truth_template

    def load_ground_truth(self, filepath: str = "data/ground_truth_entities.json") -> None:
        """Load manually annotated ground truth dataset"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.ground_truth = [EntityGroundTruth(**item) for item in data]

        # Validate ground truth
        for gt in self.ground_truth:
            if any(e['text'] == "ENTITY_TEXT" for e in gt.true_entities):
                raise ValueError(f"Ground truth not fully labeled: {gt.page_id}")

        print(f"Loaded {len(self.ground_truth)} ground truth entity annotations")

    def validate_ner_extraction(self) -> NERValidationMetrics:
        """
        Validate NER extraction accuracy against ground truth.

        Returns:
            Validation metrics including precision, recall, type accuracy
        """
        if not self.ground_truth:
            raise ValueError("Ground truth dataset not loaded. Call load_ground_truth() first.")

        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        # Get predicted entities
        predictions = {}
        for gt in self.ground_truth:
            cursor.execute("""
                SELECT entity_text, entity_type
                FROM entity_graph
                WHERE page_id = ?
            """, (gt.page_id,))

            predictions[gt.page_id] = [
                {'text': row[0], 'type': row[1]}
                for row in cursor.fetchall()
            ]

        conn.close()

        # Calculate metrics
        exact_tp = 0
        partial_tp = 0
        total_extracted = 0
        total_ground_truth = 0
        type_correct = 0
        type_total = 0

        # By type
        tp_by_type = {}
        fp_by_type = {}
        fn_by_type = {}

        extraction_errors = []

        for gt in self.ground_truth:
            if gt.page_id not in predictions:
                continue

            pred_entities = predictions[gt.page_id]
            true_entities = gt.true_entities

            total_extracted += len(pred_entities)
            total_ground_truth += len(true_entities)

            # Create sets for comparison
            true_set_exact = {(e['text'].lower(), e['type']) for e in true_entities}
            pred_set_exact = {(e['text'].lower(), e['type']) for e in pred_entities}

            true_set_text = {e['text'].lower() for e in true_entities}
            pred_set_text = {e['text'].lower() for e in pred_entities}

            # Exact match (text + type)
            exact_tp += len(true_set_exact & pred_set_exact)

            # Partial match (text only)
            partial_tp += len(true_set_text & pred_set_text)

            # Type accuracy (when entity found)
            for pred in pred_entities:
                if pred['text'].lower() in true_set_text:
                    type_total += 1
                    # Check if type is correct
                    if (pred['text'].lower(), pred['type']) in true_set_exact:
                        type_correct += 1
                    else:
                        extraction_errors.append((
                            gt.page_id,
                            f"Wrong type for '{pred['text']}': predicted {pred['type']}"
                        ))

            # By-type metrics
            for entity in true_entities:
                entity_type = entity['type']
                if entity_type not in tp_by_type:
                    tp_by_type[entity_type] = 0
                    fp_by_type[entity_type] = 0
                    fn_by_type[entity_type] = 0

                if (entity['text'].lower(), entity_type) in pred_set_exact:
                    tp_by_type[entity_type] += 1
                else:
                    fn_by_type[entity_type] += 1

            for entity in pred_entities:
                entity_type = entity['type']
                if entity_type not in fp_by_type:
                    fp_by_type[entity_type] = 0

                if (entity['text'].lower(), entity_type) not in true_set_exact:
                    fp_by_type[entity_type] += 1

        # Calculate overall metrics
        exact_precision = exact_tp / total_extracted if total_extracted > 0 else 0.0
        exact_recall = exact_tp / total_ground_truth if total_ground_truth > 0 else 0.0

        partial_precision = partial_tp / total_extracted if total_extracted > 0 else 0.0

        type_accuracy = type_correct / type_total if type_total > 0 else 0.0

        # By-type metrics
        precision_by_type = {}
        recall_by_type = {}

        for entity_type in set(list(tp_by_type.keys()) + list(fp_by_type.keys())):
            tp = tp_by_type.get(entity_type, 0)
            fp = fp_by_type.get(entity_type, 0)
            fn = fn_by_type.get(entity_type, 0)

            precision_by_type[entity_type] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall_by_type[entity_type] = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        metrics = NERValidationMetrics(
            total_entities_extracted=total_extracted,
            total_entities_ground_truth=total_ground_truth,
            exact_match_precision=exact_precision,
            exact_match_recall=exact_recall,
            partial_match_precision=partial_precision,
            type_accuracy=type_accuracy,
            precision_by_type=precision_by_type,
            recall_by_type=recall_by_type,
            extraction_errors=extraction_errors[:20],
            passed=(exact_precision >= self.target_precision)
        )

        return metrics

    def generate_report(self, metrics: NERValidationMetrics) -> str:
        """Generate human-readable validation report"""
        report = []
        report.append("\n" + "="*60)
        report.append("NER VALIDATION REPORT")
        report.append("="*60)
        report.append(f"\nEntities Extracted: {metrics.total_entities_extracted}")
        report.append(f"Ground Truth Entities: {metrics.total_entities_ground_truth}")
        report.append(f"\nTarget Precision: {self.target_precision * 100}%")
        report.append(f"Exact Match Precision: {metrics.exact_match_precision * 100:.2f}%")
        report.append(f"Exact Match Recall: {metrics.exact_match_recall * 100:.2f}%")
        report.append(f"Partial Match Precision: {metrics.partial_match_precision * 100:.2f}%")
        report.append(f"Type Accuracy: {metrics.type_accuracy * 100:.2f}%")
        report.append(f"\nStatus: {'✅ PASSED' if metrics.passed else '❌ FAILED'}\n")

        report.append("-"*60)
        report.append("PRECISION BY ENTITY TYPE")
        report.append("-"*60)
        for entity_type, value in sorted(metrics.precision_by_type.items()):
            report.append(f"{entity_type:20} {value*100:6.2f}%")

        report.append("\n" + "-"*60)
        report.append("RECALL BY ENTITY TYPE")
        report.append("-"*60)
        for entity_type, value in sorted(metrics.recall_by_type.items()):
            report.append(f"{entity_type:20} {value*100:6.2f}%")

        report.append("\n" + "-"*60)
        report.append("EXTRACTION ERRORS (Sample)")
        report.append("-"*60)
        for page_id, error in metrics.extraction_errors[:10]:
            report.append(f"Page {page_id}: {error}")

        # Recommendations
        report.append("\n" + "="*60)
        report.append("RECOMMENDATIONS")
        report.append("="*60)
        if metrics.passed:
            report.append("✅ NER meets precision target")
        else:
            report.append("❌ NER below target precision")
            report.append("\nSuggested improvements:")
            report.append("- Refine NER prompts with domain-specific examples")
            report.append("- Implement entity disambiguation rules")
            report.append("- Use specialized NER models for business/education domain")
            report.append("- Add post-processing validation rules")

        report.append("\n" + "="*60 + "\n")

        return "\n".join(report)


if __name__ == "__main__":
    validator = NERValidator()

    # Step 1: Create ground truth template
    print("Creating ground truth template for NER validation...")
    validator.create_ground_truth_dataset(sample_size=30)

    # Step 2: Load ground truth
    try:
        print("\nAttempting to load ground truth dataset...")
        validator.load_ground_truth()

        # Step 3: Validate NER
        print("Validating NER extraction...")
        metrics = validator.validate_ner_extraction()

        # Step 4: Generate report
        report = validator.generate_report(metrics)
        print(report)

        # Save metrics
        output_file = Path("data/validation_results_ner.json")
        with open(output_file, 'w') as f:
            json.dump({
                'total_entities_extracted': metrics.total_entities_extracted,
                'total_entities_ground_truth': metrics.total_entities_ground_truth,
                'exact_match_precision': metrics.exact_match_precision,
                'exact_match_recall': metrics.exact_match_recall,
                'partial_match_precision': metrics.partial_match_precision,
                'type_accuracy': metrics.type_accuracy,
                'precision_by_type': metrics.precision_by_type,
                'recall_by_type': metrics.recall_by_type,
                'passed': metrics.passed
            }, f, indent=2)
        print(f"Results saved to: {output_file}")

    except FileNotFoundError:
        print("\n⚠️  Ground truth dataset not found.")
        print("Please complete manual annotation first.")
        print("See data/ground_truth_entities_template.json")
