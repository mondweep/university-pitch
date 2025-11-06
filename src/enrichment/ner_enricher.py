"""
NER Enricher Orchestrator

Orchestrates the complete NER enrichment pipeline:
1. Extract entities from ContentItems
2. Create Entity nodes (deduplicated)
3. Create MENTIONS edges
4. Track statistics and costs
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Import from lbs-knowledge-graph if available, otherwise use local
try:
    from lbs_knowledge_graph.src.enrichment.ner_extractor import NERExtractor
    from lbs_knowledge_graph.src.enrichment.entity_models import Entity, EntityMention
except ImportError:
    import sys
    sys.path.append("/workspaces/university-pitch/lbs-knowledge-graph/src")
    from enrichment.ner_extractor import NERExtractor
    from enrichment.entity_models import Entity, EntityMention

from .entity_node_builder import EntityNodeBuilder
from .mentions_builder import MentionsBuilder

logger = logging.getLogger(__name__)


class NEREnricher:
    """
    Complete NER enrichment orchestrator.

    Processes knowledge graph to extract named entities and create
    Entity nodes and MENTIONS edges.
    """

    def __init__(
        self,
        graph,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo",
        batch_size: int = 10
    ):
        """
        Initialize NER enricher.

        Args:
            graph: MGraph instance
            api_key: OpenAI API key (optional, uses env var)
            model: Model to use for extraction
            batch_size: Batch size for parallel processing
        """
        self.graph = graph
        self.extractor = NERExtractor(
            api_key=api_key,
            model=model,
            batch_size=batch_size
        )
        self.entity_builder = EntityNodeBuilder(graph)
        self.mentions_builder = MentionsBuilder(graph, self.entity_builder)

        self.stats = {
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "content_items_processed": 0,
            "entities_extracted": 0,
            "unique_entities": 0,
            "mentions_created": 0,
            "total_cost": 0.0,
            "model_used": model
        }

    async def enrich_graph(
        self,
        max_items: Optional[int] = None,
        content_filter: Optional[Dict] = None
    ) -> Dict:
        """
        Run complete NER enrichment pipeline.

        Args:
            max_items: Maximum content items to process (for testing)
            content_filter: Optional filter for content items

        Returns:
            Statistics dictionary
        """
        logger.info("🚀 Starting NER enrichment pipeline...")
        self.stats["start_time"] = datetime.now()

        # Step 1: Get ContentItems from graph
        content_items = self._get_content_items(max_items, content_filter)
        logger.info(f"📄 Found {len(content_items)} content items to process")

        if not content_items:
            logger.warning("No content items found to process")
            return self.stats

        # Step 2: Extract entities
        logger.info("🔍 Extracting entities using GPT-4...")
        extraction_results = await self.extractor.extract_batch(content_items)

        # Aggregate results
        all_entities = []
        all_mentions = []

        for result in extraction_results:
            all_entities.extend([e.to_dict() for e in result.entities])
            all_mentions.extend([m.to_dict() for m in result.mentions])
            self.stats["total_cost"] += result.cost

        self.stats["content_items_processed"] = len(content_items)
        self.stats["entities_extracted"] = len(all_entities)

        logger.info(f"✅ Extracted {len(all_entities)} entities (before deduplication)")

        # Step 3: Create Entity nodes
        logger.info("🔨 Creating Entity nodes...")
        entity_stats = self.entity_builder.add_entities(all_entities)
        self.stats["unique_entities"] = entity_stats["unique_entities"]
        self.stats["merged_entities"] = entity_stats["merged_entities"]

        # Step 4: Create MENTIONS edges
        logger.info("🔗 Creating MENTIONS edges...")
        mentions_stats = self.mentions_builder.add_mentions(all_mentions)
        self.stats["mentions_created"] = mentions_stats["edges_created"]

        # Finalize stats
        self.stats["end_time"] = datetime.now()
        self.stats["duration"] = (
            self.stats["end_time"] - self.stats["start_time"]
        ).total_seconds()

        # Get extractor stats
        extractor_stats = self.extractor.get_stats()
        self.stats["api_calls"] = extractor_stats["api_calls"]
        self.stats["total_tokens"] = extractor_stats["total_tokens"]

        logger.info(f"""
✅ NER Enrichment Complete!

📊 Statistics:
- Content Items: {self.stats['content_items_processed']}
- Entities Extracted: {self.stats['entities_extracted']}
- Unique Entities: {self.stats['unique_entities']}
- Merged Entities: {self.stats['merged_entities']}
- MENTIONS Edges: {self.stats['mentions_created']}

💰 Cost:
- API Calls: {self.stats['api_calls']}
- Total Tokens: {self.stats['total_tokens']:,}
- Total Cost: ${self.stats['total_cost']:.2f}

⏱️ Duration: {self.stats['duration']:.1f}s
""")

        return self.stats

    def _get_content_items(
        self,
        max_items: Optional[int] = None,
        content_filter: Optional[Dict] = None
    ) -> List[Dict[str, str]]:
        """
        Get ContentItems from graph for NER processing.

        Args:
            max_items: Maximum items to retrieve
            content_filter: Optional filter criteria

        Returns:
            List of dicts with 'id' and 'content' keys
        """
        # Query ContentItem nodes
        content_nodes = self.graph.query(node_type="ContentItem")

        items = []
        for node in content_nodes:
            # Check if already enriched with entities
            # (skip if MENTIONS edges already exist)
            mentions = list(self.graph.get_edges(
                from_node_id=node.id,
                edge_type="MENTIONS"
            ))

            if mentions:
                # Already enriched, skip
                continue

            # Get text content
            text = node.data.get("text", "")
            if not text or len(text) < 50:
                # Skip very short content
                continue

            items.append({
                "id": node.id,
                "content": text
            })

            if max_items and len(items) >= max_items:
                break

        return items

    def get_enrichment_report(self) -> Dict:
        """
        Get detailed enrichment report.

        Returns:
            Detailed report dictionary
        """
        report = {
            "pipeline_stats": self.stats,
            "entity_stats": self.entity_builder.get_entity_stats(),
            "mention_stats": self.mentions_builder.get_mention_stats(),
            "validation": self.mentions_builder.validate_mentions()
        }

        return report

    def save_stats(self, output_path: Path):
        """
        Save enrichment statistics to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        stats = self.stats.copy()

        # Convert datetime to string
        if stats.get("start_time"):
            stats["start_time"] = stats["start_time"].isoformat()
        if stats.get("end_time"):
            stats["end_time"] = stats["end_time"].isoformat()

        with open(output_path, "w") as f:
            json.dump(stats, f, indent=2)

        logger.info(f"💾 Stats saved to {output_path}")


async def run_ner_enrichment(
    graph,
    api_key: Optional[str] = None,
    model: str = "gpt-4-turbo",
    batch_size: int = 10,
    max_items: Optional[int] = None
) -> Dict:
    """
    Convenience function to run NER enrichment.

    Args:
        graph: MGraph instance
        api_key: OpenAI API key
        model: Model to use
        batch_size: Batch size
        max_items: Max items to process

    Returns:
        Statistics dictionary
    """
    enricher = NEREnricher(graph, api_key, model, batch_size)
    return await enricher.enrich_graph(max_items=max_items)
