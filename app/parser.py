"""
Physics problem parser using Google Gemini AI.

Handles the AI API call with retry logic and validates the
parsed output against Pydantic models. Supports both text
and image-based (OCR) problem parsing.

Optimizations:
- Flash→Pro automatic fallback on validation failures
- Thinking budget control for reasoning depth
- JSON error recovery (auto-fix common AI mistakes)
- In-memory LRU caching of parsed results
"""

import hashlib
import json
import logging
import re
from functools import lru_cache

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.models import ParsedPhysicsProblem
from app.prompts import build_prompt, build_image_prompt

logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=settings.gemini_api_key)

# ── In-memory result cache ────────────────────────────────

_result_cache: dict[str, ParsedPhysicsProblem] = {}
_cache_order: list[str] = []


def _cache_key(text: str) -> str:
    """Generate a stable cache key from problem text."""
    normalized = re.sub(r'\s+', ' ', text.strip().lower())
    return hashlib.md5(normalized.encode()).hexdigest()


def _cache_get(key: str) -> ParsedPhysicsProblem | None:
    """Get a cached result, or None if not cached."""
    return _result_cache.get(key)


def _cache_put(key: str, result: ParsedPhysicsProblem) -> None:
    """Store a result in the cache, evicting oldest if full."""
    if key in _result_cache:
        return
    if len(_result_cache) >= settings.cache_max_size:
        oldest = _cache_order.pop(0)
        _result_cache.pop(oldest, None)
    _result_cache[key] = result
    _cache_order.append(key)


# ── Custom exceptions ─────────────────────────────────────

class ParsingError(Exception):
    """Raised when the AI output cannot be parsed or validated."""

    def __init__(self, message: str, raw_output: str | None = None):
        super().__init__(message)
        self.raw_output = raw_output


# ── Gemini API calls ──────────────────────────────────────

def _build_config(model: str) -> dict:
    """Build generation config, adding thinking budget for Flash models."""
    config = {
        "temperature": 0,
        "response_mime_type": "application/json",
    }
    if "flash" in model and settings.thinking_budget > 0:
        config["thinking_config"] = types.ThinkingConfig(
            thinking_budget=settings.thinking_budget
        )
    return config


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True,
)
def _call_gemini(prompt: str, model: str | None = None) -> str:
    """Call Gemini API with retry on transient failures."""
    model = model or settings.gemini_model
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=_build_config(model),
    )
    return response.text


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True,
)
def _call_gemini_with_image(prompt: str, image_bytes: bytes, mime_type: str, model: str | None = None) -> str:
    """Call Gemini API with an image (multimodal) with retry on transient failures."""
    model = model or settings.gemini_model
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    text_part = types.Part.from_text(text=prompt)

    response = client.models.generate_content(
        model=model,
        contents=[image_part, text_part],
        config=_build_config(model),
    )
    return response.text


# ── JSON error recovery ──────────────────────────────────

