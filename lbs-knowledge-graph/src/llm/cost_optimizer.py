"""
Cost Optimizer for LLM Integration

Provides intelligent model selection, caching strategies, and budget optimization
for knowledge graph enrichment operations.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ModelTier(Enum):
    """Model pricing tiers."""
    ULTRA_CHEAP = "ultra_cheap"  # GPT-3.5-turbo, Claude Haiku
    CHEAP = "cheap"               # GPT-4o-mini
    BALANCED = "balanced"         # GPT-4-turbo, Claude Sonnet
    PREMIUM = "premium"           # GPT-4, Claude Opus


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    provider: str
    model: str
    tier: ModelTier
    input_cost_per_1k: float  # USD per 1K input tokens
    output_cost_per_1k: float  # USD per 1K output tokens
    quality_score: float  # 0-1 scale for expected quality
    speed_score: float  # 0-1 scale for response speed


# Model registry with pricing and quality metrics
MODEL_REGISTRY = {
    # OpenAI Models
    "gpt-3.5-turbo": ModelConfig(
        provider="openai",
        model="gpt-3.5-turbo",
        tier=ModelTier.ULTRA_CHEAP,
        input_cost_per_1k=0.0005,
        output_cost_per_1k=0.0015,
        quality_score=0.70,
        speed_score=0.95
    ),
    "gpt-4o-mini": ModelConfig(
        provider="openai",
        model="gpt-4o-mini",
        tier=ModelTier.CHEAP,
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
        quality_score=0.80,
        speed_score=0.90
    ),
    "gpt-4-turbo": ModelConfig(
        provider="openai",
        model="gpt-4-turbo",
        tier=ModelTier.BALANCED,
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.03,
        quality_score=0.95,
        speed_score=0.80
    ),
    "gpt-4": ModelConfig(
        provider="openai",
        model="gpt-4",
        tier=ModelTier.PREMIUM,
        input_cost_per_1k=0.03,
        output_cost_per_1k=0.06,
        quality_score=0.98,
        speed_score=0.70
    ),

    # Anthropic Models
    "claude-3-haiku": ModelConfig(
        provider="anthropic",
        model="claude-3-haiku",
        tier=ModelTier.ULTRA_CHEAP,
        input_cost_per_1k=0.00025,
        output_cost_per_1k=0.00125,
        quality_score=0.75,
        speed_score=0.95
    ),
    "claude-3-sonnet": ModelConfig(
        provider="anthropic",
        model="claude-3-sonnet",
        tier=ModelTier.BALANCED,
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
        quality_score=0.90,
        speed_score=0.85
    ),
    "claude-3-opus": ModelConfig(
        provider="anthropic",
        model="claude-3-opus",
        tier=ModelTier.PREMIUM,
        input_cost_per_1k=0.015,
        output_cost_per_1k=0.075,
        quality_score=0.98,
        speed_score=0.75
    )
}


class CostOptimizer:
    """
    Intelligent cost optimization for LLM operations.

    Features:
    - Model selection based on task complexity
    - Budget-aware processing
    - Result caching recommendations
    - Batch size optimization
    """

    def __init__(
        self,
        budget_limit: float = 50.0,
        quality_threshold: float = 0.70,
        prefer_provider: Optional[str] = None
    ):
        """
        Initialize cost optimizer.

        Args:
            budget_limit: Maximum budget in USD
            quality_threshold: Minimum acceptable quality score
            prefer_provider: Preferred provider ('openai' or 'anthropic')
        """
        self.budget_limit = budget_limit
        self.quality_threshold = quality_threshold
        self.prefer_provider = prefer_provider

        # Filter models by quality threshold
        self.available_models = {
            name: config for name, config in MODEL_REGISTRY.items()
            if config.quality_score >= quality_threshold
        }

        if prefer_provider:
            self.available_models = {
                name: config for name, config in self.available_models.items()
                if config.provider == prefer_provider
            }

    def select_model_for_task(
        self,
        task_type: str,
        estimated_input_tokens: int = 500,
        estimated_output_tokens: int = 200,
        require_reasoning: bool = False
    ) -> Tuple[str, str]:
        """
        Select optimal model for a specific task.

        Args:
            task_type: Type of enrichment task
            estimated_input_tokens: Expected input token count
            estimated_output_tokens: Expected output token count
            require_reasoning: Whether task requires complex reasoning

        Returns:
            Tuple of (provider, model_name)
        """
        # Task complexity mapping
        task_complexity = {
            "sentiment": 0.3,      # Simple classification
            "personas": 0.4,       # Multi-label classification
            "topics": 0.6,         # Extraction with context
            "entities": 0.7,       # Named entity recognition
            "ner": 0.7,           # Named entity recognition
            "journey": 0.5,        # Stage classification
            "similarity": 0.8      # Semantic comparison
        }

        complexity = task_complexity.get(task_type, 0.5)

        # Adjust for reasoning requirement
        if require_reasoning:
            complexity = min(complexity + 0.2, 1.0)

        # Find models that meet quality requirements
        quality_requirement = self.quality_threshold + (complexity * 0.2)

        suitable_models = [
            (name, config) for name, config in self.available_models.items()
            if config.quality_score >= quality_requirement
        ]

        if not suitable_models:
            # Fallback to any model meeting threshold
            suitable_models = list(self.available_models.items())

        # Calculate cost for each model
        model_costs = []
        for name, config in suitable_models:
            input_cost = (estimated_input_tokens / 1000) * config.input_cost_per_1k
            output_cost = (estimated_output_tokens / 1000) * config.output_cost_per_1k
            total_cost = input_cost + output_cost

            # Score: balance cost and quality
            cost_score = 1.0 / (1.0 + total_cost * 1000)  # Normalize
            quality_score = config.quality_score
            speed_score = config.speed_score

            # Combined score (40% cost, 40% quality, 20% speed)
            combined_score = (0.4 * cost_score) + (0.4 * quality_score) + (0.2 * speed_score)

            model_costs.append((name, config, total_cost, combined_score))

        # Sort by combined score (descending)
        model_costs.sort(key=lambda x: x[3], reverse=True)

        # Select best model
        best_model_name, best_config, cost, score = model_costs[0]

        return best_config.provider, best_model_name

    def optimize_batch_size(
        self,
        total_items: int,
        estimated_tokens_per_item: int = 100,
        model_name: str = "gpt-3.5-turbo"
    ) -> int:
        """
        Calculate optimal batch size for processing.

        Args:
            total_items: Total number of items to process
            estimated_tokens_per_item: Estimated tokens per item
            model_name: Model being used

        Returns:
            Optimal batch size
        """
        model_config = MODEL_REGISTRY.get(model_name)
        if not model_config:
            return 50  # Default

        # Calculate tokens per batch at different sizes
        batch_sizes = [10, 25, 50, 100]

        best_batch_size = 50
        best_cost_per_item = float('inf')

        for batch_size in batch_sizes:
            # Overhead tokens for batch formatting (JSON structure, etc.)
            overhead = 100 + (batch_size * 20)  # Base + per-item overhead
            tokens_per_batch = (estimated_tokens_per_item * batch_size) + overhead

            # Cost per batch
            cost_per_batch = (tokens_per_batch / 1000) * model_config.input_cost_per_1k
            cost_per_item = cost_per_batch / batch_size

            if cost_per_item < best_cost_per_item:
                best_cost_per_item = cost_per_item
                best_batch_size = batch_size

        return best_batch_size

    def estimate_total_cost(
        self,
        enrichment_plan: Dict[str, int],
        tokens_per_item: Dict[str, int] = None
    ) -> Dict:
        """
        Estimate total cost for enrichment plan.

        Args:
            enrichment_plan: Dict mapping task types to item counts
            tokens_per_item: Dict mapping task types to token estimates

        Returns:
            Dict with cost breakdown and recommendations
        """
        if tokens_per_item is None:
            # Default token estimates
            tokens_per_item = {
                "sentiment": 150,
                "topics": 300,
                "personas": 250,
                "entities": 400,
                "ner": 400,
                "journey": 200,
                "similarity": 350
            }

        cost_breakdown = {}
        total_cost = 0.0
        recommendations = []

        for task_type, item_count in enrichment_plan.items():
            # Select optimal model
            provider, model_name = self.select_model_for_task(
                task_type,
                estimated_input_tokens=tokens_per_item.get(task_type, 200)
            )

            model_config = MODEL_REGISTRY[model_name]

            # Optimize batch size
            batch_size = self.optimize_batch_size(
                item_count,
                tokens_per_item.get(task_type, 200),
                model_name
            )

            # Calculate cost
            tokens_per_request = tokens_per_item.get(task_type, 200)
            num_batches = (item_count + batch_size - 1) // batch_size

            # Account for batch overhead
            overhead_per_batch = 100 + (batch_size * 20)
            total_input_tokens = (tokens_per_request * item_count) + (overhead_per_batch * num_batches)
            total_output_tokens = (100 * item_count)  # Estimated output

            input_cost = (total_input_tokens / 1000) * model_config.input_cost_per_1k
            output_cost = (total_output_tokens / 1000) * model_config.output_cost_per_1k
            task_total_cost = input_cost + output_cost

            total_cost += task_total_cost

            cost_breakdown[task_type] = {
                "model": f"{provider}/{model_name}",
                "item_count": item_count,
                "batch_size": batch_size,
                "num_batches": num_batches,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "cost": task_total_cost,
                "cost_per_item": task_total_cost / item_count
            }

            # Generate recommendations
            if task_total_cost > self.budget_limit * 0.3:
                recommendations.append(
                    f"⚠️ {task_type} accounts for {(task_total_cost/self.budget_limit)*100:.1f}% "
                    f"of budget. Consider using a cheaper model or reducing scope."
                )

        # Budget check
        within_budget = total_cost <= self.budget_limit
        budget_utilization = (total_cost / self.budget_limit) * 100

        if not within_budget:
            recommendations.insert(0,
                f"🚨 Total cost ${total_cost:.2f} exceeds budget ${self.budget_limit:.2f}!"
            )
        elif budget_utilization > 80:
            recommendations.insert(0,
                f"⚠️ Using {budget_utilization:.1f}% of budget. Consider cost optimization."
            )

        return {
            "total_cost": total_cost,
            "budget_limit": self.budget_limit,
            "within_budget": within_budget,
            "budget_utilization_percent": budget_utilization,
            "breakdown": cost_breakdown,
            "recommendations": recommendations
        }

    def get_caching_strategy(
        self,
        task_type: str,
        item_count: int,
        similarity_threshold: float = 0.9
    ) -> Dict:
        """
        Recommend caching strategy for task.

        Args:
            task_type: Type of enrichment task
            item_count: Number of items to process
            similarity_threshold: Threshold for considering items similar

        Returns:
            Dict with caching recommendations
        """
        # Task-specific caching benefits
        cache_effectiveness = {
            "sentiment": 0.60,  # Moderate - similar content patterns
            "topics": 0.40,     # Lower - more variation
            "personas": 0.70,   # Higher - limited persona types
            "entities": 0.30,   # Lower - unique entities
            "ner": 0.30,       # Lower - unique entities
            "journey": 0.65,    # Higher - limited journey stages
            "similarity": 0.20  # Lower - comparing unique pairs
        }

        effectiveness = cache_effectiveness.get(task_type, 0.40)

        # Estimate cache hits
        estimated_cache_hits = int(item_count * effectiveness)
        estimated_api_calls = item_count - estimated_cache_hits

        # Estimate savings
        provider, model_name = self.select_model_for_task(task_type)
        model_config = MODEL_REGISTRY[model_name]
        cost_per_item = 0.001  # Rough estimate

        potential_savings = estimated_cache_hits * cost_per_item

        return {
            "task_type": task_type,
            "cache_effectiveness": effectiveness,
            "estimated_cache_hits": estimated_cache_hits,
            "estimated_api_calls": estimated_api_calls,
            "cache_hit_rate": effectiveness * 100,
            "potential_savings": potential_savings,
            "recommendation": "Enable caching" if effectiveness > 0.5 else "Optional caching"
        }

    def optimize_for_budget(
        self,
        enrichment_plan: Dict[str, int],
        target_budget: Optional[float] = None
    ) -> Dict:
        """
        Optimize enrichment plan to fit within budget.

        Args:
            enrichment_plan: Original enrichment plan
            target_budget: Target budget (uses instance budget if not provided)

        Returns:
            Optimized plan with cost breakdown
        """
        if target_budget is None:
            target_budget = self.budget_limit

        # Get initial cost estimate
        initial_estimate = self.estimate_total_cost(enrichment_plan)

        if initial_estimate["within_budget"]:
            return {
                "optimized": False,
                "original_cost": initial_estimate["total_cost"],
                "optimized_cost": initial_estimate["total_cost"],
                "savings": 0.0,
                "plan": enrichment_plan,
                "message": "Original plan is within budget"
            }

        # Try optimization strategies
        optimized_plan = enrichment_plan.copy()

        # Strategy 1: Reduce scope for expensive tasks
        for task_type in sorted(
            initial_estimate["breakdown"].keys(),
            key=lambda t: initial_estimate["breakdown"][t]["cost"],
            reverse=True
        ):
            if initial_estimate["total_cost"] <= target_budget:
                break

            # Reduce by 20%
            reduction_factor = 0.8
            optimized_plan[task_type] = int(enrichment_plan[task_type] * reduction_factor)
            initial_estimate = self.estimate_total_cost(optimized_plan)

        return {
            "optimized": True,
            "original_cost": self.estimate_total_cost(enrichment_plan)["total_cost"],
            "optimized_cost": initial_estimate["total_cost"],
            "savings": self.estimate_total_cost(enrichment_plan)["total_cost"] - initial_estimate["total_cost"],
            "plan": optimized_plan,
            "within_budget": initial_estimate["within_budget"],
            "message": "Plan optimized to reduce costs"
        }

    def print_cost_report(self, enrichment_plan: Dict[str, int]):
        """
        Print formatted cost report for enrichment plan.

        Args:
            enrichment_plan: Dict mapping task types to item counts
        """
        estimate = self.estimate_total_cost(enrichment_plan)

        print("\n" + "="*70)
        print("COST OPTIMIZATION REPORT")
        print("="*70)

        print(f"\n💰 Total Estimated Cost: ${estimate['total_cost']:.2f}")
        print(f"📊 Budget Limit: ${estimate['budget_limit']:.2f}")
        print(f"✅ Within Budget: {'Yes' if estimate['within_budget'] else 'No'}")
        print(f"📈 Budget Utilization: {estimate['budget_utilization_percent']:.1f}%")

        print("\n📋 Cost Breakdown by Task:")
        print("-" * 70)

        for task_type, details in estimate["breakdown"].items():
            print(f"\n{task_type.upper()}:")
            print(f"  Model: {details['model']}")
            print(f"  Items: {details['item_count']:,}")
            print(f"  Batch size: {details['batch_size']}")
            print(f"  Batches: {details['num_batches']}")
            print(f"  Tokens: {details['total_input_tokens']:,} input + {details['total_output_tokens']:,} output")
            print(f"  Cost: ${details['cost']:.2f} (${details['cost_per_item']:.4f} per item)")

        if estimate["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in estimate["recommendations"]:
                print(f"  {rec}")

        print("\n" + "="*70 + "\n")
