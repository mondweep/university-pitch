"""
Data models for persona classification and targeting.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class PersonaType(Enum):
    """Target persona types based on LBS audience taxonomy."""
    PROSPECTIVE_STUDENTS = "prospective_students"
    CURRENT_STUDENTS = "current_students"
    ALUMNI = "alumni"
    FACULTY_STAFF = "faculty_staff"
    RECRUITERS = "recruiters"
    MEDIA = "media"


class JourneyStage(Enum):
    """User journey stages for persona targeting."""
    AWARENESS = "awareness"          # Discovering LBS
    CONSIDERATION = "consideration"  # Evaluating programs
    DECISION = "decision"            # Making choice
    ACTION = "action"                # Applying/enrolling
    RETENTION = "retention"          # Staying engaged


@dataclass
class Persona:
    """Persona entity representing a target audience."""
    id: str
    name: str
    type: PersonaType
    slug: str
    description: str
    characteristics: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    priority: int = 3  # 1-5, higher = more important
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'slug': self.slug,
            'description': self.description,
            'characteristics': self.characteristics,
            'goals': self.goals,
            'pain_points': self.pain_points,
            'interests': self.interests,
            'priority': self.priority,
            'metadata': self.metadata
        }


@dataclass
class PersonaTarget:
    """Target relationship between content and persona."""
    persona_id: str
    persona_name: str
    relevance: float  # 0-1 score
    journey_stage: JourneyStage
    intent: str  # Why this targets this persona
    confidence: float = 1.0  # LLM confidence
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'persona_id': self.persona_id,
            'persona_name': self.persona_name,
            'relevance': self.relevance,
            'journey_stage': self.journey_stage.value,
            'intent': self.intent,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


# LBS Persona Definitions (from SITE_TAXONOMY.md)
LBS_PERSONAS = {
    PersonaType.PROSPECTIVE_STUDENTS: Persona(
        id="persona_prospective",
        name="Prospective Students",
        type=PersonaType.PROSPECTIVE_STUDENTS,
        slug="prospective-students",
        description="Individuals considering MBA, Masters, or PhD programs at LBS",
        characteristics=[
            "Career changers or advancers",
            "International backgrounds",
            "3-10 years work experience",
            "High achievers",
            "Leadership potential"
        ],
        goals=[
            "Understand program offerings",
            "Evaluate admission requirements",
            "Learn about career outcomes",
            "Compare with other schools",
            "Understand financial options"
        ],
        pain_points=[
            "Uncertainty about program fit",
            "Concerns about cost/ROI",
            "Application process complexity",
            "Work-life balance during program"
        ],
        interests=[
            "Program curriculum",
            "Faculty expertise",
            "Career services",
            "Alumni network",
            "Campus life"
        ],
        priority=5
    ),
    PersonaType.CURRENT_STUDENTS: Persona(
        id="persona_current",
        name="Current Students",
        type=PersonaType.CURRENT_STUDENTS,
        slug="current-students",
        description="Enrolled students actively participating in programs",
        characteristics=[
            "Enrolled in MBA, Masters, or PhD",
            "Accessing campus resources",
            "Building networks",
            "Engaged in academics"
        ],
        goals=[
            "Access course materials",
            "Find internships/jobs",
            "Join clubs and activities",
            "Connect with faculty",
            "Use support services"
        ],
        pain_points=[
            "Information overload",
            "Time management",
            "Career uncertainty",
            "Resource navigation"
        ],
        interests=[
            "Academic resources",
            "Career services",
            "Student clubs",
            "Events and workshops",
            "Support services"
        ],
        priority=4
    ),
    PersonaType.ALUMNI: Persona(
        id="persona_alumni",
        name="Alumni",
        type=PersonaType.ALUMNI,
        slug="alumni",
        description="LBS graduates maintaining connection with the school",
        characteristics=[
            "Program graduates",
            "Global network members",
            "Career established",
            "Potential mentors/donors"
        ],
        goals=[
            "Stay connected to LBS",
            "Access alumni resources",
            "Mentor current students",
            "Attend reunions and events",
            "Continue professional development"
        ],
        pain_points=[
            "Staying informed about LBS",
            "Finding relevant alumni events",
            "Leveraging alumni network"
        ],
        interests=[
            "Alumni events",
            "Networking opportunities",
            "Executive education",
            "Giving back",
            "LBS news and updates"
        ],
        priority=3
    ),
    PersonaType.FACULTY_STAFF: Persona(
        id="persona_faculty",
        name="Faculty & Staff",
        type=PersonaType.FACULTY_STAFF,
        slug="faculty-staff",
        description="LBS employees including faculty, researchers, and staff",
        characteristics=[
            "Internal audience",
            "Academic experts",
            "Administrative professionals",
            "Research active"
        ],
        goals=[
            "Access internal resources",
            "Share research and expertise",
            "Support students",
            "Collaborate with colleagues",
            "Professional development"
        ],
        pain_points=[
            "Administrative processes",
            "Resource access",
            "Communication gaps"
        ],
        interests=[
            "Research resources",
            "Teaching tools",
            "Faculty profiles",
            "Internal policies",
            "Professional development"
        ],
        priority=3
    ),
    PersonaType.RECRUITERS: Persona(
        id="persona_recruiters",
        name="Recruiters & Employers",
        type=PersonaType.RECRUITERS,
        slug="recruiters-employers",
        description="Companies and recruiters seeking to hire LBS talent",
        characteristics=[
            "Corporate partners",
            "Hiring managers",
            "Talent acquisition professionals",
            "Seeking MBA/Masters talent"
        ],
        goals=[
            "Access talent pool",
            "Post job opportunities",
            "Understand student profiles",
            "Build corporate partnerships",
            "Attend recruiting events"
        ],
        pain_points=[
            "Finding right candidates",
            "Understanding program offerings",
            "Navigating recruiting process"
        ],
        interests=[
            "Student profiles",
            "Career services",
            "Recruiting events",
            "Corporate partnerships",
            "Alumni outcomes"
        ],
        priority=3
    ),
    PersonaType.MEDIA: Persona(
        id="persona_media",
        name="Media & Press",
        type=PersonaType.MEDIA,
        slug="media-press",
        description="Journalists, media outlets, and press seeking information",
        characteristics=[
            "Journalists and reporters",
            "Media organizations",
            "Content creators",
            "External stakeholders"
        ],
        goals=[
            "Access press releases",
            "Contact faculty experts",
            "Get institutional information",
            "Find research insights",
            "Access media resources"
        ],
        pain_points=[
            "Finding contact information",
            "Accessing timely information",
            "Understanding research"
        ],
        interests=[
            "News and announcements",
            "Faculty expertise",
            "Research publications",
            "Media contacts",
            "Institutional facts"
        ],
        priority=2
    )
}


def get_persona_by_type(persona_type: PersonaType) -> Persona:
    """Get persona definition by type."""
    return LBS_PERSONAS[persona_type]


def get_all_personas() -> List[Persona]:
    """Get all persona definitions."""
    return list(LBS_PERSONAS.values())


def get_persona_by_id(persona_id: str) -> Optional[Persona]:
    """Get persona by ID."""
    for persona in LBS_PERSONAS.values():
        if persona.id == persona_id:
            return persona
    return None


def get_persona_by_name(name: str) -> Optional[Persona]:
    """Get persona by name (case-insensitive)."""
    name_lower = name.lower()
    for persona in LBS_PERSONAS.values():
        if persona.name.lower() == name_lower or persona.slug == name_lower:
            return persona
    return None
