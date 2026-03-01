"""
Horizontal surface diagram generator.

Draws a block on a flat surface with force arrows for
gravity, normal force, friction, and applied forces.
"""

from app.models import ParsedPhysicsProblem
from app.diagrams.base import (
    Point, svg_arrow, svg_block, svg_ground, svg_wrap,
    get_force_color, get_force_label,
)


ARROW_LENGTH = 80


def generate_horizontal_diagram(data: ParsedPhysicsProblem) -> str:
    """Generate SVG for a block on a horizontal surface."""
    obj = data.objects[0]
    mass = obj.mass or 1

    width, height = 650, 450

    # Ground line
    ground_y = 320
    content = svg_ground(50, ground_y, 600, ground_y)

    # Block sitting on ground
    block_size = 60
    cx, cy = width / 2, ground_y - block_size / 2
    block_center = Point(cx, cy)

    label = f"{mass:.0f}kg" if mass else "m"
    content += svg_block(block_center, block_size, label)

    # Draw force arrows
    for force in data.forces:
        color = get_force_color(force.type.value)
        flabel = get_force_label(force.type.value, force.magnitude)

        if force.type.value == "gravity":
            end = block_center.offset(0, ARROW_LENGTH)
            content += svg_arrow(block_center, end, color, flabel)

        elif force.type.value == "normal":
            end = block_center.offset(0, -ARROW_LENGTH)
            content += svg_arrow(block_center, end, color, flabel)

        elif force.type.value == "applied":
            if force.direction.value in ("left",):
                end = block_center.offset(-ARROW_LENGTH, 0)
            else:  # right or default
                end = block_center.offset(ARROW_LENGTH, 0)
            content += svg_arrow(block_center, end, color, flabel)

        elif force.type.value == "friction_force":
            if force.direction.value in ("right",):
                end = block_center.offset(ARROW_LENGTH * 0.7, 0)
            else:  # left or default
                end = block_center.offset(-ARROW_LENGTH * 0.7, 0)
            content += svg_arrow(block_center, end, color, flabel)

        elif force.type.value == "tension":
            if force.direction.value in ("left",):
                end = block_center.offset(-ARROW_LENGTH, 0)
            else:
                end = block_center.offset(ARROW_LENGTH, 0)
            content += svg_arrow(block_center, end, color, flabel)

    # Title
    content += f'<text x="{width / 2}" y="30" font-size="16" font-family="Arial" fill="#1E293B" text-anchor="middle" font-weight="bold">Free Body Diagram — Horizontal Surface</text>'

    return svg_wrap(content, width, height)
