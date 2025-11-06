"""
Ground truth topic labels for validation.
10 pages with manually labeled topics.
"""

GROUND_TRUTH_TOPICS = [
    {
        "page_id": "gt_topic_001",
        "title": "MBA Programme Overview",
        "text": "The MBA programme at London Business School is a transformative 15-21 month journey...",
        "expected_topics": [
            {"name": "MBA Programme", "category": "academic_programmes", "importance_min": 0.9},
            {"name": "Business Education", "category": "academic_programmes", "importance_min": 0.75},
            {"name": "Career Development", "category": "career_services", "importance_min": 0.7}
        ],
        "expected_topic_count_min": 3,
        "expected_topic_count_max": 5
    },
    {
        "page_id": "gt_topic_002",
        "title": "Finance Faculty Research",
        "text": "Our Finance department conducts cutting-edge research in asset pricing, corporate governance...",
        "expected_topics": [
            {"name": "Finance", "category": "academic_programmes", "importance_min": 0.9},
            {"name": "Research", "category": "research_areas", "importance_min": 0.85},
            {"name": "Asset Pricing", "category": "research_areas", "importance_min": 0.7},
            {"name": "Corporate Governance", "category": "research_areas", "importance_min": 0.7}
        ],
        "expected_topic_count_min": 4,
        "expected_topic_count_max": 6
    },
    {
        "page_id": "gt_topic_003",
        "title": "Executive Education Programmes",
        "text": "LBS offers executive education programmes for senior leaders and high-potential managers...",
        "expected_topics": [
            {"name": "Executive Education", "category": "academic_programmes", "importance_min": 0.9},
            {"name": "Leadership Development", "category": "career_services", "importance_min": 0.8}
        ],
        "expected_topic_count_min": 2,
        "expected_topic_count_max": 4
    },
    {
        "page_id": "gt_topic_004",
        "title": "Alumni Network Events",
        "text": "The LBS Alumni Network hosts regular events connecting graduates across industries and geographies...",
        "expected_topics": [
            {"name": "Alumni Network", "category": "student_life", "importance_min": 0.9},
            {"name": "Networking", "category": "student_life", "importance_min": 0.8},
            {"name": "Professional Development", "category": "career_services", "importance_min": 0.7}
        ],
        "expected_topic_count_min": 3,
        "expected_topic_count_max": 5
    },
    {
        "page_id": "gt_topic_005",
        "title": "Admissions Requirements",
        "text": "Applicants to the MBA programme must have a bachelor's degree, GMAT/GRE scores, and professional experience...",
        "expected_topics": [
            {"name": "Admissions", "category": "admissions_info", "importance_min": 0.95},
            {"name": "Application Process", "category": "admissions_info", "importance_min": 0.85},
            {"name": "Requirements", "category": "admissions_info", "importance_min": 0.8}
        ],
        "expected_topic_count_min": 3,
        "expected_topic_count_max": 5
    }
]

def validate_topic_extraction(page_id: str, extracted_topics: list) -> dict:
    """Validate extracted topics against ground truth."""
    truth = next((item for item in GROUND_TRUTH_TOPICS if item["page_id"] == page_id), None)
    if not truth:
        return {"valid": False, "error": "Page ID not found in ground truth"}

    topic_count_valid = truth["expected_topic_count_min"] <= len(extracted_topics) <= truth["expected_topic_count_max"]

    # Check for expected topics
    expected_names = {t["name"].lower() for t in truth["expected_topics"]}
    extracted_names = {t["name"].lower() if isinstance(t, dict) else str(t).lower() for t in extracted_topics}

    matches = expected_names.intersection(extracted_names)
    recall = len(matches) / len(expected_names) if expected_names else 0

    return {
        "valid": topic_count_valid and recall >= 0.5,  # At least 50% recall
        "topic_count_valid": topic_count_valid,
        "recall": recall,
        "expected_topics": len(expected_names),
        "extracted_topics": len(extracted_names),
        "matches": len(matches)
    }
