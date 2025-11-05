# Phase 2: Knowledge Graph Quality Validation - Implementation Guide

**Phase:** 2 - Knowledge Graph Construction
**Status:** Ready for Execution
**Last Updated:** November 5, 2025

---

## Executive Summary

This document describes the comprehensive quality validation framework for Phase 2 of the LBS Knowledge Graph project. The validation suite ensures graph integrity, completeness, and quality meet all technical specifications.

### Validation Components

1. **Graph Validator** (`graph_validator.py`) - Integrity and constraint validation
2. **Completeness Checker** (`completeness_checker.py`) - Coverage analysis
3. **Quality Metrics** (`graph_quality_metrics.py`) - Structural analysis
4. **Master Script** (`run_phase2_validation.py`) - Orchestration

---

## 1. Graph Integrity Validation

### Purpose

Validate that the MGraph knowledge graph maintains structural integrity and satisfies all domain constraints.

### Validation Checks

#### 1.1 Node Validation

**Checks Performed:**
- ✓ Node type validity (Page, Section, ContentItem, Topic, Category, Persona)
- ✓ Required properties presence
- ✓ Property data types
- ✓ Value constraints (e.g., importance 0-1)
- ✓ UUID format validation

**Example:**
```python
from graph_validator import GraphValidator

validator = GraphValidator()
validator.validate_nodes(graph)

# Check results
report = validator.generate_report()
if report['summary']['is_valid']:
    print("✓ All nodes valid")
```

#### 1.2 Edge Validation

**Checks Performed:**
- ✓ Edge type validity (CONTAINS, LINKS_TO, HAS_TOPIC, BELONGS_TO, TARGETS)
- ✓ Source and target nodes exist
- ✓ Edge properties
- ✓ Relationship constraints

#### 1.3 Orphaned Node Detection

**Purpose:** Identify nodes without edges (except taxonomies)

**Valid Isolated Nodes:**
- Topic nodes (pre-defined taxonomy)
- Category nodes (pre-defined taxonomy)

**Invalid Isolated Nodes:**
- Page nodes (must have sections)
- Section nodes (must have content)
- ContentItem nodes (must connect to sections)

#### 1.4 Dangling Edge Detection

**Purpose:** Find edges pointing to non-existent nodes

**Critical Issues:**
- Missing source node
- Missing target node

**Impact:** Graph traversal failures, query errors

#### 1.5 Hierarchy Validation

**Purpose:** Ensure hierarchical relationships form trees (no cycles)

**Hierarchical Relationships:**
- CONTAINS (Page → Section → ContentItem)
- BELONGS_TO (Topic → Category)

**Algorithm:** Depth-First Search (DFS) cycle detection

**Example Violation:**
```
Page A → Section B → Page A  ✗ CYCLE DETECTED
```

#### 1.6 Domain Constraints

**Business Rules:**
- Pages SHOULD have ≥1 Section
- Sections SHOULD have ≥1 ContentItem
- ContentItems MUST have unique hashes within Section
- Topics MUST belong to Category

**Severity:**
- CRITICAL: Data corruption risk
- ERROR: Business rule violation
- WARNING: Best practice deviation
- INFO: Optimization opportunity

### Success Criteria

**PASS Requirements:**
- Zero CRITICAL issues
- Zero ERROR issues
- <10 WARNING issues

---

## 2. Graph Completeness Analysis

### Purpose

Verify that all parsed content is represented in the knowledge graph (NFR6.1: 95%+ completeness).

### Completeness Metrics

#### 2.1 Node Completeness

**Formula:**
```
Node Completeness = (Actual Pages / Expected Pages) × 100
```

**Target:** ≥95%

**Calculation:**
1. Count expected pages from `data/parsed/*.json`
2. Count actual Page nodes in graph
3. Identify missing pages

#### 2.2 Edge Completeness

**Formula:**
```
Edge Completeness = (Actual Links / Expected Links) × 100
```

**Target:** ≥90%

**Links Tracked:**
- Internal page links (LINKS_TO edges)
- Section containment (CONTAINS edges)
- Topic relationships (HAS_TOPIC edges)

#### 2.3 Property Completeness

**Required Properties:**

**Pages:**
- Title: 95%+
- Type: 95%+
- URL: 100%

**Sections:**
- Type: 100%
- Order: 100%

**ContentItems:**
- Hash: 95%+
- Text: 95%+
- Type: 100%

### Missing Entity Analysis

**Identification Process:**
1. Load expected IDs from parsed JSON
2. Query graph for actual IDs
3. Compute difference (missing entities)
4. Categorize by type (Page, Section, ContentItem)

**Example Output:**
```json
{
  "missing_pages": ["page-123", "page-456"],
  "missing_sections": [],
  "missing_content": ["content-789"]
}
```

### Success Criteria

