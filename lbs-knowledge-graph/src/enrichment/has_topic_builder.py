"""
HAS_TOPIC Relationship Builder

Creates Topic nodes and HAS_TOPIC edges in the knowledge graph.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    from mgraph import MGraph
except ImportError:
    # Fallback for testing
    MGraph = None

from .topic_models import Topic, TopicRelevance, TopicExtractionResult

logger = logging.getLogger(__name__)


class HasTopicBuilder:
    """
    Build Topic nodes and HAS_TOPIC relationships in knowledge graph.

    Features:
    - Create/update Topic nodes
    - Build HAS_TOPIC edges with relevance scores
    - Support multi-topic relationships
    - Handle topic hierarchy
    """

    def __init__(self, graph: MGraph):
        """
        Initialize HAS_TOPIC builder.

        Args:
            graph: MGraph database instance
        """
        if graph is None:
            raise ValueError("MGraph instance is required")

        self.graph = graph

        # Track created topics
        self.topic_nodes: Dict[str, str] = {}  # name -> node_id
        self.topic_stats = {
            'topics_created': 0,
            'topics_updated': 0,
            'edges_created': 0
        }

        logger.info("Initialized HasTopicBuilder")

    def create_topic_node(self, topic: Topic) -> str:
        """
        Create or update Topic node in graph.

        Args:
            topic: Topic object

        Returns:
            Topic node ID
        """
        # Check if topic already exists
        if topic.name in self.topic_nodes:
            # Update existing topic
            node_id = self.topic_nodes[topic.name]

            # Update frequency and importance
            self.graph.update_node(
                node_id=node_id,
                properties={
                    'frequency': topic.frequency,
                    'importance': topic.importance
                }
            )

            self.topic_stats['topics_updated'] += 1
            logger.debug(f"Updated topic: {topic.name} (frequency={topic.frequency})")

            return node_id

        # Create new topic node
        node_id = self.graph.add_node(
            node_type='Topic',
            properties={
                'id': topic.id,
                'name': topic.name,
                'slug': topic.name.lower().replace(' ', '-'),
                'description': topic.description or '',
                'category': topic.category.value,
                'discipline': topic.discipline.value if topic.discipline else None,
                'theme': topic.theme.value if topic.theme else None,
                'frequency': topic.frequency,
                'importance': topic.importance,
                'aliases': topic.aliases,
                'keywords': topic.keywords,
                'source': topic.source,
                'extracted_at': topic.extracted_at or datetime.now().isoformat()
            }
        )

        self.topic_nodes[topic.name] = node_id
        self.topic_stats['topics_created'] += 1

        logger.info(f"Created topic node: {topic.name} (id={node_id})")

        return node_id

    def create_has_topic_edge(
        self,
        source_id: str,
        topic_id: str,
        relevance: float,
        context: Optional[str] = None
    ) -> str:
        """
        Create HAS_TOPIC relationship.

        Args:
            source_id: Source node ID (Page or Section)
            topic_id: Topic node ID
            relevance: Relevance score (0-1)
            context: Optional context snippet

        Returns:
            Edge ID
        """
        edge_id = self.graph.add_edge(
            from_node=source_id,
            to_node=topic_id,
            edge_type='HAS_TOPIC',
            properties={
                'confidence': relevance,
                'relevance': relevance,
                'source': 'llm',
                'context': context or '',
                'extracted_at': datetime.now().isoformat()
            }
        )

        self.topic_stats['edges_created'] += 1

        logger.debug(f"Created HAS_TOPIC edge: {source_id} -> {topic_id} (relevance={relevance:.2f})")

        return edge_id

    def build_topics_for_source(
        self,
        source_node_id: str,
        topics: List[Topic],
        relevance_scores: Optional[List[float]] = None
    ) -> List[str]:
        """
        Build topics and relationships for a source node.

        Args:
            source_node_id: Source node ID (Page or Section)
            topics: List of Topic objects
            relevance_scores: Optional list of relevance scores (defaults to topic.importance)

        Returns:
            List of created topic node IDs
        """
        if not topics:
            return []

        topic_node_ids = []

        for i, topic in enumerate(topics):
            # Create/update topic node
            topic_node_id = self.create_topic_node(topic)
            topic_node_ids.append(topic_node_id)

            # Get relevance score
            relevance = relevance_scores[i] if relevance_scores else topic.importance

            # Create HAS_TOPIC edge
            self.create_has_topic_edge(
                source_id=source_node_id,
                topic_id=topic_node_id,
                relevance=relevance
            )

        logger.info(f"Built {len(topics)} topics for source: {source_node_id}")

        return topic_node_ids

    def build_topic_graph(
        self,
        extractions: List[Dict]
    ) -> MGraph:
        """
        Build complete topic graph from extraction results.

        Args:
            extractions: List of dicts with:
                - source_node_id: Source node ID
                - topics: List of Topic objects

        Returns:
            Updated MGraph instance
        """
        logger.info(f"Building topic graph from {len(extractions)} extractions")

        for extraction in extractions:
            source_id = extraction['source_node_id']
            topics = extraction['topics']

            self.build_topics_for_source(source_id, topics)

        logger.info(f"Topic graph complete: {self.topic_stats}")

        return self.graph

    def build_topic_hierarchy(self, topics: List[Topic]) -> None:
        """
        Build CHILD_OF relationships between topics.

        Args:
            topics: List of Topic objects with parent_topic_id set
        """
        hierarchy_count = 0

        for topic in topics:
            if topic.parent_topic_id:
                # Find parent topic node
                parent_node_id = None
                for name, node_id in self.topic_nodes.items():
                    parent_topic = next(
                        (t for t in topics if t.id == topic.parent_topic_id),
                        None
                    )
                    if parent_topic and name == parent_topic.name:
                        parent_node_id = node_id
                        break

                if parent_node_id:
                    topic_node_id = self.topic_nodes[topic.name]

                    # Create CHILD_OF edge
                    self.graph.add_edge(
                        from_node=topic_node_id,
                        to_node=parent_node_id,
                        edge_type='CHILD_OF',
                        properties={}
                    )

                    hierarchy_count += 1

        logger.info(f"Built {hierarchy_count} topic hierarchy relationships")

    def link_related_topics(self, topics: List[Topic]) -> None:
        """
        Build RELATED_TO relationships between topics.

        Args:
            topics: List of Topic objects with related_topics set
        """
        relation_count = 0

        for topic in topics:
            if not topic.related_topics:
                continue

            topic_node_id = self.topic_nodes.get(topic.name)
            if not topic_node_id:
                continue

            for related_topic_id in topic.related_topics:
                # Find related topic node
                related_node_id = None
                for name, node_id in self.topic_nodes.items():
                    related_topic = next(
                        (t for t in topics if t.id == related_topic_id),
                        None
                    )
                    if related_topic and name == related_topic.name:
                        related_node_id = node_id
                        break

                if related_node_id:
                    # Create RELATED_TO edge (bidirectional)
                    self.graph.add_edge(
                        from_node=topic_node_id,
                        to_node=related_node_id,
                        edge_type='RELATED_TO',
                        properties={}
                    )

                    relation_count += 1

        logger.info(f"Built {relation_count} topic relation relationships")

    def get_stats(self) -> Dict:
        """Get builder statistics"""
        return {
            **self.topic_stats,
            'total_topics': len(self.topic_nodes)
        }

    def export_topics(self) -> List[Dict]:
        """Export all topics as dictionaries"""
        topics = []

        for name, node_id in self.topic_nodes.items():
            node_data = self.graph.get_node(node_id)
            topics.append({
                'node_id': node_id,
                'name': name,
                **node_data.get('properties', {})
            })

        return topics
