"""
RELATED_TO Edge Builder for Knowledge Graph

Creates RELATED_TO edges between similar pages with semantic metadata.
Implements intelligent edge creation with topic analysis and reasoning.
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class EdgeConfig:
    """Configuration for RELATED_TO edge creation"""
    min_similarity: float = 0.7
    max_edges_per_page: int = 5
    require_shared_topics: bool = False
    min_shared_topics: int = 1
    add_reasoning: bool = True


class RelatedToBuilder:
    """Build RELATED_TO edges between similar pages"""

    def __init__(self, config: Optional[EdgeConfig] = None):
        """
        Initialize edge builder

        Args:
            config: Configuration for edge creation
        """
        self.config = config or EdgeConfig()
        self.stats = {
            "total_edges_created": 0,
            "edges_with_shared_topics": 0,
            "average_shared_topics": 0.0,
            "similarity_distribution": Counter()
        }

    def _get_page_data(self, page_id: str, graph: Dict) -> Optional[Dict]:
        """
        Get page data from graph

        Args:
            page_id: ID of the page
            graph: Graph dictionary

        Returns:
            Page node data or None if not found
        """
        for node in graph.get("nodes", []):
            if node.get("id") == page_id:
                return node
        return None

    def _extract_topics(self, page_data: Dict) -> Set[str]:
        """
        Extract topics from page data

        Args:
            page_data: Page node data

        Returns:
            Set of topics
        """
        topics = set()
        data = page_data.get("data", {})

        # Extract from topics field
        if "topics" in data:
            if isinstance(data["topics"], list):
                topics.update(data["topics"])
            elif isinstance(data["topics"], str):
                topics.add(data["topics"])

        # Extract from type
        if "type" in data:
            topics.add(data["type"])

        return topics

    def _find_shared_topics(
        self,
        page1_id: str,
        page2_id: str,
        graph: Dict
    ) -> List[str]:
        """
        Find topics shared between two pages

        Args:
            page1_id: First page ID
            page2_id: Second page ID
            graph: Graph dictionary

        Returns:
            List of shared topics
        """
        page1 = self._get_page_data(page1_id, graph)
        page2 = self._get_page_data(page2_id, graph)

        if not page1 or not page2:
            return []

        topics1 = self._extract_topics(page1)
        topics2 = self._extract_topics(page2)

        shared = topics1.intersection(topics2)
        return sorted(list(shared))

    def _generate_reasoning(
        self,
        page1_id: str,
        page2_id: str,
        similarity: float,
        shared_topics: List[str],
        graph: Dict
    ) -> str:
        """
        Generate reasoning for why pages are related

        Args:
            page1_id: First page ID
            page2_id: Second page ID
            similarity: Similarity score
            shared_topics: List of shared topics
            graph: Graph dictionary

        Returns:
            Reasoning text
        """
        page1 = self._get_page_data(page1_id, graph)
        page2 = self._get_page_data(page2_id, graph)

        if not page1 or not page2:
            return "automatic"

        reasons = []

        # High similarity
        if similarity >= 0.9:
            reasons.append("very high semantic similarity")
        elif similarity >= 0.8:
            reasons.append("high semantic similarity")
        else:
            reasons.append("semantic similarity")

        # Shared topics
        if shared_topics:
            if len(shared_topics) == 1:
                reasons.append(f"shared topic: {shared_topics[0]}")
            elif len(shared_topics) == 2:
                reasons.append(f"shared topics: {', '.join(shared_topics)}")
            else:
                reasons.append(f"multiple shared topics ({len(shared_topics)})")

        # Same type
        type1 = page1.get("data", {}).get("type")
        type2 = page2.get("data", {}).get("type")
        if type1 and type2 and type1 == type2:
            if type1 not in shared_topics:  # Don't duplicate
                reasons.append(f"same page type: {type1}")

        if not reasons:
            return "automatic"

        return "; ".join(reasons)

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        similarity: float,
        graph: Dict
    ) -> Optional[Dict]:
        """
        Create a RELATED_TO edge between two pages

        Args:
            source_id: Source page ID
            target_id: Target page ID
            similarity: Similarity score
            graph: Graph dictionary

        Returns:
            Edge dictionary or None if edge should not be created
        """
        # Check minimum similarity
        if similarity < self.config.min_similarity:
            return None

        # Find shared topics
        shared_topics = self._find_shared_topics(source_id, target_id, graph)

        # Check topic requirements
        if self.config.require_shared_topics:
            if len(shared_topics) < self.config.min_shared_topics:
                return None

        # Generate reasoning
        reasoning = "automatic"
        if self.config.add_reasoning:
            reasoning = self._generate_reasoning(
                source_id, target_id, similarity, shared_topics, graph
            )

        # Create edge
        edge = {
            "source": source_id,
            "target": target_id,
            "edge_type": "RELATED_TO",
            "data": {
                "similarity": round(similarity, 3),
                "reasoning": reasoning
            }
        }

        # Add shared topics if any
        if shared_topics:
            edge["data"]["shared_topics"] = shared_topics
            self.stats["edges_with_shared_topics"] += 1

        # Update stats
        self.stats["total_edges_created"] += 1
        similarity_bucket = int(similarity * 10) / 10
        self.stats["similarity_distribution"][similarity_bucket] += 1

        return edge

    def build_edges(
        self,
        similarities: Dict[str, List[Tuple[str, float]]],
        graph: Dict
    ) -> List[Dict]:
        """
        Build RELATED_TO edges for all similar pages

        Args:
            similarities: Dictionary mapping page_id to list of (similar_page_id, score)
            graph: Graph dictionary

        Returns:
            List of edge dictionaries
        """
        edges = []
        seen_pairs = set()

        logger.info(f"Building RELATED_TO edges for {len(similarities)} pages")

        for source_id, similar_pages in similarities.items():
            # Limit edges per page
            for target_id, similarity in similar_pages[:self.config.max_edges_per_page]:
                # Avoid duplicate edges (since similarity is bidirectional)
                pair = tuple(sorted([source_id, target_id]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                # Create edge
                edge = self.create_edge(source_id, target_id, similarity, graph)
                if edge:
                    edges.append(edge)

        # Calculate average shared topics
        if self.stats["edges_with_shared_topics"] > 0:
            total_shared = sum(
                len(edge["data"].get("shared_topics", []))
                for edge in edges
            )
            self.stats["average_shared_topics"] = (
                total_shared / self.stats["edges_with_shared_topics"]
            )

        logger.info(f"Created {len(edges)} RELATED_TO edges")

        return edges

    def add_edges_to_graph(
        self,
        graph: Dict,
        similarities: Dict[str, List[Tuple[str, float]]]
    ) -> Dict:
        """
        Add RELATED_TO edges to graph

        Args:
            graph: Graph dictionary
            similarities: Dictionary mapping page_id to list of (similar_page_id, score)

        Returns:
            Updated graph dictionary
        """
        # Build edges
        new_edges = self.build_edges(similarities, graph)

        # Add to graph
        if "edges" not in graph:
            graph["edges"] = []

        graph["edges"].extend(new_edges)

        logger.info(f"Added {len(new_edges)} RELATED_TO edges to graph")
        logger.info(f"Total edges in graph: {len(graph['edges'])}")

        return graph

    def get_stats(self) -> Dict:
        """Get edge creation statistics"""
        stats = self.stats.copy()
        stats["similarity_distribution"] = dict(stats["similarity_distribution"])
        return stats


def main():
    """Test edge building"""
    import json

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
                    "type": "programme",
                    "topics": ["mba", "leadership", "finance"]
                }
            },
            {
                "id": "page2",
                "node_type": "Page",
                "data": {
                    "title": "Executive MBA",
                    "type": "programme",
                    "topics": ["mba", "executive", "leadership"]
                }
            },
            {
                "id": "page3",
                "node_type": "Page",
                "data": {
                    "title": "Finance Courses",
                    "type": "course",
                    "topics": ["finance", "investment"]
                }
            }
        ],
        "edges": []
    }

    # Sample similarities
    similarities = {
        "page1": [("page2", 0.85), ("page3", 0.72)],
        "page2": [("page1", 0.85)],
        "page3": [("page1", 0.72)]
    }

    # Create builder
    config = EdgeConfig(
        min_similarity=0.7,
        max_edges_per_page=5,
        add_reasoning=True
    )
    builder = RelatedToBuilder(config)

    # Build edges
    graph = builder.add_edges_to_graph(graph, similarities)

    # Print results
    print("\nEdge Building Results:")
    print(f"Total edges created: {len(graph['edges'])}")
    print(f"\nEdges:")
    for edge in graph["edges"]:
        print(f"\n{edge['source']} → {edge['target']}")
        print(f"  Similarity: {edge['data']['similarity']}")
        print(f"  Reasoning: {edge['data']['reasoning']}")
        if "shared_topics" in edge["data"]:
            print(f"  Shared topics: {edge['data']['shared_topics']}")

    print(f"\nStats: {json.dumps(builder.get_stats(), indent=2)}")


if __name__ == "__main__":
    main()
