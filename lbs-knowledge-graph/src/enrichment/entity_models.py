"""
Entity Data Models

Defines entity types and structures for Named Entity Recognition.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


class EntityType(str, Enum):
    """Entity type classification"""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    EVENT = "EVENT"


@dataclass
class Entity:
    """
    Represents a named entity extracted from content.

    Attributes:
        id: Unique entity identifier (UUID)
        name: Entity name as it appears in text
        entity_type: Classification (PERSON, ORGANIZATION, LOCATION, EVENT)
        canonical_name: Normalized form of the name
        aliases: Alternative names/mentions
        metadata: Additional entity information (role, title, affiliation, etc.)
        mention_count: Number of times entity appears
        first_mentioned: Timestamp of first mention
        prominence: Importance score based on frequency and context (0.0-1.0)
        confidence: Extraction confidence score (0.0-1.0)
    """
    id: str
    name: str
    entity_type: EntityType
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    mention_count: int = 1
    first_mentioned: Optional[datetime] = None
    prominence: float = 0.0
    confidence: float = 1.0

    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "canonical_name": self.canonical_name,
            "aliases": self.aliases,
            "metadata": self.metadata,
            "mention_count": self.mention_count,
            "first_mentioned": self.first_mentioned.isoformat() if self.first_mentioned else None,
            "prominence": round(self.prominence, 3),
            "confidence": round(self.confidence, 3)
        }


@dataclass
class EntityMention:
    """
    Represents a single mention of an entity in content.

    Attributes:
        entity_id: ID of the entity
        content_id: ID of the content item containing the mention
        entity_text: Text as it appears in the content
        context: Surrounding text for context
        prominence: Mention prominence (high/medium/low)
        confidence: Extraction confidence
        position: Position in content (for prominence calculation)
        extracted_by: Model used for extraction
    """
    entity_id: str
    content_id: str
    entity_text: str
    context: str
    prominence: str = "medium"  # high, medium, low
    confidence: float = 1.0
    position: int = 0  # Character position in content
    extracted_by: str = "gpt-4-turbo"

    def to_dict(self) -> dict:
        """Convert mention to dictionary"""
        return {
            "entity_id": self.entity_id,
            "content_id": self.content_id,
            "entity_text": self.entity_text,
            "context": self.context,
            "prominence": self.prominence,
            "confidence": round(self.confidence, 3),
            "position": self.position,
            "extracted_by": self.extracted_by
        }


@dataclass
class EntityRelationship:
    """
    Represents a relationship between two entities.

    Attributes:
        from_entity_id: Source entity ID
        to_entity_id: Target entity ID
        relationship_type: Type of relationship (WORKS_WITH, AFFILIATED_WITH, etc.)
        confidence: Relationship confidence score
        evidence: Text evidence for the relationship
        metadata: Additional relationship data
    """
    from_entity_id: str
    to_entity_id: str
    relationship_type: str
    confidence: float = 1.0
    evidence: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert relationship to dictionary"""
        return {
            "from_entity_id": self.from_entity_id,
            "to_entity_id": self.to_entity_id,
            "relationship_type": self.relationship_type,
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "metadata": self.metadata
        }


@dataclass
class NERExtractionResult:
    """
    Result of NER extraction on content.

    Attributes:
        content_id: ID of content analyzed
        entities: List of extracted entities
        mentions: List of entity mentions
        relationships: List of entity relationships
        extraction_time: Time taken for extraction (seconds)
        cost: API cost for extraction
        model_used: Model used for extraction
    """
    content_id: str
    entities: List[Entity] = field(default_factory=list)
    mentions: List[EntityMention] = field(default_factory=list)
    relationships: List[EntityRelationship] = field(default_factory=list)
    extraction_time: float = 0.0
    cost: float = 0.0
    model_used: str = "gpt-4-turbo"

    def to_dict(self) -> dict:
        """Convert result to dictionary"""
        return {
            "content_id": self.content_id,
            "entities": [e.to_dict() for e in self.entities],
            "mentions": [m.to_dict() for m in self.mentions],
            "relationships": [r.to_dict() for r in self.relationships],
            "extraction_time": round(self.extraction_time, 3),
            "cost": round(self.cost, 4),
            "model_used": self.model_used
        }


@dataclass  
class EntityStatistics:
    """
    Statistics for entity extraction.
    Stub class for test compatibility - to be implemented.
    """
    total_entities: int = 0
    entities_by_type: Dict[str, int] = field(default_factory=dict)
    unique_entities: int = 0
    avg_prominence: float = 0.0
