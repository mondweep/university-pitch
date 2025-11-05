#!/usr/bin/env python3
"""
Graph Quality Metrics - Calculate Phase 2 specific quality metrics
Analyzes graph structure, density, connectivity, and other graph-theoretic properties
"""

import logging
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import json

logger = logging.getLogger(__name__)


@dataclass
class GraphMetrics:
    """Comprehensive graph quality metrics"""
    # Basic counts
    total_nodes: int = 0
    total_edges: int = 0

    # Nodes by type
    node_counts_by_type: Dict[str, int] = field(default_factory=dict)

    # Edges by type
    edge_counts_by_type: Dict[str, int] = field(default_factory=dict)

    # Density metrics
    graph_density: float = 0.0
    avg_node_degree: float = 0.0
    max_node_degree: int = 0
    min_node_degree: int = 0

    # Connectivity metrics
    connected_components: int = 0
    largest_component_size: int = 0
    isolated_nodes: int = 0

    # Path metrics
    avg_path_length: float = 0.0
    max_path_length: int = 0
    diameter: int = 0

    # Hub analysis
    hub_nodes: List[Dict[str, Any]] = field(default_factory=list)
    hub_threshold: int = 10

    # Clustering
    clustering_coefficient: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'basic': {
                'total_nodes': self.total_nodes,
                'total_edges': self.total_edges,
                'node_counts_by_type': self.node_counts_by_type,
                'edge_counts_by_type': self.edge_counts_by_type
            },
            'density': {
                'graph_density': self.graph_density,
                'avg_node_degree': self.avg_node_degree,
                'max_node_degree': self.max_node_degree,
                'min_node_degree': self.min_node_degree
            },
            'connectivity': {
                'connected_components': self.connected_components,
                'largest_component_size': self.largest_component_size,
                'isolated_nodes': self.isolated_nodes
            },
            'paths': {
                'avg_path_length': self.avg_path_length,
                'max_path_length': self.max_path_length,
                'diameter': self.diameter
            },
            'hubs': {
                'threshold': self.hub_threshold,
                'count': len(self.hub_nodes),
                'nodes': self.hub_nodes
            },
            'clustering': {
                'coefficient': self.clustering_coefficient
            }
        }


