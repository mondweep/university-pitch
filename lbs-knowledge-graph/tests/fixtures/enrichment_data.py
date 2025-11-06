"""
Test Fixtures for Phase 3 Semantic Enrichment
Mock LLM responses, sample content, and enriched graph data
Target: 300+ lines
"""

import pytest
from typing import Dict, List, Any
from datetime import datetime


# ==================== Mock LLM Responses ====================

@pytest.fixture
def mock_sentiment_responses() -> Dict[str, Dict[str, Any]]:
    """Mock sentiment analysis responses from LLM"""
    return {
        "positive": {
            "sentiment": "positive",
            "score": 0.85,
            "confidence": 0.92,
            "aspects": {
                "career_growth": 0.90,
                "learning_experience": 0.85,
                "networking": 0.80
            },
            "reasoning": "The text emphasizes transformative career outcomes and world-class education"
        },
        "negative": {
            "sentiment": "negative",
            "score": -0.65,
            "confidence": 0.88,
            "aspects": {
                "cost": -0.75,
                "time_commitment": -0.60,
                "stress": -0.55
            },
            "reasoning": "The text focuses on challenges, costs, and demanding workload"
        },
        "neutral": {
            "sentiment": "neutral",
            "score": 0.05,
            "confidence": 0.75,
            "aspects": {
                "factual_info": 0.00,
                "descriptive": 0.10
            },
            "reasoning": "The text provides factual information without emotional context"
        },
        "mixed": {
            "sentiment": "mixed",
            "score": 0.15,
            "confidence": 0.80,
            "aspects": {
                "opportunity": 0.70,
                "challenge": -0.40
            },
            "reasoning": "The text balances positive opportunities with realistic challenges"
        }
    }


@pytest.fixture
def mock_topic_responses() -> Dict[str, Dict[str, Any]]:
    """Mock topic extraction responses from LLM"""
    return {
        "mba_page": {
            "topics": [
                {
                    "name": "Business Education",
                    "relevance": 0.95,
                    "keywords": ["MBA", "business school", "education", "programme"],
                    "category": "education"
                },
                {
                    "name": "Career Development",
                    "relevance": 0.88,
                    "keywords": ["career", "transformation", "opportunities", "growth"],
                    "category": "career"
                },
                {
                    "name": "Leadership",
                    "relevance": 0.75,
                    "keywords": ["leadership", "management", "executive"],
                    "category": "skills"
                },
                {
                    "name": "Global Perspective",
                    "relevance": 0.70,
                    "keywords": ["global", "international", "diverse", "cohort"],
                    "category": "experience"
                },
                {
                    "name": "Finance",
                    "relevance": 0.65,
                    "keywords": ["finance", "investment", "financial"],
                    "category": "subject"
                }
            ],
            "primary_topic": "Business Education",
            "topic_distribution": {
                "education": 0.40,
                "career": 0.30,
                "skills": 0.20,
                "experience": 0.10
            }
        },
        "faculty_page": {
            "topics": [
                {
                    "name": "Faculty Profile",
                    "relevance": 0.98,
                    "keywords": ["professor", "faculty", "academic", "expertise"],
                    "category": "people"
                },
                {
                    "name": "Research",
                    "relevance": 0.85,
                    "keywords": ["research", "publications", "studies"],
                    "category": "academic"
                },
                {
                    "name": "Corporate Finance",
                    "relevance": 0.80,
                    "keywords": ["finance", "corporate", "strategy"],
                    "category": "subject"
                }
            ],
            "primary_topic": "Faculty Profile",
            "topic_distribution": {
                "people": 0.50,
                "academic": 0.30,
                "subject": 0.20
            }
        }
    }


