"""
Journey Models for Persona Journey Mapping

Defines data structures for modeling user journeys through content:
- Journey stages (AWARENESS → CONSIDERATION → DECISION → ACTION → RETENTION)
- Journey paths (sequences of pages with transition probabilities)
- Entry points and conversion points
"""

from enum import Enum
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, Field
from datetime import datetime


class JourneyStage(str, Enum):
    """Journey stages in the customer decision process"""
    AWARENESS = "awareness"           # Initial discovery and exploration
    CONSIDERATION = "consideration"   # Evaluating options and comparing
    DECISION = "decision"            # Making the decision to apply/engage
    ACTION = "action"                # Taking action (apply, register, contact)
    RETENTION = "retention"          # Post-action engagement and loyalty


class JourneyPath(BaseModel):
    """A sequence of pages representing a typical user journey"""
    path_id: str = Field(..., description="Unique identifier for this path")
    persona_id: str = Field(..., description="Persona this path is typical for")
    page_sequence: List[str] = Field(default_factory=list, description="Ordered list of page IDs")
    transition_probs: List[float] = Field(default_factory=list, description="Probability of each transition")
    stage_labels: List[JourneyStage] = Field(default_factory=list, description="Journey stage for each page")
    frequency: int = Field(default=1, description="How common this path is")
    completion_rate: float = Field(default=0.0, description="Percentage who complete this path (0-1)")
    avg_duration_minutes: Optional[int] = Field(None, description="Average time to complete path")

    @property
    def length(self) -> int:
        """Number of pages in the path"""
        return len(self.page_sequence)

    @property
    def path_strength(self) -> float:
        """Overall strength of this path (average transition probability)"""
        if not self.transition_probs:
            return 0.0
        return sum(self.transition_probs) / len(self.transition_probs)


class EntryPoint(BaseModel):
    """A typical entry point for a persona's journey"""
    page_id: str = Field(..., description="Page ID of entry point")
    page_url: str = Field(..., description="URL of entry point")
    page_title: str = Field(..., description="Title of entry point")
    entry_rate: float = Field(..., description="Percentage of persona journeys starting here (0-1)")
    stage: JourneyStage = Field(default=JourneyStage.AWARENESS, description="Journey stage")
    traffic_sources: List[str] = Field(default_factory=list, description="Traffic sources (search, social, direct, etc.)")

    class Config:
        use_enum_values = True


class ConversionPoint(BaseModel):
    """A key decision or conversion point in a journey"""
    page_id: str = Field(..., description="Page ID of conversion point")
    page_url: str = Field(..., description="URL of conversion point")
    page_title: str = Field(..., description="Title of conversion point")
    conversion_rate: float = Field(..., description="Percentage who convert at this point (0-1)")
    stage: JourneyStage = Field(default=JourneyStage.DECISION, description="Journey stage")
    conversion_actions: List[str] = Field(default_factory=list, description="Actions taken (apply, contact, register)")

    class Config:
        use_enum_values = True


class JourneyStageInfo(BaseModel):
    """Information about pages in a specific journey stage"""
    stage: JourneyStage
    page_ids: Set[str] = Field(default_factory=set, description="Pages in this stage")
    typical_content_types: List[str] = Field(default_factory=list, description="Content types in this stage")
    avg_time_in_stage: Optional[int] = Field(None, description="Average time spent in stage (minutes)")
    transition_to: Dict[JourneyStage, float] = Field(default_factory=dict, description="Transitions to other stages")

    class Config:
        use_enum_values = True


