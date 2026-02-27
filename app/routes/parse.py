"""
Parse routes — handles physics problem parsing via AI (text and image).
"""

import logging

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.models import ProblemInput
from app.parser import parse_physics_problem, parse_physics_image, ParsingError

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp",
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/parse")
@limiter.limit(settings.rate_limit)
async def parse_problem(request: Request, data: ProblemInput):
    """
    Parse a physics problem text into structured JSON.

    Accepts natural language physics problems and returns a validated
    structured representation with objects, surfaces, forces, etc.
    """
    try:
        result = parse_physics_problem(data.problem)
        return {
            "status": "success",
            "data": result.model_dump(),
        }
    except ParsingError as e:
        logger.warning(f"Parsing failed: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "message": str(e),
                "raw_output": e.raw_output[:500] if e.raw_output else None,
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error in /parse: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Internal server error. Please try again.",
            },
        )


@router.post("/parse-image")
@limiter.limit(settings.rate_limit)
async def parse_image(request: Request, file: UploadFile = File(...)):
    """
    Parse a physics problem from an uploaded image.

    Uses Gemini Vision to OCR the image and extract structured physics data.
    Accepts JPEG, PNG, WebP, GIF, or BMP images up to 10MB.

    Upload via multipart/form-data with the field name 'file'.
    """
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": f"Unsupported image type: {file.content_type}. "
                           f"Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
            },
        )

    # Read and validate size
    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": f"Image too large ({len(image_bytes) / 1024 / 1024:.1f}MB). "
                           f"Maximum size: {MAX_IMAGE_SIZE / 1024 / 1024:.0f}MB.",
            },
        )

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": "Empty file uploaded."},
        )

    try:
        result = parse_physics_image(image_bytes, file.content_type)
        return {
            "status": "success",
            "data": result.model_dump(),
        }
    except ParsingError as e:
        logger.warning(f"Image parsing failed: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "message": str(e),
                "raw_output": e.raw_output[:500] if e.raw_output else None,
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error in /parse-image: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Internal server error. Please try again.",
            },
        )

