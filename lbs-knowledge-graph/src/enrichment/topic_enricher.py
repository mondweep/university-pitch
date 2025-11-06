"""
Topic Enricher - Orchestrator for Topic Extraction

Loads graph, extracts topics, creates nodes and relationships.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

from .llm_client import LLMClient, LLMProvider
from .topic_extractor import TopicExtractor
from .has_topic_builder import HasTopicBuilder
from .topic_models import TopicStatistics

logger = logging.getLogger(__name__)


class TopicEnricher:
    """
    Orchestrate topic extraction and graph enrichment.

    Workflow:
    1. Load graph from Phase 2
    2. Extract topics from Page and Section nodes
    3. Create Topic nodes
    4. Create HAS_TOPIC relationships
    5. Export enriched graph
    """

    def __init__(
        self,
        graph,
        llm_client: LLMClient,
        min_relevance: float = 0.7,
        batch_size: int = 50
    ):
        """
        Initialize topic enricher.

        Args:
            graph: MGraph instance
            llm_client: LLM client for API calls
            min_relevance: Minimum relevance threshold
            batch_size: Batch size for extraction
        """
        self.graph = graph
        self.llm_client = llm_client
        self.min_relevance = min_relevance
        self.batch_size = batch_size

        # Initialize components
        self.extractor = TopicExtractor(
            llm_client=llm_client,
            min_relevance=min_relevance
        )
        self.builder = HasTopicBuilder(graph=graph)

        # Statistics
        self.stats = TopicStatistics()

        logger.info("Initialized TopicEnricher")

    async def extract_topics_from_nodes(
        self,
        node_type: str,
        max_nodes: Optional[int] = None
    ) -> List[Dict]:
        """
        Extract topics from nodes of a specific type.

        Args:
            node_type: Node type (Page or Section)
            max_nodes: Optional limit on number of nodes

        Returns:
            List of extraction results
        """
        logger.info(f"Extracting topics from {node_type} nodes...")

        # Get nodes from graph
        nodes = self.graph.get_nodes_by_type(node_type)

        if max_nodes:
            nodes = nodes[:max_nodes]

        logger.info(f"Found {len(nodes)} {node_type} nodes")

        # Prepare extraction items
        items = []
        for node in nodes:
            props = node.get('properties', {})

            # Get text content
            text = props.get('title', '')
            if props.get('description'):
                text += '\n' + props.get('description')

            # For sections, also include heading
            if node_type == 'Section' and props.get('heading'):
                text = props.get('heading') + '\n' + text

            # Context
            context = {
                'source_id': node['id'],
                'source_type': node_type,
                'page_type': props.get('type', 'unknown')
            }

            items.append({
                'text': text,
                'context': context,
                'node': node
            })

        # Extract topics in batches
        logger.info(f"Extracting topics from {len(items)} items (batch_size={self.batch_size})")

        extraction_results = await self.extractor.extract_batch(
            items=items,
            batch_size=self.batch_size
        )

        # Update statistics
        self.stats.items_processed += len(items)

        return extraction_results

    def build_topic_graph(self, extraction_results: List) -> None:
        """
        Build Topic nodes and HAS_TOPIC edges from extraction results.

        Args:
            extraction_results: List of TopicExtractionResult objects
        """
        logger.info("Building topic graph...")

        # Prepare extractions for builder
        extractions = []

        for result in extraction_results:
            # Get all extracted topics for this source
            topics = []
            for topic_data in result.topics:
                # Find or create Topic object
                topic = self.extractor.get_topic_by_name(topic_data['name'])
                if topic:
                    topics.append(topic)

            if topics:
                extractions.append({
                    'source_node_id': result.source_id,
                    'topics': topics
                })

        # Build topic graph
        self.builder.build_topic_graph(extractions)

        # Update statistics
        builder_stats = self.builder.get_stats()
        self.stats.total_topics = builder_stats['total_topics']
        self.stats.total_assignments = builder_stats['edges_created']

    async def enrich_graph(
        self,
        process_pages: bool = True,
        process_sections: bool = True,
        max_pages: Optional[int] = None,
        max_sections: Optional[int] = None
    ) -> TopicStatistics:
        """
        Run complete topic enrichment pipeline.

        Args:
            process_pages: Whether to process Page nodes
            process_sections: Whether to process Section nodes
            max_pages: Optional limit on Page nodes
            max_sections: Optional limit on Section nodes

        Returns:
            TopicStatistics with results
        """
        start_time = datetime.now()

        logger.info("=== STARTING TOPIC ENRICHMENT ===")

        # Extract topics from Pages
        if process_pages:
            logger.info("Phase 1: Extracting topics from Pages...")
            page_results = await self.extract_topics_from_nodes('Page', max_pages)
            self.build_topic_graph(page_results)

        # Extract topics from Sections
        if process_sections:
            logger.info("Phase 2: Extracting topics from Sections...")
            section_results = await self.extract_topics_from_nodes('Section', max_sections)
            self.build_topic_graph(section_results)

        # Calculate statistics
        self.stats.processing_time = (datetime.now() - start_time).total_seconds()

        # Get extractor stats
        extractor_stats = self.extractor.get_stats()
        self.stats.topics_by_category = extractor_stats['topics_by_category']

        # Calculate averages
        if self.stats.items_processed > 0:
            self.stats.avg_topics_per_item = (
                self.stats.total_assignments / self.stats.items_processed
            )

        # Get LLM stats
        llm_stats = self.llm_client.get_stats()
        self.stats.total_api_calls = llm_stats['api_calls']
        self.stats.estimated_cost = llm_stats['total_cost']

        logger.info("=== TOPIC ENRICHMENT COMPLETE ===")
        self._print_stats()

        return self.stats

    def _print_stats(self) -> None:
        """Print enrichment statistics"""
        logger.info("=== TOPIC ENRICHMENT STATISTICS ===")
        logger.info(f"Total unique topics: {self.stats.total_topics}")
        logger.info(f"Total topic assignments: {self.stats.total_assignments}")
        logger.info(f"Items processed: {self.stats.items_processed}")
        logger.info(f"Average topics per item: {self.stats.avg_topics_per_item:.2f}")
        logger.info(f"Processing time: {self.stats.processing_time:.2f}s")
        logger.info(f"API calls: {self.stats.total_api_calls}")
        logger.info(f"Estimated cost: ${self.stats.estimated_cost:.2f}")
        logger.info("Topics by category:")
        for category, count in self.stats.topics_by_category.items():
            logger.info(f"  {category}: {count}")

    def export_enriched_graph(self, output_path: Path) -> None:
        """
        Export enriched graph with topics.

        Args:
            output_path: Output file path
        """
        logger.info(f"Exporting enriched graph to {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export graph
        self.graph.save(str(output_path))

        logger.info(f"Enriched graph saved: {output_path}")

    def generate_report(self, output_path: Path) -> None:
        """
        Generate topic distribution report.

        Args:
            output_path: Output file path
        """
        logger.info(f"Generating topic report: {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get all topics
        topics = self.extractor.get_all_topics()

        # Sort by frequency
        topics.sort(key=lambda t: t.frequency, reverse=True)

        # Build report
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': {
                'total_topics': self.stats.total_topics,
                'total_assignments': self.stats.total_assignments,
                'items_processed': self.stats.items_processed,
                'avg_topics_per_item': self.stats.avg_topics_per_item,
                'processing_time': self.stats.processing_time,
                'api_calls': self.stats.total_api_calls,
                'estimated_cost': self.stats.estimated_cost
            },
            'topics_by_category': self.stats.topics_by_category,
            'top_topics': [
                {
                    'name': t.name,
                    'category': t.category.value,
                    'frequency': t.frequency,
                    'importance': t.importance,
                    'discipline': t.discipline.value if t.discipline else None,
                    'theme': t.theme.value if t.theme else None
                }
                for t in topics[:50]  # Top 50 topics
            ],
            'all_topics': [
                {
                    'name': t.name,
                    'category': t.category.value,
                    'frequency': t.frequency,
                    'importance': t.importance
                }
                for t in topics
            ]
        }

        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Topic report saved: {output_path}")

    def get_statistics(self) -> TopicStatistics:
        """Get enrichment statistics"""
        return self.stats
