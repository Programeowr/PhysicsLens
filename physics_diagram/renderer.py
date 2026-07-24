"""Dependency-free SVG renderer for solved force diagrams."""

from __future__ import annotations

from .layout import layout_scene
from .scene_graph import build_scene_graph
from .schema import ForceSolution, ParseResult
from .svg_renderer import render_scene


def render(result: ParseResult, solution: ForceSolution, output_path: str) -> str:
    scene = build_scene_graph(result, solution)
    layout_scene(scene)
    return render_scene(scene, output_path)


def render_generic(result: ParseResult, solution: ForceSolution | None, output_path: str) -> str:
    scene = build_scene_graph(result, solution)
    layout_scene(scene)
    return render_scene(scene, output_path)
