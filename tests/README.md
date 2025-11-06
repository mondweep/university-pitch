# Phase 3 Semantic Enrichment Test Suite

This directory contains comprehensive tests for Phase 3 semantic enrichment components.

## Test Files (134 Tests Total)

### Core Component Tests

1. **`test_llm_client.py`** (22 tests)
   - LLM client with OpenAI and Anthropic support
   - Response caching and cost tracking
   - Batch processing and retry logic

2. **`test_sentiment.py`** (20 tests)  
   - Sentiment analysis (positive/negative/neutral/mixed)
   - Batch analysis and aggregation
   - Ground truth validation (50 labeled examples)

3. **`test_topics.py`** (14 tests)
   - Topic extraction and frequency analysis
   - Co-occurrence and trending topics
   - Ground truth validation (10 labeled pages)

4. **`test_ner.py`** (20 tests)
   - Named entity recognition (PERSON, ORG, LOCATION, EVENT)
   - Entity relationships and prominence
   - Ground truth validation (10 labeled items)

5. **`test_personas.py`** (15 tests)
   - Persona classification for 6 target audiences
   - Multi-target detection and journey stage mapping
   - Ground truth validation (10 labeled pages)

6. **`test_similarity.py`** (20 tests)
   - Cosine and Jaccard similarity
   - Multi-signal similarity (embeddings + topics + entities)
   - Approximate nearest neighbors

7. **`test_clustering.py`** (15 tests)
   - Topic clustering with hierarchical algorithms
   - Optimal cluster count selection
   - 3-level topic hierarchy

8. **`test_integration_phase3.py`** (8 tests)
   - End-to-end workflow testing
   - Performance benchmarks
   - Error recovery

## Test Fixtures

### Ground Truth Datasets (`fixtures/`)

- **`ground_truth_sentiment.py`** - 50 manually labeled sentiment examples
- **`ground_truth_topics.py`** - 10 pages with topic labels
- **`ground_truth_ner.py`** - 10 content items with entity labels  
- **`ground_truth_personas.py`** - 10 pages with persona labels
- **`mock_llm_responses.py`** - Mock API responses for deterministic testing

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_sentiment.py -v

# Run specific test class
pytest tests/test_sentiment.py::TestGroundTruthValidation -v

# Run only async tests
pytest tests/ -k asyncio -v

# Run with verbose output
pytest tests/ -v --tb=short
```

## Coverage Goals

- **Target Coverage:** ≥80% (statements, branches, functions, lines)
- **Test Count:** 100+ tests ✅ (achieved 134)
- **Ground Truth:** 50+ examples ✅ (achieved 75)

## Test Structure

Each test file follows this structure:

```python
# 1. Imports
import pytest
from unittest.mock import Mock, AsyncMock

# 2. Fixtures
@pytest.fixture
def mock_client():
    return Mock()

# 3. Test Classes (grouped by functionality)
class TestComponentFeature:
    def test_specific_behavior(self):
        # Arrange
        # Act
        # Assert
        pass

# 4. Integration Tests
class TestIntegration:
    @pytest.mark.asyncio
    async def test_workflow(self):
        pass
```

## Test Quality Standards

- **Fast:** Unit tests <100ms
- **Isolated:** No dependencies between tests
- **Repeatable:** Deterministic results
- **Self-validating:** Clear pass/fail
- **Comprehensive:** Edge cases covered

## Documentation

See `/workspaces/university-pitch/docs/PHASE_3_TEST_REPORT.md` for detailed test report.

## CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
- name: Run Phase 3 Tests
  run: |
    pytest tests/ --cov=src --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Contributing

When adding new tests:

1. Follow existing test structure
2. Add ground truth data if testing against labeled examples
3. Mock external API calls
4. Update this README with test counts
5. Ensure ≥80% coverage for new code

---

**Created:** 2025-11-06
**Tests:** 134
**Coverage Target:** ≥80%
