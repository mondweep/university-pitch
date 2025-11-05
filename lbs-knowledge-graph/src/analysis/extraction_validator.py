"""
Extraction Validator for LBS Knowledge Graph Project.

Validates domain extractor accuracy by comparing extracted entities
against ground truth or expected patterns. Calculates precision, recall,
and F1 scores for:
- Page type classification
- Section type detection
- Content item extraction
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from models.entities import Page, Section, ContentItem
    from models.enums import PageType, SectionType, ContentType
except ImportError:
    # Fallback for when models aren't yet created
    logger = logging.getLogger(__name__)
    logger.warning("Models not found - using mock types")
    PageType = type('PageType', (), {})
    SectionType = type('SectionType', (), {})
    ContentType = type('ContentType', (), {})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationMetrics:
    """Metrics for a single validation category."""

    true_positives: int
    false_positives: int
    false_negatives: int
    total_samples: int
    precision: float
    recall: float
    f1_score: float
    accuracy: float

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ValidationReport:
    """Comprehensive validation report."""

    page_type_metrics: Dict[str, ValidationMetrics]
    section_type_metrics: Dict[str, ValidationMetrics]
    content_type_metrics: Dict[str, ValidationMetrics]
    overall_metrics: Dict[str, float]
    confusion_matrices: Dict[str, Any]
    errors: List[Dict[str, Any]]

    def to_dict(self) -> Dict:
        return {
            'page_type_metrics': {k: v.to_dict() for k, v in self.page_type_metrics.items()},
            'section_type_metrics': {k: v.to_dict() for k, v in self.section_type_metrics.items()},
            'content_type_metrics': {k: v.to_dict() for k, v in self.content_type_metrics.items()},
            'overall_metrics': self.overall_metrics,
            'confusion_matrices': self.confusion_matrices,
            'errors': self.errors
        }

    def to_json(self, path: Path) -> None:
        """Save report as JSON."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class ExtractionValidator:
    """Validates extraction accuracy against ground truth."""

    def __init__(self, ground_truth_path: Optional[Path] = None):
        """
        Initialize validator.

        Args:
            ground_truth_path: Path to ground truth dataset (optional)
        """
        self.ground_truth = {}
        if ground_truth_path and ground_truth_path.exists():
            self._load_ground_truth(ground_truth_path)

    def _load_ground_truth(self, path: Path) -> None:
        """Load ground truth dataset."""
        logger.info(f"Loading ground truth from {path}")
        with open(path) as f:
            self.ground_truth = json.load(f)
        logger.info(f"Loaded {len(self.ground_truth)} ground truth entries")

    def validate_page_extraction(
        self,
        pages: List[Dict],
        expected_types: Optional[Dict[str, str]] = None
    ) -> ValidationMetrics:
        """
        Validate page type extraction.

        Args:
            pages: List of extracted Page entities
            expected_types: Dict mapping page IDs to expected types

        Returns:
            ValidationMetrics for page classification
        """
        logger.info("Validating page type extraction...")

        if expected_types is None:
            expected_types = self.ground_truth.get('page_types', {})

        if not expected_types:
            logger.warning("No ground truth for page types - using heuristic validation")
            return self._heuristic_page_validation(pages)

        tp = 0  # True positives
        fp = 0  # False positives
        fn = 0  # False negatives

        # Compare extracted vs expected
        for page in pages:
            page_id = page.get('id') or page.get('page_name')
            extracted_type = page.get('type') or self._infer_page_type_from_name(page_id)
            expected_type = expected_types.get(page_id)

            if expected_type:
                if extracted_type == expected_type:
                    tp += 1
                else:
                    fp += 1
                    fn += 1
            else:
                logger.warning(f"No ground truth for page {page_id}")

        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = tp / len(pages) if pages else 0.0

        return ValidationMetrics(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            total_samples=len(pages),
            precision=precision,
            recall=recall,
            f1_score=f1,
            accuracy=accuracy
        )

    def validate_section_extraction(
        self,
        sections: List[Dict],
        expected_sections: Optional[Dict[str, List[str]]] = None
    ) -> ValidationMetrics:
        """
        Validate section type extraction.

        Args:
            sections: List of extracted Section entities
            expected_sections: Dict mapping page IDs to expected section types

        Returns:
            ValidationMetrics for section detection
        """
        logger.info("Validating section type extraction...")

        if expected_sections is None:
            expected_sections = self.ground_truth.get('section_types', {})

        if not expected_sections:
            logger.warning("No ground truth for sections - using heuristic validation")
            return self._heuristic_section_validation(sections)

        tp = 0
        fp = 0
        fn = 0

        # Group sections by page
        sections_by_page = defaultdict(list)
        for section in sections:
            page_id = section.get('pageId', '')
            sections_by_page[page_id].append(section)

        # Validate each page's sections
        for page_id, page_sections in sections_by_page.items():
            expected = expected_sections.get(page_id, [])
            extracted = [s.get('type', 'unknown') for s in page_sections]

            # Count matches
            expected_counter = Counter(expected)
            extracted_counter = Counter(extracted)

            for section_type in set(expected + extracted):
                expected_count = expected_counter[section_type]
                extracted_count = extracted_counter[section_type]

                matches = min(expected_count, extracted_count)
                tp += matches
                fp += max(0, extracted_count - expected_count)
                fn += max(0, expected_count - extracted_count)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = tp / len(sections) if sections else 0.0

        return ValidationMetrics(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            total_samples=len(sections),
            precision=precision,
            recall=recall,
            f1_score=f1,
            accuracy=accuracy
        )

    def validate_content_extraction(
        self,
        content_items: List[Dict],
        expected_content: Optional[Dict[str, List[str]]] = None
    ) -> ValidationMetrics:
        """
        Validate content item extraction.

        Args:
            content_items: List of extracted ContentItem entities
            expected_content: Dict mapping section IDs to expected content types

        Returns:
            ValidationMetrics for content extraction
        """
        logger.info("Validating content item extraction...")

        if expected_content is None:
            expected_content = self.ground_truth.get('content_types', {})

        if not expected_content:
            logger.warning("No ground truth for content - using heuristic validation")
            return self._heuristic_content_validation(content_items)

        tp = 0
        fp = 0
        fn = 0

        # Group content by section
        content_by_section = defaultdict(list)
        for item in content_items:
            section_ids = item.get('sectionIds', [])
            for section_id in section_ids:
                content_by_section[section_id].append(item)

        # Validate each section's content
        for section_id, section_content in content_by_section.items():
            expected = expected_content.get(section_id, [])
            extracted = [c.get('type', 'unknown') for c in section_content]

            expected_counter = Counter(expected)
            extracted_counter = Counter(extracted)

            for content_type in set(expected + extracted):
                expected_count = expected_counter[content_type]
                extracted_count = extracted_counter[content_type]

                matches = min(expected_count, extracted_count)
                tp += matches
                fp += max(0, extracted_count - expected_count)
                fn += max(0, expected_count - extracted_count)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = tp / len(content_items) if content_items else 0.0

        return ValidationMetrics(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            total_samples=len(content_items),
            precision=precision,
            recall=recall,
            f1_score=f1,
            accuracy=accuracy
        )

    def calculate_confusion_matrix(
        self,
        predictions: List[str],
        ground_truth: List[str],
        labels: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate confusion matrix for multi-class classification.

        Args:
            predictions: List of predicted labels
            ground_truth: List of actual labels
            labels: List of all possible labels

        Returns:
            Confusion matrix as nested dict
        """
        matrix = {label: {other: 0 for other in labels} for label in labels}

        for pred, actual in zip(predictions, ground_truth):
            if pred in labels and actual in labels:
                matrix[actual][pred] += 1

        return {
            'matrix': matrix,
            'labels': labels,
            'total_samples': len(predictions)
        }

    def generate_error_report(
        self,
        pages: List[Dict],
        sections: List[Dict],
        content_items: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate detailed error report for misclassifications.

        Returns:
            List of error entries with details
        """
        errors = []

        # Page errors
        for page in pages:
            page_id = page.get('id') or page.get('page_name')
            expected_type = self.ground_truth.get('page_types', {}).get(page_id)
            extracted_type = page.get('type')

            if expected_type and extracted_type != expected_type:
                errors.append({
                    'entity_type': 'page',
                    'entity_id': page_id,
                    'expected': expected_type,
                    'extracted': extracted_type,
                    'url': page.get('url', 'unknown')
                })

        # Section errors
        for section in sections:
            section_id = section.get('id')
            page_id = section.get('pageId')
            expected_sections = self.ground_truth.get('section_types', {}).get(page_id, [])
            extracted_type = section.get('type')

            # Simple check if section type is unexpected
            if extracted_type == 'other' or extracted_type == 'unknown':
                errors.append({
                    'entity_type': 'section',
                    'entity_id': section_id,
                    'page_id': page_id,
                    'extracted': extracted_type,
                    'note': 'Unclassified section'
                })

        return errors

    def validate_all(
        self,
        pages: List[Dict],
        sections: List[Dict],
        content_items: List[Dict]
    ) -> ValidationReport:
        """
        Run all validation checks and generate comprehensive report.

        Args:
            pages: Extracted page entities
            sections: Extracted section entities
            content_items: Extracted content items

        Returns:
            Complete validation report
        """
        logger.info("Running comprehensive validation...")

        # Validate each entity type
        page_metrics = self.validate_page_extraction(pages)
        section_metrics = self.validate_section_extraction(sections)
        content_metrics = self.validate_content_extraction(content_items)

        # Calculate overall metrics
        overall = {
            'total_pages': len(pages),
            'total_sections': len(sections),
            'total_content_items': len(content_items),
            'avg_precision': (page_metrics.precision + section_metrics.precision + content_metrics.precision) / 3,
            'avg_recall': (page_metrics.recall + section_metrics.recall + content_metrics.recall) / 3,
            'avg_f1': (page_metrics.f1_score + section_metrics.f1_score + content_metrics.f1_score) / 3,
            'avg_accuracy': (page_metrics.accuracy + section_metrics.accuracy + content_metrics.accuracy) / 3
        }

        # Generate confusion matrices (if ground truth available)
        confusion_matrices = {}
        if self.ground_truth:
            # Page type confusion matrix
            page_predictions = [p.get('type', 'unknown') for p in pages]
            page_actuals = [self.ground_truth.get('page_types', {}).get(p.get('id') or p.get('page_name'), 'unknown') for p in pages]
            page_labels = list(set(page_predictions + page_actuals))

            if len(page_predictions) == len(page_actuals):
                confusion_matrices['page_types'] = self.calculate_confusion_matrix(
                    page_predictions, page_actuals, page_labels
                )

        # Generate error report
        errors = self.generate_error_report(pages, sections, content_items)

        return ValidationReport(
            page_type_metrics={'overall': page_metrics},
            section_type_metrics={'overall': section_metrics},
            content_type_metrics={'overall': content_metrics},
            overall_metrics=overall,
            confusion_matrices=confusion_matrices,
            errors=errors
        )

    # Heuristic validation methods (when no ground truth available)

    def _heuristic_page_validation(self, pages: List[Dict]) -> ValidationMetrics:
        """Validate pages using heuristic rules."""
        total = len(pages)
        classified = sum(1 for p in pages if p.get('type') and p['type'] not in ['other', 'unknown'])
        accuracy = classified / total if total > 0 else 0.0

        return ValidationMetrics(
            true_positives=classified,
            false_positives=0,
            false_negatives=total - classified,
            total_samples=total,
            precision=accuracy,
            recall=accuracy,
            f1_score=accuracy,
            accuracy=accuracy
        )

    def _heuristic_section_validation(self, sections: List[Dict]) -> ValidationMetrics:
        """Validate sections using heuristic rules."""
        total = len(sections)
        classified = sum(1 for s in sections if s.get('type') and s['type'] not in ['other', 'unknown'])
        accuracy = classified / total if total > 0 else 0.0

        return ValidationMetrics(
            true_positives=classified,
            false_positives=0,
            false_negatives=total - classified,
            total_samples=total,
            precision=accuracy,
            recall=accuracy,
            f1_score=accuracy,
            accuracy=accuracy
        )

    def _heuristic_content_validation(self, content_items: List[Dict]) -> ValidationMetrics:
        """Validate content using heuristic rules."""
        total = len(content_items)
        classified = sum(1 for c in content_items if c.get('type') and c['type'] not in ['other', 'unknown'])
        accuracy = classified / total if total > 0 else 0.0

        return ValidationMetrics(
            true_positives=classified,
            false_positives=0,
            false_negatives=total - classified,
            total_samples=total,
            precision=accuracy,
            recall=accuracy,
            f1_score=accuracy,
            accuracy=accuracy
        )

    def _infer_page_type_from_name(self, page_name: str) -> str:
        """Infer page type from page name."""
        page_name_lower = page_name.lower()

        if 'homepage' in page_name_lower:
            return 'homepage'
        elif 'programme' in page_name_lower or 'program' in page_name_lower:
            return 'programme'
        elif 'faculty' in page_name_lower:
            return 'faculty'
        elif 'news' in page_name_lower:
            return 'news'
        elif 'event' in page_name_lower:
            return 'event'
        elif 'alumni' in page_name_lower:
            return 'alumni'
        elif 'about' in page_name_lower:
            return 'about'
        elif 'contact' in page_name_lower:
            return 'contact'
        else:
            return 'other'


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extraction_validator.py <extracted_data.json> [ground_truth.json] [output_file]")
        sys.exit(1)

    extracted_path = Path(sys.argv[1])
    ground_truth_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    output_file = Path(sys.argv[3]) if len(sys.argv) > 3 else Path('validation_report.json')

    # Load extracted data
    with open(extracted_path) as f:
        data = json.load(f)

    pages = data.get('pages', [])
    sections = data.get('sections', [])
    content_items = data.get('content_items', [])

    # Create validator and run validation
    validator = ExtractionValidator(ground_truth_path)
    report = validator.validate_all(pages, sections, content_items)

    # Save report
    report.to_json(output_file)
    logger.info(f"Validation report saved to {output_file}")

    # Print summary
    print("\n=== Validation Summary ===")
    print(f"Page Classification Accuracy: {report.page_type_metrics['overall'].accuracy:.2%}")
    print(f"Section Detection Accuracy: {report.section_type_metrics['overall'].accuracy:.2%}")
    print(f"Content Extraction Accuracy: {report.content_type_metrics['overall'].accuracy:.2%}")
    print(f"Overall F1 Score: {report.overall_metrics['avg_f1']:.2%}")
    print(f"Total Errors: {len(report.errors)}")
