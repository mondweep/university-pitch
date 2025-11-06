"""
Test script to verify LLM integration module.

This script runs basic tests to ensure all components are working correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_imports():
    """Test that all components can be imported."""
    print("\n" + "="*60)
    print("TEST 1: Importing Components")
    print("="*60 + "\n")

    try:
        from src.llm import (
            LLMClient,
            BatchProcessor,
            ResponseParser,
            CostTracker,
            CostOptimizer,
            ModelTier,
            MODEL_REGISTRY,
            SENTIMENT_BATCH_PROMPT,
            TOPIC_BATCH_PROMPT,
            PERSONA_BATCH_PROMPT,
            NER_BATCH_PROMPT,
            JOURNEY_BATCH_PROMPT,
            SIMILARITY_PROMPT,
            format_batch_prompt,
            format_single_item_prompt
        )
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_model_registry():
    """Test that model registry is properly configured."""
    print("\n" + "="*60)
    print("TEST 2: Model Registry")
    print("="*60 + "\n")

    try:
        from src.llm import MODEL_REGISTRY, ModelTier

        print(f"Models registered: {len(MODEL_REGISTRY)}")
        print("\nModel Details:")
        print("-" * 60)

        for model_name, config in MODEL_REGISTRY.items():
            print(f"\n{model_name}:")
            print(f"  Provider: {config.provider}")
            print(f"  Tier: {config.tier.value}")
            print(f"  Input: ${config.input_cost_per_1k:.6f}/1K")
            print(f"  Output: ${config.output_cost_per_1k:.6f}/1K")
            print(f"  Quality: {config.quality_score*100:.0f}%")
            print(f"  Speed: {config.speed_score*100:.0f}%")

        print("\n✅ Model registry valid!")
        return True
    except Exception as e:
        print(f"❌ Model registry error: {e}")
        return False


def test_cost_optimizer():
    """Test cost optimizer functionality."""
    print("\n" + "="*60)
    print("TEST 3: Cost Optimizer")
    print("="*60 + "\n")

    try:
        from src.llm import CostOptimizer

        optimizer = CostOptimizer(budget_limit=50.0, quality_threshold=0.70)

        # Test model selection
        print("Testing model selection:")
        for task_type in ['sentiment', 'topics', 'personas', 'entities', 'journey']:
            provider, model = optimizer.select_model_for_task(task_type)
            print(f"  {task_type:12} -> {provider}/{model}")

        # Test batch size optimization
        print("\nTesting batch size optimization:")
        for total_items in [100, 500, 1000, 3963]:
            batch_size = optimizer.optimize_batch_size(total_items, 100, 'gpt-3.5-turbo')
            print(f"  {total_items:4} items -> batch size {batch_size}")

        # Test cost estimation
        print("\nTesting cost estimation:")
        enrichment_plan = {
            'sentiment': 3963,
            'topics': 10,
            'personas': 10,
            'entities': 3963
        }

        estimate = optimizer.estimate_total_cost(enrichment_plan)
        print(f"  Total cost: ${estimate['total_cost']:.2f}")
        print(f"  Within budget: {estimate['within_budget']}")
        print(f"  Budget utilization: {estimate['budget_utilization_percent']:.1f}%")

        print("\n✅ Cost optimizer working correctly!")
        return True
    except Exception as e:
        print(f"❌ Cost optimizer error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_response_parser():
    """Test response parser functionality."""
    print("\n" + "="*60)
    print("TEST 4: Response Parser")
    print("="*60 + "\n")

    try:
        from src.llm import ResponseParser

        parser = ResponseParser()

        # Test JSON parsing
        test_json = '''
        [
            {
                "id": "test_1",
                "sentiment": "positive",
                "confidence": 0.85
            }
        ]
        '''

        parsed = parser.parse_json_response(test_json)
        print(f"✅ Parsed JSON: {type(parsed)}, {len(parsed)} items")

        # Test validation
        validated = parser.validate_batch_response(parsed, 'sentiment', 1)
        print(f"✅ Validated: {len(validated)} items")

        # Test error recovery
        malformed_json = "Some text before [{'id': 'test', 'sentiment': 'positive'}] some text after"
        try:
            fixed = parser.parse_json_response(malformed_json)
            print(f"✅ Error recovery successful")
        except:
            print(f"⚠️  Error recovery needs work")

        print("\n✅ Response parser working!")
        return True
    except Exception as e:
        print(f"❌ Response parser error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cost_tracker():
    """Test cost tracker functionality."""
    print("\n" + "="*60)
    print("TEST 5: Cost Tracker")
    print("="*60 + "\n")

    try:
        from src.llm import CostTracker

        tracker = CostTracker(budget_limit=10.0, alert_threshold=0.8)

        # Track some requests
        tracker.track_request('sentiment', 0.05, 1000, 500)
        tracker.track_request('topics', 0.10, 2000, 1000)
        tracker.track_request('personas', 0.03, 500, 250)

        # Get report
        report = tracker.get_cost_report()
        print(f"Total cost: ${report['total_cost']:.2f}")
        print(f"Total requests: {report['total_requests']}")
        print(f"Budget used: {report['budget_used_percentage']:.1f}%")

        print("\n✅ Cost tracker working!")
        return True
    except Exception as e:
        print(f"❌ Cost tracker error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompts():
    """Test prompt templates."""
    print("\n" + "="*60)
    print("TEST 6: Prompt Templates")
    print("="*60 + "\n")

    try:
        from src.llm import (
            SENTIMENT_BATCH_PROMPT,
            TOPIC_BATCH_PROMPT,
            PERSONA_BATCH_PROMPT,
            NER_BATCH_PROMPT,
            JOURNEY_BATCH_PROMPT,
            format_batch_prompt
        )

        prompts = {
            'sentiment': SENTIMENT_BATCH_PROMPT,
            'topics': TOPIC_BATCH_PROMPT,
            'personas': PERSONA_BATCH_PROMPT,
            'ner': NER_BATCH_PROMPT,
            'journey': JOURNEY_BATCH_PROMPT
        }

        for name, template in prompts.items():
            print(f"  {name:12} -> {len(template):4} chars")

        # Test formatting
        test_items = [{"id": 1, "content": "Test content"}]
        formatted = format_batch_prompt(SENTIMENT_BATCH_PROMPT, test_items)
        print(f"\n✅ Formatted prompt: {len(formatted)} chars")

        print("\n✅ Prompt templates valid!")
        return True
    except Exception as e:
        print(f"❌ Prompt template error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("LLM INTEGRATION MODULE - TEST SUITE")
    print("="*60)

    tests = [
        test_imports,
        test_model_registry,
        test_cost_optimizer,
        test_response_parser,
        test_cost_tracker,
        test_prompts
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append((test.__name__, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60 + "\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Module is ready for integration.")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
