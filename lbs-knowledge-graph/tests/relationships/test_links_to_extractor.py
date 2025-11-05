"""
Unit tests for LinksToRelationshipExtractor.
"""

import pytest
from src.relationships.links_to_extractor import LinksToRelationshipExtractor
from src.relationships.models import Edge, EdgeType, LinkType


class TestLinksToRelationshipExtractor:
    """Test suite for LinksToRelationshipExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = LinksToRelationshipExtractor(base_domain="london.edu")

    def test_extract_page_links_basic(self):
        """Test basic page link extraction."""
        page = {
            "id": "page-1",
            "url": "https://london.edu/page1",
            "links": [
                {"url": "https://london.edu/page2", "text": "Go to page 2"},
                {"url": "https://london.edu/page3", "text": "Go to page 3"},
            ],
        }

        all_pages = [
            page,
            {"id": "page-2", "url": "https://london.edu/page2"},
            {"id": "page-3", "url": "https://london.edu/page3"},
        ]

        edges = self.extractor.extract_page_links(page, all_pages)

        assert len(edges) == 2
        assert all(e.source_id == "page-1" for e in edges)
        assert all(e.relationship_type == EdgeType.LINKS_TO for e in edges)
        assert {e.target_id for e in edges} == {"page-2", "page-3"}

    def test_extract_page_links_skip_external(self):
        """Test that external links are skipped."""
        page = {
            "id": "page-1",
            "url": "https://london.edu/page1",
            "links": [
                {"url": "https://london.edu/page2", "text": "Internal"},
                {"url": "https://google.com", "text": "External"},
            ],
        }

        all_pages = [
            page,
            {"id": "page-2", "url": "https://london.edu/page2"},
        ]

        edges = self.extractor.extract_page_links(page, all_pages)

        assert len(edges) == 1
        assert edges[0].target_id == "page-2"

    def test_extract_page_links_skip_self_links(self):
        """Test that self-links are skipped."""
        page = {
            "id": "page-1",
            "url": "https://london.edu/page1",
            "links": [
                {"url": "https://london.edu/page1", "text": "Self link"},
                {"url": "https://london.edu/page2", "text": "Other page"},
            ],
        }

        all_pages = [
            page,
            {"id": "page-2", "url": "https://london.edu/page2"},
        ]

        edges = self.extractor.extract_page_links(page, all_pages)

        assert len(edges) == 1
        assert edges[0].target_id == "page-2"

    def test_extract_page_links_relative_urls(self):
        """Test handling of relative URLs."""
        page = {
            "id": "page-1",
            "url": "https://london.edu/page1",
            "links": [
                {"url": "/page2", "text": "Relative link"},
                {"url": "../page3", "text": "Parent relative"},
            ],
        }

        all_pages = [
            page,
            {"id": "page-2", "url": "https://london.edu/page2"},
            {"id": "page-3", "url": "https://london.edu/page3"},
        ]

        edges = self.extractor.extract_page_links(page, all_pages)

        assert len(edges) == 2

    def test_classify_link_type_navigation(self):
        """Test navigation link classification."""
        link = {"url": "/programmes/mba", "position": "header"}

        link_type = self.extractor.classify_link_type(link, "")

        assert link_type == LinkType.NAVIGATION

    def test_classify_link_type_reference(self):
        """Test reference link classification."""
        link = {"url": "/research/paper", "position": "content"}
        context = "As discussed in [1], the research shows..."

        link_type = self.extractor.classify_link_type(link, context)

        assert link_type == LinkType.REFERENCE

    def test_classify_link_type_citation(self):
        """Test citation link classification."""
        link = {"url": "/paper", "class": "citation", "position": "content"}

        link_type = self.extractor.classify_link_type(link, "")

        assert link_type == LinkType.CITATION

    def test_calculate_link_strength_header(self):
        """Test link strength calculation for header links."""
        link = {"text": "Important Navigation Link", "position": "header"}
        page = {"id": "page-1"}

        strength = self.extractor.calculate_link_strength(link, page, "header")

        assert strength >= 0.7  # Header links should be strong

    def test_calculate_link_strength_footer(self):
        """Test link strength calculation for footer links."""
        link = {"text": "Footer Link", "position": "footer"}
        page = {"id": "page-1"}

        strength = self.extractor.calculate_link_strength(link, page, "footer")

        assert strength <= 0.5  # Footer links should be weaker

    def test_calculate_link_strength_with_context(self):
        """Test link strength increases with context."""
        link1 = {"text": "Link", "position": "content"}
        link2 = {
            "text": "Link",
            "position": "content",
            "context": "This is a detailed context explaining the importance of this link.",
        }
        page = {"id": "page-1"}

        strength1 = self.extractor.calculate_link_strength(link1, page, "content")
        strength2 = self.extractor.calculate_link_strength(link2, page, "content")

        assert strength2 > strength1

    def test_build_link_graph(self):
        """Test building complete link graph."""
        pages = [
            {
                "id": "page-1",
                "url": "https://london.edu/page1",
                "links": [
                    {"url": "https://london.edu/page2", "text": "Link to 2"},
                ],
            },
            {
                "id": "page-2",
                "url": "https://london.edu/page2",
                "links": [
                    {"url": "https://london.edu/page3", "text": "Link to 3"},
                ],
            },
            {
                "id": "page-3",
                "url": "https://london.edu/page3",
                "links": [],
            },
        ]

        edges = self.extractor.build_link_graph(pages)

        assert len(edges) == 2
        assert any(e.source_id == "page-1" and e.target_id == "page-2" for e in edges)
        assert any(e.source_id == "page-2" and e.target_id == "page-3" for e in edges)

    def test_is_internal_link(self):
        """Test internal link detection."""
        assert self.extractor._is_internal_link("https://london.edu/page") is True
        assert self.extractor._is_internal_link("https://www.london.edu/page") is True
        assert self.extractor._is_internal_link("/relative/path") is True
        assert self.extractor._is_internal_link("https://google.com") is False
        assert self.extractor._is_internal_link("https://example.com") is False

    def test_get_inbound_links(self):
        """Test getting inbound links for a page."""
        pages = [
            {
                "id": "page-1",
                "url": "https://london.edu/page1",
                "links": [
                    {"url": "https://london.edu/page3", "text": "Link to 3"},
                ],
            },
            {
                "id": "page-2",
                "url": "https://london.edu/page2",
                "links": [
                    {"url": "https://london.edu/page3", "text": "Link to 3"},
                ],
            },
            {
                "id": "page-3",
                "url": "https://london.edu/page3",
                "links": [],
            },
        ]

        self.extractor.build_link_graph(pages)
        inbound = self.extractor.get_inbound_links("page-3")

        assert set(inbound) == {"page-1", "page-2"}

    def test_get_outbound_links(self):
        """Test getting outbound links for a page."""
        pages = [
            {
                "id": "page-1",
                "url": "https://london.edu/page1",
                "links": [
                    {"url": "https://london.edu/page2", "text": "Link to 2"},
                    {"url": "https://london.edu/page3", "text": "Link to 3"},
                ],
            },
            {
                "id": "page-2",
                "url": "https://london.edu/page2",
                "links": [],
            },
            {
                "id": "page-3",
                "url": "https://london.edu/page3",
                "links": [],
            },
        ]

        self.extractor.build_link_graph(pages)
        outbound = self.extractor.get_outbound_links("page-1")

        assert set(outbound) == {"page-2", "page-3"}

    def test_get_statistics(self):
        """Test statistics generation."""
        pages = [
            {
                "id": "page-1",
                "url": "https://london.edu/page1",
                "links": [
                    {"url": "https://london.edu/page2", "text": "Link", "position": "header"},
                ],
            },
            {
                "id": "page-2",
                "url": "https://london.edu/page2",
                "links": [],
            },
        ]

        self.extractor.build_link_graph(pages)
        stats = self.extractor.get_statistics()

        assert stats["total_links_to_edges"] == 1
        assert stats["total_source_pages"] == 1
        assert stats["total_target_pages"] == 1
        assert "link_type_distribution" in stats
        assert "avg_link_strength" in stats

    def test_reset(self):
        """Test extractor reset."""
        pages = [
            {
                "id": "page-1",
                "url": "https://london.edu/page1",
                "links": [
                    {"url": "https://london.edu/page2", "text": "Link"},
                ],
            },
            {
                "id": "page-2",
                "url": "https://london.edu/page2",
                "links": [],
            },
        ]

        self.extractor.build_link_graph(pages)
        assert len(self.extractor.extracted_edges) > 0

        self.extractor.reset()
        assert len(self.extractor.extracted_edges) == 0
        assert len(self.extractor.link_graph) == 0
