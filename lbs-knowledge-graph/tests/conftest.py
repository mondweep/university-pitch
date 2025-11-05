"""
Test fixtures and configuration for Phase 2 tests
"""

import pytest
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


# ==================== Test Data Fixtures ====================

@pytest.fixture
def sample_page_data() -> Dict[str, Any]:
    """Sample parsed page data from Phase 1"""
    return {
        'url': 'https://london.edu/programmes/mba',
        'metadata': {
            'title': 'MBA Programme - London Business School',
            'canonical_url': 'https://london.edu/programmes/mba',
            'language': 'en',
            'description': 'Transform your career with LBS MBA',
            'og_title': 'MBA Programme',
            'keywords': ['mba', 'business school', 'london']
        },
        'dom': {
            'tag': 'html',
            'attrs': {'lang': 'en'},
            'children': [
                {
                    'tag': 'head',
                    'children': [
                        {'tag': 'title', 'text': 'MBA Programme - London Business School'}
                    ]
                },
                {
                    'tag': 'body',
                    'children': [
                        {
                            'tag': 'main',
                            'children': [
                                {
                                    'tag': 'section',
                                    'attrs': {'class': 'hero', 'data-section-type': 'hero'},
                                    'children': [
                                        {'tag': 'h1', 'text': 'MBA Programme'},
                                        {'tag': 'p', 'text': 'Transform your career with our world-class MBA'}
                                    ]
                                },
                                {
                                    'tag': 'section',
                                    'attrs': {'class': 'content', 'data-section-type': 'content'},
                                    'children': [
                                        {'tag': 'h2', 'text': 'Programme Overview'},
                                        {'tag': 'p', 'text': 'Our MBA programme offers a transformative learning experience.'},
                                        {
                                            'tag': 'ul',
                                            'children': [
                                                {'tag': 'li', 'text': '15-21 months duration'},
                                                {'tag': 'li', 'text': 'Global cohort'},
                                                {'tag': 'li', 'text': 'World-class faculty'}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        'links': [
            {
                'href': '/admissions',
                'text': 'Admissions',
                'type': 'internal'
            },
            {
                'href': '/programmes/masters',
                'text': 'Masters Programmes',
                'type': 'internal'
            }
        ]
    }


@pytest.fixture
def sample_faculty_page() -> Dict[str, Any]:
    """Sample faculty page data"""
    return {
        'url': 'https://london.edu/faculty/john-doe',
        'metadata': {
            'title': 'Prof. John Doe - Faculty',
            'canonical_url': 'https://london.edu/faculty/john-doe',
            'language': 'en',
            'description': 'Professor of Finance'
        },
        'dom': {
            'tag': 'html',
            'children': [
                {
                    'tag': 'body',
                    'children': [
                        {
                            'tag': 'main',
                            'children': [
                                {
                                    'tag': 'section',
                                    'attrs': {'class': 'profile'},
                                    'children': [
                                        {'tag': 'h1', 'text': 'Professor John Doe'},
                                        {'tag': 'h2', 'text': 'Professor of Finance'},
                                        {'tag': 'p', 'text': 'Leading expert in corporate finance and strategy.'}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        'links': []
    }


@pytest.fixture
def sample_news_page() -> Dict[str, Any]:
    """Sample news article page data"""
    return {
        'url': 'https://london.edu/news/2024/digital-transformation',
        'metadata': {
            'title': 'Digital Transformation in Business',
            'canonical_url': 'https://london.edu/news/2024/digital-transformation',
            'language': 'en',
            'publishedAt': '2024-01-15T10:00:00Z'
        },
        'dom': {
            'tag': 'html',
            'children': [
                {
                    'tag': 'body',
                    'children': [
                        {
                            'tag': 'article',
                            'children': [
                                {'tag': 'h1', 'text': 'Digital Transformation in Business'},
                                {'tag': 'time', 'attrs': {'datetime': '2024-01-15'}, 'text': 'January 15, 2024'},
                                {'tag': 'p', 'text': 'The impact of digital transformation on modern business practices.'}
                            ]
                        }
                    ]
                }
            ]
        },
        'links': []
    }


@pytest.fixture
def malformed_page_data() -> Dict[str, Any]:
    """Malformed page data for edge case testing"""
    return {
        'url': 'https://london.edu/invalid',
        'metadata': {},  # Missing required fields
        'dom': {
            'tag': 'div',  # Not html root
            'children': []
        },
        'links': None  # Should be list
    }


@pytest.fixture
def empty_page_data() -> Dict[str, Any]:
    """Empty page data for edge case testing"""
    return {
        'url': 'https://london.edu/empty',
        'metadata': {
            'title': 'Empty Page',
            'canonical_url': 'https://london.edu/empty',
            'language': 'en'
        },
        'dom': {
            'tag': 'html',
            'children': []
        },
        'links': []
    }


@pytest.fixture
def sample_text_hashes() -> Dict[str, str]:
    """Sample text hash mappings"""
    texts = [
        'Transform your career with our world-class MBA',
        'Our MBA programme offers a transformative learning experience.',
        '15-21 months duration',
        'Global cohort',
        'World-class faculty'
    ]

    hashes = {}
    for text in texts:
        normalized = ' '.join(text.split())
        hash_value = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        hashes[hash_value] = text

    return hashes


# ==================== Mock Classes ====================

class MockNode:
    """Mock graph node for testing"""

    def __init__(self, node_id: str, node_type: str, data: Dict[str, Any]):
        self.id = node_id
        self.node_type = node_type
        self.data = data
        self.edges_out = []
        self.edges_in = []

    def __repr__(self):
        return f"MockNode({self.node_type}:{self.id})"


class MockEdge:
    """Mock graph edge for testing"""

    def __init__(self, from_node: str, to_node: str, edge_type: str, data: Dict[str, Any] = None):
        self.from_node = from_node
        self.to_node = to_node
        self.edge_type = edge_type
        self.data = data or {}

    def __repr__(self):
        return f"MockEdge({self.from_node})-[{self.edge_type}]->({self.to_node})"


class MockGraph:
    """Mock graph database for testing"""

    def __init__(self):
        self.nodes: Dict[str, MockNode] = {}
        self.edges: List[MockEdge] = []

    def add_node(self, node_id: str, node_type: str, data: Dict[str, Any]) -> MockNode:
        node = MockNode(node_id, node_type, data)
        self.nodes[node_id] = node
        return node

    def get_node(self, node_id: str) -> MockNode:
        return self.nodes.get(node_id)

    def add_edge(self, from_node: str, to_node: str, edge_type: str, data: Dict[str, Any] = None):
        edge = MockEdge(from_node, to_node, edge_type, data)
        self.edges.append(edge)

        # Update node edge lists
        if from_node in self.nodes:
            self.nodes[from_node].edges_out.append(edge)
        if to_node in self.nodes:
            self.nodes[to_node].edges_in.append(edge)

        return edge

    def get_edges(self, from_node: str = None, to_node: str = None, edge_type: str = None) -> List[MockEdge]:
        filtered = self.edges

        if from_node:
            filtered = [e for e in filtered if e.from_node == from_node]
        if to_node:
            filtered = [e for e in filtered if e.to_node == to_node]
        if edge_type:
            filtered = [e for e in filtered if e.edge_type == edge_type]

        return filtered

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.edges)


@pytest.fixture
def mock_graph():
    """Fixture providing a mock graph database"""
    return MockGraph()


# ==================== Helper Functions ====================

def generate_test_hash(text: str) -> str:
    """Generate SHA-256 hash for test text"""
    normalized = ' '.join(text.split())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def create_test_page(
    url: str = 'https://london.edu/test',
    page_type: str = 'program',
    num_sections: int = 2
) -> Dict[str, Any]:
    """Create test page data"""
    sections = []
    for i in range(num_sections):
        sections.append({
            'tag': 'section',
            'attrs': {'class': f'section-{i}'},
            'children': [
                {'tag': 'h2', 'text': f'Section {i}'},
                {'tag': 'p', 'text': f'Content for section {i}'}
            ]
        })

    return {
        'url': url,
        'metadata': {
            'title': f'Test Page - {page_type}',
            'canonical_url': url,
            'language': 'en'
        },
        'dom': {
            'tag': 'html',
            'children': [
                {
                    'tag': 'body',
                    'children': [
                        {
                            'tag': 'main',
                            'children': sections
                        }
                    ]
                }
            ]
        },
        'links': []
    }


@pytest.fixture
def test_page_factory():
    """Factory fixture for creating test pages"""
    return create_test_page


# ==================== Performance Helpers ====================

@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()
            return self.elapsed()

        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# ==================== Test Data Paths ====================

@pytest.fixture
def test_data_dir(tmp_path) -> Path:
    """Temporary directory for test data"""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_parsed_pages(test_data_dir, sample_page_data) -> Path:
    """Create sample parsed pages directory structure"""
    pages_dir = test_data_dir / "parsed"
    pages_dir.mkdir()

    # Create sample page directory
    page_dir = pages_dir / "mba"
    page_dir.mkdir()

    # Write files
    with open(page_dir / "dom.json", 'w') as f:
        json.dump(sample_page_data['dom'], f, indent=2)

    with open(page_dir / "metadata.json", 'w') as f:
        json.dump(sample_page_data['metadata'], f, indent=2)

    with open(page_dir / "links.json", 'w') as f:
        json.dump(sample_page_data['links'], f, indent=2)

    return pages_dir


# ==================== Pytest Configuration ====================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "edge_case: Edge case tests")
