"""
Entity Models for Named Entity Recognition
Defines entity types, structures, and relationship models.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class EntityType(Enum):
    """Named entity types for LBS content."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    PROGRAMME = "PROGRAMME"
    EVENT = "EVENT"
    DEGREE = "DEGREE"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_string(cls, type_str: str) -> 'EntityType':
        """Convert string to EntityType."""
        try:
            return cls[type_str.upper()]
        except KeyError:
            return cls.UNKNOWN


class EntityRelationType(Enum):
    """Relationship types between entities and content."""
    MENTIONS = "MENTIONS"
    AFFILIATED_WITH = "AFFILIATED_WITH"
    LOCATED_IN = "LOCATED_IN"
    TEACHES = "TEACHES"
    STUDIES = "STUDIES"
    LEADS = "LEADS"
    PARTICIPATES_IN = "PARTICIPATES_IN"


@dataclass
class Entity:
    """Named entity with metadata."""

    name: str
    type: EntityType
    confidence: float  # 0-1
    context: str = ""  # Surrounding text
    normalized_name: Optional[str] = None  # Canonical name
    aliases: List[str] = field(default_factory=list)  # Alternative names
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Graph properties
    id: Optional[str] = None  # UUID assigned by graph
    prominence: float = 0.0  # Frequency/importance score

    # Provenance
    source_ids: List[str] = field(default_factory=list)  # Page/Section IDs
    extracted_at: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization validation and normalization."""
        if isinstance(self.type, str):
            self.type = EntityType.from_string(self.type)

        if self.normalized_name is None:
            self.normalized_name = self._normalize_name(self.name)

        if self.extracted_at is None:
            self.extracted_at = datetime.utcnow()

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize entity name for matching.

        Examples:
            "Prof. John Smith" -> "john smith"
            "The University of London" -> "university of london"
        """
        # Remove common titles and prefixes
        prefixes = ["prof.", "dr.", "professor", "the", "mr.", "ms.", "mrs."]
        normalized = name.lower().strip()

        for prefix in prefixes:
            if normalized.startswith(prefix + " "):
                normalized = normalized[len(prefix) + 1:]

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def matches(self, other: 'Entity', threshold: float = 0.9) -> bool:
        """
        Check if this entity matches another entity.

        Args:
            other: Entity to compare
            threshold: Similarity threshold (0-1)

        Returns:
            True if entities match
        """
        # Same type required
        if self.type != other.type:
            return False

        # Exact normalized name match
        if self.normalized_name == other.normalized_name:
            return True

        # Check aliases
        if other.normalized_name in [a.lower() for a in self.aliases]:
            return True
        if self.normalized_name in [a.lower() for a in other.aliases]:
            return True

        # Fuzzy string similarity (simplified)
        # In production, use proper string similarity (e.g., difflib, fuzzywuzzy)
        s1 = set(self.normalized_name.split())
        s2 = set(other.normalized_name.split())

        if not s1 or not s2:
            return False

        intersection = len(s1 & s2)
        union = len(s1 | s2)
        jaccard = intersection / union if union > 0 else 0.0

        return jaccard >= threshold

    def merge(self, other: 'Entity') -> 'Entity':
        """
        Merge another entity into this one.

        Args:
            other: Entity to merge

        Returns:
            Merged entity
        """
        # Take higher confidence
        if other.confidence > self.confidence:
            self.confidence = other.confidence

        # Merge aliases
        if other.name not in self.aliases and other.name != self.name:
            self.aliases.append(other.name)
        self.aliases.extend([a for a in other.aliases if a not in self.aliases])

        # Merge source IDs
        self.source_ids.extend([sid for sid in other.source_ids if sid not in self.source_ids])

        # Combine contexts (keep shorter one)
        if len(other.context) < len(self.context):
            self.context = other.context

        # Merge metadata
        self.metadata.update(other.metadata)

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "confidence": self.confidence,
            "context": self.context,
            "normalized_name": self.normalized_name,
            "aliases": self.aliases,
            "prominence": self.prominence,
            "source_ids": self.source_ids,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Create entity from dictionary."""
        extracted_at = None
        if data.get("extracted_at"):
            extracted_at = datetime.fromisoformat(data["extracted_at"])

        return cls(
            name=data["name"],
            type=EntityType.from_string(data["type"]),
            confidence=data["confidence"],
            context=data.get("context", ""),
            normalized_name=data.get("normalized_name"),
            aliases=data.get("aliases", []),
            metadata=data.get("metadata", {}),
            id=data.get("id"),
            prominence=data.get("prominence", 0.0),
            source_ids=data.get("source_ids", []),
            extracted_at=extracted_at
        )


@dataclass
class EntityMention:
    """Represents a mention of an entity in content."""

    entity_id: str  # Entity node ID
    source_id: str  # Page or Section ID
    source_type: str  # "Page" or "Section"
    context: str  # Surrounding text
    position: int = 0  # Position in text
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "context": self.context,
            "position": self.position,
            "confidence": self.confidence
        }


class EntityStatistics:
    """Statistics about extracted entities."""

    def __init__(self):
        self.total_entities = 0
        self.unique_entities = 0
        self.entities_by_type: Dict[EntityType, int] = {}
        self.mentions_count = 0
        self.avg_confidence = 0.0
        self.top_entities: List[tuple] = []  # (name, count) tuples

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_entities": self.total_entities,
            "unique_entities": self.unique_entities,
            "entities_by_type": {
                k.value: v for k, v in self.entities_by_type.items()
            },
            "mentions_count": self.mentions_count,
            "avg_confidence": self.avg_confidence,
            "top_entities": self.top_entities
        }
