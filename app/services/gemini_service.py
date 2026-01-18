"""
Google Gemini API service for Grounding Search and structured responses
"""
from typing import Type, TypeVar
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError
from app.config import get_settings
from app.logger import logger

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)


class GeminiService:
    """Service for Google Gemini API interactions"""

    def __init__(self):
        """Initialize Gemini client"""
        self.settings = get_settings()
        self.client = genai.Client(api_key=self.settings.google_api_key)
        self.model_name = self.settings.gemini_model
        logger.info(f"GeminiService initialized with model: {self.model_name}")

    def grounding_search(self, prompt: str) -> str:
        """
        Perform Grounding Search using Google Search

        Args:
            prompt: Search prompt

        Returns:
            str: Raw response text from Gemini

        Raises:
            Exception: If API call fails
        """
        logger.info(f"[Grounding Search] Prompt length: {len(prompt)} chars")
        logger.debug(f"[Grounding Search] Prompt: {prompt[:200]}...")

        try:
            # Configure Grounding Tool
            grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )

            # Configure request
            config = types.GenerateContentConfig(
                tools=[grounding_tool]
            )

            # Call API
            logger.info(f"[Grounding Search] Calling Gemini API: {self.model_name}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

            # Extract response text
            result_text = response.text
            logger.info(f"[Grounding Search] Response length: {len(result_text)} chars")
            logger.debug(f"[Grounding Search] Response: {result_text[:200]}...")

            return result_text

        except Exception as e:
            logger.error(f"[Grounding Search] Error: {type(e).__name__}: {str(e)}")
            raise

    def structured_response(self, prompt: str, schema: Type[T]) -> T:
        """
        Get structured JSON response using Pydantic schema

        Args:
            prompt: Prompt for Gemini
            schema: Pydantic model class for response validation

        Returns:
            Validated Pydantic model instance

        Raises:
            ValidationError: If response doesn't match schema
            Exception: If API call fails
        """
        schema_name = schema.__name__
        logger.info(f"[Structured Response] Schema: {schema_name}")
        logger.debug(f"[Structured Response] Prompt: {prompt[:200]}...")

        response = None
        response_text = None

        try:
            # Configure JSON response
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema.model_json_schema(),
            )

            # Call API
            logger.info(f"[Structured Response] Calling Gemini API: {self.model_name}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

            # Parse and validate with Pydantic
            response_text = response.text
            logger.debug(f"[Structured Response] Raw JSON: {response_text[:200]}...")

            result = schema.model_validate_json(response_text)
            logger.info(f"[Structured Response] Successfully parsed as {schema_name}")

            return result

        except ValidationError as e:
            logger.error(f"[Structured Response] Validation error: {e}")
            if response_text:
                logger.error(f"[Structured Response] Raw response: {response_text}")
            raise

        except Exception as e:
            logger.error(f"[Structured Response] Error: {type(e).__name__}: {str(e)}")
            if response_text:
                logger.error(f"[Structured Response] Raw response: {response_text}")
            raise
