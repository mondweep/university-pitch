"""
Enrichment Package for Knowledge Graph

Provides multiple enrichment capabilities:
1. Named Entity Recognition (NER) - Extract and link entities
2. Semantic Similarity - Find related pages through embeddings

NER Components:
    - EntityNodeBuilder: Build entity nodes
    - MentionsBuilder: Create MENTIONS edges
    - NEREnricher: NER enrichment pipeline

Similarity Components:
    - EmbeddingGenerator: Generate embeddings for pages
    - SimilarityCalculator: Calculate semantic similarity
    - RelatedToBuilder: Create RELATED_TO edges
    - SimilarityEnricher: Similarity enrichment pipeline

Example Usage:
    # NER enrichment
    from enrichment import NEREnricher
    enricher = NEREnricher()
    enriched_graph = enricher.enrich_graph(graph)

    # Similarity enrichment
    from enrichment import SimilarityEnricher
    enricher = SimilarityEnricher()
    enriched_graph = enricher.enrich_graph(graph)
"""

# Similarity enrichment (always available)
from .embedding_generator import EmbeddingGenerator, EmbeddingConfig
from .similarity_calculator import SimilarityCalculator, SimilarityConfig
from .related_to_builder import RelatedToBuilder, EdgeConfig
from .similarity_enricher import SimilarityEnricher

__all__ = [
    # Similarity
    'EmbeddingGenerator',
    'EmbeddingConfig',
    'SimilarityCalculator',
    'SimilarityConfig',
    'RelatedToBuilder',
    'EdgeConfig',
    'SimilarityEnricher',
]

# NER enrichment (optional, import if available)
try:
    from .entity_node_builder import EntityNodeBuilder
    from .mentions_builder import MentionsBuilder
    from .ner_enricher import NEREnricher, run_ner_enrichment

    __all__.extend([
        'EntityNodeBuilder',
        'MentionsBuilder',
        'NEREnricher',
        'run_ner_enrichment',
    ])
except ImportError:
    pass  # NER components not available

__version__ = '1.0.0'
