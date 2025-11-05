"""
Unit tests for ContainsRelationshipExtractor.
"""

import pytest
from datetime import datetime
from src.relationships.contains_extractor import ContainsRelationshipExtractor
from src.relationships.models import Edge, EdgeType


class TestContainsRelationshipExtractor:
    """Test suite for ContainsRelationshipExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = ContainsRelationshipExtractor()

    def test_extract_page_sections_basic(self):
        """Test basic page-to-section extraction."""
        page_id = "page-123"
        sections = [
            {"id": "section-1", "order": 0},
            {"id": "section-2", "order": 1},
            {"id": "section-3", "order": 2},
        ]

        edges = self.extractor.extract_page_sections(page_id, sections)

        assert len(edges) == 3
        assert all(e.source_id == page_id for e in edges)
        assert all(e.relationship_type == EdgeType.CONTAINS for e in edges)
        assert [e.target_id for e in edges] == ["section-1", "section-2", "section-3"]

    def test_extract_page_sections_with_properties(self):
        """Test section extraction with required property."""
        page_id = "page-456"
        sections = [
            {"id": "section-1", "order": 0, "required": True},
            {"id": "section-2", "order": 1, "required": False},
        ]

        edges = self.extractor.extract_page_sections(page_id, sections)

        assert len(edges) == 2
        assert edges[0].properties["required"] is True
        assert edges[1].properties["required"] is False
        assert edges[0].properties["order"] == 0
        assert edges[1].properties["order"] == 1

    def test_extract_page_sections_skip_invalid(self):
        """Test that sections without IDs are skipped."""
        page_id = "page-789"
        sections = [
            {"id": "section-1", "order": 0},
            {"order": 1},  # Missing ID
            {"id": "section-3", "order": 2},
        ]

        edges = self.extractor.extract_page_sections(page_id, sections)

        assert len(edges) == 2
        assert [e.target_id for e in edges] == ["section-1", "section-3"]

    def test_extract_section_content_basic(self):
        """Test basic section-to-content extraction."""
        section_id = "section-abc"
        content_items = [
            {"id": "content-1"},
            {"id": "content-2"},
            {"id": "content-3"},
        ]

        edges = self.extractor.extract_section_content(section_id, content_items)

        assert len(edges) == 3
        assert all(e.source_id == section_id for e in edges)
        assert all(e.relationship_type == EdgeType.CONTAINS for e in edges)

    def test_extract_section_content_with_order(self):
        """Test content extraction with explicit order."""
        section_id = "section-def"
        content_items = [
            {"id": "content-1", "order": 5},
            {"id": "content-2", "order": 10},
        ]

        edges = self.extractor.extract_section_content(section_id, content_items)

        assert edges[0].properties["order"] == 5
        assert edges[1].properties["order"] == 10

    def test_extract_nested_sections(self):
        """Test nested section extraction."""
        sections = [
            {"id": "section-1", "parent_id": "section-0", "order": 0},
            {"id": "section-2", "parent_id": "section-0", "order": 1},
            {"id": "section-3", "parent_id": "section-1", "order": 0},
        ]

        edges = self.extractor.extract_nested_sections(sections)

        assert len(edges) == 3
        assert edges[0].source_id == "section-0"
        assert edges[0].target_id == "section-1"
        assert edges[2].source_id == "section-1"
        assert edges[2].target_id == "section-3"

    def test_validate_hierarchy_no_cycles(self):
        """Test hierarchy validation passes with no cycles."""
        edges = [
            Edge(
                source_id="page-1",
                target_id="section-1",
                relationship_type=EdgeType.CONTAINS,
                properties={"order": 0},
            ),
            Edge(
                source_id="section-1",
                target_id="content-1",
                relationship_type=EdgeType.CONTAINS,
                properties={"order": 0},
            ),
        ]

        report = self.extractor.validate_hierarchy(edges)

        assert report.is_valid is True
        assert report.errors == 0

    def test_validate_hierarchy_detects_cycles(self):
        """Test hierarchy validation detects circular dependencies."""
        # Create circular dependency
        self.extractor.parent_child_map = {
            "section-1": ["section-2"],
            "section-2": ["section-3"],
            "section-3": ["section-1"],  # Cycle!
        }

        edges = [
            Edge(
                source_id="section-1",
                target_id="section-2",
                relationship_type=EdgeType.CONTAINS,
                properties={"order": 0},
            ),
            Edge(
                source_id="section-2",
                target_id="section-3",
                relationship_type=EdgeType.CONTAINS,
                properties={"order": 0},
            ),
            Edge(
                source_id="section-3",
                target_id="section-1",
                relationship_type=EdgeType.CONTAINS,
                properties={"order": 0},
            ),
        ]

        report = self.extractor.validate_hierarchy(edges)

        assert report.is_valid is False
        assert report.errors > 0
        assert any("circular" in issue.message.lower() for issue in report.issues)

    def test_validate_hierarchy_detects_order_gaps(self):
        """Test hierarchy validation detects gaps in order sequence."""
        edges = [
            Edge(
                source_id="page-1",
                target_id="section-1",
                relationship_type=EdgeType.CONTAINS,
                properties={"order": 0},
            ),
            Edge(
                source_id="page-1",
                target_id="section-2",
                relationship_type=EdgeType.CONTAINS,
                properties={"order": 5},  # Gap from 0 to 5
            ),
        ]

        report = self.extractor.validate_hierarchy(edges)

        assert report.warnings > 0
        assert any("gap" in issue.message.lower() for issue in report.issues)

    def test_validate_hierarchy_detects_duplicate_orders(self):
        """Test hierarchy validation detects duplicate order values."""
        edges = [
            Edge(
                source_id="page-1",
                target_id="section-1",
                relationship_type=EdgeType.CONTAINS,
                properties={"order": 0},
            ),
            Edge(
                source_id="page-1",
                target_id="section-2",
                relationship_type=EdgeType.CONTAINS,
                properties={"order": 0},  # Duplicate!
            ),
        ]

        report = self.extractor.validate_hierarchy(edges)

        assert report.is_valid is False
        assert report.errors > 0
        assert any("duplicate" in issue.message.lower() for issue in report.issues)

    def test_get_statistics(self):
        """Test statistics generation."""
        page_id = "page-1"
        sections = [
            {"id": "section-1", "order": 0},
            {"id": "section-2", "order": 1},
        ]

        self.extractor.extract_page_sections(page_id, sections)
        stats = self.extractor.get_statistics()

        assert stats["total_contains_edges"] == 2
        assert stats["total_parents"] == 1
        assert stats["total_children"] == 2
        assert stats["avg_children_per_parent"] == 2.0

    def test_reset(self):
        """Test extractor reset."""
        page_id = "page-1"
        sections = [{"id": "section-1", "order": 0}]

        self.extractor.extract_page_sections(page_id, sections)
        assert len(self.extractor.extracted_edges) > 0

        self.extractor.reset()
        assert len(self.extractor.extracted_edges) == 0
        assert len(self.extractor.parent_child_map) == 0

    def test_edge_deduplication(self):
        """Test that duplicate edges are handled properly."""
        page_id = "page-1"
        sections = [{"id": "section-1", "order": 0}]

        # Extract same relationships twice
        edges1 = self.extractor.extract_page_sections(page_id, sections)
        edges2 = self.extractor.extract_page_sections(page_id, sections)

        # Edges should be equal
        assert edges1[0] == edges2[0]

        # Sets should deduplicate
        combined = set(edges1 + edges2)
        assert len(combined) == 1