class Journey(BaseModel):
    """Complete journey model for a persona"""
    journey_id: str = Field(..., description="Unique identifier")
    persona_id: str = Field(..., description="Persona this journey is for")
    persona_name: str = Field(..., description="Human-readable persona name")

    # Entry and conversion points
    entry_points: List[EntryPoint] = Field(default_factory=list, description="Typical entry points")
    conversion_points: List[ConversionPoint] = Field(default_factory=list, description="Key conversion points")

    # Journey stages
    stages: Dict[JourneyStage, JourneyStageInfo] = Field(
        default_factory=dict,
        description="Pages grouped by journey stage"
    )

    # Typical paths
    typical_paths: List[JourneyPath] = Field(default_factory=list, description="Common journey paths")

    # Journey metrics
    avg_path_length: float = Field(default=0.0, description="Average number of pages in journey")
    avg_completion_time: Optional[int] = Field(None, description="Average time to complete (minutes)")
    overall_completion_rate: float = Field(default=0.0, description="Overall journey completion rate (0-1)")

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="When journey was analyzed")
    page_count: int = Field(default=0, description="Total pages in journey")
    path_count: int = Field(default=0, description="Number of typical paths identified")

    class Config:
        use_enum_values = True

    def get_pages_for_stage(self, stage: JourneyStage) -> Set[str]:
        """Get all page IDs for a specific journey stage"""
        return self.stages.get(stage, JourneyStageInfo(stage=stage)).page_ids

    def get_most_common_paths(self, top_n: int = 5) -> List[JourneyPath]:
        """Get the most common paths ordered by frequency"""
        return sorted(self.typical_paths, key=lambda p: p.frequency, reverse=True)[:top_n]

    def get_top_entry_points(self, top_n: int = 3) -> List[EntryPoint]:
        """Get the top entry points ordered by entry rate"""
        return sorted(self.entry_points, key=lambda e: e.entry_rate, reverse=True)[:top_n]

    def get_top_conversion_points(self, top_n: int = 2) -> List[ConversionPoint]:
        """Get the top conversion points ordered by conversion rate"""
        return sorted(self.conversion_points, key=lambda c: c.conversion_rate, reverse=True)[:top_n]


class NextStepEdge(BaseModel):
    """Represents a NEXT_STEP relationship between pages"""
    from_page: str = Field(..., description="Source page ID")
    to_page: str = Field(..., description="Target page ID")
    transition_prob: float = Field(..., description="Probability of this transition (0-1)")
    persona_id: str = Field(..., description="Persona this transition is typical for")
    from_stage: Optional[JourneyStage] = Field(None, description="Journey stage of source page")
    to_stage: Optional[JourneyStage] = Field(None, description="Journey stage of target page")
    path_strength: float = Field(default=0.0, description="How common this transition is")
    sample_size: int = Field(default=1, description="Number of journey samples with this transition")

    class Config:
        use_enum_values = True

    @property
    def is_stage_progression(self) -> bool:
        """Check if this transition progresses to a later stage"""
        if not self.from_stage or not self.to_stage:
            return False

        stage_order = {
            JourneyStage.AWARENESS: 0,
            JourneyStage.CONSIDERATION: 1,
            JourneyStage.DECISION: 2,
            JourneyStage.ACTION: 3,
            JourneyStage.RETENTION: 4
        }

        return stage_order.get(self.to_stage, 0) > stage_order.get(self.from_stage, 0)


# Persona definitions (from SITE_TAXONOMY.md)
PERSONAS = {
    "prospective_student": {
        "name": "Prospective Student",
        "interests": ["programmes", "admissions", "student-experience", "career-outcomes"],
        "typical_entry_stages": [JourneyStage.AWARENESS, JourneyStage.CONSIDERATION]
    },
    "current_student": {
        "name": "Current Student",
        "interests": ["courses", "career-services", "clubs", "campus-facilities"],
        "typical_entry_stages": [JourneyStage.ACTION, JourneyStage.RETENTION]
    },
    "alumni": {
        "name": "Alumni",
        "interests": ["network", "continuing-education", "career-support", "giving"],
        "typical_entry_stages": [JourneyStage.RETENTION, JourneyStage.AWARENESS]
    },
    "faculty_researcher": {
        "name": "Faculty & Researcher",
        "interests": ["research", "publications", "collaborations", "teaching"],
        "typical_entry_stages": [JourneyStage.AWARENESS, JourneyStage.ACTION]
    },
    "corporate_partner": {
        "name": "Corporate Partner",
        "interests": ["recruitment", "custom-education", "research-partnerships"],
        "typical_entry_stages": [JourneyStage.CONSIDERATION, JourneyStage.DECISION]
    },
    "media_press": {
        "name": "Media & Press",
        "interests": ["press-releases", "faculty-experts", "research-findings"],
        "typical_entry_stages": [JourneyStage.AWARENESS]
    }
}


def get_persona_ids() -> List[str]:
    """Get list of all persona IDs"""
    return list(PERSONAS.keys())


def get_persona_name(persona_id: str) -> str:
    """Get human-readable persona name"""
    return PERSONAS.get(persona_id, {}).get("name", persona_id)
