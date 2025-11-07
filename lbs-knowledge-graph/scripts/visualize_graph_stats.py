#!/usr/bin/env python3
"""
Quick Graph Statistics and Overview

Provides a comprehensive statistical overview of the LBS Knowledge Graph
without requiring heavy visualization libraries.

Usage:
    python scripts/visualize_graph_stats.py
    python scripts/visualize_graph_stats.py --verbose
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_graph(graph_path: str) -> Dict:
    """Load graph from JSON file."""
    print(f"📂 Loading graph from: {graph_path}")
    with open(graph_path, 'r') as f:
        return json.load(f)


def analyze_nodes(graph: Dict) -> Dict:
    """Analyze node statistics."""
    nodes = graph.get('nodes', [])

    stats = {
        'total': len(nodes),
        'by_type': defaultdict(int),
        'with_data': 0,
        'sample_by_type': {}
    }

    for node in nodes:
        node_type = node.get('node_type', 'unknown')
        stats['by_type'][node_type] += 1

        if node.get('data'):
            stats['with_data'] += 1

        # Keep first sample of each type
        if node_type not in stats['sample_by_type']:
            stats['sample_by_type'][node_type] = node

    return stats


def analyze_edges(graph: Dict) -> Dict:
    """Analyze edge statistics."""
    edges = graph.get('edges', [])

    stats = {
        'total': len(edges),
        'by_type': defaultdict(int),
        'connections': defaultdict(int),
        'sample_by_type': {}
    }

    for edge in edges:
        edge_type = edge.get('edge_type', 'unknown')
        stats['by_type'][edge_type] += 1

        # Count connections per node
        from_node = edge.get('from_node')
        to_node = edge.get('to_node')
        if from_node:
            stats['connections'][from_node] += 1
        if to_node:
            stats['connections'][to_node] += 1

        # Keep first sample of each type
        if edge_type not in stats['sample_by_type']:
            stats['sample_by_type'][edge_type] = edge

    return stats


def analyze_connectivity(graph: Dict, node_stats: Dict, edge_stats: Dict) -> Dict:
    """Analyze graph connectivity."""

    # Most connected nodes
    top_connected = sorted(
        edge_stats['connections'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    # Node ID to node mapping
    node_map = {n['id']: n for n in graph.get('nodes', [])}

    # Get node types for top connected
    top_with_types = []
    for node_id, count in top_connected:
        node = node_map.get(node_id, {})
        node_type = node.get('node_type', 'unknown')
        title = node.get('data', {}).get('title', node_id)
        top_with_types.append((title, node_type, count))

    # Calculate average degree
    total_connections = sum(edge_stats['connections'].values())
    avg_degree = total_connections / node_stats['total'] if node_stats['total'] > 0 else 0

    return {
        'top_connected': top_with_types,
        'avg_degree': avg_degree,
        'isolated_nodes': node_stats['total'] - len(edge_stats['connections'])
    }


def print_stats(node_stats: Dict, edge_stats: Dict, connectivity: Dict, verbose: bool = False):
    """Print formatted statistics."""

    print("\n" + "=" * 70)
    print("LBS KNOWLEDGE GRAPH - STATISTICS")
    print("=" * 70)

    # Overview
    print("\n📊 OVERVIEW")
    print(f"  Total Nodes: {node_stats['total']:,}")
    print(f"  Total Edges: {edge_stats['total']:,}")
    print(f"  Average Connections per Node: {connectivity['avg_degree']:.2f}")
    print(f"  Isolated Nodes: {connectivity['isolated_nodes']}")

    # Node types
    print("\n🔷 NODE TYPES")
    for node_type, count in sorted(node_stats['by_type'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / node_stats['total'] * 100) if node_stats['total'] > 0 else 0
        print(f"  {node_type:20s}: {count:5,} ({pct:5.1f}%)")

    # Edge types
    print("\n🔗 EDGE TYPES")
    for edge_type, count in sorted(edge_stats['by_type'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / edge_stats['total'] * 100) if edge_stats['total'] > 0 else 0
        print(f"  {edge_type:20s}: {count:5,} ({pct:5.1f}%)")

    # Top connected
    print("\n⭐ MOST CONNECTED NODES")
    for i, (title, node_type, count) in enumerate(connectivity['top_connected'], 1):
        print(f"  {i:2d}. {title[:50]:50s} ({node_type}, {count} connections)")

    # Verbose details
    if verbose:
        print("\n" + "=" * 70)
        print("DETAILED SAMPLES")
        print("=" * 70)

        print("\n📄 SAMPLE NODES BY TYPE:")
        for node_type, node in node_stats['sample_by_type'].items():
            print(f"\n  {node_type}:")
            print(f"    ID: {node.get('id')}")
            data = node.get('data', {})
            if data:
                print(f"    Data keys: {list(data.keys())[:5]}")
                if 'title' in data:
                    print(f"    Title: {data.get('title')[:60]}")

        print("\n🔗 SAMPLE EDGES BY TYPE:")
        for edge_type, edge in edge_stats['sample_by_type'].items():
            print(f"\n  {edge_type}:")
            print(f"    From: {edge.get('from_node')}")
            print(f"    To: {edge.get('to_node')}")
            data = edge.get('data', {})
            if data:
                print(f"    Data keys: {list(data.keys())[:5]}")

    print("\n" + "=" * 70)
    print("💡 TIP: Use --verbose flag for detailed samples")
    print("=" * 70)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='LBS Knowledge Graph Statistics')
    parser.add_argument('--graph', default='data/graph/graph.json', help='Path to graph JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed samples')
    args = parser.parse_args()

    # Auto-detect graph location (handle both root and lbs-knowledge-graph directories)
    graph_path = args.graph
    if not Path(graph_path).exists():
        # Try lbs-knowledge-graph subdirectory
        alt_path = Path('lbs-knowledge-graph') / graph_path
        if alt_path.exists():
            graph_path = str(alt_path)
        else:
            print(f"❌ Error: Graph file not found: {args.graph}")
            print(f"   Tried: {args.graph}")
            print(f"   Tried: {alt_path}")
            print(f"\n💡 Tip: Run from either:")
            print(f"   - /workspaces/university-pitch/lbs-knowledge-graph/ directory, or")
            print(f"   - /workspaces/university-pitch/ directory (will auto-detect)")
            sys.exit(1)

    # Load graph
    try:
        graph = load_graph(graph_path)
    except FileNotFoundError:
        print(f"❌ Error: Graph file not found: {graph_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in graph file: {e}")
        sys.exit(1)

    # Analyze
    print("🔍 Analyzing nodes...")
    node_stats = analyze_nodes(graph)

    print("🔍 Analyzing edges...")
    edge_stats = analyze_edges(graph)

    print("🔍 Analyzing connectivity...")
    connectivity = analyze_connectivity(graph, node_stats, edge_stats)

    # Print results
    print_stats(node_stats, edge_stats, connectivity, args.verbose)

    print("\n✅ Analysis complete!")
    print("\n📊 Next steps:")
    print("  - View interactive visualization: python scripts/visualize_graph_interactive.py")
    print("  - View specific subgraph: python scripts/visualize_subgraph.py --node-type Page")
    print("  - See full guide: cat docs/GRAPH_VISUALIZATION_GUIDE.md")


if __name__ == "__main__":
    main()
