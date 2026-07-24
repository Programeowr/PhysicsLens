"""Convert a prepared scene graph into clean, extensible SVG markup."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Iterable

from .schema import SceneAnnotation, SceneCanvas, SceneForce, SceneGraph, SceneObject, SceneSurface

FONT_FAMILY = "Inter, Roboto, Source Sans Pro, Arial, sans-serif"


def render_scene(scene: SceneGraph, output_path: str) -> str:
    parts: list[str] = []
    parts.extend(_svg_start(scene.canvas, scene.title))
    parts.append('<g id="background">')
    parts.append(_background_rect(scene.canvas))
    parts.append("</g>")
    parts.append('<g id="surfaces">')
    parts.extend(_render_surfaces(scene.surfaces))
    parts.append("</g>")
    parts.append('<g id="objects">')
    parts.extend(_render_objects(scene.objects))
    parts.append("</g>")
    parts.append('<g id="forces">')
    parts.extend(_render_forces(scene.forces))
    parts.append("</g>")
    parts.append('<g id="annotations">')
    parts.extend(_render_annotations(scene.annotations))
    parts.append("</g>")
    parts.append("</svg>")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")
    return str(path)


def _svg_start(canvas: SceneCanvas, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas.width}" height="{canvas.height}" viewBox="0 0 {canvas.width} {canvas.height}" role="img" aria-label="{escape(title)}">',
        "<defs>",
        "<marker id=\"arrowhead\" markerWidth=\"10\" markerHeight=\"10\" refX=\"9\" refY=\"5\" orient=\"auto\" markerUnits=\"strokeWidth\">",
        "<path d=\"M0,0 L10,5 L0,10 Z\" fill=\"context-stroke\" />",
        "</marker>",
        "</defs>",
        _text_block(title, canvas.width / 2, 38, 24, True),
    ]


def _background_rect(canvas: SceneCanvas) -> str:
    return f'<rect width="100%" height="100%" fill="#f8f8f8"/>'


def _render_surfaces(surfaces: Iterable[SceneSurface]) -> list[str]:
    parts: list[str] = []
    for surface in surfaces:
        if surface.type == "incline" and surface.start and surface.end:
            parts.append(
                f'<path d="M {surface.start[0]:.1f} {surface.start[1]:.1f} L {surface.end[0]:.1f} {surface.end[1]:.1f}" stroke="#6c6c6c" stroke-width="8" stroke-linecap="round"/>'
            )
            parts.append(
                f'<path d="M {surface.start[0]:.1f} {surface.start[1]:.1f} L {surface.end[0]:.1f} {surface.start[1]:.1f}" stroke="#aaaaaa" stroke-width="2" stroke-dasharray="6 6"/>'
            )
        elif surface.type == "ground" and surface.start and surface.end:
            parts.append(
                f'<line x1="{surface.start[0]:.1f}" y1="{surface.start[1]:.1f}" x2="{surface.end[0]:.1f}" y2="{surface.end[1]:.1f}" stroke="#555" stroke-width="7" stroke-linecap="round"/>'
            )
        elif surface.type == "pulley" and surface.center and surface.radius:
            parts.append(
                f'<circle cx="{surface.center[0]:.1f}" cy="{surface.center[1]:.1f}" r="{surface.radius:.1f}" fill="none" stroke="#5a5a5a" stroke-width="5"/>'
            )
            parts.append(
                f'<line x1="{surface.center[0] - surface.radius:.1f}" y1="{surface.center[1]:.1f}" x2="{surface.center[0] - surface.radius - 60:.1f}" y2="{surface.center[1]:.1f}" stroke="#5a5a5a" stroke-width="4"/>'
            )
            parts.append(
                f'<line x1="{surface.center[0] + surface.radius:.1f}" y1="{surface.center[1]:.1f}" x2="{surface.center[0] + surface.radius + 60:.1f}" y2="{surface.center[1]:.1f}" stroke="#5a5a5a" stroke-width="4"/>'
            )
        elif surface.type == "trajectory" and surface.points:
            points_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in surface.points)
            parts.append(
                f'<polyline points="{points_str}" fill="none" stroke="#4a4a4a" stroke-width="3" stroke-linejoin="round"/>'
            )
    return parts


def _render_objects(objects: Iterable[SceneObject]) -> list[str]:
    parts: list[str] = []
    for obj in objects:
        x, y = obj.position
        parts.append(
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({obj.rotation_deg:.1f})">'
            f'<rect x="{-obj.width / 2:.1f}" y="{-obj.height / 2:.1f}" width="{obj.width:.1f}" height="{obj.height:.1f}" rx="14" fill="#e6e6e6" stroke="#3a3a3a" stroke-width="2"/>'
            f'<text x="0" y="4" text-anchor="middle" fill="#222" font-family="{FONT_FAMILY}" font-size="16">{escape(obj.label)}</text>'
            "</g>"
        )
    return parts


def _render_forces(forces: Iterable[SceneForce]) -> list[str]:
    parts: list[str] = []
    for force in forces:
        if not (force.anchor_position and force.tip_position and force.label_position):
            continue
        ax, ay = force.anchor_position
        tx, ty = force.tip_position
        lx, ly = force.label_position
        parts.append(
            f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="{force.color}" stroke-width="4" stroke-linecap="round" marker-end="url(#arrowhead)"/>'
        )
        parts.append(
            f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="5" fill="{force.color}"/>'
        )
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" fill="{force.color}" font-family="{FONT_FAMILY}" font-size="14" font-weight="700">{escape(force.label)} = {force.magnitude_n:.1f} N</text>'
        )
    return parts


def _render_annotations(annotations: Iterable[SceneAnnotation]) -> list[str]:
    parts: list[str] = []
    for annotation in annotations:
        if annotation.type == "angle" and annotation.position and annotation.radius and annotation.label_position:
            x, y = annotation.position
            parts.append(
                f'<path d="M {x + annotation.radius:.1f} {y:.1f} A {annotation.radius:.1f} {annotation.radius:.1f} 0 0 0 {x:.1f} {y - annotation.radius:.1f}" fill="none" stroke="#777" stroke-width="2"/>'
            )
            parts.append(
                f'<text x="{annotation.label_position[0]:.1f}" y="{annotation.label_position[1]:.1f}" fill="#333" font-family="{FONT_FAMILY}" font-size="15">{annotation.value:.0f}°</text>'
            )
    return parts


def _text_block(text: str, x: float, y: float, size: int, bold: bool = False) -> str:
    weight = "bold" if bold else "normal"
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" fill="#222" font-family="{FONT_FAMILY}" font-size="{size}" font-weight="{weight}">{escape(text)}</text>'
