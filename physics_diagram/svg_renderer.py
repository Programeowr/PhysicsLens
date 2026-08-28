"""Convert a laid-out scene graph into SVG output.

Sharper visual primitives are chosen based on RenderHints/DiagramIntent:
  - cart      → box body + two wheels
  - sphere/ball → circle marker
  - hanging_mass → block with suspension line
  - projectile  → circle marker + trajectory arc (when view_mode=trajectory)
  - surface textures: rough hash-marks, frictionless dashes, smooth plain line
  - velocity/acceleration vectors when RenderHints flags are set
  - component construction lines when show_components is True
  - diagnostics overlay (coloured bounding-box outlines + labels) when
    scene.diagnostics is populated
"""

from __future__ import annotations

from html import escape
from math import cos, pi, sin, tan
from pathlib import Path

from .schema import SceneGraph

# ── constants ─────────────────────────────────────────────────────────────────
FONT = "Arial, sans-serif"

FORCE_COLORS: dict[str, str] = {
    "weight":        "#d62728",
    "normal_force":  "#1f77b4",
    "normal":        "#1f77b4",
    "friction":      "#9467bd",
    "tension":       "#ff7f0e",
    "applied_force": "#2ca02c",
    "applied":       "#2ca02c",
    "spring":        "#8c564b",
    "air_resistance":"#17becf",
    "component":     "#7f7f7f",
}
_DEFAULT_FORCE_COLOR = "#333333"

DIAG_COLORS = ["#e377c2", "#bcbd22", "#17becf", "#9467bd", "#8c564b"]


# ── SVG header / footer ───────────────────────────────────────────────────────

def _svg_start(scene: SceneGraph) -> list[str]:
    w, h = scene.canvas.width, scene.canvas.height
    bg = scene.canvas.background
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' width="{w:g}" height="{h:g}"'
        f' viewBox="0 0 {w:g} {h:g}">',
        "<defs>",
        '  <marker id="arrow" markerWidth="10" markerHeight="8"'
        '   refX="9" refY="4" orient="auto">',
        '    <path d="M0,0 L10,4 L0,8 z" fill="context-stroke"/>',
        "  </marker>",
        '  <marker id="arrow-vel" markerWidth="10" markerHeight="8"'
        '   refX="9" refY="4" orient="auto">',
        '    <path d="M0,0 L10,4 L0,8 z" fill="#2196F3"/>',
        "  </marker>",
        '  <marker id="arrow-acc" markerWidth="10" markerHeight="8"'
        '   refX="9" refY="4" orient="auto">',
        '    <path d="M0,0 L10,4 L0,8 z" fill="#FF5722"/>',
        "  </marker>",
        "</defs>",
        f'<rect width="100%" height="100%" fill="{bg}"/>',
    ]
    if scene.hints.show_title:
        parts.append(
            f'<text x="{w / 2:.1f}" y="36"'
            f' text-anchor="middle" font-family="{FONT}"'
            f' font-size="21" font-weight="bold" fill="#111">'
            f'{escape(scene.title)}</text>'
        )
    return parts


# ── object primitives ─────────────────────────────────────────────────────────

def _render_box(obj, label: str) -> list[str]:
    x = obj.x - obj.width / 2
    y = obj.y - obj.height / 2
    rot = (f' transform="rotate({obj.rotation_deg:.1f} {obj.x:.1f} {obj.y:.1f})"'
           if obj.rotation_deg else "")
    parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{obj.width:.1f}"'
        f' height="{obj.height:.1f}" rx="4"'
        f' fill="{obj.fill}" stroke="{obj.stroke}" stroke-width="2.5"{rot}/>',
    ]
    if label:
        parts.append(
            f'<text x="{obj.x:.1f}" y="{obj.y + 5:.1f}"'
            f' text-anchor="middle" font-family="{FONT}"'
            f' font-size="14" fill="#222">{escape(label)}</text>'
        )
    return parts


def _render_sphere(obj, label: str) -> list[str]:
    r = max(obj.width, obj.height) / 2
    parts = [
        f'<circle cx="{obj.x:.1f}" cy="{obj.y:.1f}" r="{r:.1f}"'
        f' fill="{obj.fill}" stroke="{obj.stroke}" stroke-width="2.5"/>',
    ]
    if label:
        parts.append(
            f'<text x="{obj.x:.1f}" y="{obj.y - r - 6:.1f}"'
            f' text-anchor="middle" font-family="{FONT}"'
            f' font-size="14" fill="#222">{escape(label)}</text>'
        )
    return parts


