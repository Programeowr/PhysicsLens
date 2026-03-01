"""
Inclined plane diagram generator.

Draws a block on an inclined surface with force arrows for
gravity, normal force, friction, and applied forces.
"""

import math

from app.models import ParsedPhysicsProblem
from app.diagrams.base import (
    Point, svg_arrow, svg_block, svg_ground, svg_wrap,
    get_force_color, get_force_label,
)


ARROW_LENGTH = 80


def generate_incline_diagram(data: ParsedPhysicsProblem) -> str:
    """Generate SVG for a block on an inclined plane."""
    # Extract parameters
    surface = data.surfaces[0]
    obj = data.objects[0]
    angle = surface.angle or 30
    mass = obj.mass or 1
    angle_rad = math.radians(angle)

    # Canvas dimensions
    width, height = 650, 500

    # Incline geometry
    base_len = 350
    x1, y1 = 80, 420  # bottom-left of incline
    x2 = x1 + base_len
    y2 = y1 - base_len * math.tan(angle_rad)

    # Block center on the incline (at ~40% up)
    t = 0.4
    cx = x1 + t * (x2 - x1)
    cy = y1 + t * (y2 - y1)
    block_center = Point(cx, cy)
    block_size = 55

    # Draw incline surface
    content = svg_ground(x1, y1, x2, y2)

    # Draw horizontal baseline
    content += f'<line x1="{x1}" y1="{y1}" x2="{x1 + base_len}" y2="{y1}" stroke="#CBD5E1" stroke-width="1" stroke-dasharray="6,4"/>'

    # Draw angle arc
    arc_r = 50
    arc_end_x = x1 + arc_r
    arc_end_y = y1
    arc_top_x = x1 + arc_r * math.cos(angle_rad)
    arc_top_y = y1 - arc_r * math.sin(angle_rad)
    content += f'<path d="M {arc_end_x:.1f} {arc_end_y:.1f} A {arc_r} {arc_r} 0 0 0 {arc_top_x:.1f} {arc_top_y:.1f}" fill="none" stroke="#64748B" stroke-width="1.5"/>'
    # Angle label
    label_x = x1 + (arc_r + 15) * math.cos(angle_rad / 2)
    label_y = y1 - (arc_r + 15) * math.sin(angle_rad / 2)
    content += f'<text x="{label_x:.1f}" y="{label_y:.1f}" font-size="14" font-family="Arial" fill="#475569">{angle}°</text>'

    # Draw block
    label = f"{mass:.0f}kg" if mass else "m"
    content += svg_block(block_center, block_size, label, angle=angle)

    # Draw force arrows
    for force in data.forces:
        color = get_force_color(force.type.value)
        flabel = get_force_label(force.type.value, force.magnitude)

        if force.type.value == "gravity":
            end = block_center.offset(0, ARROW_LENGTH)
            content += svg_arrow(block_center, end, color, flabel)

        elif force.type.value == "normal":
            # Perpendicular to incline surface, pointing away
            nx = -math.sin(angle_rad) * ARROW_LENGTH
            ny = -math.cos(angle_rad) * ARROW_LENGTH
            end = block_center.offset(nx, ny)
            content += svg_arrow(block_center, end, color, flabel)

        elif force.type.value == "friction_force":
            # Along incline, opposing motion (up the incline)
            fx = -math.cos(angle_rad) * ARROW_LENGTH * 0.7
            fy = math.sin(angle_rad) * ARROW_LENGTH * 0.7
            end = block_center.offset(fx, fy)
            content += svg_arrow(block_center, end, color, flabel)

        elif force.type.value == "applied":
            if force.direction.value in ("up_along_plane",):
                ax = math.cos(angle_rad) * ARROW_LENGTH
                ay = -math.sin(angle_rad) * ARROW_LENGTH
            else:
                ax = -math.cos(angle_rad) * ARROW_LENGTH
                ay = math.sin(angle_rad) * ARROW_LENGTH
            end = block_center.offset(ax, ay)
            content += svg_arrow(block_center, end, color, flabel)

        elif force.type.value == "tension":
            # Tension along the plane upward
            tx = math.cos(angle_rad) * ARROW_LENGTH
            ty = -math.sin(angle_rad) * ARROW_LENGTH
            end = block_center.offset(tx, ty)
            content += svg_arrow(block_center, end, color, flabel)

    # Title
    content += f'<text x="{width / 2}" y="30" font-size="16" font-family="Arial" fill="#1E293B" text-anchor="middle" font-weight="bold">Free Body Diagram — Inclined Plane</text>'

    return svg_wrap(content, width, height)
