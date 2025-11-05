#!/usr/bin/env python3
"""
Completeness Checker - Verify graph completeness against source data
Ensures all parsed content is represented in the knowledge graph
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CompletenessMetrics:
    """Graph completeness metrics"""
    # Expected counts (from parsed data)
    expected_pages: int = 0
    expected_sections: int = 0
    expected_content_items: int = 0
    expected_links: int = 0

    # Actual counts (from graph)
    actual_pages: int = 0
    actual_sections: int = 0
    actual_content_items: int = 0
    actual_links: int = 0

    # Missing entities
    missing_pages: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    missing_content: List[str] = field(default_factory=list)

    # Property completeness
    pages_with_title: int = 0
    pages_with_type: int = 0
    sections_with_heading: int = 0
    content_with_hash: int = 0
    content_with_text: int = 0

    def calculate_percentages(self) -> Dict[str, float]:
        """Calculate completeness percentages"""
        return {
            'node_completeness': self._percent(self.actual_pages, self.expected_pages),
            'section_completeness': self._percent(self.actual_sections, self.expected_sections),
            'content_completeness': self._percent(self.actual_content_items, self.expected_content_items),
            'edge_completeness': self._percent(self.actual_links, self.expected_links),
            'page_title_completeness': self._percent(self.pages_with_title, self.actual_pages),
            'page_type_completeness': self._percent(self.pages_with_type, self.actual_pages),
            'section_heading_completeness': self._percent(self.sections_with_heading, self.actual_sections),
            'content_hash_completeness': self._percent(self.content_with_hash, self.actual_content_items),
            'content_text_completeness': self._percent(self.content_with_text, self.actual_content_items),
        }

    @staticmethod
    def _percent(numerator: int, denominator: int) -> float:
        """Calculate percentage with safety check"""
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    def meets_requirements(self) -> bool:
        """Check if completeness meets NFR6.1 (95%+ completeness)"""
        percentages = self.calculate_percentages()

        required_95 = [
            'node_completeness',
            'section_completeness',
            'content_completeness',
            'page_title_completeness',
            'content_hash_completeness',
            'content_text_completeness'
        ]

        for metric in required_95:
            if percentages.get(metric, 0) < 95.0:
                return False

        return True


@dataclass
class CompletenessReport:
    """Comprehensive completeness report"""
    metrics: CompletenessMetrics
    passes_requirements: bool
    percentages: Dict[str, float]
    missing_entities: Dict[str, List[str]]
    recommendations: List[str] = field(default_factory=list)


class CompletenessChecker:
    """Check graph completeness against parsed data"""

    def __init__(self, parsed_data_dir: str = "data/parsed"):
        self.parsed_data_dir = Path(parsed_data_dir)
        self.metrics = CompletenessMetrics()

    def calculate_node_completeness(
        self,
        graph: Any,  # MGraph instance
        expected_pages: int
    ) -> float:
        """
        Calculate node completeness percentage

        Args:
            graph: MGraph instance
            expected_pages: Expected number of pages from parsing

        Returns:
            Completeness percentage (0-100)
        """
        try:
            # Get actual page count from graph
            if hasattr(graph, 'query'):
                actual_pages = len(list(graph.query(node_type='Page')))
            elif hasattr(graph, 'all_nodes'):
                actual_pages = len([
                    n for n in graph.all_nodes()
                    if hasattr(n, 'node_type') and n.node_type == 'Page'
                ])
            else:
                actual_pages = 0

            self.metrics.expected_pages = expected_pages
            self.metrics.actual_pages = actual_pages

            if expected_pages == 0:
                return 0.0

            return round((actual_pages / expected_pages) * 100, 2)

        except Exception as e:
            logger.error(f"Error calculating node completeness: {e}")
            return 0.0

    def calculate_edge_completeness(
        self,
        graph: Any,
        expected_links: int
    ) -> float:
        """
        Calculate edge completeness percentage

        Args:
            graph: MGraph instance
            expected_links: Expected number of links from parsing

        Returns:
            Completeness percentage (0-100)
        """
        try:
            # Get actual link count from graph
            if hasattr(graph, 'all_edges'):
                actual_links = len([
                    e for e in graph.all_edges()
                    if hasattr(e, 'edge_type') and e.edge_type == 'LINKS_TO'
                ])
            else:
                actual_links = 0

            self.metrics.expected_links = expected_links
            self.metrics.actual_links = actual_links

            if expected_links == 0:
                return 100.0  # No links expected

            return round((actual_links / expected_links) * 100, 2)

        except Exception as e:
            logger.error(f"Error calculating edge completeness: {e}")
            return 0.0

    def check_missing_entities(
        self,
        graph: Any,
        parsed_dir: Path
    ) -> List[str]:
        """
        Identify missing entities by comparing graph to parsed data

        Args:
            graph: MGraph instance
            parsed_dir: Directory with parsed JSON files

        Returns:
            List of missing entity IDs
        """
        missing = []

        try:
            # Load expected pages from parsed data
            json_files = list(parsed_dir.glob('**/*.json'))
            expected_page_ids = set()
            expected_section_ids = set()
            expected_content_ids = set()

            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Handle both single page and array
                    pages = [data] if isinstance(data, dict) else data

                    for page in pages:
                        if not isinstance(page, dict):
                            continue

                        # Track page ID
                        if 'id' in page:
                            expected_page_ids.add(page['id'])

                        # Track section IDs
                        for section in page.get('sections', []):
                            if 'id' in section:
                                expected_section_ids.add(section['id'])

                            # Track content item IDs
                            for content in section.get('contentItems', []):
                                if 'id' in content:
                                    expected_content_ids.add(content['id'])

                except Exception as e:
                    logger.warning(f"Error reading {json_file}: {e}")

            # Update expected counts
            self.metrics.expected_pages = len(expected_page_ids)
            self.metrics.expected_sections = len(expected_section_ids)
            self.metrics.expected_content_items = len(expected_content_ids)

            # Get actual IDs from graph
            actual_page_ids = set()
            actual_section_ids = set()
            actual_content_ids = set()

            if hasattr(graph, 'all_nodes'):
                for node in graph.all_nodes():
                    node_id = node.id if hasattr(node, 'id') else None
                    node_type = node.node_type if hasattr(node, 'node_type') else None

                    if node_id and node_type:
                        if node_type == 'Page':
                            actual_page_ids.add(node_id)
                        elif node_type == 'Section':
                            actual_section_ids.add(node_id)
                        elif node_type == 'ContentItem':
                            actual_content_ids.add(node_id)

            # Update actual counts
            self.metrics.actual_pages = len(actual_page_ids)
            self.metrics.actual_sections = len(actual_section_ids)
            self.metrics.actual_content_items = len(actual_content_ids)

            # Find missing entities
            self.metrics.missing_pages = list(expected_page_ids - actual_page_ids)
            self.metrics.missing_sections = list(expected_section_ids - actual_section_ids)
            self.metrics.missing_content = list(expected_content_ids - actual_content_ids)

            missing = (
                self.metrics.missing_pages +
                self.metrics.missing_sections +
                self.metrics.missing_content
            )

            logger.info(f"Found {len(missing)} missing entities")

        except Exception as e:
            logger.error(f"Error checking missing entities: {e}")

        return missing

    def analyze_property_completeness(self, graph: Any) -> Dict[str, float]:
        """
        Analyze completeness of node properties

        Args:
            graph: MGraph instance

        Returns:
            Dictionary of property completeness percentages
        """
        try:
            if not hasattr(graph, 'all_nodes'):
                return {}

            nodes = list(graph.all_nodes())

            # Check Page properties
            pages = [n for n in nodes if hasattr(n, 'node_type') and n.node_type == 'Page']
            for page in pages:
                data = page.data if hasattr(page, 'data') else {}
                if data.get('title'):
                    self.metrics.pages_with_title += 1
                if data.get('type'):
                    self.metrics.pages_with_type += 1

            # Check Section properties
            sections = [n for n in nodes if hasattr(n, 'node_type') and n.node_type == 'Section']
            for section in sections:
                data = section.data if hasattr(section, 'data') else {}
                if data.get('heading'):
                    self.metrics.sections_with_heading += 1

            # Check ContentItem properties
            content_items = [n for n in nodes if hasattr(n, 'node_type') and n.node_type == 'ContentItem']
            for item in content_items:
                data = item.data if hasattr(item, 'data') else {}
                if data.get('hash'):
                    self.metrics.content_with_hash += 1
                if data.get('text'):
                    self.metrics.content_with_text += 1

            return self.metrics.calculate_percentages()

        except Exception as e:
            logger.error(f"Error analyzing property completeness: {e}")
            return {}

    def generate_completeness_report(
        self,
        graph: Any,
        parsed_dir: Optional[Path] = None
    ) -> CompletenessReport:
        """
        Generate comprehensive completeness report

        Args:
            graph: MGraph instance
            parsed_dir: Optional path to parsed data directory

        Returns:
            CompletenessReport instance
        """
        logger.info("Generating completeness report...")

        # Use instance parsed_dir if not provided
        if parsed_dir is None:
            parsed_dir = self.parsed_data_dir

        # Check missing entities
        if parsed_dir and parsed_dir.exists():
            self.check_missing_entities(graph, parsed_dir)

        # Analyze property completeness
        self.analyze_property_completeness(graph)

        # Calculate percentages
        percentages = self.metrics.calculate_percentages()

        # Check if meets requirements
        passes = self.metrics.meets_requirements()

        # Generate recommendations
        recommendations = self._generate_recommendations(percentages, passes)

        return CompletenessReport(
            metrics=self.metrics,
            passes_requirements=passes,
            percentages=percentages,
            missing_entities={
                'pages': self.metrics.missing_pages,
                'sections': self.metrics.missing_sections,
                'content_items': self.metrics.missing_content
            },
            recommendations=recommendations
        )

    def print_report(self, report: CompletenessReport) -> None:
        """Print completeness report to console"""
        print("\n" + "="*60)
        print("GRAPH COMPLETENESS REPORT")
        print("="*60)

        print(f"\nOverall Status: {'✓ PASSED' if report.passes_requirements else '✗ FAILED'}")

        print(f"\nNode Completeness:")
        print(f"  Pages: {report.metrics.actual_pages}/{report.metrics.expected_pages} "
              f"({report.percentages['node_completeness']}%)")
        print(f"  Sections: {report.metrics.actual_sections}/{report.metrics.expected_sections} "
              f"({report.percentages['section_completeness']}%)")
        print(f"  Content Items: {report.metrics.actual_content_items}/{report.metrics.expected_content_items} "
              f"({report.percentages['content_completeness']}%)")

        print(f"\nEdge Completeness:")
        print(f"  Links: {report.metrics.actual_links}/{report.metrics.expected_links} "
              f"({report.percentages['edge_completeness']}%)")

        print(f"\nProperty Completeness:")
        print(f"  Page Titles: {report.percentages['page_title_completeness']}%")
        print(f"  Page Types: {report.percentages['page_type_completeness']}%")
        print(f"  Section Headings: {report.percentages['section_heading_completeness']}%")
        print(f"  Content Hashes: {report.percentages['content_hash_completeness']}%")
        print(f"  Content Text: {report.percentages['content_text_completeness']}%")

        if report.missing_entities['pages']:
            print(f"\nMissing Pages ({len(report.missing_entities['pages'])}):")
            for page_id in report.missing_entities['pages'][:10]:
                print(f"  - {page_id}")
            if len(report.missing_entities['pages']) > 10:
                print(f"  ... and {len(report.missing_entities['pages']) - 10} more")

        if report.recommendations:
            print(f"\nRecommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")

        print("="*60)

    def export_report(
        self,
        report: CompletenessReport,
        output_file: str = "data/validation/completeness_report.json"
    ) -> None:
        """Export completeness report to JSON"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            'summary': {
                'passes_requirements': report.passes_requirements,
                'node_completeness': report.percentages['node_completeness'],
                'edge_completeness': report.percentages['edge_completeness']
            },
            'metrics': {
                'expected': {
                    'pages': report.metrics.expected_pages,
                    'sections': report.metrics.expected_sections,
                    'content_items': report.metrics.expected_content_items,
                    'links': report.metrics.expected_links
                },
                'actual': {
                    'pages': report.metrics.actual_pages,
                    'sections': report.metrics.actual_sections,
                    'content_items': report.metrics.actual_content_items,
                    'links': report.metrics.actual_links
                }
            },
            'percentages': report.percentages,
            'missing_entities': report.missing_entities,
            'recommendations': report.recommendations
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Completeness report exported to {output_path}")

    def _generate_recommendations(
        self,
        percentages: Dict[str, float],
        passes: bool
    ) -> List[str]:
        """Generate actionable recommendations based on results"""
        recommendations = []

        if passes:
            recommendations.append("Graph completeness meets all requirements (95%+)")
        else:
            if percentages['node_completeness'] < 95:
                recommendations.append(
                    f"Node completeness is {percentages['node_completeness']}%. "
                    "Review graph builder for missing pages."
                )

            if percentages['section_completeness'] < 95:
                recommendations.append(
                    f"Section completeness is {percentages['section_completeness']}%. "
                    "Check section extraction logic."
                )

            if percentages['content_completeness'] < 95:
                recommendations.append(
                    f"Content completeness is {percentages['content_completeness']}%. "
                    "Verify content item processing."
                )

        if percentages['edge_completeness'] < 90:
            recommendations.append(
                f"Edge completeness is {percentages['edge_completeness']}%. "
                "Review link extraction and LINKS_TO edge creation."
            )

        return recommendations


def main():
    """Test completeness checker"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Check graph completeness against parsed data'
    )
    parser.add_argument(
        '--graph-file',
        required=True,
        help='Path to graph JSON file'
    )
    parser.add_argument(
        '--parsed-dir',
        default='data/parsed',
        help='Directory with parsed JSON files'
    )
    parser.add_argument(
        '--output',
        default='data/validation/completeness_report.json',
        help='Output file for completeness report'
    )

    args = parser.parse_args()

    # Load graph (MGraph implementation needed)
    try:
        from mgraph_db import MGraph
        logger.info(f"Loading graph from {args.graph_file}")
        graph = MGraph()
        graph.load_from_json(args.graph_file)
    except ImportError:
        logger.error("mgraph_db not installed. Install with: pip install mgraph-db")
        return 1

    # Check completeness
    checker = CompletenessChecker(args.parsed_dir)
    report = checker.generate_completeness_report(graph)

    # Print report
    checker.print_report(report)

    # Export report
    checker.export_report(report, args.output)

    # Exit with status
    if report.passes_requirements:
        logger.info("✓ Completeness check PASSED")
        return 0
    else:
        logger.error("✗ Completeness check FAILED")
        return 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    exit(main())
