# Topic Clustering & Hierarchy Builder

**Phase 3 Deliverable** - Semantic enrichment through topic clustering and hierarchy construction.

## Overview

This system clusters topics by co-occurrence patterns and builds a parent-child hierarchy, creating a taxonomy from flat topic lists.

## Features

- **Co-occurrence Analysis**: Builds topic similarity from page-topic relationships
- **Hierarchical Clustering**: Groups similar topics using Ward linkage
- **Hierarchy Construction**: Creates parent-child relationships (CHILD_OF edges)
- **Visualization**: Generates Mermaid diagrams with color-coded depth levels
- **Zero-Cost**: Pure graph analysis, no API calls required

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Topic Clustering Pipeline                  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  1. Load Graph          │  Load Topic nodes and HAS_TOPIC   │
│                         │  edges from JSON graph             │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  2. Build Co-occurrence │  Calculate Jaccard similarity      │
│     Matrix              │  between topic pairs               │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  3. Cluster Topics      │  Hierarchical clustering with      │
│                         │  3-5 clusters                       │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  4. Build Hierarchy     │  Create CHILD_OF edges based on    │
│                         │  cluster centroids and frequency   │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  5. Enrich Graph        │  Add CHILD_OF edges to graph with  │
│                         │  confidence scores                 │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  6. Generate Outputs    │  Mermaid diagrams, statistics,     │
│                         │  enriched graph JSON               │
└──────────────────────────────────────────────────────────────┘
```

## Components

### 1. TopicClusterAnalyzer (`src/enrichment/topic_cluster_analyzer.py`)

Clusters topics using co-occurrence patterns.

**Key Methods:**
- `load_topics_from_graph()`: Extract topics and build page-topic mappings
- `build_similarity_matrix()`: Calculate Jaccard similarity
- `cluster_topics()`: Hierarchical clustering
- `export_clusters()`: Generate cluster statistics

**Algorithm:**
```python
# Jaccard Similarity
similarity(A, B) = |A ∩ B| / |A ∪ B|

# Where A and B are sets of pages containing each topic
```

### 2. TopicHierarchyBuilder (`src/enrichment/topic_hierarchy_builder.py`)

Builds parent-child relationships.

**Key Methods:**
- `load_topics_and_clusters()`: Load input data
- `build_hierarchy()`: Create CHILD_OF relationships
- `generate_mermaid()`: Create visualization

**Strategies:**
1. **Cluster-based**: Cluster centroid becomes parent
2. **Frequency-based**: High-frequency topics become parents
3. **Similarity-based**: Name overlap suggests parent-child

### 3. TopicClusterEnricher (`src/enrichment/topic_cluster_enricher.py`)

Master orchestrator.

**Key Methods:**
- `load_graph()`: Load input graph
- `run_clustering()`: Execute clustering pipeline
- `run_hierarchy_building()`: Build hierarchy
- `enrich_graph()`: Add CHILD_OF edges
- `generate_visualizations()`: Create output files
- `run_pipeline()`: Execute full pipeline

### 4. CLI Script (`scripts/enrich_topic_clusters.py`)

Command-line interface for the pipeline.

## Usage

### Basic Usage

```bash
python scripts/enrich_topic_clusters.py \
    --graph data/graph.json
```

### Advanced Usage

```bash
python scripts/enrich_topic_clusters.py \
    --graph data/graph.json \
    --clusters 5 \
    --confidence 0.6 \
    --similarity 0.3 \
    --output-dir docs \
    --output-graph data/graph_enriched.json
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--graph` | *required* | Input graph JSON with Topic nodes |
| `--clusters` | 5 | Target number of clusters (3-5 recommended) |
| `--confidence` | 0.6 | Minimum confidence for CHILD_OF edges |
| `--similarity` | 0.3 | Minimum similarity for clustering |
| `--output-dir` | docs | Output directory for reports |
| `--output-graph` | data/graph_with_clusters.json | Enriched graph output |

## Output Files

### 1. TOPIC_HIERARCHY.md

Human-readable report with:
- Summary statistics
- Mermaid hierarchy visualization
- Cluster breakdown
- Next steps

### 2. topic_hierarchy.mmd

Mermaid diagram showing:
- Root topics (red)
- Level 1 children (teal)
- Level 2 children (light teal)
- CHILD_OF edges with confidence scores

### 3. cluster_stats.json

Detailed statistics:
```json
{
  "metadata": {
    "created_at": "timestamp",
    "n_clusters": 3,
    "n_relationships": 7
  },
  "clusters": [
    {
      "id": "cluster_0",
      "name": "MBA Programs & Related",
      "topics": ["topic_mba", "topic_leadership", ...],
      "coherence_score": 0.7,
      "size": 5
    }
  ],
  "hierarchy": {
    "relationships": [...],
    "depths": {...}
  }
}
```

### 4. graph_with_clusters.json

Enriched graph with CHILD_OF edges:
```json
{
  "id": "child_of_parent_child",
  "from": "child_topic_id",
  "to": "parent_topic_id",
  "edge_type": "CHILD_OF",
  "data": {
    "confidence": 0.91,
    "relationship_type": "cluster_based",
    "created_at": "timestamp"
  }
}
```

## Graph Requirements

Input graph must contain:

1. **Topic Nodes**:
```json
{
  "id": "topic_id",
  "node_type": "Topic",
  "data": {
    "name": "Topic Name",
    "frequency": 10,
    "importance": 0.8
  }
}
```

2. **HAS_TOPIC Edges**:
```json
{
  "from": "page_id",
  "to": "topic_id",
  "edge_type": "HAS_TOPIC"
}
```

## Performance

- **Time**: ~1 minute for 20-30 topics
- **Cost**: $0 (no API calls)
- **Memory**: O(n²) for similarity matrix
- **Scalability**: Efficient up to 100 topics

## Example Output

### Test Graph Results

```
Topics: 10
Pages: 3
Execution: 0.08 seconds

