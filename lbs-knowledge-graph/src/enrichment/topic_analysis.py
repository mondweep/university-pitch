"""
Topic Analysis for Knowledge Graph Insights

Analyzes topic distribution, co-occurrence, and trends.
Generates insights for topic clustering visualization.
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Set
from collections import Counter, defaultdict
from dataclasses import dataclass

from .topic_models import Topic

logger = logging.getLogger(__name__)


@dataclass
class TopicInsight:
    """Insight about topic usage and patterns."""
    topic_id: str
    topic_name: str
    frequency: int
    importance: float
    category: str
    co_occurring_topics: List[Tuple[str, int]]
    pages_count: int
    trend: str  # 'rising', 'stable', 'declining'


class TopicAnalyzer:
    """
    Analyze topic patterns and generate insights.

    Features:
    - Topic frequency distribution
    - Topic co-occurrence matrix
    - Trending topics detection
    - Topic coverage analysis
    """

    def __init__(self, topics: List[Topic], page_topics: Dict[str, List[str]]):
        """
        Initialize topic analyzer.

        Args:
            topics: List of all topics
            page_topics: Mapping of page_id -> [topic_ids]
        """
        self.topics = topics
        self.page_topics = page_topics

        # Create topic lookup
        self.topic_map = {t.id: t for t in topics}

        logger.info(
            f"Initialized TopicAnalyzer with {len(topics)} topics, "
            f"{len(page_topics)} pages"
        )

    def calculate_frequency_distribution(self) -> Dict[str, int]:
        """
        Calculate topic frequency across all pages.

        Returns:
            Dictionary of topic_id -> frequency count
        """
        logger.info("Calculating topic frequency distribution...")

        frequency = Counter()

        for page_id, topic_ids in self.page_topics.items():
            frequency.update(topic_ids)

        logger.info(f"Processed {len(self.page_topics)} pages")

        return dict(frequency)

    def calculate_co_occurrence_matrix(
        self,
        min_support: int = 2
    ) -> Dict[Tuple[str, str], int]:
        """
        Calculate topic co-occurrence matrix.

        Args:
            min_support: Minimum co-occurrence count

        Returns:
            Dictionary of (topic_id1, topic_id2) -> co-occurrence count
        """
        logger.info("Calculating topic co-occurrence matrix...")

        co_occurrence = Counter()

        for page_id, topic_ids in self.page_topics.items():
            # Get all pairs of topics on this page
            for i, topic1 in enumerate(topic_ids):
                for topic2 in topic_ids[i + 1:]:
                    # Sort to ensure consistency
                    pair = tuple(sorted([topic1, topic2]))
                    co_occurrence[pair] += 1

        # Filter by minimum support
        filtered = {
            pair: count
            for pair, count in co_occurrence.items()
            if count >= min_support
        }

        logger.info(
            f"Found {len(filtered)} co-occurring topic pairs "
            f"(min support: {min_support})"
        )

        return filtered

    def identify_trending_topics(
        self,
        top_n: int = 10
    ) -> List[TopicInsight]:
        """
        Identify trending topics based on frequency and importance.

        Args:
            top_n: Number of top trending topics

        Returns:
            List of trending topic insights
        """
        logger.info("Identifying trending topics...")

        frequency = self.calculate_frequency_distribution()

        # Calculate composite trend score
        trending_scores = []

        for topic in self.topics:
            freq = frequency.get(topic.id, 0)

            # Composite score: frequency * importance
            score = freq * topic.importance

            trending_scores.append({
                'topic': topic,
                'frequency': freq,
                'score': score
            })

        # Sort by trend score
        trending_scores.sort(key=lambda x: x['score'], reverse=True)

        # Get co-occurring topics for each trending topic
        co_occurrence = self.calculate_co_occurrence_matrix()

        insights = []
        for item in trending_scores[:top_n]:
            topic = item['topic']

            # Get co-occurring topics
            co_occurring = []
            for (topic1, topic2), count in co_occurrence.items():
                if topic1 == topic.id:
                    co_occurring.append((topic2, count))
                elif topic2 == topic.id:
                    co_occurring.append((topic1, count))

            # Sort by co-occurrence count
            co_occurring.sort(key=lambda x: x[1], reverse=True)

            # Count pages
            pages_count = sum(
                1 for topic_ids in self.page_topics.values()
                if topic.id in topic_ids
            )

            # Determine trend (simple heuristic based on score)
            if item['score'] > np.percentile([s['score'] for s in trending_scores], 75):
                trend = 'rising'
            elif item['score'] < np.percentile([s['score'] for s in trending_scores], 25):
                trend = 'declining'
            else:
                trend = 'stable'

            insight = TopicInsight(
                topic_id=topic.id,
                topic_name=topic.name,
                frequency=item['frequency'],
                importance=topic.importance,
                category=topic.category.value,
                co_occurring_topics=co_occurring[:5],
                pages_count=pages_count,
                trend=trend
            )

            insights.append(insight)

        logger.info(f"Identified {len(insights)} trending topics")

        return insights

    def calculate_topic_coverage(self) -> Dict:
        """
        Calculate topic coverage metrics per page.

        Returns:
            Dictionary with coverage statistics
        """
        logger.info("Calculating topic coverage...")

        topics_per_page = [
            len(topic_ids) for topic_ids in self.page_topics.values()
        ]

        coverage = {
            'total_pages': len(self.page_topics),
            'total_topics': len(self.topics),
            'avg_topics_per_page': np.mean(topics_per_page) if topics_per_page else 0,
            'median_topics_per_page': np.median(topics_per_page) if topics_per_page else 0,
            'min_topics_per_page': min(topics_per_page) if topics_per_page else 0,
            'max_topics_per_page': max(topics_per_page) if topics_per_page else 0,
            'pages_without_topics': sum(1 for count in topics_per_page if count == 0)
        }

        logger.info(
            f"Coverage: {coverage['avg_topics_per_page']:.1f} avg topics/page"
        )

        return coverage

    def generate_topic_report(self) -> Dict:
        """
        Generate comprehensive topic analysis report.

        Returns:
            Report dictionary with all analysis results
        """
        logger.info("Generating topic analysis report...")

        frequency = self.calculate_frequency_distribution()
        co_occurrence = self.calculate_co_occurrence_matrix()
        trending = self.identify_trending_topics(top_n=10)
        coverage = self.calculate_topic_coverage()

        # Topic distribution by category
        category_dist = Counter()
        for topic in self.topics:
            category_dist[topic.category.value] += 1

        report = {
            'summary': {
                'total_topics': len(self.topics),
                'total_pages': len(self.page_topics),
                'avg_topics_per_page': coverage['avg_topics_per_page'],
                'total_topic_assignments': sum(frequency.values())
            },
            'frequency_distribution': {
                'top_10_topics': sorted(
                    frequency.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                'distribution': frequency
            },
            'category_distribution': dict(category_dist),
            'co_occurrence': {
                'total_pairs': len(co_occurrence),
                'top_10_pairs': sorted(
                    co_occurrence.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            },
            'trending_topics': [
                {
                    'name': t.topic_name,
                    'frequency': t.frequency,
                    'importance': t.importance,
                    'category': t.category,
                    'trend': t.trend,
                    'pages_count': t.pages_count,
                    'co_occurring': [
                        self.topic_map[tid].name for tid, _ in t.co_occurring_topics[:3]
                    ]
                }
                for t in trending
            ],
            'coverage': coverage
        }

        logger.info("Topic analysis report generated")

        return report

    def export_heatmap_data(
        self,
        top_n: int = 20
    ) -> Tuple[List[str], np.ndarray]:
        """
        Export topic co-occurrence data for heatmap visualization.

        Args:
            top_n: Number of top topics to include

        Returns:
            Tuple of (topic_names, co_occurrence_matrix)
        """
        logger.info(f"Exporting heatmap data for top {top_n} topics...")

        # Get top N most frequent topics
        frequency = self.calculate_frequency_distribution()
        top_topics = sorted(
            frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        topic_ids = [tid for tid, _ in top_topics]
        topic_names = [self.topic_map[tid].name for tid in topic_ids]

        # Calculate co-occurrence for top topics
        co_occurrence = self.calculate_co_occurrence_matrix(min_support=1)

        # Build matrix
        n = len(topic_ids)
        matrix = np.zeros((n, n))

        for i, topic1 in enumerate(topic_ids):
            for j, topic2 in enumerate(topic_ids):
                if i == j:
                    matrix[i, j] = frequency[topic1]
                else:
                    pair = tuple(sorted([topic1, topic2]))
                    matrix[i, j] = co_occurrence.get(pair, 0)

        logger.info(f"Generated {n}x{n} co-occurrence matrix")

        return topic_names, matrix
