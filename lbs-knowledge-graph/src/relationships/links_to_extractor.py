"""
LinksToRelationshipExtractor - Extract LINKS_TO relationships between pages.

Handles:
- Page → Page LINKS_TO relationships
- Link type classification (navigation, reference, citation, related)
- Anchor text extraction
- Link strength calculation
- Internal vs external link handling
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from urllib.parse import urlparse, urljoin

from .models import (
    Edge,
    EdgeType,
    LinkType,
    LinksToProperties,
)

logger = logging.getLogger(__name__)


class LinksToRelationshipExtractor:
    """
    Extract LINKS_TO relationships between pages.

    This extractor creates edges representing hyperlinks:
    - Classifies link types (navigation, reference, etc.)
    - Calculates link strength based on position and context
    - Handles internal and external links
    """

    def __init__(self, base_domain: str = "london.edu") -> None:
        """
        Initialize the LINKS_TO relationship extractor.

        Args:
            base_domain: Base domain for internal link detection
        """
        self.base_domain = base_domain
        self.extracted_edges: Set[Edge] = set()
        self.link_graph: Dict[str, List[str]] = {}  # source -> [targets]

        # Patterns for link classification
        self.navigation_patterns = [
            r"/programmes?/",
            r"/about/",
            r"/admissions/",
            r"/faculty/",
            r"/research/",
            r"/news/",
            r"/events/",
            r"/contact/",
        ]

        self.position_weights = {
            "header": 0.9,
            "navigation": 0.95,
            "content": 0.7,
            "sidebar": 0.5,
            "footer": 0.3,
        }

    def extract_page_links(
        self, page: Dict[str, Any], all_pages: List[Dict[str, Any]]
    ) -> List[Edge]:
        """
        Extract Page → Page LINKS_TO relationships.

        Args:
            page: Page object with 'id', 'url', and 'links' fields
            all_pages: List of all pages for URL resolution

        Returns:
            List of LINKS_TO edges
        """
        edges: List[Edge] = []
        page_id = page.get("id")
        page_url = page.get("url")
        links = page.get("links", [])

        if not page_id or not page_url:
            logger.warning("Page missing ID or URL, skipping link extraction")
            return edges

        # Build URL to ID mapping
        url_to_id = {p.get("url"): p.get("id") for p in all_pages if p.get("url") and p.get("id")}

        for link in links:
            link_url = link.get("url", link.get("href", ""))
            if not link_url:
                continue

            # Resolve relative URLs
            absolute_url = urljoin(page_url, link_url)

            # Check if internal link
            if not self._is_internal_link(absolute_url):
                # Skip external links or create external edge
                continue

            # Find target page ID
            target_id = url_to_id.get(absolute_url)
            if not target_id:
                logger.debug(f"Link target not found in graph: {absolute_url}")
                continue

            # Skip self-links
            if target_id == page_id:
                continue

            # Extract link properties
            anchor_text = link.get("text", link.get("anchor_text", "")).strip()
            context = link.get("context", "")
            position = link.get("position", "content")

            # Classify link type
            link_type = self.classify_link_type(link, context)

            # Calculate link strength
            link_strength = self.calculate_link_strength(link, page, position)

            # Create edge properties
            properties = LinksToProperties(
                link_type=link_type,
                anchor_text=anchor_text or absolute_url,
                link_strength=link_strength,
                position=position,
                context=context[:200] if context else None,  # Limit context length
            ).model_dump()

            # Create edge
            edge = Edge(
                source_id=page_id,
                target_id=target_id,
                relationship_type=EdgeType.LINKS_TO,
                properties=properties,
            )

            edges.append(edge)
            self.extracted_edges.add(edge)

            # Track link graph
            if page_id not in self.link_graph:
                self.link_graph[page_id] = []
            self.link_graph[page_id].append(target_id)

        logger.info(f"Extracted {len(edges)} LINKS_TO edges for page {page_id}")
        return edges

    def classify_link_type(self, link: Dict[str, Any], context: str) -> LinkType:
        """
        Classify the type of link based on URL and context.

        Args:
            link: Link object with 'url' and other properties
            context: Surrounding text context

        Returns:
            LinkType classification
        """
        url = link.get("url", link.get("href", ""))
        position = link.get("position", "").lower()
        css_classes = link.get("class", "").lower()

        # Check position-based classification
        if position in ("header", "navigation", "nav", "menu"):
            return LinkType.NAVIGATION

        if position == "footer":
            # Footer links are typically navigation or related
            return LinkType.NAVIGATION

        # Check CSS class indicators
        if any(x in css_classes for x in ["nav", "menu", "breadcrumb"]):
            return LinkType.NAVIGATION

        if any(x in css_classes for x in ["citation", "reference", "footnote"]):
            return LinkType.CITATION

        if any(x in css_classes for x in ["related", "see-also", "more"]):
            return LinkType.RELATED

        # Check URL patterns
        for pattern in self.navigation_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return LinkType.NAVIGATION

        # Check context for citations
        if context:
            citation_indicators = [
                r"\[\d+\]",  # [1], [2], etc.
                r"\(\d{4}\)",  # (2023), etc.
                r"see also",
                r"refer to",
                r"as discussed in",
            ]
            for indicator in citation_indicators:
                if re.search(indicator, context, re.IGNORECASE):
                    return LinkType.REFERENCE

        # Default to internal link
        return LinkType.INTERNAL

    def calculate_link_strength(
        self, link: Dict[str, Any], page: Dict[str, Any], position: str
    ) -> float:
        """
        Calculate link strength score based on position and context.

        Args:
            link: Link object
            page: Source page object
            position: Link position on page

        Returns:
            Link strength score (0-1)
        """
        strength = 0.5  # Base strength

        # Position weight
        pos_weight = self.position_weights.get(position.lower(), 0.5)
        strength = strength * 0.5 + pos_weight * 0.5

        # Anchor text quality (longer, more descriptive = stronger)
        anchor_text = link.get("text", link.get("anchor_text", ""))
        if anchor_text:
            word_count = len(anchor_text.split())
            if word_count >= 3:
                strength += 0.1
            if word_count >= 5:
                strength += 0.1

        # Context relevance (presence of context = stronger)
        context = link.get("context", "")
        if context and len(context) > 50:
            strength += 0.05

        # Link prominence (heading links are stronger)
        if link.get("in_heading", False):
            strength += 0.15

        # Ensure strength is in valid range
        return max(0.0, min(1.0, strength))

    def build_link_graph(self, pages: List[Dict[str, Any]]) -> List[Edge]:
        """
        Build complete link graph for all pages.

        Args:
            pages: List of all page objects

        Returns:
            List of all LINKS_TO edges
        """
        all_edges: List[Edge] = []

        for page in pages:
            edges = self.extract_page_links(page, pages)
            all_edges.extend(edges)

        logger.info(f"Built link graph with {len(all_edges)} total edges")
        return all_edges

    def _is_internal_link(self, url: str) -> bool:
        """
        Check if a URL is an internal link.

        Args:
            url: URL to check

        Returns:
            True if internal link, False otherwise
        """
        try:
            parsed = urlparse(url)

            # Relative URLs are internal
            if not parsed.netloc:
                return True

            # Check if domain matches
            return self.base_domain in parsed.netloc
        except Exception as e:
            logger.warning(f"Error parsing URL {url}: {e}")
            return False

    def get_inbound_links(self, page_id: str) -> List[str]:
        """
        Get all pages that link to the given page.

        Args:
            page_id: Target page ID

        Returns:
            List of source page IDs
        """
        inbound = []
        for source, targets in self.link_graph.items():
            if page_id in targets:
                inbound.append(source)
        return inbound

    def get_outbound_links(self, page_id: str) -> List[str]:
        """
        Get all pages that the given page links to.

        Args:
            page_id: Source page ID

        Returns:
            List of target page IDs
        """
        return self.link_graph.get(page_id, [])

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about extracted LINKS_TO relationships.

        Returns:
            Dictionary with statistics
        """
        total_edges = len(self.extracted_edges)
        total_sources = len(self.link_graph)
        total_targets = len(set(target for targets in self.link_graph.values() for target in targets))

        # Calculate link type distribution
        link_type_counts: Dict[str, int] = {}
        for edge in self.extracted_edges:
            link_type = edge.properties.get("link_type", "unknown")
            link_type_counts[link_type] = link_type_counts.get(link_type, 0) + 1

        # Calculate average link strength
        strengths = [
            edge.properties.get("link_strength", 0.5)
            for edge in self.extracted_edges
        ]
        avg_strength = sum(strengths) / len(strengths) if strengths else 0.0

        return {
            "total_links_to_edges": total_edges,
            "total_source_pages": total_sources,
            "total_target_pages": total_targets,
            "link_type_distribution": link_type_counts,
            "avg_link_strength": round(avg_strength, 3),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def reset(self) -> None:
        """Reset the extractor state."""
        self.extracted_edges.clear()
        self.link_graph.clear()
