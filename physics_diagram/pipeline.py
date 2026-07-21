"""Public orchestration entry point for parsing, solving and rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .parser import parse
from .physics_engine import SOLVERS, solve
from .renderer import render, render_generic
from .validation import validate


def solve_and_render(text: str, output_path: str) -> dict[str, Any]:
    """Return parsing, solution, SVG path and a clear status for one question."""
    result = validate(parse(text))
    if not result.is_complete:
        diagram = render_generic(result, None, output_path)
        return {"parse_result": result, "force_solution": None, "diagram_path": diagram,
                "status": "needs_clarification", "missing_fields": result.missing_required}
    if result.scenario_type not in SOLVERS:
        diagram = render_generic(result, None, output_path)
        return {"parse_result": result, "force_solution": None, "diagram_path": diagram,
                "status": "unsupported_scenario", "missing_fields": []}
    solution = solve(result)
    diagram = render(result, solution, output_path)
    return {"parse_result": result, "force_solution": solution, "diagram_path": diagram,
            "status": "ok", "missing_fields": []}
