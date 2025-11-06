# LLM Integration Module

Cost-optimized LLM API integration for knowledge graph enrichment with support for OpenAI and Anthropic models.

## Features

- **Multi-Provider Support**: OpenAI (GPT-4) and Anthropic (Claude 3)
- **Batch Processing**: Efficient batching (50 items per API call)
- **Response Caching**: Avoid duplicate API calls
- **Rate Limiting**: Configurable rate limits with exponential backoff
- **Cost Tracking**: Real-time cost estimation and monitoring
- **Type Safety**: Pydantic models for response validation
- **Error Handling**: Automatic retries with fallback strategies

## Components

### 1. LLMClient (`llm_client.py`)

Unified client for LLM API calls with caching and rate limiting.

```python
from llm import LLMClient

# Initialize client
client = LLMClient(
    provider='openai',  # or 'anthropic'
    model='gpt-4',      # or 'claude-3-opus-20240229'
    cache_dir='.cache/llm'
)

# Single completion
response = await client.complete(
    prompt="Analyze sentiment: This product is amazing!",
    max_tokens=500
)

# Batch completions (50 items per batch, 5 concurrent)
prompts = ["prompt 1", "prompt 2", ...]
responses = await client.batch_complete(prompts, max_tokens=500)

# Get statistics
stats = client.get_statistics()
print(f"Total cost: ${stats['estimated_cost']:.2f}")
print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
```

**Key Features:**
- Automatic response caching (24-hour TTL)
- Rate limiting (60 requests/minute default)
- Exponential backoff retry (3 attempts)
- Token counting and cost estimation

### 2. BatchProcessor (`batch_processor.py`)

High-level processor for batch enrichment operations.

```python
from llm import LLMClient, BatchProcessor

client = LLMClient()
processor = BatchProcessor(
    llm_client=client,
    batch_size=50,
    max_concurrent=5
)

# Process items with progress tracking
items = [
    {'id': 1, 'content': 'text to analyze...'},
    {'id': 2, 'content': 'more text...'},
    ...
]

def progress_callback(processed, total):
    print(f"Progress: {processed}/{total} ({processed/total:.1%})")

enriched = await processor.process_items_parallel(
    items=items,
    prompt_template='sentiment_analysis',
    max_tokens=500,
    progress_callback=progress_callback
)

# Get statistics
stats = processor.get_statistics()
print(f"Processed: {stats['processed_items']}/{stats['total_items']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"Total cost: ${stats['total_cost']:.2f}")
```

**Key Features:**
- Parallel batch processing
- Progress tracking and reporting
- Automatic retry for failed batches
- Cost accumulation and monitoring

### 3. PromptTemplates (`prompts.py`)

Optimized prompt templates for common enrichment tasks.

```python
from llm.prompts import PromptTemplates

templates = PromptTemplates()

# Sentiment analysis
prompt = templates.sentiment_analysis(
    content="This is great!",
    include_reasoning=True
)

# Topic extraction
prompt = templates.topic_extraction(
    content="AI and machine learning are transforming...",
    num_topics=5,
    domain='technology'
)

# Named entity recognition
prompt = templates.named_entity_recognition(
    content="University of Cambridge offers programs..."
)

# Persona classification
prompt = templates.persona_classification(
    content="...",
    available_personas=['student', 'faculty', 'admin']
)

# Semantic similarity
prompt = templates.semantic_similarity(
    content1="...",
    content2="..."
)
```

**Available Templates:**
- `sentiment_analysis` - Classify sentiment with confidence scores
- `topic_extraction` - Extract 3-5 topics with keywords
- `named_entity_recognition` - Extract people, organizations, locations
- `persona_classification` - Classify target audience
- `semantic_similarity` - Compare content similarity
- `content_categorization` - Categorize into predefined categories
- `key_insights_extraction` - Extract key insights and findings
- `quality_assessment` - Assess content quality dimensions
- `relationship_inference` - Infer relationships for graph edges

### 4. ResponseParser (`response_parser.py`)

Type-safe parsing and validation of LLM responses.

```python
from llm.response_parser import ResponseParser

# Parse sentiment response
result = ResponseParser.parse_sentiment(llm_response)
if result:
    print(f"Sentiment: {result.sentiment}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Score: {result.score:.2f}")

# Parse topics
result = ResponseParser.parse_topics(llm_response)
if result:
    for topic in result.topics:
        print(f"- {topic.name} ({topic.confidence:.2f})")
        print(f"  Keywords: {', '.join(topic.keywords)}")

# Parse entities
result = ResponseParser.parse_entities(llm_response)
if result:
    for entity in result.entities:
        print(f"- {entity.text} ({entity.type}, {entity.confidence:.2f})")

# Generic parser with validation
from llm.response_parser import SentimentResult
result = ResponseParser.validate_and_clean(
    response=llm_response,
    expected_type=SentimentResult
)
```

