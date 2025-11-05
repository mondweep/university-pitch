"""
Ground Truth Builder for LBS Knowledge Graph Project.

Provides tools for creating ground truth datasets for validation:
- Manual labeling interface
- Sample page selection
- Ground truth dataset management
- Comparison helpers
"""

import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GroundTruthEntry:
    """Single ground truth entry."""

    entity_id: str
    entity_type: str  # 'page', 'section', 'content'
    label: str  # Expected type/classification
    metadata: Dict[str, Any]
    labeled_by: str
    labeled_at: str
    confidence: float = 1.0  # 0.0-1.0
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GroundTruthDataset:
    """Collection of ground truth entries."""

    name: str
    description: str
    created_at: str
    entries: List[GroundTruthEntry]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'entries': [e.to_dict() for e in self.entries],
            'metadata': self.metadata
        }

    def to_json(self, path: Path) -> None:
        """Save dataset as JSON."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved ground truth dataset to {path}")

    @classmethod
    def from_json(cls, path: Path) -> 'GroundTruthDataset':
        """Load dataset from JSON."""
        with open(path) as f:
            data = json.load(f)

        entries = [
            GroundTruthEntry(**entry_data)
            for entry_data in data['entries']
        ]

        return cls(
            name=data['name'],
            description=data['description'],
            created_at=data['created_at'],
            entries=entries,
            metadata=data.get('metadata', {})
        )


class GroundTruthBuilder:
    """Interactive tool for creating ground truth datasets."""

    def __init__(self, parsed_dir: Path, output_dir: Path):
        """
        Initialize ground truth builder.

        Args:
            parsed_dir: Directory containing parsed content
            output_dir: Directory for saving ground truth datasets
        """
        self.parsed_dir = Path(parsed_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.pages_data: List[Dict] = []
        self.ground_truth_entries: List[GroundTruthEntry] = []

        self._load_pages()

    def _load_pages(self) -> None:
        """Load all parsed pages."""
        logger.info(f"Loading pages from {self.parsed_dir}")

        for page_dir in self.parsed_dir.iterdir():
            if not page_dir.is_dir():
                continue

            page_data = self._load_page_data(page_dir)
            if page_data:
                self.pages_data.append(page_data)

        logger.info(f"Loaded {len(self.pages_data)} pages")

    def _load_page_data(self, page_dir: Path) -> Optional[Dict]:
        """Load data for a single page."""
        try:
            page_data = {
                'page_name': page_dir.name,
                'path': page_dir
            }

            # Load metadata
            metadata_file = page_dir / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file) as f:
                    page_data['metadata'] = json.load(f)

            # Load DOM
            dom_file = page_dir / 'dom.json'
            if dom_file.exists():
                with open(dom_file) as f:
                    page_data['dom'] = json.load(f)

            # Load text hashes
            text_file = page_dir / 'text.json'
            if text_file.exists():
                with open(text_file) as f:
                    page_data['text_hashes'] = json.load(f)

            # Load links
            links_file = page_dir / 'links.json'
            if links_file.exists():
                with open(links_file) as f:
                    page_data['links'] = json.load(f)

            return page_data

        except Exception as e:
            logger.error(f"Error loading {page_dir}: {e}")
            return None

    def sample_pages(
        self,
        num_samples: int = 20,
        strategy: str = 'random'
    ) -> List[Dict]:
        """
        Sample pages for manual labeling.

        Args:
            num_samples: Number of pages to sample
            strategy: Sampling strategy ('random', 'diverse', 'stratified')

        Returns:
            List of sampled page data
        """
        if strategy == 'random':
            return random.sample(self.pages_data, min(num_samples, len(self.pages_data)))

        elif strategy == 'diverse':
            # Select diverse pages based on URL patterns
            page_types = {}
            for page in self.pages_data:
                page_type = self._infer_page_type(page['page_name'])
                if page_type not in page_types:
                    page_types[page_type] = []
                page_types[page_type].append(page)

            # Sample from each type
            samples = []
            samples_per_type = max(1, num_samples // len(page_types))
            for pages in page_types.values():
                samples.extend(random.sample(pages, min(samples_per_type, len(pages))))

            return samples[:num_samples]

        elif strategy == 'stratified':
            # Ensure proportional representation
            page_types = {}
            for page in self.pages_data:
                page_type = self._infer_page_type(page['page_name'])
                if page_type not in page_types:
                    page_types[page_type] = []
                page_types[page_type].append(page)

            total = len(self.pages_data)
            samples = []

            for page_type, pages in page_types.items():
                proportion = len(pages) / total
                type_samples = int(num_samples * proportion)
                samples.extend(random.sample(pages, min(type_samples, len(pages))))

            return samples[:num_samples]

        else:
            raise ValueError(f"Unknown sampling strategy: {strategy}")

    def create_interactive_labeling_session(
        self,
        samples: List[Dict],
        labeler_name: str = 'annotator'
    ) -> GroundTruthDataset:
        """
        Create interactive labeling session for manual annotation.

        Args:
            samples: Pages to label
            labeler_name: Name of person doing labeling

        Returns:
            GroundTruthDataset with labeled entries
        """
        logger.info(f"Starting interactive labeling session for {len(samples)} pages")
        print(f"\n{'='*60}")
        print(f"Ground Truth Labeling Session")
        print(f"{'='*60}\n")
        print(f"Pages to label: {len(samples)}")
        print(f"Labeler: {labeler_name}\n")

        entries = []

        page_type_options = [
            'homepage', 'programme', 'faculty', 'news', 'event',
            'alumni', 'about', 'admissions', 'student_life', 'contact', 'other'
        ]

        for i, page in enumerate(samples, 1):
            print(f"\n--- Page {i}/{len(samples)} ---")
            print(f"Page Name: {page['page_name']}")

            metadata = page.get('metadata', {})
            print(f"Title: {metadata.get('title', 'N/A')}")
            print(f"Description: {metadata.get('description', 'N/A')[:100]}...")

            # Show inferred type
            inferred = self._infer_page_type(page['page_name'])
            print(f"Inferred Type: {inferred}")

            # Get label
            print(f"\nPage Type Options: {', '.join(page_type_options)}")
            label = input(f"Enter page type (or press Enter to accept '{inferred}'): ").strip()

            if not label:
                label = inferred

            confidence = input("Confidence (0.0-1.0, default 1.0): ").strip()
            confidence = float(confidence) if confidence else 1.0

            notes = input("Notes (optional): ").strip() or None

            # Create entry
            entry = GroundTruthEntry(
                entity_id=page['page_name'],
                entity_type='page',
                label=label,
                metadata={
                    'title': metadata.get('title'),
                    'url_pattern': page['page_name']
                },
                labeled_by=labeler_name,
                labeled_at=datetime.now().isoformat(),
                confidence=confidence,
                notes=notes
            )

            entries.append(entry)
            self.ground_truth_entries.append(entry)

        print(f"\n{'='*60}")
        print(f"Labeling session complete!")
        print(f"Total labeled: {len(entries)}")
        print(f"{'='*60}\n")

        # Create dataset
        dataset = GroundTruthDataset(
            name=f"manual_labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"Manual labels created by {labeler_name}",
            created_at=datetime.now().isoformat(),
            entries=entries,
            metadata={
                'labeler': labeler_name,
                'total_entries': len(entries),
                'sampling_strategy': 'manual'
            }
        )

        return dataset

    def create_automated_ground_truth(
        self,
        samples: Optional[List[Dict]] = None,
        labeler_name: str = 'automated'
    ) -> GroundTruthDataset:
        """
        Create ground truth using automated heuristic rules.

        Useful for initial baseline when manual labeling isn't available.

        Args:
            samples: Pages to label (or all if None)
            labeler_name: Name for automated labeler

        Returns:
            GroundTruthDataset with automated labels
        """
        logger.info("Creating automated ground truth labels...")

        if samples is None:
            samples = self.pages_data

        entries = []

        for page in samples:
            page_name = page['page_name']
            label = self._infer_page_type(page_name)

            # Lower confidence for automated labels
            confidence = 0.7 if label != 'other' else 0.3

            entry = GroundTruthEntry(
                entity_id=page_name,
                entity_type='page',
                label=label,
                metadata={
                    'title': page.get('metadata', {}).get('title'),
                    'automated': True
                },
                labeled_by=labeler_name,
                labeled_at=datetime.now().isoformat(),
                confidence=confidence,
                notes='Automated heuristic labeling'
            )

            entries.append(entry)

        dataset = GroundTruthDataset(
            name=f"automated_labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Automated heuristic labels",
            created_at=datetime.now().isoformat(),
            entries=entries,
            metadata={
                'labeler': labeler_name,
                'total_entries': len(entries),
                'automated': True
            }
        )

        return dataset

    def export_for_validation(
        self,
        dataset: GroundTruthDataset,
        output_file: Optional[Path] = None
    ) -> Path:
        """
        Export ground truth in format expected by ExtractionValidator.

        Args:
            dataset: GroundTruthDataset to export
            output_file: Output path (auto-generated if None)

        Returns:
            Path to exported file
        """
        if output_file is None:
            output_file = self.output_dir / f"{dataset.name}_validator_format.json"

        # Convert to validator format
        validator_format = {
            'page_types': {},
            'section_types': {},
            'content_types': {},
            'metadata': dataset.metadata
        }

        for entry in dataset.entries:
            if entry.entity_type == 'page':
                validator_format['page_types'][entry.entity_id] = entry.label
            elif entry.entity_type == 'section':
                page_id = entry.metadata.get('page_id')
                if page_id not in validator_format['section_types']:
                    validator_format['section_types'][page_id] = []
                validator_format['section_types'][page_id].append(entry.label)
            elif entry.entity_type == 'content':
                section_id = entry.metadata.get('section_id')
                if section_id not in validator_format['content_types']:
                    validator_format['content_types'][section_id] = []
                validator_format['content_types'][section_id].append(entry.label)

        with open(output_file, 'w') as f:
            json.dump(validator_format, f, indent=2)

        logger.info(f"Exported ground truth to {output_file}")
        return output_file

    def compare_with_extracted(
        self,
        dataset: GroundTruthDataset,
        extracted_pages: List[Dict]
    ) -> Dict[str, Any]:
        """
        Compare ground truth with extracted classifications.

        Args:
            dataset: Ground truth dataset
            extracted_pages: Extracted page data

        Returns:
            Comparison results
        """
        matches = 0
        mismatches = []

        # Build lookup
        ground_truth_lookup = {
            entry.entity_id: entry.label
            for entry in dataset.entries
            if entry.entity_type == 'page'
        }

        for page in extracted_pages:
            page_id = page.get('id') or page.get('page_name')
            extracted_type = page.get('type') or self._infer_page_type(page_id)
            expected_type = ground_truth_lookup.get(page_id)

            if expected_type:
                if extracted_type == expected_type:
                    matches += 1
                else:
                    mismatches.append({
                        'page_id': page_id,
                        'expected': expected_type,
                        'extracted': extracted_type
                    })

        total = len(ground_truth_lookup)
        accuracy = matches / total if total > 0 else 0.0

        return {
            'total_compared': total,
            'matches': matches,
            'mismatches': len(mismatches),
            'accuracy': accuracy,
            'mismatch_details': mismatches
        }

    def _infer_page_type(self, page_name: str) -> str:
        """Infer page type from page name using heuristics."""
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
        elif 'admissions' in page_name_lower or 'admission' in page_name_lower:
            return 'admissions'
        elif 'student' in page_name_lower or 'life' in page_name_lower:
            return 'student_life'
        elif 'contact' in page_name_lower:
            return 'contact'
        else:
            return 'other'


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ground_truth.py <parsed_dir> [mode] [num_samples]")
        print("Modes: interactive, automated")
        sys.exit(1)

    parsed_dir = Path(sys.argv[1])
    mode = sys.argv[2] if len(sys.argv) > 2 else 'automated'
    num_samples = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    output_dir = parsed_dir.parent / 'analysis' / 'ground_truth'

    builder = GroundTruthBuilder(parsed_dir, output_dir)

    if mode == 'interactive':
        samples = builder.sample_pages(num_samples, strategy='diverse')
        dataset = builder.create_interactive_labeling_session(samples)
    else:
        samples = builder.sample_pages(num_samples, strategy='diverse')
        dataset = builder.create_automated_ground_truth(samples)

    # Save dataset
    dataset.to_json(output_dir / f"{dataset.name}.json")

    # Export for validator
    validator_file = builder.export_for_validation(dataset)

    logger.info(f"Ground truth dataset created with {len(dataset.entries)} entries")
    logger.info(f"Saved to: {output_dir / dataset.name}.json")
    logger.info(f"Validator format: {validator_file}")
