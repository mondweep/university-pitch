#!/usr/bin/env python3
"""
Quality Metrics Calculator - Calculate data quality metrics
Analyzes coverage, completeness, and semantic enrichment quality
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import argparse


@dataclass
class QualityMetrics:
    """Quality metrics container"""
    # Completeness metrics
    total_pages: int = 0
    pages_with_title: int = 0
    pages_with_description: int = 0
    pages_with_sections: int = 0

    total_sections: int = 0
    sections_with_heading: int = 0
    sections_with_content: int = 0

    total_content_items: int = 0
    content_items_with_text: int = 0
    content_items_with_hash: int = 0

    # Semantic enrichment metrics
    content_with_sentiment: int = 0
    content_with_topics: int = 0
    content_with_audiences: int = 0
    content_with_keywords: int = 0

    # Deduplication metrics
    unique_text_hashes: int = 0
    total_text_occurrences: int = 0
    duplicate_content_items: int = 0

    # Data quality metrics
    pages_with_errors: int = 0
    sections_with_errors: int = 0
    content_with_errors: int = 0

    # Relationship metrics
    total_links: int = 0
    internal_links: int = 0
    broken_links: int = 0

    def calculate_percentages(self) -> Dict[str, float]:
        """Calculate percentage metrics"""
        return {
            # Completeness
            'page_title_completeness': self._percent(self.pages_with_title, self.total_pages),
            'page_description_completeness': self._percent(self.pages_with_description, self.total_pages),
            'page_sections_completeness': self._percent(self.pages_with_sections, self.total_pages),
            'section_heading_completeness': self._percent(self.sections_with_heading, self.total_sections),
            'section_content_completeness': self._percent(self.sections_with_content, self.total_sections),
            'content_text_completeness': self._percent(self.content_items_with_text, self.total_content_items),
            'content_hash_completeness': self._percent(self.content_items_with_hash, self.total_content_items),

            # Semantic enrichment
            'sentiment_coverage': self._percent(self.content_with_sentiment, self.total_content_items),
            'topic_coverage': self._percent(self.content_with_topics, self.total_content_items),
            'audience_coverage': self._percent(self.content_with_audiences, self.total_content_items),
            'keyword_coverage': self._percent(self.content_with_keywords, self.total_content_items),

            # Deduplication
            'deduplication_rate': self._percent(
                self.total_text_occurrences - self.unique_text_hashes,
                self.total_text_occurrences
            ),

            # Quality
            'page_error_rate': self._percent(self.pages_with_errors, self.total_pages),
            'section_error_rate': self._percent(self.sections_with_errors, self.total_sections),
            'content_error_rate': self._percent(self.content_with_errors, self.total_content_items),

            # Links
            'internal_link_rate': self._percent(self.internal_links, self.total_links),
            'broken_link_rate': self._percent(self.broken_links, self.total_links),
        }

    @staticmethod
    def _percent(numerator: int, denominator: int) -> float:
        """Calculate percentage with safety check"""
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    def passes_minimum_requirements(self) -> bool:
        """Check if data meets minimum quality requirements"""
        percentages = self.calculate_percentages()

        # NFR requirements from technical specs
        requirements = {
            'page_title_completeness': 95.0,      # Minimum 95% completeness
            'content_text_completeness': 95.0,    # Minimum 95% completeness
            'content_hash_completeness': 95.0,    # All content should be hashed
            'deduplication_rate': 80.0,           # Should catch 80%+ duplicates (target from specs)
            'page_error_rate': 5.0,               # Max 5% error rate (inverse, lower is better)
        }

        failures = []
        for metric, required in requirements.items():
            actual = percentages.get(metric, 0.0)

            # For error rates, lower is better
            if 'error' in metric:
                if actual > required:
                    failures.append(f"{metric}: {actual}% (max {required}%)")
            else:
                if actual < required:
                    failures.append(f"{metric}: {actual}% (min {required}%)")

        return len(failures) == 0, failures


class QualityMetricsCalculator:
    """Calculate comprehensive quality metrics"""

    def __init__(self, data_dir: str = "data/parsed"):
        self.data_dir = Path(data_dir)
        self.metrics = QualityMetrics()
        self.text_hashes = set()
        self.hash_usage_count = {}

    def analyze_page(self, page_data: Dict) -> None:
        """Analyze a single page and update metrics"""
        self.metrics.total_pages += 1

        # Check page completeness
        if page_data.get('title'):
            self.metrics.pages_with_title += 1
        if page_data.get('description'):
            self.metrics.pages_with_description += 1

        sections = page_data.get('sections', [])
        if sections:
            self.metrics.pages_with_sections += 1

        # Analyze sections
        for section in sections:
            self.analyze_section(section)

        # Track errors
        if page_data.get('_validation_errors'):
            self.metrics.pages_with_errors += 1

        # Analyze links
        links = page_data.get('links', [])
        self.metrics.total_links += len(links)
        for link in links:
            if link.get('url', '').startswith('/') or 'london.edu' in link.get('url', ''):
                self.metrics.internal_links += 1
            if link.get('broken'):
                self.metrics.broken_links += 1

    def analyze_section(self, section_data: Dict) -> None:
        """Analyze a single section and update metrics"""
        self.metrics.total_sections += 1

        # Check section completeness
        if section_data.get('heading'):
            self.metrics.sections_with_heading += 1

        content_items = section_data.get('contentItems', [])
        if content_items:
            self.metrics.sections_with_content += 1

        # Analyze content items
        for item in content_items:
            self.analyze_content_item(item)

        # Track errors
        if section_data.get('_validation_errors'):
            self.metrics.sections_with_errors += 1

    def analyze_content_item(self, content_data: Dict) -> None:
        """Analyze a single content item and update metrics"""
        self.metrics.total_content_items += 1

        # Check content completeness
        if content_data.get('text'):
            self.metrics.content_items_with_text += 1

        text_hash = content_data.get('hash')
        if text_hash:
            self.metrics.content_items_with_hash += 1

            # Track hash usage
            self.text_hashes.add(text_hash)
            self.hash_usage_count[text_hash] = self.hash_usage_count.get(text_hash, 0) + 1

        # Check semantic enrichment
        if content_data.get('sentiment'):
            self.metrics.content_with_sentiment += 1

        if content_data.get('topics'):
            self.metrics.content_with_topics += 1

        if content_data.get('audiences'):
            self.metrics.content_with_audiences += 1

        if content_data.get('keywords'):
            self.metrics.content_with_keywords += 1

        # Track errors
        if content_data.get('_validation_errors'):
            self.metrics.content_with_errors += 1

    def finalize_metrics(self) -> None:
        """Calculate final deduplication metrics"""
        self.metrics.unique_text_hashes = len(self.text_hashes)
        self.metrics.total_text_occurrences = sum(self.hash_usage_count.values())
        self.metrics.duplicate_content_items = sum(
            1 for count in self.hash_usage_count.values() if count > 1
        )

    def calculate_all(self) -> QualityMetrics:
        """Process all pages and calculate metrics"""
        json_files = list(self.data_dir.glob('**/*.json'))

        print(f"Analyzing {len(json_files)} files for quality metrics...")

        for i, file_path in enumerate(json_files, 1):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle both single page and array of pages
                if isinstance(data, dict):
                    self.analyze_page(data)
                elif isinstance(data, list):
                    for page in data:
                        self.analyze_page(page)

                if i % 100 == 0:
                    print(f"  Analyzed {i}/{len(json_files)} files...")

            except Exception as e:
                print(f"  Error analyzing {file_path}: {e}")

        # Finalize deduplication metrics
        self.finalize_metrics()

        print(f"✓ Quality analysis complete!")

        return self.metrics

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        percentages = self.metrics.calculate_percentages()
        passes, failures = self.metrics.passes_minimum_requirements()

        return {
            'summary': {
                'total_pages': self.metrics.total_pages,
                'total_sections': self.metrics.total_sections,
                'total_content_items': self.metrics.total_content_items,
                'unique_content_items': self.metrics.unique_text_hashes,
                'passes_requirements': passes
            },
            'completeness': {
                'pages': {
                    'title': percentages['page_title_completeness'],
                    'description': percentages['page_description_completeness'],
                    'sections': percentages['page_sections_completeness']
                },
                'sections': {
                    'heading': percentages['section_heading_completeness'],
                    'content': percentages['section_content_completeness']
                },
                'content': {
                    'text': percentages['content_text_completeness'],
                    'hash': percentages['content_hash_completeness']
                }
            },
            'semantic_enrichment': {
                'sentiment': percentages['sentiment_coverage'],
                'topics': percentages['topic_coverage'],
                'audiences': percentages['audience_coverage'],
                'keywords': percentages['keyword_coverage']
            },
            'deduplication': {
                'rate': percentages['deduplication_rate'],
                'unique_hashes': self.metrics.unique_text_hashes,
                'total_occurrences': self.metrics.total_text_occurrences,
                'duplicate_items': self.metrics.duplicate_content_items
            },
            'quality': {
                'page_errors': percentages['page_error_rate'],
                'section_errors': percentages['section_error_rate'],
                'content_errors': percentages['content_error_rate']
            },
            'relationships': {
                'total_links': self.metrics.total_links,
                'internal_link_rate': percentages['internal_link_rate'],
                'broken_link_rate': percentages['broken_link_rate']
            },
            'requirements_check': {
                'passed': passes,
                'failures': failures if not passes else []
            }
        }

    def print_report(self) -> None:
        """Print quality metrics report"""
        report = self.generate_report()

        print("\n" + "="*60)
        print("DATA QUALITY METRICS REPORT")
        print("="*60)

        # Summary
        summary = report['summary']
        print(f"\nSummary:")
        print(f"  Total pages: {summary['total_pages']:,}")
        print(f"  Total sections: {summary['total_sections']:,}")
        print(f"  Total content items: {summary['total_content_items']:,}")
        print(f"  Unique content items: {summary['unique_content_items']:,}")
        print(f"  Requirements check: {'✓ PASSED' if summary['passes_requirements'] else '✗ FAILED'}")

        # Completeness
        print(f"\nCompleteness Metrics:")
        comp = report['completeness']
        print(f"  Pages:")
        print(f"    Title: {comp['pages']['title']}%")
        print(f"    Description: {comp['pages']['description']}%")
        print(f"    Sections: {comp['pages']['sections']}%")
        print(f"  Sections:")
        print(f"    Heading: {comp['sections']['heading']}%")
        print(f"    Content: {comp['sections']['content']}%")
        print(f"  Content:")
        print(f"    Text: {comp['content']['text']}%")
        print(f"    Hash: {comp['content']['hash']}%")

        # Semantic Enrichment
        print(f"\nSemantic Enrichment Coverage:")
        sem = report['semantic_enrichment']
        print(f"  Sentiment: {sem['sentiment']}%")
        print(f"  Topics: {sem['topics']}%")
        print(f"  Audiences: {sem['audiences']}%")
        print(f"  Keywords: {sem['keywords']}%")

        # Deduplication
        print(f"\nDeduplication Metrics:")
        dedup = report['deduplication']
        print(f"  Deduplication rate: {dedup['rate']}%")
        print(f"  Unique hashes: {dedup['unique_hashes']:,}")
        print(f"  Total occurrences: {dedup['total_occurrences']:,}")
        print(f"  Duplicate items: {dedup['duplicate_items']:,}")

        # Quality
        print(f"\nQuality Metrics:")
        qual = report['quality']
        print(f"  Page error rate: {qual['page_errors']}%")
        print(f"  Section error rate: {qual['section_errors']}%")
        print(f"  Content error rate: {qual['content_errors']}%")

        # Relationships
        print(f"\nRelationship Metrics:")
        rel = report['relationships']
        print(f"  Total links: {rel['total_links']:,}")
        print(f"  Internal link rate: {rel['internal_link_rate']}%")
        print(f"  Broken link rate: {rel['broken_link_rate']}%")

        # Requirements check
        req_check = report['requirements_check']
        if not req_check['passed']:
            print(f"\n⚠️  Requirements Check Failures:")
            for failure in req_check['failures']:
                print(f"  - {failure}")

        print("="*60)

    def export_report(self, output_file: str = "data/quality_metrics.json") -> None:
        """Export quality metrics report to JSON"""
        report = self.generate_report()

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"✓ Quality metrics exported to {output_path}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Calculate data quality metrics'
    )
    parser.add_argument(
        '--data-dir',
        default='data/parsed',
        help='Directory containing parsed JSON files'
    )
    parser.add_argument(
        '--output',
        default='data/quality_metrics.json',
        help='Output file for quality metrics report'
    )

    args = parser.parse_args()

    # Initialize calculator
    calculator = QualityMetricsCalculator(args.data_dir)

    # Calculate metrics
    metrics = calculator.calculate_all()

    # Print report
    calculator.print_report()

    # Export report
    calculator.export_report(args.output)

    # Exit with error code if requirements not met
    report = calculator.generate_report()
    if not report['summary']['passes_requirements']:
        print("\n⚠️  Data does not meet minimum quality requirements!")
        exit(1)
    else:
        print("\n✓ Data meets all minimum quality requirements!")
        exit(0)


if __name__ == "__main__":
    main()
