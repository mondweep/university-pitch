"""
Mock LLM responses for deterministic testing.
"""

# Sentiment analysis mock responses
SENTIMENT_MOCK_RESPONSES = {
    "positive": {
        "content": '{"polarity": "positive", "score": 0.85, "confidence": 0.9, "magnitude": 0.8}',
        "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70}
    },
    "negative": {
        "content": '{"polarity": "negative", "score": 0.25, "confidence": 0.85, "magnitude": 0.7}',
        "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70}
    },
    "neutral": {
        "content": '{"polarity": "neutral", "score": 0.5, "confidence": 0.75, "magnitude": 0.3}',
        "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70}
    },
    "mixed": {
        "content": '{"polarity": "mixed", "score": 0.6, "confidence": 0.7, "magnitude": 0.6}',
        "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70}
    }
}

# Topic extraction mock responses
TOPIC_MOCK_RESPONSES = {
    "academic": {
        "content": '''{"topics": [
            {"name": "Finance", "category": "academic_programmes", "importance": 0.9, "keywords": ["finance", "investment", "banking"]},
            {"name": "MBA Programme", "category": "academic_programmes", "importance": 0.85, "keywords": ["mba", "masters", "business"]}
        ]}''',
        "usage": {"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 180}
    },
    "research": {
        "content": '''{"topics": [
            {"name": "Research Methods", "category": "research_areas", "importance": 0.75, "keywords": ["research", "methodology", "analysis"]},
            {"name": "Innovation", "category": "research_areas", "importance": 0.7, "keywords": ["innovation", "technology", "development"]}
        ]}''',
        "usage": {"prompt_tokens": 100, "completion_tokens": 80, "total_tokens": 180}
    }
}

# NER mock responses
NER_MOCK_RESPONSES = {
    "people_org": {
        "content": '''{"entities": [
            {
                "text": "Professor Jane Smith",
                "type": "PERSON",
                "metadata": {"role": "Professor", "department": "Finance", "affiliation": "London Business School"},
                "context": "Professor Jane Smith leads the Finance department at London Business School",
                "confidence": 0.95,
                "position": 0
            },
            {
                "text": "London Business School",
                "type": "ORGANIZATION",
                "metadata": {"type": "Business School", "location": "London"},
                "context": "at London Business School, a leading institution",
                "confidence": 0.98,
                "position": 50
            }
        ]}''',
        "usage": {"prompt_tokens": 200, "completion_tokens": 150, "total_tokens": 350}
    },
    "locations_events": {
        "content": '''{"entities": [
            {
                "text": "London",
                "type": "LOCATION",
                "metadata": {"type": "city", "country": "United Kingdom"},
                "context": "based in London, the financial capital",
                "confidence": 0.92,
                "position": 20
            },
            {
                "text": "Global Leadership Conference",
                "type": "EVENT",
                "metadata": {"date": "2024-06-15", "type": "Conference"},
                "context": "at the Global Leadership Conference next month",
                "confidence": 0.88,
                "position": 100
            }
        ]}''',
        "usage": {"prompt_tokens": 200, "completion_tokens": 150, "total_tokens": 350}
    }
}

# Persona classification mock responses
PERSONA_MOCK_RESPONSES = {
    "prospective_students": {
        "content": '''{"personas": [
            {
                "persona": "Prospective Students",
                "relevance": 0.90,
                "is_primary": true,
                "journey_stage": "consideration",
                "signals": ["MBA programme", "career switch", "application process"],
                "intent": "Inform prospective students about MBA options"
            }
        ]}''',
        "usage": {"prompt_tokens": 120, "completion_tokens": 100, "total_tokens": 220}
    },
    "alumni": {
        "content": '''{"personas": [
            {
                "persona": "Alumni",
                "relevance": 0.85,
                "is_primary": true,
                "journey_stage": "retention",
                "signals": ["alumni network", "continued learning", "career development"],
                "intent": "Engage alumni with networking opportunities"
            }
        ]}''',
        "usage": {"prompt_tokens": 120, "completion_tokens": 100, "total_tokens": 220}
    },
    "multi_target": {
        "content": '''{"personas": [
            {
                "persona": "Prospective Students",
                "relevance": 0.88,
                "is_primary": true,
                "journey_stage": "consideration",
                "signals": ["programme information", "admissions"],
                "intent": "Inform about programmes"
            },
            {
                "persona": "Current Students",
                "relevance": 0.72,
                "is_primary": false,
                "journey_stage": "action",
                "signals": ["course resources", "academic support"],
                "intent": "Support current students"
            }
        ]}''',
        "usage": {"prompt_tokens": 120, "completion_tokens": 150, "total_tokens": 270}
    }
}
