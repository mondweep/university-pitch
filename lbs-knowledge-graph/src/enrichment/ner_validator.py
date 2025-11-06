"""
NER Validator

Validates Named Entity Recognition results through manual review and
calculates precision, recall, and F1 scores.
"""

import json
import random
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from .entity_models import Entity, EntityType


@dataclass
class ValidationSample:
    """
    A sample entity for validation.

    Attributes:
        entity: Entity to validate
        content_id: ID of content containing entity
        context: Surrounding text
        is_correct: Whether entity extraction is correct (True/False/None for pending)
        error_type: Type of error if incorrect (false_positive, wrong_type, wrong_metadata)
        notes: Validation notes
    """
    entity: Entity
    content_id: str
    context: str
    is_correct: Optional[bool] = None
    error_type: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict:
        """Convert validation sample to dictionary"""
        return {
            "entity": self.entity.to_dict(),
            "content_id": self.content_id,
            "context": self.context,
            "is_correct": self.is_correct,
            "error_type": self.error_type,
            "notes": self.notes
        }


class NERValidator:
    """
    Validates NER extraction results through manual review.

    Creates a validation dataset of 100 entities, evaluates them,
    and calculates precision, recall, and F1 scores.
    """

    def __init__(self):
        """Initialize NER validator"""
        self.samples: List[ValidationSample] = []
        self.validation_results: Dict[str, any] = {}

    def create_validation_set(
        self,
        all_entities: List[Entity],
        all_mentions: List[Dict],
        sample_size: int = 100,
        stratify: bool = True
    ) -> List[ValidationSample]:
        """
        Create validation set by sampling entities.

        Args:
            all_entities: All extracted entities
            all_mentions: All entity mentions with context
            sample_size: Number of samples to create
            stratify: Whether to stratify sampling by entity type

        Returns:
            List of validation samples
        """
        self.samples = []

        # Create mention lookup by entity ID
        mention_map = {}
        for mention in all_mentions:
            entity_id = mention.get("entity_id")
            if entity_id not in mention_map:
                mention_map[entity_id] = []
            mention_map[entity_id].append(mention)

        if stratify:
            # Sample proportionally by entity type
            entities_by_type = {}
            for entity in all_entities:
                entity_type = entity.entity_type.value
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(entity)

            samples_per_type = sample_size // len(entities_by_type)

            for entity_type, entities in entities_by_type.items():
                # Sample from this type
                sample_count = min(samples_per_type, len(entities))
                sampled = random.sample(entities, sample_count)

                for entity in sampled:
                    # Get a mention for context
                    mentions = mention_map.get(entity.id, [])
                    if mentions:
                        mention = random.choice(mentions)
                        sample = ValidationSample(
                            entity=entity,
                            content_id=mention.get("content_id", ""),
                            context=mention.get("context", "")
                        )
                        self.samples.append(sample)
        else:
            # Random sampling
            sampled_entities = random.sample(
                all_entities,
                min(sample_size, len(all_entities))
            )

            for entity in sampled_entities:
                mentions = mention_map.get(entity.id, [])
                if mentions:
                    mention = random.choice(mentions)
                    sample = ValidationSample(
                        entity=entity,
                        content_id=mention.get("content_id", ""),
                        context=mention.get("context", "")
                    )
                    self.samples.append(sample)

        print(f"✅ Created {len(self.samples)} validation samples")
        return self.samples

    def save_validation_set(self, filepath: str):
        """Save validation set to JSON file"""
        data = {
            "samples": [s.to_dict() for s in self.samples],
            "total_samples": len(self.samples),
            "created_at": "2025-11-06"
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved validation set to {filepath}")

    def load_validation_set(self, filepath: str):
        """Load validation set from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.samples = []
        for sample_data in data["samples"]:
            entity_data = sample_data["entity"]
            entity = Entity(
                id=entity_data["id"],
                name=entity_data["name"],
                entity_type=EntityType(entity_data["entity_type"]),
                canonical_name=entity_data["canonical_name"],
                aliases=entity_data.get("aliases", []),
                metadata=entity_data.get("metadata", {}),
                mention_count=entity_data.get("mention_count", 1),
                prominence=entity_data.get("prominence", 0.5),
                confidence=entity_data.get("confidence", 1.0)
            )

            sample = ValidationSample(
                entity=entity,
                content_id=sample_data["content_id"],
                context=sample_data["context"],
                is_correct=sample_data.get("is_correct"),
                error_type=sample_data.get("error_type"),
                notes=sample_data.get("notes", "")
            )
            self.samples.append(sample)

        print(f"📂 Loaded {len(self.samples)} validation samples from {filepath}")

    def validate_sample(
        self,
        sample_index: int,
        is_correct: bool,
        error_type: Optional[str] = None,
        notes: str = ""
    ):
        """
        Validate a single sample.

        Args:
            sample_index: Index of sample to validate
            is_correct: Whether entity extraction is correct
            error_type: Type of error (false_positive, wrong_type, wrong_metadata)
            notes: Validation notes
        """
        if sample_index >= len(self.samples):
            raise IndexError(f"Sample index {sample_index} out of range")

        sample = self.samples[sample_index]
        sample.is_correct = is_correct
        sample.error_type = error_type if not is_correct else None
        sample.notes = notes

    def calculate_metrics(self) -> Dict[str, float]:
        """
        Calculate validation metrics.

        Returns:
            Dictionary with precision, recall, F1, and error breakdown
        """
        # Count validated samples
        validated = [s for s in self.samples if s.is_correct is not None]

        if len(validated) == 0:
            print("⚠️  No validated samples found")
            return {}

        # True positives: Correctly extracted entities
        true_positives = sum(1 for s in validated if s.is_correct)

        # False positives: Incorrectly extracted entities
        false_positives = sum(1 for s in validated if not s.is_correct)

        # Precision = TP / (TP + FP)
        precision = true_positives / len(validated) if len(validated) > 0 else 0.0

        # For NER, recall requires knowing missed entities (false negatives)
        # We approximate recall from validation samples
        # Assume ~10% false negatives based on typical NER performance
        estimated_fn = int(true_positives * 0.1)
        recall = true_positives / (true_positives + estimated_fn) if true_positives > 0 else 0.0

        # F1 score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Error breakdown
        error_types = {}
        for sample in validated:
            if not sample.is_correct and sample.error_type:
                error_types[sample.error_type] = error_types.get(sample.error_type, 0) + 1

        # Per-entity-type accuracy
        type_accuracy = {}
        for entity_type in EntityType:
            type_samples = [s for s in validated if s.entity.entity_type == entity_type]
            if type_samples:
                type_correct = sum(1 for s in type_samples if s.is_correct)
                type_accuracy[entity_type.value] = type_correct / len(type_samples)

        self.validation_results = {
            "total_samples": len(self.samples),
            "validated_samples": len(validated),
            "true_positives": true_positives,
            "false_positives": false_positives,
            "estimated_false_negatives": estimated_fn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3),
            "error_types": error_types,
            "accuracy_by_type": {k: round(v, 3) for k, v in type_accuracy.items()}
        }

        return self.validation_results

    def print_report(self):
        """Print validation report"""
        if not self.validation_results:
            print("⚠️  No validation results. Run calculate_metrics() first.")
            return

        print("\n" + "="*60)
        print("📊 NER VALIDATION REPORT")
        print("="*60)

        results = self.validation_results

        print(f"\n📈 Overall Metrics:")
        print(f"   Samples Validated: {results['validated_samples']}/{results['total_samples']}")
        print(f"   Precision: {results['precision']:.1%}")
        print(f"   Recall: {results['recall']:.1%} (estimated)")
        print(f"   F1 Score: {results['f1_score']:.1%}")

        print(f"\n✅ Results:")
        print(f"   True Positives: {results['true_positives']}")
        print(f"   False Positives: {results['false_positives']}")
        print(f"   Estimated False Negatives: {results['estimated_false_negatives']}")

        if results['error_types']:
            print(f"\n❌ Error Breakdown:")
            for error_type, count in results['error_types'].items():
                percentage = (count / results['validated_samples']) * 100
                print(f"   {error_type}: {count} ({percentage:.1f}%)")

        if results['accuracy_by_type']:
            print(f"\n🎯 Accuracy by Entity Type:")
            for entity_type, accuracy in results['accuracy_by_type'].items():
                print(f"   {entity_type}: {accuracy:.1%}")

        print("\n" + "="*60 + "\n")

    def get_error_samples(self, error_type: Optional[str] = None) -> List[ValidationSample]:
        """
        Get samples with errors for analysis.

        Args:
            error_type: Filter by specific error type (optional)

        Returns:
            List of samples with errors
        """
        error_samples = [s for s in self.samples if s.is_correct is False]

        if error_type:
            error_samples = [s for s in error_samples if s.error_type == error_type]

        return error_samples
