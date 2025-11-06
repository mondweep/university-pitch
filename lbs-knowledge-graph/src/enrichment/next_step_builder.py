"""
NEXT_STEP Builder - Creates Journey Pathway Relationships

Creates NEXT_STEP relationships between pages based on journey analysis:
- Represents typical navigation paths for each persona
- Stores transition probabilities
- Tracks persona context
- Calculates path strength
"""

import logging
from typing import List, Dict, Optional
import numpy as np

from src.graph.mgraph_wrapper import MGraph
from src.enrichment.journey_models import (
    Journey, JourneyPath, NextStepEdge, JourneyStage
)


logger = logging.getLogger(__name__)


class NextStepBuilder:
    """Builds NEXT_STEP relationships in the knowledge graph"""

    def __init__(self, graph: MGraph):
        """
        Initialize NEXT_STEP builder

        Args:
            graph: MGraph instance to add relationships to
        """
        self.graph = graph
        self.edges_created = 0

    def build_next_steps_for_journey(self, journey: Journey) -> int:
        """
        Build NEXT_STEP edges for all paths in a journey

        Args:
            journey: Journey object with typical paths

        Returns:
            Number of edges created
        """
        logger.info(f"Building NEXT_STEP edges for {journey.persona_name}")

        edges_created = 0

        for path in journey.typical_paths:
            path_edges = self.build_next_steps_for_path(path, journey)
            edges_created += path_edges

        logger.info(f"  Created {edges_created} NEXT_STEP edges")
        return edges_created

    def build_next_steps_for_path(self, path: JourneyPath, journey: Journey) -> int:
        """
        Build NEXT_STEP edges for a specific path

        Args:
            path: JourneyPath with page sequence and transitions
            journey: Parent Journey object for context

        Returns:
            Number of edges created
        """
        edges_created = 0

        for i in range(len(path.page_sequence) - 1):
            from_page = path.page_sequence[i]
            to_page = path.page_sequence[i + 1]
            transition_prob = path.transition_probs[i] if i < len(path.transition_probs) else 0.5
            from_stage = path.stage_labels[i] if i < len(path.stage_labels) else None
            to_stage = path.stage_labels[i + 1] if i + 1 < len(path.stage_labels) else None

            # Create NEXT_STEP edge
            success = self.create_next_step_edge(
                from_page=from_page,
                to_page=to_page,
                transition_prob=transition_prob,
                persona_id=journey.persona_id,
                from_stage=from_stage,
                to_stage=to_stage,
                path_strength=path.path_strength,
                frequency=path.frequency
            )

            if success:
                edges_created += 1

        return edges_created

    def create_next_step_edge(
        self,
        from_page: str,
        to_page: str,
        transition_prob: float,
        persona_id: str,
        from_stage: Optional[JourneyStage] = None,
        to_stage: Optional[JourneyStage] = None,
        path_strength: float = 0.5,
        frequency: int = 1
    ) -> bool:
        """
        Create a NEXT_STEP relationship between two pages

        Args:
            from_page: Source page ID
            to_page: Target page ID
            transition_prob: Probability of this transition (0-1)
            persona_id: Persona this transition is typical for
            from_stage: Journey stage of source page
            to_stage: Journey stage of target page
            path_strength: Overall strength of the path
            frequency: How common this path is

        Returns:
            True if edge created successfully
        """
        try:
            # Check if pages exist
            if not self._page_exists(from_page) or not self._page_exists(to_page):
                logger.warning(f"  Page not found: {from_page} or {to_page}")
                return False

            # Build edge properties
            properties = {
                'transition_prob': float(transition_prob),
                'persona_id': persona_id,
                'path_strength': float(path_strength),
                'frequency': int(frequency)
            }

            # Add stage information if available
            if from_stage:
                properties['from_stage'] = from_stage.value
            if to_stage:
                properties['to_stage'] = to_stage.value

            # Create or update NEXT_STEP relationship
            self.graph.add_edge(
                from_node=from_page,
                to_node=to_page,
                edge_type='NEXT_STEP',
                properties=properties
            )

            self.edges_created += 1
            return True

        except Exception as e:
            logger.error(f"  Error creating NEXT_STEP edge: {e}")
            return False

    def calculate_transition_matrix(self, persona_id: str) -> np.ndarray:
        """
        Calculate page transition probability matrix for a persona

        Creates a matrix where M[i,j] = probability of transitioning
        from page i to page j for this persona.

        Args:
            persona_id: Persona identifier

        Returns:
            NxN numpy array of transition probabilities
        """
        # Get all pages for this persona
        pages = self._get_persona_pages(persona_id)
        n_pages = len(pages)

        if n_pages == 0:
            return np.array([])

        # Create page index mapping
        page_to_idx = {page: idx for idx, page in enumerate(pages)}

        # Initialize transition matrix
        matrix = np.zeros((n_pages, n_pages))

        # Query all NEXT_STEP edges for this persona
        query = f"""
        MATCH (from:Page)-[next:NEXT_STEP {{persona_id: '{persona_id}'}}]->(to:Page)
        RETURN from.id as from_id, to.id as to_id, next.transition_prob as prob
        """

        results = self.graph.execute_query(query)

        # Fill matrix
        for row in results:
            from_id = row['from_id']
            to_id = row['to_id']
            prob = row['prob']

            if from_id in page_to_idx and to_id in page_to_idx:
                i = page_to_idx[from_id]
                j = page_to_idx[to_id]
                matrix[i, j] = prob

        # Normalize rows to sum to 1 (or 0 for pages with no outgoing edges)
        row_sums = matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        matrix = matrix / row_sums

        return matrix

    def get_next_step_recommendations(
        self,
        current_page: str,
        persona_id: str,
        top_n: int = 3
    ) -> List[Dict]:
        """
        Get recommended next steps from current page for a persona

        Args:
            current_page: Current page ID
            persona_id: Persona identifier
            top_n: Number of recommendations to return

        Returns:
            List of dicts with page_id, title, transition_prob
        """
        query = f"""
        MATCH (current:Page {{id: '{current_page}'}})
              -[next:NEXT_STEP {{persona_id: '{persona_id}'}}]->
              (target:Page)
        RETURN target.id as page_id,
               target.title as title,
               target.url as url,
               next.transition_prob as prob,
               next.path_strength as strength
        ORDER BY next.transition_prob DESC
        LIMIT {top_n}
        """

        results = self.graph.execute_query(query)

        recommendations = []
        for row in results:
            recommendations.append({
                'page_id': row['page_id'],
                'title': row['title'],
                'url': row['url'],
                'transition_prob': row['prob'],
                'path_strength': row['strength']
            })

        return recommendations

    def get_journey_statistics(self, persona_id: str) -> Dict:
        """
        Get statistics about NEXT_STEP edges for a persona

        Args:
            persona_id: Persona identifier

        Returns:
            Dict with statistics
        """
        # Count total edges
        count_query = f"""
        MATCH (:Page)-[next:NEXT_STEP {{persona_id: '{persona_id}'}}]->(:Page)
        RETURN count(next) as total_edges
        """
        result = self.graph.execute_query(count_query)
        total_edges = result[0]['total_edges'] if result else 0

        # Get average transition probability
        avg_query = f"""
        MATCH (:Page)-[next:NEXT_STEP {{persona_id: '{persona_id}'}}]->(:Page)
        RETURN avg(next.transition_prob) as avg_prob
        """
        result = self.graph.execute_query(avg_query)
        avg_prob = result[0]['avg_prob'] if result else 0.0

        # Get unique pages with NEXT_STEP edges
        pages_query = f"""
        MATCH (p:Page)-[next:NEXT_STEP {{persona_id: '{persona_id}'}}]->(:Page)
        RETURN count(DISTINCT p) as unique_pages
        """
        result = self.graph.execute_query(pages_query)
        unique_pages = result[0]['unique_pages'] if result else 0

        return {
            'persona_id': persona_id,
            'total_next_step_edges': total_edges,
            'unique_pages_with_next_steps': unique_pages,
            'avg_transition_probability': float(avg_prob) if avg_prob else 0.0
        }

    def _page_exists(self, page_id: str) -> bool:
        """Check if a page exists in the graph"""
        query = f"""
        MATCH (p:Page {{id: '{page_id}'}})
        RETURN count(p) as count
        """
        result = self.graph.execute_query(query)
        return result[0]['count'] > 0 if result else False

    def _get_persona_pages(self, persona_id: str) -> List[str]:
        """Get all pages targeted at a persona"""
        query = f"""
        MATCH (page:Page)-[:TARGETS]->(persona:Persona {{id: '{persona_id}'}})
        RETURN page.id as page_id
        ORDER BY page.id
        """
        results = self.graph.execute_query(query)
        return [r['page_id'] for r in results]

    def validate_next_steps(self) -> Dict:
        """
        Validate NEXT_STEP relationships

        Returns:
            Dict with validation results
        """
        # Count total NEXT_STEP edges
        total_query = """
        MATCH (:Page)-[next:NEXT_STEP]->(:Page)
        RETURN count(next) as total
        """
        result = self.graph.execute_query(total_query)
        total = result[0]['total'] if result else 0

        # Check for invalid probabilities
        invalid_query = """
        MATCH (:Page)-[next:NEXT_STEP]->(:Page)
        WHERE next.transition_prob < 0 OR next.transition_prob > 1
        RETURN count(next) as invalid
        """
        result = self.graph.execute_query(invalid_query)
        invalid = result[0]['invalid'] if result else 0

        # Check for missing persona_id
        missing_persona_query = """
        MATCH (:Page)-[next:NEXT_STEP]->(:Page)
        WHERE next.persona_id IS NULL
        RETURN count(next) as missing
        """
        result = self.graph.execute_query(missing_persona_query)
        missing_persona = result[0]['missing'] if result else 0

        return {
            'total_next_step_edges': total,
            'invalid_probabilities': invalid,
            'missing_persona_id': missing_persona,
            'valid': invalid == 0 and missing_persona == 0
        }
