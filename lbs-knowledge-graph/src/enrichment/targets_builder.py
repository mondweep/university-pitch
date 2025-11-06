"""
TARGETS Relationship Builder for Knowledge Graph.
Creates Persona nodes and TARGETS edges from content to personas.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from ..graph.mgraph_compat import MGraph
from .persona_models import Persona, PersonaTarget, get_all_personas


logger = logging.getLogger(__name__)


class TargetsBuilder:
    """Build TARGETS relationships in knowledge graph."""

    def __init__(self, graph: MGraph):
        """
        Initialize targets builder.

        Args:
            graph: MGraph instance
        """
        self.graph = graph
        self.persona_nodes = {}  # persona_id -> node_id mapping
        logger.info("Initialized TargetsBuilder")

    def create_persona_node(self, persona: Persona) -> str:
        """
        Create Persona node in graph.

        Args:
            persona: Persona definition

        Returns:
            Node ID
        """
        # Check if persona already exists
        existing = self.graph.get_nodes_by_type("Persona")
        for node_id in existing:
            node = self.graph.get_node(node_id)
            if node and node.get('persona_id') == persona.id:
                logger.debug(f"Persona node already exists: {persona.name}")
                self.persona_nodes[persona.id] = node_id
                return node_id

        # Create new persona node
        node_data = {
            'type': 'Persona',
            'persona_id': persona.id,
            'name': persona.name,
            'slug': persona.slug,
            'persona_type': persona.type.value,
            'description': persona.description,
            'characteristics': persona.characteristics,
            'goals': persona.goals,
            'pain_points': persona.pain_points,
            'interests': persona.interests,
            'priority': persona.priority,
            'content_count': 0,
            'page_count': 0,
            'metadata': persona.metadata
        }

        node_id = self.graph.add_node(**node_data)
        self.persona_nodes[persona.id] = node_id

        logger.info(f"Created Persona node: {persona.name} (id={node_id})")
        return node_id

    def create_targets_edge(
        self,
        source_id: str,
        persona_id: str,
        relevance: float,
        journey_stage: str,
        intent: str = "",
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create TARGETS relationship from content to persona.

        Args:
            source_id: Source node ID (Page or Section)
            persona_id: Persona ID
            relevance: Relevance score (0-1)
            journey_stage: Journey stage name
            intent: Why content targets this persona
            confidence: Classification confidence
            metadata: Additional metadata

        Returns:
            Edge ID
        """
        # Get persona node ID
        persona_node_id = self.persona_nodes.get(persona_id)
        if not persona_node_id:
            logger.error(f"Persona node not found: {persona_id}")
            return None

        # Create edge data
        edge_data = {
            'type': 'TARGETS',
            'relevance': relevance,
            'journey_stage': journey_stage,
            'intent': intent,
            'confidence': confidence,
            'metadata': metadata or {}
        }

        # Check if edge already exists
        existing_edges = self.graph.get_edges_from(source_id)
        for edge_id in existing_edges:
            edge = self.graph.get_edge(edge_id)
            if (edge and edge.get('type') == 'TARGETS' and
                edge['target'] == persona_node_id):
                # Update existing edge
                for key, value in edge_data.items():
                    edge[key] = value
                logger.debug(f"Updated existing TARGETS edge: {source_id} -> {persona_node_id}")
                return edge_id

        # Create new edge
        edge_id = self.graph.add_edge(
            source=source_id,
            target=persona_node_id,
            **edge_data
        )

        logger.debug(f"Created TARGETS edge: {source_id} -> {persona_node_id} (rel={relevance:.2f})")
        return edge_id

    def build_persona_graph(
        self,
        classifications: List[Dict[str, Any]]
    ) -> MGraph:
        """
        Build complete persona graph with nodes and relationships.

        Args:
            classifications: List of classification results
                Each item should have:
                - node_id: Source node ID
                - targets: List of PersonaTarget objects

        Returns:
            Updated MGraph
        """
        # Create all persona nodes first
        logger.info("Creating persona nodes...")
        for persona in get_all_personas():
            self.create_persona_node(persona)

        # Create TARGETS edges
        logger.info("Creating TARGETS edges...")
        total_edges = 0
        for item in classifications:
            node_id = item.get('node_id')
            targets = item.get('targets', [])

            for target in targets:
                if isinstance(target, PersonaTarget):
                    edge_id = self.create_targets_edge(
                        source_id=node_id,
                        persona_id=target.persona_id,
                        relevance=target.relevance,
                        journey_stage=target.journey_stage.value,
                        intent=target.intent,
                        confidence=target.confidence,
                        metadata=target.metadata
                    )
                    if edge_id:
                        total_edges += 1

        logger.info(f"Created {total_edges} TARGETS edges for {len(classifications)} nodes")

        # Update persona node counts
        self._update_persona_counts()

        return self.graph

    def _update_persona_counts(self):
        """Update content_count and page_count for persona nodes."""
        for persona_id, node_id in self.persona_nodes.items():
            # Count incoming TARGETS edges
            incoming = self.graph.get_edges_to(node_id)
            targets_edges = [
                e for e in incoming
                if self.graph.get_edge(e).get('type') == 'TARGETS'
            ]

            # Count unique pages
            page_sources = set()
            content_count = 0

            for edge_id in targets_edges:
                edge = self.graph.get_edge(edge_id)
                source_node = self.graph.get_node(edge['source'])

                if source_node.get('type') == 'Page':
                    page_sources.add(edge['source'])
                    content_count += 1
                elif source_node.get('type') == 'Section':
                    # Find parent page
                    section_edges = self.graph.get_edges_to(edge['source'])
                    for se in section_edges:
                        sec_edge = self.graph.get_edge(se)
                        if sec_edge.get('type') == 'CONTAINS':
                            parent = self.graph.get_node(sec_edge['source'])
                            if parent.get('type') == 'Page':
                                page_sources.add(sec_edge['source'])
                                break
                    content_count += 1

            # Update node
            node = self.graph.get_node(node_id)
            node['content_count'] = content_count
            node['page_count'] = len(page_sources)

            logger.debug(f"Updated persona {persona_id}: {content_count} content, {len(page_sources)} pages")

    def get_persona_distribution(self) -> Dict[str, Dict[str, int]]:
        """
        Get distribution of content across personas.

        Returns:
            Dict mapping persona_id to counts
        """
        distribution = {}

        for persona_id, node_id in self.persona_nodes.items():
            node = self.graph.get_node(node_id)
            distribution[persona_id] = {
                'name': node.get('name', ''),
                'content_count': node.get('content_count', 0),
                'page_count': node.get('page_count', 0),
                'priority': node.get('priority', 3)
            }

        return distribution

    def generate_report(self, output_path: Path) -> Dict[str, Any]:
        """
        Generate persona targeting report.

        Args:
            output_path: Output file path for JSON report

        Returns:
            Report data
        """
        distribution = self.get_persona_distribution()

        # Calculate statistics
        total_content = sum(p['content_count'] for p in distribution.values())
        total_pages = sum(p['page_count'] for p in distribution.values())

        # Journey stage distribution
        journey_stages = {}
        for persona_id, node_id in self.persona_nodes.items():
            incoming = self.graph.get_edges_to(node_id)
            for edge_id in incoming:
                edge = self.graph.get_edge(edge_id)
                if edge.get('type') == 'TARGETS':
                    stage = edge.get('journey_stage', 'unknown')
                    journey_stages[stage] = journey_stages.get(stage, 0) + 1

        report = {
            'summary': {
                'total_personas': len(self.persona_nodes),
                'total_targets_edges': sum(len(self.graph.get_edges_to(nid)) for nid in self.persona_nodes.values()),
                'total_content_targeted': total_content,
                'total_pages_targeted': total_pages,
                'avg_personas_per_content': total_content / len(distribution) if distribution else 0
            },
            'persona_distribution': distribution,
            'journey_stage_distribution': journey_stages,
            'personas': {
                pid: {
                    'id': pid,
                    'node_id': nid,
                    **distribution[pid]
                }
                for pid, nid in self.persona_nodes.items()
            }
        }

        # Save report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Generated persona targeting report: {output_path}")
        logger.info(f"  Total personas: {report['summary']['total_personas']}")
        logger.info(f"  Total TARGETS edges: {report['summary']['total_targets_edges']}")
        logger.info(f"  Avg personas per content: {report['summary']['avg_personas_per_content']:.2f}")

        return report