def _recover_json(raw_text: str) -> str:
    """
    Attempt to fix common AI JSON mistakes before parsing.
    Returns cleaned text.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)

    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)

    # Fix single quotes to double quotes (common AI mistake)
    # Only do this if the text doesn't parse as-is
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # Try replacing single quotes
    fixed = text.replace("'", '"')
    try:
        json.loads(fixed)
        return fixed
    except json.JSONDecodeError:
        pass

    return text  # Return best effort


# ── Validation ────────────────────────────────────────────

def _validate_parsed_output(raw_text: str) -> ParsedPhysicsProblem:
    """Parse JSON (with error recovery) and validate against Pydantic model."""
    cleaned = _recover_json(raw_text)

    try:
        parsed_json = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"AI returned invalid JSON: {raw_text[:200]}")
        raise ParsingError(
            f"AI returned invalid JSON: {e.msg} at position {e.pos}",
            raw_output=raw_text,
        )

    # Apply physics sanity fixes before validation
    parsed_json = _apply_physics_fixes(parsed_json)

    try:
        result = ParsedPhysicsProblem.model_validate(parsed_json)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise ParsingError(
            f"AI output failed validation: {e}",
            raw_output=raw_text,
        )

    return result


def _apply_physics_fixes(data: dict) -> dict:
    """
    Auto-fix common physics mistakes in the AI output.
    Ensures basic physics invariants hold.
    """
    objects = {obj["id"]: obj for obj in data.get("objects", [])}
    forces = data.get("forces", [])
    g = data.get("constants", {}).get("gravity", 9.8)

    # Fix 1: Ensure gravity exists for every object with mass
    objects_with_gravity = {
        f["object_id"] for f in forces if f.get("type") == "gravity"
    }
    for obj_id, obj in objects.items():
        mass = obj.get("mass")
        if mass and mass > 0 and obj_id not in objects_with_gravity:
            forces.append({
                "type": "gravity",
                "magnitude": round(mass * g, 2),
                "direction": "vertical_down",
                "object_id": obj_id,
            })
            logger.info(f"Auto-added missing gravity for {obj_id}")

    # Fix 2: Correct gravity magnitude if wrong
    for force in forces:
        if force.get("type") == "gravity" and force.get("object_id") in objects:
            obj = objects[force["object_id"]]
            mass = obj.get("mass")
            if mass and mass > 0:
                expected = round(mass * g, 2)
                actual = force.get("magnitude")
                if actual and abs(actual - expected) > 1.0:
                    logger.info(
                        f"Fixed gravity for {force['object_id']}: "
                        f"{actual}→{expected}"
                    )
                    force["magnitude"] = expected

    # Fix 3: Ensure mass is positive
    for obj in data.get("objects", []):
        if obj.get("mass") is not None and obj["mass"] <= 0:
            obj["mass"] = abs(obj["mass"]) if obj["mass"] != 0 else None

    data["forces"] = forces
    return data


# ── Public API ────────────────────────────────────────────

def parse_physics_problem(problem_text: str) -> ParsedPhysicsProblem:
    """
    Parse a physics problem text into a validated structured representation.

    Uses Flash first, then automatically falls back to Pro if Flash
    output fails validation.

    Args:
        problem_text: The natural language physics problem.

    Returns:
        A validated ParsedPhysicsProblem instance.

    Raises:
        ParsingError: If both models fail to produce valid output.
    """
    # Check cache first
    key = _cache_key(problem_text)
    cached = _cache_get(key)
    if cached:
        logger.info(f"Cache hit for problem: {problem_text[:50]}...")
        return cached

    prompt = build_prompt(problem_text)

    # Attempt 1: Flash (fast, cheap)
    try:
        raw_text = _call_gemini(prompt, model=settings.gemini_model)
        result = _validate_parsed_output(raw_text)
        _cache_put(key, result)
        return result
    except ParsingError as flash_err:
        logger.warning(
            f"Flash failed, trying Pro fallback: {flash_err}"
        )
    except Exception as e:
        logger.error(f"Flash API call failed: {e}")

    # Attempt 2: Pro fallback (slower, more accurate)
    try:
        raw_text = _call_gemini(prompt, model=settings.gemini_fallback_model)
        result = _validate_parsed_output(raw_text)
        _cache_put(key, result)
        return result
    except ParsingError as pro_err:
        raise pro_err
    except Exception as e:
        logger.error(f"Pro API call also failed: {e}")
        raise ParsingError(
            f"AI service unavailable after Flash+Pro attempts: {type(e).__name__}",
            raw_output=None,
        )


def parse_physics_image(image_bytes: bytes, mime_type: str) -> ParsedPhysicsProblem:
    """
    Parse a physics problem from an image (OCR + parsing in one step).

    Uses Flash first, then falls back to Pro if validation fails.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        mime_type: MIME type of the image (e.g. 'image/jpeg', 'image/png').

    Returns:
        A validated ParsedPhysicsProblem instance.

    Raises:
        ParsingError: If both models fail.
    """
    prompt = build_image_prompt()

    # Attempt 1: Flash
    try:
        raw_text = _call_gemini_with_image(
            prompt, image_bytes, mime_type, model=settings.gemini_model
        )
        result = _validate_parsed_output(raw_text)
        return result
    except ParsingError as flash_err:
        logger.warning(
            f"Flash Vision failed, trying Pro fallback: {flash_err}"
        )
    except Exception as e:
        logger.error(f"Flash Vision API call failed: {e}")

    # Attempt 2: Pro fallback
    try:
        raw_text = _call_gemini_with_image(
            prompt, image_bytes, mime_type, model=settings.gemini_fallback_model
        )
        result = _validate_parsed_output(raw_text)
        return result
    except ParsingError as pro_err:
        raise pro_err
    except Exception as e:
        logger.error(f"Pro Vision API call also failed: {e}")
        raise ParsingError(
            f"AI service unavailable after Flash+Pro Vision attempts: {type(e).__name__}",
            raw_output=None,
        )