@pytest.fixture
def mock_ner_responses() -> Dict[str, Dict[str, Any]]:
    """Mock named entity recognition responses from LLM"""
    return {
        "mba_content": {
            "entities": [
                {
                    "text": "London Business School",
                    "type": "ORGANIZATION",
                    "confidence": 0.98,
                    "context": "...at London Business School offers..."
                },
                {
                    "text": "MBA",
                    "type": "PROGRAM",
                    "confidence": 0.95,
                    "context": "...our MBA programme..."
                },
                {
                    "text": "London",
                    "type": "LOCATION",
                    "confidence": 0.92,
                    "context": "...based in London..."
                },
                {
                    "text": "15-21 months",
                    "type": "DURATION",
                    "confidence": 0.90,
                    "context": "...programme duration of 15-21 months..."
                }
            ],
            "entity_counts": {
                "ORGANIZATION": 3,
                "PROGRAM": 5,
                "LOCATION": 2,
                "DURATION": 1,
                "PERSON": 0
            }
        },
        "faculty_content": {
            "entities": [
                {
                    "text": "Professor John Doe",
                    "type": "PERSON",
                    "confidence": 0.99,
                    "context": "...Professor John Doe specializes..."
                },
                {
                    "text": "Finance Department",
                    "type": "ORGANIZATION",
                    "confidence": 0.93,
                    "context": "...in the Finance Department..."
                },
                {
                    "text": "PhD",
                    "type": "DEGREE",
                    "confidence": 0.95,
                    "context": "...holds a PhD from..."
                }
            ],
            "entity_counts": {
                "PERSON": 1,
                "ORGANIZATION": 1,
                "DEGREE": 1
            }
        }
    }


@pytest.fixture
def mock_persona_responses() -> Dict[str, Dict[str, Any]]:
    """Mock persona classification responses from LLM"""
    return {
        "prospective_student": {
            "personas": [
                {
                    "name": "Prospective MBA Student",
                    "relevance": 0.95,
                    "confidence": 0.92,
                    "indicators": [
                        "programme details",
                        "admission requirements",
                        "career outcomes"
                    ],
                    "intent": "research_program"
                },
                {
                    "name": "Career Changer",
                    "relevance": 0.75,
                    "confidence": 0.85,
                    "indicators": [
                        "career transformation",
                        "new opportunities"
                    ],
                    "intent": "career_development"
                }
            ],
            "primary_persona": "Prospective MBA Student",
            "journey_stage": "awareness"
        },
        "alumni": {
            "personas": [
                {
                    "name": "Alumni",
                    "relevance": 0.88,
                    "confidence": 0.90,
                    "indicators": [
                        "alumni network",
                        "continuing education",
                        "reunions"
                    ],
                    "intent": "stay_connected"
                }
            ],
            "primary_persona": "Alumni",
            "journey_stage": "retention"
        },
        "corporate_partner": {
            "personas": [
                {
                    "name": "Corporate Partner",
                    "relevance": 0.92,
                    "confidence": 0.88,
                    "indicators": [
                        "executive education",
                        "corporate programmes",
                        "recruitment"
                    ],
                    "intent": "partnership"
                }
            ],
            "primary_persona": "Corporate Partner",
            "journey_stage": "engagement"
        }
    }


# ==================== Sample Content for Testing ====================

@pytest.fixture
def sample_content_items() -> List[Dict[str, Any]]:
    """Sample content items for enrichment testing"""
    return [
        {
            "id": "content-1",
            "text": "Transform your career with our world-class MBA programme. Join a diverse cohort of ambitious professionals.",
            "type": "paragraph",
            "page_id": "mba-page",
            "section_id": "hero-section",
            "word_count": 15,
            "expected_sentiment": "positive",
            "expected_topics": ["Business Education", "Career Development"],
            "expected_persona": "Prospective MBA Student"
        },
        {
            "id": "content-2",
            "text": "The programme requires a significant time commitment and substantial financial investment.",
            "type": "paragraph",
            "page_id": "mba-page",
            "section_id": "requirements-section",
            "word_count": 12,
            "expected_sentiment": "neutral",
            "expected_topics": ["Programme Requirements"],
            "expected_persona": "Prospective MBA Student"
        },
        {
            "id": "content-3",
            "text": "Professor John Doe specializes in corporate finance and has published extensively in top journals.",
            "type": "paragraph",
            "page_id": "faculty-page",
            "section_id": "profile-section",
            "word_count": 14,
            "expected_sentiment": "neutral",
            "expected_topics": ["Faculty Profile", "Research"],
            "expected_persona": "Prospective Student"
        }
    ]


# ==================== Graph Fixtures with Enrichment ====================

