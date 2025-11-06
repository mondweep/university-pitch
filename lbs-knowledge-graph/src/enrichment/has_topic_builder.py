"""
HAS_TOPIC Relationship Builder

Creates Topic nodes and HAS_TOPIC edges from Page/Section to Topic.
"""

from typing import List, Dict, Set, Optional
from datetime import datetime
import uuid

from mgraph import MGraph
from .topic_models import Topic, TopicRelevance, TopicCategory, TopicExtractionResult


class HasTopicBuilder:
    """
    Build HAS_TOPIC relationships in the knowledge graph.

    Creates Topic nodes and edges from Page/Section nodes to Topics.
    """

    def __init__(self, graph: MGraph):
        """
        Initialize HAS_TOPIC builder.

        Args:
            graph: MGraph instance
        """
        self.graph = graph
        self.topics_created = 0
        self.edges_created = 0
        self.topics_cache: Dict[str, Dict] = {}  # topic_id -> topic_node

    def build_from_extraction_results(
        self,
        results: List[TopicExtractionResult],
        overwrite: bool = False
    ) -> Dict:
        """
        Build HAS_TOPIC relationships from extraction results.

        Args:
            results: List of TopicExtractionResult objects
            overwrite: If True, remove existing HAS_TOPIC edges first

        Returns:
            Statistics dictionary
        """
        print(f"\n🔨 Building HAS_TOPIC relationships...")
        print(f"   Processing {len(results)} extraction results")

        if overwrite:
            self._clear_existing_topics()

        # Create all unique topics first
        all_topics = self._collect_all_topics(results)
        self._create_topic_nodes(all_topics)

        # Create edges from pages to topics
        for result in results:
            self._create_edges_for_result(result)

        stats = {
            'topics_created': self.topics_created,
            'edges_created': self.edges_created,
            'results_processed': len(results)
        }

        print(f"\n✅ HAS_TOPIC build complete:")
        print(f"   • {self.topics_created} topics created")
        print(f"   • {self.edges_created} edges created")

        return stats

    def _collect_all_topics(self, results: List[TopicExtractionResult]) -> List[Dict]:
        """
        Collect all unique topics from results.

        Args:
            results: Extraction results

        Returns:
            List of unique topic dictionaries
        """
        topics_map: Dict[str, Dict] = {}

        for result in results:
            for topic_data in result.topics:
                topic_id = topic_data['id']

                if topic_id not in topics_map:
                    topics_map[topic_id] = topic_data
                else:
                    # Merge: use higher relevance, accumulate pages
                    existing = topics_map[topic_id]
                    if topic_data['relevance'] > existing['relevance']:
                        existing['relevance'] = topic_data['relevance']

        return list(topics_map.values())

    def _create_topic_nodes(self, topics: List[Dict]) -> None:
        """
        Create Topic nodes in the graph.

        Args:
            topics: List of topic dictionaries
        """
        print(f"\n📝 Creating {len(topics)} topic nodes...")

        for topic_data in topics:
            # Check if topic already exists
            existing = self.graph.search_nodes(
                node_type="Topic",
                filters={'id': topic_data['id']},
                limit=1
            )

            if existing:
                # Update existing topic
                topic_node = existing[0]
                self.topics_cache[topic_data['id']] = topic_node
                continue

            # Create new topic node
            topic_node = {
                'id': topic_data['id'],
                'name': topic_data['name'],
                'category': topic_data['category'],
                'frequency': 1,
                'importance': topic_data['relevance'],
                'source': topic_data['source'],
                'extracted_at': datetime.now().isoformat(),
                'keywords': [topic_data['name']],
                'aliases': [topic_data.get('original_name', topic_data['name'])]
            }

            # Add discipline if present
            if 'discipline' in topic_data:
                topic_node['discipline'] = topic_data['discipline']

            # Add theme if present
            if 'theme' in topic_data:
                topic_node['theme'] = topic_data['theme']

            # Create node in graph
            self.graph.add_node(
                node_id=topic_node['id'],
                node_type="Topic",
                data=topic_node
            )

            self.topics_cache[topic_data['id']] = topic_node
            self.topics_created += 1

        print(f"   ✅ Created {self.topics_created} new topics")

    def _create_edges_for_result(self, result: TopicExtractionResult) -> None:
        """
        Create HAS_TOPIC edges for a single extraction result.

        Args:
            result: TopicExtractionResult
        """
        source_id = result.source_id
        source_type = result.source_type

        for topic_data in result.topics:
            topic_id = topic_data['id']

            # Create HAS_TOPIC edge
            edge_props = {
                'relationship_type': 'HAS_TOPIC',
                'relevance': topic_data['relevance'],
                'confidence': topic_data['confidence'],
                'extracted_by': topic_data['model'],
                'created_at': datetime.now().isoformat(),
                'source': topic_data['source']
            }

            # Add edge to graph
            self.graph.add_edge(
                source_id=source_id,
                target_id=topic_id,
                edge_type="HAS_TOPIC",
                data=edge_props
            )

            self.edges_created += 1

    def _clear_existing_topics(self) -> None:
        """Remove existing Topic nodes and HAS_TOPIC edges"""
        print("⚠️  Clearing existing topics and edges...")

        # Get all topic nodes
        topics = self.graph.search_nodes(node_type="Topic")

        for topic in topics:
            self.graph.remove_node(topic['id'])

        print(f"   Removed {len(topics)} existing topics")

    def update_topic_statistics(self) -> Dict:
        """
        Update topic frequency and importance statistics.

        Counts how many times each topic appears and updates importance.

        Returns:
            Statistics dictionary
        """
        print("\n📊 Updating topic statistics...")

        topics = self.graph.search_nodes(node_type="Topic")

        for topic in topics:
            topic_id = topic['id']

            # Count HAS_TOPIC edges
            edges = self.graph.get_edges(target_id=topic_id, edge_type="HAS_TOPIC")
            frequency = len(edges)

            # Calculate average relevance
            if edges:
                avg_relevance = sum(e.get('relevance', 0.5) for e in edges) / len(edges)
            else:
                avg_relevance = 0.5

            # Update topic node
            topic['frequency'] = frequency
            topic['importance'] = avg_relevance

            self.graph.update_node(
                node_id=topic_id,
                data={'frequency': frequency, 'importance': avg_relevance}
            )

        stats = {
            'topics_updated': len(topics),
            'total_edges': sum(topic['frequency'] for topic in topics)
        }

        print(f"   ✅ Updated statistics for {len(topics)} topics")

        return stats

    def get_topic_distribution(self) -> Dict:
        """
        Get distribution of topics by category.

        Returns:
            Dictionary of category -> count
        """
        topics = self.graph.search_nodes(node_type="Topic")

        distribution: Dict[str, int] = {}

        for topic in topics:
            category = topic.get('category', 'general')
            distribution[category] = distribution.get(category, 0) + 1

        return distribution

    def get_top_topics(self, limit: int = 20) -> List[Dict]:
        """
        Get top topics by frequency.

        Args:
            limit: Maximum topics to return

        Returns:
            List of topic dictionaries sorted by frequency
        """
        topics = self.graph.search_nodes(node_type="Topic")

        # Sort by frequency
        sorted_topics = sorted(
            topics,
            key=lambda t: t.get('frequency', 0),
            reverse=True
        )

        return sorted_topics[:limit]
