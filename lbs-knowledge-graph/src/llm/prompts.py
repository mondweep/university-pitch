"""
Prompt templates for knowledge graph enrichment tasks.

All prompts are designed for batch processing with structured JSON output.
"""

# Sentiment Analysis - Batch format with numeric scores (0-1 scale)
SENTIMENT_BATCH_PROMPT = """
Analyze the sentiment of the following content items from London Business School's website.
Score each item on a scale from 0 to 1, where:
- 0.0-0.3 = Negative (challenges, problems, barriers, concerns)
- 0.4-0.6 = Neutral (informational, factual, educational content)
- 0.7-1.0 = Positive (opportunities, benefits, success, achievements)

Items to analyze:
{items_json}

For each item, analyze the overall tone and sentiment, considering:
- Word choice and emotional language
- Context and subject matter (educational content is typically neutral)
- Value proposition (marketing content is typically positive)
- Target audience perspective

Return JSON array in this exact format:
[
  {{
    "id": "content_item_id",
    "sentiment": 0.0-1.0,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
  }}
]

Scoring guidelines:
- Educational/informational content: 0.5-0.6 (neutral)
- Marketing/promotional content: 0.7-0.9 (positive)
- Requirements/challenges: 0.3-0.4 (slightly negative)
- Success stories/outcomes: 0.8-1.0 (very positive)
- Navigation/links: 0.5 (neutral)

Confidence guidelines:
- 0.8-1.0: Clear sentiment, strong indicators
- 0.6-0.8: Moderate sentiment, some indicators
- 0.4-0.6: Mixed or unclear sentiment
- <0.4: Insufficient information

Return ONLY the JSON array, no additional text.
"""

# Topic Extraction - Batch format
TOPIC_BATCH_PROMPT = """
Extract 5-10 relevant topics from each content page. Topics should be specific, actionable themes that categorize the content.

Pages to analyze:
{items_json}

For each page, identify:
- Main subject areas (e.g., "admissions", "research", "campus life")
- Specific programs or departments mentioned
- Key themes or concepts
- Target audience indicators

Return JSON array in this exact format:
[
  {{
    "page_id": "page_identifier",
    "topics": [
      {{
        "name": "topic_name",
        "confidence": 0.0-1.0,
        "category": "academic|administrative|student_life|research|other"
      }}
    ]
  }}
]

Topic naming guidelines:
- Use lowercase, underscore-separated (e.g., "undergraduate_admissions")
- Be specific (prefer "masters_computer_science" over "graduate_programs")
- Limit to 2-3 words per topic
- Confidence >0.7 for explicitly mentioned topics, 0.5-0.7 for implied

Return ONLY the JSON array, no additional text.
"""

# Persona Classification - Batch format
PERSONA_BATCH_PROMPT = """
Classify each content page by its target audience persona(s). Multiple personas may apply to a single page.

Target personas:
1. Prospective Undergraduate Student - High school students exploring college options
2. Prospective Graduate Student - Those considering advanced degrees
3. Current Student - Enrolled students seeking resources/information
4. Alumni - Graduates maintaining connection with institution
5. Faculty/Staff - Current employees and job seekers
6. Parents/Families - Family members of prospective or current students

Pages to classify:
{items_json}

For each page, determine:
- Primary persona(s) based on content, language, and calls-to-action
- Confidence level for each persona assignment

Return JSON array in this exact format:
[
  {{
    "page_id": "page_identifier",
    "personas": [
      {{
        "persona": "prospective_undergrad|prospective_grad|current_student|alumni|faculty_staff|parent_family",
        "confidence": 0.0-1.0,
        "indicators": ["brief", "list", "of", "reasons"]
      }}
    ]
  }}
]

Classification guidelines:
- A page may have multiple personas (e.g., admissions page for both undergrad and grad)
- confidence >0.8 for pages clearly targeted at persona
- confidence 0.5-0.8 for secondary audiences
- Include at least 2-3 indicators per persona

Return ONLY the JSON array, no additional text.
"""

