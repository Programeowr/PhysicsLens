"""FastAPI adapter exposing the local, rule-based pipeline."""

from __future__ import annotations

import base64
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel

from .pipeline import solve_and_render

app = FastAPI(title="Physics Diagram Generator", version="1.0")


class SolveRequest(BaseModel):
    text: str


@app.post("/solve")
def solve_question(request: SolveRequest) -> dict[str, object]:
    with NamedTemporaryFile(suffix=".svg", delete=False) as temp:
        output_path = temp.name
    result = solve_and_render(request.text, output_path)
    response: dict[str, object] = {"status": result["status"], "missing_fields": result["missing_fields"]}
    if result["status"] == "ok" and result["diagram_path"]:
        response["diagram_svg_base64"] = base64.b64encode(Path(str(result["diagram_path"])).read_bytes()).decode("ascii")
    return response


@app.post("/solve.svg", response_class=Response)
def solve_question_svg(request: SolveRequest) -> Response:
    """Return the rendered diagram itself, ready for a browser or <img> tag."""
    with NamedTemporaryFile(suffix=".svg", delete=False) as temp:
        output_path = temp.name
    result = solve_and_render(request.text, output_path)
    if result["status"] != "ok" or not result["diagram_path"]:
        missing = ", ".join(result["missing_fields"])
        return Response(f"Unable to solve: {missing}", status_code=422, media_type="text/plain")
    return Response(Path(str(result["diagram_path"])).read_text(encoding="utf-8"), media_type="image/svg+xml")
