"""Dependency-free SVG renderer for solved force diagrams."""

from __future__ import annotations

from html import escape
from math import cos, pi, sin, tan
from pathlib import Path

from .schema import ForceSolution, ForceVector, ParseResult

WIDTH, HEIGHT = 900, 620
COLORS = {"weight": "#d62728", "normal_force": "#1f77b4", "friction": "#9467bd", "tension": "#ff7f0e", "applied_force": "#2ca02c"}


def _svg_start(title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        "<defs><marker id=\"arrow\" markerWidth=\"10\" markerHeight=\"8\" refX=\"9\" refY=\"4\" orient=\"auto\"><path d=\"M0,0 L10,4 L0,8 z\" fill=\"context-stroke\"/></marker></defs>",
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="450" y="38" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold">{escape(title)}</text>',
    ]


def _force_scale(solution: ForceSolution) -> float:
    return 140.0 / max((force.magnitude_n for force in solution.forces), default=1.0)


def _force_svg(vector: ForceVector, anchor: tuple[float, float], scale: float) -> str:
    radians = vector.direction_deg * pi / 180
    length = max(36.0, vector.magnitude_n * scale)
    x2, y2 = anchor[0] + length * cos(radians), anchor[1] - length * sin(radians)
    color = COLORS.get(vector.name, "#333")
    label = escape(vector.name.replace("_", " ").title())
    return (
        f'<line x1="{anchor[0]:.1f}" y1="{anchor[1]:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="3" marker-end="url(#arrow)"/>'
        f'<text x="{x2:.1f}" y="{y2 - 8:.1f}" text-anchor="middle" fill="{color}" font-family="Arial" font-size="14">{label} = {vector.magnitude_n:.1f} N</text>'
    )


def _save(parts: list[str], output_path: str) -> str:
    parts.append("</svg>")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(parts), encoding="utf-8")
    return str(path)


def render_inclined_plane(result: ParseResult, solution: ForceSolution, output_path: str) -> str:
    angle = result.geometry.incline_angle_deg or 0.0
    radians = angle * pi / 180
    start, length = (120.0, 500.0), 570.0
    end = (start[0] + length * cos(radians), start[1] - length * sin(radians))
    cx, cy = start[0] + 300 * cos(radians) - 22 * sin(radians), start[1] - 300 * sin(radians) - 22 * cos(radians)
    parts = _svg_start("Inclined Plane Free-Body Diagram")
    parts += [
        f'<path d="M {start[0]} {start[1]} L {end[0]:.1f} {end[1]:.1f}" stroke="#555" stroke-width="7"/>',
        f'<path d="M {start[0]} {start[1]} L {end[0]:.1f} {start[1]}" stroke="#999" stroke-width="2"/>',
        f'<path d="M {start[0]+50} {start[1]} A 50 50 0 0 0 {start[0]+50*cos(radians):.1f} {start[1]-50*sin(radians):.1f}" fill="none" stroke="#777" stroke-width="2"/>',
        f'<text x="{start[0]+75}" y="{start[1]-15}" font-family="Arial" font-size="16">{angle:g}°</text>',
        f'<rect x="{cx-44:.1f}" y="{cy-28:.1f}" width="88" height="56" rx="3" fill="#e6e6e6" stroke="#222" stroke-width="2" transform="rotate({-angle:.1f} {cx:.1f} {cy:.1f})"/>',
        f'<text x="{cx:.1f}" y="{cy+5:.1f}" text-anchor="middle" font-family="Arial" font-size="15">{result.objects[0].mass_kg:g} kg</text>',
    ]
    parts.extend(_force_svg(force, (cx, cy), _force_scale(solution)) for force in solution.forces)
    return _save(parts, output_path)


def render_horizontal_friction(result: ParseResult, solution: ForceSolution, output_path: str) -> str:
    anchor = (450.0, 365.0)
    parts = _svg_start("Horizontal Free-Body Diagram")
    parts += ['<line x1="100" y1="420" x2="800" y2="420" stroke="#555" stroke-width="7"/>', '<rect x="405" y="335" width="90" height="60" rx="3" fill="#e6e6e6" stroke="#222" stroke-width="2"/>', f'<text x="450" y="370" text-anchor="middle" font-family="Arial" font-size="15">{result.objects[0].mass_kg:g} kg</text>']
    parts.extend(_force_svg(force, anchor, _force_scale(solution)) for force in solution.forces)
    return _save(parts, output_path)