def _render_cart(obj, label: str) -> list[str]:
    """Box body with two wheels underneath."""
    bx = obj.x - obj.width / 2
    by = obj.y - obj.height / 2
    wr = 10.0          # wheel radius
    w_y = obj.y + obj.height / 2 + wr   # wheel centre y
    parts = [
        f'<rect x="{bx:.1f}" y="{by:.1f}" width="{obj.width:.1f}"'
        f' height="{obj.height:.1f}" rx="3"'
        f' fill="{obj.fill}" stroke="{obj.stroke}" stroke-width="2.5"/>',
        f'<circle cx="{obj.x - obj.width / 4:.1f}" cy="{w_y:.1f}"'
        f' r="{wr:.1f}" fill="#888" stroke="#333" stroke-width="2"/>',
        f'<circle cx="{obj.x + obj.width / 4:.1f}" cy="{w_y:.1f}"'
        f' r="{wr:.1f}" fill="#888" stroke="#333" stroke-width="2"/>',
    ]
    if label:
        parts.append(
            f'<text x="{obj.x:.1f}" y="{obj.y + 5:.1f}"'
            f' text-anchor="middle" font-family="{FONT}"'
            f' font-size="14" fill="#222">{escape(label)}</text>'
        )
    return parts


def _render_hanging_mass(obj, label: str) -> list[str]:
    """Block with a short suspension line above it."""
    bx = obj.x - obj.width / 2
    by = obj.y - obj.height / 2
    rope_top_y = by - 28
    parts = [
        f'<line x1="{obj.x:.1f}" y1="{rope_top_y:.1f}"'
        f' x2="{obj.x:.1f}" y2="{by:.1f}"'
        f' stroke="#555" stroke-width="3"/>',
        f'<rect x="{bx:.1f}" y="{by:.1f}" width="{obj.width:.1f}"'
        f' height="{obj.height:.1f}" rx="3"'
        f' fill="{obj.fill}" stroke="{obj.stroke}" stroke-width="2.5"/>',
    ]
    if label:
        parts.append(
            f'<text x="{obj.x:.1f}" y="{obj.y + 5:.1f}"'
            f' text-anchor="middle" font-family="{FONT}"'
            f' font-size="14" fill="#222">{escape(label)}</text>'
        )
    return parts


def _render_projectile_marker(obj, label: str) -> list[str]:
    r = max(obj.width, obj.height) / 2
    parts = [
        f'<circle cx="{obj.x:.1f}" cy="{obj.y:.1f}" r="{r:.1f}"'
        f' fill="#555" stroke="#222" stroke-width="2"/>',
    ]
    if label:
        parts.append(
            f'<text x="{obj.x:.1f}" y="{obj.y - r - 6:.1f}"'
            f' text-anchor="middle" font-family="{FONT}"'
            f' font-size="13" fill="#222">{escape(label)}</text>'
        )
    return parts


# ── dispatch: choose primitive from RenderHints ───────────────────────────────

def _render_object(obj, scene: SceneGraph) -> list[str]:
    shape = obj.shape or scene.hints.object_shape or "box"
    # Build label: prefer stored label, fall back to mass
    label = obj.label or (f"{obj.mass_kg:g} kg" if obj.mass_kg is not None else "")
    if shape == "sphere" or shape == "ball":
        return _render_sphere(obj, label)
    if shape == "cart":
        return _render_cart(obj, label)
    if shape == "hanging_mass":
        return _render_hanging_mass(obj, label)
    if shape == "projectile":
        return _render_projectile_marker(obj, label)
    return _render_box(obj, label)


# ── surface primitives ────────────────────────────────────────────────────────

def _surface_texture_marks(x1: float, y1: float, x2: float, y2: float,
                            texture: str) -> list[str]:
    """Return hatch marks or dashes overlaid on a surface line."""
    if texture == "rough":
        # Short downward serrations spaced every 24 px along the surface
        parts: list[str] = []
        dx, dy = x2 - x1, y2 - y1
        length = max((dx * dx + dy * dy) ** 0.5, 1.0)
        steps = max(1, int(length / 24))
        ux, uy = dx / length, dy / length      # unit along surface
        nx, ny = -uy, ux                        # normal (points "up" from line)
        for i in range(steps):
            t = (i + 0.5) / steps
            sx = x1 + t * dx
            sy = y1 + t * dy
            parts.append(
                f'<line x1="{sx:.1f}" y1="{sy:.1f}"'
                f' x2="{sx - nx * 8:.1f}" y2="{sy - ny * 8:.1f}"'
                f' stroke="#777" stroke-width="1.5"/>'
            )
        return parts
    if texture == "frictionless":
        # Dashed overlay
        return [
            f'<line x1="{x1:.1f}" y1="{y1:.1f}"'
            f' x2="{x2:.1f}" y2="{y2:.1f}"'
            f' stroke="#aaa" stroke-width="2.5"'
            f' stroke-dasharray="10 6"/>'
        ]
    return []


