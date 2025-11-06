"""
Topic Analysis for Knowledge Graph

Analyzes topic distribution, identifies trending/niche topics,
and calculates co-occurrence statistics.
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Set
from collections import Counter, defaultdict
from dataclasses import dataclass

from ..graph.mgraph_compat import MGraph, MNode

logger = logging.getLogger(__name__)


@dataclass
class TopicStats:
    """Topic statistics"""
    topic_id: str
    topic_name: str
    frequency: int  # Number of pages containing topic
    avg_position: float  # Average position in page (0-1, lower = earlier)
    co_occurrence_count: int  # Number of topics that co-occur with this one
    centrality: float  # Topic centrality score


class TopicAnalysis:
    """
    Analyze topic distribution and relationships in knowledge graph.
    """

    def __init__(self, graph: MGraph):
        """
        Initialize topic analysis.

        Args:
            graph: Knowledge graph instance
        """
        self.graph = graph
        logger.info("Initialized TopicAnalysis")

    def analyze_distribution(self) -> Dict:
        """
        Analyze topic frequency distribution across pages.

        Returns:
            Dictionary with distribution statistics
        """
        topic_nodes = self.graph.query(node_type='Topic')

        if not topic_nodes:
            logger.warning("No topics found in graph")
            return {}

        # Count pages per topic (via HAS_TOPIC edges)
        frequencies = []
        for topic in topic_nodes:
            has_topic_edges = self.graph.get_edges(to_node_id=topic.id, edge_type='HAS_TOPIC')
            frequency = len(has_topic_edges)
            frequencies.append(frequency)

        frequencies = np.array(frequencies)

        distribution = {
            'total_topics': len(topic_nodes),
            'total_frequency': int(frequencies.sum()),
            'avg_frequency': float(frequencies.mean()),
            'median_frequency': float(np.median(frequencies)),
            'std_frequency': float(frequencies.std()),
            'min_frequency': int(frequencies.min()),
            'max_frequency': int(frequencies.max()),
            'unique_topics': len([f for f in frequencies if f == 1]),
            'common_topics': len([f for f in frequencies if f >= 5]),
        }

        logger.info(
            f"Topic distribution: {distribution['total_topics']} topics, "
            f"avg freq={distribution['avg_frequency']:.2f}, "
            f"{distribution['unique_topics']} unique, "
            f"{distribution['common_topics']} common (5+)"
        )

        return distribution

    def find_trending_topics(self, threshold: int = 5) -> List[TopicStats]:
        """
        Identify trending topics (high frequency, high centrality).

        Args:
            threshold: Minimum frequency to be considered trending

        Returns:
            List of trending topic statistics
        """
        topic_nodes = self.graph.query(node_type='Topic')
        trending = []

        for topic in topic_nodes:
            # Count pages containing topic
            has_topic_edges = self.graph.get_edges(to_node_id=topic.id, edge_type='HAS_TOPIC')
            frequency = len(has_topic_edges)

            if frequency < threshold:
                continue

            # Calculate average position in pages
            positions = []
            for edge in has_topic_edges:
                position = edge.data.get('position', 0.5)  # Default to middle
                positions.append(position)
            avg_position = np.mean(positions) if positions else 0.5

            # Count co-occurring topics
            co_occurrence_count = len(self.graph.get_edges(from_node_id=topic.id, edge_type='RELATED_TOPIC'))

            # Get centrality
            centrality = topic.data.get('centrality', 0.0)

            stats = TopicStats(
                topic_id=topic.id,
                topic_name=topic.data.get('name', topic.id),
                frequency=frequency,
                avg_position=avg_position,
                co_occurrence_count=co_occurrence_count,
                centrality=centrality
            )

            trending.append(stats)

        # Sort by combined score (frequency * centrality)
        trending.sort(key=lambda t: t.frequency * (1 + t.centrality), reverse=True)

        logger.info(f"Found {len(trending)} trending topics (threshold={threshold})")

        for i, stats in enumerate(trending[:10], 1):
            logger.info(
                f"  {i}. {stats.topic_name} (freq={stats.frequency}, "
                f"cent={stats.centrality:.3f}, co-occ={stats.co_occurrence_count})"
            )

        return trending

    def find_niche_topics(self, max_frequency: int = 2) -> List[TopicStats]:
        """
        Identify niche topics (low frequency but high relevance).

        Args:
            max_frequency: Maximum frequency to be considered niche

        Returns:
            List of niche topic statistics
        """
        topic_nodes = self.graph.query(node_type='Topic')
        niche = []

        for topic in topic_nodes:
            # Count pages containing topic
            has_topic_edges = self.graph.get_edges(to_node_id=topic.id, edge_type='HAS_TOPIC')
            frequency = len(has_topic_edges)

            if frequency > max_frequency:
                continue

            # Calculate average position in pages
            positions = []
            for edge in has_topic_edges:
                position = edge.data.get('position', 0.5)
                positions.append(position)
            avg_position = np.mean(positions) if positions else 0.5

            # Count co-occurring topics
            co_occurrence_count = len(self.graph.get_edges(from_node_id=topic.id, edge_type='RELATED_TOPIC'))

            # Get centrality
            centrality = topic.data.get('centrality', 0.0)

            stats = TopicStats(
                topic_id=topic.id,
                topic_name=topic.data.get('name', topic.id),
                frequency=frequency,
                avg_position=avg_position,
                co_occurrence_count=co_occurrence_count,
                centrality=centrality
            )

            niche.append(stats)

        # Sort by relevance (early position + centrality)
        niche.sort(key=lambda t: (1 - t.avg_position) * (1 + t.centrality), reverse=True)

        logger.info(f"Found {len(niche)} niche topics (max_freq={max_frequency})")

        for i, stats in enumerate(niche[:10], 1):
            logger.info(
                f"  {i}. {stats.topic_name} (freq={stats.frequency}, "
                f"pos={stats.avg_position:.2f}, cent={stats.centrality:.3f})"
            )

        return niche

    def calculate_cooccurrence(self) -> np.ndarray:
        """
        Generate topic co-occurrence matrix.

        Counts how many pages contain both topic A and topic B.

        Returns:
            NxN co-occurrence matrix (N = number of topics)
        """
        topic_nodes = self.graph.query(node_type='Topic')
        n_topics = len(topic_nodes)

        if n_topics == 0:
            return np.array([])

        # Create topic ID to index mapping
        topic_to_idx = {topic.id: i for i, topic in enumerate(topic_nodes)}
        idx_to_topic = {i: topic for i, topic in enumerate(topic_nodes)}

        # Initialize co-occurrence matrix
        cooccurrence = np.zeros((n_topics, n_topics), dtype=int)

        # Get all pages
        page_nodes = self.graph.query(node_type='Page')

        for page in page_nodes:
            # Get all topics in this page
            topic_edges = self.graph.get_edges(from_node_id=page.id, edge_type='HAS_TOPIC')
            page_topics = [edge.to_node for edge in topic_edges]

            # Update co-occurrence counts
            for i, topic1 in enumerate(page_topics):
                if topic1 not in topic_to_idx:
                    continue
                idx1 = topic_to_idx[topic1]

                for topic2 in page_topics[i:]:  # Include diagonal (self co-occurrence)
                    if topic2 not in topic_to_idx:
                        continue
                    idx2 = topic_to_idx[topic2]

                    cooccurrence[idx1, idx2] += 1
                    if idx1 != idx2:  # Symmetric matrix
                        cooccurrence[idx2, idx1] += 1

        logger.info(
            f"Calculated {n_topics}x{n_topics} co-occurrence matrix, "
            f"total co-occurrences={cooccurrence.sum()}"
        )

        return cooccurrence

    def calculate_diversity_metrics(self) -> Dict:
        """
        Calculate topic diversity metrics.

        Metrics include:
        - Topic coverage: % of pages with at least one topic
        - Average topics per page
        - Topic entropy (distribution uniformity)

        Returns:
            Dictionary with diversity metrics
        """
        page_nodes = self.graph.query(node_type='Page')
        topic_nodes = self.graph.query(node_type='Topic')

        if not page_nodes or not topic_nodes:
            return {}

        # Count topics per page
        topics_per_page = []
        pages_with_topics = 0

        for page in page_nodes:
            topic_edges = self.graph.get_edges(from_node_id=page.id, edge_type='HAS_TOPIC')
            num_topics = len(topic_edges)
            topics_per_page.append(num_topics)

            if num_topics > 0:
                pages_with_topics += 1

        # Calculate topic frequency distribution for entropy
        topic_frequencies = []
        for topic in topic_nodes:
            has_topic_edges = self.graph.get_edges(to_node_id=topic.id, edge_type='HAS_TOPIC')
            topic_frequencies.append(len(has_topic_edges))

        # Calculate entropy
        topic_frequencies = np.array(topic_frequencies)
        total_freq = topic_frequencies.sum()

        if total_freq > 0:
            probabilities = topic_frequencies / total_freq
            probabilities = probabilities[probabilities > 0]  # Remove zeros
            entropy = -np.sum(probabilities * np.log2(probabilities))
            max_entropy = np.log2(len(topic_nodes))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        else:
            entropy = 0
            normalized_entropy = 0

        metrics = {
            'total_pages': len(page_nodes),
            'total_topics': len(topic_nodes),
            'topic_coverage': pages_with_topics / len(page_nodes),
            'avg_topics_per_page': np.mean(topics_per_page),
            'median_topics_per_page': np.median(topics_per_page),
            'max_topics_per_page': max(topics_per_page),
            'topic_entropy': float(entropy),
            'normalized_entropy': float(normalized_entropy),
        }

        logger.info(
            f"Diversity metrics: {metrics['topic_coverage']:.1%} coverage, "
            f"{metrics['avg_topics_per_page']:.2f} topics/page, "
            f"entropy={metrics['normalized_entropy']:.3f}"
        )

        return metrics

    def get_topic_page_mapping(self) -> Dict[str, List[str]]:
        """
        Get mapping of topics to pages that contain them.

        Returns:
            Dictionary mapping topic IDs to list of page IDs
        """
        topic_nodes = self.graph.query(node_type='Topic')
        mapping = {}

        for topic in topic_nodes:
            has_topic_edges = self.graph.get_edges(to_node_id=topic.id, edge_type='HAS_TOPIC')
            page_ids = [edge.from_node for edge in has_topic_edges]
            mapping[topic.id] = page_ids

        return mapping

    def get_page_topic_mapping(self) -> Dict[str, List[str]]:
        """
        Get mapping of pages to topics they contain.

        Returns:
            Dictionary mapping page IDs to list of topic IDs
        """
        page_nodes = self.graph.query(node_type='Page')
        mapping = {}

        for page in page_nodes:
            topic_edges = self.graph.get_edges(from_node_id=page.id, edge_type='HAS_TOPIC')
            topic_ids = [edge.to_node for edge in topic_edges]
            mapping[page.id] = topic_ids

        return mapping

    def export_analysis_report(self, output_path: str) -> None:
        """
        Export comprehensive topic analysis report.

        Args:
            output_path: Output file path for report
        """
        from pathlib import Path
        import json

        # Gather all statistics
        distribution = self.analyze_distribution()
        trending = self.find_trending_topics(threshold=5)
        niche = self.find_niche_topics(max_frequency=2)
        diversity = self.calculate_diversity_metrics()

        # Create report
        report = {
            'distribution': distribution,
            'diversity': diversity,
            'trending_topics': [
                {
                    'topic_id': t.topic_id,
                    'name': t.topic_name,
                    'frequency': t.frequency,
                    'centrality': t.centrality,
                    'co_occurrence': t.co_occurrence_count
                }
                for t in trending[:20]
            ],
            'niche_topics': [
                {
                    'topic_id': t.topic_id,
                    'name': t.topic_name,
                    'frequency': t.frequency,
                    'avg_position': t.avg_position,
                    'centrality': t.centrality
                }
                for t in niche[:20]
            ],
        }

        # Write report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Exported topic analysis report to {output_path}")