def render_atwood_pulley(result: ParseResult, solution: ForceSolution, output_path: str) -> str:
    anchors = {result.objects[0].id: (350.0, 410.0), result.objects[1].id: (550.0, 410.0)}
    parts = _svg_start("Atwood Pulley Free-Body Diagram")
    parts += ['<circle cx="450" cy="155" r="50" fill="none" stroke="#555" stroke-width="5"/>', '<path d="M 400 155 L 350 155 L 350 380 M 500 155 L 550 155 L 550 380" fill="none" stroke="#555" stroke-width="4"/>']
    for obj in result.objects[:2]:
        x, y = anchors[obj.id]
        parts += [f'<rect x="{x-38}" y="{y-28}" width="76" height="56" rx="3" fill="#e6e6e6" stroke="#222" stroke-width="2"/>', f'<text x="{x}" y="{y+5}" text-anchor="middle" font-family="Arial" font-size="14">{obj.mass_kg:g} kg</text>']
    parts.extend(_force_svg(force, anchors[force.anchor], _force_scale(solution)) for force in solution.forces)
    return _save(parts, output_path)


def render_projectile_motion(result: ParseResult, solution: ForceSolution, output_path: str) -> str:
    range_m = float(solution.derived_values["range_m"] or 1.0)
    height = float(solution.derived_values["max_height_m"] or 1.0)
    # Scale physical coordinates consistently into a fixed drawing area.
    scale = min(620 / max(range_m, 1), 280 / max(height, 1))
    origin = (130.0, 490.0)
    points = []
    angle = (result.geometry.projectile_angle_deg or 45.0) * pi / 180
    speed = result.geometry.initial_speed_ms or 1.0
    for index in range(61):
        x = range_m * index / 60
        y = x * tan(angle) - 9.8 * x * x / (2 * speed * speed * cos(angle) ** 2)
        points.append(f"{origin[0] + x * scale:.1f},{origin[1] - y * scale:.1f}")
    anchor = (origin[0] + range_m * scale / 2, origin[1] - height * scale)
    mass_label = f"{result.objects[0].mass_kg:g} kg" if result.objects and result.objects[0].mass_kg is not None else "projectile"
    parts = _svg_start("Projectile Motion Force Diagram")
    parts += [f'<line x1="{origin[0]}" y1="{origin[1]}" x2="{origin[0] + range_m*scale:.1f}" y2="{origin[1]}" stroke="#555" stroke-width="4"/>', f'<polyline points="{" ".join(points)}" fill="none" stroke="#555" stroke-width="3"/>', f'<circle cx="{anchor[0]:.1f}" cy="{anchor[1]:.1f}" r="11" fill="#e6e6e6" stroke="#222" stroke-width="2"/>', f'<text x="{anchor[0]:.1f}" y="{anchor[1]-18:.1f}" text-anchor="middle" font-family="Arial" font-size="14">{mass_label}</text>']
    parts.extend(_force_svg(force, anchor, _force_scale(solution)) for force in solution.forces)
    return _save(parts, output_path)


def render_generic(result: ParseResult, solution: ForceSolution | None, output_path: str) -> str:
    anchor = (450.0, 330.0)
    label = result.objects[0].label if result.objects and result.objects[0].label else "object"
    parts = _svg_start("Generic Free-Body Diagram") + [f'<rect x="405" y="300" width="90" height="60" rx="3" fill="#e6e6e6" stroke="#222" stroke-width="2"/>', f'<text x="450" y="336" text-anchor="middle" font-family="Arial" font-size="15">{escape(label)}</text>']
    if solution:
        parts.extend(_force_svg(force, anchor, _force_scale(solution)) for force in solution.forces)
    return _save(parts, output_path)


RENDERERS = {"inclined_plane": render_inclined_plane, "horizontal_friction": render_horizontal_friction, "atwood_pulley": render_atwood_pulley, "projectile_motion": render_projectile_motion}


def render(result: ParseResult, solution: ForceSolution, output_path: str) -> str:
    return RENDERERS.get(result.scenario_type, render_generic)(result, solution, output_path)
