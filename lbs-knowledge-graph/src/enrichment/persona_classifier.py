"""
Persona Classification for Content Targeting

Classifies content by target persona (prospective students, alumni, etc.)
and creates TARGETS relationships with relevance scores.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from src.graph.mgraph_wrapper import MGraph
from .llm_client import LLMClient
from .persona_models import (
    PersonaType, PersonaTarget, JourneyStage,
    get_all_personas, get_persona_by_name
)


# Persona classification prompt template
PERSONA_CLASSIFICATION_PROMPT = """Classify this content by target audience personas. Content may target multiple personas.

Content Title: {title}
Content Text: {text}

Personas:
1. Prospective Students (25-35, career switchers, considering MBA/Masters/PhD)
2. Current Students (enrolled students, accessing resources, building networks)
3. Alumni (graduates, staying connected, mentoring, continuing education)
4. Faculty & Staff (internal audience, research, teaching, administration)
5. Recruiters & Employers (corporate partners, hiring LBS talent)
6. Media & Press (journalists, media outlets, press seeking information)

Journey Stages:
- awareness: Discovering LBS
- consideration: Evaluating programs
- decision: Making choice
- action: Applying/enrolling/engaging
- retention: Staying engaged

Return JSON array with personas that this content targets (include only if relevance ≥0.6):
[
  {
    "persona": "Prospective Students",
    "relevance": 0.90,
    "is_primary": true,
    "journey_stage": "consideration",
    "signals": ["MBA programme", "career switch", "application process"],
    "intent": "Inform prospective students about MBA options"
  },
  {
    "persona": "Alumni",
    "relevance": 0.65,
    "is_primary": false,
    "journey_stage": "retention",
    "signals": ["networking events", "continued learning"],
    "intent": "Engage alumni with networking opportunities"
  }
]

