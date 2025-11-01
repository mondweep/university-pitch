# Testing and Quality Assurance Strategy

## Overview

This document outlines the comprehensive testing strategy for the LBS Semantic Knowledge Graph platform, ensuring quality, reliability, and performance across all components.

**Testing Philosophy:** Test-Driven Development (TDD) with automated CI/CD integration

**Target Coverage:** 80% minimum code coverage

**Testing Pyramid:**
- 70% Unit Tests
- 20% Integration Tests
- 10% End-to-End Tests

---

## 1. Testing Levels

### 1.1 Unit Testing

**Scope:** Individual functions, classes, and modules

**Framework:**
- Python: pytest
- JavaScript/TypeScript: Jest
- MGraph-DB: pytest with custom fixtures

**Coverage Target:** 85%

**Example: MGraph Operations**
```python
# tests/unit/test_graph_operations.py

import pytest
from mgraph_db import MGraph
from src.graph_builder import LBSGraphBuilder

class TestGraphBuilder:

    @pytest.fixture
    def sample_page_data(self):
        return {
            'id': 'page-1',
            'url': 'https://london.edu/test',
            'title': 'Test Page',
            'type': 'program',
            'sections': [
                {
                    'id': 'section-1',
                    'type': 'hero',
                    'heading': 'Test Section',
                    'order': 0
                }
            ]
        }

    def test_create_page_node(self, sample_page_data):
        """Test that page nodes are created correctly"""
        builder = LBSGraphBuilder()
        graph = builder.build_from_content([sample_page_data])

        # Assert node exists
        page_node = graph.get_node('page-1')
        assert page_node is not None
        assert page_node.data['title'] == 'Test Page'
        assert page_node.node_type == 'Page'

    def test_contains_relationship(self, sample_page_data):
        """Test that CONTAINS relationships are created"""
        builder = LBSGraphBuilder()
        graph = builder.build_from_content([sample_page_data])

        # Get edge
        edges = graph.get_edges(
            from_node='page-1',
            to_node='section-1',
            edge_type='CONTAINS'
        )

        assert len(edges) == 1
        assert edges[0].data['order'] == 0

    def test_graph_query_by_type(self, sample_page_data):
        """Test querying nodes by type"""
        builder = LBSGraphBuilder()
        graph = builder.build_from_content([sample_page_data])

        results = graph.query(
            node_type='Page',
            filters={'type': 'program'}
        )

        assert results.count() == 1
        assert results.first().data['id'] == 'page-1'

    def test_graph_traversal(self, sample_page_data):
        """Test graph traversal operations"""
        builder = LBSGraphBuilder()
        graph = builder.build_from_content([sample_page_data])

        # Traverse from page to sections
        sections = graph.traverse(
            start_node='page-1',
            edge_type='CONTAINS',
            depth=1
        )

        assert sections.count() == 1
        assert sections.first().data['id'] == 'section-1'
```

**Example: Content Parser**
```python
# tests/unit/test_parser.py

def test_html_to_json_conversion():
    """Test HTML to JSON conversion"""
    html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <main>
                <h1>Heading</h1>
                <p>Content</p>
            </main>
        </body>
    </html>
    """

    parser = HTMLParser()
    result = parser.parse(html)

    assert result['dom']['tag'] == 'html'
    assert 'h1' in str(result)
    assert len(result['text_hashes']) > 0

def test_text_hash_generation():
    """Test content hashing"""
    text = "London Business School offers world-class programmes"

    hash1 = generate_hash(text)
    hash2 = generate_hash(text)

    assert hash1 == hash2  # Deterministic
    assert len(hash1) == 64  # SHA-256 length

    # Different text should produce different hash
    hash3 = generate_hash("Different text")
    assert hash1 != hash3

def test_duplicate_content_detection():
    """Test duplicate content identification"""
    texts = [
        "Common footer text",
        "Common footer text",
        "Different content"
    ]

    deduplicator = ContentDeduplicator()
    unique_texts = deduplicator.process(texts)

    assert len(unique_texts) == 2
    assert unique_texts[0]['usage_count'] == 2
```

### 1.2 Integration Testing

**Scope:** Component interactions, API endpoints, database operations

**Framework:** pytest with fixtures, requests library

**Coverage Target:** 75%

