"""
Data models for relationship edges in the knowledge graph.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class LinkType(str, Enum):
    """Types of page linking relationships."""

    NAVIGATION = "navigation"
    REFERENCE = "reference"
    CITATION = "citation"
    RELATED = "related"
    INTERNAL = "internal"
    EXTERNAL = "external"


class EdgeType(str, Enum):
    """Types of edges in the knowledge graph."""

    CONTAINS = "CONTAINS"
    LINKS_TO = "LINKS_TO"
    HAS_TOPIC = "HAS_TOPIC"
    BELONGS_TO = "BELONGS_TO"
    TARGETS = "TARGETS"
    CHILD_OF = "CHILD_OF"


class Edge(BaseModel):
    """
    Represents an edge in the knowledge graph.

    Edges connect two nodes with typed relationships and properties.
    """

    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    relationship_type: EdgeType = Field(..., description="Type of relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    @field_validator("source_id", "target_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        """Validate that IDs are not empty."""
        if not v or not v.strip():
            raise ValueError("Node IDs cannot be empty")
        return v.strip()

    def __hash__(self) -> int:
        """Make edge hashable for deduplication."""
        return hash((self.source_id, self.target_id, self.relationship_type))

    def __eq__(self, other: object) -> bool:
        """Check equality based on source, target, and type."""
        if not isinstance(other, Edge):
            return False
        return (
            self.source_id == other.source_id
            and self.target_id == other.target_id
            and self.relationship_type == other.relationship_type
        )


class ContainsProperties(BaseModel):
    """Properties for CONTAINS relationships."""

    order: int = Field(..., ge=0, description="Display order (0-indexed)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    required: bool = Field(default=False, description="Is this item required?")
    conditional: Optional[str] = Field(None, description="Condition for display")


class LinksToProperties(BaseModel):
    """Properties for LINKS_TO relationships."""

    link_type: LinkType = Field(..., description="Type of link")
    anchor_text: str = Field(..., description="Link anchor text")
    link_strength: float = Field(default=0.5, ge=0.0, le=1.0, description="Link strength score")
    position: Optional[str] = Field(None, description="Position on page (header, content, footer)")
    context: Optional[str] = Field(None, description="Surrounding context")


class ValidationIssue(BaseModel):
    """Represents a validation issue in the graph."""

    severity: str = Field(..., description="Issue severity: error, warning, info")
    issue_type: str = Field(..., description="Type of issue")
    message: str = Field(..., description="Issue description")
    node_id: Optional[str] = Field(None, description="Affected node ID")
    edge: Optional[Edge] = Field(None, description="Affected edge")


class ValidationReport(BaseModel):
    """Report of graph validation results."""

    is_valid: bool = Field(..., description="Overall validation status")
    total_nodes: int = Field(default=0, ge=0, description="Total nodes checked")
    total_edges: int = Field(default=0, ge=0, description="Total edges checked")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of issues found")
    errors: int = Field(default=0, ge=0, description="Number of errors")
    warnings: int = Field(default=0, ge=0, description="Number of warnings")
    info: int = Field(default=0, ge=0, description="Number of info messages")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Validation timestamp")

    def add_issue(
        self,
        severity: str,
        issue_type: str,
        message: str,
        node_id: Optional[str] = None,
        edge: Optional[Edge] = None,
    ) -> None:
        """Add a validation issue to the report."""
        issue = ValidationIssue(
            severity=severity,
            issue_type=issue_type,
            message=message,
            node_id=node_id,
            edge=edge,
        )
        self.issues.append(issue)

        # Update counters
        if severity == "error":
            self.errors += 1
            self.is_valid = False
        elif severity == "warning":
            self.warnings += 1
        elif severity == "info":
            self.info += 1


class GraphStatistics(BaseModel):
    """Statistics about the knowledge graph."""

    total_nodes: int = Field(default=0, ge=0)
    total_edges: int = Field(default=0, ge=0)
    nodes_by_type: Dict[str, int] = Field(default_factory=dict)
    edges_by_type: Dict[str, int] = Field(default_factory=dict)
    orphaned_nodes: int = Field(default=0, ge=0)
    avg_edges_per_node: float = Field(default=0.0, ge=0.0)
    max_depth: int = Field(default=0, ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
