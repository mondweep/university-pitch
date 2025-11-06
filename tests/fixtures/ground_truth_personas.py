"""
Ground truth persona labels for validation.
10 pages with manually labeled target personas.
"""

GROUND_TRUTH_PERSONAS = [
    {
        "content_id": "gt_persona_001",
        "title": "MBA Programme Application Guide",
        "text": "Learn how to apply to our MBA programme...",
        "expected_personas": [
            {
                "persona_name": "Prospective Students",
                "relevance_min": 0.85,
                "is_primary": True,
                "journey_stage": "consideration"
            }
        ],
        "expected_primary": "Prospective Students",
        "multi_target": False
    },
    {
        "content_id": "gt_persona_002",
        "title": "Alumni Career Services",
        "text": "Exclusive career support for LBS alumni...",
        "expected_personas": [
            {
                "persona_name": "Alumni",
                "relevance_min": 0.90,
                "is_primary": True,
                "journey_stage": "retention"
            }
        ],
        "expected_primary": "Alumni",
        "multi_target": False
    },
    {
        "content_id": "gt_persona_003",
        "title": "Faculty Research Opportunities",
        "text": "Join our research team and collaborate with leading academics...",
        "expected_personas": [
            {
                "persona_name": "Faculty & Staff",
                "relevance_min": 0.85,
                "is_primary": True,
                "journey_stage": "action"
            }
        ],
        "expected_primary": "Faculty & Staff",
        "multi_target": False
    },
    {
        "content_id": "gt_persona_004",
        "title": "Recruiting LBS Talent",
        "text": "Connect with top business school graduates for your organization...",
        "expected_personas": [
            {
                "persona_name": "Recruiters & Employers",
                "relevance_min": 0.90,
                "is_primary": True,
                "journey_stage": "action"
            }
        ],
        "expected_primary": "Recruiters & Employers",
        "multi_target": False
    },
    {
        "content_id": "gt_persona_005",
        "title": "Programme Information and Student Resources",
        "text": "Comprehensive guide for prospective and current students...",
        "expected_personas": [
            {
                "persona_name": "Prospective Students",
                "relevance_min": 0.75,
                "is_primary": True,
                "journey_stage": "consideration"
            },
            {
                "persona_name": "Current Students",
                "relevance_min": 0.70,
                "is_primary": False,
                "journey_stage": "action"
            }
        ],
        "expected_primary": "Prospective Students",
        "multi_target": True
    }
]

def validate_persona_classification(content_id: str, extracted_personas: list, primary_persona: str) -> dict:
    """Validate persona classification against ground truth."""
    truth = next((item for item in GROUND_TRUTH_PERSONAS if item["content_id"] == content_id), None)
    if not truth:
        return {"valid": False, "error": "Content ID not found in ground truth"}

    # Check primary persona
    primary_correct = primary_persona == truth["expected_primary"]

    # Check multi-target classification
    multi_target_correct = (len(extracted_personas) > 1) == truth["multi_target"]

    # Check expected personas are present
    expected_names = {p["persona_name"] for p in truth["expected_personas"]}
    extracted_names = {
        p["persona_name"] if isinstance(p, dict) else
        (p.name if hasattr(p, 'name') else str(p))
        for p in extracted_personas
    }

    matches = expected_names.intersection(extracted_names)
    recall = len(matches) / len(expected_names) if expected_names else 0

    return {
        "valid": primary_correct and recall >= 0.8,  # 80% recall required
        "primary_correct": primary_correct,
        "multi_target_correct": multi_target_correct,
        "recall": recall,
        "expected_personas": len(expected_names),
        "extracted_personas": len(extracted_names),
        "matches": len(matches)
    }
