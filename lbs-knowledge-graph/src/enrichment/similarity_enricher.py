"""
Similarity Enricher - Orchestrates similarity calculation and graph enrichment
Generates embeddings, calculates similarities, and creates RELATED_TO relationships.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .embedding_generator import EmbeddingGenerator
from .similarity_calculator import SimilarityCalculator, SimilarityResult
from .related_to_builder import RelatedToBuilder, RelatedToEdge
from ..graph.mgraph_compat import MGraph

logger = logging.getLogger(__name__)


class SimilarityEnricher:
    """Enrich knowledge graph with similarity relationships."""

    def __init__(
        self,
        graph: MGraph,
        embedding_generator: EmbeddingGenerator,
        similarity_calculator: Optional[SimilarityCalculator] = None,
        top_k: int = 5,
        threshold: float = 0.7,
        use_multi_signal: bool = True
    ):
        """
        Initialize similarity enricher.

        Args:
            graph: MGraph instance
            embedding_generator: Embedding generator
            similarity_calculator: Similarity calculator (creates default if None)
            top_k: Number of similar items per node
            threshold: Minimum similarity threshold
            use_multi_signal: Use multi-signal similarity
        """
        self.graph = graph
        self.embedding_gen = embedding_generator
        self.similarity_calc = similarity_calculator or SimilarityCalculator()
        self.related_builder = RelatedToBuilder(graph)

        self.top_k = top_k
        self.threshold = threshold
        self.use_multi_signal = use_multi_signal

        logger.info(
            f"Initialized SimilarityEnricher "
            f"(top_k={top_k}, threshold={threshold}, "
            f"multi_signal={use_multi_signal})"
        )

    async def generate_all_embeddings(
        self,
        node_types: List[str] = ['Page', 'Section'],
        batch_size: int = 100
    ) -> Dict[str, List[float]]:
        """
        Generate embeddings for all nodes of specified types.

        Args:
            node_types: List of node types to process
            batch_size: Batch size for embedding generation

        Returns:
            Dictionary mapping node_id -> embedding
        """
        logger.info(f"Generating embeddings for node types: {node_types}")

        embeddings = {}
        all_nodes = []

        # Collect all nodes of specified types
        for node_type in node_types:
            nodes = self.graph.get_nodes_by_type(node_type)
            all_nodes.extend(nodes)
            logger.info(f"Found {len(nodes)} {node_type} nodes")

        logger.info(f"Total nodes to process: {len(all_nodes)}")

        # Prepare texts for embedding
        texts = []
        node_ids = []

        for node in all_nodes:
            # Extract text content
            text = self._extract_node_text(node)

            if text:
                texts.append(text)
                node_ids.append(node['id'])

        logger.info(f"Prepared {len(texts)} texts for embedding")

        # Generate embeddings in batches
        try:
            all_embeddings = await self.embedding_gen.generate_batch(
                texts,
                batch_size=batch_size
            )

            # Map embeddings to node IDs
            for node_id, embedding in zip(node_ids, all_embeddings):
                embeddings[node_id] = embedding

            logger.info(f"Generated {len(embeddings)} embeddings")

            # Store embeddings in graph nodes
            self._store_embeddings_in_graph(embeddings)

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

        return embeddings

    def _extract_node_text(self, node: Dict) -> str:
        """
        Extract text content from node for embedding.

        Args:
            node: Node dictionary

        Returns:
            Combined text content
        """
        node_type = node.get('type', '')

        if node_type == 'Page':
            # Combine title, description, and keywords
            parts = []

            if node.get('title'):
                parts.append(node['title'])

            if node.get('description'):
                parts.append(node['description'])

            if node.get('keywords'):
                keywords = node['keywords']
                if isinstance(keywords, list):
                    parts.append(' '.join(keywords))

            return ' '.join(parts)

        elif node_type == 'Section':
            # Combine heading and subheading
            parts = []

            if node.get('heading'):
                parts.append(node['heading'])

            if node.get('subheading'):
                parts.append(node['subheading'])

            # Get content items if available
            content_items = self.graph.get_edges(
                node['id'],
                edge_type='CONTAINS'
            )

            for item in content_items[:5]:  # Limit to first 5 items
                target_node = self.graph.get_node(item['target'])
                if target_node and target_node.get('text'):
                    parts.append(target_node['text'][:200])  # First 200 chars

            return ' '.join(parts)

        # Fallback to text field
        return node.get('text', '')

    def _store_embeddings_in_graph(
        self,
        embeddings: Dict[str, List[float]]
    ) -> None:
        """
        Store embeddings in graph nodes.

        Args:
            embeddings: Dictionary of node_id -> embedding
        """
        for node_id, embedding in embeddings.items():
            node = self.graph.get_node(node_id)

            if node:
                # Store embedding in metadata
                if 'metadata' not in node:
                    node['metadata'] = {}

                node['metadata']['embedding'] = embedding
                node['metadata']['embedding_model'] = self.embedding_gen.model
                node['metadata']['embedding_generated_at'] = datetime.utcnow().isoformat()

                # Update node in graph
                self.graph.update_node(node_id, node)

        logger.info(f"Stored {len(embeddings)} embeddings in graph nodes")

    def calculate_all_similarities(
        self,
        embeddings: Dict[str, List[float]],
        use_ann: bool = True,
        ann_sample_ratio: float = 0.1
    ) -> List[Dict]:
        """
        Calculate pairwise similarities for all embeddings.

        Args:
            embeddings: Dictionary of node_id -> embedding
            use_ann: Use approximate nearest neighbors for speed
            ann_sample_ratio: Sampling ratio for ANN

        Returns:
            List of similarity results
        """
        logger.info(
            f"Calculating similarities for {len(embeddings)} nodes "
            f"(ANN={'enabled' if use_ann else 'disabled'})"
        )

        all_similarities = []
        processed = 0

        for query_id, query_embedding in embeddings.items():
            # Get query node data
            query_node = self.graph.get_node(query_id)

            if not query_node:
                continue

            # Prepare query data
            query_data = {
                'embedding': query_embedding,
                'topics': query_node.get('topics', []),
                'entities': self._extract_entities(query_node)
            }

            # Prepare candidates (exclude query itself)
            candidates = {}
            for candidate_id, candidate_embedding in embeddings.items():
                if candidate_id == query_id:
                    continue

                candidate_node = self.graph.get_node(candidate_id)

                if candidate_node:
                    candidates[candidate_id] = {
                        'embedding': candidate_embedding,
                        'topics': candidate_node.get('topics', []),
                        'entities': self._extract_entities(candidate_node)
                    }

            # Calculate similarities
            if use_ann and len(candidates) > 100:
                # Use approximate nearest neighbors
                candidate_embeddings = {
                    cid: cdata['embedding']
                    for cid, cdata in candidates.items()
                }

                results = self.similarity_calc.approximate_nearest_neighbors(
                    query_embedding,
                    candidate_embeddings,
                    top_k=self.top_k,
                    sample_ratio=ann_sample_ratio
                )
            else:
                # Use exact search
                results = self.similarity_calc.batch_similarity(
                    query_id,
                    query_data,
                    candidates,
                    top_k=self.top_k,
                    threshold=self.threshold,
                    use_multi_signal=self.use_multi_signal
                )

            # Convert to dictionaries
            for result in results:
                all_similarities.append({
                    'source_id': query_id,
                    'target_id': result.content_id,
                    'similarity': result.similarity,
                    'similarity_type': result.similarity_type,
                    'metadata': result.metadata
                })

            processed += 1

            if processed % 10 == 0:
                logger.info(f"Processed {processed}/{len(embeddings)} nodes")

        logger.info(
            f"Calculated {len(all_similarities)} similarity relationships"
        )

        return all_similarities

    def _extract_entities(self, node: Dict) -> List[str]:
        """
        Extract entity names from node.

        Args:
            node: Node dictionary

        Returns:
            List of entity names
        """
        entities = node.get('entities', [])

        if isinstance(entities, list):
            # Extract entity text/name
            entity_names = []
            for entity in entities:
                if isinstance(entity, dict):
                    entity_names.append(entity.get('text', ''))
                elif isinstance(entity, str):
                    entity_names.append(entity)

            return [e for e in entity_names if e]

        return []

    def build_related_to_relationships(
        self,
        similarities: List[Dict],
        bidirectional: bool = True
    ) -> int:
        """
        Build RELATED_TO relationships from similarity results.

        Args:
            similarities: List of similarity results
            bidirectional: Create edges in both directions

        Returns:
            Number of created edges
        """
        logger.info("Building RELATED_TO relationships")

        created = self.related_builder.build_related_graph(
            similarities,
            bidirectional=bidirectional,
            min_similarity=self.threshold
        )

        return created

    async def enrich(
        self,
        node_types: List[str] = ['Page', 'Section'],
        use_ann: bool = True,
        export_results: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict:
        """
        Run complete similarity enrichment pipeline.

        Args:
            node_types: Node types to process
            use_ann: Use approximate nearest neighbors
            export_results: Export results to files
            output_dir: Output directory for exports

        Returns:
            Enrichment statistics
        """
        start_time = datetime.utcnow()

        logger.info("Starting similarity enrichment pipeline")

        # Step 1: Generate embeddings
        logger.info("Step 1: Generating embeddings")
        embeddings = await self.generate_all_embeddings(node_types)

        # Step 2: Calculate similarities
        logger.info("Step 2: Calculating similarities")
        similarities = self.calculate_all_similarities(embeddings, use_ann=use_ann)

        # Step 3: Build RELATED_TO relationships
        logger.info("Step 3: Building RELATED_TO relationships")
        edges_created = self.build_related_to_relationships(similarities)

        # Get statistics
        stats = self.related_builder.get_related_stats()

        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Prepare results
        results = {
            'nodes_processed': len(embeddings),
            'similarities_calculated': len(similarities),
            'edges_created': edges_created,
            'duration_seconds': duration,
            'statistics': stats,
            'config': {
                'top_k': self.top_k,
                'threshold': self.threshold,
                'use_multi_signal': self.use_multi_signal,
                'use_ann': use_ann
            }
        }

        # Export results
        if export_results and output_dir:
            self._export_results(results, similarities, output_dir)

        logger.info(
            f"Similarity enrichment complete in {duration:.1f}s: "
            f"{len(embeddings)} nodes, {len(similarities)} similarities, "
            f"{edges_created} edges created"
        )

        return results

    def _export_results(
        self,
        results: Dict,
        similarities: List[Dict],
        output_dir: Path
    ) -> None:
        """
        Export enrichment results to files.

        Args:
            results: Results dictionary
            similarities: Similarity results
            output_dir: Output directory
        """
        import json

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export summary
        summary_path = output_dir / 'similarity_enrichment_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Exported summary to {summary_path}")

        # Export similarities
        similarities_path = output_dir / 'similarities.json'
        with open(similarities_path, 'w') as f:
            json.dump({
                'count': len(similarities),
                'similarities': similarities
            }, f, indent=2)

        logger.info(f"Exported similarities to {similarities_path}")

        # Export RELATED_TO edges
        edges_path = output_dir / 'related_to_edges.json'
        self.related_builder.export_edges(str(edges_path))