class QualityMetrics:
    """Calculate comprehensive graph quality metrics"""

    def __init__(self):
        self.metrics = GraphMetrics()

    def calculate_density(self, graph: Any) -> float:
        """
        Calculate graph density
        Density = |E| / (|V| * (|V| - 1)) for directed graphs

        Args:
            graph: MGraph instance

        Returns:
            Density value (0-1)
        """
        try:
            num_nodes = graph.node_count() if hasattr(graph, 'node_count') else 0
            num_edges = graph.edge_count() if hasattr(graph, 'edge_count') else 0

            self.metrics.total_nodes = num_nodes
            self.metrics.total_edges = num_edges

            if num_nodes <= 1:
                return 0.0

            max_edges = num_nodes * (num_nodes - 1)
            density = num_edges / max_edges if max_edges > 0 else 0.0

            self.metrics.graph_density = round(density, 4)
            return self.metrics.graph_density

        except Exception as e:
            logger.error(f"Error calculating density: {e}")
            return 0.0

    def calculate_avg_degree(self, graph: Any) -> float:
        """
        Calculate average node degree
        Avg Degree = 2 * |E| / |V| for undirected, |E| / |V| for directed

        Args:
            graph: MGraph instance

        Returns:
            Average degree
        """
        try:
            num_nodes = graph.node_count() if hasattr(graph, 'node_count') else 0
            num_edges = graph.edge_count() if hasattr(graph, 'edge_count') else 0

            if num_nodes == 0:
                return 0.0

            # For directed graphs
            avg_degree = num_edges / num_nodes

            self.metrics.avg_node_degree = round(avg_degree, 2)
            return self.metrics.avg_node_degree

        except Exception as e:
            logger.error(f"Error calculating average degree: {e}")
            return 0.0

    def find_hub_nodes(self, graph: Any, threshold: int = 10) -> List[Dict]:
        """
        Find hub nodes (nodes with high degree)

        Args:
            graph: MGraph instance
            threshold: Minimum degree to be considered a hub

        Returns:
            List of hub node info dicts
        """
        try:
            hubs = []

            if not hasattr(graph, 'all_nodes'):
                return hubs

            # Calculate degree for each node
            node_degrees = {}

            # Count outbound edges
            if hasattr(graph, 'all_edges'):
                for edge in graph.all_edges():
                    from_id = edge.from_node if hasattr(edge, 'from_node') else None
                    to_id = edge.to_node if hasattr(edge, 'to_node') else None

                    if from_id:
                        node_degrees[from_id] = node_degrees.get(from_id, 0) + 1
                    if to_id:
                        node_degrees[to_id] = node_degrees.get(to_id, 0) + 1

            # Find nodes meeting threshold
            for node in graph.all_nodes():
                node_id = node.id if hasattr(node, 'id') else str(node)
                degree = node_degrees.get(node_id, 0)

                if degree >= threshold:
                    node_type = node.node_type if hasattr(node, 'node_type') else 'Unknown'
                    node_data = node.data if hasattr(node, 'data') else {}

                    hubs.append({
                        'id': node_id,
                        'type': node_type,
                        'degree': degree,
                        'title': node_data.get('title') or node_data.get('name', 'Untitled')
                    })

            # Sort by degree descending
            hubs.sort(key=lambda x: x['degree'], reverse=True)

            self.metrics.hub_nodes = hubs
            self.metrics.hub_threshold = threshold

            # Update min/max degrees
            if node_degrees:
                self.metrics.max_node_degree = max(node_degrees.values())
                self.metrics.min_node_degree = min(node_degrees.values())

            logger.info(f"Found {len(hubs)} hub nodes (threshold: {threshold})")

            return hubs

        except Exception as e:
            logger.error(f"Error finding hub nodes: {e}")
            return []

    def calculate_path_metrics(self, graph: Any, sample_size: int = 100) -> Dict:
        """
        Calculate path metrics using BFS sampling
        (Full all-pairs shortest paths is O(V²), so we sample)

        Args:
            graph: MGraph instance
            sample_size: Number of source nodes to sample

        Returns:
            Dictionary with path metrics
        """
        try:
            if not hasattr(graph, 'all_nodes') or not hasattr(graph, 'all_edges'):
                return {}

            nodes = list(graph.all_nodes())
            if not nodes:
                return {}

            # Build adjacency list
            adj_list = {}
            for edge in graph.all_edges():
                from_id = edge.from_node if hasattr(edge, 'from_node') else None
                to_id = edge.to_node if hasattr(edge, 'to_node') else None

                if from_id and to_id:
                    if from_id not in adj_list:
                        adj_list[from_id] = []
                    adj_list[from_id].append(to_id)

            # Sample nodes
            import random
            sample_nodes = random.sample(nodes, min(sample_size, len(nodes)))

            all_path_lengths = []
            max_path = 0

            # BFS from each sample node
            for start_node in sample_nodes:
                start_id = start_node.id if hasattr(start_node, 'id') else str(start_node)
                distances = self._bfs_distances(start_id, adj_list)

                path_lengths = [d for d in distances.values() if d > 0]
                if path_lengths:
                    all_path_lengths.extend(path_lengths)
                    max_path = max(max_path, max(path_lengths))

            # Calculate average
            avg_path = sum(all_path_lengths) / len(all_path_lengths) if all_path_lengths else 0.0

            self.metrics.avg_path_length = round(avg_path, 2)
            self.metrics.max_path_length = max_path
            self.metrics.diameter = max_path  # Approximation from sample

            return {
                'avg_path_length': self.metrics.avg_path_length,
                'max_path_length': self.metrics.max_path_length,
                'diameter': self.metrics.diameter
            }

        except Exception as e:
            logger.error(f"Error calculating path metrics: {e}")
            return {}

    def find_disconnected_components(self, graph: Any) -> List[List[str]]:
        """
        Find disconnected components using union-find

        Args:
            graph: MGraph instance

        Returns:
            List of components (each component is a list of node IDs)
        """
        try:
            if not hasattr(graph, 'all_nodes') or not hasattr(graph, 'all_edges'):
                return []

            nodes = list(graph.all_nodes())
            if not nodes:
                return []

            # Build undirected adjacency list
            adj_list = {}
            for node in nodes:
                node_id = node.id if hasattr(node, 'id') else str(node)
                adj_list[node_id] = []

            for edge in graph.all_edges():
                from_id = edge.from_node if hasattr(edge, 'from_node') else None
                to_id = edge.to_node if hasattr(edge, 'to_node') else None

                if from_id and to_id:
                    adj_list[from_id].append(to_id)
                    adj_list[to_id].append(from_id)  # Undirected

            # Find components using DFS
            visited = set()
            components = []

            for node_id in adj_list:
                if node_id not in visited:
                    component = self._dfs_component(node_id, adj_list, visited)
                    components.append(component)

            # Update metrics
            self.metrics.connected_components = len(components)
            self.metrics.largest_component_size = max(len(c) for c in components) if components else 0
            self.metrics.isolated_nodes = sum(1 for c in components if len(c) == 1)

            logger.info(f"Found {len(components)} connected components")

            return components

        except Exception as e:
            logger.error(f"Error finding components: {e}")
            return []

    def calculate_clustering_coefficient(self, graph: Any, sample_size: int = 100) -> float:
        """
        Calculate average clustering coefficient (sampled)

        Args:
            graph: MGraph instance
            sample_size: Number of nodes to sample

        Returns:
            Clustering coefficient (0-1)
        """
        try:
            if not hasattr(graph, 'all_nodes') or not hasattr(graph, 'all_edges'):
                return 0.0

            nodes = list(graph.all_nodes())
            if not nodes:
                return 0.0

            # Build adjacency list (undirected)
            adj_list = {}
            for edge in graph.all_edges():
                from_id = edge.from_node if hasattr(edge, 'from_node') else None
                to_id = edge.to_node if hasattr(edge, 'to_node') else None

                if from_id and to_id:
                    if from_id not in adj_list:
                        adj_list[from_id] = set()
                    if to_id not in adj_list:
                        adj_list[to_id] = set()

                    adj_list[from_id].add(to_id)
                    adj_list[to_id].add(from_id)

            # Sample nodes
            import random
            sample_nodes = random.sample(nodes, min(sample_size, len(nodes)))

            coefficients = []

            for node in sample_nodes:
                node_id = node.id if hasattr(node, 'id') else str(node)
                neighbors = adj_list.get(node_id, set())

                if len(neighbors) < 2:
                    continue

                # Count edges between neighbors
                edges_between_neighbors = 0
                for n1 in neighbors:
                    for n2 in neighbors:
                        if n1 != n2 and n2 in adj_list.get(n1, set()):
                            edges_between_neighbors += 1

                # Clustering coefficient for this node
                max_edges = len(neighbors) * (len(neighbors) - 1)
                coefficient = edges_between_neighbors / max_edges if max_edges > 0 else 0.0
                coefficients.append(coefficient)

            # Average
            avg_coefficient = sum(coefficients) / len(coefficients) if coefficients else 0.0

            self.metrics.clustering_coefficient = round(avg_coefficient, 4)
            return self.metrics.clustering_coefficient

        except Exception as e:
            logger.error(f"Error calculating clustering coefficient: {e}")
            return 0.0

    def analyze_node_distribution(self, graph: Any) -> Dict[str, int]:
        """
        Analyze distribution of nodes by type

        Args:
            graph: MGraph instance

        Returns:
            Dictionary of node counts by type
        """
        try:
            distribution = {}

            if hasattr(graph, 'all_nodes'):
                for node in graph.all_nodes():
                    node_type = node.node_type if hasattr(node, 'node_type') else 'Unknown'
                    distribution[node_type] = distribution.get(node_type, 0) + 1

            self.metrics.node_counts_by_type = distribution
            return distribution

        except Exception as e:
            logger.error(f"Error analyzing node distribution: {e}")
            return {}

    def analyze_edge_distribution(self, graph: Any) -> Dict[str, int]:
        """
        Analyze distribution of edges by type

        Args:
            graph: MGraph instance

        Returns:
            Dictionary of edge counts by type
        """
        try:
            distribution = {}

            if hasattr(graph, 'all_edges'):
                for edge in graph.all_edges():
                    edge_type = edge.edge_type if hasattr(edge, 'edge_type') else 'Unknown'
                    distribution[edge_type] = distribution.get(edge_type, 0) + 1

            self.metrics.edge_counts_by_type = distribution
            return distribution

        except Exception as e:
            logger.error(f"Error analyzing edge distribution: {e}")
            return {}

    def generate_quality_report(self, graph: Any) -> Dict[str, Any]:
        """
        Generate comprehensive quality metrics report

        Args:
            graph: MGraph instance

        Returns:
            Complete quality report dictionary
        """
        logger.info("Generating graph quality report...")

        # Run all analyses
        self.calculate_density(graph)
        self.calculate_avg_degree(graph)
        self.find_hub_nodes(graph)
        self.calculate_path_metrics(graph)
        self.find_disconnected_components(graph)
        self.calculate_clustering_coefficient(graph)
        self.analyze_node_distribution(graph)
        self.analyze_edge_distribution(graph)

        return self.metrics.to_dict()

    # Private helper methods

    def _bfs_distances(self, start_id: str, adj_list: Dict) -> Dict[str, int]:
        """BFS to find distances from start node"""
        distances = {start_id: 0}
        queue = deque([start_id])

        while queue:
            node_id = queue.popleft()
            current_dist = distances[node_id]

            for neighbor in adj_list.get(node_id, []):
                if neighbor not in distances:
                    distances[neighbor] = current_dist + 1
                    queue.append(neighbor)

        return distances

    def _dfs_component(
        self,
        start_id: str,
        adj_list: Dict,
        visited: Set[str]
    ) -> List[str]:
        """DFS to find connected component"""
        component = []
        stack = [start_id]

        while stack:
            node_id = stack.pop()
            if node_id in visited:
                continue

            visited.add(node_id)
            component.append(node_id)

            for neighbor in adj_list.get(node_id, []):
                if neighbor not in visited:
                    stack.append(neighbor)

        return component