**Example: API Integration Tests**
```python
# tests/integration/test_api.py

import pytest
import requests
from mgraph_db import MGraph

@pytest.fixture
def api_client():
    """API client fixture"""
    return APIClient(base_url='http://localhost:3000/v1')

@pytest.fixture
def test_graph(tmp_path):
    """Create test graph"""
    graph = MGraph()

    # Add test data
    graph.add_node('Page', data={'id': 'p1', 'title': 'Test'})
    graph.add_node('Topic', data={'id': 't1', 'name': 'Finance'})
    graph.add_edge('p1', 't1', 'HAS_TOPIC', {'confidence': 0.9})

    # Save to temp file
    graph_file = tmp_path / "test_graph.json"
    graph.save_to_json(str(graph_file))

    return str(graph_file)

class TestPagesAPI:

    def test_list_pages(self, api_client, test_graph):
        """Test GET /pages endpoint"""
        response = api_client.get('/pages', params={'limit': 10})

        assert response.status_code == 200
        assert 'data' in response.json()
        assert 'pagination' in response.json()

    def test_get_page_by_id(self, api_client, test_graph):
        """Test GET /pages/:id endpoint"""
        response = api_client.get('/pages/p1')

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 'p1'
        assert data['title'] == 'Test'

    def test_page_not_found(self, api_client):
        """Test 404 for non-existent page"""
        response = api_client.get('/pages/invalid-id')

        assert response.status_code == 404
        assert 'error' in response.json()

class TestGraphQueryAPI:

    def test_graph_query(self, api_client, test_graph):
        """Test POST /graph/query endpoint"""
        query = {
            'query': 'MATCH (p:Page)-[:HAS_TOPIC]->(t:Topic) RETURN p, t',
            'params': {},
            'limit': 10
        }

        response = api_client.post('/graph/query', json=query)

        assert response.status_code == 200
        assert len(response.json()['results']) > 0

    def test_graph_traversal(self, api_client, test_graph):
        """Test GET /graph/traverse endpoint"""
        params = {
            'start': 'p1',
            'depth': 2,
            'direction': 'outbound',
            'relationship': 'HAS_TOPIC'
        }

        response = api_client.get('/graph/traverse', params=params)

        assert response.status_code == 200
        assert 'paths' in response.json()

class TestSearchAPI:

    def test_full_text_search(self, api_client):
        """Test GET /search endpoint"""
        response = api_client.get('/search', params={
            'q': 'finance',
            'limit': 10
        })

        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert 'total' in data

    def test_filtered_search(self, api_client):
        """Test search with filters"""
        response = api_client.get('/search', params={
            'q': 'mba',
            'type': 'page',
            'topic': 'finance',
            'sentiment': 'positive'
        })

        assert response.status_code == 200
        assert all(r['type'] == 'page' for r in response.json()['results'])
```

**Example: MGraph-DB Integration**
```python
# tests/integration/test_mgraph_integration.py

def test_mgraph_persistence():
    """Test MGraph save and load"""
    graph = MGraph()

    # Add nodes
    graph.add_node('Page', data={'id': 'p1', 'title': 'Test'})
    graph.add_node('Page', data={'id': 'p2', 'title': 'Test 2'})

    # Add edge
    graph.add_edge('p1', 'p2', 'LINKS_TO', {'text': 'Link'})

    # Save
    graph.save_to_json('test_graph.json')

    # Load into new graph
    new_graph = MGraph()
    new_graph.load_from_json('test_graph.json')

    # Verify
    assert new_graph.node_count() == 2
    assert new_graph.edge_count() == 1

    p1 = new_graph.get_node('p1')
    assert p1.data['title'] == 'Test'

def test_mgraph_export_formats():
    """Test MGraph export to various formats"""
    graph = MGraph()
    graph.add_node('Page', data={'id': 'p1', 'title': 'Test'})

    # Test exports
    graph.export_graphml('test.graphml')
    graph.export_cypher('test.cypher')
    graph.export_mermaid('test.mmd')

    # Verify files exist and have content
    assert os.path.exists('test.graphml')
    assert os.path.getsize('test.graphml') > 0

    assert os.path.exists('test.cypher')
    assert 'CREATE' in open('test.cypher').read()

    assert os.path.exists('test.mmd')
    assert 'graph' in open('test.mmd').read()
```

### 1.3 End-to-End Testing

**Scope:** Full user workflows, UI interactions

**Framework:** Playwright (Python)

**Coverage Target:** Critical user paths

