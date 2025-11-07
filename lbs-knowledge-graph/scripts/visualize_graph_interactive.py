#!/usr/bin/env python3
"""
Interactive HTML Graph Visualization

Creates an interactive HTML visualization of the LBS Knowledge Graph
using pyvis for exploration in a web browser.

Usage:
    # Full graph (may be slow with 3,963 nodes)
    python scripts/visualize_graph_interactive.py

    # Filtered view (recommended)
    python scripts/visualize_graph_interactive.py --node-types Page,Section --max-nodes 100

    # Single page and its connections
    python scripts/visualize_graph_interactive.py --focus-node "homepage_5002b6553ab6"
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_graph(graph_path: str) -> Dict:
    """Load graph from JSON file."""
    print(f"📂 Loading graph from: {graph_path}")
    with open(graph_path, 'r') as f:
        return json.load(f)


def filter_graph(
    graph: Dict,
    node_types: Optional[List[str]] = None,
    max_nodes: Optional[int] = None,
    focus_node: Optional[str] = None
) -> tuple[Dict, Dict]:
    """Filter graph based on criteria."""

    all_nodes = {n['id']: n for n in graph.get('nodes', [])}
    all_edges = graph.get('edges', [])

    # If focusing on specific node, get its neighborhood
    if focus_node:
        if focus_node not in all_nodes:
            print(f"⚠️  Warning: Node '{focus_node}' not found in graph")
            return {}, {}

        # Get connected nodes
        connected = {focus_node}
        for edge in all_edges:
            if edge['from_node'] == focus_node:
                connected.add(edge['to_node'])
            elif edge['to_node'] == focus_node:
                connected.add(edge['from_node'])

        # Filter to connected nodes
        filtered_nodes = {nid: n for nid, n in all_nodes.items() if nid in connected}
        filtered_edges = [
            e for e in all_edges
            if e['from_node'] in connected and e['to_node'] in connected
        ]

        print(f"🎯 Focus: {focus_node}")
        print(f"   Found {len(filtered_nodes)} connected nodes")

        return filtered_nodes, filtered_edges

    # Filter by node type
    filtered_nodes = all_nodes
    if node_types:
        filtered_nodes = {
            nid: n for nid, n in all_nodes.items()
            if n.get('node_type') in node_types
        }
        print(f"🔍 Filtered to node types: {', '.join(node_types)}")
        print(f"   {len(filtered_nodes)} nodes match")

    # Limit number of nodes
    if max_nodes and len(filtered_nodes) > max_nodes:
        # Keep most connected nodes
        node_degrees = {}
        for edge in all_edges:
            node_degrees[edge['from_node']] = node_degrees.get(edge['from_node'], 0) + 1
            node_degrees[edge['to_node']] = node_degrees.get(edge['to_node'], 0) + 1

        # Sort by degree and take top N
        sorted_nodes = sorted(
            filtered_nodes.keys(),
            key=lambda nid: node_degrees.get(nid, 0),
            reverse=True
        )[:max_nodes]

        filtered_nodes = {nid: filtered_nodes[nid] for nid in sorted_nodes}
        print(f"📉 Limited to {max_nodes} most connected nodes")

    # Filter edges to only include nodes we're keeping
    filtered_edges = [
        e for e in all_edges
        if e['from_node'] in filtered_nodes and e['to_node'] in filtered_nodes
    ]

    print(f"✅ Final graph: {len(filtered_nodes)} nodes, {len(filtered_edges)} edges")

    return filtered_nodes, filtered_edges


def create_visualization(
    nodes: Dict,
    edges: List[Dict],
    output_path: str,
    title: str = "LBS Knowledge Graph"
):
    """Create interactive visualization using pyvis."""

    try:
        from pyvis.network import Network
    except ImportError:
        print("\n❌ Error: pyvis not installed")
        print("   Install with: pip install pyvis")
        sys.exit(1)

    print(f"\n🎨 Creating visualization...")

    # Create network
    net = Network(
        height="900px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
        directed=True
    )

    # Configure physics
    net.barnes_hut(
        gravity=-20000,
        central_gravity=0.3,
        spring_length=100,
        spring_strength=0.001,
        damping=0.09
    )

    # Node colors by type
    type_colors = {
        'Page': '#e74c3c',       # Red
        'Section': '#3498db',     # Blue
        'ContentItem': '#2ecc71', # Green
        'Topic': '#f39c12',       # Orange
        'Entity': '#9b59b6',      # Purple
        'unknown': '#95a5a6'      # Gray
    }

    # Add nodes
    for node_id, node in nodes.items():
        node_type = node.get('node_type', 'unknown')
        data = node.get('data', {})

        # Node label
        title_text = data.get('title', node_id)
        label = title_text[:30] + "..." if len(title_text) > 30 else title_text

        # Node hover info
        hover_info = f"<b>{node_type}</b><br>"
        hover_info += f"ID: {node_id}<br>"
        if 'title' in data:
            hover_info += f"Title: {data['title']}<br>"
        if 'url' in data:
            hover_info += f"URL: {data['url']}<br>"

        # Add node
        net.add_node(
            node_id,
            label=label,
            title=hover_info,
            color=type_colors.get(node_type, type_colors['unknown']),
            size=20 if node_type == 'Page' else 10
        )

    # Add edges
    edge_colors = {
        'HAS_SECTION': '#3498db',
        'HAS_CONTENT': '#2ecc71',
        'HAS_TOPIC': '#f39c12',
        'MENTIONS': '#9b59b6',
        'LINKS_TO': '#e74c3c'
    }

    for edge in edges:
        from_node = edge.get('from_node')
        to_node = edge.get('to_node')
        edge_type = edge.get('edge_type', 'unknown')

        if from_node in nodes and to_node in nodes:
            net.add_edge(
                from_node,
                to_node,
                title=edge_type,
                color=edge_colors.get(edge_type, '#95a5a6')
            )

    # Set options
    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "font": {
          "size": 14,
          "face": "arial"
        }
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        },
        "smooth": {
          "type": "continuous"
        }
      },
      "physics": {
        "enabled": true,
        "stabilization": {
          "iterations": 100
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """)

    # Save
    net.save_graph(output_path)
    print(f"✅ Visualization saved to: {output_path}")
    print(f"   Open in browser to explore!")