def main():
    """Test quality metrics calculator"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Calculate graph quality metrics'
    )
    parser.add_argument(
        '--graph-file',
        required=True,
        help='Path to graph JSON file'
    )
    parser.add_argument(
        '--output',
        default='data/validation/quality_metrics.json',
        help='Output file for quality metrics'
    )

    args = parser.parse_args()

    # Load graph
    try:
        from mgraph_db import MGraph
        logger.info(f"Loading graph from {args.graph_file}")
        graph = MGraph()
        graph.load_from_json(args.graph_file)
    except ImportError:
        logger.error("mgraph_db not installed. Install with: pip install mgraph-db")
        return 1

    # Calculate metrics
    calculator = QualityMetrics()
    report = calculator.generate_quality_report(graph)

    # Print summary
    print("\n" + "="*60)
    print("GRAPH QUALITY METRICS")
    print("="*60)
    print(f"\nBasic Metrics:")
    print(f"  Total Nodes: {report['basic']['total_nodes']:,}")
    print(f"  Total Edges: {report['basic']['total_edges']:,}")
    print(f"\nDensity Metrics:")
    print(f"  Graph Density: {report['density']['graph_density']:.4f}")
    print(f"  Avg Node Degree: {report['density']['avg_node_degree']:.2f}")
    print(f"\nConnectivity:")
    print(f"  Connected Components: {report['connectivity']['connected_components']}")
    print(f"  Largest Component: {report['connectivity']['largest_component_size']}")
    print(f"\nHub Nodes: {report['hubs']['count']}")
    print("="*60)

    # Export
    from pathlib import Path
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Quality metrics exported to {output_path}")
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    exit(main())
