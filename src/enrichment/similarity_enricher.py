"""
Similarity Enricher - Orchestrates the complete similarity enrichment pipeline

Coordinates embedding generation, similarity calculation, and edge creation
to add RELATED_TO relationships to the knowledge graph.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from .embedding_generator import EmbeddingGenerator, EmbeddingConfig
from .similarity_calculator import SimilarityCalculator, SimilarityConfig
from .related_to_builder import RelatedToBuilder, EdgeConfig

logger = logging.getLogger(__name__)


class SimilarityEnricher:
    """Orchestrates similarity enrichment pipeline"""

    def __init__(
        self,
        embedding_config: Optional[EmbeddingConfig] = None,
        similarity_config: Optional[SimilarityConfig] = None,
        edge_config: Optional[EdgeConfig] = None
    ):
        """
        Initialize similarity enricher

        Args:
            embedding_config: Configuration for embedding generation
            similarity_config: Configuration for similarity calculation
            edge_config: Configuration for edge creation
        """
        self.embedding_generator = EmbeddingGenerator(embedding_config)
        self.similarity_calculator = SimilarityCalculator(similarity_config)
        self.edge_builder = RelatedToBuilder(edge_config)

        self.stats = {
            "start_time": None,
            "end_time": None,
            "duration_seconds": 0,
            "pages_processed": 0,
            "embeddings_generated": 0,
            "similarities_calculated": 0,
            "edges_created": 0,
            "embedding_stats": {},
            "similarity_stats": {},
            "edge_stats": {}
        }

    def enrich_graph(self, graph: Dict) -> Dict:
        """
        Enrich graph with similarity-based RELATED_TO edges

        Args:
            graph: Knowledge graph dictionary

        Returns:
            Enriched graph with RELATED_TO edges
        """
        self.stats["start_time"] = datetime.now().isoformat()
        logger.info("Starting similarity enrichment pipeline")

        # Step 1: Extract pages from graph
        pages = [node for node in graph.get("nodes", [])
                if node.get("node_type") == "Page"]
        self.stats["pages_processed"] = len(pages)
        logger.info(f"Found {len(pages)} pages to process")

        if not pages:
            logger.warning("No pages found in graph")
            return graph

        # Step 2: Generate embeddings
        logger.info("Step 1/3: Generating embeddings...")
        embeddings = self.embedding_generator.generate_page_embeddings(pages)
        self.stats["embeddings_generated"] = len(embeddings)
        self.stats["embedding_stats"] = self.embedding_generator.get_stats()

        if not embeddings:
            logger.error("No embeddings generated")
            return graph

        logger.info(f"Generated {len(embeddings)} embeddings")

        # Step 3: Calculate similarities
        logger.info("Step 2/3: Calculating similarities...")
        similarities = self.similarity_calculator.get_all_similarities_by_page(embeddings)

        # Count total similarities
        total_similarities = sum(len(similar_pages) for similar_pages in similarities.values())
        self.stats["similarities_calculated"] = total_similarities
        self.stats["similarity_stats"] = self.similarity_calculator.get_stats()

        logger.info(f"Found {total_similarities} similar page pairs")

        # Step 4: Create RELATED_TO edges
        logger.info("Step 3/3: Creating RELATED_TO edges...")
        enriched_graph = self.edge_builder.add_edges_to_graph(graph, similarities)
        self.stats["edges_created"] = self.edge_builder.stats["total_edges_created"]
        self.stats["edge_stats"] = self.edge_builder.get_stats()

        # Update metadata
        if "metadata" not in enriched_graph:
            enriched_graph["metadata"] = {}

        enriched_graph["metadata"]["similarity_enriched"] = True
        enriched_graph["metadata"]["similarity_enrichment_date"] = datetime.now().isoformat()

        # Finalize stats
        self.stats["end_time"] = datetime.now().isoformat()
        start = datetime.fromisoformat(self.stats["start_time"])
        end = datetime.fromisoformat(self.stats["end_time"])
        self.stats["duration_seconds"] = (end - start).total_seconds()

        logger.info(f"Similarity enrichment complete in {self.stats['duration_seconds']:.2f}s")
        logger.info(f"Created {self.stats['edges_created']} RELATED_TO edges")

        return enriched_graph

    def enrich_graph_from_file(
        self,
        input_path: Path,
        output_path: Path,
        stats_path: Optional[Path] = None
    ) -> Dict:
        """
        Enrich graph from JSON file

        Args:
            input_path: Path to input graph JSON
            output_path: Path to save enriched graph
            stats_path: Optional path to save statistics

        Returns:
            Enriched graph dictionary
        """
        logger.info(f"Loading graph from {input_path}")

        # Load graph
        with open(input_path, 'r') as f:
            graph = json.load(f)

        # Enrich graph
        enriched_graph = self.enrich_graph(graph)

        # Save enriched graph
        logger.info(f"Saving enriched graph to {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(enriched_graph, f, indent=2)

        # Save stats if requested
        if stats_path:
            logger.info(f"Saving statistics to {stats_path}")
            stats_path.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_path, 'w') as f:
                json.dump(self.get_stats(), f, indent=2)

        return enriched_graph

    def get_stats(self) -> Dict:
        """Get complete enrichment statistics"""
        return self.stats.copy()

    def print_summary(self):
        """Print enrichment summary"""
        print("\n" + "="*60)
        print("SIMILARITY ENRICHMENT SUMMARY")
        print("="*60)

        print(f"\nProcessing:")
        print(f"  Duration: {self.stats['duration_seconds']:.2f} seconds")
        print(f"  Pages processed: {self.stats['pages_processed']}")

        print(f"\nEmbeddings:")
        print(f"  Generated: {self.stats['embeddings_generated']}")
        emb_stats = self.stats['embedding_stats']
        print(f"  API calls: {emb_stats.get('api_calls', 0)}")
        print(f"  Cache hits: {emb_stats.get('cache_hits', 0)}")
        print(f"  Cache hit rate: {emb_stats.get('cache_hit_rate', 0):.1%}")
        print(f"  Total tokens: {emb_stats.get('total_tokens', 0):,}")
        print(f"  Estimated cost: ${emb_stats.get('estimated_cost', 0):.4f}")

        print(f"\nSimilarities:")
        print(f"  Comparisons: {self.stats['similarity_stats'].get('total_comparisons', 0)}")
        print(f"  Above threshold: {self.stats['similarity_stats'].get('similarities_above_threshold', 0)}")

        print(f"\nEdges:")
        print(f"  RELATED_TO edges created: {self.stats['edges_created']}")
        edge_stats = self.stats['edge_stats']
        print(f"  Edges with shared topics: {edge_stats.get('edges_with_shared_topics', 0)}")
        print(f"  Average shared topics: {edge_stats.get('average_shared_topics', 0):.2f}")

        if 'similarity_distribution' in edge_stats:
            print(f"\nSimilarity distribution:")
            for score, count in sorted(edge_stats['similarity_distribution'].items()):
                print(f"  {score:.1f}: {count} edges")

        print("\n" + "="*60)


def main():
    """Test similarity enricher"""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Sample graph
    graph = {
        "nodes": [
            {
                "id": "page1",
                "node_type": "Page",
                "data": {
                    "title": "MBA Programme",
                    "description": "Full-time MBA with focus on leadership and strategy",
                    "type": "programme",
                    "topics": ["mba", "leadership", "strategy"]
                }
            },
            {
                "id": "page2",
                "node_type": "Page",
                "data": {
                    "title": "Executive MBA",
                    "description": "Part-time MBA for experienced executives",
                    "type": "programme",
                    "topics": ["mba", "executive", "leadership"]
                }
            },
            {
                "id": "page3",
                "node_type": "Page",
                "data": {
                    "title": "Finance Courses",
                    "description": "Advanced courses in corporate finance",
                    "type": "course",
                    "topics": ["finance", "investment"]
                }
            }
        ],
        "edges": []
    }

    # Check for API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not set. Please set it to test enrichment.")
        sys.exit(1)

    # Create enricher
    embedding_config = EmbeddingConfig(
        cache_dir=Path(".cache/embeddings")
    )
    similarity_config = SimilarityConfig(
        similarity_threshold=0.7,
        top_k=3
    )
    edge_config = EdgeConfig(
        min_similarity=0.7,
        max_edges_per_page=5
    )

    enricher = SimilarityEnricher(
        embedding_config=embedding_config,
        similarity_config=similarity_config,
        edge_config=edge_config
    )

    # Enrich graph
    enriched_graph = enricher.enrich_graph(graph)

    # Print results
    enricher.print_summary()

    print(f"\nEnriched graph has {len(enriched_graph['edges'])} edges")
    print("\nSample edges:")
    for edge in enriched_graph["edges"][:3]:
        print(f"\n{edge['source']} → {edge['target']}")
        print(f"  {edge['data']}")


if __name__ == "__main__":
    main()
