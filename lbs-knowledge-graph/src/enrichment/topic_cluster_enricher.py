"""
Topic Cluster Enricher - Master Orchestration

Orchestrates complete topic clustering and hierarchy building pipeline.
Coordinates: clustering -> hierarchy -> analysis -> visualization.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.enrichment.topic_clusterer import TopicClusterer, TopicCluster
from src.enrichment.topic_hierarchy_builder import TopicHierarchyBuilder
from src.enrichment.topic_analysis import TopicAnalyzer
from src.enrichment.topic_models import Topic
from src.enrichment.embedding_generator import EmbeddingGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TopicClusterEnricher:
    """
    Master orchestration for topic clustering pipeline.

    Steps:
    1. Load topics from graph
    2. Generate embeddings
    3. Cluster topics (hierarchical clustering)
    4. Build topic hierarchy
    5. Create SUBTOPIC_OF edges
    6. Generate analysis and insights
    7. Export visualizations
    """

    def __init__(
        self,
        neo4j_client=None,
        min_clusters: int = 5,
        max_clusters: int = 10
    ):
        """
        Initialize topic cluster enricher.

        Args:
            neo4j_client: Neo4j client for graph operations
            min_clusters: Minimum number of clusters
            max_clusters: Maximum number of clusters
        """
        self.neo4j_client = neo4j_client
        self.min_clusters = min_clusters
        self.max_clusters = max_clusters

        # Initialize components
        self.embedding_generator = EmbeddingGenerator()
        self.clusterer = None
        self.hierarchy_builder = TopicHierarchyBuilder(neo4j_client)
        self.analyzer = None

        # Results
        self.topics: List[Topic] = []
        self.clusters: Dict[str, TopicCluster] = {}
        self.hierarchy: Dict = {}
        self.analysis_report: Dict = {}

        logger.info("Initialized TopicClusterEnricher")

    def load_topics_from_graph(self) -> List[Topic]:
        """
        Load all topics from Neo4j graph.

        Returns:
            List of Topic objects
        """
        logger.info("Loading topics from graph...")

        if not self.neo4j_client:
            # Use mock data for testing
            logger.warning("No Neo4j client, using mock topics")
            return self._create_mock_topics()

        query = """
        MATCH (t:Topic)
        RETURN t.id AS id, t.name AS name, t.description AS description,
               t.category AS category, t.frequency AS frequency,
               t.importance AS importance
        ORDER BY t.importance DESC, t.frequency DESC
        """

        results = self.neo4j_client.run_query(query)

        topics = []
        for record in results:
            # Convert to Topic object (simplified)
            topic = Topic(
                id=record['id'],
                name=record['name'],
                description=record.get('description'),
                category=record.get('category', 'general'),
                frequency=record.get('frequency', 1),
                importance=record.get('importance', 0.5)
            )
            topics.append(topic)

        logger.info(f"Loaded {len(topics)} topics from graph")

        self.topics = topics
        return topics

    def _create_mock_topics(self) -> List[Topic]:
        """Create mock topics for testing."""
        from .topic_models import TopicCategory

        mock_topics = [
            Topic(id="topic-1", name="MBA Programme", description="Full-time MBA", category=TopicCategory.ACADEMIC, frequency=25, importance=0.95),
            Topic(id="topic-2", name="Executive MBA", description="Part-time EMBA", category=TopicCategory.ACADEMIC, frequency=18, importance=0.9),
            Topic(id="topic-3", name="Masters in Finance", description="MiF programme", category=TopicCategory.ACADEMIC, frequency=15, importance=0.85),
            Topic(id="topic-4", name="Corporate Finance", description="Finance discipline", category=TopicCategory.ACADEMIC, frequency=20, importance=0.8),
            Topic(id="topic-5", name="Marketing Strategy", description="Marketing courses", category=TopicCategory.ACADEMIC, frequency=12, importance=0.75),
            Topic(id="topic-6", name="Alumni Network", description="Alumni community", category=TopicCategory.ALUMNI, frequency=10, importance=0.7),
            Topic(id="topic-7", name="Career Services", description="Career support", category=TopicCategory.CAREER, frequency=14, importance=0.72),
            Topic(id="topic-8", name="Student Clubs", description="Campus clubs", category=TopicCategory.STUDENT_LIFE, frequency=8, importance=0.65),
            Topic(id="topic-9", name="Research Centers", description="Research facilities", category=TopicCategory.RESEARCH, frequency=11, importance=0.78),
            Topic(id="topic-10", name="Faculty Research", description="Academic research", category=TopicCategory.RESEARCH, frequency=13, importance=0.8),
        ]

        return mock_topics

    async def run_clustering_pipeline(self) -> Dict:
        """
        Run complete clustering pipeline.

        Returns:
            Pipeline results and statistics
        """
        logger.info("=" * 60)
        logger.info("STARTING TOPIC CLUSTERING PIPELINE")
        logger.info("=" * 60)

        start_time = datetime.now()

        # Step 1: Load topics
        logger.info("\n[1/7] Loading topics from graph...")
        if not self.topics:
            self.topics = self.load_topics_from_graph()

        # Step 2: Initialize clusterer
        logger.info(f"\n[2/7] Initializing topic clusterer...")
        self.clusterer = TopicClusterer(
            topics=self.topics,
            embedding_generator=self.embedding_generator.generate_embedding,
            min_clusters=self.min_clusters,
            max_clusters=self.max_clusters
        )

        # Step 3: Cluster topics
        logger.info(f"\n[3/7] Clustering topics...")
        self.clusters = self.clusterer.cluster_topics()

        # Step 4: Build hierarchy
        logger.info(f"\n[4/7] Building topic hierarchy...")
        self.hierarchy = self.clusterer.build_topic_hierarchy()

        # Step 5: Create SUBTOPIC_OF edges
        logger.info(f"\n[5/7] Creating SUBTOPIC_OF relationships...")
        relationships = self.hierarchy_builder.build_hierarchy_from_clusters(
            self.hierarchy,
            self.clusters
        )

        # Validate hierarchy
        validation = self.hierarchy_builder.validate_hierarchy()

        # Create edges in graph (if client available)
        if self.neo4j_client:
            edges_created = self.hierarchy_builder.create_edges_in_graph()
        else:
            edges_created = 0
            logger.info("Skipping graph edge creation (no Neo4j client)")

        # Step 6: Analyze topics
        logger.info(f"\n[6/7] Analyzing topic patterns...")
        
        # Create mock page-topic mapping for analysis
        page_topics = self._create_mock_page_topics()
        
        self.analyzer = TopicAnalyzer(
            topics=self.topics,
            page_topics=page_topics
        )
        
        self.analysis_report = self.analyzer.generate_topic_report()

        # Step 7: Export results
        logger.info(f"\n[7/7] Exporting results...")
        self._export_results()

        # Calculate pipeline stats
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        cluster_stats = self.clusterer.get_cluster_stats()

        pipeline_results = {
            'success': True,
            'duration_seconds': duration,
            'topics_processed': len(self.topics),
            'clusters_created': len(self.clusters),
            'cluster_stats': cluster_stats,
            'hierarchy': {
                'root_topics': len(self.hierarchy['root']),
                'primary_topics': len(self.hierarchy['primary']),
                'specific_topics': len(self.hierarchy['specific'])
            },
            'relationships_created': len(relationships),
            'edges_created_in_graph': edges_created,
            'validation': validation,
            'analysis': {
                'total_pages': self.analysis_report['summary']['total_pages'],
                'avg_topics_per_page': self.analysis_report['summary']['avg_topics_per_page']
            }
        }

        logger.info("\n" + "=" * 60)
        logger.info("CLUSTERING PIPELINE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration:.1f}s")
        logger.info(f"Topics processed: {len(self.topics)}")
        logger.info(f"Clusters created: {len(self.clusters)}")
        logger.info(f"Hierarchy levels: {len(self.hierarchy['root'])} root -> {len(self.hierarchy['primary'])} primary -> {len(self.hierarchy['specific'])} specific")
        logger.info(f"Validation: {'PASSED' if validation['valid'] else 'FAILED'}")

        return pipeline_results

    def _create_mock_page_topics(self) -> Dict[str, List[str]]:
        """Create mock page-topic mapping for testing."""
        import random
        
        # Simulate 20 pages with topics
        page_topics = {}
        topic_ids = [t.id for t in self.topics]
        
        for i in range(20):
            page_id = f"page-{i+1}"
            # Each page has 2-5 topics
            n_topics = random.randint(2, 5)
            page_topics[page_id] = random.sample(topic_ids, min(n_topics, len(topic_ids)))
        
        return page_topics

    def _export_results(self) -> None:
        """Export clustering results to files."""
        output_dir = Path(__file__).parent.parent.parent / "lbs-knowledge-graph" / "data"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export cluster stats
        cluster_stats = self.clusterer.get_cluster_stats()
        stats_file = output_dir / "clustering_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(cluster_stats, f, indent=2)
        logger.info(f"Exported cluster stats to {stats_file}")

        # Export hierarchy
        hierarchy_file = output_dir / "topic_hierarchy.json"
        with open(hierarchy_file, 'w') as f:
            # Convert hierarchy to JSON-serializable format
            serializable_hierarchy = {
                'root': self.hierarchy['root'],
                'primary': self.hierarchy['primary'],
                'specific': self.hierarchy['specific']
            }
            json.dump(serializable_hierarchy, f, indent=2)
        logger.info(f"Exported hierarchy to {hierarchy_file}")

        # Export relationships
        self.hierarchy_builder.export_hierarchy(
            str(output_dir / "subtopic_relationships.json")
        )

        # Export analysis report
        analysis_file = output_dir / "topic_analysis_report.json"
        with open(analysis_file, 'w') as f:
            # Make report JSON-serializable
            serializable_report = {
                'summary': self.analysis_report['summary'],
                'category_distribution': self.analysis_report['category_distribution'],
                'trending_topics': self.analysis_report['trending_topics'],
                'coverage': self.analysis_report['coverage']
            }
            json.dump(serializable_report, f, indent=2)
        logger.info(f"Exported analysis report to {analysis_file}")


async def main():
    """Main entry point for topic clustering."""
    enricher = TopicClusterEnricher(
        neo4j_client=None,  # Set to actual client if available
        min_clusters=5,
        max_clusters=10
    )

    results = await enricher.run_clustering_pipeline()

    print("\n" + "=" * 60)
    print("PIPELINE RESULTS")
    print("=" * 60)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
