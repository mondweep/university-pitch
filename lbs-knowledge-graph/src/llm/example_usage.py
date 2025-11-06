"""
Example usage of LLM integration module.

Demonstrates how to use the LLM client and batch processor for
knowledge graph enrichment.
"""

import asyncio
import logging
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.llm import LLMClient, BatchProcessor
from src.llm.response_parser import ResponseParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_single_completion():
    """Example: Single LLM completion with caching."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Single Completion")
    print("="*60 + "\n")

    client = LLMClient(
        provider='openai',  # Change to 'anthropic' if needed
        model='gpt-4'
    )

    # Sentiment analysis
    prompt = """Analyze the sentiment of the following content.

Content: The University of Cambridge offers world-class education with exceptional faculty and cutting-edge research opportunities.

Respond with ONLY valid JSON in this format:
{
  "sentiment": "positive" | "negative" | "neutral",
  "confidence": 0.0-1.0,
  "score": -1.0 to 1.0
}"""

    response = await client.complete(prompt, max_tokens=200)
    print(f"Response:\n{response}\n")

    # Parse response
    result = ResponseParser.parse_sentiment(response)
    if result:
        print(f"Sentiment: {result.sentiment}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Score: {result.score:.2f}")

    # Show statistics
    stats = client.get_statistics()
    print(f"\nCost: ${stats['estimated_cost']:.4f}")


async def example_batch_processing():
    """Example: Batch processing with progress tracking."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Batch Processing")
    print("="*60 + "\n")

    # Sample data (simulating knowledge graph nodes)
    items = [
        {
            'id': 1,
            'content': 'Bachelor of Science in Computer Science with focus on AI and machine learning.'
        },
        {
            'id': 2,
            'content': 'Master of Business Administration with specialization in entrepreneurship.'
        },
        {
            'id': 3,
            'content': 'PhD in Molecular Biology researching cancer treatment breakthroughs.'
        },
        {
            'id': 4,
            'content': 'Certificate in Data Science covering Python, statistics, and visualization.'
        },
        {
            'id': 5,
            'content': 'Undergraduate research opportunity in renewable energy systems.'
        }
    ]

    # Initialize client and processor
    client = LLMClient(
        provider='openai',
        model='gpt-4'
    )

    processor = BatchProcessor(
        llm_client=client,
        batch_size=3,  # Small batch for demo
        max_concurrent=2
    )

    # Progress callback
    def show_progress(processed, total):
        percentage = (processed / total) * 100
        print(f"Progress: {processed}/{total} items ({percentage:.1f}%)")

    # Process items
    print(f"Processing {len(items)} items...\n")

    enriched = await processor.process_items_parallel(
        items=items,
        prompt_template='sentiment_analysis',
        max_tokens=200,
        progress_callback=show_progress
    )

    print("\nResults:")
    print("-" * 60)

    for item in enriched:
        result = ResponseParser.parse_sentiment(item.get('llm_response', ''))
        if result:
            print(f"\nItem {item['id']}:")
            print(f"  Content: {item['content'][:60]}...")
            print(f"  Sentiment: {result.sentiment} (confidence: {result.confidence:.2f})")

    # Show statistics
    stats = processor.get_statistics()
    print("\n" + "="*60)
    print("Statistics:")
    print("-" * 60)
    print(f"Total items: {stats['total_items']}")
    print(f"Processed: {stats['processed_items']}")
    print(f"Failed: {stats['failed_items']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Total cost: ${stats['total_cost']:.4f}")
    print(f"Processing time: {stats['elapsed_time']:.2f}s")
    print(f"Items/second: {stats['items_per_second']:.2f}")

    # LLM client statistics
    llm_stats = stats['llm_statistics']
    print(f"\nLLM Client Stats:")
    print(f"  Total requests: {llm_stats['total_requests']}")
    print(f"  API calls: {llm_stats['api_calls']}")
    print(f"  Cached responses: {llm_stats['cached_responses']}")
    print(f"  Cache hit rate: {llm_stats['cache_hit_rate']:.1%}")


