# Knowledge Graph Enrichment - Sentiment Analysis

This module provides sentiment analysis capabilities for the LBS Knowledge Graph.

## Overview

The sentiment enrichment pipeline:
1. Loads graph from Phase 2 (`data/graph/graph.json`)
2. Extracts all ContentItem nodes (3,743 items)
3. Analyzes sentiment using OpenAI GPT-4o-mini
4. Updates graph with sentiment metadata
5. Propagates sentiment to parent Section and Page nodes
6. Exports enriched graph with statistics

## Components

### 1. Models (`models.py`)
- `SentimentPolarity`: Enum for sentiment classification (positive/negative/neutral/mixed)
- `SentimentScore`: Pydantic model with polarity, score (0-1), and confidence (0-1)
- `ContentItemWithSentiment`: Container for enriched content items

### 2. LLM Client (`llm_client.py`)
- OpenAI API integration using `gpt-4o-mini` model
- Batch processing for efficiency (50 items per batch)
- Cost tracking and usage statistics
- Automatic retries on failure

### 3. Sentiment Analyzer (`sentiment_analyzer.py`)
- Single content item analysis
- Batch processing with progress tracking
- Sentiment aggregation for hierarchies (weighted average)
- Caching for performance

### 4. Sentiment Enricher (`sentiment_enricher.py`)
- Load graph from JSON
- Extract and enrich ContentItem nodes
- Propagate sentiment to Sections (weighted by word count)
- Propagate sentiment to Pages (weighted by section size)
- Export enriched graph

## Usage

### Test Sentiment Analysis

Run test on sample content:

```bash
cd lbs-knowledge-graph
export OPENAI_API_KEY="your-key-here"
python scripts/test_sentiment.py
```

Expected output:
- 4 sample texts analyzed
- Sentiment polarity, score, and confidence displayed
- Batch processing test
- Cost and token usage statistics

### Run Full Enrichment

Enrich entire graph with sentiment:

```bash
cd lbs-knowledge-graph
export OPENAI_API_KEY="your-key-here"
python scripts/enrich_sentiment.py
```

The script will:
1. Load graph from `data/graph/graph.json`
2. Display content item count and cost estimate
3. Ask for confirmation before making API calls
4. Process all ContentItems in batches of 50
5. Show progress bar during processing
6. Export enriched graph to `data/graph/graph_with_sentiment.json`
7. Generate report in `data/graph/sentiment_report.json`

## Output

### Enriched Graph Format

Each node with sentiment will have a `sentiment` field in its `data`:

```json
{
  "id": "content_item_123",
  "node_type": "ContentItem",
  "data": {
    "text": "London Business School offers world-class programs...",
    "sentiment": {
      "polarity": "positive",
      "score": 0.823,
      "confidence": 0.912,
      "magnitude": 0.646
    }
  }
}
```

### Sentiment Report Format

```json
{
  "timestamp": "2025-11-05T20:00:00",
  "duration_seconds": 245.3,
  "graph_stats": {
    "total_nodes": 3963,
    "content_items": 3743,
    "content_with_sentiment": 3743,
    "sentiment_distribution": {
      "positive": 1856,
      "negative": 243,
      "neutral": 1521,
      "mixed": 123
    },
    "average_sentiment_score": 0.567,
    "average_confidence": 0.834
  },
  "api_stats": {
    "api_calls": 75,
    "total_tokens": 112500,
    "total_cost": 8.43
  }
}
```

## Sentiment Propagation

### ContentItem → Section

Sections aggregate sentiment from all child ContentItems using weighted average:
- Weight = word count of content item
- Higher weight for longer, more substantive content

### Section → Page

Pages aggregate sentiment from all child Sections using weighted average:
- Weight = number of content items in section
- Higher weight for sections with more content

## Cost Estimates

Using `gpt-4o-mini` (most cost-efficient):
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens
- Average: ~150 tokens per content item
- **Estimated cost for 3,743 items: ~$8-12**

## Performance

- Batch size: 50 items per API call
- Concurrency: Parallel processing within batches
- Expected duration: ~4-6 minutes for full enrichment
- Rate limiting: Automatic retries with exponential backoff

## Error Handling

- API failures: Automatic retries (max 3 attempts)
- JSON parse errors: Fallback to neutral sentiment
- Empty/short text: Skip analysis, assign neutral sentiment
- Invalid responses: Log warning and continue

## Validation

Target accuracy: ≥80% on validation set
- Test script includes expected sentiment for samples
- Manual review of 100 random items recommended
- Check sentiment distribution for reasonableness

## Next Steps

After sentiment enrichment:
1. Validate sentiment accuracy on sample
2. Review sentiment distribution statistics
3. Use enriched graph for topic extraction (Phase 3.2)
4. Use enriched graph for audience classification (Phase 3.3)
