"""
Extractors package for LBS Knowledge Graph.

Provides domain entity extractors for Phase 2 implementation:
- PageExtractor: Extracts Page entities with multi-signal classification
- SectionExtractor: Extracts Section entities with DOM-based detection
- ContentItemExtractor: Extracts ContentItem entities with hash linking

Usage:
    from extractors import PageExtractor, SectionExtractor, ContentItemExtractor

    page_extractor = PageExtractor()
    section_extractor = SectionExtractor()
    content_extractor = ContentItemExtractor()

    # Extract entities from parsed data
    page = page_extractor.extract_page_entity(parsed_data)
    sections_data = section_extractor.detect_sections(parsed_data['dom'])
    sections = [section_extractor.extract_section_entity(s, page.id) for s in sections_data]
"""

from .page_extractor import PageExtractor
from .section_extractor import SectionExtractor
from .content_item_extractor import ContentItemExtractor

__all__ = [
    'PageExtractor',
    'SectionExtractor',
    'ContentItemExtractor',
]
