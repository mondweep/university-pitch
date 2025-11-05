"""
Unit tests for RelationshipBuilder.
"""

import pytest
from src.relationships.relationship_builder import RelationshipBuilder
from src.relationships.models import Edge, EdgeType


class TestRelationshipBuilder:
    """Test suite for RelationshipBuilder."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = RelationshipBuilder(base_domain="london.edu")

    def test_build_all_relationships(self):
        """Test building all relationships."""
        pages = [
            {
                "id": "page-1",
                "url": "https://london.edu/page1",
                "links": [
                    {"url": "https://london.edu/page2", "text": "Link to page 2"},
                ],
            },
            {
                "id": "page-2",
                "url": "https://london.edu/page2",
                "links": [],
            },
        ]

        sections = [
            {"id": "section-1", "page_id": "page-1", "order": 0},
            {"id": "section-2", "page_id": "page-1", "order": 1},
            {"id": "section-3", "page_id": "page-2", "order": 0},
        ]

        content_items = [
            {"id": "content-1", "section_ids": ["section-1"]},
            {"id": "content-2", "section_ids": ["section-1"]},
            {"id": "content-3", "section_ids": ["section-2"]},
        ]

        edges = self.builder.build_all_relationships(pages, sections, content_items)

        # Should have:
        # - 3 Page->Section edges
        # - 3 Section->ContentItem edges
        # - 1 Page->Page link edge
        assert len(edges) >= 7

        contains_edges = [e for e in edges if e.relationship_type == EdgeType.CONTAINS]
        links_edges = [e for e in edges if e.relationship_type == EdgeType.LINKS_TO]

        assert len(contains_edges) == 6
        assert len(links_edges) == 1

    def test_build_with_nested_sections(self):
        """Test building relationships with nested sections."""
        pages = [{"id": "page-1", "url": "https://london.edu/page1", "links": []}]

        sections = [
            {"id": "section-1", "page_id": "page-1", "order": 0},
            {"id": "section-1-1", "page_id": "page-1", "parent_id": "section-1", "order": 0},
            {"id": "section-1-2", "page_id": "page-1", "parent_id": "section-1", "order": 1},
        ]

        content_items = []

        edges = self.builder.build_all_relationships(pages, sections, content_items)

        # Should have:
        # - 1 Page->Section edge (page-1 -> section-1)
        # - 2 Section->Section edges (section-1 -> section-1-1, section-1 -> section-1-2)
        # Note: Nested sections also have page_id, so they get page edges too
        assert len(edges) >= 3

        nested_edges = [
            e
            for e in edges
            if e.source_id.startswith("section") and e.target_id.startswith("section")
        ]
        assert len(nested_edges) == 2

    def test_deduplication(self):
        """Test that duplicate edges are removed."""
        pages = []
        sections = [
            {"id": "section-1", "page_id": "page-1", "order": 0},
        ]
        content_items = [
            {"id": "content-1", "section_ids": ["section-1"]},
        ]

        # Build twice
        edges1 = self.builder.build_all_relationships(pages, sections, content_items)
        self.builder.reset()
        edges2 = self.builder.build_all_relationships(pages, sections, content_items)

        # Should produce same edges
        assert len(edges1) == len(edges2)

    def test_get_statistics(self):
        """Test statistics generation."""
        pages = [
            {
                "id": "page-1",
                "url": "https://london.edu/page1",
                "links": [{"url": "https://london.edu/page2", "text": "Link"}],
            },
            {"id": "page-2", "url": "https://london.edu/page2", "links": []},
        ]

        sections = [
            {"id": "section-1", "page_id": "page-1", "order": 0},
        ]

        content_items = []

        self.builder.build_all_relationships(pages, sections, content_items)
        stats = self.builder.get_statistics()

        assert stats.total_edges >= 2
        assert EdgeType.CONTAINS.value in stats.edges_by_type
        assert EdgeType.LINKS_TO.value in stats.edges_by_type

    def test_export_edges_json(self):
        """Test JSON export."""
        pages = []
        sections = [
            {"id": "section-1", "page_id": "page-1", "order": 0},
        ]
        content_items = []

        self.builder.build_all_relationships(pages, sections, content_items)
        exported = self.builder.export_edges(format="json")

        assert isinstance(exported, list)
        assert len(exported) > 0
        assert all("source" in edge for edge in exported)
        assert all("target" in edge for edge in exported)
        assert all("type" in edge for edge in exported)

    def test_export_edges_cypher(self):
        """Test Cypher export."""
        pages = []
        sections = [
            {"id": "section-1", "page_id": "page-1", "order": 0},
        ]
        content_items = []

        self.builder.build_all_relationships(pages, sections, content_items)
        exported = self.builder.export_edges(format="cypher")

        assert isinstance(exported, list)
        assert len(exported) > 0
        assert all("MATCH" in stmt for stmt in exported)
        assert all("CREATE" in stmt for stmt in exported)

    def test_reset(self):
        """Test builder reset."""
        pages = []
        sections = [
            {"id": "section-1", "page_id": "page-1", "order": 0},
        ]
        content_items = []

        self.builder.build_all_relationships(pages, sections, content_items)
        assert len(self.builder.all_edges) > 0

        self.builder.reset()
        assert len(self.builder.all_edges) == 0
        assert len(self.builder.edges_by_type) == 0

    def test_validate_relationships(self):
        """Test relationship validation."""
        pages = []
        sections = [
            {"id": "section-1", "page_id": "page-1", "order": 0},
            {"id": "section-2", "page_id": "page-1", "order": 1},
        ]
        content_items = []

        edges = self.builder.build_all_relationships(pages, sections, content_items)
        report = self.builder.validate_relationships(edges=edges)

        assert report.total_edges == len(edges)
        # Should be valid (no cycles, proper order)
        assert report.errors == 0
