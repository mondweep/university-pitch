"""
Topic Cluster Enricher - Orchestration

Orchestrates complete topic clustering and hierarchy pipeline.
Coordinates: clustering -> hierarchy -> edge creation -> visualization.
"""

import json
import logging
from typing import Dict, List
from pathlib import Path
from datetime import datetime

from .topic_cluster_analyzer import TopicClusterAnalyzer
from .topic_hierarchy_builder import TopicHierarchyBuilder

logger = logging.getLogger(__name__)


class TopicClusterEnricher:
    """
    Master orchestrator for topic clustering and hierarchy enrichment.

    Pipeline:
    1. Load graph with topics
    2. Cluster topics by co-occurrence
    3. Build parent-child hierarchy
    4. Create CHILD_OF edges in graph
    5. Generate visualizations and reports
    6. Export enriched graph
    """

    def __init__(
        self,
        n_clusters: int = 5,
        confidence_threshold: float = 0.6,
        similarity_threshold: float = 0.3
    ):
        """
        Initialize enricher.

        Args:
            n_clusters: Target number of clusters
            confidence_threshold: Min confidence for CHILD_OF edges
            similarity_threshold: Min similarity for clustering
        """
        self.n_clusters = n_clusters
        self.confidence_threshold = confidence_threshold
        self.similarity_threshold = similarity_threshold

        self.graph: Dict = None
        self.analyzer: TopicClusterAnalyzer = None
        self.hierarchy_builder: TopicHierarchyBuilder = None

        self.clusters: List[Dict] = []
        self.relationships: List = []
        self.statistics: Dict = {}

    def load_graph(self, graph_path: str) -> None:
        """
        Load graph from JSON file.

        Args:
            graph_path: Path to graph JSON file
        """
        logger.info(f"Loading graph from {graph_path}...")

        with open(graph_path, 'r') as f:
            self.graph = json.load(f)

        n_nodes = len(self.graph.get('nodes', []))
        n_edges = len(self.graph.get('edges', []))

        logger.info(f"Loaded graph: {n_nodes} nodes, {n_edges} edges")

        # Count topics
        n_topics = sum(
            1 for node in self.graph['nodes']
            if node.get('node_type') == 'Topic'
        )

        logger.info(f"Found {n_topics} Topic nodes in graph")

        if n_topics == 0:
            raise ValueError("No Topic nodes found in graph. Run topic extraction first.")

    def run_clustering(self) -> Dict:
        """
        Run topic clustering pipeline.

        Returns:
            Cluster statistics dictionary
        """
        logger.info("Starting topic clustering...")

        # Initialize analyzer
        self.analyzer = TopicClusterAnalyzer(
            n_clusters=self.n_clusters,
            similarity_threshold=self.similarity_threshold
        )

        # Load topics and build co-occurrence
        self.analyzer.load_topics_from_graph(self.graph)

        # Cluster topics
        clusters = self.analyzer.cluster_topics()

        # Export cluster data
        self.clusters = self.analyzer.export_clusters()['clusters']

        logger.info(f"Clustering complete: {len(self.clusters)} clusters created")

        return {
            'n_clusters': len(self.clusters),
            'avg_cluster_size': sum(len(c['topics']) for c in self.clusters) / len(self.clusters) if self.clusters else 0,
            'avg_coherence': sum(c['coherence_score'] for c in self.clusters) / len(self.clusters) if self.clusters else 0
        }

    def run_hierarchy_building(self) -> Dict:
        """
        Build topic hierarchy.

        Returns:
            Hierarchy statistics dictionary
        """
        logger.info("Building topic hierarchy...")

        # Initialize builder
        self.hierarchy_builder = TopicHierarchyBuilder(
            confidence_threshold=self.confidence_threshold
        )

        # Load topics and clusters
        self.hierarchy_builder.load_topics_and_clusters(
            self.graph,
            self.clusters
        )

        # Build hierarchy
        relationships = self.hierarchy_builder.build_hierarchy()
        self.relationships = relationships

        logger.info(f"Hierarchy complete: {len(relationships)} CHILD_OF edges")

        return {
            'n_relationships': len(relationships),
            'avg_confidence': sum(r.confidence for r in relationships) / len(relationships) if relationships else 0,
            'max_depth': max(self.hierarchy_builder.topic_depths.values()) if self.hierarchy_builder.topic_depths else 0
        }

    def enrich_graph(self) -> None:
        """Add CHILD_OF edges to graph."""
        logger.info("Enriching graph with CHILD_OF edges...")

        edges_added = 0

        for rel in self.relationships:
            edge = {
                'id': f"child_of_{rel.parent_id}_{rel.child_id}",
                'from': rel.child_id,
                'to': rel.parent_id,
                'edge_type': 'CHILD_OF',
                'data': {
                    'confidence': float(rel.confidence),
                    'relationship_type': rel.relationship_type,
                    'created_at': datetime.now().isoformat()
                }
            }

            self.graph['edges'].append(edge)
            edges_added += 1

        logger.info(f"Added {edges_added} CHILD_OF edges to graph")

    def generate_visualizations(self, output_dir: str) -> Dict[str, str]:
        """
        Generate visualization files.

        Args:
            output_dir: Directory for output files

        Returns:
            Dictionary of generated file paths
        """
        logger.info("Generating visualizations...")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        generated_files = {}

        # 1. Mermaid hierarchy diagram
        mermaid_diagram = self.hierarchy_builder.generate_mermaid()
        mermaid_path = output_path / 'topic_hierarchy.mmd'

        with open(mermaid_path, 'w') as f:
            f.write(mermaid_diagram)

        generated_files['mermaid'] = str(mermaid_path)
        logger.info(f"Generated Mermaid diagram: {mermaid_path}")

        # 2. Cluster statistics JSON
        cluster_stats = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'n_clusters': len(self.clusters),
                'n_relationships': len(self.relationships)
            },
            'clusters': self.clusters,
            'hierarchy': self.hierarchy_builder.export_hierarchy(),
            'statistics': self.statistics
        }

        stats_path = output_path / 'cluster_stats.json'
        with open(stats_path, 'w') as f:
            json.dump(cluster_stats, f, indent=2)

        generated_files['stats'] = str(stats_path)
        logger.info(f"Generated statistics: {stats_path}")

        return generated_files

    def export_enriched_graph(self, output_path: str) -> None:
        """
        Export enriched graph to JSON.

        Args:
            output_path: Output file path
        """
        logger.info(f"Exporting enriched graph to {output_path}...")

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(self.graph, f, indent=2)

        logger.info(f"Graph exported: {output_file}")

    def run_pipeline(
        self,
        graph_path: str,
        output_dir: str,
        output_graph: str = None
    ) -> Dict:
        """
        Run complete enrichment pipeline.

        Args:
            graph_path: Input graph JSON path
            output_dir: Output directory for reports
            output_graph: Output path for enriched graph (optional)

        Returns:
            Pipeline statistics dictionary
        """
        logger.info("=" * 60)
        logger.info("TOPIC CLUSTERING & HIERARCHY ENRICHMENT PIPELINE")
        logger.info("=" * 60)

        start_time = datetime.now()

        try:
            # Step 1: Load graph
            self.load_graph(graph_path)

            # Step 2: Cluster topics
            cluster_stats = self.run_clustering()

            # Step 3: Build hierarchy
            hierarchy_stats = self.run_hierarchy_building()

            # Step 4: Enrich graph
            self.enrich_graph()

            # Step 5: Generate visualizations
            viz_files = self.generate_visualizations(output_dir)

            # Step 6: Export enriched graph
            if output_graph:
                self.export_enriched_graph(output_graph)

            # Calculate final statistics
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.statistics = {
                'success': True,
                'duration_seconds': duration,
                'clustering': cluster_stats,
                'hierarchy': hierarchy_stats,
                'files_generated': viz_files,
                'total_edges_added': len(self.relationships),
                'timestamp': datetime.now().isoformat()
            }

            logger.info("=" * 60)
            logger.info("PIPELINE COMPLETE ✅")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Clusters: {cluster_stats['n_clusters']}")
            logger.info(f"Hierarchy edges: {hierarchy_stats['n_relationships']}")
            logger.info(f"Max depth: {hierarchy_stats['max_depth']}")
            logger.info("=" * 60)

            return self.statistics

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            self.statistics = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return self.statistics
