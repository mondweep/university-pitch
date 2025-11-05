"""
Domain entity models for the LBS Knowledge Graph.

This module defines Pydantic models for all core domain entities:
- Page: Webpage entity with metadata and classification
- Section: Page section/component entity
- ContentItem: Atomic content block entity
- SentimentScore: Sentiment analysis result
- Entity: Named entity extraction result

All models use Pydantic for validation and serialization.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl

from .enums import PageType, SectionType, ContentType, EntityType


class SentimentScore(BaseModel):
    """Sentiment analysis score for content"""

    polarity: float = Field(..., ge=-1.0, le=1.0, description="Sentiment polarity from -1 (negative) to +1 (positive)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    label: str = Field(..., description="Sentiment label: positive, neutral, or negative")
    magnitude: Optional[float] = Field(None, ge=0.0, le=1.0, description="Strength of sentiment")

    class Config:
        frozen = True


class Entity(BaseModel):
    """Named entity extracted from content"""

    text: str = Field(..., description="Entity text")
    type: EntityType = Field(..., description="Entity type classification")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")

    class Config:
        frozen = True


class Page(BaseModel):
    """
    Webpage entity representing a page from london.edu.

    Contains core metadata, classification, content tracking, and analytics.
    """

    # Core fields
    id: str = Field(..., description="UUID v4 identifier")
    url: str = Field(..., description="Canonical URL (unique)")
    title: str = Field(..., description="Page title")
    description: Optional[str] = Field(None, description="Meta description")

    # Classification
    type: PageType = Field(..., description="Page classification")
    category: Optional[str] = Field(None, description="Primary category")
    language: str = Field(default="en", description="ISO 639-1 language code")

    # Content tracking
    hash: str = Field(..., description="SHA-256 hash of raw HTML")
    content_hash: str = Field(..., description="SHA-256 hash of extracted content")
    version: int = Field(default=1, description="Version number (incremented on change)")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="First crawl timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    fetched_at: datetime = Field(default_factory=datetime.now, description="Last fetch timestamp")
    published_at: Optional[datetime] = Field(None, description="Original publish date")

    # SEO & Social
    keywords: List[str] = Field(default_factory=list, description="Meta keywords")
    og_image: Optional[str] = Field(None, description="Open Graph image URL")
    og_description: Optional[str] = Field(None, description="Open Graph description")

    # Analytics
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Calculated importance score")
    depth: int = Field(default=0, ge=0, description="Distance from homepage")
    inbound_links: int = Field(default=0, ge=0, description="Number of pages linking to this")
    outbound_links: int = Field(default=0, ge=0, description="Number of links from this page")

    # Custom metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        validate_assignment = True


class Section(BaseModel):
    """
    Section/component entity within a page.

    Represents a logical section of content with type classification and ordering.
    """

    # Core fields
    id: str = Field(..., description="UUID v4 identifier")
    page_id: str = Field(..., description="Parent page ID")

    # Classification
    type: SectionType = Field(..., description="Section type classification")
    component: Optional[str] = Field(None, description="Component identifier/class name")

    # Content
    heading: Optional[str] = Field(None, description="Section heading (text hash)")
    subheading: Optional[str] = Field(None, description="Section subheading (text hash)")
    order: int = Field(..., ge=0, description="Display order on page (0-indexed)")

    # Metadata
    css_selector: Optional[str] = Field(None, description="Original CSS selector")
    attributes: Dict[str, str] = Field(default_factory=dict, description="HTML attributes")

    # Custom metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        validate_assignment = True


class ContentItem(BaseModel):
    """
    Atomic content item entity.

    Represents a single piece of content (text, image, etc.) with deduplication
    via content hashing and semantic enrichment.
    """

    # Core fields
    id: str = Field(..., description="UUID v4 identifier")
    hash: str = Field(..., description="SHA-256 hash of content")

    # Content
    text: str = Field(..., description="Text content")
    type: ContentType = Field(..., description="Content type classification")

    # Semantics (LLM-generated)
    sentiment: Optional[SentimentScore] = Field(None, description="Sentiment analysis result")
    topics: List[str] = Field(default_factory=list, description="Topic IDs")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    entities: List[Entity] = Field(default_factory=list, description="Named entities")

    # Audience
    audiences: List[str] = Field(default_factory=list, description="Persona IDs")
    reading_level: Optional[int] = Field(None, ge=1, le=12, description="Reading level (1-12)")

    # Usage tracking
    page_ids: List[str] = Field(default_factory=list, description="Pages using this content")
    section_ids: List[str] = Field(default_factory=list, description="Sections using this content")
    usage_count: int = Field(default=0, ge=0, description="Number of times used")

    # Metadata
    language: str = Field(default="en", description="ISO 639-1 language code")
    word_count: int = Field(default=0, ge=0, description="Word count")
    char_count: int = Field(default=0, ge=0, description="Character count")

    # Custom metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        validate_assignment = True


class ContainsRelationship(BaseModel):
    """Hierarchical containment relationship (Page->Section, Section->ContentItem)"""

    source_id: str = Field(..., description="Source entity ID")
    source_type: str = Field(..., description="Source entity type")
    target_id: str = Field(..., description="Target entity ID")
    target_type: str = Field(..., description="Target entity type")
    order: int = Field(..., ge=0, description="Display order")
    required: bool = Field(default=False, description="Is this item required?")
    conditional: Optional[str] = Field(None, description="Condition for display")


class LinksToRelationship(BaseModel):
    """Hyperlink relationship between pages"""

    source_id: str = Field(..., description="Source page ID")
    target_id: str = Field(..., description="Target page ID")
    text: str = Field(..., description="Link anchor text")
    type: str = Field(..., description="Link type")
    position: int = Field(..., ge=0, description="Position on source page")
    context: Optional[str] = Field(None, description="Surrounding context")


class GraphReadyEntities(BaseModel):
    """Container for all extracted entities and relationships"""

    pages: List[Page] = Field(default_factory=list)
    sections: List[Section] = Field(default_factory=list)
    content_items: List[ContentItem] = Field(default_factory=list)
    relationships: List[Any] = Field(default_factory=list)  # Union of relationship types
