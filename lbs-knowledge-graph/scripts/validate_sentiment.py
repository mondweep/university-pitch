#!/usr/bin/env python3
"""
Sentiment Analysis Validation Script

Validates sentiment analysis accuracy by comparing LLM results against
manually labeled ground truth data.

Target: ≥80% accuracy
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.enrichment.llm_client import LLMClient
from src.enrichment.sentiment_analyzer import SentimentAnalyzer
from src.enrichment.models import SentimentPolarity


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def load_ground_truth(ground_truth_path: Path) -> List[Dict]:
    """
    Load manually labeled ground truth data.

    Format:
    [
        {
            "id": "content_item_id",
            "text": "sample text...",
            "ground_truth_sentiment": "positive|negative|neutral",
            "notes": "optional notes"
        }
    ]
    """
    if not ground_truth_path.exists():
        print(f"❌ Ground truth file not found: {ground_truth_path}")
        print("\n   Creating template ground truth file...")

        # Load graph to sample content items
        project_root = Path(__file__).parent.parent
        graph_path = project_root / "data" / "graph" / "graph.json"

        if not graph_path.exists():
            print(f"❌ Graph file not found: {graph_path}")
            sys.exit(1)

        with open(graph_path, "r", encoding="utf-8") as f:
            graph = json.load(f)

        # Sample 50 random content items
        content_items = [
            node for node in graph["nodes"]
            if node.get("node_type") == "ContentItem"
        ]

        import random
        random.seed(42)
        sampled_items = random.sample(content_items, min(50, len(content_items)))

        # Create template
        template = []
        for item in sampled_items:
            data = item.get("data", {})
            template.append({
                "id": item["id"],
                "text": data.get("text", "")[:200] + "...",  # First 200 chars
                "ground_truth_sentiment": "LABEL_ME",  # User must label
                "notes": ""
            })

        # Save template
        with open(ground_truth_path, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        print(f"   ✅ Created template at: {ground_truth_path}")
        print("\n   📝 PLEASE LABEL THE GROUND TRUTH DATA:")
        print(f"      1. Open: {ground_truth_path}")
        print("      2. For each item, replace 'LABEL_ME' with: positive, negative, or neutral")
        print("      3. Re-run this validation script")
        print()
        sys.exit(0)

    with open(ground_truth_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check if any items are still unlabeled
    unlabeled = [item for item in data if item.get("ground_truth_sentiment") == "LABEL_ME"]
    if unlabeled:
        print(f"⚠️  WARNING: {len(unlabeled)} items still need labeling!")
        print("   Please label all items before validation.")
        sys.exit(0)

    return data


async def validate_sentiment(
    ground_truth: List[Dict],
    llm_client: LLMClient
) -> Tuple[Dict, List[Dict]]:
    """
    Validate sentiment analysis against ground truth.

    Returns:
        Tuple of (metrics_dict, detailed_results)
    """
    print("   Running sentiment analysis on ground truth items...")

    sentiment_analyzer = SentimentAnalyzer(llm_client)

    # Prepare items for analysis
    items_to_analyze = []
    for item in ground_truth:
        items_to_analyze.append({
            "id": item["id"],
            "text": item["text"],
            "word_count": len(item["text"].split())
        })

    # Analyze in batches
    results = await sentiment_analyzer.analyze_batch(items_to_analyze, batch_size=10)

    # Compare with ground truth
    correct = 0
    total = len(ground_truth)
    detailed_results = []

    # Track confusion matrix
    confusion_matrix = {
        "positive": {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0},
        "negative": {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0},
        "neutral": {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
    }

    for gt_item, result in zip(ground_truth, results):
        ground_truth_label = gt_item["ground_truth_sentiment"].lower()
        predicted_label = result.sentiment.polarity.value if result.sentiment else "neutral"

        # Count correct predictions
        if ground_truth_label == predicted_label:
            correct += 1
            match = True
        else:
            match = False

        # Update confusion matrix
        if ground_truth_label in confusion_matrix:
            confusion_matrix[ground_truth_label][predicted_label] += 1

        # Detailed result
        detailed_results.append({
            "id": gt_item["id"],
            "text_preview": gt_item["text"][:100] + "...",
            "ground_truth": ground_truth_label,
            "predicted": predicted_label,
            "confidence": result.sentiment.confidence if result.sentiment else 0.0,
            "score": result.sentiment.score if result.sentiment else 0.5,
            "match": match
        })

    # Calculate metrics
    accuracy = (correct / total) * 100 if total > 0 else 0.0

    # Calculate per-class precision and recall
    per_class_metrics = {}
    for label in ["positive", "negative", "neutral"]:
        # True positives
        tp = confusion_matrix[label][label]

        # False positives (predicted as label but was something else)
        fp = sum(confusion_matrix[other][label] for other in confusion_matrix if other != label)

        # False negatives (was label but predicted as something else)
        fn = sum(confusion_matrix[label][other] for other in confusion_matrix[label] if other != label)

        # Precision and recall
        precision = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        per_class_metrics[label] = {
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1_score": round(f1, 2),
            "support": sum(confusion_matrix[label].values())
        }

    metrics = {
        "accuracy": round(accuracy, 2),
        "correct": correct,
        "total": total,
        "confusion_matrix": confusion_matrix,
        "per_class_metrics": per_class_metrics
    }

    return metrics, detailed_results


async def main():
    """Main validation workflow"""

    print_header("Sentiment Analysis Validation")

    # Load environment variables
    load_dotenv()

    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        print("   Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)

    # Paths
    project_root = Path(__file__).parent.parent
    ground_truth_path = project_root / "data" / "validation" / "sentiment_ground_truth.json"
    report_path = project_root / "data" / "validation" / "sentiment_validation_report.json"

    # Ensure validation directory exists
    ground_truth_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Load ground truth
    print_header("Step 1: Loading Ground Truth")
    ground_truth = load_ground_truth(ground_truth_path)
    print(f"   ✅ Loaded {len(ground_truth)} labeled items")

    # Step 2: Initialize LLM client
    print_header("Step 2: Initializing LLM Client")
    llm_client = LLMClient(
        api_key=api_key,
        model="gpt-4o-mini",
        max_retries=3,
        timeout=30
    )
    print("   ✅ LLM client ready")

    # Step 3: Run validation
    print_header("Step 3: Running Validation")

    start_time = datetime.now()
    metrics, detailed_results = await validate_sentiment(ground_truth, llm_client)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"   ✅ Validation complete in {duration:.1f} seconds")

    # Step 4: Display results
    print_header("Step 4: Validation Results")

    print(f"   Overall Accuracy: {metrics['accuracy']}%")
    print(f"   Correct: {metrics['correct']} / {metrics['total']}")

    # Determine if passed
    passed = metrics['accuracy'] >= 80.0
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"\n   Target: ≥80% accuracy")
    print(f"   Status: {status}")

    print(f"\n   Per-Class Metrics:")
    for label, class_metrics in metrics['per_class_metrics'].items():
        print(f"\n      {label.capitalize()}:")
        print(f"         Precision: {class_metrics['precision']}%")
        print(f"         Recall: {class_metrics['recall']}%")
        print(f"         F1-Score: {class_metrics['f1_score']}%")
        print(f"         Support: {class_metrics['support']}")

    print(f"\n   Confusion Matrix:")
    print("                 Predicted")
    print("               Pos    Neg    Neu    Mix")
    for label in ["positive", "negative", "neutral"]:
        cm = metrics['confusion_matrix'][label]
        print(f"   {label[:3].capitalize()}  {cm['positive']:4}   {cm['negative']:4}   {cm['neutral']:4}   {cm['mixed']:4}")

    # Step 5: Export report
    print_header("Step 5: Exporting Report")

    llm_stats = llm_client.get_stats()

    report = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration,
        "passed": passed,
        "target_accuracy": 80.0,
        "metrics": metrics,
        "api_stats": llm_stats,
        "detailed_results": detailed_results
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"   ✅ Report saved to: {report_path}")

    # Final summary
    print_header(f"{status} - Validation Complete")
    print(f"   Accuracy: {metrics['accuracy']}%")
    print(f"   Report: {report_path}")
    print(f"   API Cost: ${llm_stats['total_cost']:.2f}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