Clusters: 3
├── MBA Programs & Related (5 topics, coherence: 0.70)
├── Executive Education & Related (2 topics, coherence: 0.50)
└── Research & Related (3 topics, coherence: 1.00)

Hierarchy:
├── MBA Programs (root)
│   ├── Leadership Development (0.91)
│   ├── Finance (0.91)
│   ├── Business Strategy (0.91)
│   └── Marketing (0.91)
├── Executive Education (root)
│   └── Innovation (0.85)
└── Research (root)
    ├── Faculty (1.00)
    └── Entrepreneurship (1.00)
```

## Algorithm Details

### Clustering Algorithm

1. **Similarity Calculation**: Jaccard similarity on page co-occurrence
2. **Clustering Method**: Agglomerative hierarchical clustering
3. **Linkage**: Average linkage between cluster centroids
4. **Stopping Criterion**: Target number of clusters (n_clusters parameter)

### Hierarchy Building

1. **Cluster-based**: Centroid (most connected topic) becomes parent
2. **Confidence**: Based on cluster coherence (0.7 + coherence * 0.3)
3. **Frequency-based**: Top 20% frequent topics can be parents
4. **Cycle Detection**: Remove cycles by removing lowest confidence edges
5. **Depth Calculation**: BFS from roots to assign depths

## Integration

### With Topic Extraction

Run after topic extraction:
```bash
# Step 1: Extract topics
python scripts/enrich_topics.py --graph data/graph.json

# Step 2: Cluster and build hierarchy
python scripts/enrich_topic_clusters.py --graph data/graph.json
```

### With Phase 4 Enrichments

Use CHILD_OF edges for:
- Navigation paths
- Topic recommendations
- Semantic search
- Knowledge graph querying

## Testing

### Unit Tests

```bash
pytest tests/test_topic_cluster_analyzer.py
pytest tests/test_topic_hierarchy_builder.py
pytest tests/test_topic_cluster_enricher.py
```

### Integration Test

```bash
python scripts/enrich_topic_clusters.py \
    --graph data/test_graph_with_topics.json \
    --output-dir /tmp/test_output
```

## Troubleshooting

### No Topic Nodes Found

**Error**: "No Topic nodes found in graph"

**Solution**: Run topic extraction first:
```bash
python scripts/enrich_topics.py --graph data/graph.json
```

### Low Coherence Scores

**Issue**: Clusters have low coherence (<0.5)

**Solutions**:
- Increase `--similarity` threshold
- Reduce `--clusters` count
- Check for outlier topics

### Too Many Root Topics

**Issue**: Many topics at depth 0

**Solutions**:
- Lower `--confidence` threshold
- Review topic frequency distribution
- Manually assign parent topics

## Future Enhancements

- [ ] Support for multiple hierarchy levels (3+)
- [ ] Topic merging based on similarity
- [ ] Interactive visualization (D3.js)
- [ ] Automatic parent topic generation
- [ ] Integration with LLM for hierarchy validation

## References

- Hierarchical Clustering: https://en.wikipedia.org/wiki/Hierarchical_clustering
- Jaccard Similarity: https://en.wikipedia.org/wiki/Jaccard_index
- Mermaid Diagrams: https://mermaid.js.org/

## License

MIT License

## Contact

For issues or questions, please open a GitHub issue.
