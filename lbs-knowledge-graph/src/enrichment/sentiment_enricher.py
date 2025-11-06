"""
Sentiment Enricher for Knowledge Graph

Enriches graph with sentiment analysis for all content items.
"""

import json
from typing import Dict, List, Optional, Set
from pathlib import Path
from .models import SentimentScore
from .sentiment_analyzer import SentimentAnalyzer


class SentimentEnricher:
    """
    Enriches knowledge graph with sentiment analysis.

    Features:
    - Load graph from JSON
    - Extract ContentItem nodes
    - Run sentiment analysis in batches
    - Update graph with sentiment metadata
    - Propagate sentiment to parent Section and Page nodes
    """

    def __init__(self, graph: Dict, sentiment_analyzer: SentimentAnalyzer):
        """
        Initialize sentiment enricher.

        Args:
            graph: Graph dictionary with 'nodes' and 'edges'
            sentiment_analyzer: SentimentAnalyzer instance
        """
        self.graph = graph
        self.sentiment_analyzer = sentiment_analyzer

        # Build index for fast lookups
        self.node_index = {node["id"]: node for node in graph["nodes"]}
        self.edges_by_parent = self._build_parent_index()

    def _build_parent_index(self) -> Dict[str, List[str]]:
        """Build index of parent -> children relationships"""
        parent_index = {}

        for edge in self.graph["edges"]:
            edge_type = edge.get("edge_type", "")
            if edge_type == "CONTAINS":
                parent_id = edge["source"]
                child_id = edge["target"]

                if parent_id not in parent_index:
                    parent_index[parent_id] = []

                parent_index[parent_id].append(child_id)

        return parent_index

    def get_content_items(self) -> List[Dict]:
        """Extract all ContentItem nodes from graph"""
        return [
            node for node in self.graph["nodes"]
            if node.get("node_type") == "ContentItem"
        ]

    def get_sections(self) -> List[Dict]:
        """Extract all Section nodes from graph"""
        return [
            node for node in self.graph["nodes"]
            if node.get("node_type") == "Section"
        ]

    def get_pages(self) -> List[Dict]:
        """Extract all Page nodes from graph"""
        return [
            node for node in self.graph["nodes"]
            if node.get("node_type") == "Page"
        ]

    async def enrich_graph(self, batch_size: int = 50, progress_callback: Optional[callable] = None) -> Dict:
        """
        Enrich entire graph with sentiment analysis.

        Args:
            batch_size: Number of items to process in parallel
            progress_callback: Optional callback for progress updates

        Returns:
            Enriched graph dictionary
        """
        print("📊 Starting sentiment enrichment...")

        # Step 1: Analyze all ContentItems
        content_items = self.get_content_items()
        print(f"   Found {len(content_items)} ContentItem nodes")

        if len(content_items) == 0:
            print("⚠️  No ContentItems found in graph")
            return self.graph

        # Prepare content items for analysis
        items_to_analyze = []
        for node in content_items:
            data = node.get("data", {})
            items_to_analyze.append({
                "id": node["id"],
                "text": data.get("text", ""),
                "word_count": data.get("word_count", 0)
            })

        # Analyze in batches
        results = await self.sentiment_analyzer.analyze_batch(
            items_to_analyze,
            batch_size=batch_size,
            progress_callback=progress_callback
        )

        # Update ContentItem nodes with sentiment
        updated_count = 0
        for result in results:
            if result.has_sentiment():
                self.update_node_sentiment(result.content_id, result.sentiment)
                updated_count += 1

        print(f"   ✅ Updated {updated_count} ContentItems with sentiment")

        # Step 2: Propagate sentiment to Sections
        sections = self.get_sections()
        print(f"   Propagating sentiment to {len(sections)} Sections...")

        for section in sections:
            self.propagate_to_section(section["id"])

        # Step 3: Propagate sentiment to Pages
        pages = self.get_pages()
        print(f"   Propagating sentiment to {len(pages)} Pages...")

        for page in pages:
            self.propagate_to_page(page["id"])

        print("✅ Sentiment enrichment complete")

        return self.graph

    def update_node_sentiment(self, node_id: str, sentiment: SentimentScore):
        """
        Update graph node with sentiment metadata.

        Args:
            node_id: Node ID
            sentiment: SentimentScore to add to node
        """
        if node_id not in self.node_index:
            return

        node = self.node_index[node_id]

        # Add sentiment to node data
        if "data" not in node:
            node["data"] = {}

        node["data"]["sentiment"] = sentiment.to_dict()

    def get_node_sentiment(self, node_id: str) -> Optional[SentimentScore]:
        """Get sentiment score for a node"""
        if node_id not in self.node_index:
            return None

        node = self.node_index[node_id]
        data = node.get("data", {})
        sentiment_data = data.get("sentiment")

        if not sentiment_data:
            return None

        return SentimentScore.from_dict(sentiment_data)

    def get_children_ids(self, parent_id: str) -> List[str]:
        """Get list of child node IDs for a parent"""
        return self.edges_by_parent.get(parent_id, [])

    def propagate_to_section(self, section_id: str):
        """
        Propagate sentiment from ContentItems to Section.

        Aggregates sentiment from all child ContentItems using weighted average.
        """
        # Get child ContentItems
        child_ids = self.get_children_ids(section_id)

        # Get sentiment scores
        sentiments = []
        weights = []

        for child_id in child_ids:
            sentiment = self.get_node_sentiment(child_id)
            if sentiment and sentiment.confidence > 0:
                sentiments.append(sentiment)

                # Weight by word count (longer content has more weight)
                child_node = self.node_index.get(child_id)
                if child_node:
                    word_count = child_node.get("data", {}).get("word_count", 1)
                    weights.append(max(1, word_count))  # Minimum weight of 1

        # Aggregate sentiment
        if sentiments:
            aggregated = self.sentiment_analyzer.aggregate_sentiment(sentiments, weights)
            self.update_node_sentiment(section_id, aggregated)

    def propagate_to_page(self, page_id: str):
        """
        Propagate sentiment from Sections to Page.

        Aggregates sentiment from all child Sections using weighted average.
        """
        # Get child Sections
        child_ids = self.get_children_ids(page_id)

        # Get sentiment scores
        sentiments = []
        weights = []

        for child_id in child_ids:
            sentiment = self.get_node_sentiment(child_id)
            if sentiment and sentiment.confidence > 0:
                sentiments.append(sentiment)

                # Weight by number of content items in section
                section_children = self.get_children_ids(child_id)
                weights.append(max(1, len(section_children)))  # Minimum weight of 1

        # Aggregate sentiment
        if sentiments:
            aggregated = self.sentiment_analyzer.aggregate_sentiment(sentiments, weights)
            self.update_node_sentiment(page_id, aggregated)

    def export_graph(self, output_path: Path):
        """
        Export enriched graph to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=2, ensure_ascii=False)

        print(f"💾 Exported enriched graph to: {output_path}")

    def get_statistics(self) -> Dict:
        """
        Generate sentiment statistics for the graph.

        Returns:
            Dictionary with sentiment distribution statistics
        """
        stats = {
            "total_nodes": len(self.graph["nodes"]),
            "content_items": 0,
            "sections": 0,
            "pages": 0,
            "content_with_sentiment": 0,
            "sections_with_sentiment": 0,
            "pages_with_sentiment": 0,
            "sentiment_distribution": {
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "mixed": 0
            },
            "average_sentiment_score": 0.0,
            "average_confidence": 0.0
        }

        sentiment_scores = []
        confidence_scores = []

        for node in self.graph["nodes"]:
            node_type = node.get("node_type")

            if node_type == "ContentItem":
                stats["content_items"] += 1
            elif node_type == "Section":
                stats["sections"] += 1
            elif node_type == "Page":
                stats["pages"] += 1

            # Check for sentiment
            sentiment = self.get_node_sentiment(node["id"])
            if sentiment:
                if node_type == "ContentItem":
                    stats["content_with_sentiment"] += 1
                elif node_type == "Section":
                    stats["sections_with_sentiment"] += 1
                elif node_type == "Page":
                    stats["pages_with_sentiment"] += 1

                # Distribution
                stats["sentiment_distribution"][sentiment.polarity.value] += 1

                # For averages
                sentiment_scores.append(sentiment.score)
                confidence_scores.append(sentiment.confidence)

        # Calculate averages
        if sentiment_scores:
            stats["average_sentiment_score"] = round(sum(sentiment_scores) / len(sentiment_scores), 3)
        if confidence_scores:
            stats["average_confidence"] = round(sum(confidence_scores) / len(confidence_scores), 3)

        return stats