def main():
    """Main entry point."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Interactive LBS Knowledge Graph Visualization')
    parser.add_argument('--graph', default='data/graph/graph.json', help='Path to graph JSON')
    parser.add_argument('--output', default='visualizations/graph_interactive.html', help='Output HTML file')
    parser.add_argument('--node-types', help='Comma-separated node types to include (e.g., Page,Section)')
    parser.add_argument('--max-nodes', type=int, help='Maximum number of nodes to display')
    parser.add_argument('--focus-node', help='Focus on specific node and its connections')
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

    # Auto-detect output location
    output_path = args.output
    if not Path(output_path).parent.exists():
        # Try lbs-knowledge-graph subdirectory
        alt_output = Path('lbs-knowledge-graph') / output_path
        if alt_output.parent.exists():
            output_path = str(alt_output)

    # Load graph
    try:
        graph = load_graph(graph_path)
    except FileNotFoundError:
        print(f"❌ Error: Graph file not found: {graph_path}")
        sys.exit(1)

    # Parse node types
    node_types = None
    if args.node_types:
        node_types = [t.strip() for t in args.node_types.split(',')]

    # Filter graph
    print(f"\n🔍 Filtering graph...")
    filtered_nodes, filtered_edges = filter_graph(
        graph,
        node_types=node_types,
        max_nodes=args.max_nodes,
        focus_node=args.focus_node
    )

    if not filtered_nodes:
        print("❌ No nodes to visualize after filtering")
        sys.exit(1)

    # Create output directory
    final_output = Path(output_path)
    final_output.parent.mkdir(parents=True, exist_ok=True)

    # Create visualization
    create_visualization(
        filtered_nodes,
        filtered_edges,
        str(final_output),
        title=f"LBS Knowledge Graph ({len(filtered_nodes)} nodes)"
    )

    print("\n🎉 Success!")
    print(f"\n📖 To view:")
    print(f"   Open: {final_output}")
    print(f"   Or run: open {final_output}  (Mac)")
    print(f"          xdg-open {final_output}  (Linux)")
    print("\n💡 Tips:")
    print("   - Click and drag nodes to rearrange")
    print("   - Hover over nodes for details")
    print("   - Use mouse wheel to zoom")
    print("   - Use navigation buttons in bottom right")


if __name__ == "__main__":
    main()
