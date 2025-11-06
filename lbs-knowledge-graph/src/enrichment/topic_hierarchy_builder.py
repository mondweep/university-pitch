"""
Topic Hierarchy Builder

Analyzes topic relationships and creates SUBTOPIC_OF edges to build taxonomy.
"""

from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime

from mgraph import MGraph
from .topic_models import TopicCategory, TopicTaxonomy


class TopicHierarchyBuilder:
    """
    Build topic hierarchy (taxonomy) in the knowledge graph.

    Creates SUBTOPIC_OF relationships between topics to build
    a 3-level taxonomy.
    """

    def __init__(self, graph: MGraph):
        """
        Initialize hierarchy builder.

        Args:
            graph: MGraph instance
        """
        self.graph = graph
        self.hierarchy_edges = 0

        # Root topics from taxonomy
        self.root_topics = {
            'Academic Programmes': ['MBA', 'Masters', 'Executive Education', 'PhD'],
            'Research & Thought Leadership': ['Research', 'Publications', 'Faculty Research'],
            'Faculty & Experts': ['Faculty', 'Professors', 'Researchers'],
            'Student Life & Community': ['Campus', 'Student Clubs', 'Student Support'],
            'Alumni & Network': ['Alumni', 'Alumni Network', 'Career Support'],
            'Events & Conferences': ['Events', 'Seminars', 'Conferences'],
            'Admissions & Applications': ['Admissions', 'Application', 'Requirements']
        }

    def build_hierarchy(self) -> Dict:
        """
        Build topic hierarchy from existing topics.

        Creates:
        1. Root topic nodes (if not exist)
        2. SUBTOPIC_OF edges based on taxonomy and similarity
        3. Updates topic levels

        Returns:
            Statistics dictionary
        """
        print("\n🏗️  Building topic hierarchy...")

        # Get all topics
        topics = self.graph.search_nodes(node_type="Topic")
        print(f"   Found {len(topics)} topics")

        # Create root topics
        root_topic_ids = self._create_root_topics()

        # Assign topics to root categories
        self._assign_to_root_topics(topics, root_topic_ids)

        # Build sub-hierarchies within categories
        self._build_sub_hierarchies(topics)

        stats = {
            'root_topics': len(root_topic_ids),
            'hierarchy_edges': self.hierarchy_edges,
            'max_depth': self._calculate_max_depth()
        }

        print(f"\n✅ Hierarchy build complete:")
        print(f"   • {len(root_topic_ids)} root topics")
        print(f"   • {self.hierarchy_edges} hierarchy edges")
        print(f"   • Max depth: {stats['max_depth']} levels")

        return stats

    def _create_root_topics(self) -> Dict[str, str]:
        """
        Create root topic nodes.

        Returns:
            Dictionary of root topic name -> topic ID
        """
        print("\n📝 Creating root topics...")

        root_ids = {}

        for root_name in self.root_topics.keys():
            # Check if exists
            existing = self.graph.search_nodes(
                node_type="Topic",
                filters={'name': root_name}
            )

            if existing:
                root_ids[root_name] = existing[0]['id']
                continue

            # Create root topic
            import uuid
            topic_id = str(uuid.uuid4())

            topic_node = {
                'id': topic_id,
                'name': root_name,
                'category': self._infer_root_category(root_name),
                'level': 0,  # Root level
                'frequency': 0,
                'importance': 0.9,  # High importance for roots
                'source': 'taxonomy',
                'extracted_at': datetime.now().isoformat(),
                'is_root': True
            }

            self.graph.add_node(
                node_id=topic_id,
                node_type="Topic",
                data=topic_node
            )

            root_ids[root_name] = topic_id

        print(f"   ✅ Created {len(root_ids)} root topics")
        return root_ids

    def _assign_to_root_topics(
        self,
        topics: List[Dict],
        root_topic_ids: Dict[str, str]
    ) -> None:
        """
        Assign topics to root categories.

        Args:
            topics: List of topic nodes
            root_topic_ids: Dictionary of root topic name -> ID
        """
        print("\n🔗 Assigning topics to root categories...")

        for topic in topics:
            # Skip if already has parent
            if topic.get('parent_topic_id'):
                continue

            # Skip root topics
            if topic.get('is_root'):
                continue

            # Find matching root topic
            topic_name = topic['name'].lower()

            for root_name, keywords in self.root_topics.items():
                # Check if topic name matches any keyword
                if any(kw.lower() in topic_name for kw in keywords):
                    root_id = root_topic_ids[root_name]

                    # Create SUBTOPIC_OF edge
                    self._create_hierarchy_edge(topic['id'], root_id, level=1)
                    break

    def _build_sub_hierarchies(self, topics: List[Dict]) -> None:
        """
        Build sub-hierarchies within categories.

        Creates SUBTOPIC_OF edges between related topics based on
        name similarity and category matching.

        Args:
            topics: List of topic nodes
        """
        print("\n🔗 Building sub-hierarchies...")

        # Group topics by category
        by_category: Dict[str, List[Dict]] = {}

        for topic in topics:
            if topic.get('is_root'):
                continue

            category = topic.get('category', 'general')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(topic)

        # Build hierarchies within each category
        for category, category_topics in by_category.items():
            self._build_category_hierarchy(category_topics)

    def _build_category_hierarchy(self, topics: List[Dict]) -> None:
        """
        Build hierarchy for topics in a single category.

        Uses name-based rules to infer parent-child relationships.

        Args:
            topics: Topics in the same category
        """
        # Sort by name length (shorter names = more general)
        sorted_topics = sorted(topics, key=lambda t: len(t['name']))

        for i, topic in enumerate(sorted_topics):
            # Skip if already has parent at level 2
            current_level = self._get_topic_level(topic['id'])
            if current_level >= 2:
                continue

            # Look for parent in previous topics (more general)
            for parent_candidate in sorted_topics[:i]:
                if self._is_subtopic_of(topic['name'], parent_candidate['name']):
                    # Create edge
                    self._create_hierarchy_edge(
                        topic['id'],
                        parent_candidate['id'],
                        level=2
                    )
                    break

    def _is_subtopic_of(self, topic_name: str, parent_name: str) -> bool:
        """
        Check if topic_name is a subtopic of parent_name.

        Rules:
        - Topic name contains parent name
        - Topic is more specific (e.g., "Digital Marketing" is subtopic of "Marketing")

        Args:
            topic_name: Potential subtopic name
            parent_name: Potential parent name

        Returns:
            True if subtopic relationship detected
        """
        topic_lower = topic_name.lower()
        parent_lower = parent_name.lower()

        # Topic contains parent
        if parent_lower in topic_lower and topic_lower != parent_lower:
            return True

        # Known relationships
        subtopic_map = {
            'marketing': ['digital marketing', 'brand management', 'marketing analytics'],
            'finance': ['corporate finance', 'financial markets', 'investment management'],
            'strategy': ['corporate strategy', 'competitive strategy', 'business models'],
            'leadership': ['inclusive leadership', 'leadership development'],
            'mba': ['executive mba', 'mba programme'],
            'masters': ['masters in finance', 'masters in management', 'masters in analytics']
        }

        for parent, subtopics in subtopic_map.items():
            if parent in parent_lower:
                for subtopic in subtopics:
                    if subtopic in topic_lower:
                        return True

        return False

    def _create_hierarchy_edge(
        self,
        child_id: str,
        parent_id: str,
        level: int
    ) -> None:
        """
        Create SUBTOPIC_OF edge.

        Args:
            child_id: Child topic ID
            parent_id: Parent topic ID
            level: Hierarchy level of child
        """
        edge_props = {
            'relationship_type': 'SUBTOPIC_OF',
            'level': level,
            'created_at': datetime.now().isoformat()
        }

        self.graph.add_edge(
            source_id=child_id,
            target_id=parent_id,
            edge_type="SUBTOPIC_OF",
            data=edge_props
        )

        # Update child topic level
        self.graph.update_node(
            node_id=child_id,
            data={'parent_topic_id': parent_id, 'level': level}
        )

        self.hierarchy_edges += 1

    def _get_topic_level(self, topic_id: str) -> int:
        """
        Get current hierarchy level of topic.

        Args:
            topic_id: Topic ID

        Returns:
            Level (0 = root, 1 = primary, 2 = secondary)
        """
        topics = self.graph.search_nodes(
            node_type="Topic",
            filters={'id': topic_id}
        )

        if not topics:
            return 0

        return topics[0].get('level', 0)

    def _calculate_max_depth(self) -> int:
        """
        Calculate maximum hierarchy depth.

        Returns:
            Maximum depth (levels)
        """
        topics = self.graph.search_nodes(node_type="Topic")

        if not topics:
            return 0

        return max(topic.get('level', 0) for topic in topics)

    def _infer_root_category(self, root_name: str) -> str:
        """
        Infer TopicCategory for root topic.

        Args:
            root_name: Root topic name

        Returns:
            Category string
        """
        category_map = {
            'Academic Programmes': 'academic',
            'Research & Thought Leadership': 'research',
            'Faculty & Experts': 'faculty',
            'Student Life & Community': 'student_life',
            'Alumni & Network': 'alumni',
            'Events & Conferences': 'events',
            'Admissions & Applications': 'admissions'
        }

        return category_map.get(root_name, 'general')

    def get_hierarchy_tree(self) -> Dict:
        """
        Get complete hierarchy tree.

        Returns:
            Nested dictionary representing hierarchy
        """
        topics = self.graph.search_nodes(node_type="Topic")

        # Build tree structure
        tree: Dict[str, Dict] = {}
        roots = [t for t in topics if t.get('level', 0) == 0]

        for root in roots:
            tree[root['name']] = self._build_subtree(root['id'], topics)

        return tree

    def _build_subtree(self, parent_id: str, all_topics: List[Dict]) -> Dict:
        """
        Build subtree for a parent topic.

        Args:
            parent_id: Parent topic ID
            all_topics: All topics

        Returns:
            Subtree dictionary
        """
        subtree = {}

        # Find children
        children = [
            t for t in all_topics
            if t.get('parent_topic_id') == parent_id
        ]

        for child in children:
            subtree[child['name']] = self._build_subtree(child['id'], all_topics)

        return subtree
