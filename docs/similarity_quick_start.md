# Semantic Similarity Quick Start

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install openai numpy python-dotenv
```

### 2. Set API Key
```bash
export OPENAI_API_KEY="sk-..."
```

### 3. Run Enrichment
```bash
python scripts/enrich_similarity.py \
  --graph lbs-knowledge-graph/data/graph/graph.json \
  --output data/checkpoints/graph_with_similarity.json \
  --stats data/similarity_stats.json
```

## Expected Output

```
Starting similarity enrichment
Input graph: lbs-knowledge-graph/data/graph/graph.json
Output graph: data/checkpoints/graph_with_similarity.json
Statistics: data/similarity_stats.json

Step 1/3: Generating embeddings...
Generated 10 embeddings successfully
Stats: {
  "api_calls": 10,
  "cache_hits": 0,
  "estimated_cost": 0.0001
}

Step 2/3: Calculating similarities...
Found 25 similar page pairs

Step 3/3: Creating RELATED_TO edges...
Created 25 RELATED_TO edges

============================================================
SIMILARITY ENRICHMENT SUMMARY
============================================================

Processing:
  Duration: 8.50 seconds
  Pages processed: 10

Embeddings:
  Generated: 10
  API calls: 10
  Cache hits: 0
  Total tokens: 1,500
  Estimated cost: $0.0001

Similarities:
  Comparisons: 45
  Above threshold: 25

Edges:
  RELATED_TO edges created: 25
  Edges with shared topics: 18
  Average shared topics: 2.3

============================================================

✓ Enriched graph saved to: data/checkpoints/graph_with_similarity.json
✓ Statistics saved to: data/similarity_stats.json

Similarity enrichment completed successfully!
```

## Sample RELATED_TO Edge

```json
{
  "source": "mba_programme_page",
  "target": "executive_mba_page",
  "edge_type": "RELATED_TO",
  "data": {
    "similarity": 0.85,
    "shared_topics": ["mba", "leadership"],
    "reasoning": "high semantic similarity; shared topics: mba, leadership; same page type: programme"
  }
}
```

## Verify Results

```bash
# Check graph structure
python -c "
import json
with open('data/checkpoints/graph_with_similarity.json') as f:
    g = json.load(f)
    print(f'Nodes: {len(g[\"nodes\"])}')
    print(f'Edges: {len(g[\"edges\"])}')
    related = [e for e in g['edges'] if e['edge_type'] == 'RELATED_TO']
    print(f'RELATED_TO edges: {len(related)}')
"

# View statistics
cat data/similarity_stats.json | python -m json.tool
```

## Store in Memory

```bash
npx claude-flow@alpha hooks memory-set \
  --key "swarm/similarity/stats" \
  --value "$(cat data/similarity_stats.json)"
```

## Next Steps

1. **Adjust thresholds** if you have too many/few edges
2. **Enable caching** for subsequent runs
3. **Integrate with Neo4j** to visualize relationships
4. **Validate quality** by reviewing edge reasoning

## Common Issues

### "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### "No module named 'openai'"
```bash
pip install openai numpy
```

### Too many edges
```bash
# Increase threshold
python scripts/enrich_similarity.py \
  --graph data/graph.json \
  --threshold 0.8 \
  --top-k 3
```

### Too few edges
```bash
# Lower threshold
python scripts/enrich_similarity.py \
  --graph data/graph.json \
  --threshold 0.6 \
  --top-k 10
```

## Phase 3 Integration

```bash
# Complete Phase 3 enrichment pipeline
# Assumes graph_with_personas.json exists from LLM enrichment

python scripts/enrich_similarity.py \
  --graph data/checkpoints/graph_with_personas.json \
  --output data/checkpoints/graph_complete.json \
  --stats data/similarity_stats.json \
  --verbose
```

## Cost Estimation

| Pages | Cost (USD) | Duration |
|-------|-----------|----------|
| 10    | $0.0001   | 5s       |
| 50    | $0.0005   | 30s      |
| 100   | $0.001    | 2min     |
| 500   | $0.005    | 10min    |

Based on text-embedding-ada-002 pricing: $0.0001 per 1K tokens
