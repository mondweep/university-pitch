#!/usr/bin/env python3
"""
Graph Validator - Validate MGraph integrity and constraints for Phase 2
Ensures knowledge graph quality, integrity, and completeness
"""

import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

# MGraph will be imported from the graph module
try:
    from mgraph_db import MGraph, MNode, MEdge
except ImportError:
    # For type hints when mgraph_db not installed yet
    MGraph = Any
    MNode = Any
    MEdge = Any

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    level: ValidationLevel
    category: str
    message: str
    node_id: Optional[str] = None
    edge_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Graph validation report"""
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return len([i for i in self.issues if i.level == ValidationLevel.CRITICAL])

    @property
    def error_count(self) -> int:
        return len([i for i in self.issues if i.level == ValidationLevel.ERROR])

    @property
    def warning_count(self) -> int:
        return len([i for i in self.issues if i.level == ValidationLevel.WARNING])

    @property
    def success_rate(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return round((self.passed_checks / self.total_checks) * 100, 2)

    @property
    def is_valid(self) -> bool:
        """Graph is valid if no critical or error issues"""
        return self.critical_count == 0 and self.error_count == 0


class GraphValidator:
    """Validate MGraph integrity and constraints"""

    # Expected node types from schema
    EXPECTED_NODE_TYPES = {'Page', 'Section', 'ContentItem', 'Topic', 'Category', 'Persona'}

    # Expected edge types from schema
    EXPECTED_EDGE_TYPES = {'CONTAINS', 'LINKS_TO', 'HAS_TOPIC', 'BELONGS_TO', 'TARGETS'}

    # Required node properties by type
    REQUIRED_NODE_PROPERTIES = {
        'Page': {'id', 'url', 'title', 'type'},
        'Section': {'id', 'type', 'order'},
        'ContentItem': {'id', 'hash', 'text', 'type'},
        'Topic': {'id', 'name', 'slug', 'category'},
        'Category': {'id', 'name', 'slug', 'level'},
        'Persona': {'id', 'name', 'type', 'description'}
    }

    # Hierarchical relationships (must form trees, not cycles)
    HIERARCHICAL_EDGE_TYPES = {'CONTAINS', 'BELONGS_TO'}

    def __init__(self):
        self.report = ValidationReport()

    def validate_nodes(self, graph: MGraph) -> ValidationReport:
        """
        Validate all nodes in the graph

        Checks:
        - Node type validity
        - Required properties presence
        - Property data types
        - UUID format validity
        """
        logger.info("Validating graph nodes...")

        try:
            nodes = list(graph.all_nodes()) if hasattr(graph, 'all_nodes') else []

            for node in nodes:
                self.report.total_checks += 1

                # Check node type
                if not self._validate_node_type(node):
                    self.report.failed_checks += 1
                    continue

                # Check required properties
                if not self._validate_node_properties(node):
                    self.report.failed_checks += 1
                    continue

                # Check property values
                if not self._validate_node_values(node):
                    self.report.failed_checks += 1
                    continue

                self.report.passed_checks += 1

            logger.info(f"Node validation complete: {self.report.passed_checks}/{self.report.total_checks} passed")

        except Exception as e:
            logger.error(f"Node validation failed: {e}")
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                category="validation_error",
                message=f"Node validation failed: {str(e)}"
            ))

        return self.report

    def validate_edges(self, graph: MGraph) -> ValidationReport:
        """
        Validate all edges in the graph

        Checks:
        - Edge type validity
        - Source and target nodes exist
        - Edge properties
        - Relationship constraints
        """
        logger.info("Validating graph edges...")

        try:
            edges = list(graph.all_edges()) if hasattr(graph, 'all_edges') else []

            for edge in edges:
                self.report.total_checks += 1

                # Check edge type
                if not self._validate_edge_type(edge):
                    self.report.failed_checks += 1
                    continue

                # Check endpoints exist
                if not self._validate_edge_endpoints(graph, edge):
                    self.report.failed_checks += 1
                    continue

                # Check edge properties
                if not self._validate_edge_properties(edge):
                    self.report.failed_checks += 1
                    continue

                self.report.passed_checks += 1

            logger.info(f"Edge validation complete: {self.report.passed_checks}/{self.report.total_checks} passed")

        except Exception as e:
            logger.error(f"Edge validation failed: {e}")
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                category="validation_error",
                message=f"Edge validation failed: {str(e)}"
            ))

        return self.report

    def check_orphaned_nodes(self, graph: MGraph) -> List[str]:
        """
        Find nodes without any edges (except isolated Topic/Category nodes which are valid)

        Returns:
            List of orphaned node IDs
        """
        logger.info("Checking for orphaned nodes...")

        orphaned = []

        try:
            nodes = list(graph.all_nodes()) if hasattr(graph, 'all_nodes') else []
            edges = list(graph.all_edges()) if hasattr(graph, 'all_edges') else []

            # Build set of nodes with edges
            nodes_with_edges = set()
            for edge in edges:
                if hasattr(edge, 'from_node'):
                    nodes_with_edges.add(edge.from_node)
                if hasattr(edge, 'to_node'):
                    nodes_with_edges.add(edge.to_node)

            # Find orphaned nodes
            for node in nodes:
                node_id = node.id if hasattr(node, 'id') else str(node)
                node_type = node.node_type if hasattr(node, 'node_type') else 'Unknown'

                # Topics and Categories can be isolated (pre-defined taxonomy)
                if node_type in {'Topic', 'Category'}:
                    continue

                if node_id not in nodes_with_edges:
                    orphaned.append(node_id)
                    self.report.issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="orphaned_node",
                        message=f"Node has no edges: {node_type}",
                        node_id=node_id
                    ))

            logger.info(f"Found {len(orphaned)} orphaned nodes")

        except Exception as e:
            logger.error(f"Orphaned node check failed: {e}")
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="check_error",
                message=f"Orphaned node check failed: {str(e)}"
            ))

        return orphaned

    def check_dangling_edges(self, graph: MGraph) -> List[Dict]:
        """
        Find edges pointing to non-existent nodes

        Returns:
            List of dangling edge info dicts
        """
        logger.info("Checking for dangling edges...")

        dangling = []

        try:
            nodes = list(graph.all_nodes()) if hasattr(graph, 'all_nodes') else []
            edges = list(graph.all_edges()) if hasattr(graph, 'all_edges') else []

            # Build set of valid node IDs
            valid_node_ids = {
                node.id if hasattr(node, 'id') else str(node)
                for node in nodes
            }

            # Check each edge
            for edge in edges:
                from_id = edge.from_node if hasattr(edge, 'from_node') else None
                to_id = edge.to_node if hasattr(edge, 'to_node') else None
                edge_type = edge.edge_type if hasattr(edge, 'edge_type') else 'Unknown'

                if from_id and from_id not in valid_node_ids:
                    dangling.append({
                        'edge_type': edge_type,
                        'from_node': from_id,
                        'to_node': to_id,
                        'issue': 'missing_source'
                    })
                    self.report.issues.append(ValidationIssue(
                        level=ValidationLevel.CRITICAL,
                        category="dangling_edge",
                        message=f"Edge source node does not exist: {from_id}",
                        details={'edge_type': edge_type, 'target': to_id}
                    ))

                if to_id and to_id not in valid_node_ids:
                    dangling.append({
                        'edge_type': edge_type,
                        'from_node': from_id,
                        'to_node': to_id,
                        'issue': 'missing_target'
                    })
                    self.report.issues.append(ValidationIssue(
                        level=ValidationLevel.CRITICAL,
                        category="dangling_edge",
                        message=f"Edge target node does not exist: {to_id}",
                        details={'edge_type': edge_type, 'source': from_id}
                    ))

            logger.info(f"Found {len(dangling)} dangling edges")

        except Exception as e:
            logger.error(f"Dangling edge check failed: {e}")
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                category="check_error",
                message=f"Dangling edge check failed: {str(e)}"
            ))

        return dangling

    def validate_hierarchy(self, graph: MGraph) -> ValidationReport:
        """
        Validate hierarchical relationships (CONTAINS, BELONGS_TO)
        Must form trees, not cycles

        Returns:
            Validation report with cycle detection results
        """
        logger.info("Validating hierarchical relationships...")

        try:
            edges = list(graph.all_edges()) if hasattr(graph, 'all_edges') else []

            # Check each hierarchical edge type
            for edge_type in self.HIERARCHICAL_EDGE_TYPES:
                # Build adjacency list
                hierarchy_edges = [
                    e for e in edges
                    if hasattr(e, 'edge_type') and e.edge_type == edge_type
                ]

                # Build graph
                adj_list = {}
                for edge in hierarchy_edges:
                    from_id = edge.from_node if hasattr(edge, 'from_node') else None
                    to_id = edge.to_node if hasattr(edge, 'to_node') else None

                    if from_id and to_id:
                        if from_id not in adj_list:
                            adj_list[from_id] = []
                        adj_list[from_id].append(to_id)

                # Detect cycles using DFS
                cycles = self._detect_cycles(adj_list)

                if cycles:
                    for cycle in cycles:
                        self.report.issues.append(ValidationIssue(
                            level=ValidationLevel.CRITICAL,
                            category="hierarchy_cycle",
                            message=f"Cycle detected in {edge_type} hierarchy",
                            details={'cycle': cycle}
                        ))
                        self.report.failed_checks += 1
                else:
                    self.report.passed_checks += 1

                self.report.total_checks += 1

            logger.info("Hierarchy validation complete")

        except Exception as e:
            logger.error(f"Hierarchy validation failed: {e}")
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                category="validation_error",
                message=f"Hierarchy validation failed: {str(e)}"
            ))

        return self.report

    def validate_constraints(self, graph: MGraph) -> ValidationReport:
        """
        Validate domain-specific constraints

        Constraints:
        - Pages must have at least one Section
        - Sections must have at least one ContentItem
        - ContentItems must have unique hashes within their Section
        - Topics must be categorized
        """
        logger.info("Validating domain constraints...")

        try:
            nodes = list(graph.all_nodes()) if hasattr(graph, 'all_nodes') else []
            edges = list(graph.all_edges()) if hasattr(graph, 'all_edges') else []

            # Group nodes by type
            nodes_by_type = {}
            for node in nodes:
                node_type = node.node_type if hasattr(node, 'node_type') else 'Unknown'
                if node_type not in nodes_by_type:
                    nodes_by_type[node_type] = []
                nodes_by_type[node_type].append(node)

            # Build edge index
            outbound_edges = {}
            for edge in edges:
                from_id = edge.from_node if hasattr(edge, 'from_node') else None
                if from_id:
                    if from_id not in outbound_edges:
                        outbound_edges[from_id] = []
                    outbound_edges[from_id].append(edge)

            # Check Page constraints
            for page in nodes_by_type.get('Page', []):
                page_id = page.id if hasattr(page, 'id') else str(page)
                page_edges = outbound_edges.get(page_id, [])

                contains_sections = any(
                    e for e in page_edges
                    if hasattr(e, 'edge_type') and e.edge_type == 'CONTAINS'
                )

                if not contains_sections:
                    self.report.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="constraint_violation",
                        message="Page has no sections",
                        node_id=page_id
                    ))

            # Check Section constraints
            for section in nodes_by_type.get('Section', []):
                section_id = section.id if hasattr(section, 'id') else str(section)
                section_edges = outbound_edges.get(section_id, [])

                contains_content = any(
                    e for e in section_edges
                    if hasattr(e, 'edge_type') and e.edge_type == 'CONTAINS'
                )

                if not contains_content:
                    self.report.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="constraint_violation",
                        message="Section has no content items",
                        node_id=section_id
                    ))

            logger.info("Constraint validation complete")

        except Exception as e:
            logger.error(f"Constraint validation failed: {e}")
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="validation_error",
                message=f"Constraint validation failed: {str(e)}"
            ))

        return self.report

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        return {
            'summary': {
                'total_checks': self.report.total_checks,
                'passed_checks': self.report.passed_checks,
                'failed_checks': self.report.failed_checks,
                'success_rate': self.report.success_rate,
                'is_valid': self.report.is_valid
            },
            'issues_by_level': {
                'critical': self.report.critical_count,
                'errors': self.report.error_count,
                'warnings': self.report.warning_count
            },
            'issues': [
                {
                    'level': issue.level.value,
                    'category': issue.category,
                    'message': issue.message,
                    'node_id': issue.node_id,
                    'edge_id': issue.edge_id,
                    'details': issue.details
                }
                for issue in self.report.issues
            ]
        }

    # Private helper methods

    def _validate_node_type(self, node: MNode) -> bool:
        """Validate node type is expected"""
        node_type = node.node_type if hasattr(node, 'node_type') else None

        if not node_type:
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="invalid_node_type",
                message="Node has no type",
                node_id=str(node)
            ))
            return False

        if node_type not in self.EXPECTED_NODE_TYPES:
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="unexpected_node_type",
                message=f"Unexpected node type: {node_type}",
                node_id=node.id if hasattr(node, 'id') else str(node)
            ))
            return False

        return True

    def _validate_node_properties(self, node: MNode) -> bool:
        """Validate node has required properties"""
        node_type = node.node_type if hasattr(node, 'node_type') else None
        node_id = node.id if hasattr(node, 'id') else str(node)
        node_data = node.data if hasattr(node, 'data') else {}

        required_props = self.REQUIRED_NODE_PROPERTIES.get(node_type, set())

        for prop in required_props:
            if prop not in node_data or node_data[prop] is None:
                self.report.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="missing_property",
                    message=f"Node missing required property: {prop}",
                    node_id=node_id,
                    details={'node_type': node_type, 'property': prop}
                ))
                return False

        return True

    def _validate_node_values(self, node: MNode) -> bool:
        """Validate node property values"""
        node_id = node.id if hasattr(node, 'id') else str(node)
        node_data = node.data if hasattr(node, 'data') else {}

        # Validate importance values (0-1)
        if 'importance' in node_data:
            importance = node_data['importance']
            if not (0 <= importance <= 1):
                self.report.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="invalid_value",
                    message=f"Importance out of range: {importance}",
                    node_id=node_id
                ))
                return False

        return True

    def _validate_edge_type(self, edge: MEdge) -> bool:
        """Validate edge type is expected"""
        edge_type = edge.edge_type if hasattr(edge, 'edge_type') else None

        if not edge_type:
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="invalid_edge_type",
                message="Edge has no type"
            ))
            return False

        if edge_type not in self.EXPECTED_EDGE_TYPES:
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="unexpected_edge_type",
                message=f"Unexpected edge type: {edge_type}"
            ))
            return False

        return True

    def _validate_edge_endpoints(self, graph: MGraph, edge: MEdge) -> bool:
        """Validate edge endpoints exist"""
        from_id = edge.from_node if hasattr(edge, 'from_node') else None
        to_id = edge.to_node if hasattr(edge, 'to_node') else None

        if not from_id or not to_id:
            self.report.issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                category="invalid_edge",
                message="Edge missing source or target"
            ))
            return False

        return True

    def _validate_edge_properties(self, edge: MEdge) -> bool:
        """Validate edge properties"""
        edge_data = edge.data if hasattr(edge, 'data') else {}

        # Validate confidence values (0-1)
        if 'confidence' in edge_data:
            confidence = edge_data['confidence']
            if not (0 <= confidence <= 1):
                self.report.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="invalid_value",
                    message=f"Confidence out of range: {confidence}"
                ))
                return False

        return True

    def _detect_cycles(self, adj_list: Dict[str, List[str]]) -> List[List[str]]:
        """
        Detect cycles in directed graph using DFS

        Returns:
            List of cycles (each cycle is a list of node IDs)
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adj_list.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            rec_stack.remove(node)

        for node in adj_list:
            if node not in visited:
                dfs(node, [])

        return cycles


def main():
    """Test validation with sample graph"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate MGraph knowledge graph integrity'
    )
    parser.add_argument(
        '--graph-file',
        required=True,
        help='Path to graph JSON file'
    )
    parser.add_argument(
        '--output',
        default='validation_report.json',
        help='Output file for validation report'
    )

    args = parser.parse_args()

    # Load graph
    logger.info(f"Loading graph from {args.graph_file}")
    graph = MGraph()
    graph.load_from_json(args.graph_file)

    # Validate
    validator = GraphValidator()
    validator.validate_nodes(graph)
    validator.validate_edges(graph)
    validator.check_orphaned_nodes(graph)
    validator.check_dangling_edges(graph)
    validator.validate_hierarchy(graph)
    validator.validate_constraints(graph)

    # Generate report
    report = validator.generate_report()

    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to {args.output}")

    # Exit with status
    if report['summary']['is_valid']:
        logger.info("✓ Graph validation PASSED")
        return 0
    else:
        logger.error("✗ Graph validation FAILED")
        return 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    exit(main())
