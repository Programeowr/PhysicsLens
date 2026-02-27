"""
Physics problem parser using Google Gemini AI.

Handles the AI API call with retry logic and validates the
parsed output against Pydantic models. Supports both text
and image-based (OCR) problem parsing.
"""

import base64
import json
import logging

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.models import ParsedPhysicsProblem
from app.prompts import build_prompt, build_image_prompt

logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=settings.gemini_api_key)


class ParsingError(Exception):
    """Raised when the AI output cannot be parsed or validated."""

    def __init__(self, message: str, raw_output: str | None = None):
        super().__init__(message)
        self.raw_output = raw_output


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True,
)
def _call_gemini(prompt: str) -> str:
    """Call Gemini API with retry on transient failures."""
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config={
            "temperature": 0,
            "response_mime_type": "application/json",
        },
    )
    return response.text


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True,
)
def _call_gemini_with_image(prompt: str, image_bytes: bytes, mime_type: str) -> str:
    """Call Gemini API with an image (multimodal) with retry on transient failures."""
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    text_part = types.Part.from_text(text=prompt)

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[image_part, text_part],
        config={
            "temperature": 0,
            "response_mime_type": "application/json",
        },
    )
    return response.text


def _validate_parsed_output(raw_text: str) -> ParsedPhysicsProblem:
    """Parse JSON and validate against Pydantic model."""
    # Parse JSON
    try:
        parsed_json = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"AI returned invalid JSON: {raw_text[:200]}")
        raise ParsingError(
            f"AI returned invalid JSON: {e.msg} at position {e.pos}",
            raw_output=raw_text,
        )

    # Validate against Pydantic model
    try:
        result = ParsedPhysicsProblem.model_validate(parsed_json)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise ParsingError(
            f"AI output failed validation: {e}",
            raw_output=raw_text,
        )

    return result


def parse_physics_problem(problem_text: str) -> ParsedPhysicsProblem:
    """
    Parse a physics problem text into a validated structured representation.

    Args:
        problem_text: The natural language physics problem.

    Returns:
        A validated ParsedPhysicsProblem instance.

    Raises:
        ParsingError: If the AI output cannot be parsed or fails validation.
    """
    prompt = build_prompt(problem_text)

    try:
        raw_text = _call_gemini(prompt)
    except Exception as e:
        logger.error(f"Gemini API call failed after retries: {e}")
        raise ParsingError(
            f"AI service unavailable: {type(e).__name__}. Please try again later.",
            raw_output=None,
        )

    return _validate_parsed_output(raw_text)


def parse_physics_image(image_bytes: bytes, mime_type: str) -> ParsedPhysicsProblem:
    """
    Parse a physics problem from an image (OCR + parsing in one step).

    Uses Gemini's multimodal vision to read the problem text from the
    image and extract the structured physics data.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        mime_type: MIME type of the image (e.g. 'image/jpeg', 'image/png').

    Returns:
        A validated ParsedPhysicsProblem instance.

    Raises:
        ParsingError: If the image cannot be read or the output fails validation.
    """
    prompt = build_image_prompt()

    try:
        raw_text = _call_gemini_with_image(prompt, image_bytes, mime_type)
    except Exception as e:
        logger.error(f"Gemini Vision API call failed after retries: {e}")
        raise ParsingError(
            f"AI service unavailable: {type(e).__name__}. Please try again later.",
            raw_output=None,
        )

    return _validate_parsed_output(raw_text)

