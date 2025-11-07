"""
Topic Models for Knowledge Graph Enrichment

Defines data models for topics and topic-related entities based on taxonomy.
"""

from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum


class TopicCategory(str, Enum):
    """Topic categories from LBS taxonomy"""
    ACADEMIC = "academic"
    RESEARCH = "research"
    STUDENT_LIFE = "student_life"
    BUSINESS = "business"
    ALUMNI = "alumni"
    EVENTS = "events"
    ADMISSIONS = "admissions"
    CAREER = "career"
    FACULTY = "faculty"
    GENERAL = "general"


class BusinessDiscipline(str, Enum):
    """Business academic disciplines"""
    ACCOUNTING_FINANCE = "accounting_finance"
    ECONOMICS = "economics"
    MARKETING = "marketing"
    STRATEGY = "strategy"
    OPERATIONS_ANALYTICS = "operations_analytics"
    ORGANIZATIONAL_BEHAVIOUR = "organizational_behaviour"
    ENTREPRENEURSHIP = "entrepreneurship"
    OTHER = "other"


class CrossCuttingTheme(str, Enum):
    """Cross-cutting business themes"""
    SUSTAINABILITY_ESG = "sustainability_esg"
    TECHNOLOGY_DIGITAL = "technology_digital"
    GLOBALIZATION = "globalization"
    DIVERSITY_INCLUSION = "diversity_inclusion"
    FUTURE_OF_WORK = "future_of_work"
    INNOVATION = "innovation"
    LEADERSHIP = "leadership"


class Topic(BaseModel):
    """
    Topic entity representing a semantic concept or theme.

    Extracted from page/section content using LLM analysis.
    """
    id: str = Field(..., description="Unique topic ID (UUID)")
    name: str = Field(..., description="Topic name (normalized)")
    description: Optional[str] = Field(None, description="Brief topic description")
    category: TopicCategory = Field(..., description="Primary topic category")

    # Classification
    discipline: Optional[BusinessDiscipline] = Field(None, description="Business discipline if academic")
    theme: Optional[CrossCuttingTheme] = Field(None, description="Cross-cutting theme if applicable")

    # Metadata
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    keywords: List[str] = Field(default_factory=list, description="Related keywords")

    # Frequency and importance
    frequency: int = Field(default=0, description="Number of times topic appears")
    importance: float = Field(default=0.5, ge=0, le=1, description="Topic importance score")

    # Taxonomy relationships
    parent_topic_id: Optional[str] = Field(None, description="Parent topic ID in hierarchy")
    related_topics: List[str] = Field(default_factory=list, description="Related topic IDs")

    # Source tracking
    source: str = Field(default="llm", description="Extraction source (llm, manual, rule)")
    extracted_at: Optional[str] = Field(None, description="Extraction timestamp")


class TopicRelevance(BaseModel):
    """
    Relevance score and context for a topic assignment.

    Used in HAS_TOPIC relationship properties.
    """
    topic_id: str = Field(..., description="Topic ID")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    relevance: float = Field(..., ge=0, le=1, description="Relevance score (0-1)")
    context: Optional[str] = Field(None, description="Context snippet where topic appears")
    position: Optional[int] = Field(None, description="Position in content (for ranking)")

    # LLM metadata
    model: str = Field(default="gpt-4", description="LLM model used")
    prompt_version: str = Field(default="v1", description="Prompt version")


class TopicExtractionResult(BaseModel):
    """Result from LLM topic extraction"""
    topics: List[Dict] = Field(..., description="Extracted topics with metadata")
    source_id: str = Field(..., description="Source Page/Section ID")
    source_type: str = Field(..., description="Source type (Page/Section)")
    content_preview: str = Field(..., description="Content preview (first 200 chars)")

    # Statistics
    total_tokens: Optional[int] = Field(None, description="Tokens used")
    extraction_time: Optional[float] = Field(None, description="Extraction time in seconds")


class TopicStatistics(BaseModel):
    """Statistics for topic extraction process"""
    total_topics: int = Field(default=0, description="Total unique topics")
    total_assignments: int = Field(default=0, description="Total topic assignments")

    # By category
    topics_by_category: Dict[str, int] = Field(default_factory=dict, description="Topics per category")

    # By source
    topics_by_source: Dict[str, int] = Field(default_factory=dict, description="Assignments per source type")

    # Quality metrics
    avg_confidence: float = Field(default=0, description="Average confidence score")
    avg_topics_per_item: float = Field(default=0, description="Average topics per content item")

    # Cost tracking
    total_api_calls: int = Field(default=0, description="Total LLM API calls")
    estimated_cost: float = Field(default=0, description="Estimated cost in USD")

    # Processing
    items_processed: int = Field(default=0, description="Items processed")
    items_failed: int = Field(default=0, description="Items that failed")
    processing_time: float = Field(default=0, description="Total processing time")


