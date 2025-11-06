#!/usr/bin/env python3
"""
NER Enrichment Script

Extracts named entities from content and builds entity graph.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.mgraph_compat import MGraph
from src.enrichment.ner_extractor import NERExtractor
from src.enrichment.entity_graph_builder import EntityGraphBuilder


async def main():
    """Run NER enrichment"""
    print("🚀 Starting Named Entity Recognition Enrichment...\n")

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return

    # Load graph from existing file
    graph_file = Path(__file__).parent.parent / "data" / "graph" / "graph.json"

    if not graph_file.exists():
        print(f"❌ Error: Graph file not found at {graph_file}")
        print("   Run the scraping and graph building first.")
        return

    print(f"📂 Loading graph from {graph_file}...")
    graph = MGraph()
    graph.load_from_json(str(graph_file))
    print(f"✅ Graph loaded: {graph.node_count()} nodes, {graph.edge_count()} edges\n")

    # Get ContentItem nodes
    print("📂 Loading content items...")
    content_nodes = graph.query(node_type='ContentItem')

    # Filter nodes with content
    content_items = []
    for node in content_nodes:
        content = node.data.get('content', '')
        if content and len(content.strip()) > 0:
            content_items.append({
                'id': node.id,
                'content': content
            })

    print(f"✅ Loaded {len(content_items)} content items with text\n")

    if not content_items:
        print("⚠️  No content items found. Run scraping first.")
        return

    # Initialize NER extractor
    print("🔧 Initializing NER extractor with GPT-4-turbo...")
    extractor = NERExtractor(
        model="gpt-4-turbo",  # High accuracy for NER
        batch_size=30  # Smaller batches for NER (uses more tokens)
    )
    print("✅ NER extractor ready\n")

    # Prepare content items for extraction
    items = [
        {"id": item["id"], "content": item["content"]}
        for item in content_items
    ]

    # Extract entities in batches
    print("🔍 Extracting named entities from content...")
    print(f"   Processing {len(items)} items in batches of 30...")
    results = await extractor.extract_batch(items)

    # Calculate totals
    total_entities = sum(len(r.entities) for r in results)
    total_mentions = sum(len(r.mentions) for r in results)
    total_relationships = sum(len(r.relationships) for r in results)

    print(f"\n✅ Entity extraction complete!")
    print(f"   Entities extracted: {total_entities}")
    print(f"   Mentions found: {total_mentions}")
    print(f"   Relationships identified: {total_relationships}")

    # Get extraction stats
    stats = extractor.get_stats()
    print(f"\n💰 API Usage:")
    print(f"   Model: {stats['model']}")
    print(f"   API calls: {stats['api_calls']}")
    print(f"   Total tokens: {stats['total_tokens']:,}")
    print(f"   Avg tokens/call: {stats['avg_tokens_per_call']:.0f}")
    print(f"   Total cost: ${stats['total_cost']:.2f}")

    # Build entity graph
    print("\n🏗️  Building entity graph...")
    builder = EntityGraphBuilder(graph)
    build_stats = builder.build_entities(results)

    print(f"✅ Graph building complete!")
    print(f"   Entities created: {build_stats['entities_created']}")
    print(f"   Entities updated (merged): {build_stats['entities_updated']}")
    print(f"   Mentions (edges) created: {build_stats['mentions_created']}")
    print(f"   Relationships created: {build_stats['relationships_created']}")

    # Get entity statistics
    entity_stats = builder.get_entity_stats()
    print(f"\n📊 Entity Statistics:")
    print(f"   Total unique entities: {entity_stats['total_entities']}")
    print(f"   People (PERSON): {entity_stats.get('PERSON', 0)}")
    print(f"   Organizations: {entity_stats.get('ORGANIZATION', 0)}")
    print(f"   Locations: {entity_stats.get('LOCATION', 0)}")
    print(f"   Events: {entity_stats.get('EVENT', 0)}")

    # Get top entities
    print(f"\n🌟 Top 15 Entities by Prominence:")
    top_entities = builder.get_top_entities(limit=15)
    for i, entity in enumerate(top_entities, 1):
        print(f"   {i:2d}. {entity['name']} ({entity['entity_type']})")
        print(f"       Mentions: {entity['mention_count']}, Prominence: {entity['prominence']:.2f}")

    # Save statistics
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)

    stats_data = {
        "extraction": {
            "total_entities": total_entities,
            "total_mentions": total_mentions,
            "total_relationships": total_relationships,
            "unique_entities": entity_stats['total_entities'],
            "api_stats": stats
        },
        "graph": {
            **build_stats,
            **entity_stats
        },
        "top_entities": top_entities[:15]
    }

    stats_file = output_dir / "ner_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats_data, f, indent=2)

    print(f"\n💾 Statistics saved to {stats_file}")

    # Summary
    print(f"\n{'='*60}")
    print("📋 NER ENRICHMENT SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Extracted {entity_stats['total_entities']} unique entities")
    print(f"✅ Created {build_stats['mentions_created']} MENTIONS relationships")
    print(f"✅ Identified {build_stats['relationships_created']} entity relationships")
    print(f"💰 Cost: ${stats['total_cost']:.2f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
