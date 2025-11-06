# Semantic Similarity Enrichment

## Overview

The semantic similarity enrichment system automatically identifies and links related pages in the knowledge graph based on their semantic content. It uses OpenAI embeddings to create `RELATED_TO` edges between pages with similar meanings, topics, or themes.

## Features

- **Embedding Generation**: Creates embeddings using OpenAI's `text-embedding-ada-002` model
- **Intelligent Caching**: Caches embeddings to minimize API costs
- **Cosine Similarity**: Calculates semantic similarity between all page pairs
- **Automatic Edge Creation**: Creates `RELATED_TO` edges with metadata
- **Topic Analysis**: Identifies shared topics between related pages
- **Reasoning Generation**: Provides human-readable explanations for relationships

## Architecture

### Components

1. **EmbeddingGenerator** (`embedding_generator.py`)
   - Generates embeddings for page content
   - Handles batching and rate limiting
   - Implements caching for cost optimization

2. **SimilarityCalculator** (`similarity_calculator.py`)
   - Calculates cosine similarity between embeddings
   - Finds top-k most similar pages
   - Provides similarity statistics

3. **RelatedToBuilder** (`related_to_builder.py`)
   - Creates `RELATED_TO` edges
   - Analyzes shared topics
   - Generates relationship reasoning

4. **SimilarityEnricher** (`similarity_enricher.py`)
   - Orchestrates the complete pipeline
   - Manages configuration
   - Tracks statistics and performance

## Usage

### Command Line

Basic usage:
```bash
python scripts/enrich_similarity.py --graph data/graph.json
```

With custom threshold:
```bash
python scripts/enrich_similarity.py \
  --graph data/graph.json \
  --threshold 0.8 \
  --top-k 10
```

All options:
```bash
python scripts/enrich_similarity.py \
  --graph data/graph.json \
  --output data/enriched_graph.json \
  --stats data/similarity_stats.json \
  --threshold 0.7 \
  --top-k 5 \
  --batch-size 100 \
  --cache-dir .cache/embeddings \
  --verbose
```

### Python API

```python
from enrichment import SimilarityEnricher
from enrichment.embedding_generator import EmbeddingConfig
from enrichment.similarity_calculator import SimilarityConfig
from enrichment.related_to_builder import EdgeConfig

# Configure components
embedding_config = EmbeddingConfig(
    model="text-embedding-ada-002",
    batch_size=100,
    cache_dir=Path(".cache/embeddings")
)

similarity_config = SimilarityConfig(
    similarity_threshold=0.7,
    top_k=5,
    min_similarity=0.5
)

edge_config = EdgeConfig(
    min_similarity=0.7,
    max_edges_per_page=5,
    add_reasoning=True
)

# Create enricher
enricher = SimilarityEnricher(
    embedding_config=embedding_config,
    similarity_config=similarity_config,
    edge_config=edge_config
)

# Enrich graph
enriched_graph = enricher.enrich_graph(graph)

# Get statistics
stats = enricher.get_stats()
enricher.print_summary()
```

## Configuration

### Embedding Configuration

```python
EmbeddingConfig(
    model="text-embedding-ada-002",  # OpenAI embedding model
    batch_size=100,                   # Batch size for API calls
    max_retries=3,                    # Retry attempts on failure
    retry_delay=1.0,                  # Delay between retries (seconds)
    cache_dir=Path(".cache"),         # Cache directory
    api_key=None                      # OpenAI API key (or use env var)
)
```

### Similarity Configuration

```python
SimilarityConfig(
    similarity_threshold=0.7,          # Minimum similarity for edges
    top_k=5,                          # Number of top similar pages
    min_similarity=0.5,               # Minimum similarity to consider
    max_similarities_per_page=10      # Maximum edges per page
)
```

### Edge Configuration

```python
EdgeConfig(
    min_similarity=0.7,               # Minimum similarity for edge creation
    max_edges_per_page=5,             # Maximum edges per page
    require_shared_topics=False,      # Require shared topics
    min_shared_topics=1,              # Minimum shared topics
    add_reasoning=True                # Generate reasoning text
)
```

## Environment Setup

Required environment variable:
```bash
export OPENAI_API_KEY="sk-..."
```

Or create a `.env` file:
```env
OPENAI_API_KEY=sk-...
```

## RELATED_TO Edge Structure

