"""
Knowledge Graph Enrichment Package

This package provides sentiment analysis, persona targeting, and other enrichment features
for the LBS Knowledge Graph.

Modules:
- models: Pydantic models for sentiment scores
- llm_client: OpenAI API client for sentiment analysis
- sentiment_analyzer: Core sentiment analysis logic
- sentiment_enricher: Graph enrichment with sentiment
- persona_models: Persona definitions and data models
- persona_classifier: LLM-based persona classification
- targets_builder: Build TARGETS relationships in graph
- persona_enricher: Orchestrate persona enrichment
"""

from .models import (
    SentimentPolarity,
    SentimentScore,
    ContentItemWithSentiment
)
from .llm_client import LLMClient
from .sentiment_analyzer import SentimentAnalyzer
from .sentiment_enricher import SentimentEnricher
from .persona_models import (
    Persona,
    PersonaTarget,
    PersonaType,
    JourneyStage,
    get_all_personas,
    get_persona_by_id,
    get_persona_by_name
)
# Lazy imports to avoid memgraph dependency for sentiment-only usage
# from .persona_classifier import PersonaClassifier
# from .targets_builder import TargetsBuilder
# from .persona_enricher import PersonaEnricher

__all__ = [
    "SentimentPolarity",
    "SentimentScore",
    "ContentItemWithSentiment",
    "LLMClient",
    "SentimentAnalyzer",
    "SentimentEnricher",
    "Persona",
    "PersonaTarget",
    "PersonaType",
    "JourneyStage",
    "get_all_personas",
    "get_persona_by_id",
    "get_persona_by_name",
    # Lazy imports - import directly when needed:
    # "PersonaClassifier",
    # "TargetsBuilder",
    # "PersonaEnricher"
]

__version__ = "1.1.0"
