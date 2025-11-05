"""
Graph Schema Definitions for LBS Knowledge Graph

Defines Pydantic schemas for nodes and edges in the knowledge graph.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PageNode(BaseModel):
    """Page node schema"""
    id: str = Field(..., description="Unique page ID")
    url: str = Field(..., description="Page URL")
    title: str = Field(..., description="Page title")
    type: str = Field(default="other", description="Page type")
    importance: float = Field(default=0.5, ge=0, le=1, description="Page importance")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Update timestamp")
    description: Optional[str] = Field(None, description="Page description")
    keywords: Optional[str] = Field(None, description="Page keywords")


class SectionNode(BaseModel):
    """Section node schema"""
    id: str = Field(..., description="Unique section ID")
    section_type: str = Field(..., description="Section type")
    heading: Optional[str] = Field(None, description="Section heading")
    order: int = Field(..., description="Section order within page")


class ContentItemNode(BaseModel):
    """Content item node schema"""
    id: str = Field(..., description="Unique content ID")
    hash: str = Field(..., description="Content hash")
    text: str = Field(..., description="Content text")
    content_type: str = Field(..., description="Content type")
    word_count: int = Field(default=0, description="Word count")
    order: int = Field(default=0, description="Order within section")


class TopicNode(BaseModel):
    """Topic node schema"""
    id: str = Field(..., description="Unique topic ID")
    name: str = Field(..., description="Topic name")
    slug: str = Field(..., description="URL-friendly slug")
    category: str = Field(..., description="Topic category")
    importance: float = Field(default=0.5, ge=0, le=1, description="Topic importance")


class CategoryNode(BaseModel):
    """Category node schema"""
    id: str = Field(..., description="Unique category ID")
    name: str = Field(..., description="Category name")
    parent_id: Optional[str] = Field(None, description="Parent category ID")
    level: int = Field(default=0, description="Hierarchy level")


class PersonaNode(BaseModel):
    """Persona (audience) node schema"""
    id: str = Field(..., description="Unique persona ID")
    name: str = Field(..., description="Persona name")
    description: str = Field(..., description="Persona description")
    characteristics: List[str] = Field(default_factory=list, description="Key characteristics")


class ContainsEdge(BaseModel):
    """CONTAINS relationship schema"""
    order: int = Field(default=0, description="Order of contained element")


class LinksToEdge(BaseModel):
    """LINKS_TO relationship schema"""
    text: str = Field(default="", description="Link text")
    link_type: str = Field(default="internal", description="Link type (internal/external)")


class HasTopicEdge(BaseModel):
    """HAS_TOPIC relationship schema"""
    confidence: float = Field(..., ge=0, le=1, description="Topic confidence score")
    source: str = Field(default="llm", description="Source of topic assignment")


class BelongsToEdge(BaseModel):
    """BELONGS_TO relationship schema"""
    relevance: float = Field(default=0.5, ge=0, le=1, description="Category relevance")


class TargetsEdge(BaseModel):
    """TARGETS relationship schema"""
    relevance: float = Field(default=0.5, ge=0, le=1, description="Persona targeting relevance")


class LBSGraphSchema:
    """
    Complete graph schema definition
    """

    NODE_TYPES = {
        'Page': PageNode,
        'Section': SectionNode,
        'ContentItem': ContentItemNode,
        'Topic': TopicNode,
        'Category': CategoryNode,
        'Persona': PersonaNode
    }

    EDGE_TYPES = {
        'CONTAINS': ContainsEdge,
        'LINKS_TO': LinksToEdge,
        'HAS_TOPIC': HasTopicEdge,
        'BELONGS_TO': BelongsToEdge,
        'TARGETS': TargetsEdge
    }

    @classmethod
    def get_node_schema(cls, node_type: str) -> Optional[type[BaseModel]]:
        """Get schema for a node type"""
        return cls.NODE_TYPES.get(node_type)

    @classmethod
    def get_edge_schema(cls, edge_type: str) -> Optional[type[BaseModel]]:
        """Get schema for an edge type"""
        return cls.EDGE_TYPES.get(edge_type)

    @classmethod
    def validate_node(cls, node_type: str, data: dict) -> BaseModel:
        """Validate and return a node instance"""
        schema = cls.get_node_schema(node_type)
        if not schema:
            raise ValueError(f"Unknown node type: {node_type}")
        return schema(**data)

    @classmethod
    def validate_edge(cls, edge_type: str, data: dict) -> BaseModel:
        """Validate and return an edge instance"""
        schema = cls.get_edge_schema(edge_type)
        if not schema:
            raise ValueError(f"Unknown edge type: {edge_type}")
        return schema(**data)