**Example: E2E Tests**
```python
# tests/e2e/test_content_discovery.py

from playwright.sync_api import sync_playwright

def test_search_and_view_page():
    """Test user searching and viewing content"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Navigate to search
        page.goto('https://lbs-kg.com/search')

        # Search for "MBA"
        page.fill('input[name="search"]', 'MBA')
        page.click('button[type="submit"]')

        # Wait for results
        page.wait_for_selector('.search-results')

        # Verify results
        results = page.query_selector_all('.search-result')
        assert len(results) > 0

        # Click first result
        results[0].click()

        # Verify page loaded
        page.wait_for_selector('h1')
        assert 'MBA' in page.inner_text('h1')

        browser.close()

def test_topic_navigation():
    """Test navigating by topic"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Navigate to topics
        page.goto('https://lbs-kg.com/topics')

        # Click Finance topic
        page.click('a[href="/topics/finance"]')

        # Verify topic page loaded
        page.wait_for_selector('.topic-content')

        # Verify related content displayed
        content_items = page.query_selector_all('.content-item')
        assert len(content_items) > 0

        browser.close()

def test_persona_portal():
    """Test persona-specific portal"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Navigate to persona selector
        page.goto('https://lbs-kg.com')

        # Select "Prospective Student" persona
        page.click('button[data-persona="prospective_student"]')

        # Verify personalized content
        page.wait_for_selector('.personalized-dashboard')

        # Check for relevant sections
        assert page.is_visible('text=Admissions')
        assert page.is_visible('text=Programmes')

        browser.close()
```

---

## 2. Performance Testing

### 2.1 Load Testing

**Tool:** Locust (Python-based load testing)

**Targets:**
- API endpoints: 100 req/s sustained
- Graph queries: <500ms p95
- Search queries: <1s p95

**Example: Load Test**
```python
# tests/performance/locustfile.py

from locust import HttpUser, task, between

class LBSKGUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def search_content(self):
        """Search for content (most common operation)"""
        queries = ['MBA', 'Finance', 'Leadership', 'Executive Education']
        query = random.choice(queries)

        self.client.get(f'/search?q={query}&limit=10')

    @task(2)
    def get_page(self):
        """Get specific page"""
        page_ids = ['page-1', 'page-2', 'page-3']
        page_id = random.choice(page_ids)

        self.client.get(f'/pages/{page_id}')

    @task(1)
    def graph_query(self):
        """Execute graph query"""
        self.client.post('/graph/query', json={
            'query': 'MATCH (p:Page {type: "program"}) RETURN p LIMIT 10'
        })

    @task(1)
    def browse_topics(self):
        """Browse topics"""
        self.client.get('/topics')

# Run with: locust -f locustfile.py --host=https://api.lbs-kg.com
```

**Performance Benchmarks:**
```bash
# Run load test
locust -f tests/performance/locustfile.py \
  --host=https://api.lbs-kg.com \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m \
  --html=performance_report.html
```

### 2.2 MGraph Performance Tests

```python
# tests/performance/test_mgraph_performance.py

import time
import pytest
from mgraph_db import MGraph

def test_large_graph_query_performance():
    """Test query performance on large graph"""
    graph = MGraph()

    # Create 10,000 nodes
    for i in range(10000):
        graph.add_node('Page', data={'id': f'p{i}', 'index': i})

    # Measure query time
    start = time.time()
    results = graph.query(node_type='Page', filters={'index': 5000})
    duration = time.time() - start

    assert duration < 0.1  # Should be < 100ms (O(1) lookup)
    assert results.count() == 1

def test_graph_traversal_performance():
    """Test traversal performance"""
    graph = MGraph()

    # Create chain of 100 nodes
    for i in range(100):
        graph.add_node('Page', data={'id': f'p{i}'})
        if i > 0:
            graph.add_edge(f'p{i-1}', f'p{i}', 'LINKS_TO')

    # Measure traversal time
    start = time.time()
    path = graph.traverse('p0', edge_type='LINKS_TO', depth=50)
    duration = time.time() - start

    assert duration < 0.5  # Should be < 500ms
    assert path.count() == 50

def test_graph_load_from_s3_performance():
    """Test graph loading from S3 (cold start simulation)"""
    # This tests Lambda cold start performance

    start = time.time()

    # Simulate S3 download
    with open('large_graph.json', 'r') as f:
        graph_data = f.read()

    # Load into MGraph
    graph = MGraph()
    graph.load_from_json_string(graph_data)

    duration = time.time() - start

    # Should load in < 1 second for serverless cold start
    assert duration < 1.0
    assert graph.node_count() > 0
```

---

## 3. Test Data Management

### 3.1 Test Fixtures

