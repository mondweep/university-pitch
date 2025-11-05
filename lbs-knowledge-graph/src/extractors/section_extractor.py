"""
SectionExtractor - Extracts Section entities from DOM structure.

This extractor implements DOM-based section detection, hierarchy building,
and section type classification based on semantic HTML and CSS patterns.

Key Features:
- DOM traversal for section detection
- Semantic HTML tag recognition (section, article, aside, nav)
- CSS class-based section type inference
- Section hierarchy construction
- Order tracking for proper sequencing
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple

from ..models.entities import Section
from ..models.enums import SectionType


logger = logging.getLogger(__name__)


class SectionExtractor:
    """
    Extracts Section entities from DOM structure.

    Identifies major sections within a page using semantic HTML tags,
    CSS classes, and structural patterns.
    """

    # Semantic section tags
    SECTION_TAGS = {'section', 'article', 'aside', 'nav', 'header', 'footer', 'main'}

    # Semantic CSS class patterns for section type detection
    CLASS_PATTERNS = {
        SectionType.HERO: ['hero', 'banner', 'jumbotron', 'masthead'],
        SectionType.NAVIGATION: ['nav', 'navigation', 'menu', 'navbar'],
        SectionType.HEADER: ['header', 'page-header', 'site-header'],
        SectionType.FOOTER: ['footer', 'page-footer', 'site-footer'],
        SectionType.SIDEBAR: ['sidebar', 'aside', 'widget-area'],
        SectionType.CALLOUT: ['cta', 'callout', 'call-to-action', 'promo'],
        SectionType.GALLERY: ['gallery', 'carousel', 'slider', 'slideshow'],
        SectionType.TESTIMONIAL: ['testimonial', 'quote', 'review'],
        SectionType.STATS: ['stats', 'statistics', 'metrics', 'numbers', 'counters'],
        SectionType.PROFILE: ['profile', 'bio', 'biography', 'about-author'],
        SectionType.FORM: ['form', 'contact-form', 'signup'],
        SectionType.LISTING: ['listing', 'grid', 'card-grid', 'post-list'],
    }

    def extract_section_entity(self, section_data: Dict[str, Any], page_id: str) -> Section:
        """
        Extract Section entity from section data.

        Args:
            section_data: Section information from DOM traversal
            page_id: Parent page UUID

        Returns:
            Section entity
        """
        return Section(
            id=str(uuid.uuid4()),
            page_id=page_id,
            type=section_data['type'],
            component=section_data.get('component'),
            heading=section_data.get('heading'),
            subheading=section_data.get('subheading'),
            order=section_data['order'],
            css_selector=section_data.get('css_selector'),
            attributes=section_data.get('attributes', {}),
            metadata=section_data.get('metadata', {})
        )

    def detect_sections(self, dom: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect all sections in the DOM.

        Uses semantic HTML tags, CSS classes, and structural patterns
        to identify major page sections.

        Args:
            dom: Parsed DOM structure

        Returns:
            List of section data dictionaries
        """
        sections = []
        order = 0

        def traverse(node: Dict[str, Any], depth: int = 0, parent_path: str = '') -> None:
            nonlocal order

            # Only look at top-level containers (depth <= 3)
            if depth > 3:
                return

            tag = node.get('tag', '')
            attrs = node.get('attributes', {})
            class_attr = attrs.get('class', '')

            # Check if this is a section-worthy element
            is_section = False

            # 1. Semantic tags
            if tag in self.SECTION_TAGS:
                is_section = True

            # 2. Divs with semantic classes
            elif tag == 'div' and class_attr:
                semantic_keywords = ['hero', 'content', 'sidebar', 'banner', 'wrapper', 'container', 'section']
                if any(kw in class_attr.lower() for kw in semantic_keywords):
                    is_section = True

            if is_section:
                # Extract section information
                section_type = self.classify_section_type(node, order)
                heading = self._extract_heading(node)
                subheading = self._extract_subheading(node)
                css_selector = self._generate_selector(node, parent_path)
                component = self._extract_component_name(node)

                section = {
                    'type': section_type,
                    'component': component,
                    'heading': heading,
                    'subheading': subheading,
                    'order': order,
                    'css_selector': css_selector,
                    'attributes': self._extract_attributes(node),
                    'metadata': {'tag': tag, 'depth': depth}
                }

                sections.append(section)
                order += 1

                # Don't recurse into detected sections (to avoid nested detection)
                return

            # Recurse to children
            for child in node.get('children', []):
                child_path = f"{parent_path} > {tag}" if parent_path else tag
                traverse(child, depth + 1, child_path)

        # Start traversal
        traverse(dom)

        logger.info(f"Detected {len(sections)} sections")
        return sections

    def build_hierarchy(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build hierarchical relationships between sections.

        Analyzes section order and nesting to create parent-child relationships.

        Args:
            sections: List of detected sections

        Returns:
            Hierarchy metadata with parent-child relationships
        """
        hierarchy = {
            'roots': [],
            'children': {},
            'parents': {}
        }

        # For now, treat all sections as top-level (flat hierarchy)
        # Future enhancement: parse CSS selector to determine nesting
        for i, section in enumerate(sections):
            section_id = f"section_{i}"
            hierarchy['roots'].append(section_id)

        return hierarchy

    def classify_section_type(self, section: Dict[str, Any], order: int) -> SectionType:
        """
        Classify section type based on multiple signals.

        Signals:
        1. HTML tag name
        2. CSS classes
        3. Position (first section likely hero)
        4. Child element patterns
        5. Text content patterns

        Args:
            section: Section DOM node
            order: Section order on page

        Returns:
            SectionType classification
        """
        tag = section.get('tag', '')
        attrs = section.get('attributes', {})
        class_attr = attrs.get('class', '').lower()

        # 1. Tag-based classification
        if tag == 'nav':
            return SectionType.NAVIGATION
        if tag == 'header':
            return SectionType.HEADER
        if tag == 'footer':
            return SectionType.FOOTER
        if tag == 'aside':
            return SectionType.SIDEBAR

        # 2. Class-based classification
        for section_type, patterns in self.CLASS_PATTERNS.items():
            if any(pattern in class_attr for pattern in patterns):
                return section_type

        # 3. Position-based heuristics
        if order == 0 or (order == 1 and tag != 'nav'):
            # First non-nav section is often hero
            if 'banner' in class_attr or 'hero' in class_attr or len(class_attr) == 0:
                return SectionType.HERO

        # 4. Child pattern analysis
        children = section.get('children', [])
        if len(children) >= 3:
            if self._are_similar_children(children):
                return SectionType.LISTING

        # 5. Form detection
        if self._contains_form(section):
            return SectionType.FORM

        # Default to CONTENT
        return SectionType.CONTENT

    def _extract_heading(self, element: Dict[str, Any]) -> Optional[str]:
        """
        Extract primary heading from section.

        Looks for h1, h2, h3 tags in direct children.

        Args:
            element: Section DOM node

        Returns:
            Heading text hash or None
        """
        def find_heading(node: Dict[str, Any], max_depth: int = 2) -> Optional[str]:
            if max_depth == 0:
                return None

            tag = node.get('tag', '')
            if tag in ['h1', 'h2', 'h3']:
                text_hash = node.get('text_hash')
                if text_hash:
                    return text_hash

            # Recurse to children
            for child in node.get('children', []):
                heading = find_heading(child, max_depth - 1)
                if heading:
                    return heading

            return None

        return find_heading(element)

    def _extract_subheading(self, element: Dict[str, Any]) -> Optional[str]:
        """
        Extract subheading from section.

        Looks for h4, h5, h6, or paragraph immediately after heading.

        Args:
            element: Section DOM node

        Returns:
            Subheading text hash or None
        """
        # Simplified implementation - just look for h4
        def find_subheading(node: Dict[str, Any], max_depth: int = 2) -> Optional[str]:
            if max_depth == 0:
                return None

            tag = node.get('tag', '')
            if tag in ['h4', 'h5', 'h6']:
                text_hash = node.get('text_hash')
                if text_hash:
                    return text_hash

            for child in node.get('children', []):
                subheading = find_subheading(child, max_depth - 1)
                if subheading:
                    return subheading

            return None

        return find_subheading(element)

    def _generate_selector(self, element: Dict[str, Any], parent_path: str) -> str:
        """
        Generate CSS selector for element.

        Args:
            element: DOM node
            parent_path: Parent element path

        Returns:
            CSS selector string
        """
        tag = element.get('tag', 'div')
        attrs = element.get('attributes', {})

        # Include ID if available
        elem_id = attrs.get('id')
        if elem_id:
            return f"#{elem_id}"

        # Include class if available
        class_attr = attrs.get('class', '').strip()
        if class_attr:
            # Use first class only
            first_class = class_attr.split()[0]
            return f"{tag}.{first_class}"

        return tag

    def _extract_component_name(self, element: Dict[str, Any]) -> Optional[str]:
        """
        Extract component identifier from element.

        Uses class name or ID as component identifier.

        Args:
            element: DOM node

        Returns:
            Component name or None
        """
        attrs = element.get('attributes', {})

        # Prefer ID
        if 'id' in attrs:
            return attrs['id']

        # Use first class
        class_attr = attrs.get('class', '').strip()
        if class_attr:
            return class_attr.split()[0]

        return None

    def _extract_attributes(self, element: Dict[str, Any]) -> Dict[str, str]:
        """Extract HTML attributes from element."""
        return element.get('attributes', {})

    def _are_similar_children(self, children: List[Dict[str, Any]]) -> bool:
        """
        Check if children have similar structure (indicates a listing).

        Args:
            children: List of child DOM nodes

        Returns:
            True if children are similar
        """
        if len(children) < 3:
            return False

        # Compare tags
        tags = [child.get('tag', '') for child in children[:5]]  # Sample first 5
        if len(set(tags)) == 1:  # All same tag
            return True

        # Compare class patterns
        classes = [child.get('attributes', {}).get('class', '') for child in children[:5]]
        if len([c for c in classes if c]) >= 3:  # At least 3 have classes
            # Check if classes are similar
            first_class = classes[0].split()[0] if classes[0] else ''
            if first_class and all(first_class in c for c in classes[1:4] if c):
                return True

        return False

    def _contains_form(self, element: Dict[str, Any]) -> bool:
        """
        Check if element contains a form.

        Args:
            element: DOM node

        Returns:
            True if form found
        """
        def search_form(node: Dict[str, Any], max_depth: int = 3) -> bool:
            if max_depth == 0:
                return False

            if node.get('tag') == 'form':
                return True

            for child in node.get('children', []):
                if search_form(child, max_depth - 1):
                    return True

            return False

        return search_form(element)
