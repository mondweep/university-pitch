"""
Persona Classifier using LLM for content targeting.
Classifies content by target personas and calculates relevance scores.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..llm.llm_client import LLMClient
from .persona_models import (
    PersonaTarget,
    PersonaType,
    JourneyStage,
    get_all_personas,
    get_persona_by_name
)


logger = logging.getLogger(__name__)


# Prompt template for persona classification
PERSONA_PROMPT_TEMPLATE = """Classify the target audience(s) for this LBS (London Business School) content.

Return ONLY valid JSON with no other text:
{{
  "personas": [
    {{
      "name": "prospective_students|current_students|alumni|faculty_staff|recruiters|media",
      "relevance": 0.0-1.0,
      "journey_stage": "awareness|consideration|decision|action|retention",
      "intent": "brief description of why this targets this persona"
    }}
  ]
}}

Personas:
- prospective_students: Individuals considering MBA, Masters, or PhD programs
- current_students: Enrolled students seeking resources and support
- alumni: Graduates maintaining connection with LBS
- faculty_staff: LBS employees (faculty, researchers, staff)
- recruiters: Companies and recruiters seeking to hire LBS talent
- media: Journalists, media outlets seeking information

Journey Stages:
- awareness: Discovering LBS and its offerings
- consideration: Evaluating programs/options
- decision: Making choice/commitment
- action: Applying/enrolling/participating
- retention: Staying engaged/connected

Content Type: {page_type}
Title: {title}
Content: "{text}"

Return JSON:"""


class PersonaClassifier:
    """Classify content by target personas using LLM."""

    def __init__(
        self,
        llm_client: LLMClient,
        relevance_threshold: float = 0.6,
        max_personas_per_content: int = 3
    ):
        """
        Initialize persona classifier.

        Args:
            llm_client: LLM client for classification
            relevance_threshold: Minimum relevance score (0-1)
            max_personas_per_content: Max personas to return per content
        """
        self.llm_client = llm_client
        self.relevance_threshold = relevance_threshold
        self.max_personas_per_content = max_personas_per_content
        self.personas = {p.slug.replace('-', '_'): p for p in get_all_personas()}

        logger.info(
            f"Initialized PersonaClassifier with {len(self.personas)} personas, "
            f"threshold={relevance_threshold}"
        )

    async def classify_content(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[PersonaTarget]:
        """
        Classify content by target personas.

        Args:
            text: Content text to classify
            metadata: Optional metadata (page_type, title, etc.)

        Returns:
            List of PersonaTarget objects sorted by relevance
        """
        metadata = metadata or {}

        # Build prompt
        prompt = PERSONA_PROMPT_TEMPLATE.format(
            page_type=metadata.get('page_type', 'unknown'),
            title=metadata.get('title', 'N/A'),
            text=text[:2000]  # Limit text length
        )

        try:
            # Get LLM classification
            response = await self.llm_client.complete(
                prompt=prompt,
                max_tokens=800
            )

            # Parse JSON response
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(response)

            # Convert to PersonaTarget objects
            targets = []
            for persona_data in result.get('personas', []):
                persona_name = persona_data.get('name', '')
                relevance = float(persona_data.get('relevance', 0))

                # Skip low-relevance personas
                if relevance < self.relevance_threshold:
                    continue

                # Get persona definition
                persona = self.personas.get(persona_name)
                if not persona:
                    logger.warning(f"Unknown persona: {persona_name}")
                    continue

                # Parse journey stage
                stage_str = persona_data.get('journey_stage', 'awareness')
                try:
                    journey_stage = JourneyStage[stage_str.upper()]
                except KeyError:
                    logger.warning(f"Invalid journey stage: {stage_str}, using AWARENESS")
                    journey_stage = JourneyStage.AWARENESS

                target = PersonaTarget(
                    persona_id=persona.id,
                    persona_name=persona.name,
                    relevance=relevance,
                    journey_stage=journey_stage,
                    intent=persona_data.get('intent', ''),
                    confidence=1.0,
                    metadata={'source': 'llm', 'model': self.llm_client.model}
                )
                targets.append(target)

            # Sort by relevance and limit
            targets.sort(key=lambda t: t.relevance, reverse=True)
            targets = targets[:self.max_personas_per_content]

            logger.debug(
                f"Classified content: {len(targets)} personas (max_rel={targets[0].relevance if targets else 0:.2f})"
            )

            return targets

        except Exception as e:
            logger.error(f"Error classifying content: {e}")
            return []

    async def classify_batch(
        self,
        items: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> List[List[PersonaTarget]]:
        """
        Classify multiple content items in batches.

        Args:
            items: List of dicts with 'text' and optional 'metadata'
            batch_size: Number of items to process concurrently

        Returns:
            List of persona target lists for each item
        """
        results = []
        total = len(items)

        for i in range(0, total, batch_size):
            batch = items[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}")

            # Process batch concurrently
            tasks = [
                self.classify_content(
                    text=item.get('text', ''),
                    metadata=item.get('metadata', {})
                )
                for item in batch
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        logger.info(f"Classified {total} items, avg personas per item: {sum(len(r) for r in results) / total:.1f}")

        return results

    def get_persona_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get all persona definitions."""
        return {
            slug: {
                'id': persona.id,
                'name': persona.name,
                'type': persona.type.value,
                'description': persona.description,
                'goals': persona.goals,
                'interests': persona.interests,
                'priority': persona.priority
            }
            for slug, persona in self.personas.items()
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get LLM usage statistics."""
        return self.llm_client.get_statistics()
