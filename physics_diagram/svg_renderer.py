"""Convert a laid-out scene graph into SVG output."""

from __future__ import annotations

from html import escape
from math import cos, pi, sin, tan
from pathlib import Path

from .schema import SceneGraph


COLORS = {
    "weight": "#d62728",
    "normal_force": "#1f77b4",
    "friction": "#9467bd",
    "tension": "#ff7f0e",
    "applied_force": "#2ca02c",
}


def _svg_start(scene: SceneGraph) -> list[str]:
    canvas = scene.canvas
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas.width:g}" height="{canvas.height:g}" viewBox="0 0 {canvas.width:g} {canvas.height:g}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="context-stroke"/></marker></defs>',
        f'<rect width="100%" height="100%" fill="{canvas.background}"/>',
    ]
    if scene.hints.show_title:
        parts.append(f'<text x="{canvas.width / 2:.1f}" y="38" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold">{escape(scene.title)}</text>')
    return parts


def _render_force(force) -> str:
    color = COLORS.get(force.name, "#333")
    label = escape(force.name.replace("_", " ").title())
    return (
        f'<line x1="{force.x1:.1f}" y1="{force.y1:.1f}" x2="{force.x2:.1f}" y2="{force.y2:.1f}" stroke="{color}" stroke-width="3" marker-end="url(#arrow)"/>'
        f'<text x="{force.label_x:.1f}" y="{force.label_y:.1f}" text-anchor="middle" fill="{color}" font-family="Arial" font-size="14">{label} = {force.magnitude_n:.1f} N</text>'
    )


def _render_object(obj) -> str:
    if obj.shape == "circle":
        return f'<circle cx="{obj.x:.1f}" cy="{obj.y:.1f}" r="{max(obj.width, obj.height) / 2:.1f}" fill="{obj.fill}" stroke="{obj.stroke}" stroke-width="2"/>'
    x = obj.x - obj.width / 2
    y = obj.y - obj.height / 2
    transform = f' transform="rotate({obj.rotation_deg:.1f} {obj.x:.1f} {obj.y:.1f})"' if obj.rotation_deg else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{obj.width:.1f}" height="{obj.height:.1f}" rx="3" fill="{obj.fill}" stroke="{obj.stroke}" stroke-width="2"{transform}/>'


def _render_annotation(annotation) -> str:
    return f'<text x="{annotation.x:.1f}" y="{annotation.y:.1f}" text-anchor="{annotation.align}" fill="{annotation.fill}" font-family="Arial" font-size="{annotation.size:g}">{escape(annotation.text)}</text>'


def _render_incline_scene(scene: SceneGraph) -> list[str]:
    result = scene.source_result
    if result is None:
        return []
    angle = float(result.geometry.incline_angle_deg or 0.0)
    radians = angle * pi / 180
    start, length = (120.0, 500.0), 570.0
    end = (start[0] + length * cos(radians), start[1] - length * sin(radians))
    cx = start[0] + 300 * cos(radians) - 22 * sin(radians)
    cy = start[1] - 300 * sin(radians) - 22 * cos(radians)
    mass = result.objects[0].mass_kg if result.objects and result.objects[0].mass_kg is not None else None
    parts = [
        f'<path d="M {start[0]:.1f} {start[1]:.1f} L {end[0]:.1f} {end[1]:.1f}" stroke="#555" stroke-width="7"/>',
        f'<path d="M {start[0]:.1f} {start[1]:.1f} L {end[0]:.1f} {start[1]:.1f}" stroke="#999" stroke-width="2"/>',
        f'<path d="M {start[0]+50:.1f} {start[1]:.1f} A 50 50 0 0 0 {start[0]+50*cos(radians):.1f} {start[1]-50*sin(radians):.1f}" fill="none" stroke="#777" stroke-width="2"/>',
        f'<text x="{start[0]+75:.1f}" y="{start[1]-15:.1f}" font-family="Arial" font-size="16">{angle:g}°</text>',
        f'<rect x="{cx-44:.1f}" y="{cy-28:.1f}" width="88" height="56" rx="3" fill="#e6e6e6" stroke="#222" stroke-width="2" transform="rotate({-angle:.1f} {cx:.1f} {cy:.1f})"/>',
    ]
    if mass is not None:
        parts.append(f'<text x="{cx:.1f}" y="{cy+5:.1f}" text-anchor="middle" font-family="Arial" font-size="15">{mass:g} kg</text>')
    return parts


