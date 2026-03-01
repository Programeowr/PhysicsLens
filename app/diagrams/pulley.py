"""
Pulley system (Atwood machine) diagram generator.

Draws two masses connected by a rope over a pulley with
gravity and tension force arrows on each mass.
"""

import math

from app.models import ParsedPhysicsProblem
from app.diagrams.base import (
    Point, svg_arrow, svg_block, svg_wrap,
    get_force_color, get_force_label,
)


ARROW_LENGTH = 70


def generate_pulley_diagram(data: ParsedPhysicsProblem) -> str:
    """Generate SVG for an Atwood machine (two masses over a pulley)."""
    # Get the two masses (ignore rope objects)
    mass_objects = [o for o in data.objects if o.type.value != "rope"]

    if len(mass_objects) < 2:
        # Fallback: single mass on pulley
        mass_objects = mass_objects + mass_objects  # duplicate

    m1 = mass_objects[0]
    m2 = mass_objects[1]

    width, height = 650, 550

    # Pulley position (top center)
    pulley_cx, pulley_cy = width / 2, 80
    pulley_r = 30

    # Support structure
    content = f"""
    <line x1="{pulley_cx}" y1="20" x2="{pulley_cx}" y2="{pulley_cy - pulley_r}"
          stroke="#334155" stroke-width="4"/>
    <line x1="{pulley_cx - 60}" y1="20" x2="{pulley_cx + 60}" y2="20"
          stroke="#334155" stroke-width="4"/>
    """

    # Pulley wheel
    content += f"""
    <circle cx="{pulley_cx}" cy="{pulley_cy}" r="{pulley_r}"
            fill="#E2E8F0" stroke="#475569" stroke-width="3"/>
    <circle cx="{pulley_cx}" cy="{pulley_cy}" r="5"
            fill="#475569"/>
    """

    # Rope and mass positions
    left_x = pulley_cx - pulley_r
    right_x = pulley_cx + pulley_r

    left_mass_y = 280
    right_mass_y = 320  # slightly lower for visual clarity

    block_size = 55

    # Ropes from pulley to masses
    content += f"""
    <line x1="{left_x}" y1="{pulley_cy}" x2="{left_x}" y2="{left_mass_y - block_size / 2}"
          stroke="#64748B" stroke-width="2"/>
    <line x1="{right_x}" y1="{pulley_cy}" x2="{right_x}" y2="{right_mass_y - block_size / 2}"
          stroke="#64748B" stroke-width="2"/>
    """

    # Rope over pulley arc
    content += f"""
    <path d="M {left_x} {pulley_cy} A {pulley_r} {pulley_r} 0 0 1 {right_x} {pulley_cy}"
          fill="none" stroke="#64748B" stroke-width="2"/>
    """

    # Left mass (m1)
    m1_center = Point(left_x, left_mass_y)
    m1_label = f"{m1.mass:.0f}kg" if m1.mass else "m₁"
    content += svg_block(m1_center, block_size, m1_label)

    # Right mass (m2)
    m2_center = Point(right_x, right_mass_y)
    m2_label = f"{m2.mass:.0f}kg" if m2.mass else "m₂"
    content += svg_block(m2_center, block_size, m2_label)

    # Draw forces on each mass
    for force in data.forces:
        color = get_force_color(force.type.value)
        flabel = get_force_label(force.type.value, force.magnitude)

        # Determine which mass this force applies to
        if force.object_id == m1.id:
            center = m1_center
        elif force.object_id == m2.id:
            center = m2_center
        else:
            continue

        if force.type.value == "gravity":
            end = center.offset(0, ARROW_LENGTH)
            content += svg_arrow(center, end, color, flabel)

        elif force.type.value == "tension":
            end = center.offset(0, -ARROW_LENGTH)
            content += svg_arrow(center, end, color, flabel)

    # Mass labels below blocks
    content += f'<text x="{left_x}" y="{left_mass_y + block_size / 2 + 20}" font-size="13" font-family="Arial" fill="#475569" text-anchor="middle">m₁</text>'
    content += f'<text x="{right_x}" y="{right_mass_y + block_size / 2 + 20}" font-size="13" font-family="Arial" fill="#475569" text-anchor="middle">m₂</text>'

    # Title
    content += f'<text x="{width / 2}" y="{height - 20}" font-size="16" font-family="Arial" fill="#1E293B" text-anchor="middle" font-weight="bold">Free Body Diagram — Atwood Machine</text>'

    return svg_wrap(content, width, height)