async def example_topic_extraction():
    """Example: Topic extraction with custom templates."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Topic Extraction")
    print("="*60 + "\n")

    client = LLMClient()
    processor = BatchProcessor(client, batch_size=2)

    items = [
        {
            'id': 1,
            'content': 'Artificial intelligence and machine learning are revolutionizing healthcare with predictive diagnostics and personalized treatment plans.'
        },
        {
            'id': 2,
            'content': 'Climate change mitigation strategies focus on renewable energy, carbon capture, and sustainable agriculture practices.'
        }
    ]

    enriched = await processor.process_items_parallel(
        items=items,
        prompt_template='topic_extraction',
        max_tokens=300,
        num_topics=5,
        domain='technology'
    )

    print("Extracted Topics:")
    print("-" * 60)

    for item in enriched:
        result = ResponseParser.parse_topics(item.get('llm_response', ''))
        if result:
            print(f"\nItem {item['id']}:")
            for topic in result.topics:
                print(f"  - {topic.name} (confidence: {topic.confidence:.2f})")
                print(f"    Keywords: {', '.join(topic.keywords)}")


async def example_entity_extraction():
    """Example: Named entity recognition."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Named Entity Recognition")
    print("="*60 + "\n")

    client = LLMClient()

    from src.llm.prompts import PromptTemplates
    templates = PromptTemplates()

    content = """
    University of Cambridge is located in Cambridge, England.
    Professor Jane Smith leads the AI Research Lab, which collaborates with
    Microsoft and Google on natural language processing projects.
    The annual AI Summit 2024 will be held in London next month.
    """

    prompt = templates.named_entity_recognition(content)
    response = await client.complete(prompt, max_tokens=300)

    result = ResponseParser.parse_entities(response)
    if result:
        print(f"Found {len(result.entities)} entities:\n")

        # Group by type
        by_type = {}
        for entity in result.entities:
            if entity.type not in by_type:
                by_type[entity.type] = []
            by_type[entity.type].append(entity)

        for entity_type, entities in by_type.items():
            print(f"{entity_type}:")
            for entity in entities:
                print(f"  - {entity.text} (confidence: {entity.confidence:.2f})")
            print()


async def example_cost_comparison():
    """Example: Compare costs across different models."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Cost Comparison")
    print("="*60 + "\n")

    test_prompt = "Analyze sentiment: This is a test prompt for cost estimation."

    models = [
        ('openai', 'gpt-4'),
        ('openai', 'gpt-4-turbo'),
        ('openai', 'gpt-3.5-turbo'),
        ('anthropic', 'claude-3-opus-20240229'),
        ('anthropic', 'claude-3-sonnet-20240229'),
        ('anthropic', 'claude-3-haiku-20240307'),
    ]

    print(f"Prompt length: {len(test_prompt)} chars")
    print(f"Max tokens: 500\n")
    print("-" * 60)

    for provider, model in models:
        client = LLMClient(provider=provider, model=model)
        cost = client.estimate_cost(test_prompt, max_tokens=500)
        print(f"{provider:12} {model:30} ${cost:.6f}")

    print("-" * 60)
    print("\nFor 10 pages (3,963 nodes) with 100 tokens avg per prompt:")

    for provider, model in models:
        client = LLMClient(provider=provider, model=model)
        single_cost = client.estimate_cost("x" * 400, max_tokens=500)  # ~100 tokens
        total_cost = single_cost * 3963
        print(f"{provider:12} {model:30} ${total_cost:.2f}")


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("LLM Integration Module - Example Usage")
    print("="*60)

    try:
        # Check if API keys are configured
        import os
        if not os.getenv('OPENAI_API_KEY') and not os.getenv('ANTHROPIC_API_KEY'):
            print("\n⚠️  WARNING: No API keys found in environment!")
            print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY to run examples.")
            print("See .env.example for configuration.\n")
            return

        # Run examples (comment out as needed)
        await example_single_completion()
        await example_batch_processing()
        await example_topic_extraction()
        await example_entity_extraction()
        await example_cost_comparison()

        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == '__main__':
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    asyncio.run(main())