**Pytest Fixtures:**
```python
# tests/conftest.py

import pytest
from mgraph_db import MGraph

@pytest.fixture(scope='session')
def test_graph():
    """Create a test graph with sample data"""
    graph = MGraph()

    # Pages
    graph.add_node('Page', data={
        'id': 'mba-page',
        'url': 'https://london.edu/mba',
        'title': 'MBA Programme',
        'type': 'program'
    })

    # Topics
    graph.add_node('Topic', data={
        'id': 'finance-topic',
        'name': 'Finance',
        'category': 'subjects'
    })

    # Relationships
    graph.add_edge('mba-page', 'finance-topic', 'HAS_TOPIC', {
        'confidence': 0.95
    })

    return graph

@pytest.fixture
def sample_pages():
    """Sample page data"""
    return [
        {
            'id': 'page-1',
            'url': 'https://london.edu/programmes',
            'title': 'Programmes',
            'type': 'program'
        },
        {
            'id': 'page-2',
            'url': 'https://london.edu/faculty',
            'title': 'Faculty',
            'type': 'faculty'
        }
    ]

@pytest.fixture
def mock_llm_service(mocker):
    """Mock LLM API calls"""
    mock = mocker.patch('src.llm.OpenAIService')
    mock.analyze_sentiment.return_value = {
        'polarity': 0.8,
        'label': 'positive',
        'confidence': 0.9
    }
    mock.extract_topics.return_value = ['finance', 'mba']
    return mock
```

### 3.2 Test Data Generators

```python
# tests/utils/data_generators.py

from faker import Faker
import random

fake = Faker()

def generate_test_pages(count=10):
    """Generate test page data"""
    pages = []
    page_types = ['program', 'faculty', 'news', 'event']

    for i in range(count):
        pages.append({
            'id': f'page-{i}',
            'url': f'https://london.edu/test/{fake.slug()}',
            'title': fake.sentence(),
            'type': random.choice(page_types),
            'description': fake.paragraph()
        })

    return pages

def generate_test_content(count=50):
    """Generate test content items"""
    content_items = []

    for i in range(count):
        text = fake.paragraph()
        content_items.append({
            'id': f'content-{i}',
            'hash': hashlib.sha256(text.encode()).hexdigest(),
            'text': text,
            'type': 'paragraph'
        })

    return content_items
```

---

## 4. Continuous Integration

### 4.1 GitHub Actions Test Workflow

**.github/workflows/test.yml:**
```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pip install mgraph-db

      - name: Run unit tests
        run: |
          pytest tests/unit \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            --junitxml=junit.xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests

      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: junit.xml

  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run integration tests
        run: |
          pytest tests/integration \
            --cov=src \
            --cov-append \
            --junitxml=junit-integration.xml

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Playwright
        run: |
          pip install playwright pytest-playwright
          playwright install chromium

      - name: Run E2E tests
        run: |
          pytest tests/e2e \
            --browser chromium \
            --headed=false \
            --slowmo=100

  performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Locust
        run: pip install locust

      - name: Run performance tests
        run: |
          locust -f tests/performance/locustfile.py \
            --host=${{ secrets.STAGING_URL }} \
            --users=50 \
            --spawn-rate=5 \
            --run-time=2m \
            --html=performance_report.html \
            --headless

      - name: Upload performance report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: performance_report.html
```

---

## 5. Quality Gates

### 5.1 Code Quality Checks

**Pre-commit Hooks:**
```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### 5.2 Coverage Requirements

**pytest.ini:**
```ini
[pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    --strict-markers
    --cov=src
    --cov-fail-under=80
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Slow running tests
```

### 5.3 Pull Request Requirements

**Required Checks:**
- ✅ All unit tests pass
- ✅ Code coverage ≥ 80%
- ✅ No linting errors
- ✅ Type checking passes
- ✅ Integration tests pass
- ✅ Security scan passes (Snyk/Dependabot)

---

## 6. Test Metrics and Reporting

### 6.1 Test Metrics

**Key Metrics:**
- Test coverage percentage
- Test execution time
- Flaky test rate
- Mean time to detect (MTTD) bugs
- Mean time to resolve (MTTR) bugs

**Dashboard:**
```
Test Metrics Dashboard
├── Coverage Trend (last 30 days)
├── Test Execution Time (by suite)
├── Failure Rate (by test type)
├── Bug Detection Lead Time
└── Test Reliability Score
```

---

**Document Version:** 1.0
**Last Updated:** November 2025
