"""Public rendering facade for the scene-graph-based SVG pipeline."""

from __future__ import annotations

from typing import Any

from .layout import layout_scene
from .scene_graph import build_scene_graph
from .svg_renderer import render_scene
from .schema import ForceSolution, ParseResult


def render_diagram(
    result: ParseResult,
    solution: ForceSolution | None,
    output_path: str,
    render_options: dict[str, Any] | None = None,
    diagnostics: bool = False,
) -> str:
    scene = build_scene_graph(result, solution, render_options)
    laid_out = layout_scene(scene, diagnostics=diagnostics)
    return render_scene(laid_out, output_path)


def render(result: ParseResult, solution: ForceSolution, output_path: str) -> str:
    return render_diagram(result, solution, output_path)


def render_generic(result: ParseResult, solution: ForceSolution | None, output_path: str) -> str:
    return render_diagram(result, solution, output_path, {"title": "Generic Free-Body Diagram"})
