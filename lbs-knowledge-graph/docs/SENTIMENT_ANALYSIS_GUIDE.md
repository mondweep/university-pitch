# Sentiment Analysis Guide

## Overview

The sentiment analysis system enriches the knowledge graph by analyzing the emotional tone and polarity of all content items. This guide explains how to set up, run, and validate the sentiment analysis.

## Architecture

### Components

1. **LLMClient** (`src/enrichment/llm_client.py`)
   - Handles API calls to OpenAI GPT-4o-mini
   - Tracks costs and usage
   - Implements retry logic and rate limiting

2. **SentimentAnalyzer** (`src/enrichment/sentiment_analyzer.py`)
   - Analyzes individual content items
   - Batch processing for efficiency
   - Sentiment aggregation for hierarchies

3. **SentimentEnricher** (`src/enrichment/sentiment_enricher.py`)
   - Orchestrates full graph enrichment
   - Propagates sentiment from content → sections → pages
   - Generates statistics and reports

4. **Validation** (`scripts/validate_sentiment.py`)
   - Compares LLM results vs ground truth
   - Calculates accuracy, precision, recall
   - Target: ≥80% accuracy

## Setup

### 1. Install Dependencies

```bash
cd /workspaces/university-pitch/lbs-knowledge-graph
source venv/bin/activate
pip install -r requirements-llm.txt
```

### 2. Configure API Key

Edit `.env` file and set your OpenAI API key:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

Or export it directly:

```bash
export OPENAI_API_KEY='sk-your-actual-key-here'
```

### 3. Verify Setup

```bash
python scripts/test_sentiment_setup.py
```

Expected output:
```
✅ ALL CHECKS PASSED - Ready to run sentiment enrichment!
```

## Running Sentiment Analysis

### Full Enrichment

Process all 3,743 content items:

```bash
cd /workspaces/university-pitch/lbs-knowledge-graph
source venv/bin/activate
python scripts/enrich_sentiment.py
```

**Cost estimate**: ~$0.42 (based on gpt-4o-mini pricing)

### Process Flow

1. **Load Graph**: Reads `data/graph/graph.json` (from Phase 2)
2. **Extract ContentItems**: Finds all 3,743 content items
3. **Batch Analysis**: Processes in batches of 50
4. **Update Graph**: Adds sentiment properties to nodes
5. **Propagate**: Aggregates sentiment to sections and pages
6. **Export**: Saves enriched graph and statistics

### Output Files

- `data/graph/graph_with_sentiment.json` - Enriched graph
- `data/graph/sentiment_report.json` - Full analysis report

## Sentiment Model

### Properties Added to Nodes

Each ContentItem, Section, and Page node receives:

```json
{
  "sentiment": {
    "polarity": "positive|negative|neutral|mixed",
    "score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "magnitude": 0.0-1.0
  }
}
```

### Sentiment Categories

- **Positive** (score ≥ 0.6): Enthusiastic, optimistic, promotional
- **Neutral** (0.4 < score < 0.6): Informational, factual, objective
- **Negative** (score ≤ 0.4): Challenging, problematic, cautionary
- **Mixed** (high variance): Contains contradictory sentiments

### Aggregation Logic

Sentiment propagates up the hierarchy using weighted averages:

1. **ContentItem → Section**
   - Weight by word count (longer content = more weight)
   - Filter out low-confidence scores

2. **Section → Page**
   - Weight by number of content items
   - Detect mixed sentiment (high variance)

## Validation

### 1. Create Ground Truth Dataset

First run creates a template with 50 random items:

```bash
python scripts/validate_sentiment.py
```

This creates: `data/validation/sentiment_ground_truth.json`

### 2. Label Ground Truth

Manually label each item:

```json
{
  "id": "item_123",
  "text": "The MBA program offers excellent opportunities...",
  "ground_truth_sentiment": "positive",  // Replace "LABEL_ME"
  "notes": "Clearly positive marketing content"
}
```

### 3. Run Validation

After labeling all items:

```bash
python scripts/validate_sentiment.py
```

### Validation Metrics

- **Accuracy**: Overall correctness (target: ≥80%)
- **Precision**: Correct positive predictions / all positive predictions
- **Recall**: Correct positive predictions / all actual positives
- **F1-Score**: Harmonic mean of precision and recall
- **Confusion Matrix**: Shows classification patterns

### Sample Output