def _render_surface(surf, texture: str) -> list[str]:
    parts = [
        f'<line x1="{surf.x1:.1f}" y1="{surf.y1:.1f}"'
        f' x2="{surf.x2:.1f}" y2="{surf.y2:.1f}"'
        f' stroke="{surf.stroke}" stroke-width="{surf.stroke_width:.1f}"/>'
    ]
    parts.extend(_surface_texture_marks(surf.x1, surf.y1, surf.x2, surf.y2, texture))
    return parts


# ── force arrows ──────────────────────────────────────────────────────────────

def _force_color(name: str) -> str:
    return FORCE_COLORS.get(name.lower(), _DEFAULT_FORCE_COLOR)


def _render_force(force) -> list[str]:
    color = _force_color(force.name)
    label = escape(force.name.replace("_", " ").title())
    mag_str = f"{force.magnitude_n:.1f} N"
    return [
        f'<line x1="{force.x1:.1f}" y1="{force.y1:.1f}"'
        f' x2="{force.x2:.1f}" y2="{force.y2:.1f}"'
        f' stroke="{color}" stroke-width="3.5"'
        f' stroke-linecap="round" marker-end="url(#arrow)"/>',
        f'<circle cx="{force.x1:.1f}" cy="{force.y1:.1f}"'
        f' r="4" fill="{color}"/>',
        f'<text x="{force.label_x:.1f}" y="{force.label_y:.1f}"'
        f' text-anchor="middle" font-family="{FONT}"'
        f' font-size="13" font-weight="600" fill="{color}">'
        f'{label} = {mag_str}</text>',
    ]


# ── component construction lines ──────────────────────────────────────────────

def _render_components(force) -> list[str]:
    """Dashed horizontal + vertical decomposition lines for the force vector."""
    color = _force_color(force.name)
    return [
        # horizontal component
        f'<line x1="{force.x1:.1f}" y1="{force.y1:.1f}"'
        f' x2="{force.x2:.1f}" y2="{force.y1:.1f}"'
        f' stroke="{color}" stroke-width="1.5" stroke-dasharray="6 4"'
        f' opacity="0.7"/>',
        # vertical component
        f'<line x1="{force.x2:.1f}" y1="{force.y1:.1f}"'
        f' x2="{force.x2:.1f}" y2="{force.y2:.1f}"'
        f' stroke="{color}" stroke-width="1.5" stroke-dasharray="6 4"'
        f' opacity="0.7"/>',
    ]


# ── velocity / acceleration vectors ──────────────────────────────────────────

def _render_velocity_vector(obj, vf) -> list[str]:
    """Draw a blue velocity arrow from object centre in the motion direction."""
    motion = vf.motion_state if vf else "unknown"
    dir_map = {
        "moving_right":       0.0,
        "moving_left":        180.0,
        "moving_up_incline":  45.0,
        "moving_down_incline": -45.0,
        "launched_upward":    60.0,
        "descending":         -90.0,
    }
    if motion not in dir_map:
        return []
    deg = dir_map[motion]
    rad = deg * pi / 180
    length = 60.0
    tx = obj.x + length * cos(rad)
    ty = obj.y - length * sin(rad)
    return [
        f'<line x1="{obj.x:.1f}" y1="{obj.y:.1f}"'
        f' x2="{tx:.1f}" y2="{ty:.1f}"'
        f' stroke="#2196F3" stroke-width="3"'
        f' marker-end="url(#arrow-vel)"/>',
        f'<text x="{tx + 8:.1f}" y="{ty:.1f}"'
        f' font-family="{FONT}" font-size="13"'
        f' font-weight="600" fill="#2196F3">v</text>',
    ]


def _render_acceleration_vector(obj, vf) -> list[str]:
    """Draw an orange acceleration arrow from object centre."""
    motion = vf.motion_state if vf else "unknown"
    dir_map = {
        "accelerating":        0.0,
        "decelerating":        180.0,
        "moving_up_incline":   45.0,
        "moving_down_incline": -45.0,
    }
    if motion not in dir_map:
        return []
    deg = dir_map[motion]
    rad = deg * pi / 180
    length = 55.0
    tx = obj.x + length * cos(rad)
    ty = obj.y - length * sin(rad)
    return [
        f'<line x1="{obj.x:.1f}" y1="{obj.y:.1f}"'
        f' x2="{tx:.1f}" y2="{ty:.1f}"'
        f' stroke="#FF5722" stroke-width="3"'
        f' marker-end="url(#arrow-acc)"/>',
        f'<text x="{tx + 8:.1f}" y="{ty:.1f}"'
        f' font-family="{FONT}" font-size="13"'
        f' font-weight="600" fill="#FF5722">a</text>',
    ]


