"""
Response parser for LLM outputs with error handling and validation.

Handles:
- JSON parsing with error recovery
- Schema validation
- Malformed response fixing
- Structured data extraction
"""

import json
import re
from typing import Dict, List, Any, Optional


class ResponseParser:
    """
    Parse and validate LLM responses with robust error handling.
    """

    def __init__(self):
        """Initialize response parser."""
        self.validation_schemas = self._init_schemas()

    def _init_schemas(self) -> Dict:
        """Initialize validation schemas for different response types."""
        return {
            "sentiment": {
                "required_fields": ["id", "sentiment", "confidence"],
                "optional_fields": ["reasoning"],
                "validators": {
                    "sentiment": lambda x: x in ["positive", "neutral", "negative"],
                    "confidence": lambda x: 0.0 <= x <= 1.0
                }
            },
            "topics": {
                "required_fields": ["page_id", "topics"],
                "validators": {
                    "topics": lambda x: isinstance(x, list) and len(x) > 0
                }
            },
            "personas": {
                "required_fields": ["page_id", "personas"],
                "validators": {
                    "personas": lambda x: isinstance(x, list) and len(x) > 0
                }
            },
            "ner": {
                "required_fields": ["page_id", "entities"],
                "validators": {
                    "entities": lambda x: isinstance(x, list)
                }
            },
            "entities": {
                "required_fields": ["page_id", "entities"],
                "validators": {
                    "entities": lambda x: isinstance(x, list)
                }
            },
            "journey": {
                "required_fields": ["page_id", "stages"],
                "validators": {
                    "stages": lambda x: isinstance(x, list) and len(x) > 0
                }
            },
            "journey_stages": {
                "required_fields": ["page_id", "stages"],
                "validators": {
                    "stages": lambda x: isinstance(x, list) and len(x) > 0
                }
            },
            "similarity": {
                "required_fields": ["similarity_score", "relationship_type"],
                "optional_fields": ["shared_topics", "shared_entities", "reasoning"],
                "validators": {
                    "similarity_score": lambda x: 0.0 <= x <= 1.0,
                    "relationship_type": lambda x: x in [
                        "duplicate", "complementary", "related", "unrelated"
                    ]
                }
            }
        }

    def parse_json_response(self, response_text: str) -> Any:
        """
        Parse JSON response with error recovery.

        Args:
            response_text: Raw LLM response

        Returns:
            Parsed JSON object/array

        Raises:
            ValueError: If JSON cannot be parsed
        """
        # Try direct JSON parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON array or object in text
        # Look for [...] or {...}
        array_match = re.search(r'\[\s*\{.*?\}\s*\]', response_text, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except json.JSONDecodeError:
                pass

        object_match = re.search(r'\{\s*".*?\s*\}', response_text, re.DOTALL)
        if object_match:
            try:
                return json.loads(object_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try to fix common JSON issues
        fixed_text = self._fix_json_errors(response_text)
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse JSON response: {str(e)}\nResponse: {response_text[:200]}...")

    def _fix_json_errors(self, text: str) -> str:
        """
        Attempt to fix common JSON formatting errors.

        Args:
            text: Malformed JSON text

        Returns:
            Fixed JSON text
        """
        # Remove any text before first { or [
        text = re.sub(r'^[^{\[]*', '', text)

        # Remove any text after last } or ]
        text = re.sub(r'[^}\]]*$', '', text)

        # Fix single quotes to double quotes
        text = text.replace("'", '"')

        # Fix trailing commas
        text = re.sub(r',\s*([}\]])', r'\1', text)

        # Fix missing commas between objects
        text = re.sub(r'}\s*{', '},{', text)

        return text

    def validate_response(
        self,
        data: Dict,
        response_type: str
    ) -> Dict:
        """
        Validate response against schema.

        Args:
            data: Parsed response data
            response_type: Type of response (sentiment, topics, etc.)

        Returns:
            Validated data

        Raises:
            ValueError: If validation fails
        """
        if response_type not in self.validation_schemas:
            raise ValueError(f"Unknown response type: {response_type}")

        schema = self.validation_schemas[response_type]

        # Check required fields
        for field in schema["required_fields"]:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Run field validators
        if "validators" in schema:
            for field, validator in schema["validators"].items():
                if field in data:
                    if not validator(data[field]):
                        raise ValueError(f"Validation failed for field: {field}")

        return data

    def validate_batch_response(
        self,
        data: List[Dict],
        response_type: str,
        expected_count: Optional[int] = None
    ) -> List[Dict]:
        """
        Validate batch response.

        Args:
            data: List of response items
            response_type: Type of response
            expected_count: Expected number of items (optional)

        Returns:
            List of validated items
        """
        if not isinstance(data, list):
            raise ValueError("Batch response must be a list")

        if expected_count is not None and len(data) != expected_count:
            print(f"Warning: Expected {expected_count} items, got {len(data)}")

        # Validate each item
        validated = []
        for i, item in enumerate(data):
            try:
                validated_item = self.validate_response(item, response_type)
                validated.append(validated_item)
            except ValueError as e:
                print(f"Validation error for item {i}: {str(e)}")
                # Add error marker to item
                validated.append({
                    **item,
                    "validation_error": str(e)
                })

        return validated

    def extract_structured_data(
        self,
        response_text: str,
        response_type: str
    ) -> Any:
        """
        Parse and validate response in one step.

        Args:
            response_text: Raw LLM response
            response_type: Expected response type

        Returns:
            Validated structured data
        """
        # Parse JSON
        parsed = self.parse_json_response(response_text)

        # Validate
        if isinstance(parsed, list):
            return self.validate_batch_response(parsed, response_type)
        else:
            return self.validate_response(parsed, response_type)

    def safe_extract(
        self,
        response_text: str,
        response_type: str,
        default: Any = None
    ) -> Any:
        """
        Extract structured data with fallback to default.

        Args:
            response_text: Raw LLM response
            response_type: Expected response type
            default: Default value if extraction fails

        Returns:
            Validated data or default value
        """
        try:
            return self.extract_structured_data(response_text, response_type)
        except Exception as e:
            print(f"Error extracting structured data: {str(e)}")
            return default

    def format_error_report(self, errors: List[Dict]) -> str:
        """
        Format error report for failed items.

        Args:
            errors: List of error dictionaries

        Returns:
            Formatted error report
        """
        if not errors:
            return "No errors"

        report = f"Found {len(errors)} errors:\n\n"

        for i, error in enumerate(errors, 1):
            item_id = error.get("id", error.get("page_id", "unknown"))
            error_msg = error.get("error", error.get("validation_error", "unknown error"))
            report += f"{i}. Item {item_id}: {error_msg}\n"

        return report