Only include personas with relevance ≥0.6.
Identify is_primary=true for the main target persona (highest relevance).
"""


@dataclass
class PersonaClassification:
    """Result of persona classification for a content item."""
    content_id: str
    content_type: str  # 'page' or 'section'
    personas: List[Dict[str, Any]]
    primary_persona: Optional[str] = None
    multi_target: bool = False
    extracted_by: str = "gpt-4o-mini"
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'content_id': self.content_id,
            'content_type': self.content_type,
            'personas': self.personas,
            'primary_persona': self.primary_persona,
            'multi_target': self.multi_target,
            'extracted_by': self.extracted_by,
            'confidence': self.confidence
        }


class PersonaClassifier:
    """
    Classifier for target persona identification.

    Uses LLM to classify content by target personas with:
    - Multi-label classification (1-3 personas per content)
    - Relevance scores (0-1)
    - Primary persona identification
    - Journey stage mapping
    """

    def __init__(
        self,
        llm_client: LLMClient,
        graph: MGraph,
        min_relevance: float = 0.6,
        batch_size: int = 50
    ):
        """
        Initialize persona classifier.

        Args:
            llm_client: LLM client for classification
            graph: Memgraph connection
            min_relevance: Minimum relevance score to include (default 0.6)
            batch_size: Number of items to process per batch
        """
        self.llm_client = llm_client
        self.graph = graph
        self.min_relevance = min_relevance
        self.batch_size = batch_size

        self.classifications = []
        self.total_processed = 0
        self.multi_target_count = 0

    async def classify_content(
        self,
        content_type: str = "both"
    ) -> List[PersonaClassification]:
        """
        Classify all content by target personas.

        Args:
            content_type: Type to classify ('page', 'section', or 'both')

        Returns:
            List of PersonaClassification objects
        """
        self.classifications = []

        # Load content from graph
        if content_type in ["page", "both"]:
            pages = self._load_pages()
            print(f"📄 Classifying {len(pages)} pages by persona...")
            page_results = await self._classify_batch(pages, "page")
            self.classifications.extend(page_results)

        if content_type in ["section", "both"]:
            sections = self._load_sections()
            print(f"📋 Classifying {len(sections)} sections by persona...")
            section_results = await self._classify_batch(sections, "section")
            self.classifications.extend(section_results)

        # Calculate statistics
        self.total_processed = len(self.classifications)
        self.multi_target_count = sum(1 for c in self.classifications if c.multi_target)

        print(f"\n✅ Classified {self.total_processed} items")
        print(f"   Multi-target: {self.multi_target_count} ({self.multi_target_count/self.total_processed*100:.1f}%)")

        return self.classifications

    def _load_pages(self) -> List[Dict[str, Any]]:
        """Load pages from graph."""
        query = """
        MATCH (p:Page)
        WHERE p.title IS NOT NULL AND p.text IS NOT NULL
        RETURN
            p.id AS id,
            p.title AS title,
            p.text AS text,
            p.url AS url,
            p.type AS type
        LIMIT 1000
        """

        results = self.graph.execute_and_fetch(query)
        pages = [dict(row) for row in results]
        return pages

    def _load_sections(self) -> List[Dict[str, Any]]:
        """Load sections from graph."""
        query = """
        MATCH (s:Section)
        WHERE s.heading IS NOT NULL AND s.text IS NOT NULL
        RETURN
            s.id AS id,
            s.heading AS title,
            s.text AS text,
            s.type AS type,
            s.pageId AS page_id
        LIMIT 1000
        """

        results = self.graph.execute_and_fetch(query)
        sections = [dict(row) for row in results]
        return sections

    async def _classify_batch(
        self,
        items: List[Dict[str, Any]],
        content_type: str
    ) -> List[PersonaClassification]:
        """Classify a batch of content items."""
        results = []

        # Process in parallel batches
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = await asyncio.gather(
                *[self._classify_item(item, content_type) for item in batch],
                return_exceptions=True
            )

            # Handle results and exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"⚠️  Classification error: {result}")
                    continue
                if result:
                    results.append(result)

            print(f"   Processed {min(i + self.batch_size, len(items))}/{len(items)}", end="\r")

        return results

    async def _classify_item(
        self,
        item: Dict[str, Any],
        content_type: str
    ) -> Optional[PersonaClassification]:
        """Classify a single content item."""
        try:
            title = item.get("title", "")
            text = item.get("text", "")

            # Truncate text for efficiency (max 800 chars)
            text_sample = text[:800] if len(text) > 800 else text

            # Build prompt
            prompt = PERSONA_CLASSIFICATION_PROMPT.format(
                title=title.replace('"', '\\"'),
                text=text_sample.replace('"', '\\"')
            )

            # Call LLM
            response = await self.llm_client.client.chat.completions.create(
                model=self.llm_client.model,
                messages=[
                    {"role": "system", "content": "You are a persona classification expert. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=400,
                response_format={"type": "json_object"}
            )

            # Track usage
            self.llm_client.api_calls += 1
            usage = response.usage
            self.llm_client.total_tokens += usage.total_tokens

            # Calculate cost
            if self.llm_client.model in self.llm_client.pricing:
                input_cost = (usage.prompt_tokens / 1_000_000) * self.llm_client.pricing[self.llm_client.model]["input"]
                output_cost = (usage.completion_tokens / 1_000_000) * self.llm_client.pricing[self.llm_client.model]["output"]
                self.llm_client.total_cost += input_cost + output_cost

            # Parse response
            content = response.choices[0].message.content

            # Handle both array and object responses
            data = json.loads(content)
            if isinstance(data, dict) and "personas" in data:
                personas_data = data["personas"]
            elif isinstance(data, list):
                personas_data = data
            else:
                personas_data = [data]

            # Parse personas
            parsed_personas = self.parse_persona_results(personas_data)

            # Filter by relevance
            filtered = [p for p in parsed_personas if p.get("relevance", 0) >= self.min_relevance]

            if not filtered:
                return None

            # Identify primary persona
            primary = self.identify_primary_persona(filtered)

            # Calculate average confidence
            avg_confidence = sum(p.get("confidence", 1.0) for p in filtered) / len(filtered)

            return PersonaClassification(
                content_id=item["id"],
                content_type=content_type,
                personas=filtered,
                primary_persona=primary,
                multi_target=len(filtered) > 1,
                extracted_by=self.llm_client.model,
                confidence=avg_confidence
            )

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error for {item.get('id', 'unknown')}: {e}")
            return None
        except Exception as e:
            print(f"⚠️  Classification error for {item.get('id', 'unknown')}: {e}")
            return None

    def parse_persona_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """
        Parse LLM results into persona classifications.

        Args:
            results: Raw LLM response data

        Returns:
            List of parsed persona dictionaries
        """
        parsed = []

        for result in results:
            # Get persona object
            persona_name = result.get("persona", "")
            persona = get_persona_by_name(persona_name)

            if not persona:
                continue

            # Parse journey stage
            journey_stage_str = result.get("journey_stage", "awareness")
            try:
                journey_stage = JourneyStage(journey_stage_str.lower())
            except ValueError:
                journey_stage = JourneyStage.AWARENESS

            parsed.append({
                "persona_id": persona.id,
                "persona_name": persona.name,
                "persona_type": persona.type.value,
                "relevance": float(result.get("relevance", 0.7)),
                "is_primary": result.get("is_primary", False),
                "journey_stage": journey_stage.value,
                "signals": result.get("signals", []),
                "intent": result.get("intent", ""),
                "confidence": 0.9  # High confidence from structured LLM output
            })

        return parsed

    def identify_primary_persona(self, personas: List[Dict[str, Any]]) -> str:
        """
        Identify primary target persona.

        Args:
            personas: List of persona classifications

        Returns:
            Primary persona ID
        """
        if not personas:
            return None

        # Check if any marked as primary
        for persona in personas:
            if persona.get("is_primary"):
                return persona["persona_id"]

        # Otherwise, return highest relevance
        primary = max(personas, key=lambda p: p.get("relevance", 0))
        primary["is_primary"] = True
        return primary["persona_id"]

    def get_statistics(self) -> Dict[str, Any]:
        """Get classification statistics."""
        if not self.classifications:
            return {}

        # Count by persona
        persona_counts = {}
        for classification in self.classifications:
            for persona in classification.personas:
                persona_name = persona["persona_name"]
                persona_counts[persona_name] = persona_counts.get(persona_name, 0) + 1

        # Count primary personas
        primary_counts = {}
        for classification in self.classifications:
            if classification.primary_persona:
                primary_counts[classification.primary_persona] = primary_counts.get(classification.primary_persona, 0) + 1

        # Calculate averages
        avg_personas_per_content = sum(len(c.personas) for c in self.classifications) / len(self.classifications)
        avg_relevance = sum(
            p["relevance"] for c in self.classifications for p in c.personas
        ) / sum(len(c.personas) for c in self.classifications)

        return {
            "total_classified": self.total_processed,
            "multi_target_count": self.multi_target_count,
            "multi_target_rate": self.multi_target_count / self.total_processed if self.total_processed > 0 else 0,
            "avg_personas_per_content": round(avg_personas_per_content, 2),
            "avg_relevance": round(avg_relevance, 2),
            "persona_distribution": persona_counts,
            "primary_persona_distribution": primary_counts,
            "llm_stats": self.llm_client.get_stats()
        }
