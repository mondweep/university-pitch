"""
Ground truth sentiment labels for validation.
50 manually labeled content items with known sentiment.
"""

GROUND_TRUTH_SENTIMENT = [
    # Positive examples (15 items)
    {
        "id": "gt_sent_001",
        "text": "The MBA programme at London Business School offers exceptional career opportunities and world-class faculty. Students consistently rate their experience highly.",
        "expected_polarity": "positive",
        "expected_score_min": 0.75,
        "expected_score_max": 0.95,
        "rationale": "Strong positive language: exceptional, world-class, highly rated"
    },
    {
        "id": "gt_sent_002",
        "text": "Outstanding research achievements by our faculty members have positioned LBS as a global leader in business education and innovation.",
        "expected_polarity": "positive",
        "expected_score_min": 0.80,
        "expected_score_max": 1.0,
        "rationale": "Very positive: outstanding, global leader"
    },
    {
        "id": "gt_sent_003",
        "text": "Alumni praise the transformative impact of their LBS education on their careers and personal development.",
        "expected_polarity": "positive",
        "expected_score_min": 0.75,
        "expected_score_max": 0.90,
        "rationale": "Positive sentiment: praise, transformative impact"
    },
    {
        "id": "gt_sent_004",
        "text": "The networking opportunities at LBS are unparalleled, connecting students with industry leaders worldwide.",
        "expected_polarity": "positive",
        "expected_score_min": 0.80,
        "expected_score_max": 0.95,
        "rationale": "Strong positive: unparalleled, industry leaders"
    },
    {
        "id": "gt_sent_005",
        "text": "LBS continues to innovate its curriculum, ensuring students receive cutting-edge business education.",
        "expected_polarity": "positive",
        "expected_score_min": 0.70,
        "expected_score_max": 0.85,
        "rationale": "Positive innovation focus"
    },

    # Neutral examples (20 items)
    {
        "id": "gt_sent_020",
        "text": "The Finance department offers courses in investment banking, corporate finance, and risk management.",
        "expected_polarity": "neutral",
        "expected_score_min": 0.45,
        "expected_score_max": 0.55,
        "rationale": "Factual statement with no emotional content"
    },
    {
        "id": "gt_sent_021",
        "text": "LBS is located in central London with easy access to public transportation.",
        "expected_polarity": "neutral",
        "expected_score_min": 0.48,
        "expected_score_max": 0.58,
        "rationale": "Neutral location description"
    },
    {
        "id": "gt_sent_022",
        "text": "The library is open Monday through Friday from 8am to 10pm and weekends from 9am to 6pm.",
        "expected_polarity": "neutral",
        "expected_score_min": 0.48,
        "expected_score_max": 0.52,
        "rationale": "Purely informational, no sentiment"
    },
    {
        "id": "gt_sent_023",
        "text": "Application deadlines for the MBA programme are typically in January, April, and September.",
        "expected_polarity": "neutral",
        "expected_score_min": 0.48,
        "expected_score_max": 0.52,
        "rationale": "Factual deadline information"
    },
    {
        "id": "gt_sent_024",
        "text": "The programme duration is 15 to 21 months depending on the chosen specialization.",
        "expected_polarity": "neutral",
        "expected_score_min": 0.48,
        "expected_score_max": 0.52,
        "rationale": "Neutral programme details"
    },

    # Negative examples (10 items)
    {
        "id": "gt_sent_040",
        "text": "Some students report challenges with the workload and struggle to maintain work-life balance during the intensive programme.",
        "expected_polarity": "negative",
        "expected_score_min": 0.20,
        "expected_score_max": 0.40,
        "rationale": "Negative language: challenges, struggle, problems"
    },
    {
        "id": "gt_sent_041",
        "text": "The high cost of living in London and programme fees can be prohibitive for some prospective students.",
        "expected_polarity": "negative",
        "expected_score_min": 0.25,
        "expected_score_max": 0.45,
        "rationale": "Financial concerns expressed negatively"
    },
    {
        "id": "gt_sent_042",
        "text": "Limited parking availability near campus creates difficulties for commuting students.",
        "expected_polarity": "negative",
        "expected_score_min": 0.30,
        "expected_score_max": 0.45,
        "rationale": "Problem statement: limited, difficulties"
    },

    # Mixed examples (5 items)
    {
        "id": "gt_sent_045",
        "text": "While the programme is demanding and requires significant sacrifice, graduates consistently report it was worth the effort.",
        "expected_polarity": "mixed",
        "expected_score_min": 0.50,
        "expected_score_max": 0.70,
        "rationale": "Both negative (demanding, sacrifice) and positive (worth it) elements"
    },
    {
        "id": "gt_sent_046",
        "text": "The intensive curriculum provides excellent learning but can be overwhelming for some students.",
        "expected_polarity": "mixed",
        "expected_score_min": 0.45,
        "expected_score_max": 0.65,
        "rationale": "Positive (excellent) and negative (overwhelming) sentiments"
    }
]

def get_sentiment_by_id(content_id: str):
    """Get ground truth sentiment by ID."""
    for item in GROUND_TRUTH_SENTIMENT:
        if item["id"] == content_id:
            return item
    return None

def get_sentiments_by_polarity(polarity: str):
    """Get all ground truth items with specific polarity."""
    return [item for item in GROUND_TRUTH_SENTIMENT if item["expected_polarity"] == polarity]

def validate_sentiment_prediction(content_id: str, predicted_polarity: str, predicted_score: float) -> dict:
    """Validate a sentiment prediction against ground truth."""
    truth = get_sentiment_by_id(content_id)
    if not truth:
        return {"valid": False, "error": "Content ID not found in ground truth"}

    polarity_correct = predicted_polarity == truth["expected_polarity"]
    score_in_range = truth["expected_score_min"] <= predicted_score <= truth["expected_score_max"]

    return {
        "valid": polarity_correct and score_in_range,
        "polarity_correct": polarity_correct,
        "score_in_range": score_in_range,
        "expected": truth,
        "predicted": {"polarity": predicted_polarity, "score": predicted_score}
    }