```json
{
  "source": "page1_id",
  "target": "page2_id",
  "edge_type": "RELATED_TO",
  "data": {
    "similarity": 0.85,
    "shared_topics": ["mba", "finance"],
    "reasoning": "high semantic similarity; shared topics: mba, finance"
  }
}
```

## Performance & Cost

### Expected Performance

For a graph with 10 pages:
- **Embeddings**: ~10 API calls (with caching)
- **Comparisons**: 45 pairwise comparisons
- **Edges**: ~25 RELATED_TO edges (with threshold 0.7)
- **Duration**: ~5-10 seconds
- **Cost**: ~$0.001 USD

### Cost Optimization

1. **Enable Caching**: Embeddings are cached automatically
2. **Batch Processing**: Requests are batched for efficiency
3. **Threshold Tuning**: Higher thresholds = fewer edges = lower cost
4. **Top-K Limiting**: Limit edges per page to reduce processing

### Scaling

| Pages | Embeddings | Comparisons | Est. Cost | Duration |
|-------|-----------|-------------|-----------|----------|
| 10    | 10        | 45          | $0.001    | 5s       |
| 50    | 50        | 1,225       | $0.005    | 30s      |
| 100   | 100       | 4,950       | $0.010    | 2min     |
| 500   | 500       | 124,750     | $0.050    | 10min    |

## Statistics

The enricher tracks comprehensive statistics:

```json
{
  "pages_processed": 10,
  "embeddings_generated": 10,
  "similarities_calculated": 25,
  "edges_created": 25,
  "duration_seconds": 8.5,
  "embedding_stats": {
    "total_requests": 10,
    "api_calls": 10,
    "cache_hits": 0,
    "cache_hit_rate": 0.0,
    "total_tokens": 1500,
    "estimated_cost": 0.00015
  },
  "similarity_stats": {
    "total_comparisons": 45,
    "similarities_above_threshold": 25,
    "mean": 0.75,
    "median": 0.78,
    "min": 0.70,
    "max": 0.92
  },
  "edge_stats": {
    "total_edges_created": 25,
    "edges_with_shared_topics": 18,
    "average_shared_topics": 2.3
  }
}
```

## Testing

Run unit tests:
```bash
pytest tests/test_similarity_enrichment.py -v
```

Test with sample data:
```bash
python src/enrichment/embedding_generator.py
python src/enrichment/similarity_calculator.py
python src/enrichment/related_to_builder.py
python src/enrichment/similarity_enricher.py
```

## Troubleshooting

### API Key Error
```
ValueError: OpenAI API key required
```
**Solution**: Set `OPENAI_API_KEY` environment variable

### Import Error
```
ImportError: openai package not installed
```
**Solution**: `pip install openai`

### Low Similarity Scores
**Solution**:
- Lower the `similarity_threshold`
- Check embedding quality
- Verify page content is meaningful

### Too Many Edges
**Solution**:
- Increase `similarity_threshold`
- Reduce `max_edges_per_page`
- Enable `require_shared_topics`

## Best Practices

1. **Start with Defaults**: Use default thresholds (0.7) initially
2. **Enable Caching**: Always use cache_dir to save costs
3. **Monitor Costs**: Track `estimated_cost` in stats
4. **Validate Results**: Review edge reasoning for quality
5. **Tune Thresholds**: Adjust based on your domain
6. **Batch Processing**: Process large graphs in chunks

## Integration with Pipeline

### Phase 3 Workflow

```bash
# Step 1: LLM-based enrichment (topics, sentiment, personas)
python scripts/enrich_llm.py --graph data/graph.json

# Step 2: Semantic similarity enrichment
python scripts/enrich_similarity.py \
  --graph data/graph_with_personas.json \
  --output data/graph_with_similarity.json

# Step 3: Validate and export
python scripts/validate_graph.py data/graph_with_similarity.json
```

### Memory Storage

Store statistics in swarm memory:
```bash
npx claude-flow@alpha hooks memory-set \
  --key "swarm/similarity/stats" \
  --value "$(cat data/similarity_stats.json)"
```

## Future Enhancements

- [ ] Support for other embedding models (Anthropic, HuggingFace)
- [ ] Multilingual embedding support
- [ ] Incremental updates (add new pages without full recomputation)
- [ ] Advanced similarity metrics (Manhattan, Euclidean)
- [ ] Visualization of similarity clusters
- [ ] A/B testing of different thresholds
- [ ] Integration with vector databases (Pinecone, Weaviate)

## References

- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)
- [Vector Embeddings Guide](https://www.pinecone.io/learn/vector-embeddings/)
