"""Public orchestration entry point for parsing, solving and rendering."""

from __future__ import annotations

import logging
from typing import Any, Literal

from .parser import parse
from .physics_engine import SOLVERS, solve
from .renderer import render_diagram
from .validation import validate

logger = logging.getLogger(__name__)

ParserMode = Literal["deterministic", "llm"]


def _run_parser(text: str, parser: ParserMode):
    """Dispatch to the requested parser with hybrid fallback logic.
    
    When parser="llm" is requested, this runs deterministic first and only
    calls the LLM if the result is incomplete. This keeps the common case
    fast while handling edge cases gracefully.
    """
    result = parse(text)  # always try deterministic first
    
    # Hybrid mode: use LLM as a fallback for incomplete parses
    if parser == "llm" and not result.is_complete:
        logger.info("Deterministic parse incomplete (missing: %s); trying LLM fallback.", result.missing_required)
        try:
            from .llm_parser import parse_with_llm
            llm_result = parse_with_llm(text)
            if llm_result.is_complete:
                logger.info("LLM fallback succeeded.")
                return llm_result
            logger.warning("LLM fallback also incomplete (missing: %s).", llm_result.missing_required)
            return llm_result  # return LLM's attempt even if incomplete
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM fallback failed (%s); returning deterministic result.", exc)
            return result
    
    return result


def solve_and_render(
    text: str,
    output_path: str,
    parser: ParserMode = "llm",
) -> dict[str, Any]:
    """Return parsing, solution, SVG path and a clear status for one question.

    Args:
        text: Raw natural-language physics problem.
        output_path: File path where the SVG will be written.
        parser: ``"llm"`` (default) enables hybrid mode: tries deterministic first, then
                falls back to Ollama qwen2.5:7b if the parse is incomplete;
                ``"deterministic"`` uses only the regex/keyword pipeline.
    """
    result = validate(_run_parser(text, parser))
    if not result.is_complete:
        diagram = render_diagram(result, None, output_path, {"title": "Generic Free-Body Diagram"})
        return {"parse_result": result, "force_solution": None, "diagram_path": diagram,
                "status": "needs_clarification", "missing_fields": result.missing_required}
    if result.scenario_type not in SOLVERS:
        diagram = render_diagram(result, None, output_path, {"title": "Generic Free-Body Diagram"})
        return {"parse_result": result, "force_solution": None, "diagram_path": diagram,
                "status": "unsupported_scenario", "missing_fields": []}
    solution = solve(result)
    diagram = render_diagram(result, solution, output_path)
    return {"parse_result": result, "force_solution": solution, "diagram_path": diagram,
            "status": "ok", "missing_fields": []}