```
================================================================================
  ✅ PASSED - Validation Complete
================================================================================

Overall Accuracy: 85.2%
Correct: 43 / 50

Per-Class Metrics:
  Positive:
    Precision: 88.9%
    Recall: 91.4%
    F1-Score: 90.1%
    Support: 35

  Neutral:
    Precision: 75.0%
    Recall: 60.0%
    F1-Score: 66.7%
    Support: 10

  Negative:
    Precision: 100.0%
    Recall: 80.0%
    F1-Score: 88.9%
    Support: 5
```

## Cost Optimization

### Model Selection

- **gpt-4o-mini**: $0.42 for full enrichment (recommended)
  - Input: $0.150 per 1M tokens
  - Output: $0.600 per 1M tokens

- **gpt-3.5-turbo**: ~$0.30 (cheaper but less accurate)
- **gpt-4-turbo**: ~$5.60 (most accurate but expensive)

### Batch Processing

- Default batch size: 50 items
- Parallel API calls reduce total time
- Automatic retry on failures

### Caching

- Results cached during session
- Prevents duplicate API calls
- Useful for interrupted runs

## Troubleshooting

### Common Issues

**1. "OPENAI_API_KEY not found"**
```bash
# Check if key is set
echo $OPENAI_API_KEY

# If empty, set it:
export OPENAI_API_KEY='sk-your-key-here'

# Or add to .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

**2. "Graph file not found"**
```bash
# Run Phase 2 first to generate graph
python -m src.graph.knowledge_graph_builder
```

**3. "Import errors"**
```bash
# Install dependencies
pip install -r requirements-llm.txt
```

**4. "Rate limit exceeded"**
- Wait 60 seconds and retry
- Or use smaller batch size: `batch_size=10`

**5. "Low accuracy (<80%)"**
- Check ground truth labels for errors
- Ensure diverse sample (positive, neutral, negative)
- Consider using gpt-4-turbo for higher accuracy

## Statistics

### Expected Results

For LBS marketing content (3,743 items):

- **Positive**: ~70% (promotional, enthusiastic)
- **Neutral**: ~25% (informational, factual)
- **Negative**: ~3% (challenges, concerns)
- **Mixed**: ~2% (balanced discussions)

### Average Metrics

- **Sentiment Score**: 0.65-0.75 (slightly positive)
- **Confidence**: 0.75-0.85 (high confidence)
- **Coverage**: 100% of content items

## Integration with Other Enrichments

Sentiment data can be combined with:

1. **Topic Analysis**: Sentiment by topic
2. **Journey Mapping**: Sentiment across user journeys
3. **Persona Analysis**: Sentiment by target persona
4. **Similarity**: Find similar sentiment patterns

## API Reference

### SentimentScore Model

```python
from src.enrichment.models import SentimentScore, SentimentPolarity

score = SentimentScore(
    polarity=SentimentPolarity.POSITIVE,
    score=0.85,
    confidence=0.92,
    magnitude=0.7
)
```

### LLMClient Usage

```python
from src.enrichment.llm_client import LLMClient

client = LLMClient(
    api_key="sk-...",
    model="gpt-4o-mini",
    max_retries=3,
    timeout=30
)

# Analyze single text
sentiment = await client.analyze_sentiment("Great MBA program!")

# Analyze batch
texts = ["Text 1", "Text 2", "Text 3"]
sentiments = await client.analyze_batch(texts, batch_size=50)

# Get usage stats
stats = client.get_stats()
# {api_calls: 5, total_tokens: 1250, total_cost: 0.15}
```

### SentimentEnricher Usage

```python
from src.enrichment.sentiment_enricher import SentimentEnricher

enricher = SentimentEnricher(graph, sentiment_analyzer)

# Enrich full graph
enriched_graph = await enricher.enrich_graph(
    batch_size=50,
    progress_callback=lambda current, total: print(f"{current}/{total}")
)

# Get statistics
stats = enricher.get_statistics()

# Export results
enricher.export_graph(Path("output/enriched_graph.json"))
```

## Next Steps

After sentiment enrichment:

1. **Run Validation**: Ensure ≥80% accuracy
2. **Analyze Distribution**: Check sentiment patterns
3. **Integrate with Topics**: Combine with topic analysis
4. **Generate Visualizations**: Create sentiment heatmaps
5. **Export to Neo4j**: Load enriched graph to database

## Support

For issues or questions:
- Check Phase 3 implementation plan: `plans/01_IMPLEMENTATION_PLAN.md`
- Review data model: `plans/04_DATA_MODEL_SCHEMA.md`
- Check test results: `docs/PHASE_3_TEST_REPORT.md`
