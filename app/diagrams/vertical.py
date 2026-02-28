"""
Vertical scenario diagram generator.

Draws objects in vertical scenarios like elevators, hanging objects,
and scales, with gravity and normal/tension force arrows.
"""

from app.models import ParsedPhysicsProblem
from app.diagrams.base import (
    Point, svg_arrow, svg_block, svg_wrap,
    get_force_color, get_force_label,
)


ARROW_LENGTH = 80


def generate_vertical_diagram(data: ParsedPhysicsProblem) -> str:
    """Generate SVG for vertical scenarios (elevator, hanging objects)."""
    obj = data.objects[0]
    mass = obj.mass or 1

    width, height = 650, 550

    # Draw elevator box
    elev_x, elev_y = 175, 80
    elev_w, elev_h = 300, 380

    content = f"""
    <rect x="{elev_x}" y="{elev_y}" width="{elev_w}" height="{elev_h}"
          fill="#F8FAFC" stroke="#334155" stroke-width="3" rx="5"/>
    """

    # Elevator floor
    floor_y = elev_y + elev_h - 40
    content += f"""
    <line x1="{elev_x}" y1="{floor_y}" x2="{elev_x + elev_w}" y2="{floor_y}"
          stroke="#64748B" stroke-width="2" stroke-dasharray="6,3"/>
    """

    # Elevator label
    content += f'<text x="{elev_x + elev_w / 2}" y="{elev_y + 30}" font-size="14" font-family="Arial" fill="#64748B" text-anchor="middle">Elevator</text>'

    # Acceleration arrow on the elevator
    arr_x = elev_x + elev_w + 30
    if data.acceleration:
        accel = data.acceleration
        accel_label = f"a={accel.magnitude}m/s²"
        is_up = accel.direction.value in ("up", "vertical_up")
        if is_up:
            y1, y2 = elev_y + elev_h, elev_y + 60
            accel_label += " ↑"
        else:
            y1, y2 = elev_y + 60, elev_y + elev_h
            accel_label += " ↓"
    else:
        y1, y2 = elev_y + elev_h, elev_y + 60
        accel_label = "acceleration"
    content += f"""
    <line x1="{arr_x}" y1="{y1}" x2="{arr_x}" y2="{y2}"
          stroke="#94A3B8" stroke-width="2" stroke-dasharray="5,3"
          marker-end="url(#arrowhead-gray)"/>
    <text x="{arr_x + 10}" y="{elev_y + elev_h / 2}" font-size="13"
          font-family="Arial" fill="#94A3B8" writing-mode="tb">{accel_label}</text>
    """

    # Block (person/object) on elevator floor
    block_size = 60
    cx = elev_x + elev_w / 2
    cy = floor_y - block_size / 2 - 5
    block_center = Point(cx, cy)

    label = f"{mass:.0f}kg" if mass else "m"
    content += svg_block(block_center, block_size, label)

    # Scale / platform under block
    scale_y = floor_y - 5
    scale_w = block_size + 30
    content += f"""
    <rect x="{cx - scale_w / 2}" y="{scale_y}" width="{scale_w}" height="8"
          fill="#CBD5E1" stroke="#94A3B8" stroke-width="1" rx="2"/>
    """

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

        elif force.type.value == "tension":
            end = block_center.offset(0, -ARROW_LENGTH)
            content += svg_arrow(block_center, end, color, flabel)

        elif force.type.value == "applied":
            if force.direction.value in ("up", "vertical_up"):
                end = block_center.offset(0, -ARROW_LENGTH)
            else:
                end = block_center.offset(0, ARROW_LENGTH)
            content += svg_arrow(block_center, end, color, flabel)

    # Title
    content += f'<text x="{width / 2}" y="{height - 20}" font-size="16" font-family="Arial" fill="#1E293B" text-anchor="middle" font-weight="bold">Free Body Diagram — Vertical / Elevator</text>'

    return svg_wrap(content, width, height)