def _render_horizontal_scene(scene: SceneGraph) -> list[str]:
    result = scene.source_result
    if result is None:
        return []
    mass = result.objects[0].mass_kg if result.objects and result.objects[0].mass_kg is not None else None
    parts = [
        '<line x1="100" y1="420" x2="800" y2="420" stroke="#555" stroke-width="7"/>',
        '<rect x="405" y="335" width="90" height="60" rx="3" fill="#e6e6e6" stroke="#222" stroke-width="2"/>'
    ]
    if mass is not None:
        parts.append(f'<text x="450" y="370" text-anchor="middle" font-family="Arial" font-size="15">{mass:g} kg</text>')
    return parts


def _render_atwood_scene(scene: SceneGraph) -> list[str]:
    if scene.source_result is None or len(scene.objects) < 2:
        return []
    return [
        '<circle cx="450" cy="155" r="50" fill="none" stroke="#555" stroke-width="5"/>',
        '<path d="M 400 155 L 350 155 L 350 380 M 500 155 L 550 155 L 550 380" fill="none" stroke="#555" stroke-width="4"/>',
    ]


def _render_projectile_scene(scene: SceneGraph) -> list[str]:
    result = scene.source_result
    solution = scene.source_solution
    if result is None or solution is None:
        return []
    range_m = float(solution.derived_values.get("range_m") or 1.0)
    height = float(solution.derived_values.get("max_height_m") or 1.0)
    scale = min(620 / max(range_m, 1), 280 / max(height, 1))
    origin = (130.0, 490.0)
    points: list[str] = []
    angle = (result.geometry.projectile_angle_deg or 45.0) * pi / 180
    speed = result.geometry.initial_speed_ms or 1.0
    for index in range(61):
        x = range_m * index / 60
        y = x * tan(angle) - 9.8 * x * x / (2 * speed * speed * cos(angle) ** 2)
        points.append(f"{origin[0] + x * scale:.1f},{origin[1] - y * scale:.1f}")
    anchor = (origin[0] + range_m * scale / 2, origin[1] - height * scale)
    mass_label = f"{result.objects[0].mass_kg:g} kg" if result.objects and result.objects[0].mass_kg is not None else "projectile"
    return [
        f'<line x1="{origin[0]:.1f}" y1="{origin[1]:.1f}" x2="{origin[0] + range_m*scale:.1f}" y2="{origin[1]:.1f}" stroke="#555" stroke-width="4"/>',
        f'<polyline points="{" ".join(points)}" fill="none" stroke="#555" stroke-width="3"/>',
        f'<circle cx="{anchor[0]:.1f}" cy="{anchor[1]:.1f}" r="11" fill="#e6e6e6" stroke="#222" stroke-width="2"/>',
        f'<text x="{anchor[0]:.1f}" y="{anchor[1]-18:.1f}" text-anchor="middle" font-family="Arial" font-size="14">{mass_label}</text>',
    ]


def render_scene(scene: SceneGraph, output_path: str) -> str:
    parts = _svg_start(scene)
    if scene.scenario_type == "inclined_plane":
        parts.extend(_render_incline_scene(scene))
    elif scene.scenario_type == "horizontal_friction":
        parts.extend(_render_horizontal_scene(scene))
    elif scene.scenario_type == "atwood_pulley":
        parts.extend(_render_atwood_scene(scene))
    elif scene.scenario_type == "projectile_motion":
        parts.extend(_render_projectile_scene(scene))
    else:
        for surface in scene.surfaces:
            if surface.kind == "ground":
                parts.append(f'<line x1="{surface.x1:.1f}" y1="{surface.y1:.1f}" x2="{surface.x2:.1f}" y2="{surface.y2:.1f}" stroke="#555" stroke-width="4"/>')
    parts.extend(_render_object(obj) for obj in scene.objects)
    parts.extend(_render_force(force) for force in scene.forces)
    parts.extend(_render_annotation(annotation) for annotation in scene.annotations)
    parts.append("</svg>")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(part for part in parts if part), encoding="utf-8")
    return str(path)


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
