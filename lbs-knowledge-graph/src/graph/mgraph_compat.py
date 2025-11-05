"""
MGraph-Compatible Graph Database Implementation

Lightweight implementation compatible with MGraph-DB API specification.
Uses NetworkX as backend with MGraph-like interface.
"""

import json
import networkx as nx
from typing import Dict, List, Any, Optional, Iterator
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class MNode:
    """Graph node representation"""
    id: str
    node_type: str
    data: Dict[str, Any]

    def dict(self):
        return asdict(self)


@dataclass
class MEdge:
    """Graph edge representation"""
    from_node: str
    to_node: str
    edge_type: str
    data: Dict[str, Any]

    def dict(self):
        return asdict(self)


class MGraph:
    """
    MGraph-compatible graph database using NetworkX backend

    Provides O(1) lookups with proper indexing and supports multiple export formats.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()  # Directed graph with multiple edges
        self._nodes_by_type = {}  # Index: type -> {node_id}
        self._edges_by_type = {}  # Index: type -> [(from, to, data)]

    def add_node(self, node_type: str, node_id: str, data: Dict[str, Any]) -> None:
        """
        Add a node to the graph

        Args:
            node_type: Type of node (Page, Section, etc.)
            node_id: Unique node identifier
            data: Node properties
        """
        self.graph.add_node(node_id, node_type=node_type, **data)

        # Update type index
        if node_type not in self._nodes_by_type:
            self._nodes_by_type[node_type] = set()
        self._nodes_by_type[node_type].add(node_id)

    def add_edge(self, from_node_id: str, to_node_id: str, edge_type: str, data: Dict[str, Any] = None) -> None:
        """
        Add an edge between nodes

        Args:
            from_node_id: Source node ID
            to_node_id: Target node ID
            edge_type: Type of edge (CONTAINS, LINKS_TO, etc.)
            data: Edge properties
        """
        edge_data = data or {}
        edge_data['edge_type'] = edge_type

        self.graph.add_edge(from_node_id, to_node_id, **edge_data)

        # Update type index
        if edge_type not in self._edges_by_type:
            self._edges_by_type[edge_type] = []
        self._edges_by_type[edge_type].append((from_node_id, to_node_id, edge_data))

    def get_node(self, node_id: str) -> Optional[MNode]:
        """Get a node by ID (O(1) lookup)"""
        if node_id not in self.graph.nodes:
            return None

        node_data = self.graph.nodes[node_id]
        node_type = node_data.get('node_type', 'Unknown')
        data = {k: v for k, v in node_data.items() if k != 'node_type'}

        return MNode(id=node_id, node_type=node_type, data=data)

    def get_edges(self, from_node_id: str = None, to_node_id: str = None, edge_type: str = None) -> List[MEdge]:
        """Get edges matching criteria"""
        edges = []

        if from_node_id and to_node_id:
            # Get all edges between specific nodes
            if self.graph.has_edge(from_node_id, to_node_id):
                edge_data_list = self.graph.get_edge_data(from_node_id, to_node_id)
                if edge_data_list:
                    for key, edge_data in edge_data_list.items():
                        if edge_type is None or edge_data.get('edge_type') == edge_type:
                            data = {k: v for k, v in edge_data.items() if k != 'edge_type'}
                            edges.append(MEdge(
                                from_node=from_node_id,
                                to_node=to_node_id,
                                edge_type=edge_data.get('edge_type', 'Unknown'),
                                data=data
                            ))
        elif from_node_id:
            # Get all outgoing edges
            if from_node_id in self.graph:
                for to_node in self.graph.successors(from_node_id):
                    edge_data_list = self.graph.get_edge_data(from_node_id, to_node)
                    for key, edge_data in edge_data_list.items():
                        if edge_type is None or edge_data.get('edge_type') == edge_type:
                            data = {k: v for k, v in edge_data.items() if k != 'edge_type'}
                            edges.append(MEdge(
                                from_node=from_node_id,
                                to_node=to_node,
                                edge_type=edge_data.get('edge_type', 'Unknown'),
                                data=data
                            ))
        elif to_node_id:
            # Get all incoming edges
            if to_node_id in self.graph:
                for from_node in self.graph.predecessors(to_node_id):
                    edge_data_list = self.graph.get_edge_data(from_node, to_node_id)
                    for key, edge_data in edge_data_list.items():
                        if edge_type is None or edge_data.get('edge_type') == edge_type:
                            data = {k: v for k, v in edge_data.items() if k != 'edge_type'}
                            edges.append(MEdge(
                                from_node=from_node,
                                to_node=to_node_id,
                                edge_type=edge_data.get('edge_type', 'Unknown'),
                                data=data
                            ))

        return edges

    def query(self, node_type: str = None, filters: Dict[str, Any] = None, limit: int = None) -> List[MNode]:
        """
        Query nodes by type and filters

        Args:
            node_type: Filter by node type
            filters: Additional property filters
            limit: Maximum results to return

        Returns:
            List of matching nodes
        """
        # Use index for type filtering (O(1))
        if node_type:
            node_ids = self._nodes_by_type.get(node_type, set())
        else:
            node_ids = self.graph.nodes()

        results = []
        for node_id in node_ids:
            node = self.get_node(node_id)
            if node:
                # Apply filters
                if filters:
                    matches = all(node.data.get(k) == v for k, v in filters.items())
                    if not matches:
                        continue

                results.append(node)

                if limit and len(results) >= limit:
                    break

        return results

    def all_nodes(self) -> Iterator[MNode]:
        """Iterator over all nodes"""
        for node_id in self.graph.nodes():
            yield self.get_node(node_id)

    def all_edges(self) -> Iterator[MEdge]:
        """Iterator over all edges"""
        for from_node, to_node, edge_data in self.graph.edges(data=True):
            data = {k: v for k, v in edge_data.items() if k != 'edge_type'}
            yield MEdge(
                from_node=from_node,
                to_node=to_node,
                edge_type=edge_data.get('edge_type', 'Unknown'),
                data=data
            )

    def node_count(self) -> int:
        """Get total number of nodes"""
        return self.graph.number_of_nodes()

    def edge_count(self) -> int:
        """Get total number of edges"""
        return self.graph.number_of_edges()

    def save_to_json(self, file_path: str) -> None:
        """Save graph to JSON file"""
        data = {
            'nodes': [node.dict() for node in self.all_nodes()],
            'edges': [edge.dict() for edge in self.all_edges()]
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load_from_json(self, file_path: str) -> None:
        """Load graph from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Clear existing graph
        self.graph.clear()
        self._nodes_by_type.clear()
        self._edges_by_type.clear()

        # Load nodes
        for node_data in data.get('nodes', []):
            self.add_node(
                node_type=node_data['node_type'],
                node_id=node_data['id'],
                data=node_data['data']
            )

        # Load edges
        for edge_data in data.get('edges', []):
            self.add_edge(
                from_node_id=edge_data['from_node'],
                to_node_id=edge_data['to_node'],
                edge_type=edge_data['edge_type'],
                data=edge_data['data']
            )

    def export_graphml(self, file_path: str) -> None:
        """Export to GraphML format (for Gephi, Neo4j)"""
        nx.write_graphml(self.graph, file_path)

    def export_cypher(self, file_path: str) -> None:
        """Export to Cypher format (for Neo4j)"""
        with open(file_path, 'w', encoding='utf-8') as f:
            # Create nodes
            for node in self.all_nodes():
                props = ', '.join(f"{k}: {json.dumps(v)}" for k, v in node.data.items())
                f.write(f"CREATE (n{node.id}:{node.node_type} {{{props}}});\n")

            # Create relationships
            for edge in self.all_edges():
                props = ', '.join(f"{k}: {json.dumps(v)}" for k, v in edge.data.items())
                props_str = f" {{{props}}}" if props else ""
                f.write(f"MATCH (a {{id: '{edge.from_node}'}}), (b {{id: '{edge.to_node}'}}) "
                       f"CREATE (a)-[:{edge.edge_type}{props_str}]->(b);\n")

    def export_mermaid(self, file_path: str) -> None:
        """Export to Mermaid diagram format"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("graph TD\n")

            # Write nodes
            for node in self.all_nodes():
                label = node.data.get('title', node.data.get('name', node.id))
                f.write(f'    {node.id}["{label}"]\n')

            # Write edges
            for edge in self.all_edges():
                f.write(f'    {edge.from_node} -->|{edge.edge_type}| {edge.to_node}\n')

    def export_dot(self, file_path: str) -> None:
        """Export to DOT format (for Graphviz)"""
        nx.drawing.nx_pydot.write_dot(self.graph, file_path)

    def traverse(self, start_node_id: str, edge_type: str = None, depth: int = 1) -> List[MNode]:
        """
        Traverse graph from a starting node

        Args:
            start_node_id: Starting node ID
            edge_type: Filter by edge type
            depth: Traversal depth

        Returns:
            List of reachable nodes
        """
        if start_node_id not in self.graph:
            return []

        visited = set()
        queue = [(start_node_id, 0)]
        results = []

        while queue:
            current_id, current_depth = queue.pop(0)

            if current_id in visited or current_depth > depth:
                continue

            visited.add(current_id)

            if current_depth > 0:  # Don't include start node
                node = self.get_node(current_id)
                if node:
                    results.append(node)

            if current_depth < depth:
                for successor in self.graph.successors(current_id):
                    if successor not in visited:
                        # Check edge type if specified
                        if edge_type:
                            edges = self.get_edges(current_id, successor, edge_type)
                            if edges:
                                queue.append((successor, current_depth + 1))
                        else:
                            queue.append((successor, current_depth + 1))

        return results

    def traverse_reverse(self, start_node_id: str, edge_type: str = None, depth: int = 1) -> List[MNode]:
        """Traverse graph in reverse direction (follow incoming edges)"""
        if start_node_id not in self.graph:
            return []

        visited = set()
        queue = [(start_node_id, 0)]
        results = []

        while queue:
            current_id, current_depth = queue.pop(0)

            if current_id in visited or current_depth > depth:
                continue

            visited.add(current_id)

            if current_depth > 0:
                node = self.get_node(current_id)
                if node:
                    results.append(node)

            if current_depth < depth:
                for predecessor in self.graph.predecessors(current_id):
                    if predecessor not in visited:
                        if edge_type:
                            edges = self.get_edges(predecessor, current_id, edge_type)
                            if edges:
                                queue.append((predecessor, current_depth + 1))
                        else:
                            queue.append((predecessor, current_depth + 1))

        return results
