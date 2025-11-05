"""
Pattern Analyzer for LBS Knowledge Graph Project.

Analyzes crawled and parsed content to identify:
- Page type patterns (URL patterns, metadata patterns)
- Section patterns (DOM structure, heading hierarchy)
- Content patterns (text blocks, media usage)
- Link patterns (navigation, references)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PatternReport:
    """Report containing pattern analysis results."""

    total_pages: int
    page_type_patterns: Dict[str, Any]
    section_type_patterns: Dict[str, Any]
    content_patterns: Dict[str, Any]
    link_patterns: Dict[str, Any]
    dom_structure_patterns: Dict[str, Any]
    text_reuse_statistics: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return asdict(self)

    def to_json(self, path: Path) -> None:
        """Save report as JSON."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class PatternAnalyzer:
    """Analyzes patterns in parsed content."""

    def __init__(self, parsed_dir: Path):
        """
        Initialize pattern analyzer.

        Args:
            parsed_dir: Directory containing parsed JSON files
        """
        self.parsed_dir = Path(parsed_dir)
        self.pages_data: List[Dict] = []
        self._load_parsed_pages()

    def _load_parsed_pages(self) -> None:
        """Load all parsed pages from directory."""
        logger.info(f"Loading parsed pages from {self.parsed_dir}")

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

            # Load Next.js data if available
            nextjs_file = page_dir / 'nextjs-data.json'
            if nextjs_file.exists():
                with open(nextjs_file) as f:
                    page_data['nextjs_data'] = json.load(f)

            return page_data

        except Exception as e:
            logger.error(f"Error loading {page_dir}: {e}")
            return None

    def analyze_page_patterns(self) -> Dict[str, Any]:
        """
        Analyze page type patterns.

        Returns:
            Dictionary containing:
            - URL patterns (path structure, naming conventions)
            - Title patterns
            - Metadata patterns
            - Content type distribution
        """
        logger.info("Analyzing page patterns...")

        url_patterns = defaultdict(list)
        title_patterns = []
        metadata_coverage = defaultdict(int)
        page_types = Counter()

        for page in self.pages_data:
            page_name = page['page_name']
            metadata = page.get('metadata', {})

            # Extract URL pattern from page name
            # Format: {path}_{hash}
            parts = page_name.rsplit('_', 1)
            if parts:
                path_part = parts[0]
                url_patterns[self._categorize_url(path_part)].append(page_name)
                page_types[self._categorize_url(path_part)] += 1

            # Analyze title patterns
            title = metadata.get('title', '')
            if title:
                title_patterns.append({
                    'page': page_name,
                    'title': title,
                    'structure': self._analyze_title_structure(title)
                })

            # Check metadata coverage
            for key in metadata.keys():
                metadata_coverage[key] += 1

        return {
            'url_patterns': dict(url_patterns),
            'page_type_distribution': dict(page_types),
            'title_patterns': title_patterns,
            'metadata_coverage': {
                key: {
                    'count': count,
                    'percentage': (count / len(self.pages_data)) * 100
                }
                for key, count in metadata_coverage.items()
            },
            'total_pages': len(self.pages_data)
        }

    def analyze_section_patterns(self) -> Dict[str, Any]:
        """
        Analyze section type patterns.

        Returns:
            Dictionary containing:
            - Common section types
            - Heading hierarchy patterns
            - Section positioning patterns
            - Component usage frequency
        """
        logger.info("Analyzing section patterns...")

        section_types = Counter()
        heading_levels = Counter()
        section_tags = Counter()
        section_classes = Counter()
        depth_distribution = Counter()

        for page in self.pages_data:
            dom = page.get('dom', {})
            sections = self._find_sections(dom)

            for section in sections:
                # Analyze section tags
                tag = section.get('tag', '')
                section_tags[tag] += 1

                # Analyze section classes
                attrs = section.get('attributes', {})
                classes = attrs.get('class', '')
                if classes:
                    for cls in classes.split():
                        section_classes[cls] += 1

                # Analyze depth
                depth = section.get('depth', 0)
                depth_distribution[depth] += 1

                # Classify section type
                section_type = self._classify_section(section)
                section_types[section_type] += 1

                # Analyze heading hierarchy
                headings = self._find_headings(section)
                for heading in headings:
                    heading_levels[heading['tag']] += 1

        return {
            'section_types': dict(section_types.most_common()),
            'common_tags': dict(section_tags.most_common(20)),
            'common_classes': dict(section_classes.most_common(30)),
            'heading_levels': dict(heading_levels),
            'depth_distribution': dict(depth_distribution),
            'avg_sections_per_page': len(section_tags) / len(self.pages_data) if self.pages_data else 0
        }

    def analyze_content_patterns(self) -> Dict[str, Any]:
        """
        Analyze content block patterns.

        Returns:
            Dictionary containing:
            - Content type distribution
            - Text length patterns
            - Media usage patterns
            - Content element frequencies
        """
        logger.info("Analyzing content patterns...")

        content_types = Counter()
        text_lengths = []
        media_elements = Counter()
        interactive_elements = Counter()

        for page in self.pages_data:
            text_hashes = page.get('text_hashes', {})
            dom = page.get('dom', {})

            # Analyze text content
            for hash_val, text in text_hashes.items():
                length = len(text)
                text_lengths.append(length)

                # Classify content type by length and structure
                content_type = self._classify_content_type(text, length)
                content_types[content_type] += 1

            # Analyze media and interactive elements
            self._analyze_dom_elements(dom, media_elements, interactive_elements)

        # Calculate statistics
        avg_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0

        return {
            'content_types': dict(content_types.most_common()),
            'text_statistics': {
                'total_blocks': len(text_lengths),
                'avg_length': avg_length,
                'min_length': min(text_lengths) if text_lengths else 0,
                'max_length': max(text_lengths) if text_lengths else 0,
                'length_ranges': self._categorize_lengths(text_lengths)
            },
            'media_usage': dict(media_elements.most_common()),
            'interactive_elements': dict(interactive_elements.most_common())
        }

    def analyze_link_patterns(self) -> Dict[str, Any]:
        """
        Analyze link patterns across pages.

        Returns:
            Dictionary containing:
            - Link type distribution (internal, external, anchor)
            - Common link destinations
            - Link context patterns
            - Navigation structure
        """
        logger.info("Analyzing link patterns...")

        link_types = Counter()
        destinations = Counter()
        link_text_patterns = []
        internal_links = []

        for page in self.pages_data:
            links = page.get('links', [])
            page_name = page['page_name']

            for link in links:
                href = link.get('href', '')
                text = link.get('text', '')
                link_type = link.get('type', 'unknown')

                link_types[link_type] += 1

                if link_type == 'internal':
                    internal_links.append({
                        'source': page_name,
                        'target': href,
                        'text': text
                    })
                    destinations[href] += 1

                if text:
                    link_text_patterns.append({
                        'text': text,
                        'type': link_type,
                        'page': page_name
                    })

        return {
            'link_types': dict(link_types),
            'top_destinations': dict(destinations.most_common(20)),
            'total_links': sum(link_types.values()),
            'avg_links_per_page': sum(link_types.values()) / len(self.pages_data) if self.pages_data else 0,
            'internal_link_graph': internal_links,
            'link_text_samples': link_text_patterns[:50]
        }

    def analyze_text_reuse(self) -> Dict[str, Any]:
        """
        Analyze how text content is reused across pages.

        Returns:
            Dictionary containing:
            - Total unique texts
            - Reuse statistics
            - Most reused content
            - Unique content per page
        """
        logger.info("Analyzing text reuse patterns...")

        global_hashes = defaultdict(lambda: {'text': '', 'pages': [], 'count': 0})

        for page in self.pages_data:
            text_hashes = page.get('text_hashes', {})
            page_name = page['page_name']

            for hash_val, text in text_hashes.items():
                global_hashes[hash_val]['text'] = text
                global_hashes[hash_val]['pages'].append(page_name)
                global_hashes[hash_val]['count'] += 1

        # Calculate statistics
        unique_texts = len(global_hashes)
        total_instances = sum(data['count'] for data in global_hashes.values())
        reuse_ratio = total_instances / unique_texts if unique_texts > 0 else 0

        # Find most reused content
        most_reused = sorted(
            global_hashes.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:20]

        return {
            'total_unique_texts': unique_texts,
            'total_text_instances': total_instances,
            'reuse_ratio': reuse_ratio,
            'most_reused': [
                {
                    'hash': hash_val,
                    'text': data['text'][:100] + '...' if len(data['text']) > 100 else data['text'],
                    'usage_count': data['count'],
                    'pages': data['pages']
                }
                for hash_val, data in most_reused
            ],
            'reuse_distribution': {
                'single_use': sum(1 for data in global_hashes.values() if data['count'] == 1),
                'low_reuse_2_5': sum(1 for data in global_hashes.values() if 2 <= data['count'] <= 5),
                'medium_reuse_6_20': sum(1 for data in global_hashes.values() if 6 <= data['count'] <= 20),
                'high_reuse_20_plus': sum(1 for data in global_hashes.values() if data['count'] > 20)
            }
        }

    def generate_report(self) -> PatternReport:
        """Generate comprehensive pattern analysis report."""
        logger.info("Generating comprehensive pattern report...")

        return PatternReport(
            total_pages=len(self.pages_data),
            page_type_patterns=self.analyze_page_patterns(),
            section_type_patterns=self.analyze_section_patterns(),
            content_patterns=self.analyze_content_patterns(),
            link_patterns=self.analyze_link_patterns(),
            dom_structure_patterns=self._analyze_dom_structures(),
            text_reuse_statistics=self.analyze_text_reuse()
        )

    # Helper methods

    def _categorize_url(self, path: str) -> str:
        """Categorize URL based on path."""
        if 'homepage' in path:
            return 'homepage'
        elif 'programme' in path or 'program' in path:
            return 'programme'
        elif 'faculty' in path:
            return 'faculty'
        elif 'news' in path:
            return 'news'
        elif 'event' in path:
            return 'event'
        elif 'alumni' in path:
            return 'alumni'
        elif 'about' in path:
            return 'about'
        elif 'contact' in path:
            return 'contact'
        else:
            return 'other'

    def _analyze_title_structure(self, title: str) -> Dict[str, Any]:
        """Analyze title structure."""
        parts = title.split('|')
        return {
            'has_separator': '|' in title,
            'parts_count': len(parts),
            'pattern': ' | '.join(['<part>'] * len(parts))
        }

    def _find_sections(self, dom: Dict) -> List[Dict]:
        """Find section-like elements in DOM."""
        sections = []

        def traverse(node: Dict, depth: int = 0) -> None:
            if depth > 4:  # Limit depth
                return

            tag = node.get('tag', '')

            # Section-like tags
            if tag in ['section', 'article', 'aside', 'nav', 'header', 'footer', 'main']:
                sections.append(node)
            elif tag == 'div':
                # Check for semantic classes
                attrs = node.get('attributes', {})
                classes = attrs.get('class', '').lower()
                if any(cls in classes for cls in ['hero', 'content', 'sidebar', 'wrapper']):
                    sections.append(node)

            for child in node.get('children', []):
                traverse(child, depth + 1)

        traverse(dom)
        return sections

    def _classify_section(self, section: Dict) -> str:
        """Classify section type."""
        tag = section.get('tag', '')
        attrs = section.get('attributes', {})
        classes = attrs.get('class', '').lower()

        if tag == 'nav':
            return 'navigation'
        elif tag == 'header':
            return 'header'
        elif tag == 'footer':
            return 'footer'
        elif 'hero' in classes:
            return 'hero'
        elif 'sidebar' in classes:
            return 'sidebar'
        elif tag in ['article', 'section']:
            return 'content'
        else:
            return 'other'

    def _find_headings(self, node: Dict) -> List[Dict]:
        """Find heading elements in a node."""
        headings = []

        def traverse(n: Dict) -> None:
            tag = n.get('tag', '')
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                headings.append(n)
            for child in n.get('children', []):
                traverse(child)

        traverse(node)
        return headings

    def _classify_content_type(self, text: str, length: int) -> str:
        """Classify content type based on text and length."""
        if length < 20:
            return 'short_text'  # Buttons, labels, etc.
        elif length < 100:
            return 'heading_or_title'
        elif length < 500:
            return 'paragraph'
        else:
            return 'long_content'

    def _categorize_lengths(self, lengths: List[int]) -> Dict[str, int]:
        """Categorize text lengths into ranges."""
        ranges = {
            '0-50': 0,
            '51-200': 0,
            '201-500': 0,
            '501-1000': 0,
            '1000+': 0
        }

        for length in lengths:
            if length <= 50:
                ranges['0-50'] += 1
            elif length <= 200:
                ranges['51-200'] += 1
            elif length <= 500:
                ranges['201-500'] += 1
            elif length <= 1000:
                ranges['501-1000'] += 1
            else:
                ranges['1000+'] += 1

        return ranges

    def _analyze_dom_elements(self, dom: Dict, media: Counter, interactive: Counter) -> None:
        """Analyze media and interactive elements in DOM."""
        def traverse(node: Dict) -> None:
            tag = node.get('tag', '')

            # Media elements
            if tag == 'img':
                media['image'] += 1
            elif tag == 'video':
                media['video'] += 1
            elif tag == 'audio':
                media['audio'] += 1
            elif tag == 'iframe':
                media['iframe'] += 1

            # Interactive elements
            elif tag == 'button':
                interactive['button'] += 1
            elif tag == 'a':
                interactive['link'] += 1
            elif tag == 'input':
                interactive['input'] += 1
            elif tag == 'form':
                interactive['form'] += 1

            for child in node.get('children', []):
                traverse(child)

        traverse(dom)

    def _analyze_dom_structures(self) -> Dict[str, Any]:
        """Analyze DOM structure patterns."""
        max_depths = []
        avg_children = []

        for page in self.pages_data:
            dom = page.get('dom', {})
            max_depth = self._calculate_max_depth(dom)
            avg_child_count = self._calculate_avg_children(dom)

            max_depths.append(max_depth)
            avg_children.append(avg_child_count)

        return {
            'avg_max_depth': sum(max_depths) / len(max_depths) if max_depths else 0,
            'avg_children_per_node': sum(avg_children) / len(avg_children) if avg_children else 0,
            'depth_distribution': dict(Counter(max_depths))
        }

    def _calculate_max_depth(self, dom: Dict) -> int:
        """Calculate maximum depth of DOM tree."""
        def traverse(node: Dict) -> int:
            if not node.get('children'):
                return 0
            return 1 + max((traverse(child) for child in node['children']), default=0)

        return traverse(dom)

    def _calculate_avg_children(self, dom: Dict) -> float:
        """Calculate average number of children per node."""
        node_count = 0
        total_children = 0

        def traverse(node: Dict) -> None:
            nonlocal node_count, total_children
            node_count += 1
            children = node.get('children', [])
            total_children += len(children)
            for child in children:
                traverse(child)

        traverse(dom)
        return total_children / node_count if node_count > 0 else 0


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pattern_analyzer.py <parsed_dir> [output_file]")
        sys.exit(1)

    parsed_dir = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('pattern_report.json')

    analyzer = PatternAnalyzer(parsed_dir)
    report = analyzer.generate_report()

    report.to_json(output_file)
    logger.info(f"Pattern report saved to {output_file}")
