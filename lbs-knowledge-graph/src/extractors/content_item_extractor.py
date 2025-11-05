"""
ContentItemExtractor - Extracts ContentItem entities from sections.

This extractor implements text block extraction, content type detection,
hash-based deduplication, and media detection.

Key Features:
- Text block extraction from sections
- Content type detection (paragraph, list, quote, code, table)
- Hash linking to text_hashes from Phase 1
- Media detection (images, videos, embeds)
- Link extraction and categorization
- Deduplication via content hashing
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Set

from ..models.entities import ContentItem
from ..models.enums import ContentType


logger = logging.getLogger(__name__)


class ContentItemExtractor:
    """
    Extracts ContentItem entities from parsed text and DOM.

    Creates atomic content items with type classification and deduplication
    via content hashing.
    """

    # Tag to ContentType mapping
    TAG_TYPE_MAP = {
        'h1': ContentType.HEADING,
        'h2': ContentType.SUBHEADING,
        'h3': ContentType.SUBHEADING,
        'h4': ContentType.SUBHEADING,
        'h5': ContentType.SUBHEADING,
        'h6': ContentType.SUBHEADING,
        'p': ContentType.PARAGRAPH,
        'li': ContentType.LIST_ITEM,
        'ul': ContentType.LIST,
        'ol': ContentType.LIST,
        'blockquote': ContentType.QUOTE,
        'pre': ContentType.CODE,
        'code': ContentType.CODE,
        'table': ContentType.TABLE,
        'img': ContentType.IMAGE,
        'video': ContentType.VIDEO,
        'a': ContentType.LINK,
        'button': ContentType.BUTTON,
    }

    def extract_content_entity(self, block: Dict[str, Any], section_id: str) -> ContentItem:
        """
        Extract ContentItem entity from text block.

        Args:
            block: Content block data containing hash, text, and type
            section_id: Parent section UUID

        Returns:
            ContentItem entity
        """
        text = block['text']
        content_hash = block['hash']

        return ContentItem(
            id=str(uuid.uuid4()),
            hash=content_hash,
            text=text,
            type=block['type'],
            sentiment=None,  # Populated in Tier 3
            topics=[],
            keywords=[],
            entities=[],
            audiences=[],
            reading_level=None,
            page_ids=[],  # Populated during relationship building
            section_ids=[section_id],
            usage_count=1,
            language=block.get('language', 'en'),
            word_count=len(text.split()),
            char_count=len(text),
            metadata=block.get('metadata', {})
        )

    def extract_text_blocks(
        self,
        section: Dict[str, Any],
        text_hashes: Dict[str, str],
        dom: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract text blocks from a section.

        Traverses the DOM within the section and extracts all text content,
        linking to text_hashes for deduplication.

        Args:
            section: Section data (should include css_selector or order)
            text_hashes: Map of hash -> text from Phase 1 parser
            dom: Full DOM structure

        Returns:
            List of content block dictionaries
        """
        blocks = []
        seen_hashes: Set[str] = set()

        # Find section in DOM (simplified - in production, use css_selector)
        section_node = self._find_section_node(section, dom)
        if not section_node:
            logger.warning(f"Could not find section node for section {section.get('order')}")
            return blocks

        # Traverse section and extract text blocks
        def traverse(node: Dict[str, Any]) -> None:
            text_hash = node.get('text_hash')

            # If node has text hash, create content item
            if text_hash and text_hash in text_hashes:
                # Skip if already seen (deduplication)
                if text_hash in seen_hashes:
                    return
                seen_hashes.add(text_hash)

                text = text_hashes[text_hash]
                content_type = self.detect_content_type(node, text)

                block = {
                    'hash': text_hash,
                    'text': text,
                    'type': content_type,
                    'language': 'en',  # TODO: detect language
                    'metadata': {
                        'tag': node.get('tag', ''),
                        'attributes': node.get('attributes', {})
                    }
                }
                blocks.append(block)

            # Recurse to children
            for child in node.get('children', []):
                traverse(child)

        traverse(section_node)

        logger.debug(f"Extracted {len(blocks)} text blocks from section")
        return blocks

    def detect_content_type(self, element: Dict[str, Any], text: str = '') -> ContentType:
        """
        Classify content type based on DOM element and text.

        Signals:
        1. HTML tag name
        2. Text length and structure
        3. Text patterns (bullets, numbers)
        4. Parent context

        Args:
            element: DOM node
            text: Text content (optional, for text-based analysis)

        Returns:
            ContentType classification
        """
        tag = element.get('tag', '')

        # 1. Tag-based classification
        if tag in self.TAG_TYPE_MAP:
            return self.TAG_TYPE_MAP[tag]

        # 2. Text-based analysis
        if text:
            # Short text without punctuation = likely heading
            if len(text) < 50:
                if text.isupper():
                    return ContentType.HEADING
                if not text.rstrip().endswith(('.', '!', '?', ':')):
                    return ContentType.HEADING

            # List item patterns
            text_stripped = text.strip()
            if text_stripped.startswith(('•', '-', '*', '▪', '◦', '▫', '▪️')):
                return ContentType.LIST_ITEM

            # Numbered list patterns
            if len(text_stripped) > 0:
                first_char = text_stripped[0]
                if first_char.isdigit():
                    # Check for "1. ", "1) ", etc.
                    if len(text_stripped) > 1 and text_stripped[1:3] in ['. ', ') ', '.\t', ')\t']:
                        return ContentType.LIST_ITEM

            # Quote patterns
            if text_stripped.startswith(('"', '"', '"', '«', '„')) or text_stripped.startswith("'"):
                if text_stripped.endswith(('"', '"', '"', '»', '"', "'")):
                    return ContentType.QUOTE

            # Long text = paragraph
            if len(text) > 50:
                return ContentType.PARAGRAPH

        # 3. Parent context (check if parent is a list)
        # This would require passing parent info - simplified for now

        # Default to paragraph
        return ContentType.PARAGRAPH

    def extract_media(self, section: Dict[str, Any], dom: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract media elements (images, videos) from section.

        Args:
            section: Section data
            dom: Full DOM structure

        Returns:
            List of media metadata dictionaries
        """
        media_items = []

        section_node = self._find_section_node(section, dom)
        if not section_node:
            return media_items

        def traverse(node: Dict[str, Any]) -> None:
            tag = node.get('tag', '')
            attrs = node.get('attributes', {})

            # Image detection
            if tag == 'img':
                media_items.append({
                    'type': 'image',
                    'src': attrs.get('src', ''),
                    'alt': attrs.get('alt', ''),
                    'title': attrs.get('title'),
                    'metadata': attrs
                })

            # Video detection
            elif tag == 'video':
                media_items.append({
                    'type': 'video',
                    'src': attrs.get('src', ''),
                    'poster': attrs.get('poster'),
                    'metadata': attrs
                })

            # iframe embeds (YouTube, Vimeo, etc.)
            elif tag == 'iframe':
                src = attrs.get('src', '')
                media_type = 'embed'
                if 'youtube' in src or 'vimeo' in src:
                    media_type = 'video_embed'

                media_items.append({
                    'type': media_type,
                    'src': src,
                    'metadata': attrs
                })

            # Recurse to children
            for child in node.get('children', []):
                traverse(child)

        traverse(section_node)

        logger.debug(f"Extracted {len(media_items)} media items from section")
        return media_items

    def extract_links(self, section: Dict[str, Any], dom: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract links from section.

        Args:
            section: Section data
            dom: Full DOM structure

        Returns:
            List of link metadata dictionaries
        """
        links = []

        section_node = self._find_section_node(section, dom)
        if not section_node:
            return links

        def traverse(node: Dict[str, Any]) -> None:
            tag = node.get('tag', '')
            attrs = node.get('attributes', {})

            if tag == 'a':
                href = attrs.get('href', '')
                text_hash = node.get('text_hash', '')

                links.append({
                    'href': href,
                    'text_hash': text_hash,
                    'title': attrs.get('title'),
                    'rel': attrs.get('rel'),
                    'target': attrs.get('target'),
                    'metadata': attrs
                })

            # Recurse to children
            for child in node.get('children', []):
                traverse(child)

        traverse(section_node)

        logger.debug(f"Extracted {len(links)} links from section")
        return links

    def _find_section_node(self, section: Dict[str, Any], dom: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find section node in DOM.

        Uses section order or css_selector to locate the corresponding DOM node.

        Args:
            section: Section data
            dom: Full DOM structure

        Returns:
            Section DOM node or None
        """
        # Simplified implementation: find by order
        # In production, use css_selector for more accurate matching

        section_order = section.get('order', -1)
        if section_order < 0:
            return None

        # Collect all section-like nodes
        section_nodes = []

        def traverse(node: Dict[str, Any], depth: int = 0) -> None:
            if depth > 3:
                return

            tag = node.get('tag', '')
            if tag in {'section', 'article', 'aside', 'nav', 'header', 'footer', 'main'}:
                section_nodes.append(node)
                return  # Don't recurse into sections

            for child in node.get('children', []):
                traverse(child, depth + 1)

        traverse(dom)

        # Return section at the specified order
        if section_order < len(section_nodes):
            return section_nodes[section_order]

        return None

    def _find_sections_using_hash(
        self,
        text_hash: str,
        sections: List[Any],
        dom: Dict[str, Any]
    ) -> List[str]:
        """
        Find which sections contain a specific text hash.

        Args:
            text_hash: Text content hash
            sections: List of Section entities or section data
            dom: Full DOM structure

        Returns:
            List of section IDs containing the hash
        """
        section_ids = []

        for section in sections:
            # Get section ID (handle both entity objects and dicts)
            section_id = getattr(section, 'id', None) or section.get('id')
            if not section_id:
                continue

            # Find section node in DOM
            section_data = section if isinstance(section, dict) else {
                'order': section.order,
                'css_selector': section.css_selector
            }

            section_node = self._find_section_node(section_data, dom)
            if not section_node:
                continue

            # Check if hash appears in section subtree
            if self._hash_in_subtree(text_hash, section_node):
                section_ids.append(section_id)

        return section_ids

    def _hash_in_subtree(self, text_hash: str, node: Dict[str, Any]) -> bool:
        """
        Check if text hash appears in node's subtree.

        Args:
            text_hash: Text hash to search for
            node: DOM node to search

        Returns:
            True if hash found
        """
        if node.get('text_hash') == text_hash:
            return True

        for child in node.get('children', []):
            if self._hash_in_subtree(text_hash, child):
                return True

        return False