# ── scenario scene layers ─────────────────────────────────────────────────────

def _incline_background(scene: SceneGraph) -> list[str]:
    result = scene.source_result
    if result is None:
        return []
    angle = float(result.geometry.incline_angle_deg or 0.0)
    rad = angle * pi / 180
    start, length = (120.0, 500.0), 570.0
    end = (start[0] + length * cos(rad), start[1] - length * sin(rad))
    texture = scene.hints.surface_texture
    parts = [
        # Ramp face
        f'<path d="M {start[0]:.1f} {start[1]:.1f}'
        f' L {end[0]:.1f} {end[1]:.1f}"'
        f' stroke="#555" stroke-width="7" stroke-linecap="round"/>',
        # Horizontal baseline
        f'<path d="M {start[0]:.1f} {start[1]:.1f}'
        f' L {end[0]:.1f} {start[1]:.1f}"'
        f' stroke="#bbb" stroke-width="2"/>',
        # Angle arc
        f'<path d="M {start[0]+50:.1f} {start[1]:.1f}'
        f' A 50 50 0 0 0'
        f' {start[0]+50*cos(rad):.1f} {start[1]-50*sin(rad):.1f}"'
        f' fill="none" stroke="#777" stroke-width="2"/>',
        # Angle label
        f'<text x="{start[0]+76:.1f}" y="{start[1]-14:.1f}"'
        f' font-family="{FONT}" font-size="16" fill="#444">'
        f'{angle:g}°</text>',
    ]
    parts.extend(_surface_texture_marks(start[0], start[1], end[0], end[1], texture))
    return parts


def _horizontal_background(scene: SceneGraph) -> list[str]:
    texture = scene.hints.surface_texture
    parts = [
        '<line x1="100" y1="420" x2="800" y2="420"'
        ' stroke="#555" stroke-width="7" stroke-linecap="round"/>',
    ]
    parts.extend(_surface_texture_marks(100, 420, 800, 420, texture))
    return parts


def _atwood_background(scene: SceneGraph) -> list[str]:
    if scene.source_result is None or len(scene.objects) < 2:
        return []
    return [
        # Pulley wheel
        '<circle cx="450" cy="150" r="52"'
        ' fill="none" stroke="#555" stroke-width="5"/>',
        '<circle cx="450" cy="150" r="10"'
        ' fill="#888" stroke="#333" stroke-width="2"/>',
        # Left rope from pulley to left mass
        '<path d="M 398 150 L 350 150 L 350 382"'
        ' fill="none" stroke="#555" stroke-width="4"'
        ' stroke-linecap="round"/>',
        # Right rope from pulley to right mass
        '<path d="M 502 150 L 550 150 L 550 382"'
        ' fill="none" stroke="#555" stroke-width="4"'
        ' stroke-linecap="round"/>',
        # Support mount
        '<rect x="420" y="80" width="60" height="18"'
        ' rx="3" fill="#aaa" stroke="#666" stroke-width="2"/>',
        '<line x1="450" y1="98" x2="450" y2="150"'
        ' stroke="#777" stroke-width="3"/>',
    ]


