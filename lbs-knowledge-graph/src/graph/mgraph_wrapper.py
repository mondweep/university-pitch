"""
MGraph Wrapper - Memgraph-like interface for JSON-based graph

Provides a query interface similar to Memgraph's Python driver
but operates on JSON-loaded graphs.
"""

import json
from typing import Dict, List, Any, Optional, Iterator
from pathlib import Path


class QueryResult:
    """Wrapper for query results to mimic Memgraph ResultSet"""

    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results
        self._index = 0

    def __iter__(self):
        return iter(self.results)

    def __next__(self):
        if self._index >= len(self.results):
            raise StopIteration
        result = self.results[self._index]
        self._index += 1
        return result


class MGraph:
    """
    Memgraph-like interface for JSON-based graph operations.

    Provides Cypher-like query capabilities on JSON graph data.
    """

    def __init__(self, graph_path: str = None, host: str = None, port: int = None):
        """
        Initialize MGraph wrapper.

        Args:
            graph_path: Path to JSON graph file
            host: Ignored (for Memgraph compatibility)
            port: Ignored (for Memgraph compatibility)
        """
        self.graph_path = graph_path
        self.nodes = []
        self.edges = []
        self._nodes_by_id = {}
        self._nodes_by_type = {}

        if graph_path and Path(graph_path).exists():
            self.load_graph(graph_path)

    def load_graph(self, graph_path: str):
        """Load graph from JSON file"""
        with open(graph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.nodes = data.get('nodes', [])
        self.edges = data.get('edges', [])

        # Build indices
        self._nodes_by_id = {node['id']: node for node in self.nodes}
        self._nodes_by_type = {}
        for node in self.nodes:
            node_type = node.get('node_type', 'Unknown')
            if node_type not in self._nodes_by_type:
                self._nodes_by_type[node_type] = []
            self._nodes_by_type[node_type].append(node)

    def save_graph(self, output_path: str):
        """Save graph to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'nodes': self.nodes,
                'edges': self.edges
            }, f, indent=2)

    def execute(self, query: str, params: Dict[str, Any] = None) -> None:
        """
        Execute a write query (MERGE, CREATE, SET, etc.)

        Args:
            query: Cypher-like query string
            params: Query parameters
        """
        params = params or {}

        # Parse query type
        query_upper = query.upper().strip()

        if 'MERGE (p:Persona' in query or 'CREATE (p:Persona' in query:
            self._create_persona_node(params)
        elif 'MERGE (' in query and ')-[r:TARGETS]->' in query:
            self._create_targets_relationship(query, params)
        elif 'SET p.targeted_content_count' in query:
            # Update operation, handled by execute_and_fetch
            pass
        else:
            # Generic update/create
            pass

    def execute_and_fetch(self, query: str, params: Dict[str, Any] = None) -> QueryResult:
        """
        Execute a read query and return results.

        Args:
            query: Cypher-like query string
            params: Query parameters

        Returns:
            QueryResult iterator
        """
        params = params or {}
        query_upper = query.upper().strip()

        # Match different query patterns
        if 'MATCH (p:Page)' in query_upper:
            return self._query_pages(query, params)
        elif 'MATCH (s:Section)' in query_upper:
            return self._query_sections(query, params)
        elif 'MATCH (p:Persona)<-[r:TARGETS]' in query_upper:
            return self._query_persona_stats(query, params)
        elif 'MATCH (content)-[r:TARGETS]->(p:Persona)' in query_upper:
            if 'persona_count > 1' in query.lower():
                return self._query_multi_target_content(query, params)
            elif 'WHERE p1.id < p2.id' in query:
                return self._query_persona_overlap(query, params)
            elif 'r.journey_stage' in query:
                return self._query_journey_distribution(query, params)
            else:
                return QueryResult([])
        elif 'MATCH (p:Persona)' in query_upper and 'NOT (p)<-[:TARGETS]-()' in query_upper:
            return self._query_orphaned_personas(query, params)
        elif 'MATCH ()-[r:TARGETS]->()' in query_upper:
            if 'min(r.relevance)' in query.lower():
                return self._query_relevance_stats(query, params)
            elif 'is_primary: true' in query.lower():
                return self._query_primary_coverage(query, params)

        return QueryResult([])

    def _create_persona_node(self, params: Dict[str, Any]):
        """Create or update a Persona node"""
        persona_id = params.get('id')

        # Check if exists
        existing = self._nodes_by_id.get(persona_id)
        if existing:
            # Update properties
            existing['data'].update({
                'name': params.get('name'),
                'type': params.get('type'),
                'slug': params.get('slug'),
                'description': params.get('description'),
                'characteristics': params.get('characteristics', []),
                'goals': params.get('goals', []),
                'pain_points': params.get('pain_points', []),
                'interests': params.get('interests', []),
                'priority': params.get('priority'),
                'targeted_content_count': params.get('targeted_content_count', 0)
            })
        else:
            # Create new node
            node = {
                'id': persona_id,
                'node_type': 'Persona',
                'data': {
                    'id': persona_id,
                    'name': params.get('name'),
                    'type': params.get('type'),
                    'slug': params.get('slug'),
                    'description': params.get('description'),
                    'characteristics': params.get('characteristics', []),
                    'goals': params.get('goals', []),
                    'pain_points': params.get('pain_points', []),
                    'interests': params.get('interests', []),
                    'priority': params.get('priority'),
                    'targeted_content_count': 0
                }
            }
            self.nodes.append(node)
            self._nodes_by_id[persona_id] = node
            if 'Persona' not in self._nodes_by_type:
                self._nodes_by_type['Persona'] = []
            self._nodes_by_type['Persona'].append(node)

    def _create_targets_relationship(self, query: str, params: Dict[str, Any]):
        """Create a TARGETS relationship"""
        # Create edge
        edge = {
            'from_node': params.get('content_id'),
            'to_node': params.get('persona_id'),
            'edge_type': 'TARGETS',
            'data': {
                'relationship_type': 'TARGETS',
                'persona_id': params.get('persona_id'),
                'relevance': params.get('relevance'),
                'is_primary': params.get('is_primary'),
                'journey_stage': params.get('journey_stage'),
                'signals': params.get('signals', []),
                'intent': params.get('intent', ''),
                'confidence': params.get('confidence', 0.9),
                'extracted_by': params.get('extracted_by')
            }
        }
        self.edges.append(edge)

    def _query_pages(self, query: str, params: Dict[str, Any]) -> QueryResult:
        """Query Page nodes"""
        pages = self._nodes_by_type.get('Page', [])
        results = []

        for page in pages:
            data = page.get('data', {})
            # Check filters
            if data.get('title') and data.get('text'):
                results.append({
                    'id': page['id'],
                    'title': data.get('title', ''),
                    'text': data.get('text', ''),
                    'url': data.get('url', ''),
                    'type': data.get('type', '')
                })

        # Apply LIMIT
        if 'LIMIT' in query.upper():
            limit = int(query.upper().split('LIMIT')[1].strip())
            results = results[:limit]

        return QueryResult(results)

    def _query_sections(self, query: str, params: Dict[str, Any]) -> QueryResult:
        """Query Section nodes"""
        sections = self._nodes_by_type.get('Section', [])
        results = []

        for section in sections:
            data = section.get('data', {})
            if data.get('heading') and data.get('text'):
                results.append({
                    'id': section['id'],
                    'title': data.get('heading', ''),
                    'text': data.get('text', ''),
                    'type': data.get('type', ''),
                    'page_id': data.get('pageId', '')
                })

        if 'LIMIT' in query.upper():
            limit = int(query.upper().split('LIMIT')[1].strip())
            results = results[:limit]

        return QueryResult(results)

    def _query_persona_stats(self, query: str, params: Dict[str, Any]) -> QueryResult:
        """Query persona statistics"""
        personas = self._nodes_by_type.get('Persona', [])
        results = []

        for persona in personas:
            persona_id = persona['id']
            # Count TARGETS edges pointing to this persona
            count = sum(1 for edge in self.edges
                       if edge.get('edge_type') == 'TARGETS'
                       and edge.get('to_node') == persona_id)

            # Update node
            persona['data']['targeted_content_count'] = count

            results.append({
                'persona_id': persona_id,
                'name': persona['data'].get('name', ''),
                'content_count': count
            })

        return QueryResult(results)

    def _query_multi_target_content(self, query: str, params: Dict[str, Any]) -> QueryResult:
        """Query content targeting multiple personas"""
        # Group edges by content
        content_targets = {}
        for edge in self.edges:
            if edge.get('edge_type') == 'TARGETS':
                content_id = edge['from_node']
                if content_id not in content_targets:
                    content_targets[content_id] = []

                # Get persona name
                persona_node = self._nodes_by_id.get(edge['to_node'])
                if persona_node:
                    content_targets[content_id].append({
                        'persona_name': persona_node['data'].get('name', ''),
                        'relevance': edge['data'].get('relevance', 0),
                        'is_primary': edge['data'].get('is_primary', False)
                    })

        # Filter multi-target content
        results = []
        for content_id, personas in content_targets.items():
            if len(personas) > 1:
                content_node = self._nodes_by_id.get(content_id)
                if content_node:
                    results.append({
                        'content_type': content_node['node_type'],
                        'content_id': content_id,
                        'title': content_node['data'].get('title', ''),
                        'persona_count': len(personas),
                        'personas': personas
                    })

        # Sort by persona_count descending
        results.sort(key=lambda x: x['persona_count'], reverse=True)

        if 'LIMIT' in query.upper():
            limit = int(query.upper().split('LIMIT')[1].strip())
            results = results[:limit]

        return QueryResult(results)

    def _query_persona_overlap(self, query: str, params: Dict[str, Any]) -> QueryResult:
        """Query persona co-targeting overlap"""
        # Group edges by content
        content_personas = {}
        for edge in self.edges:
            if edge.get('edge_type') == 'TARGETS':
                content_id = edge['from_node']
                persona_id = edge['to_node']
                if content_id not in content_personas:
                    content_personas[content_id] = []
                content_personas[content_id].append(persona_id)

        # Calculate overlap
        overlap = {}
        for personas in content_personas.values():
            if len(personas) > 1:
                for i, p1_id in enumerate(personas):
                    for p2_id in personas[i+1:]:
                        # Get persona names
                        p1 = self._nodes_by_id.get(p1_id)
                        p2 = self._nodes_by_id.get(p2_id)
                        if p1 and p2:
                            p1_name = p1['data'].get('name', '')
                            p2_name = p2['data'].get('name', '')
                            key = tuple(sorted([p1_name, p2_name]))
                            overlap[key] = overlap.get(key, 0) + 1

        results = [
            {
                'persona1': p1,
                'persona2': p2,
                'overlap_count': count
            }
            for (p1, p2), count in overlap.items()
        ]

        results.sort(key=lambda x: x['overlap_count'], reverse=True)
        return QueryResult(results)

    def _query_journey_distribution(self, query: str, params: Dict[str, Any]) -> QueryResult:
        """Query journey stage distribution"""
        # Group by persona and journey stage
        distribution = {}
        for edge in self.edges:
            if edge.get('edge_type') == 'TARGETS':
                persona_id = edge['to_node']
                journey_stage = edge['data'].get('journey_stage', 'awareness')

                persona_node = self._nodes_by_id.get(persona_id)
                if persona_node:
                    persona_name = persona_node['data'].get('name', '')
                    key = (persona_name, journey_stage)
                    distribution[key] = distribution.get(key, 0) + 1

        results = [
            {
                'persona_name': persona,
                'journey_stage': stage,
                'count': count
            }
            for (persona, stage), count in distribution.items()
        ]

        results.sort(key=lambda x: (x['persona_name'], -x['count']))
        return QueryResult(results)

    def _query_orphaned_personas(self, query: str, params: Dict[str, Any]) -> QueryResult:
        """Query personas with no TARGETS edges"""
        personas = self._nodes_by_type.get('Persona', [])
        targeted_personas = set(edge['to_node'] for edge in self.edges
                               if edge.get('edge_type') == 'TARGETS')

        orphaned = []
        for persona in personas:
            if persona['id'] not in targeted_personas:
                orphaned.append(persona['data'].get('name', ''))

        return QueryResult([{
            'orphaned_count': len(orphaned),
            'orphaned_personas': orphaned
        }])

    def _query_relevance_stats(self, query: str, params: Dict[str, Any]) -> QueryResult:
        """Query relevance score statistics"""
        relevances = [edge['data'].get('relevance', 0)
                     for edge in self.edges
                     if edge.get('edge_type') == 'TARGETS']

        if not relevances:
            return QueryResult([{
                'min_relevance': 0,
                'max_relevance': 0,
                'avg_relevance': 0,
                'total_relationships': 0
            }])

        return QueryResult([{
            'min_relevance': min(relevances),
            'max_relevance': max(relevances),
            'avg_relevance': sum(relevances) / len(relevances),
            'total_relationships': len(relevances)
        }])

    def _query_primary_coverage(self, query: str, params: Dict[str, Any]) -> QueryResult:
        """Query content with primary persona"""
        content_with_primary = set()
        for edge in self.edges:
            if edge.get('edge_type') == 'TARGETS' and edge['data'].get('is_primary'):
                content_with_primary.add(edge['from_node'])

        return QueryResult([{
            'content_with_primary': len(content_with_primary)
        }])