@pytest.fixture
def enriched_page_data() -> Dict[str, Any]:
    """Sample page with semantic enrichment"""
    return {
        "id": "mba-page",
        "url": "https://london.edu/programmes/mba",
        "title": "MBA Programme",
        "type": "programme",
        "enrichment": {
            "sentiment": {
                "score": 0.85,
                "label": "positive",
                "confidence": 0.92,
                "updated_at": "2025-11-05T19:00:00Z"
            },
            "topics": [
                {
                    "name": "Business Education",
                    "relevance": 0.95,
                    "category": "education"
                },
                {
                    "name": "Career Development",
                    "relevance": 0.88,
                    "category": "career"
                }
            ],
            "entities": [
                {
                    "text": "London Business School",
                    "type": "ORGANIZATION",
                    "confidence": 0.98
                },
                {
                    "text": "MBA",
                    "type": "PROGRAM",
                    "confidence": 0.95
                }
            ],
            "personas": [
                {
                    "name": "Prospective MBA Student",
                    "relevance": 0.95,
                    "intent": "research_program"
                }
            ]
        }
    }


@pytest.fixture
def enriched_graph_fixture(mock_graph, enriched_page_data):
    """Graph fixture with enriched data"""
    # Add enriched page
    mock_graph.add_node("mba-page", "Page", enriched_page_data)

    # Add topic nodes
    mock_graph.add_node("topic-business-edu", "Topic", {
        "id": "topic-business-edu",
        "name": "Business Education",
        "category": "education",
        "description": "Educational programmes and degrees in business"
    })

    # Add persona node
    mock_graph.add_node("persona-prospective", "Persona", {
        "id": "persona-prospective",
        "name": "Prospective MBA Student",
        "description": "Individuals researching MBA programmes",
        "journey_stages": ["awareness", "consideration", "decision"]
    })

    # Add HAS_TOPIC relationship
    mock_graph.add_edge("mba-page", "topic-business-edu", "HAS_TOPIC", {
        "relevance": 0.95,
        "confidence": 0.92,
        "extracted_at": "2025-11-05T19:00:00Z"
    })

    # Add TARGETS relationship
    mock_graph.add_edge("mba-page", "persona-prospective", "TARGETS", {
        "relevance": 0.95,
        "confidence": 0.90,
        "intent": "research_program",
        "journey_stage": "awareness"
    })

    return mock_graph


# ==================== Expected Results ====================

@pytest.fixture
def expected_sentiment_results() -> Dict[str, Any]:
    """Expected sentiment analysis results"""
    return {
        "content-1": {
            "sentiment": "positive",
            "score": 0.85,
            "confidence": 0.92
        },
        "content-2": {
            "sentiment": "neutral",
            "score": 0.05,
            "confidence": 0.75
        },
        "content-3": {
            "sentiment": "neutral",
            "score": 0.00,
            "confidence": 0.80
        }
    }


@pytest.fixture
def expected_topic_results() -> Dict[str, List[str]]:
    """Expected topic extraction results"""
    return {
        "content-1": ["Business Education", "Career Development"],
        "content-2": ["Programme Requirements", "Admissions"],
        "content-3": ["Faculty Profile", "Research", "Corporate Finance"]
    }


@pytest.fixture
def expected_entity_results() -> Dict[str, List[Dict[str, Any]]]:
    """Expected NER results"""
    return {
        "content-1": [
            {"text": "MBA", "type": "PROGRAM"}
        ],
        "content-3": [
            {"text": "Professor John Doe", "type": "PERSON"},
            {"text": "corporate finance", "type": "SUBJECT"}
        ]
    }


# ==================== Batch Processing Fixtures ====================

@pytest.fixture
def large_content_batch() -> List[Dict[str, Any]]:
    """Large batch of content for performance testing"""
    return [
        {
            "id": f"content-{i}",
            "text": f"Sample content item {i} for batch processing and performance testing.",
            "type": "paragraph"
        }
        for i in range(100)
    ]


@pytest.fixture
def cost_tracking_data() -> Dict[str, Any]:
    """Data for LLM cost tracking tests"""
    return {
        "api_calls": {
            "single": {
                "items": 1,
                "tokens_in": 50,
                "tokens_out": 100,
                "cost": 0.0015
            },
            "batch_50": {
                "items": 50,
                "tokens_in": 2500,
                "tokens_out": 3000,
                "cost": 0.055
            }
        },
        "expected_savings": {
            "batch_vs_single": 0.65,  # 65% cost reduction
            "percentage": 65
        }
    }
