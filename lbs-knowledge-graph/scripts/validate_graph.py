#!/usr/bin/env python3
"""
Validate graph structure and integrity.

Usage:
    python scripts/validate_graph.py --graph data/graph/graph.json
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def load_graph(graph_path: str) -> dict:
    """Load graph from JSON file."""
    print(f"Loading graph from {graph_path}...")
    with open(graph_path, "r") as f:
        graph = json.load(f)
    return graph


def validate_structure(graph: dict) -> bool:
    """Validate basic graph structure."""
    if "nodes" not in graph:
        print("❌ Graph missing 'nodes' key")
        return False

    if "edges" not in graph:
        print("❌ Graph missing 'edges' key")
        return False

    if not isinstance(graph["nodes"], list):
        print("❌ 'nodes' must be a list")
        return False

    if not isinstance(graph["edges"], list):
        print("❌ 'edges' must be a list")
        return False

    print(f"✅ Graph loaded successfully")
    print(f"   Nodes: {len(graph['nodes']):,}")
    print(f"   Edges: {len(graph['edges']):,}")
    print()

    return True


def validate_nodes(nodes: list) -> bool:
    """Validate node structure."""
    print("Validating nodes...")

    # Check node types
    node_types = Counter(n.get("node_type", "unknown") for n in nodes)
    print(f"\n✅ Node types:")
    for node_type, count in node_types.most_common():
        print(f"   {node_type}: {count:,}")

    # Check required properties
    required_props = ["id", "node_type"]
    missing_props = []

    for i, node in enumerate(nodes):
        for prop in required_props:
            if prop not in node:
                missing_props.append((i, prop))

    if missing_props:
        print(f"\n❌ Found {len(missing_props)} nodes missing required properties:")
        for i, prop in missing_props[:10]:  # Show first 10
            print(f"   Node {i}: missing '{prop}'")
        return False

    print(f"\n✅ All nodes have required properties")

    # Check for duplicate IDs
    node_ids = [n["id"] for n in nodes]
    duplicates = [nid for nid in node_ids if node_ids.count(nid) > 1]
    if duplicates:
        print(f"\n❌ Found {len(set(duplicates))} duplicate node IDs:")
        for nid in list(set(duplicates))[:10]:
            print(f"   {nid}")
        return False

    print(f"✅ No duplicate node IDs")
    print()

    return True


def validate_edges(edges: list, nodes: list) -> bool:
    """Validate edge structure."""
    print("Validating edges...")

    # Check edge types
    edge_types = Counter(e.get("relationship_type", "unknown") for e in edges)
    print(f"\n✅ Edge types:")
    for edge_type, count in edge_types.most_common():
        print(f"   {edge_type}: {count:,}")

    # Check required properties
    required_props = ["source", "target", "relationship_type"]
    missing_props = []

    for i, edge in enumerate(edges):
        for prop in required_props:
            if prop not in edge:
                missing_props.append((i, prop))

    if missing_props:
        print(f"\n❌ Found {len(missing_props)} edges missing required properties:")
        for i, prop in missing_props[:10]:
            print(f"   Edge {i}: missing '{prop}'")
        return False

    print(f"\n✅ All edges have required properties")

    # Check edge validity (source/target exist)
    node_ids = set(n["id"] for n in nodes)
    invalid_edges = []

    for i, edge in enumerate(edges):
        if edge["source"] not in node_ids:
            invalid_edges.append((i, "source", edge["source"]))
        if edge["target"] not in node_ids:
            invalid_edges.append((i, "target", edge["target"]))

    if invalid_edges:
        print(f"\n❌ Found {len(invalid_edges)} invalid edges:")
        for i, prop, nid in invalid_edges[:10]:
            print(f"   Edge {i}: {prop} '{nid}' does not exist")
        return False

    print(f"✅ All edges valid")

    # Check for orphaned nodes
    connected_nodes = set()
    for edge in edges:
        connected_nodes.add(edge["source"])
        connected_nodes.add(edge["target"])

    orphaned = [n["id"] for n in nodes if n["id"] not in connected_nodes]
    if orphaned:
        print(f"\n⚠️  Found {len(orphaned)} orphaned nodes (no edges)")
        if len(orphaned) <= 10:
            for nid in orphaned:
                print(f"   {nid}")
    else:
        print(f"✅ No orphaned nodes")

    print()

    return True


def validate_domain_model(graph: dict) -> bool:
    """Validate domain-specific requirements."""
    print("Validating domain model...")

    nodes = graph["nodes"]
    edges = graph["edges"]

    # Check for Page nodes
    pages = [n for n in nodes if n.get("node_type") == "Page"]
    if not pages:
        print("❌ No Page nodes found")
        return False

    print(f"✅ Found {len(pages)} Page nodes")

    # Check for Section nodes
    sections = [n for n in nodes if n.get("node_type") == "Section"]
    print(f"✅ Found {len(sections)} Section nodes")

    # Check for ContentItem nodes
    items = [n for n in nodes if n.get("node_type") == "ContentItem"]
    print(f"✅ Found {len(items)} ContentItem nodes")

    # Check CONTAINS relationships
    contains = [e for e in edges if e.get("relationship_type") == "CONTAINS"]
    if not contains:
        print("⚠️  No CONTAINS relationships found")
    else:
        print(f"✅ Found {len(contains)} CONTAINS relationships")

    print()

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate graph structure")
    parser.add_argument(
        "--graph",
        default="data/graph/graph.json",
        help="Path to graph JSON file"
    )
    args = parser.parse_args()

    if not Path(args.graph).exists():
        print(f"❌ Graph file not found: {args.graph}")
        print()
        print("Please run Phase 1 + 2 first:")
        print("  python scripts/crawl.py")
        print("  python scripts/build_graph.py")
        sys.exit(1)

    print("=" * 60)
    print("Graph Validation")
    print("=" * 60)
    print()

    # Load graph
    graph = load_graph(args.graph)

    # Run validations
    validations = [
        ("Structure", lambda: validate_structure(graph)),
        ("Nodes", lambda: validate_nodes(graph["nodes"])),
        ("Edges", lambda: validate_edges(graph["edges"], graph["nodes"])),
        ("Domain Model", lambda: validate_domain_model(graph)),
    ]

    results = []
    for name, func in validations:
        success = func()
        results.append(success)

        if not success:
            print(f"\n⚠️  {name} validation failed\n")

    print("=" * 60)

    if all(results):
        print("✅✅✅ ALL VALIDATIONS PASSED ✅✅✅")
        print()
        print("Graph is valid and ready for enrichment!")
        print()
        sys.exit(0)
    else:
        failed_count = len([r for r in results if not r])
        print(f"❌ {failed_count}/{len(results)} validations failed")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
