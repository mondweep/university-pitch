"""
Persona Enricher - Orchestrates persona classification and graph enrichment.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from ..graph.graph_loader import GraphLoader
from ..graph.mgraph_compat import MGraph
from ..llm.llm_client import LLMClient
from .persona_classifier import PersonaClassifier
from .targets_builder import TargetsBuilder
from .persona_models import get_all_personas


logger = logging.getLogger(__name__)


class PersonaEnricher:
    """Enrich knowledge graph with persona targeting."""

    def __init__(
        self,
        llm_client: LLMClient,
        graph_path: Path,
        output_dir: Path,
        relevance_threshold: float = 0.6
    ):
        """
        Initialize persona enricher.

        Args:
            llm_client: LLM client for classification
            graph_path: Path to input graph JSON
            output_dir: Output directory for enriched graph
            relevance_threshold: Minimum relevance score
        """
        self.llm_client = llm_client
        self.graph_path = graph_path
        self.output_dir = output_dir
        self.relevance_threshold = relevance_threshold

        # Initialize components
        self.classifier = PersonaClassifier(
            llm_client=llm_client,
            relevance_threshold=relevance_threshold,
            max_personas_per_content=3
        )
        self.graph: Optional[MGraph] = None
        self.builder: Optional[TargetsBuilder] = None

        logger.info(f"Initialized PersonaEnricher: graph={graph_path}")

    def load_graph(self) -> MGraph:
        """Load graph from file."""
        logger.info(f"Loading graph from {self.graph_path}")
        loader = GraphLoader()
        self.graph = loader.load(str(self.graph_path))
        self.builder = TargetsBuilder(self.graph)
        logger.info(f"Loaded graph with {self.graph.node_count()} nodes, {self.graph.edge_count()} edges")
        return self.graph

    async def enrich_pages(self) -> List[Dict[str, Any]]:
        """
        Classify all Page nodes by personas.

        Returns:
            List of classification results
        """
        if not self.graph:
            raise ValueError("Graph not loaded. Call load_graph() first.")

        logger.info("Enriching Page nodes with persona targeting...")

        # Get all Page nodes
        page_nodes = self.graph.get_nodes_by_type("Page")
        logger.info(f"Found {len(page_nodes)} Page nodes")

        # Prepare classification items
        items = []
        for node_id in page_nodes:
            node = self.graph.get_node(node_id)
            if not node:
                continue

            # Combine title and description for classification
            title = node.get('title', '')
            description = node.get('description', '')
            text = f"{title}\n\n{description}" if description else title

            items.append({
                'node_id': node_id,
                'text': text,
                'metadata': {
                    'page_type': node.get('type', 'unknown'),
                    'title': title,
                    'url': node.get('url', '')
                }
            })

        # Classify in batches
        logger.info(f"Classifying {len(items)} pages...")
        classifications = await self.classifier.classify_batch(items, batch_size=50)

        # Combine results
        results = []
        for item, targets in zip(items, classifications):
            results.append({
                'node_id': item['node_id'],
                'targets': targets,
                'metadata': item['metadata']
            })

        logger.info(
            f"Classified {len(results)} pages, "
            f"total targets: {sum(len(r['targets']) for r in results)}"
        )

        return results

    async def enrich_sections(self) -> List[Dict[str, Any]]:
        """
        Classify all Section nodes by personas.

        Returns:
            List of classification results
        """
        if not self.graph:
            raise ValueError("Graph not loaded. Call load_graph() first.")

        logger.info("Enriching Section nodes with persona targeting...")

        # Get all Section nodes
        section_nodes = self.graph.get_nodes_by_type("Section")
        logger.info(f"Found {len(section_nodes)} Section nodes")

        # Prepare classification items
        items = []
        for node_id in section_nodes:
            node = self.graph.get_node(node_id)
            if not node:
                continue

            # Use heading and text for classification
            heading = node.get('heading', '')
            text_content = node.get('text', '')
            text = f"{heading}\n\n{text_content}" if text_content else heading

            # Skip if no meaningful content
            if not text.strip():
                continue

            # Get parent page for context
            parent_edges = self.graph.get_edges_to(node_id)
            page_type = 'unknown'
            for edge_id in parent_edges:
                edge = self.graph.get_edge(edge_id)
                if edge.get('type') == 'CONTAINS':
                    parent = self.graph.get_node(edge['source'])
                    if parent.get('type') == 'Page':
                        page_type = parent.get('type', 'unknown')
                        break

            items.append({
                'node_id': node_id,
                'text': text,
                'metadata': {
                    'page_type': page_type,
                    'title': heading,
                    'section_type': node.get('type', 'unknown')
                }
            })

        # Classify in batches
        logger.info(f"Classifying {len(items)} sections...")
        classifications = await self.classifier.classify_batch(items, batch_size=50)

        # Combine results
        results = []
        for item, targets in zip(items, classifications):
            results.append({
                'node_id': item['node_id'],
                'targets': targets,
                'metadata': item['metadata']
            })

        logger.info(
            f"Classified {len(results)} sections, "
            f"total targets: {sum(len(r['targets']) for r in results)}"
        )

        return results

    async def enrich_graph(self) -> MGraph:
        """
        Enrich entire graph with persona targeting.

        Returns:
            Enriched MGraph
        """
        # Load graph
        self.load_graph()

        # Classify pages and sections
        page_results = await self.enrich_pages()
        section_results = await self.enrich_sections()

        # Build persona graph
        all_results = page_results + section_results
        logger.info(f"Building persona graph with {len(all_results)} classified nodes...")
        self.graph = self.builder.build_persona_graph(all_results)

        logger.info("Persona enrichment complete!")
        return self.graph

    def export_graph(self, output_path: Optional[Path] = None) -> Path:
        """
        Export enriched graph to JSON.

        Args:
            output_path: Output file path (default: output_dir/graph_enriched.json)

        Returns:
            Path to exported file
        """
        if not self.graph:
            raise ValueError("Graph not enriched. Call enrich_graph() first.")

        if output_path is None:
            output_path = self.output_dir / "graph_enriched.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export graph
        graph_data = {
            'metadata': {
                'total_nodes': self.graph.node_count(),
                'total_edges': self.graph.edge_count(),
                'personas': len(self.builder.persona_nodes),
                'targets_edges': sum(
                    len([e for e in self.graph.get_edges_to(nid)
                         if self.graph.get_edge(e).get('type') == 'TARGETS'])
                    for nid in self.builder.persona_nodes.values()
                )
            },
            'nodes': [
                {'id': nid, **self.graph.get_node(nid)}
                for nid in self.graph.get_all_nodes()
            ],
            'edges': [
                {'id': eid, **self.graph.get_edge(eid)}
                for eid in self.graph.get_all_edges()
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(graph_data, f, indent=2)

        logger.info(f"Exported enriched graph to {output_path}")
        logger.info(f"  Nodes: {graph_data['metadata']['total_nodes']}")
        logger.info(f"  Edges: {graph_data['metadata']['total_edges']}")
        logger.info(f"  Personas: {graph_data['metadata']['personas']}")
        logger.info(f"  TARGETS edges: {graph_data['metadata']['targets_edges']}")

        return output_path

    def generate_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Generate persona targeting report.

        Args:
            output_path: Output file path (default: output_dir/persona_report.json)

        Returns:
            Report data
        """
        if not self.builder:
            raise ValueError("Graph not enriched. Call enrich_graph() first.")

        if output_path is None:
            output_path = self.output_dir / "persona_report.json"

        report = self.builder.generate_report(output_path)

        # Add LLM usage stats
        report['llm_usage'] = self.classifier.get_usage_stats()

        # Save updated report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def get_summary(self) -> Dict[str, Any]:
        """Get enrichment summary."""
        if not self.graph or not self.builder:
            return {'status': 'not_enriched'}

        distribution = self.builder.get_persona_distribution()
        stats = self.classifier.get_usage_stats()

        return {
            'status': 'enriched',
            'graph': {
                'total_nodes': self.graph.node_count(),
                'total_edges': self.graph.edge_count(),
                'personas': len(self.builder.persona_nodes),
                'targets_edges': sum(
                    len([e for e in self.graph.get_edges_to(nid)
                         if self.graph.get_edge(e).get('type') == 'TARGETS'])
                    for nid in self.builder.persona_nodes.values()
                )
            },
            'persona_distribution': distribution,
            'llm_usage': stats
        }
