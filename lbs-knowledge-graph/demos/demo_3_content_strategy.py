#!/usr/bin/env python3
"""
Demo 3: Data-Driven Content Strategy
Demonstrates how the knowledge graph provides insights for content teams:
- Content gap analysis
- Performance metrics by topic/type
- Connection analysis (hubs and orphans)
- Strategic recommendations
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.mgraph_compat import MGraph


def find_graph_path(default_path: str = 'data/graph/graph.json') -> str:
    """Find graph file with automatic path detection."""
    graph_path = Path(default_path)

    # Check default path first
    if graph_path.exists():
        return str(graph_path)

    # Try lbs-knowledge-graph prefix (running from repo root)
    alt_path = Path('lbs-knowledge-graph') / default_path
    if alt_path.exists():
        return str(alt_path)

    # Not found in either location
    print(f"❌ Error: Graph file not found")
    print(f"   Tried: {default_path}")
    print(f"   Tried: {alt_path}")
    print(f"\n💡 Tip: Run from either:")
    print(f"   - lbs-knowledge-graph/ directory: python demos/demo_3_content_strategy.py")
    print(f"   - Repository root: python lbs-knowledge-graph/demos/demo_3_content_strategy.py")
    print(f"\n📍 Current directory: {Path.cwd()}")
    sys.exit(1)


class ContentStrategyDemo:
    """Demo for data-driven content strategy insights."""

    def __init__(self, graph_path: str):
        """Initialize with graph data."""
        self.graph = MGraph()
        self.graph.load_from_json(graph_path)

        # Analyze graph structure
        self.connections = self._analyze_connections()
        self.topics = self._analyze_topics()
        self.content_types = self._analyze_content_types()

    def _analyze_connections(self) -> Dict:
        """Analyze connection patterns in the graph."""
        connections = defaultdict(int)
        edges = self.graph.all_edges()

        # Count connections per node
        for edge in edges:
            connections[edge.from_node] += 1
            connections[edge.to_node] += 1

        # Find hubs and isolated/weak nodes
        sorted_connections = sorted(connections.items(), key=lambda x: x[1], reverse=True)

        return {
            'node_connections': dict(connections),
            'hubs': sorted_connections[:10],  # Top 10 most connected
            'weak': [(nid, count) for nid, count in sorted_connections if count <= 2][-10:],  # Bottom 10
            'isolated': [
                node.data.get('id') for node in self.graph.query()
                if node.data.get('id') not in connections
            ]
        }

    def _analyze_topics(self) -> Dict:
        """Analyze topic distribution (mock for demo)."""
        topic_coverage = defaultdict(int)

        for node in self.graph.query(node_type='Page'):
            title = node.data.get('title', '').lower()

            # Mock topic assignment
            if 'alumni' in title:
                topic_coverage['Alumni'] += 1
            if 'faculty' in title or 'research' in title:
                topic_coverage['Faculty & Research'] += 1
            if 'programme' in title:
                topic_coverage['Academic Programs'] += 1
            if 'news' in title or 'event' in title:
                topic_coverage['News & Events'] += 1
            if 'about' in title:
                topic_coverage['About LBS'] += 1
            if 'contact' in title:
                topic_coverage['Contact'] += 1

        return dict(topic_coverage)

    def _analyze_content_types(self) -> Dict:
        """Analyze content type distribution."""
        type_stats = defaultdict(lambda: {'count': 0, 'avg_content': 0, 'total_content': 0})

        # Analyze ContentItems
        for node in self.graph.query(node_type='ContentItem'):
            content_type = node.data.get('content_type', 'unknown')
            text_length = len(node.data.get('text', ''))

            type_stats[content_type]['count'] += 1
            type_stats[content_type]['total_content'] += text_length

        # Calculate averages
        for content_type, stats in type_stats.items():
            if stats['count'] > 0:
                stats['avg_content'] = stats['total_content'] / stats['count']

        return dict(type_stats)

    def generate_executive_dashboard(self) -> Dict:
        """Generate executive summary dashboard."""
        # Overall metrics
        total_nodes = len(list(self.graph.query()))
        total_pages = len(list(self.graph.query(node_type='Page')))
        total_sections = len(list(self.graph.query(node_type='Section')))
        total_content_items = len(list(self.graph.query(node_type='ContentItem')))

        # Connection health
        avg_connections = sum(self.connections['node_connections'].values()) / len(self.connections['node_connections']) if self.connections['node_connections'] else 0
        isolated_count = len(self.connections['isolated'])

        # Content health score (0-100)
        health_score = self._calculate_health_score()

        return {
            'overview': {
                'total_nodes': total_nodes,
                'pages': total_pages,
                'sections': total_sections,
                'content_items': total_content_items
            },
            'connectivity': {
                'avg_connections': round(avg_connections, 2),
                'isolated_nodes': isolated_count,
                'hub_count': len(self.connections['hubs']),
                'weak_connections': len(self.connections['weak'])
            },
            'content_coverage': {
                'topics_covered': len(self.topics),
                'topic_distribution': self.topics
            },
            'health_score': health_score,
            'recommendations': self._generate_recommendations()
        }

    def _calculate_health_score(self) -> int:
        """Calculate overall content health score (0-100)."""
        score = 100

        # Penalty for isolated nodes
        if self.connections['isolated']:
            score -= len(self.connections['isolated']) * 5

        # Penalty for weak connections
        score -= len(self.connections['weak']) * 2

        # Penalty for uneven topic coverage
        if self.topics:
            topic_counts = list(self.topics.values())
            max_count = max(topic_counts)
            min_count = min(topic_counts)
            imbalance = (max_count - min_count) / max_count if max_count > 0 else 0
            score -= int(imbalance * 20)

        return max(0, min(100, score))

    def _generate_recommendations(self) -> List[str]:
        """Generate strategic recommendations."""
        recommendations = []

        # Check for isolated nodes
        if self.connections['isolated']:
            recommendations.append(
                f"🔗 Connect {len(self.connections['isolated'])} isolated nodes to improve discoverability"
            )

        # Check for weak connections
        if len(self.connections['weak']) > 5:
            recommendations.append(
                f"📊 Strengthen {len(self.connections['weak'])} weakly connected nodes"
            )

        # Check topic imbalance
        if self.topics:
            topic_counts = list(self.topics.values())
            max_count = max(topic_counts)
            min_count = min(topic_counts)

            if max_count > min_count * 3:
                recommendations.append(
                    f"⚖️ Balance topic coverage - some topics have 3x more content than others"
                )

        # Content opportunities
        if len(list(self.graph.query(node_type='Page'))) < 50:
            recommendations.append(
                "📝 Consider expanding content - currently < 50 pages in graph"
            )

        # Always suggest enrichment if not done
        recommendations.append(
            "🤖 Run sentiment + topic enrichment to unlock deeper insights"
        )

        return recommendations

    def identify_content_hubs(self) -> List[Dict]:
        """Identify key content hubs (most connected pages)."""
        hubs = []

        for node_id, connection_count in self.connections['hubs']:
            node = self.graph.get_node(node_id)
            if node:
                node_type = node.data.get('node_type', 'unknown')

                # Get page info
                if node_type == 'Section':
                    # Get parent page
                    page_id = node_id.split('_section_')[0] if '_section_' in node_id else None
                    if page_id:
                        page_node = self.graph.get_node(page_id)
                        if page_node:
                            hubs.append({
                                'id': page_id,
                                'title': page_node.data.get('title', 'Unknown'),
                                'url': page_node.data.get('url', ''),
                                'type': 'Page',
                                'connections': connection_count,
                                'section_id': node_id,
                                'importance': 'High' if connection_count > 100 else 'Medium'
                            })
                elif node_type == 'Page':
                    hubs.append({
                        'id': node_id,
                        'title': node.data.get('title', 'Unknown'),
                        'url': node.data.get('url', ''),
                        'type': 'Page',
                        'connections': connection_count,
                        'importance': 'High' if connection_count > 100 else 'Medium'
                    })

        # Remove duplicates
        seen = set()
        unique_hubs = []
        for hub in hubs:
            if hub['id'] not in seen:
                seen.add(hub['id'])
                unique_hubs.append(hub)

        return unique_hubs[:5]

    def identify_content_gaps(self) -> List[Dict]:
        """Identify content gaps and opportunities."""
        gaps = []

        # Gap 1: Weakly connected content
        weak_pages = []
        for node_id, connection_count in self.connections['weak']:
            node = self.graph.get_node(node_id)
            if node and node.data.get('node_type') == 'Page':
                weak_pages.append({
                    'id': node_id,
                    'title': node.data.get('title'),
                    'connections': connection_count,
                    'issue': 'Weakly connected'
                })

        if weak_pages:
            gaps.append({
                'type': 'Weak Connections',
                'count': len(weak_pages),
                'pages': weak_pages[:3],
                'recommendation': 'Add related content or link to other pages'
            })

        # Gap 2: Topic imbalance
        if self.topics:
            topic_counts = list(self.topics.values())
            avg_count = sum(topic_counts) / len(topic_counts)

            underrepresented = [
                topic for topic, count in self.topics.items()
                if count < avg_count * 0.5
            ]

            if underrepresented:
                gaps.append({
                    'type': 'Topic Gaps',
                    'count': len(underrepresented),
                    'topics': underrepresented,
                    'recommendation': 'Expand content in underrepresented topics'
                })

        # Gap 3: Missing connections (potential)
        # Pages that could be connected but aren't
        all_pages = list(self.graph.query(node_type='Page'))
        if len(all_pages) > 1:
            # Check for pages with no inter-page connections
            # (In real implementation, would check LINKS_TO edges)
            gaps.append({
                'type': 'Missing Cross-Links',
                'count': 'Unknown (requires enrichment)',
                'recommendation': 'Add LINKS_TO edges between related pages'
            })

        return gaps

    def analyze_performance_by_topic(self) -> List[Dict]:
        """Analyze performance metrics by topic."""
        topic_performance = []

        for topic, page_count in self.topics.items():
            # Mock engagement data
            avg_engagement = 0.6 + (page_count * 0.05)  # More pages = higher engagement (mock)
            avg_time = 90 + (page_count * 10)  # More pages = more time (mock)

            topic_performance.append({
                'topic': topic,
                'page_count': page_count,
                'avg_engagement': min(1.0, avg_engagement),
                'avg_time_on_page': int(avg_time),
                'recommendation': self._get_topic_recommendation(page_count, avg_engagement)
            })

        topic_performance.sort(key=lambda x: x['avg_engagement'], reverse=True)

        return topic_performance

    def _get_topic_recommendation(self, page_count: int, engagement: float) -> str:
        """Get recommendation for a topic."""
        if page_count < 2:
            return "Consider expanding - only 1 page"
        elif engagement < 0.4:
            return "Low engagement - review content quality"
        elif engagement > 0.8:
            return "High performer - consider more content"
        else:
            return "Healthy - maintain current approach"


def demo_automated():
    """Automated demo showing all content strategy features."""
    print("=" * 70)
    print("DEMO 3: DATA-DRIVEN CONTENT STRATEGY")
    print("=" * 70)

    graph_path = find_graph_path()
    demo = ContentStrategyDemo(graph_path)

    # Executive dashboard
    print("\n" + "=" * 70)
    print("EXECUTIVE DASHBOARD")
    print("=" * 70)

    dashboard = demo.generate_executive_dashboard()

    print("\n📊 CONTENT OVERVIEW")
    print(f"   Total nodes: {dashboard['overview']['total_nodes']:,}")
    print(f"   Pages: {dashboard['overview']['pages']}")
    print(f"   Sections: {dashboard['overview']['sections']}")
    print(f"   Content items: {dashboard['overview']['content_items']:,}")

    print("\n🔗 CONNECTIVITY HEALTH")
    print(f"   Avg connections per node: {dashboard['connectivity']['avg_connections']}")
    print(f"   Isolated nodes: {dashboard['connectivity']['isolated_nodes']}")
    print(f"   Hub nodes (highly connected): {dashboard['connectivity']['hub_count']}")
    print(f"   Weak connections: {dashboard['connectivity']['weak_connections']}")

    print("\n📚 CONTENT COVERAGE")
    print(f"   Topics covered: {dashboard['content_coverage']['topics_covered']}")
    print("\n   Topic distribution:")
    for topic, count in dashboard['content_coverage']['topic_distribution'].items():
        print(f"     • {topic}: {count} pages")

    print(f"\n💯 CONTENT HEALTH SCORE: {dashboard['health_score']}/100")

    if dashboard['health_score'] >= 80:
        print("   Status: Excellent ✅")
    elif dashboard['health_score'] >= 60:
        print("   Status: Good ⚠️")
    else:
        print("   Status: Needs attention ❌")

    print("\n📋 STRATEGIC RECOMMENDATIONS:")
    for i, rec in enumerate(dashboard['recommendations'], 1):
        print(f"\n   {i}. {rec}")

    # Content hubs
    print("\n" + "=" * 70)
    print("CONTENT HUB ANALYSIS")
    print("=" * 70)

    hubs = demo.identify_content_hubs()

    print("\n⭐ Top Content Hubs (Most Connected Pages):\n")
    print("These pages act as 'anchor content' - highly connected to other content.\n")

    for i, hub in enumerate(hubs, 1):
        print(f"{i}. {hub['title']}")
        print(f"   Connections: {hub['connections']}")
        print(f"   Importance: {hub['importance']}")
        print(f"   URL: {hub['url']}\n")

    print("💡 Strategy: Hubs are high-traffic entry points. Ensure they:")
    print("   • Have excellent content quality")
    print("   • Link to relevant secondary pages")
    print("   • Are optimized for search/discovery")

    # Content gaps
    print("\n" + "=" * 70)
    print("CONTENT GAP ANALYSIS")
    print("=" * 70)

    gaps = demo.identify_content_gaps()

    print("\n🔍 Identified Content Gaps & Opportunities:\n")

    for gap in gaps:
        print(f"Gap Type: {gap['type']}")
        print(f"Impact: {gap['count']} items affected")

        if 'pages' in gap:
            print("\nAffected pages:")
            for page in gap['pages']:
                print(f"  • {page['title']} ({page['connections']} connections)")

        if 'topics' in gap:
            print(f"\nUnderrepresented topics: {', '.join(gap['topics'])}")

        print(f"\n✅ Recommendation: {gap['recommendation']}\n")
        print("-" * 70 + "\n")

    # Performance by topic
    print("\n" + "=" * 70)
    print("PERFORMANCE BY TOPIC")
    print("=" * 70)

    performance = demo.analyze_performance_by_topic()

    print("\n📈 Topic Performance Analysis:\n")

    for topic_data in performance:
        print(f"Topic: {topic_data['topic']}")
        print(f"  Pages: {topic_data['page_count']}")
        print(f"  Engagement rate: {topic_data['avg_engagement']:.1%}")
        print(f"  Avg time on page: {topic_data['avg_time_on_page']}s")
        print(f"  ✅ {topic_data['recommendation']}\n")

    # Summary
    print("\n" + "=" * 70)
    print("VALUE DEMONSTRATED: DATA-DRIVEN CONTENT STRATEGY")
    print("=" * 70)

    print("\n✅ Traditional content management:")
    print("   - Gut-feel decisions")
    print("   - Manual audits (time-consuming)")
    print("   - Reactive approach to issues")
    print("   - Limited visibility into connections")

    print("\n✅ Knowledge graph-powered strategy:")
    print("   - Quantitative insights on content structure")
    print("   - Automated health scoring")
    print("   - Proactive gap identification")
    print("   - Clear prioritization of improvements")

    print("\n💡 Impact for LBS content teams:")
    print("   • Marketing: Identify high-value hub content")
    print("   • Web team: Fix broken/weak connections")
    print("   • Content creators: Fill identified gaps")
    print("   • Leadership: Track content health metrics")

    print("\n📊 Strategic decisions enabled:")
    print("   • Budget allocation (expand vs optimize)")
    print("   • Content roadmap priorities")
    print("   • Performance benchmarks by topic")
    print("   • ROI measurement for content investments")

    print("\n🔮 Future enhancements (with enrichment):")
    print("   • Sentiment analysis by topic")
    print("   • User journey mapping")
    print("   • Conversion tracking through graph")
    print("   • A/B testing with graph metrics")


if __name__ == "__main__":
    demo_automated()
