#!/usr/bin/env python3
"""
Run Named Entity Recognition

Extracts entities from all content items and builds entity graph.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.mgraph import MGraph
from src.enrichment.ner_extractor import NERExtractor
from src.enrichment.entity_graph_builder import EntityGraphBuilder


async def main():
    """Run NER extraction on all content"""
    print("🚀 Starting Named Entity Recognition...\n")

    # Initialize graph
    graph = MGraph()

    # Load all content items
    print("📂 Loading content items...")
    content_items = graph.query(
        """
        SELECT id, content
        FROM nodes
        WHERE type = 'ContentItem'
        """
    )
    print(f"✅ Loaded {len(content_items)} content items\n")

    if not content_items:
        print("⚠️  No content items found. Run scraping first.")
        return

    # Initialize NER extractor
    print("🔧 Initializing NER extractor...")
    extractor = NERExtractor(
        model="gpt-4-turbo",  # High accuracy model
        batch_size=30  # Process 30 items at a time
    )
    print("✅ NER extractor ready\n")

    # Extract entities
    print("🔍 Extracting entities from content...")
    results = await extractor.extract_batch(content_items)

    # Calculate total entities extracted
    total_entities = sum(len(r.entities) for r in results)
    total_mentions = sum(len(r.mentions) for r in results)
    total_relationships = sum(len(r.relationships) for r in results)

    print(f"\n✅ Extraction complete!")
    print(f"   Entities extracted: {total_entities}")
    print(f"   Mentions found: {total_mentions}")
    print(f"   Relationships identified: {total_relationships}")

    # Get extraction stats
    stats = extractor.get_stats()
    print(f"\n💰 API Usage:")
    print(f"   API calls: {stats['api_calls']}")
    print(f"   Total tokens: {stats['total_tokens']:,}")
    print(f"   Total cost: ${stats['total_cost']:.2f}")
    print(f"   Avg tokens/call: {stats['avg_tokens_per_call']:.0f}")

    # Build entity graph
    print("\n🏗️  Building entity graph...")
    builder = EntityGraphBuilder(graph)
    build_stats = builder.build_entities(results)

    print(f"✅ Graph building complete!")
    print(f"   Entities created: {build_stats['entities_created']}")
    print(f"   Entities updated: {build_stats['entities_updated']}")
    print(f"   Mentions created: {build_stats['mentions_created']}")
    print(f"   Relationships created: {build_stats['relationships_created']}")

    # Get entity statistics
    entity_stats = builder.get_entity_stats()
    print(f"\n📊 Entity Statistics:")
    print(f"   Total entities: {entity_stats['total_entities']}")
    print(f"   People: {entity_stats.get('PERSON', 0)}")
    print(f"   Organizations: {entity_stats.get('ORGANIZATION', 0)}")
    print(f"   Locations: {entity_stats.get('LOCATION', 0)}")
    print(f"   Events: {entity_stats.get('EVENT', 0)}")

    # Get top entities
    print(f"\n🌟 Top 10 Entities by Prominence:")
    top_entities = builder.get_top_entities(limit=10)
    for i, entity in enumerate(top_entities, 1):
        print(f"   {i}. {entity['name']} ({entity['entity_type']})")
        print(f"      Mentions: {entity['mention_count']}, Prominence: {entity['prominence']:.2f}")

    # Save statistics
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)

    stats_data = {
        "extraction": {
            "total_entities": total_entities,
            "total_mentions": total_mentions,
            "total_relationships": total_relationships,
            **stats
        },
        "graph": {
            **build_stats,
            **entity_stats
        },
        "top_entities": top_entities[:10]
    }

    stats_file = output_dir / "ner_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats_data, f, indent=2)

    print(f"\n💾 Statistics saved to {stats_file}")
    print("\n✅ NER extraction complete!")


if __name__ == "__main__":
    asyncio.run(main())