def _projectile_background(scene: SceneGraph) -> list[str]:
    result = scene.source_result
    solution = scene.source_solution
    if result is None or solution is None:
        return [
            '<line x1="100" y1="490" x2="800" y2="490"'
            ' stroke="#555" stroke-width="4"/>',
        ]
    range_m = float(solution.derived_values.get("range_m") or 1.0)
    height = float(solution.derived_values.get("max_height_m") or 1.0)
    scale = min(620 / max(range_m, 1.0), 280 / max(height, 1.0))
    origin = (130.0, 490.0)
    angle_rad = (result.geometry.projectile_angle_deg or 45.0) * pi / 180
    speed = result.geometry.initial_speed_ms or 1.0

    # Parabolic arc points
    pts: list[str] = []
    for i in range(61):
        x = range_m * i / 60
        cos_a = cos(angle_rad)
        y = x * tan(angle_rad) - (9.8 * x * x) / (2 * speed ** 2 * cos_a ** 2)
        pts.append(
            f"{origin[0] + x * scale:.1f},{origin[1] - y * scale:.1f}"
        )
    # Velocity vector at launch
    vx = origin[0] + 60 * cos(angle_rad)
    vy = origin[1] - 60 * sin(angle_rad)
    return [
        # Ground
        f'<line x1="{origin[0]:.1f}" y1="{origin[1]:.1f}"'
        f' x2="{origin[0] + range_m * scale:.1f}" y2="{origin[1]:.1f}"'
        f' stroke="#555" stroke-width="4"/>',
        # Trajectory arc
        f'<polyline points="{" ".join(pts)}"'
        f' fill="none" stroke="#aaa" stroke-width="2.5"'
        f' stroke-dasharray="8 5"/>',
        # Launch velocity vector
        f'<line x1="{origin[0]:.1f}" y1="{origin[1]:.1f}"'
        f' x2="{vx:.1f}" y2="{vy:.1f}"'
        f' stroke="#2196F3" stroke-width="2.5"'
        f' marker-end="url(#arrow-vel)"/>',
        f'<text x="{vx + 8:.1f}" y="{vy:.1f}"'
        f' font-family="{FONT}" font-size="13"'
        f' font-weight="600" fill="#2196F3">v₀</text>',
    ]


# ── annotations ───────────────────────────────────────────────────────────────

def _render_annotation(ann) -> str:
    return (
        f'<text x="{ann.x:.1f}" y="{ann.y:.1f}"'
        f' text-anchor="{ann.align}" fill="{ann.fill}"'
        f' font-family="{FONT}" font-size="{ann.size:g}">'
        f'{escape(ann.text)}</text>'
    )


# ── diagnostics overlay ───────────────────────────────────────────────────────

def _render_diagnostics(scene: SceneGraph) -> list[str]:
    diag = scene.diagnostics
    if diag is None:
        return []
    parts: list[str] = []
    for idx, (eid, bb) in enumerate(diag.bounding_boxes):
        color = DIAG_COLORS[idx % len(DIAG_COLORS)]
        parts.append(
            f'<rect x="{bb.x:.1f}" y="{bb.y:.1f}"'
            f' width="{bb.w:.1f}" height="{bb.h:.1f}"'
            f' fill="none" stroke="{color}" stroke-width="1.5"'
            f' stroke-dasharray="4 3" data-element-id="{escape(eid)}"/>'
        )
        parts.append(
            f'<text x="{bb.x:.1f}" y="{bb.y - 3:.1f}"'
            f' font-family="{FONT}" font-size="9"'
            f' fill="{color}">{escape(eid)}</text>'
        )
    for warn in diag.layout_warnings:
        parts.append(f'<!-- layout-warning: {escape(warn)} -->')
    return parts


# ── main entry point ──────────────────────────────────────────────────────────

def render_scene(scene: SceneGraph, output_path: str) -> str:
    parts = _svg_start(scene)

    # 1. Scenario background (surface, pulley, trajectory arc, angle mark)
    scenario = scene.scenario_type
    if scenario == "inclined_plane":
        parts.extend(_incline_background(scene))
    elif scenario == "horizontal_friction":
        parts.extend(_horizontal_background(scene))
    elif scenario == "atwood_pulley":
        parts.extend(_atwood_background(scene))
    elif scenario == "projectile_motion":
        parts.extend(_projectile_background(scene))
    else:
        # Generic: draw any surfaces stored in the graph
        texture = scene.hints.surface_texture
        for surf in scene.surfaces:
            parts.extend(_render_surface(surf, texture))

    # 2. Objects (shape chosen via RenderHints / per-object shape field)
    vf = scene.source_result.visual_features if scene.source_result else None
    for obj in scene.objects:
        parts.extend(_render_object(obj, scene))

    # 3. Force arrows
    for force in scene.forces:
        parts.extend(_render_force(force))
        if scene.hints.show_components or scene.intent.emphasize_components:
            parts.extend(_render_components(force))

    # 4. Velocity / acceleration overlay vectors
    if scene.objects:
        primary = scene.objects[0]
        if scene.hints.show_velocity_vector:
            parts.extend(_render_velocity_vector(primary, vf))
        if scene.hints.show_acceleration_vector:
            parts.extend(_render_acceleration_vector(primary, vf))

    # 5. Annotations
    for ann in scene.annotations:
        parts.append(_render_annotation(ann))

    # 6. Diagnostics overlay (bounding boxes + warnings)
    parts.extend(_render_diagnostics(scene))

    parts.append("</svg>")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(p for p in parts if p), encoding="utf-8")
    return str(path)