**PASS Requirements:**
- Node completeness ≥95%
- Section completeness ≥95%
- Content completeness ≥95%
- Edge completeness ≥90%

---

## 3. Graph Quality Metrics

### Purpose

Analyze graph structure and connectivity using graph-theoretic measures.

### Metrics Calculated

#### 3.1 Density Metrics

**Graph Density:**
```
Density = |E| / (|V| × (|V| - 1))
```

**Interpretation:**
- 0.0: No edges (disconnected)
- 0.5: Moderately connected
- 1.0: Complete graph (fully connected)

**Expected Range:** 0.01 - 0.10 (typical for knowledge graphs)

**Average Node Degree:**
```
Avg Degree = |E| / |V|
```

**Expected Range:** 3-10 (well-connected structure)

#### 3.2 Connectivity Metrics

**Connected Components:**
- Identifies disconnected subgraphs
- Target: 1 (fully connected graph)

**Largest Component Size:**
- Nodes in largest connected component
- Target: 95%+ of total nodes

**Isolated Nodes:**
- Nodes with zero degree (excluding taxonomies)
- Target: <5% of total nodes

#### 3.3 Path Metrics

**Average Path Length:**
- Mean shortest path between node pairs
- Indicates graph navigability
- Target: <5 hops

**Graph Diameter:**
- Maximum shortest path
- Target: <10 hops

**Algorithm:** Breadth-First Search (BFS) sampling

#### 3.4 Hub Analysis

**Hub Nodes:**
- Nodes with degree ≥ threshold (default: 10)
- Important navigation points

**Identification:**
1. Calculate degree for all nodes
2. Filter by threshold
3. Sort by degree descending

**Expected Hubs:**
- Homepage (high out-degree)
- Main navigation pages
- Popular topics

#### 3.5 Clustering Coefficient

**Formula:**
```
C = (# of closed triplets) / (# of connected triplets)
```

**Interpretation:**
- 0.0: No clustering (tree-like)
- 0.5: Moderate clustering
- 1.0: Complete clustering

**Expected Range:** 0.2-0.6 (hierarchical with cross-links)

### Quality Score

**Composite Score:**
```
Quality Score =
  (Density Weight × Density Norm) +
  (Connectivity Weight × Connectivity Norm) +
  (Clustering Weight × Clustering Norm)
```

**Target:** ≥75/100

---

## 4. Validation Execution

### Prerequisites

```bash
# Install dependencies
pip install mgraph-db

# Verify graph file exists
ls -lh data/graph/lbs_knowledge_graph.json

# Verify parsed data exists
ls -lh data/parsed/
```

### Running Validation

**Full Validation Suite:**
```bash
cd /workspaces/university-pitch/lbs-knowledge-graph

python src/validation/run_phase2_validation.py \
  --graph-file data/graph/lbs_knowledge_graph.json \
  --parsed-dir data/parsed \
  --output-dir data/validation
```

**Individual Validators:**

**Graph Integrity:**
```bash
python src/validation/graph_validator.py \
  --graph-file data/graph/lbs_knowledge_graph.json \
  --output data/validation/graph_validation.json
```

**Completeness:**
```bash
python src/validation/completeness_checker.py \
  --graph-file data/graph/lbs_knowledge_graph.json \
  --parsed-dir data/parsed \
  --output data/validation/completeness.json
```

**Quality Metrics:**
```bash
python src/validation/graph_quality_metrics.py \
  --graph-file data/graph/lbs_knowledge_graph.json \
  --output data/validation/quality_metrics.json
```

### Output Artifacts

**Generated Files:**

```
data/validation/
├── graph_validation_report.json     # Integrity validation
├── completeness_report.json         # Completeness analysis
├── quality_metrics.json             # Structural metrics
└── phase2_validation_results.json   # Comprehensive results

docs/
└── PHASE_2_QUALITY_REPORT.md       # Markdown report
```

### Interpreting Results

**Success Indicators:**

```json
{
  "overall_status": "success",
  "graph_validation": {
    "status": "success",
    "success_rate": 98.5,
    "critical_issues": 0,
    "errors": 0
  },
  "completeness_check": {
    "status": "success",
    "node_completeness": 96.7,
    "passes_requirements": true
  },
  "quality_metrics": {
    "status": "success",
    "density": 0.045,
    "connected_components": 1
  }
}
```

**Failure Indicators:**

```json
{
  "overall_status": "failed",
  "graph_validation": {
    "status": "failed",
    "critical_issues": 5,
    "errors": 23
  }
}
```

---

## 5. Requirements Traceability

### Functional Requirements

| Requirement | Validation Check | Status |
|-------------|------------------|--------|
| FR2.1 | Node types validation | ✓ Implemented |
| FR2.2 | Edge types validation | ✓ Implemented |
| FR2.4 | Graph integrity validation | ✓ Implemented |
| FR2.5 | Export format support | ✓ Supported (MGraph) |