**Pydantic Models:**
- `SentimentResult`
- `TopicExtractionResult`
- `NERResult`
- `PersonaResult`
- `SimilarityResult`
- `CategorizationResult`
- `InsightsResult`
- `QualityResult`
- `RelationshipResult`

## Configuration

Create a `.env` file with your API keys:

```bash
# LLM Provider Selection
LLM_PROVIDER=openai  # or anthropic

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Model Selection
LLM_MODEL=gpt-4  # or claude-3-opus-20240229

# Batch Processing
LLM_BATCH_SIZE=50
LLM_MAX_CONCURRENT=5

# Caching
LLM_CACHE_ENABLED=true

# Rate Limiting
LLM_RATE_LIMIT_PER_MINUTE=60
```

## Cost Optimization

### Pricing (per 1K tokens)

**OpenAI:**
- GPT-4: $0.03 input / $0.06 output
- GPT-4 Turbo: $0.01 input / $0.03 output
- GPT-3.5 Turbo: $0.0005 input / $0.0015 output

**Anthropic:**
- Claude 3 Opus: $0.015 input / $0.075 output
- Claude 3 Sonnet: $0.003 input / $0.015 output
- Claude 3 Haiku: $0.00025 input / $0.00125 output

### Optimization Strategies

1. **Batching**: Process 50 items per API call (10x cost reduction)
2. **Caching**: Avoid duplicate API calls (24-hour cache TTL)
3. **Concise Prompts**: Optimized templates minimize token usage
4. **Model Selection**: Use Claude 3 Sonnet for best cost/performance
5. **Rate Limiting**: Avoid API throttling penalties

### Cost Estimates

For 10 pages (3,963 nodes):

| Model | Estimated Cost |
|-------|---------------|
| GPT-4 | ~$45 |
| GPT-4 Turbo | ~$15 |
| Claude 3 Opus | ~$23 |
| **Claude 3 Sonnet** | **~$5** ✅ |
| Claude 3 Haiku | ~$0.50 |

**Recommendation**: Use Claude 3 Sonnet for production (best cost/quality balance).

## Usage Example

Complete workflow for enriching knowledge graph nodes:

```python
import asyncio
from llm import LLMClient, BatchProcessor
from llm.response_parser import ResponseParser

async def enrich_knowledge_graph():
    # Initialize client and processor
    client = LLMClient(
        provider='anthropic',
        model='claude-3-sonnet-20240229'
    )
    processor = BatchProcessor(
        llm_client=client,
        batch_size=50,
        max_concurrent=5
    )

    # Load nodes from Neo4j (example)
    nodes = [
        {'id': 1, 'content': 'Bachelor of Science in Computer Science...'},
        {'id': 2, 'content': 'Master of Arts in International Relations...'},
        # ... more nodes
    ]

    # Process sentiment analysis
    print("Analyzing sentiment...")
    enriched = await processor.process_items_parallel(
        items=nodes,
        prompt_template='sentiment_analysis',
        max_tokens=200
    )

    # Parse and save results
    for item in enriched:
        sentiment = ResponseParser.parse_sentiment(item['llm_response'])
        if sentiment:
            # Update Neo4j node with sentiment data
            print(f"Node {item['id']}: {sentiment.sentiment} ({sentiment.confidence:.2f})")

    # Get statistics
    stats = processor.get_statistics()
    print(f"\nProcessing complete:")
    print(f"- Items: {stats['processed_items']}/{stats['total_items']}")
    print(f"- Success rate: {stats['success_rate']:.1f}%")
    print(f"- Total cost: ${stats['total_cost']:.2f}")
    print(f"- Cache hit rate: {stats['llm_statistics']['cache_hit_rate']:.1%}")

# Run enrichment
asyncio.run(enrich_knowledge_graph())
```

## Error Handling

The module includes comprehensive error handling:

- **API Errors**: Automatic retry with exponential backoff
- **Rate Limiting**: Wait and retry when limits are reached
- **Malformed Responses**: Graceful parsing with None returns
- **Network Issues**: Retry up to 3 times
- **Validation Errors**: Pydantic validation with detailed error messages

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run tests
pytest tests/llm/
```

## Performance

- **Throughput**: ~100-150 items/minute (with caching)
- **Latency**: ~2-5 seconds per batch (50 items)
- **Cache Hit Rate**: 40-60% (typical)
- **Success Rate**: >95% (with retries)

## Dependencies

```bash
pip install openai anthropic pydantic
```

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure API keys**: Copy `.env.example` to `.env` and add keys
3. **Run enrichment**: Use the batch processor to enrich your knowledge graph
4. **Monitor costs**: Track usage with `get_statistics()`

## Support

For issues or questions:
- Check the documentation in this README
- Review example usage in the integration tests
- See Phase 3 implementation plan for context
