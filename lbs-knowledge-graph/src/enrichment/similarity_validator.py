"""
Similarity Validator
Manual validation tool for RELATED_TO relationship quality assessment.
"""

import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class SimilarityValidator:
    """
    Manual validator for similarity relationships.

    Validates that RELATED_TO relationships make semantic sense
    and calculates precision metrics.
    """

    def __init__(self, graph, min_similarity: float = 0.7):
        """
        Initialize validator.

        Args:
            graph: MGraph instance with RELATED_TO relationships
            min_similarity: Minimum similarity threshold to validate
        """
        self.graph = graph
        self.min_similarity = min_similarity
        self.validations = []

        logger.info(f"Initialized SimilarityValidator (threshold={min_similarity})")

    def sample_relationships(
        self,
        sample_size: int = 20,
        random_seed: int = 42
    ) -> List[Dict]:
        """
        Sample random RELATED_TO relationships for validation.

        Args:
            sample_size: Number of relationships to sample
            random_seed: Random seed for reproducibility

        Returns:
            List of sampled relationship dictionaries
        """
        logger.info(f"Sampling {sample_size} RELATED_TO relationships")

        # Collect all RELATED_TO edges
        all_edges = []

        for node_id in self.graph.get_all_nodes():
            edges = self.graph.get_edges(node_id, edge_type='RELATED_TO')

            for edge in edges:
                similarity = edge.get('similarity', 0)

                # Only include edges above threshold
                if similarity >= self.min_similarity:
                    source_node = self.graph.get_node(edge['source'])
                    target_node = self.graph.get_node(edge['target'])

                    if source_node and target_node:
                        all_edges.append({
                            'source_id': edge['source'],
                            'target_id': edge['target'],
                            'source_title': source_node.get('title', 'N/A'),
                            'target_title': target_node.get('title', 'N/A'),
                            'source_text': self._extract_text(source_node),
                            'target_text': self._extract_text(target_node),
                            'similarity': similarity,
                            'similarity_type': edge.get('similarity_type', 'unknown'),
                            'metadata': edge.get('metadata', {})
                        })

        logger.info(f"Found {len(all_edges)} RELATED_TO edges above threshold")

        # Random sampling
        random.seed(random_seed)
        sample_size = min(sample_size, len(all_edges))
        sampled = random.sample(all_edges, sample_size)

        logger.info(f"Sampled {len(sampled)} relationships for validation")

        return sampled

    def _extract_text(self, node: Dict, max_length: int = 300) -> str:
        """
        Extract readable text from node for validation.

        Args:
            node: Node dictionary
            max_length: Maximum text length

        Returns:
            Extracted text
        """
        # Try different text fields
        text_fields = ['description', 'text', 'heading', 'subheading']

        for field in text_fields:
            if field in node and node[field]:
                text = str(node[field])
                if text and len(text.strip()) > 0:
                    return text[:max_length] + ('...' if len(text) > max_length else '')

        # Fallback to title or type
        return node.get('title', node.get('type', 'No text available'))

    def validate_interactive(
        self,
        relationships: List[Dict]
    ) -> Dict:
        """
        Interactive validation of relationships (manual assessment).

        For automated testing, use validate_automated() instead.

        Args:
            relationships: List of relationships to validate

        Returns:
            Validation results with precision metrics
        """
        print("\n" + "=" * 80)
        print("SIMILARITY VALIDATION - INTERACTIVE MODE")
        print("=" * 80)
        print(f"Validating {len(relationships)} RELATED_TO relationships")
        print("\nFor each pair, assess if the similarity makes semantic sense:")
        print("  y = Yes (semantically related)")
        print("  n = No (not semantically related)")
        print("  s = Skip")
        print("=" * 80)

        correct = 0
        incorrect = 0
        skipped = 0

        for idx, rel in enumerate(relationships, 1):
            print(f"\n{'='*80}")
            print(f"Relationship {idx}/{len(relationships)}")
            print(f"{'='*80}")
            print(f"Similarity Score: {rel['similarity']:.3f}")
            print(f"Similarity Type: {rel['similarity_type']}")
            print(f"\nSOURCE: {rel['source_title']}")
            print(f"  ID: {rel['source_id']}")
            print(f"  Text: {rel['source_text']}")
            print(f"\nTARGET: {rel['target_title']}")
            print(f"  ID: {rel['target_id']}")
            print(f"  Text: {rel['target_text']}")

            # Show metadata if available
            if rel['metadata']:
                print(f"\nMetadata:")
                for key, value in rel['metadata'].items():
                    if key != 'method':
                        print(f"  {key}: {value}")

            print(f"\n{'='*80}")

            while True:
                response = input("Is this relationship semantically correct? (y/n/s): ").strip().lower()

                if response == 'y':
                    correct += 1
                    self.validations.append({
                        **rel,
                        'validated': True,
                        'correct': True,
                        'validator': 'human',
                        'validated_at': datetime.utcnow().isoformat()
                    })
                    break
                elif response == 'n':
                    incorrect += 1
                    self.validations.append({
                        **rel,
                        'validated': True,
                        'correct': False,
                        'validator': 'human',
                        'validated_at': datetime.utcnow().isoformat()
                    })
                    break
                elif response == 's':
                    skipped += 1
                    self.validations.append({
                        **rel,
                        'validated': False,
                        'correct': None,
                        'validator': 'human',
                        'validated_at': datetime.utcnow().isoformat()
                    })
                    break
                else:
                    print("Invalid input. Please enter 'y', 'n', or 's'.")

        # Calculate metrics
        total_validated = correct + incorrect
        precision = correct / total_validated if total_validated > 0 else 0.0

        results = {
            'total_relationships': len(relationships),
            'validated': total_validated,
            'correct': correct,
            'incorrect': incorrect,
            'skipped': skipped,
            'precision': precision,
            'target_precision': 0.80,
            'meets_target': precision >= 0.80,
            'validated_at': datetime.utcnow().isoformat()
        }

        # Display results
        print(f"\n{'='*80}")
        print("VALIDATION RESULTS")
        print(f"{'='*80}")
        print(f"Total relationships: {results['total_relationships']}")
        print(f"Validated: {results['validated']}")
        print(f"Correct: {results['correct']}")
        print(f"Incorrect: {results['incorrect']}")
        print(f"Skipped: {results['skipped']}")
        print(f"\nPrecision: {results['precision']:.2%}")
        print(f"Target Precision: {results['target_precision']:.2%}")
        print(f"Status: {'✅ PASSED' if results['meets_target'] else '❌ FAILED'}")
        print(f"{'='*80}\n")

        logger.info(f"Validation complete: {correct}/{total_validated} correct ({precision:.2%} precision)")

        return results

    def validate_automated(
        self,
        relationships: List[Dict],
        validation_rules: Dict = None
    ) -> Dict:
        """
        Automated validation using rules (for testing).

        Args:
            relationships: List of relationships to validate
            validation_rules: Validation rules (for testing)

        Returns:
            Validation results
        """
        logger.info(f"Running automated validation on {len(relationships)} relationships")

        correct = 0
        incorrect = 0

        for rel in relationships:
            # Default validation: similarity >= 0.75 is considered correct
            # This is a heuristic for automated testing
            is_correct = rel['similarity'] >= 0.75

            # Apply custom rules if provided
            if validation_rules:
                is_correct = self._apply_validation_rules(rel, validation_rules)

            if is_correct:
                correct += 1
            else:
                incorrect += 1

            self.validations.append({
                **rel,
                'validated': True,
                'correct': is_correct,
                'validator': 'automated',
                'validated_at': datetime.utcnow().isoformat()
            })

        # Calculate metrics
        total_validated = correct + incorrect
        precision = correct / total_validated if total_validated > 0 else 0.0

        results = {
            'total_relationships': len(relationships),
            'validated': total_validated,
            'correct': correct,
            'incorrect': incorrect,
            'skipped': 0,
            'precision': precision,
            'target_precision': 0.80,
            'meets_target': precision >= 0.80,
            'validated_at': datetime.utcnow().isoformat(),
            'validation_type': 'automated'
        }

        logger.info(
            f"Automated validation complete: {correct}/{total_validated} correct "
            f"({precision:.2%} precision)"
        )

        return results

    def _apply_validation_rules(self, relationship: Dict, rules: Dict) -> bool:
        """
        Apply custom validation rules to relationship.

        Args:
            relationship: Relationship to validate
            rules: Validation rules

        Returns:
            True if relationship passes rules
        """
        # Rule: Minimum similarity threshold
        if 'min_similarity' in rules:
            if relationship['similarity'] < rules['min_similarity']:
                return False

        # Rule: Required metadata fields
        if 'required_metadata' in rules:
            metadata = relationship.get('metadata', {})
            for field in rules['required_metadata']:
                if field not in metadata:
                    return False

        # Rule: Similarity type whitelist
        if 'allowed_types' in rules:
            if relationship['similarity_type'] not in rules['allowed_types']:
                return False

        return True

    def export_validations(self, output_path: str) -> None:
        """
        Export validation results to JSON file.

        Args:
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump({
                'validation_count': len(self.validations),
                'validations': self.validations
            }, f, indent=2)

        logger.info(f"Exported {len(self.validations)} validations to {output_path}")

    def generate_report(self, output_path: str) -> None:
        """
        Generate validation report.

        Args:
            output_path: Output file path
        """
        if not self.validations:
            logger.warning("No validations to report")
            return

        # Calculate metrics
        total = len(self.validations)
        validated = sum(1 for v in self.validations if v['validated'])
        correct = sum(1 for v in self.validations if v.get('correct', False))
        incorrect = sum(1 for v in self.validations if v['validated'] and not v.get('correct', False))
        skipped = total - validated

        precision = correct / validated if validated > 0 else 0.0

        # Generate report
        report = []
        report.append("=" * 80)
        report.append("SIMILARITY VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.utcnow().isoformat()}")
        report.append(f"Total Relationships: {total}")
        report.append(f"Validated: {validated}")
        report.append(f"Correct: {correct}")
        report.append(f"Incorrect: {incorrect}")
        report.append(f"Skipped: {skipped}")
        report.append(f"\nPrecision: {precision:.2%}")
        report.append(f"Target: 80%")
        report.append(f"Status: {'✅ PASSED' if precision >= 0.80 else '❌ FAILED'}")
        report.append("=" * 80)

        # Add incorrect relationships for review
        if incorrect > 0:
            report.append("\nINCORRECT RELATIONSHIPS:")
            report.append("-" * 80)

            for v in self.validations:
                if v['validated'] and not v.get('correct', False):
                    report.append(f"\nSource: {v['source_title']} ({v['source_id']})")
                    report.append(f"Target: {v['target_title']} ({v['target_id']})")
                    report.append(f"Similarity: {v['similarity']:.3f} ({v['similarity_type']})")
                    report.append("-" * 80)

        # Write report
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write('\n'.join(report))

        logger.info(f"Generated validation report: {output_path}")

        # Print to console
        print('\n'.join(report))
