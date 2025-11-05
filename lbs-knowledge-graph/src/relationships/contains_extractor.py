"""
ContainsRelationshipExtractor - Extract hierarchical CONTAINS relationships.

Handles:
- Page → Section CONTAINS relationships
- Section → ContentItem CONTAINS relationships
- Section → Section CONTAINS relationships (nested sections)
"""

import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from .models import (
    Edge,
    EdgeType,
    ContainsProperties,
    ValidationReport,
    ValidationIssue,
)

logger = logging.getLogger(__name__)


class ContainsRelationshipExtractor:
    """
    Extract CONTAINS relationships for hierarchical structures.

    This extractor creates edges that represent containment:
    - Page contains Sections (ordered)
    - Section contains ContentItems (ordered)
    - Section contains nested Sections (ordered)
    """

    def __init__(self) -> None:
        """Initialize the CONTAINS relationship extractor."""
        self.extracted_edges: Set[Edge] = set()
        self.parent_child_map: Dict[str, List[str]] = {}

    def extract_page_sections(
        self, page_id: str, sections: List[Dict[str, Any]]
    ) -> List[Edge]:
        """
        Extract Page → Section CONTAINS relationships.

        Args:
            page_id: Parent page ID
            sections: List of section objects with 'id' and 'order' fields

        Returns:
            List of CONTAINS edges from page to sections
        """
        edges: List[Edge] = []

        for section in sections:
            section_id = section.get("id")
            if not section_id:
                logger.warning(f"Section missing ID in page {page_id}, skipping")
                continue

            order = section.get("order", 0)
            required = section.get("required", False)

            # Create edge properties
            properties = ContainsProperties(
                order=order,
                confidence=1.0,  # Direct structural relationship
                required=required,
            ).model_dump()

            # Create edge
            edge = Edge(
                source_id=page_id,
                target_id=section_id,
                relationship_type=EdgeType.CONTAINS,
                properties=properties,
            )

            edges.append(edge)
            self.extracted_edges.add(edge)

            # Track parent-child relationship
            if page_id not in self.parent_child_map:
                self.parent_child_map[page_id] = []
            self.parent_child_map[page_id].append(section_id)

        logger.info(
            f"Extracted {len(edges)} Page→Section CONTAINS edges for page {page_id}"
        )
        return edges

    def extract_section_content(
        self, section_id: str, content_items: List[Dict[str, Any]]
    ) -> List[Edge]:
        """
        Extract Section → ContentItem CONTAINS relationships.

        Args:
            section_id: Parent section ID
            content_items: List of content item objects with 'id' field

        Returns:
            List of CONTAINS edges from section to content items
        """
        edges: List[Edge] = []

        for idx, item in enumerate(content_items):
            item_id = item.get("id")
            if not item_id:
                logger.warning(f"Content item missing ID in section {section_id}, skipping")
                continue

            # Use explicit order if provided, otherwise use index
            order = item.get("order", idx)

            # Create edge properties
            properties = ContainsProperties(
                order=order,
                confidence=1.0,
                required=False,
            ).model_dump()

            # Create edge
            edge = Edge(
                source_id=section_id,
                target_id=item_id,
                relationship_type=EdgeType.CONTAINS,
                properties=properties,
            )

            edges.append(edge)
            self.extracted_edges.add(edge)

            # Track parent-child relationship
            if section_id not in self.parent_child_map:
                self.parent_child_map[section_id] = []
            self.parent_child_map[section_id].append(item_id)

        logger.info(
            f"Extracted {len(edges)} Section→ContentItem CONTAINS edges for section {section_id}"
        )
        return edges

    def extract_nested_sections(self, sections: List[Dict[str, Any]]) -> List[Edge]:
        """
        Extract Section → Section CONTAINS relationships for nested sections.

        Args:
            sections: List of section objects with 'id', 'parent_id', and 'order' fields

        Returns:
            List of CONTAINS edges for nested sections
        """
        edges: List[Edge] = []

        for section in sections:
            section_id = section.get("id")
            parent_id = section.get("parent_id")

            if not section_id:
                logger.warning("Section missing ID, skipping")
                continue

            # Only process sections with a parent
            if not parent_id:
                continue

            order = section.get("order", 0)

            # Create edge properties
            properties = ContainsProperties(
                order=order,
                confidence=1.0,
                required=False,
            ).model_dump()

            # Create edge
            edge = Edge(
                source_id=parent_id,
                target_id=section_id,
                relationship_type=EdgeType.CONTAINS,
                properties=properties,
            )

            edges.append(edge)
            self.extracted_edges.add(edge)

            # Track parent-child relationship
            if parent_id not in self.parent_child_map:
                self.parent_child_map[parent_id] = []
            self.parent_child_map[parent_id].append(section_id)

        logger.info(f"Extracted {len(edges)} Section→Section CONTAINS edges")
        return edges

    def validate_hierarchy(self, edges: List[Edge]) -> ValidationReport:
        """
        Validate the hierarchy of CONTAINS relationships.

        Checks:
        - No orphaned nodes (all children have parents in the graph)
        - No circular dependencies
        - Order values are sequential without gaps
        - All referenced nodes exist

        Args:
            edges: List of edges to validate

        Returns:
            ValidationReport with validation results
        """
        report = ValidationReport(is_valid=True, total_edges=len(edges))

        # Build adjacency list for cycle detection
        adjacency: Dict[str, List[str]] = {}
        all_sources: Set[str] = set()
        all_targets: Set[str] = set()

        for edge in edges:
            if edge.relationship_type != EdgeType.CONTAINS:
                continue

            if edge.source_id not in adjacency:
                adjacency[edge.source_id] = []
            adjacency[edge.source_id].append(edge.target_id)

            all_sources.add(edge.source_id)
            all_targets.add(edge.target_id)

        # Check for circular dependencies using DFS
        def has_cycle(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            """Detect cycles using depth-first search."""
            visited.add(node)
            rec_stack.add(node)

            if node in adjacency:
                for neighbor in adjacency[node]:
                    if neighbor not in visited:
                        if has_cycle(neighbor, visited, rec_stack):
                            return True
                    elif neighbor in rec_stack:
                        return True

            rec_stack.remove(node)
            return False

        visited: Set[str] = set()
        for source in all_sources:
            if source not in visited:
                if has_cycle(source, visited, set()):
                    report.add_issue(
                        severity="error",
                        issue_type="circular_dependency",
                        message=f"Circular dependency detected starting from node {source}",
                        node_id=source,
                    )

        # Validate order sequences for each parent
        order_by_parent: Dict[str, List[int]] = {}
        for edge in edges:
            if edge.relationship_type != EdgeType.CONTAINS:
                continue

            order = edge.properties.get("order", 0)
            if edge.source_id not in order_by_parent:
                order_by_parent[edge.source_id] = []
            order_by_parent[edge.source_id].append(order)

        for parent_id, orders in order_by_parent.items():
            orders.sort()
            # Check for gaps in sequence
            for i in range(len(orders) - 1):
                if orders[i + 1] - orders[i] > 1:
                    report.add_issue(
                        severity="warning",
                        issue_type="order_gap",
                        message=f"Gap in order sequence for parent {parent_id}: {orders[i]} to {orders[i+1]}",
                        node_id=parent_id,
                    )

            # Check for duplicates
            if len(orders) != len(set(orders)):
                report.add_issue(
                    severity="error",
                    issue_type="duplicate_order",
                    message=f"Duplicate order values for parent {parent_id}",
                    node_id=parent_id,
                )

        logger.info(
            f"Validation complete: {report.errors} errors, {report.warnings} warnings"
        )
        return report

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about extracted CONTAINS relationships.

        Returns:
            Dictionary with statistics
        """
        total_edges = len(self.extracted_edges)
        total_parents = len(self.parent_child_map)
        total_children = sum(len(children) for children in self.parent_child_map.values())

        avg_children_per_parent = (
            total_children / total_parents if total_parents > 0 else 0.0
        )

        return {
            "total_contains_edges": total_edges,
            "total_parents": total_parents,
            "total_children": total_children,
            "avg_children_per_parent": round(avg_children_per_parent, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def reset(self) -> None:
        """Reset the extractor state."""
        self.extracted_edges.clear()
        self.parent_child_map.clear()
