"""
Graph Loader for LBS Knowledge Graph

Loads parsed content and builds complete graph with all entities.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import logging

from .mgraph_compat import MGraph
from .graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


class GraphLoader:
    """
    Load parsed data and build complete knowledge graph

    Features:
    - Load parsed JSON from Phase 1
    - Coordinate with domain extractors
    - Build complete graph with all entities
    - Validate graph integrity
    - Export to multiple formats
    """

    def __init__(self, parsed_dir: Path):
        self.parsed_dir = Path(parsed_dir)
        self.builder = GraphBuilder()

    def load_parsed_data(self) -> List[Dict[str, Any]]:
        """
        Load all parsed page data from directory

        Returns:
            List of page data dictionaries
        """
        logger.info(f"Loading parsed data from {self.parsed_dir}")

        pages = []

        # Iterate through parsed directories
        for page_dir in self.parsed_dir.iterdir():
            if not page_dir.is_dir():
                continue

            try:
                page_data = self._load_page(page_dir)
                if page_data:
                    pages.append(page_data)
            except Exception as e:
                logger.error(f"Error loading page from {page_dir}: {e}")

        logger.info(f"Loaded {len(pages)} pages")
        return pages

    def _load_page(self, page_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Load a single page's data

        Args:
            page_dir: Directory containing page data files

        Returns:
            Page data dictionary or None
        """
        # Load metadata
        metadata_file = page_dir / 'metadata.json'
        if not metadata_file.exists():
            logger.warning(f"No metadata.json in {page_dir}")
            return None

        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Load DOM structure
        dom_file = page_dir / 'dom.json'
        dom = None
        if dom_file.exists():
            with open(dom_file, 'r', encoding='utf-8') as f:
                dom = json.load(f)

        # Load text content
        text_file = page_dir / 'text.json'
        text_map = {}
        if text_file.exists():
            with open(text_file, 'r', encoding='utf-8') as f:
                text_map = json.load(f)

        # Load links
        links_file = page_dir / 'links.json'
        links = []
        if links_file.exists():
            with open(links_file, 'r', encoding='utf-8') as f:
                links = json.load(f)

        # Extract page ID from directory name
        page_id = page_dir.name

        # Build page data structure
        page_data = {
            'id': page_id,
            'url': metadata.get('canonical_url', ''),
            'title': metadata.get('title', 'Untitled'),
            'type': self._classify_page_type(metadata),
            'description': metadata.get('description'),
            'keywords': metadata.get('keywords'),
            'created_at': metadata.get('build_date'),
            'updated_at': metadata.get('build_date'),
            'metadata': metadata,
            'dom': dom,
            'text_map': text_map,
            'links': links
        }

        return page_data

    def _classify_page_type(self, metadata: Dict[str, Any]) -> str:
        """
        Classify page type from metadata

        Args:
            metadata: Page metadata

        Returns:
            Page type classification
        """
        content_type = metadata.get('contenttypename', '').lower()
        title = metadata.get('title', '').lower()
        url = metadata.get('canonical_url', '').lower()

        # Simple classification based on patterns
        if 'landing' in content_type or 'home' in title:
            return 'landing'
        elif 'programme' in url or 'mba' in url:
            return 'program'
        elif 'faculty' in url or 'research' in url:
            return 'faculty'
        elif 'event' in url:
            return 'event'
        elif 'news' in url:
            return 'news'
        elif 'about' in url:
            return 'about'
        elif 'contact' in url:
            return 'contact'
        else:
            return 'other'

    def build_complete_graph(self, pages: List[Dict[str, Any]]) -> MGraph:
        """
        Build complete knowledge graph from parsed data

        Args:
            pages: List of page data dictionaries

        Returns:
            Populated MGraph instance
        """
        logger.info(f"Building graph from {len(pages)} pages")

        # Phase 1: Add all Page nodes
        self.builder.add_pages(pages)

        # Phase 2: Add sections and content from DOM
        for page in pages:
            self._build_page_structure(page)

        # Phase 3: Add links between pages
        for page in pages:
            if page.get('links'):
                self.builder.add_links(page['links'], page['id'])

        logger.info("Graph building complete")
        return self.builder.graph

    def _build_page_structure(self, page: Dict[str, Any]) -> None:
        """
        Build sections and content items from page DOM

        Args:
            page: Page data dictionary
        """
        page_id = page['id']
        dom = page.get('dom')
        text_map = page.get('text_map', {})

        if not dom:
            return

        # Extract sections from DOM
        sections = self._extract_sections(dom, text_map, page_id)

        # Add sections to graph
        for section in sections:
            section_id = section['id']
            content_items = section.pop('content_items', [])

            self.builder.add_sections([section], page_id)

            # Add content items for this section
            if content_items:
                self.builder.add_content_items(content_items, section_id)

    def _extract_sections(self, dom: Dict[str, Any], text_map: Dict[str, str], page_id: str) -> List[Dict[str, Any]]:
        """
        Extract sections from DOM structure

        Args:
            dom: DOM tree dictionary
            text_map: Hash to text mapping
            page_id: Page ID for generating section IDs

        Returns:
            List of section dictionaries
        """
        sections = []
        section_counter = 0

        def traverse_dom(node: Dict[str, Any], depth: int = 0):
            nonlocal section_counter

            # Check if this is a semantic section
            tag = node.get('tag', '')
            if tag in ['section', 'article', 'main', 'header', 'footer', 'nav']:
                section_counter += 1
                section_id = f"{page_id}_section_{section_counter}"

                # Extract text content
                text_hash = node.get('text_hash')
                heading = text_map.get(text_hash, '') if text_hash else ''

                # Extract content items from children
                content_items = self._extract_content_items(node, text_map, section_id)

                section = {
                    'id': section_id,
                    'type': tag,
                    'heading': heading[:200] if heading else None,  # Limit heading length
                    'order': section_counter,
                    'content_items': content_items
                }

                sections.append(section)

            # Recursively traverse children
            for child in node.get('children', []):
                traverse_dom(child, depth + 1)

        traverse_dom(dom)

        # If no sections found, create a default main section
        if not sections:
            sections.append({
                'id': f"{page_id}_section_1",
                'type': 'main',
                'heading': None,
                'order': 1,
                'content_items': self._extract_content_items(dom, text_map, f"{page_id}_section_1")
            })

        return sections

    def _extract_content_items(self, node: Dict[str, Any], text_map: Dict[str, str], section_id: str) -> List[Dict[str, Any]]:
        """
        Extract content items from a section node

        Args:
            node: Section DOM node
            text_map: Hash to text mapping
            section_id: Section ID for generating content IDs

        Returns:
            List of content item dictionaries
        """
        items = []
        item_counter = 0

        def traverse_for_content(n: Dict[str, Any]):
            nonlocal item_counter

            # If node has text hash, create content item
            text_hash = n.get('text_hash')
            if text_hash and text_hash in text_map:
                item_counter += 1
                text = text_map[text_hash]

                items.append({
                    'id': f"{section_id}_content_{item_counter}",
                    'hash': text_hash,
                    'text': text,
                    'type': n.get('tag', 'text'),
                    'word_count': len(text.split()),
                    'order': item_counter
                })

            # Recursively traverse children
            for child in n.get('children', []):
                traverse_for_content(child)

        traverse_for_content(node)
        return items

    def validate_graph(self) -> Dict[str, Any]:
        """
        Validate graph integrity

        Returns:
            Validation report
        """
        return self.builder.validate_graph()

    def save_graph(self, output_dir: Path) -> Dict[str, Path]:
        """
        Save graph to multiple formats

        Args:
            output_dir: Output directory for graph files

        Returns:
            Dictionary mapping format to file path
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving graph to {output_dir}")

        formats = {
            'json': output_dir / 'graph.json',
            'graphml': output_dir / 'graph.graphml',
            'cypher': output_dir / 'graph.cypher',
            'mermaid': output_dir / 'graph.mmd',
            'dot': output_dir / 'graph.dot'
        }

        exported = {}
        for fmt, path in formats.items():
            try:
                self.builder.export_graph(fmt, path)
                exported[fmt] = path
            except Exception as e:
                logger.error(f"Failed to export {fmt}: {e}")

        return exported