# Named Entity Recognition - Batch format
NER_BATCH_PROMPT = """
Extract named entities from each content page. Focus on entities relevant to university context.

Entity types to extract:
- PERSON: Names of people (faculty, students, administrators)
- ORGANIZATION: Departments, schools, research centers, external organizations
- LOCATION: Campus buildings, cities, countries
- PROGRAM: Degree programs, majors, specializations
- EVENT: Conferences, lectures, campus events

Pages to analyze:
{items_json}

For each page, extract all relevant entities with context.

Return JSON array in this exact format:
[
  {{
    "page_id": "page_identifier",
    "entities": [
      {{
        "text": "exact_entity_text",
        "type": "PERSON|ORGANIZATION|LOCATION|PROGRAM|EVENT",
        "context": "brief surrounding context",
        "confidence": 0.0-1.0
      }}
    ]
  }}
]

Extraction guidelines:
- Include full names/titles (e.g., "Department of Computer Science" not "CS")
- confidence >0.9 for clearly identified entities
- confidence 0.7-0.9 for probable entities
- Deduplicate identical entities within a page

Return ONLY the JSON array, no additional text.
"""

# Journey Stage Classification - Batch format
JOURNEY_BATCH_PROMPT = """
Classify each content page by where it fits in the student journey stages.

Journey stages:
1. Awareness - Discovering the university, exploring options
2. Consideration - Comparing programs, researching fit
3. Decision - Making enrollment/application decision
4. Application - Actively applying or enrolling
5. Enrollment - Newly enrolled, onboarding
6. Retention - Current student experience and success
7. Completion - Graduation, alumni transition

Pages to classify:
{items_json}

For each page, determine:
- Primary journey stage(s) the content supports
- Confidence level for each stage
- Key indicators

Return JSON array in this exact format:
[
  {{
    "page_id": "page_identifier",
    "stages": [
      {{
        "stage": "awareness|consideration|decision|application|enrollment|retention|completion",
        "confidence": 0.0-1.0,
        "indicators": ["key", "supporting", "evidence"]
      }}
    ]
  }}
]

Classification guidelines:
- A page may serve multiple stages
- confidence >0.8 for primary stage
- confidence 0.5-0.8 for secondary stages
- Consider calls-to-action, content depth, and prerequisites

Return ONLY the JSON array, no additional text.
"""

# Similarity prompt for comparing content
SIMILARITY_PROMPT = """
Calculate semantic similarity between the following two content items:

Item 1:
{item1_json}

Item 2:
{item2_json}

Consider:
- Topical overlap
- Shared entities or concepts
- Target audience similarity
- Content structure and purpose

Return JSON in this exact format:
{{
  "similarity_score": 0.0-1.0,
  "shared_topics": ["list", "of", "topics"],
  "shared_entities": ["list", "of", "entities"],
  "relationship_type": "duplicate|complementary|related|unrelated",
  "reasoning": "brief explanation"
}}

Scoring guidelines:
- >0.9: Near duplicates or very similar content
- 0.7-0.9: Closely related, significant overlap
- 0.5-0.7: Moderately related, some overlap
- 0.3-0.5: Loosely related, minimal overlap
- <0.3: Unrelated content

Return ONLY the JSON object, no additional text.
"""


def format_batch_prompt(template: str, items: list, max_items: int = 50) -> str:
    """
    Format batch prompt with items.

    Args:
        template: Prompt template with {items_json} placeholder
        items: List of items to process
        max_items: Maximum items per batch

    Returns:
        Formatted prompt string
    """
    import json

    # Limit batch size
    batch = items[:max_items]

    # Convert items to JSON string
    items_json = json.dumps(batch, indent=2, ensure_ascii=False)

    return template.format(items_json=items_json)


def format_single_item_prompt(template: str, item: dict) -> str:
    """
    Format prompt for single item.

    Args:
        template: Prompt template with placeholders
        item: Item data dictionary

    Returns:
        Formatted prompt string
    """
    import json

    # Handle different placeholder patterns
    if "{item_json}" in template:
        item_json = json.dumps(item, indent=2, ensure_ascii=False)
        return template.format(item_json=item_json)
    elif "{item1_json}" in template and "{item2_json}" in template:
        # For similarity comparisons
        return template  # Caller should format both items
    else:
        return template.format(**item)