class TopicTaxonomy:
    """
    Static taxonomy of predefined topics from LBS site analysis.

    Used for validation and suggestion during LLM extraction.
    """

    # Academic disciplines from taxonomy
    ACADEMIC_TOPICS = {
        "Corporate Finance": BusinessDiscipline.ACCOUNTING_FINANCE,
        "Financial Markets": BusinessDiscipline.ACCOUNTING_FINANCE,
        "Investment Management": BusinessDiscipline.ACCOUNTING_FINANCE,
        "Risk Management": BusinessDiscipline.ACCOUNTING_FINANCE,
        "Microeconomics": BusinessDiscipline.ECONOMICS,
        "Macroeconomics": BusinessDiscipline.ECONOMICS,
        "Behavioral Economics": BusinessDiscipline.ECONOMICS,
        "Brand Management": BusinessDiscipline.MARKETING,
        "Digital Marketing": BusinessDiscipline.MARKETING,
        "Consumer Behavior": BusinessDiscipline.MARKETING,
        "Marketing Analytics": BusinessDiscipline.MARKETING,
        "Corporate Strategy": BusinessDiscipline.STRATEGY,
        "Competitive Strategy": BusinessDiscipline.STRATEGY,
        "Business Models": BusinessDiscipline.STRATEGY,
        "Operations Management": BusinessDiscipline.OPERATIONS_ANALYTICS,
        "Supply Chain": BusinessDiscipline.OPERATIONS_ANALYTICS,
        "Data Analytics": BusinessDiscipline.OPERATIONS_ANALYTICS,
        "Leadership": BusinessDiscipline.ORGANIZATIONAL_BEHAVIOUR,
        "Team Dynamics": BusinessDiscipline.ORGANIZATIONAL_BEHAVIOUR,
        "Change Management": BusinessDiscipline.ORGANIZATIONAL_BEHAVIOUR,
        "Organizational Culture": BusinessDiscipline.ORGANIZATIONAL_BEHAVIOUR,
        "Startup Strategy": BusinessDiscipline.ENTREPRENEURSHIP,
        "Venture Capital": BusinessDiscipline.ENTREPRENEURSHIP,
        "Innovation Management": BusinessDiscipline.ENTREPRENEURSHIP,
    }

    # Cross-cutting themes
    THEME_TOPICS = {
        "Sustainability": CrossCuttingTheme.SUSTAINABILITY_ESG,
        "ESG": CrossCuttingTheme.SUSTAINABILITY_ESG,
        "Environmental Sustainability": CrossCuttingTheme.SUSTAINABILITY_ESG,
        "Corporate Governance": CrossCuttingTheme.SUSTAINABILITY_ESG,
        "Digital Transformation": CrossCuttingTheme.TECHNOLOGY_DIGITAL,
        "Artificial Intelligence": CrossCuttingTheme.TECHNOLOGY_DIGITAL,
        "Fintech": CrossCuttingTheme.TECHNOLOGY_DIGITAL,
        "International Business": CrossCuttingTheme.GLOBALIZATION,
        "Emerging Markets": CrossCuttingTheme.GLOBALIZATION,
        "Gender Diversity": CrossCuttingTheme.DIVERSITY_INCLUSION,
        "Inclusive Leadership": CrossCuttingTheme.DIVERSITY_INCLUSION,
        "Remote Work": CrossCuttingTheme.FUTURE_OF_WORK,
        "Automation": CrossCuttingTheme.FUTURE_OF_WORK,
    }

    # Program-related topics
    PROGRAM_TOPICS = [
        "MBA", "Executive MBA", "Masters in Finance", "Masters in Management",
        "Masters in Analytics", "PhD Programme", "Executive Education",
        "Open Programmes", "Custom Programmes", "Online Learning"
    ]

    # Student life topics
    STUDENT_LIFE_TOPICS = [
        "Campus Life", "Student Clubs", "Career Services", "Accommodation",
        "International Students", "Student Support", "Networking",
        "Social Events", "Sports", "Wellbeing"
    ]

    # Research and faculty topics
    RESEARCH_TOPICS = [
        "Research Centers", "Faculty Research", "Publications", "Working Papers",
        "Case Studies", "Industry Partnerships", "Consulting", "Research Impact"
    ]

    @classmethod
    def get_all_topics(cls) -> List[str]:
        """Get all predefined topic names"""
        topics = []
        topics.extend(cls.ACADEMIC_TOPICS.keys())
        topics.extend(cls.THEME_TOPICS.keys())
        topics.extend(cls.PROGRAM_TOPICS)
        topics.extend(cls.STUDENT_LIFE_TOPICS)
        topics.extend(cls.RESEARCH_TOPICS)
        return topics

    @classmethod
    def get_category_for_topic(cls, topic_name: str) -> TopicCategory:
        """Infer category for a topic name"""
        topic_lower = topic_name.lower()

        # Check academic disciplines
        if topic_name in cls.ACADEMIC_TOPICS:
            return TopicCategory.ACADEMIC

        # Check programs
        if any(prog.lower() in topic_lower for prog in cls.PROGRAM_TOPICS):
            return TopicCategory.ACADEMIC

        # Check research
        if any(res.lower() in topic_lower for res in cls.RESEARCH_TOPICS):
            return TopicCategory.RESEARCH

        # Check student life
        if any(sl.lower() in topic_lower for sl in cls.STUDENT_LIFE_TOPICS):
            return TopicCategory.STUDENT_LIFE

        # Default
        return TopicCategory.GENERAL

    @classmethod
    def get_discipline(cls, topic_name: str) -> Optional[BusinessDiscipline]:
        """Get business discipline for topic if applicable"""
        return cls.ACADEMIC_TOPICS.get(topic_name)

    @classmethod
    def get_theme(cls, topic_name: str) -> Optional[CrossCuttingTheme]:
        """Get cross-cutting theme for topic if applicable"""
        return cls.THEME_TOPICS.get(topic_name)


@dataclass
class TopicCluster:
    """
    Topic cluster for hierarchical topic organization.
    Stub class for test compatibility - to be implemented.
    """
    id: str
    name: str
    topics: List[str] = field(default_factory=list)
    parent_cluster: Optional[str] = None
    level: int = 0
