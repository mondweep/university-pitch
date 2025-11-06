"""
LLM Client for Named Entity Recognition and Content Analysis
Uses OpenAI's GPT models for entity extraction and semantic analysis.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with LLM for NER and semantic analysis."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 2000
    ):
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4o-mini for cost-effectiveness)
            temperature: Sampling temperature (0 = deterministic)
            max_tokens: Maximum response tokens
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        logger.info(f"Initialized LLMClient with model: {model}")

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True
    ) -> str:
        """
        Generate completion from prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            json_mode: Whether to use JSON response format

        Returns:
            Completion text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"} if json_mode else {"type": "text"}
            )

            content = response.choices[0].message.content
            logger.debug(f"LLM completion: {len(content)} chars")
            return content

        except Exception as e:
            logger.error(f"Error in LLM completion: {e}")
            raise

    async def extract_entities(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extract named entities from text.

        Args:
            text: Text to analyze
            context: Optional context (page title, URL, etc.)

        Returns:
            Dictionary with entities list
        """
        system_prompt = """You are an expert at Named Entity Recognition for London Business School (LBS) content.
Extract named entities with high precision. Focus on:
- PERSON: Faculty names, professors, researchers, students, alumni
- ORGANIZATION: Companies, institutions, research centers, departments
- LOCATION: Cities, countries, campuses, buildings
- PROGRAMME: Degree programs (MBA, EMBA, Masters, PhD, Executive Education)
- EVENT: Conferences, seminars, workshops, webinars
- DEGREE: Specific degrees and qualifications

Return JSON with entities array. Include confidence scores (0-1) and context."""

        context_str = ""
        if context:
            context_str = f"\n\nContext:\n"
            if "page_title" in context:
                context_str += f"- Page: {context['page_title']}\n"
            if "page_type" in context:
                context_str += f"- Type: {context['page_type']}\n"

        prompt = f"""Extract named entities from the following text. Return JSON:
{{
  "entities": [
    {{
      "name": "entity name",
      "type": "PERSON|ORGANIZATION|LOCATION|PROGRAMME|EVENT|DEGREE",
      "confidence": 0.0-1.0,
      "context": "surrounding text (max 100 chars)"
    }}
  ]
}}

Domain: London Business School (LBS) - focus on faculty, programmes, locations, events.
{context_str}
Text: "{text[:2000]}"

JSON:"""

        try:
            response = await self.complete(prompt, system_prompt, json_mode=True)
            data = json.loads(response)
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"entities": []}
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {"entities": []}

    async def extract_entities_batch(
        self,
        items: List[Dict],
        batch_size: int = 50,
        delay: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Extract entities from multiple texts in batches.

        Args:
            items: List of dicts with 'text' and optional 'context'
            batch_size: Number of items per batch
            delay: Delay between batches (seconds)

        Returns:
            List of entity extraction results
        """
        results = []
        total_batches = (len(items) + batch_size - 1) // batch_size

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_num = i // batch_size + 1

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")

            # Process batch concurrently
            tasks = [
                self.extract_entities(
                    item.get("text", ""),
                    item.get("context")
                )
                for item in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error in item {i + idx}: {result}")
                    results.append({"entities": []}]
                else:
                    results.append(result)

            # Rate limiting delay
            if i + batch_size < len(items):
                await asyncio.sleep(delay)

        logger.info(f"Completed batch entity extraction: {len(results)} items")
        return results

    async def classify_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Classify sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis result
        """
        system_prompt = """You are an expert at sentiment analysis for educational content.
Analyze the sentiment and return JSON with polarity, confidence, and label."""

        prompt = f"""Analyze the sentiment of this text. Return JSON:
{{
  "polarity": -1.0 to 1.0,
  "confidence": 0.0 to 1.0,
  "label": "positive|neutral|negative",
  "magnitude": 0.0 to 1.0
}}

Text: "{text[:1000]}"

JSON:"""

        try:
            response = await self.complete(prompt, system_prompt, json_mode=True)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {
                "polarity": 0.0,
                "confidence": 0.0,
                "label": "neutral",
                "magnitude": 0.0
            }

    async def extract_topics(
        self,
        text: str,
        max_topics: int = 5
    ) -> List[str]:
        """
        Extract main topics from text.

        Args:
            text: Text to analyze
            max_topics: Maximum number of topics

        Returns:
            List of topic strings
        """
        system_prompt = """You are an expert at topic extraction for business school content.
Identify main topics and themes. Return JSON array."""

        prompt = f"""Extract the main topics from this text (max {max_topics}). Return JSON:
{{
  "topics": ["topic1", "topic2", ...]
}}

Text: "{text[:1500]}"

JSON:"""

        try:
            response = await self.complete(prompt, system_prompt, json_mode=True)
            data = json.loads(response)
            return data.get("topics", [])
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []

    async def close(self):
        """Close the OpenAI client."""
        await self.client.close()
