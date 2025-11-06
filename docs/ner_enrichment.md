# Named Entity Recognition (NER) Enrichment

## Overview

The NER enrichment pipeline extracts named entities from PDF page content and creates Entity nodes and MENTIONS edges in the knowledge graph.

## Features

- **Entity Extraction**: Uses GPT-4-turbo for high-accuracy entity recognition
- **Entity Types**: PERSON, ORGANIZATION, LOCATION, EVENT
- **Deduplication**: Automatically merges entity variations (e.g., "LBS" and "London Business School")
- **Cost Optimization**: Batch processing with configurable batch sizes
- **Metrics**: Comprehensive statistics and cost tracking

## Architecture

### Components

1. **NERExtractor** (`lbs-knowledge-graph/src/enrichment/ner_extractor.py`)
   - Extracts entities from content using OpenAI GPT-4
   - Handles entity classification and metadata extraction
   - Provides entity resolution and normalization

2. **EntityNodeBuilder** (`src/enrichment/entity_node_builder.py`)
   - Creates Entity nodes in the graph
   - Handles entity deduplication by canonical name
   - Aggregates mention counts and prominence scores

3. **MentionsBuilder** (`src/enrichment/mentions_builder.py`)
   - Creates MENTIONS edges from ContentItem to Entity
   - Aggregates multiple mentions into single edges
   - Includes context, prominence, and confidence metadata

4. **NEREnricher** (`src/enrichment/ner_enricher.py`)
   - Orchestrates the complete NER pipeline
   - Manages batch processing and statistics
   - Provides comprehensive reporting

## Data Model

### Entity Node

```json
{
  "id": "entity-organization-london-business-school",
  "name": "London Business School",
  "entity_type": "ORGANIZATION",
  "aliases": ["London Business School", "LBS"],
  "mention_count": 15,
  "prominence": 0.92,
  "confidence": 0.98,
  "metadata": {
    "type": "Business School",
    "location": "London"
  }
}
```

### MENTIONS Edge

```json
{
  "from": "content-item-123",
  "to": "entity-organization-london-business-school",
  "edge_type": "MENTIONS",
  "data": {
    "mention_count": 3,
    "context": "London Business School is a leading institution...",
    "prominence": "high",
    "confidence": 0.95,
    "entity_texts": ["London Business School", "LBS"],
    "positions": [0, 150, 300]
  }
}
```

## Usage

### CLI Script

```bash
# Basic usage
python scripts/enrich_ner.py --graph data/graph.json

# Test with limited items
python scripts/enrich_ner.py --graph data/graph.json --max-items 10

# Use different model
python scripts/enrich_ner.py --graph data/graph.json --model gpt-4o

# Adjust batch size
python scripts/enrich_ner.py --graph data/graph.json --batch-size 20

# Custom output paths
python scripts/enrich_ner.py \
  --graph data/graph.json \
  --output data/graph_with_ner.json \
  --stats-output data/ner_stats.json
```

### Python API

```python
import asyncio
from graph.mgraph_compat import MGraph
from enrichment.ner_enricher import NEREnricher

# Load graph
graph = MGraph()
graph.load_from_json("data/graph.json")

# Create enricher
enricher = NEREnricher(
    graph=graph,
    api_key="your-openai-key",
    model="gpt-4-turbo",
    batch_size=10
)

# Run enrichment
async def run():
    stats = await enricher.enrich_graph(max_items=None)
    print(f"Entities created: {stats['unique_entities']}")
    print(f"MENTIONS edges: {stats['mentions_created']}")
    print(f"Total cost: ${stats['total_cost']:.2f}")

asyncio.run(run())

# Save enriched graph
graph.save_to_json("data/graph_with_ner.json")
```

## Configuration

### Batch Size

- **Default**: 10 items per batch
- **Small graph**: 5-10 items
- **Large graph**: 20-30 items
- **Rate limits**: Adjust based on API rate limits

### Model Selection

| Model | Speed | Accuracy | Cost | Recommended |
|-------|-------|----------|------|-------------|
| gpt-4-turbo | Medium | High | $10/1M input | ✅ Default |
| gpt-4o | Fast | High | $2.50/1M input | ✅ Cost-effective |
| gpt-3.5-turbo | Very Fast | Medium | $0.50/1M input | ⚠️ Testing only |

## Expected Results

### Sample Statistics (10 Pages)

