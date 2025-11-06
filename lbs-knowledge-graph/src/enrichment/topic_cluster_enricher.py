"""
Topic Cluster Enricher

Orchestrates topic clustering, hierarchy building, and analysis.
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np

from ..graph.mgraph_compat import MGraph
from ..llm.llm_client import LLMClient
from .embedding_generator import EmbeddingGenerator
from .topic_clusterer import TopicClusterer, Topic, TopicCluster
from .topic_hierarchy_builder import TopicHierarchyBuilder
from .topic_analysis import TopicAnalysis

logger = logging.getLogger(__name__)


class TopicClusterEnricher:
    """
    Enrich knowledge graph with topic clusters and hierarchies.

    Pipeline:
    1. Load graph with topics from Phase 2
    2. Generate topic embeddings
    3. Cluster topics into hierarchies
    4. Create SUBTOPIC_OF and RELATED_TOPIC edges
    5. Calculate topic centrality
    6. Generate analysis report
    7. Export enriched graph
    """

    def __init__(
        self,
        graph_path: str,
        openai_api_key: str,
        similarity_threshold: float = 0.7,
        related_threshold: float = 0.6
    ):
        """
        Initialize topic cluster enricher.

        Args:
            graph_path: Path to input graph JSON file
            openai_api_key: OpenAI API key for embeddings
            similarity_threshold: Threshold for SUBTOPIC_OF relationships
            related_threshold: Threshold for RELATED_TOPIC relationships
        """
        self.graph_path = Path(graph_path)
        self.similarity_threshold = similarity_threshold
        self.related_threshold = related_threshold

        # Initialize components
        self.graph = MGraph()
        self.embedding_gen = EmbeddingGenerator(api_key=openai_api_key)
        self.clusterer = TopicClusterer(
            similarity_threshold=similarity_threshold,
            min_cluster_size=2,
            max_cluster_size=20
        )
        self.hierarchy_builder = None  # Initialized after loading graph
        self.analyzer = None  # Initialized after loading graph

        logger.info(f"Initialized TopicClusterEnricher for {graph_path}")

    async def load_graph(self) -> None:
        """Load knowledge graph from JSON file."""
        if not self.graph_path.exists():
            raise FileNotFoundError(f"Graph file not found: {self.graph_path}")

        self.graph.load_from_json(str(self.graph_path))

        # Initialize builders with loaded graph
        self.hierarchy_builder = TopicHierarchyBuilder(
            graph=self.graph,
            similarity_threshold=self.similarity_threshold,
            related_threshold=self.related_threshold
        )
        self.analyzer = TopicAnalysis(graph=self.graph)

        logger.info(
            f"Loaded graph: {self.graph.node_count()} nodes, "
            f"{self.graph.edge_count()} edges"
        )

    async def generate_topic_embeddings(self) -> Dict[str, List[float]]:
        """
        Generate embeddings for all topics in graph.

        Returns:
            Dictionary mapping topic IDs to embeddings
        """
        # Get all Topic nodes
        topic_nodes = self.graph.query(node_type='Topic')

        if not topic_nodes:
            logger.warning("No Topic nodes found in graph")
            return {}

        logger.info(f"Generating embeddings for {len(topic_nodes)} topics...")

        # Prepare texts for embedding
        topic_texts = []
        topic_ids = []

        for topic in topic_nodes:
            topic_name = topic.data.get('name', '')
            topic_description = topic.data.get('description', '')

            # Combine name and description for richer embeddings
            text = topic_name
            if topic_description:
                text = f"{topic_name}: {topic_description}"

            topic_texts.append(text)
            topic_ids.append(topic.id)

        # Generate embeddings in batch
        embeddings_list = await self.embedding_gen.generate_batch(topic_texts)

        # Create mapping
        embeddings = {
            topic_id: embedding
            for topic_id, embedding in zip(topic_ids, embeddings_list)
        }

        logger.info(f"Generated {len(embeddings)} topic embeddings")

        return embeddings

    def convert_to_topic_objects(self, embeddings: Dict[str, List[float]]) -> List[Topic]:
        """
        Convert graph Topic nodes to Topic objects with embeddings.

        Args:
            embeddings: Dictionary mapping topic IDs to embeddings

        Returns:
            List of Topic objects
        """
        topic_nodes = self.graph.query(node_type='Topic')
        topics = []

        for node in topic_nodes:
            if node.id not in embeddings:
                logger.warning(f"No embedding for topic: {node.id}")
                continue

            # Count frequency (number of pages containing topic)
            has_topic_edges = self.graph.get_edges(to_node_id=node.id, edge_type='HAS_TOPIC')
            frequency = len(has_topic_edges)

            topic = Topic(
                id=node.id,
                name=node.data.get('name', node.id),
                frequency=frequency,
                embedding=embeddings[node.id],
                category=node.data.get('category'),
                level=0  # Will be set during hierarchy building
            )

            topics.append(topic)

        logger.info(f"Converted {len(topics)} Topic nodes to objects")

        return topics

    def compute_similarity_matrix(self, topics: List[Topic]) -> Dict[Tuple[str, str], float]:
        """
        Compute pairwise similarity scores for all topics.

        Args:
            topics: List of Topic objects with embeddings

        Returns:
            Dictionary mapping (topic1_id, topic2_id) to similarity score
        """
        n = len(topics)
        embeddings = np.array([t.embedding for t in topics])

        # Compute cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarity_matrix = cosine_similarity(embeddings)

        # Convert to dictionary
        similarities = {}
        for i in range(n):
            for j in range(i+1, n):
                topic1_id = topics[i].id
                topic2_id = topics[j].id
                sim = float(similarity_matrix[i, j])

                similarities[(topic1_id, topic2_id)] = sim
                similarities[(topic2_id, topic1_id)] = sim  # Symmetric

        logger.info(f"Computed {len(similarities)} pairwise similarities")

        return similarities

    async def cluster_topics(self, topics: List[Topic]) -> List[TopicCluster]:
        """
        Cluster topics using hierarchical clustering.

        Args:
            topics: List of Topic objects with embeddings

        Returns:
            List of TopicCluster objects
        """
        logger.info("Clustering topics...")

        clusters = self.clusterer.cluster_topics(topics)

        # Log cluster details
        logger.info(f"Created {len(clusters)} topic clusters")

        for cluster in clusters:
            logger.info(
                f"  Cluster {cluster.cluster_id}: {cluster.size} topics, "
                f"centroid='{cluster.centroid_topic.name}', "
                f"avg_sim={cluster.avg_similarity:.3f}"
            )

        return clusters

    def build_hierarchy(self, topics: List[Topic]) -> Dict[str, List[str]]:
        """
        Build topic parent-child hierarchy.

        Args:
            topics: List of Topic objects

        Returns:
            Dictionary mapping parent IDs to child ID lists
        """
        logger.info("Building topic hierarchy...")

        hierarchy = self.clusterer.build_hierarchy(topics)

        # Log hierarchy stats
        root_count = len(hierarchy)
        child_count = sum(len(children) for children in hierarchy.values())

        logger.info(
            f"Built hierarchy: {root_count} root topics, {child_count} child topics"
        )

        return hierarchy

    def enrich_graph(
        self,
        hierarchy: Dict[str, List[str]],
        similarities: Dict[Tuple[str, str], float],
        topics: List[Topic]
    ) -> None:
        """
        Add hierarchy edges to graph.

        Args:
            hierarchy: Parent-child topic mapping
            similarities: Pairwise topic similarities
            topics: List of all topics
        """
        logger.info("Enriching graph with topic relationships...")

        # Create SUBTOPIC_OF edges
        subtopic_count = self.hierarchy_builder.build_hierarchy_from_clusters(
            hierarchy, similarities
        )

        # Create RELATED_TOPIC edges
        topic_ids = [t.id for t in topics]
        related_count = self.hierarchy_builder.build_related_topics(
            topic_ids, similarities
        )

        # Calculate centrality scores
        centralities = self.hierarchy_builder.calculate_all_centralities()

        logger.info(
            f"Graph enrichment complete: {subtopic_count} SUBTOPIC_OF edges, "
            f"{related_count} RELATED_TOPIC edges, {len(centralities)} centrality scores"
        )

    async def run_analysis(self) -> Dict:
        """
        Run comprehensive topic analysis.

        Returns:
            Dictionary with analysis results
        """
        logger.info("Running topic analysis...")

        # Distribution analysis
        distribution = self.analyzer.analyze_distribution()

        # Find trending and niche topics
        trending = self.analyzer.find_trending_topics(threshold=5)
        niche = self.analyzer.find_niche_topics(max_frequency=2)

        # Calculate diversity metrics
        diversity = self.analyzer.calculate_diversity_metrics()

        # Get hierarchy statistics
        hierarchy_stats = self.hierarchy_builder.get_hierarchy_statistics()

        analysis = {
            'distribution': distribution,
            'diversity': diversity,
            'hierarchy': hierarchy_stats,
            'trending_topics_count': len(trending),
            'niche_topics_count': len(niche),
        }

        logger.info("Topic analysis complete")

        return analysis

    async def export_graph(self, output_dir: Path) -> None:
        """
        Export enriched graph in multiple formats.

        Args:
            output_dir: Output directory for graph files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting enriched graph to {output_dir}...")

        # Export JSON (primary format)
        json_path = output_dir / 'graph_enriched.json'
        self.graph.save_to_json(str(json_path))

        # Export Cypher (for Neo4j)
        cypher_path = output_dir / 'graph_enriched.cypher'
        self.graph.export_cypher(str(cypher_path))

        # Export GraphML (for Gephi)
        graphml_path = output_dir / 'graph_enriched.graphml'
        self.graph.export_graphml(str(graphml_path))

        # Export Mermaid diagram
        mermaid_path = output_dir / 'graph_enriched.mmd'
        self.graph.export_mermaid(str(mermaid_path))

        logger.info(
            f"Exported graph: {json_path.name}, {cypher_path.name}, "
            f"{graphml_path.name}, {mermaid_path.name}"
        )

    async def export_reports(self, output_dir: Path, analysis: Dict) -> None:
        """
        Export analysis reports and visualizations.

        Args:
            output_dir: Output directory for reports
            analysis: Analysis results dictionary
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting reports to {output_dir}...")

        # Export topic analysis JSON
        analysis_path = output_dir / 'topic_analysis.json'
        self.analyzer.export_analysis_report(str(analysis_path))

        # Export topic hierarchy Mermaid diagram
        hierarchy_path = output_dir / 'topic_hierarchy.mmd'
        self.hierarchy_builder.export_hierarchy_mermaid(str(hierarchy_path))

        logger.info(f"Exported reports: {analysis_path.name}, {hierarchy_path.name}")

    async def run(
        self,
        output_dir: str = 'data/graph',
        reports_dir: str = 'docs'
    ) -> Dict:
        """
        Run complete topic clustering and enrichment pipeline.

        Args:
            output_dir: Output directory for enriched graph
            reports_dir: Output directory for analysis reports

        Returns:
            Dictionary with pipeline results
        """
        logger.info("=" * 80)
        logger.info("PHASE 3: TOPIC CLUSTERING AND HIERARCHY")
        logger.info("=" * 80)

        try:
            # Step 1: Load graph
            await self.load_graph()

            # Step 2: Generate topic embeddings
            embeddings = await self.generate_topic_embeddings()

            # Step 3: Convert to Topic objects
            topics = self.convert_to_topic_objects(embeddings)

            # Step 4: Compute similarity matrix
            similarities = self.compute_similarity_matrix(topics)

            # Step 5: Cluster topics
            clusters = await self.cluster_topics(topics)

            # Step 6: Build hierarchy
            hierarchy = self.build_hierarchy(topics)

            # Step 7: Enrich graph with relationships
            self.enrich_graph(hierarchy, similarities, topics)

            # Step 8: Run analysis
            analysis = await self.run_analysis()

            # Step 9: Export enriched graph
            await self.export_graph(Path(output_dir))

            # Step 10: Export reports
            await self.export_reports(Path(reports_dir), analysis)

            # Final statistics
            results = {
                'success': True,
                'topics_processed': len(topics),
                'clusters_created': len(clusters),
                'hierarchy_depth': analysis['hierarchy'].get('hierarchy_depth', 0),
                'root_topics': analysis['hierarchy'].get('root_topics', 0),
                'subtopic_edges': analysis['hierarchy'].get('subtopic_edges', 0),
                'related_edges': analysis['hierarchy'].get('related_topic_edges', 0),
                'trending_topics': analysis['trending_topics_count'],
                'niche_topics': analysis['niche_topics_count'],
            }

            logger.info("=" * 80)
            logger.info("PHASE 3 COMPLETE: Topic Clustering and Hierarchy")
            logger.info("=" * 80)
            logger.info(f"Topics processed: {results['topics_processed']}")
            logger.info(f"Clusters created: {results['clusters_created']}")
            logger.info(f"Root topics: {results['root_topics']}")
            logger.info(f"SUBTOPIC_OF edges: {results['subtopic_edges']}")
            logger.info(f"RELATED_TOPIC edges: {results['related_edges']}")
            logger.info(f"Hierarchy depth: {results['hierarchy_depth']}")
            logger.info(f"Trending topics: {results['trending_topics']}")
            logger.info(f"Niche topics: {results['niche_topics']}")
            logger.info("=" * 80)

            return results

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

        finally:
            # Cleanup
            await self.embedding_gen.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.embedding_gen.close()
