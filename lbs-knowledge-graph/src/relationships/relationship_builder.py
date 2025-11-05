"""
RelationshipBuilder - Master coordinator for all relationship extractors.

Coordinates:
- ContainsRelationshipExtractor
- LinksToRelationshipExtractor
- Batch processing
- Validation and deduplication
- Integration with MGraph
"""

import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

try:
    from mgraph import MGraph, Node
except ImportError:
    # Fallback for testing without mgraph installed
    MGraph = Any
    Node = Any

from .contains_extractor import ContainsRelationshipExtractor
from .links_to_extractor import LinksToRelationshipExtractor
from .models import (
    Edge,
    EdgeType,
    ValidationReport,
    GraphStatistics,
)

logger = logging.getLogger(__name__)


class RelationshipBuilder:
    """
    Master class that coordinates all relationship extractors.

    Responsibilities:
    - Coordinate multiple relationship extractors
    - Batch processing for performance
    - Relationship validation and deduplication
    - Integration with GraphBuilder and MGraph
    """

    def __init__(self, base_domain: str = "london.edu") -> None:
        """
        Initialize the relationship builder.

        Args:
            base_domain: Base domain for link extraction
        """
        self.contains_extractor = ContainsRelationshipExtractor()
        self.links_to_extractor = LinksToRelationshipExtractor(base_domain=base_domain)

        self.all_edges: Set[Edge] = set()
        self.edges_by_type: Dict[EdgeType, List[Edge]] = {}
        self.batch_size = 1000  # Process in batches for performance

    def build_all_relationships(
        self,
        pages: List[Dict[str, Any]],
        sections: List[Dict[str, Any]],
        content_items: List[Dict[str, Any]],
    ) -> List[Edge]:
        """
        Build all relationships for the knowledge graph.

        Args:
            pages: List of page objects
            sections: List of section objects
            content_items: List of content item objects

        Returns:
            List of all extracted edges
        """
        logger.info("Starting relationship extraction...")
        all_edges: List[Edge] = []

        # Step 1: Extract Page → Section CONTAINS relationships
        logger.info("Extracting Page → Section relationships...")
        page_section_map: Dict[str, List[Dict[str, Any]]] = {}
        for section in sections:
            page_id = section.get("page_id", section.get("pageId"))
            if page_id:
                if page_id not in page_section_map:
                    page_section_map[page_id] = []
                page_section_map[page_id].append(section)

        for page_id, page_sections in page_section_map.items():
            edges = self.contains_extractor.extract_page_sections(page_id, page_sections)
            all_edges.extend(edges)

        # Step 2: Extract Section → ContentItem CONTAINS relationships
        logger.info("Extracting Section → ContentItem relationships...")
        section_content_map: Dict[str, List[Dict[str, Any]]] = {}
        for item in content_items:
            section_ids = item.get("section_ids", item.get("sectionIds", []))
            if isinstance(section_ids, str):
                section_ids = [section_ids]

            for section_id in section_ids:
                if section_id not in section_content_map:
                    section_content_map[section_id] = []
                section_content_map[section_id].append(item)

        for section_id, items in section_content_map.items():
            edges = self.contains_extractor.extract_section_content(section_id, items)
            all_edges.extend(edges)

        # Step 3: Extract nested Section → Section relationships
        logger.info("Extracting nested Section → Section relationships...")
        nested_sections = [s for s in sections if s.get("parent_id") or s.get("parentId")]
        if nested_sections:
            edges = self.contains_extractor.extract_nested_sections(nested_sections)
            all_edges.extend(edges)

        # Step 4: Extract Page → Page LINKS_TO relationships
        logger.info("Extracting Page → Page link relationships...")
        link_edges = self.links_to_extractor.build_link_graph(pages)
        all_edges.extend(link_edges)

        # Step 5: Deduplicate edges
        logger.info("Deduplicating edges...")
        unique_edges = list(set(all_edges))
        logger.info(f"Removed {len(all_edges) - len(unique_edges)} duplicate edges")

        # Step 6: Group edges by type
        self._group_edges_by_type(unique_edges)

        # Store all edges
        self.all_edges = set(unique_edges)

        logger.info(f"Total relationships extracted: {len(unique_edges)}")
        return unique_edges

    def add_to_graph(self, graph: MGraph, edges: List[Edge]) -> None:
        """
        Add edges to an MGraph instance.

        Args:
            graph: MGraph instance
            edges: List of edges to add
        """
        logger.info(f"Adding {len(edges)} edges to graph...")

        # Process in batches for performance
        for i in range(0, len(edges), self.batch_size):
            batch = edges[i : i + self.batch_size]

            for edge in batch:
                try:
                    # Add edge to graph
                    # MGraph syntax: graph.add_edge(source_id, target_id, relationship_type, properties)
                    graph.add_edge(
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        edge_type=edge.relationship_type.value,
                        properties=edge.properties,
                    )
                except Exception as e:
                    logger.error(
                        f"Error adding edge {edge.source_id} -> {edge.target_id}: {e}"
                    )

            logger.info(f"Processed batch {i // self.batch_size + 1}")

        logger.info("Successfully added all edges to graph")

    def validate_relationships(
        self, graph: Optional[MGraph] = None, edges: Optional[List[Edge]] = None
    ) -> ValidationReport:
        """
        Validate all relationships in the graph.

        Args:
            graph: Optional MGraph instance to validate against
            edges: Optional list of edges to validate (uses all_edges if not provided)

        Returns:
            ValidationReport with validation results
        """
        logger.info("Validating relationships...")

        if edges is None:
            edges = list(self.all_edges)

        # Validate CONTAINS hierarchy
        contains_edges = [e for e in edges if e.relationship_type == EdgeType.CONTAINS]
        contains_report = self.contains_extractor.validate_hierarchy(contains_edges)

        # Create combined report
        report = ValidationReport(
            is_valid=contains_report.is_valid,
            total_edges=len(edges),
            issues=contains_report.issues,
            errors=contains_report.errors,
            warnings=contains_report.warnings,
            info=contains_report.info,
        )

        # Additional validations
        if graph:
            # Validate that all referenced nodes exist in graph
            all_node_ids = set()
            try:
                all_node_ids = {node.id for node in graph.get_all_nodes()}
            except Exception as e:
                logger.warning(f"Could not retrieve nodes from graph: {e}")

            if all_node_ids:
                for edge in edges:
                    if edge.source_id not in all_node_ids:
                        report.add_issue(
                            severity="error",
                            issue_type="orphaned_source",
                            message=f"Source node {edge.source_id} not found in graph",
                            edge=edge,
                        )

                    if edge.target_id not in all_node_ids:
                        report.add_issue(
                            severity="error",
                            issue_type="orphaned_target",
                            message=f"Target node {edge.target_id} not found in graph",
                            edge=edge,
                        )

        logger.info(
            f"Validation complete: {report.errors} errors, "
            f"{report.warnings} warnings, {report.info} info"
        )
        return report

    def get_statistics(self) -> GraphStatistics:
        """
        Get comprehensive statistics about relationships.

        Returns:
            GraphStatistics object with detailed metrics
        """
        # Calculate statistics from extractors
        contains_stats = self.contains_extractor.get_statistics()
        links_stats = self.links_to_extractor.get_statistics()

        # Count edges by type
        edges_by_type = {}
        for edge_type, edges in self.edges_by_type.items():
            edges_by_type[edge_type.value] = len(edges)

        # Calculate average edges per node (approximation)
        total_edges = len(self.all_edges)
        unique_nodes = set()
        for edge in self.all_edges:
            unique_nodes.add(edge.source_id)
            unique_nodes.add(edge.target_id)

        avg_edges = total_edges / len(unique_nodes) if unique_nodes else 0.0

        statistics = GraphStatistics(
            total_edges=total_edges,
            edges_by_type=edges_by_type,
            avg_edges_per_node=round(avg_edges, 2),
            timestamp=datetime.utcnow(),
        )

        # Add extractor-specific stats as metadata
        logger.info(f"CONTAINS stats: {contains_stats}")
        logger.info(f"LINKS_TO stats: {links_stats}")

        return statistics

    def export_edges(self, format: str = "json") -> Any:
        """
        Export edges in specified format.

        Args:
            format: Export format (json, csv, cypher)

        Returns:
            Exported data in specified format
        """
        if format == "json":
            return [
                {
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "type": edge.relationship_type.value,
                    "properties": edge.properties,
                    "created_at": edge.created_at.isoformat(),
                }
                for edge in self.all_edges
            ]
        elif format == "cypher":
            # Generate Cypher CREATE statements
            statements = []
            for edge in self.all_edges:
                props = ", ".join(
                    f"{k}: {repr(v)}" for k, v in edge.properties.items()
                )
                stmt = (
                    f"MATCH (a {{id: '{edge.source_id}'}}), (b {{id: '{edge.target_id}'}}) "
                    f"CREATE (a)-[:{edge.relationship_type.value} {{{props}}}]->(b)"
                )
                statements.append(stmt)
            return statements
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _group_edges_by_type(self, edges: List[Edge]) -> None:
        """
        Group edges by their relationship type.

        Args:
            edges: List of edges to group
        """
        self.edges_by_type.clear()

        for edge in edges:
            if edge.relationship_type not in self.edges_by_type:
                self.edges_by_type[edge.relationship_type] = []
            self.edges_by_type[edge.relationship_type].append(edge)

    def reset(self) -> None:
        """Reset all extractors and clear state."""
        self.contains_extractor.reset()
        self.links_to_extractor.reset()
        self.all_edges.clear()
        self.edges_by_type.clear()
        logger.info("RelationshipBuilder reset complete")
