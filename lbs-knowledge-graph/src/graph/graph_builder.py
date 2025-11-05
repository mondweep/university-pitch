"""
Graph Builder for LBS Knowledge Graph

Builds knowledge graph using MGraph-DB from parsed content.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import json
from pydantic import ValidationError

from .mgraph_compat import MGraph
from .schema import LBSGraphSchema

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Build LBS knowledge graph using MGraph-DB

    Features:
    - Batch processing for performance
    - Transaction handling
    - Schema validation
    - Multiple export formats
    """

    def __init__(self):
        self.graph = MGraph()
        self.schema = LBSGraphSchema()
        self.batch_size = 1000
        self.stats = {
            'nodes_created': 0,
            'edges_created': 0,
            'validation_errors': 0,
            'pages': 0,
            'sections': 0,
            'content_items': 0
        }

    def add_pages(self, pages: List[Dict[str, Any]]) -> None:
        """
        Add Page nodes to the graph

        Args:
            pages: List of page dictionaries with metadata
        """
        logger.info(f"Adding {len(pages)} pages to graph")

        for page in pages:
            try:
                # Validate against schema
                page_data = {
                    'id': page.get('id'),
                    'url': page.get('url', ''),
                    'title': page.get('title', 'Untitled'),
                    'type': page.get('type', 'other'),
                    'importance': page.get('importance', 0.5),
                    'created_at': page.get('created_at'),
                    'updated_at': page.get('updated_at'),
                    'description': page.get('description'),
                    'keywords': page.get('keywords')
                }

                validated = self.schema.validate_node('Page', page_data)

                # Add to graph
                self.graph.add_node(
                    node_type='Page',
                    node_id=validated.id,
                    data=validated.dict(exclude_none=True)
                )

                self.stats['nodes_created'] += 1
                self.stats['pages'] += 1

            except ValidationError as e:
                logger.error(f"Validation error for page {page.get('id')}: {e}")
                self.stats['validation_errors'] += 1
            except Exception as e:
                logger.error(f"Error adding page {page.get('id')}: {e}")

    def add_sections(self, sections: List[Dict[str, Any]], page_id: str) -> None:
        """
        Add Section nodes and CONTAINS edges from page

        Args:
            sections: List of section dictionaries
            page_id: Parent page ID
        """
        for section in sections:
            try:
                section_data = {
                    'id': section.get('id'),
                    'section_type': section.get('type', 'unknown'),
                    'heading': section.get('heading'),
                    'order': section.get('order', 0)
                }

                validated = self.schema.validate_node('Section', section_data)

                # Add Section node
                self.graph.add_node(
                    node_type='Section',
                    node_id=validated.id,
                    data=validated.dict(exclude_none=True)
                )

                # Add CONTAINS edge from Page to Section
                self.graph.add_edge(
                    from_node_id=page_id,
                    to_node_id=validated.id,
                    edge_type='CONTAINS',
                    data={'order': validated.order}
                )

                self.stats['nodes_created'] += 1
                self.stats['edges_created'] += 1
                self.stats['sections'] += 1

            except ValidationError as e:
                logger.error(f"Validation error for section {section.get('id')}: {e}")
                self.stats['validation_errors'] += 1
            except Exception as e:
                logger.error(f"Error adding section {section.get('id')}: {e}")

    def add_content_items(self, items: List[Dict[str, Any]], section_id: str) -> None:
        """
        Add ContentItem nodes and CONTAINS edges from section

        Args:
            items: List of content item dictionaries
            section_id: Parent section ID
        """
        for item in items:
            try:
                content_data = {
                    'id': item.get('id'),
                    'hash': item.get('hash', ''),
                    'text': item.get('text', ''),
                    'content_type': item.get('type', 'text'),
                    'word_count': item.get('word_count', 0),
                    'order': item.get('order', 0)
                }

                validated = self.schema.validate_node('ContentItem', content_data)

                # Add ContentItem node
                self.graph.add_node(
                    node_type='ContentItem',
                    node_id=validated.id,
                    data=validated.dict(exclude_none=True)
                )

                # Add CONTAINS edge from Section to ContentItem
                self.graph.add_edge(
                    from_node_id=section_id,
                    to_node_id=validated.id,
                    edge_type='CONTAINS',
                    data={'order': validated.order}
                )

                self.stats['nodes_created'] += 1
                self.stats['edges_created'] += 1
                self.stats['content_items'] += 1

            except ValidationError as e:
                logger.error(f"Validation error for content item {item.get('id')}: {e}")
                self.stats['validation_errors'] += 1
            except Exception as e:
                logger.error(f"Error adding content item {item.get('id')}: {e}")

    def add_links(self, links: List[Dict[str, Any]], source_page_id: str) -> None:
        """
        Add LINKS_TO edges between pages

        Args:
            links: List of link dictionaries
            source_page_id: Source page ID
        """
        for link in links:
            try:
                target_id = link.get('target_id')
                if not target_id:
                    continue

                # Check if target node exists
                if not self.graph.get_node(target_id):
                    logger.warning(f"Target page {target_id} not found, skipping link")
                    continue

                edge_data = {
                    'text': link.get('text', ''),
                    'link_type': link.get('type', 'internal')
                }

                validated = self.schema.validate_edge('LINKS_TO', edge_data)

                self.graph.add_edge(
                    from_node_id=source_page_id,
                    to_node_id=target_id,
                    edge_type='LINKS_TO',
                    data=validated.dict()
                )

                self.stats['edges_created'] += 1

            except Exception as e:
                logger.error(f"Error adding link from {source_page_id}: {e}")

    def export_graph(self, format: str, path: Path) -> Path:
        """
        Export graph to specified format

        Args:
            format: Export format (json, graphml, cypher, mermaid, dot)
            path: Output file path

        Returns:
            Path to exported file
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting graph to {format} at {path}")

        if format == 'json':
            self.graph.save_to_json(str(path))
        elif format == 'graphml':
            self.graph.export_graphml(str(path))
        elif format == 'cypher':
            self.graph.export_cypher(str(path))
        elif format == 'mermaid':
            self.graph.export_mermaid(str(path))
        elif format == 'dot':
            self.graph.export_dot(str(path))
        else:
            raise ValueError(f"Unknown export format: {format}")

        logger.info(f"Graph exported to {path}")
        return path

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get graph statistics

        Returns:
            Dictionary with graph metrics
        """
        return {
            'total_nodes': self.graph.node_count(),
            'total_edges': self.graph.edge_count(),
            'nodes_by_type': {
                'Page': len(self.graph.query(node_type='Page')),
                'Section': len(self.graph.query(node_type='Section')),
                'ContentItem': len(self.graph.query(node_type='ContentItem')),
                'Topic': len(self.graph.query(node_type='Topic')),
                'Category': len(self.graph.query(node_type='Category')),
                'Persona': len(self.graph.query(node_type='Persona'))
            },
            'build_stats': self.stats,
            'avg_degree': (
                (2 * self.graph.edge_count()) / self.graph.node_count()
                if self.graph.node_count() > 0 else 0
            )
        }

    def validate_graph(self) -> Dict[str, Any]:
        """
        Validate graph integrity

        Returns:
            Validation report
        """
        report = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Check for orphaned nodes
        for node in self.graph.all_nodes():
            incoming = len(list(self.graph.get_edges(to_node_id=node.id)))
            outgoing = len(list(self.graph.get_edges(from_node_id=node.id)))

            if incoming == 0 and outgoing == 0 and node.node_type != 'Page':
                report['warnings'].append(f"Orphaned node: {node.id} ({node.node_type})")

        # Check for broken edges
        for edge in self.graph.all_edges():
            if not self.graph.get_node(edge.from_node):
                report['errors'].append(f"Edge source not found: {edge.from_node}")
                report['valid'] = False
            if not self.graph.get_node(edge.to_node):
                report['errors'].append(f"Edge target not found: {edge.to_node}")
                report['valid'] = False

        return report
