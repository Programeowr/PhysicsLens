"""FastAPI adapter exposing the local, rule-based pipeline."""

from __future__ import annotations

import base64
import os
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from .pipeline import ParserMode, solve_and_render
from .schema import VisualFeatures


def _visual_features_dict(vf: VisualFeatures) -> dict:
    """Serialise VisualFeatures to a plain dict suitable for JSON responses."""
    return {
        "object_types": vf.object_types,
        "surface_type": vf.surface_type,
        "motion_state": vf.motion_state,
        "requested_view": vf.requested_view,
        "force_mentions": [
            {"force_type": fm.force_type, "provenance": fm.provenance, "direction_hint": fm.direction_hint}
            for fm in vf.force_mentions
        ],
        "constraint_relationships": [
            {"kind": cr.kind, "object_a_id": cr.object_a_id, "object_b_id": cr.object_b_id}
            for cr in vf.constraint_relationships
        ],
        "known_quantities": vf.known_quantities,
        "unknown_quantities": vf.unknown_quantities,
        "ambiguity_flags": [
            {"field": af.field, "reason": af.reason, "confidence": af.confidence}
            for af in vf.ambiguity_flags
        ],
        "is_ambiguous": vf.is_ambiguous,
    }

app = FastAPI(title="Physics Diagram Generator", version="2.0")

# Get allowed origins from environment variable or use wildcard for development
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")] if allowed_origins_str != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SolveRequest(BaseModel):
    text: str
    parser: ParserMode = "llm"
    """Which parser to use: ``"llm"`` (default) or ``"deterministic"``.

    - ``"llm"``: Hybrid mode — tries deterministic first, falls back to
      Ollama qwen2.5:7b if the parse is incomplete (~2–10s when LLM runs).
    - ``"deterministic"``: Fast regex/keyword extraction only (~5ms).
    
    Default is hybrid mode for best accuracy. Use deterministic for speed-critical cases.
    """


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/solve")
def solve_question(request: SolveRequest) -> dict[str, object]:
    with NamedTemporaryFile(suffix=".svg", delete=False) as temp:
        output_path = temp.name
    try:
        result = solve_and_render(request.text, output_path, parser=request.parser)
        response: dict[str, object] = {
            "status": result["status"],
            "missing_fields": result["missing_fields"],
            "parser_used": request.parser,
        }
        if result.get("force_solution"):
            response["force_solution"] = asdict(result["force_solution"])
        parse_result = result["parse_result"]
        response["visual_features"] = _visual_features_dict(parse_result.visual_features)
        if result["status"] == "ok" and result["diagram_path"]:
            response["diagram_svg_base64"] = base64.b64encode(
                Path(str(result["diagram_path"])).read_bytes()
            ).decode("ascii")
        return response
    finally:
        Path(output_path).unlink(missing_ok=True)


@app.post("/solve.svg", response_class=Response)
def solve_question_svg(request: SolveRequest) -> Response:
    """Return the rendered diagram itself, ready for a browser or <img> tag."""
    with NamedTemporaryFile(suffix=".svg", delete=False) as temp:
        output_path = temp.name
    try:
        result = solve_and_render(request.text, output_path, parser=request.parser)
        if result["status"] != "ok" or not result["diagram_path"]:
            missing = ", ".join(result["missing_fields"])
            return Response(f"Unable to solve: {missing}", status_code=422, media_type="text/plain")
        return Response(Path(str(result["diagram_path"])).read_text(encoding="utf-8"), media_type="image/svg+xml")
    finally:
        Path(output_path).unlink(missing_ok=True)