```
📊 Results:
   • Content Items Processed: 150
   • Entities Extracted: 85
   • Unique Entities: 32
   • MENTIONS Edges Created: 120

💰 Cost:
   • API Calls: 15
   • Total Tokens: 45,000
   • Total Cost: $0.18

⏱️ Performance:
   • Duration: 12.5s
   • Items/sec: 12.0
```

### Entity Distribution

- **ORGANIZATION**: 40-50% (e.g., London Business School, companies)
- **PERSON**: 30-40% (e.g., professors, alumni, staff)
- **LOCATION**: 10-20% (e.g., London, New York, campus locations)
- **EVENT**: 5-10% (e.g., conferences, programmes, initiatives)

### Precision Targets

- **Overall Precision**: ≥ 85%
- **ORGANIZATION**: ≥ 90%
- **PERSON**: ≥ 88%
- **LOCATION**: ≥ 85%
- **EVENT**: ≥ 80%

## Validation

### Automated Validation

The pipeline includes automatic validation:

```python
# Get validation report
validation = enricher.mentions_builder.validate_mentions()

if validation["errors"]:
    print(f"Errors: {len(validation['errors'])}")
else:
    print("✅ All MENTIONS edges valid")
```

### Manual Validation

```bash
# Run validation script
python src/validation/ner_validator.py \
  --graph data/graph_with_ner.json \
  --report data/ner_validation.json
```

## Cost Optimization

### Strategies

1. **Batch Processing**: Process multiple items in parallel
2. **Content Filtering**: Skip very short content (<50 chars)
3. **Skip Enriched**: Avoid re-processing items with existing MENTIONS edges
4. **Model Selection**: Use gpt-4o for cost savings
5. **Max Tokens**: Limit context to 3000 characters

### Cost Calculation

```python
# Estimate cost before running
from enrichment.ner_enricher import NEREnricher

enricher = NEREnricher(graph, model="gpt-4-turbo")
content_items = enricher._get_content_items()

estimated_tokens = len(content_items) * 3000  # ~3000 tokens/item
estimated_cost = (estimated_tokens / 1_000_000) * 10  # $10/1M tokens

print(f"Estimated cost: ${estimated_cost:.2f}")
```

## Error Handling

The pipeline handles various error scenarios:

- **API Errors**: Automatic retry with exponential backoff
- **Rate Limits**: Batch size adjustment
- **JSON Parse Errors**: Skip malformed responses
- **Missing Nodes**: Log warnings for broken references

## Performance Tuning

### Recommended Settings

**Development/Testing:**
```bash
--max-items 10 --batch-size 5 --model gpt-4-turbo
```

**Production (Small):**
```bash
--batch-size 10 --model gpt-4o
```

**Production (Large):**
```bash
--batch-size 20 --model gpt-4o
```

## Troubleshooting

### Issue: High Cost

**Solution**: Use gpt-4o instead of gpt-4-turbo
```bash
--model gpt-4o  # 4x cheaper
```

### Issue: Rate Limit Errors

**Solution**: Reduce batch size
```bash
--batch-size 5  # Default is 10
```

### Issue: Low Precision

**Solution**: Use gpt-4-turbo for better accuracy
```bash
--model gpt-4-turbo  # Higher accuracy
```

### Issue: Memory Errors

**Solution**: Process in chunks
```bash
--max-items 100  # Process in batches
```

## Integration with Phase 3

The NER enrichment is part of Phase 3 alongside:

1. **Topic Extraction** (Phase 3A)
2. **Persona Classification** (Phase 3B)
3. **NER Extraction** (Phase 3C) ← This component
4. **Sentiment Analysis** (Phase 3D)

### Coordination with Claude Flow

```bash
# Pre-task hook
npx claude-flow@alpha hooks pre-task --description "NER extraction"

# Session management
npx claude-flow@alpha hooks session-restore --session-id "swarm-phase3-ner"

# Post-task hook
npx claude-flow@alpha hooks post-task --task-id "phase3-ner"

# Store results in memory
npx claude-flow@alpha hooks memory-set \
  --key "swarm/ner/stats" \
  --value "$(cat data/ner_stats.json)"
```

## Next Steps

After NER enrichment:

1. **Validation**: Run `ner_validator.py` to check precision
2. **Sentiment Analysis**: Continue with Phase 3D
3. **Graph Querying**: Query Entity nodes for insights
4. **Visualization**: Visualize entity co-occurrence networks

## References

- [GPT-4 Documentation](https://platform.openai.com/docs/models/gpt-4)
- [Named Entity Recognition Guide](https://en.wikipedia.org/wiki/Named-entity_recognition)
- [MGraph-DB Documentation](https://github.com/mgraph-db/mgraph)
