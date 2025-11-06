"""
Ground truth NER labels for validation.
10 pages with manually labeled entities.
"""

GROUND_TRUTH_NER = [
    {
        "content_id": "gt_ner_001",
        "text": "Professor Jane Smith from the Finance department at London Business School...",
        "expected_entities": [
            {
                "text": "Professor Jane Smith",
                "type": "PERSON",
                "metadata": {"role": "Professor", "department": "Finance"}
            },
            {
                "text": "Finance",
                "type": "ORGANIZATION",  # Department
                "metadata": {"type": "Department"}
            },
            {
                "text": "London Business School",
                "type": "ORGANIZATION",
                "metadata": {"type": "Business School"}
            }
        ],
        "expected_entity_count_min": 3,
        "expected_entity_count_max": 4
    },
    {
        "content_id": "gt_ner_002",
        "text": "The Global Leadership Conference will be held in London from June 15-17, 2024...",
        "expected_entities": [
            {
                "text": "Global Leadership Conference",
                "type": "EVENT",
                "metadata": {"date": "2024-06-15 to 2024-06-17"}
            },
            {
                "text": "London",
                "type": "LOCATION",
                "metadata": {"type": "city"}
            }
        ],
        "expected_entity_count_min": 2,
        "expected_entity_count_max": 3
    },
    {
        "content_id": "gt_ner_003",
        "text": "Dr. Michael Chen, Senior Lecturer in Strategy, collaborates with Harvard Business School...",
        "expected_entities": [
            {
                "text": "Dr. Michael Chen",
                "type": "PERSON",
                "metadata": {"role": "Senior Lecturer", "department": "Strategy"}
            },
            {
                "text": "Strategy",
                "type": "ORGANIZATION",  # Department
                "metadata": {"type": "Department"}
            },
            {
                "text": "Harvard Business School",
                "type": "ORGANIZATION",
                "metadata": {"type": "Business School"}
            }
        ],
        "expected_entity_count_min": 3,
        "expected_entity_count_max": 4
    },
    {
        "content_id": "gt_ner_004",
        "text": "The MBA class visited Microsoft headquarters in Seattle...",
        "expected_entities": [
            {
                "text": "MBA",
                "type": "EVENT",  # Programme reference
                "metadata": {"type": "Programme"}
            },
            {
                "text": "Microsoft",
                "type": "ORGANIZATION",
                "metadata": {"type": "Company", "industry": "Technology"}
            },
            {
                "text": "Seattle",
                "type": "LOCATION",
                "metadata": {"type": "city"}
            }
        ],
        "expected_entity_count_min": 3,
        "expected_entity_count_max": 4
    },
    {
        "content_id": "gt_ner_005",
        "text": "Professor Sarah Williams received the Best Teacher Award at the Annual Faculty Dinner...",
        "expected_entities": [
            {
                "text": "Professor Sarah Williams",
                "type": "PERSON",
                "metadata": {"role": "Professor"}
            },
            {
                "text": "Best Teacher Award",
                "type": "EVENT",
                "metadata": {"type": "Award"}
            },
            {
                "text": "Annual Faculty Dinner",
                "type": "EVENT",
                "metadata": {"type": "Event"}
            }
        ],
        "expected_entity_count_min": 3,
        "expected_entity_count_max": 4
    }
]

def validate_ner_extraction(content_id: str, extracted_entities: list) -> dict:
    """Validate extracted entities against ground truth."""
    truth = next((item for item in GROUND_TRUTH_NER if item["content_id"] == content_id), None)
    if not truth:
        return {"valid": False, "error": "Content ID not found in ground truth"}

    entity_count_valid = truth["expected_entity_count_min"] <= len(extracted_entities) <= truth["expected_entity_count_max"]

    # Check for expected entities (by text)
    expected_texts = {e["text"].lower() for e in truth["expected_entities"]}
    extracted_texts = {
        e["text"].lower() if isinstance(e, dict) else
        (e.name.lower() if hasattr(e, 'name') else str(e).lower())
        for e in extracted_entities
    }

    matches = expected_texts.intersection(extracted_texts)
    recall = len(matches) / len(expected_texts) if expected_texts else 0
    precision = len(matches) / len(extracted_texts) if extracted_texts else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "valid": entity_count_valid and recall >= 0.6,  # At least 60% recall
        "entity_count_valid": entity_count_valid,
        "recall": recall,
        "precision": precision,
        "f1_score": f1_score,
        "expected_entities": len(expected_texts),
        "extracted_entities": len(extracted_texts),
        "matches": len(matches)
    }