### Non-Functional Requirements

| Requirement | Validation Check | Target | Status |
|-------------|------------------|--------|--------|
| NFR6.1 | Completeness | ≥95% | ✓ Validated |
| Data Integrity | Constraint validation | 0 errors | ✓ Validated |
| Graph Quality | Structural metrics | ≥75/100 | ✓ Measured |

---

## 6. Troubleshooting

### Common Issues

#### Issue: Missing Nodes

**Symptoms:**
- Node completeness <95%
- Many missing_pages in report

**Diagnosis:**
```bash
# Check if graph builder ran
ls -lh data/graph/

# Check parsed data
ls -lh data/parsed/

# Compare counts
grep -c '"id"' data/parsed/*.json
```

**Resolution:**
1. Verify graph builder completed successfully
2. Check for parsing errors in Phase 1
3. Re-run graph construction

#### Issue: Dangling Edges

**Symptoms:**
- Critical issues: dangling edges
- LINKS_TO edges to non-existent nodes

**Diagnosis:**
```python
# Check which nodes are missing
from graph_validator import GraphValidator

validator = GraphValidator()
dangling = validator.check_dangling_edges(graph)

for edge in dangling:
    print(f"Missing: {edge['issue']} - {edge['from_node']} → {edge['to_node']}")
```

**Resolution:**
1. Verify link extraction logic
2. Check for deleted/renamed pages
3. Update LINKS_TO edge creation

#### Issue: Low Graph Density

**Symptoms:**
- Density <0.01
- Few LINKS_TO edges

**Diagnosis:**
```python
from graph_quality_metrics import QualityMetrics

metrics = QualityMetrics()
report = metrics.generate_quality_report(graph)

print(f"Edges: {report['basic']['total_edges']}")
print(f"Links: {report['edge_counts_by_type'].get('LINKS_TO', 0)}")
```

**Resolution:**
1. Review link extraction from HTML
2. Verify internal link detection
3. Check link resolution logic

---

## 7. Best Practices

### Development Workflow

1. **Run validation frequently**
   - After graph building
   - After graph modifications
   - Before deployment

2. **Monitor metrics over time**
   - Track completeness trends
   - Watch for quality degradation
   - Identify structural changes

3. **Set up CI/CD integration**
   ```yaml
   # .github/workflows/validate-graph.yml
   - name: Validate Graph
     run: |
       python src/validation/run_phase2_validation.py \
         --graph-file data/graph/lbs_knowledge_graph.json
   ```

4. **Establish quality gates**
   - Block PRs if validation fails
   - Require manual review for warnings
   - Auto-generate quality reports

### Maintenance

**Weekly:**
- Run full validation suite
- Review quality trends
- Address warnings

**Monthly:**
- Analyze hub node evolution
- Review disconnected components
- Update quality thresholds

**Quarterly:**
- Comprehensive quality audit
- Benchmark against baselines
- Update validation criteria

---

## 8. Next Steps

### Phase 2 Complete

Once validation passes:

1. ✓ Graph integrity confirmed
2. ✓ Completeness verified (95%+)
3. ✓ Quality metrics baseline established
4. → **Proceed to Phase 3: Semantic Enrichment**

### Phase 3 Preview

**Semantic Enrichment:**
- LLM-based topic extraction
- Sentiment analysis
- Audience classification
- Keyword extraction

**Validation Requirements:**
- Topic coverage ≥80%
- Sentiment accuracy ≥85%
- Audience classification ≥90%

---

## 9. Appendix

### A. Graph Statistics (Expected)

**Typical LBS Graph:**
- Pages: 500-1,000
- Sections: 2,000-4,000
- Content Items: 5,000-10,000
- Topics: 100-200
- Categories: 20-30
- Edges: 15,000-30,000

**Density:** 0.03-0.08
**Avg Degree:** 4-8
**Connected Components:** 1
**Clustering:** 0.3-0.5

### B. Performance Benchmarks

**Validation Times:**
- Graph validation: <10 seconds
- Completeness check: <5 seconds
- Quality metrics: <15 seconds
- Total: <30 seconds

**Memory Usage:**
- Graph loading: ~50MB
- Validation: ~100MB
- Peak: ~150MB

### C. References

- [MGraph-DB Documentation](https://github.com/owasp-sbot/MGraph-DB)
- [Technical Specifications](../plans/03_TECHNICAL_SPECIFICATIONS.md)
- [Data Model Schema](../plans/04_DATA_MODEL_SCHEMA.md)
- [Testing Strategy](../plans/07_TESTING_STRATEGY.md)

---

**Document Version:** 1.0
**Last Updated:** November 5, 2025
**Maintained By:** Quality Validation Agent
