"""
Base SVG drawing utilities shared across all diagram generators.

Provides common SVG elements like arrowheads, labels, coordinate helpers,
and the standard SVG wrapper with defs.
"""

import math
from dataclasses import dataclass


@dataclass
class Point:
    """A 2D point."""
    x: float
    y: float

    def offset(self, dx: float, dy: float) -> "Point":
        return Point(self.x + dx, self.y + dy)


# ── Color palette for force types ────────────────────────────────────────

FORCE_COLORS = {
    "gravity": "#3B82F6",        # blue
    "normal": "#22C55E",          # green
    "friction_force": "#F97316",  # orange
    "applied": "#EF4444",         # red
    "tension": "#A855F7",         # purple
    "spring": "#EAB308",          # yellow
}

DEFAULT_FORCE_COLOR = "#6B7280"  # gray


def get_force_color(force_type: str) -> str:
    """Get the color for a given force type."""
    return FORCE_COLORS.get(force_type, DEFAULT_FORCE_COLOR)


# ── Force labels ─────────────────────────────────────────────────────────

FORCE_LABELS = {
    "gravity": "mg",
    "normal": "N",
    "friction_force": "f",
    "applied": "F",
    "tension": "T",
    "spring": "Fs",
}


def get_force_label(force_type: str, magnitude: float | None = None) -> str:
    """Get a display label for a force."""
    base = FORCE_LABELS.get(force_type, force_type)
    if magnitude is not None:
        return f"{base}={magnitude:.0f}N"
    return base


# ── SVG building blocks ─────────────────────────────────────────────────

SVG_DEFS = """
    <defs>
        <marker id="arrowhead-blue" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#3B82F6"/>
        </marker>
        <marker id="arrowhead-green" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#22C55E"/>
        </marker>
        <marker id="arrowhead-orange" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#F97316"/>
        </marker>
        <marker id="arrowhead-red" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#EF4444"/>
        </marker>
        <marker id="arrowhead-purple" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#A855F7"/>
        </marker>
        <marker id="arrowhead-yellow" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#EAB308"/>
        </marker>
        <marker id="arrowhead-gray" markerWidth="10" markerHeight="7"
                refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#6B7280"/>
        </marker>
    </defs>
"""

COLOR_TO_MARKER = {
    "#3B82F6": "arrowhead-blue",
    "#22C55E": "arrowhead-green",
    "#F97316": "arrowhead-orange",
    "#EF4444": "arrowhead-red",
    "#A855F7": "arrowhead-purple",
    "#EAB308": "arrowhead-yellow",
    "#6B7280": "arrowhead-gray",
}


def svg_arrow(start: Point, end: Point, color: str, label: str) -> str:
    """Generate an SVG arrow with a label."""
    marker_id = COLOR_TO_MARKER.get(color, "arrowhead-gray")

    # Position label slightly offset from the end of the arrow
    label_x = end.x + 8
    label_y = end.y + 5

    return f"""
    <line x1="{start.x:.1f}" y1="{start.y:.1f}"
          x2="{end.x:.1f}" y2="{end.y:.1f}"
          stroke="{color}" stroke-width="2.5"
          marker-end="url(#{marker_id})"/>
    <text x="{label_x:.1f}" y="{label_y:.1f}"
          font-size="13" font-family="Arial, sans-serif"
          fill="{color}" font-weight="bold">{label}</text>
    """


def svg_block(center: Point, size: float, label: str, angle: float = 0) -> str:
    """Generate an SVG rectangle (block) with an optional rotation and label."""
    x = center.x - size / 2
    y = center.y - size / 2
    transform = ""
    if angle != 0:
        transform = f'transform="rotate({-angle} {center.x:.1f} {center.y:.1f})"'

    return f"""
    <rect x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}"
          fill="#94A3B8" stroke="#475569" stroke-width="2" rx="3" {transform}/>
    <text x="{center.x:.1f}" y="{center.y + 5:.1f}"
          font-size="14" font-family="Arial, sans-serif"
          fill="white" text-anchor="middle" font-weight="bold"
          {transform}>{label}</text>
    """


def svg_ground(x1: float, y1: float, x2: float, y2: float) -> str:
    """Generate ground hatching beneath a surface line."""
    hatches = ""
    length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    num_hatches = int(length / 15)
    for i in range(num_hatches + 1):
        t = i / max(num_hatches, 1)
        hx = x1 + t * (x2 - x1)
        hy = y1 + t * (y2 - y1)
        hatches += f'<line x1="{hx:.1f}" y1="{hy:.1f}" x2="{hx - 8:.1f}" y2="{hy + 12:.1f}" stroke="#94A3B8" stroke-width="1"/>\n'

    return f"""
    <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"
          stroke="#334155" stroke-width="3"/>
    {hatches}
    """


def svg_wrap(content: str, width: int = 650, height: int = 500, bg_color: str = "#FFFFFF") -> str:
    """Wrap SVG content in the standard SVG element with defs."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {width} {height}">
    <rect width="{width}" height="{height}" fill="{bg_color}"/>
    {SVG_DEFS}
    {content}
</svg>"""
