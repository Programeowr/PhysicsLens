"""Scene-graph layout for the supported PhysicsLens scenarios.

Responsibilities
----------------
1. Position every scene element (objects, surfaces, force arrows).
2. Clamp force-arrow tips to canvas bounds so no arrow escapes the viewport.
3. Compute label bounding boxes and nudge labels away from collisions.
4. Enforce per-scenario layout invariants (objects inside canvas, arrows
   above minimum visible length, labels outside object bounds).
5. Optionally record bounding boxes and warnings in SceneGraph.diagnostics
   so callers (tests, the debug endpoint) can inspect the layout.

All geometry is in SVG coordinates: x grows right, y grows down.
"""

from __future__ import annotations

from math import cos, hypot, pi, sin
from typing import Optional

from .schema import (
    BoundingBox,
    DiagnosticsData,
    SceneAnnotation,
    SceneForce,
    SceneGraph,
    SceneObject,
)

# ── tuneable constants ────────────────────────────────────────────────────────

# Force-arrow length is scaled so the largest force reaches this many pixels.
_MAX_ARROW_PX = 140.0
# Arrows shorter than this are invisible; we clamp up to this minimum.
_MIN_ARROW_PX = 36.0
# Margin kept between every element and the canvas edge.
_CANVAS_MARGIN = 10.0
# Extra clearance between a label and the nearest object box.
_LABEL_PADDING = 6.0
# Estimated character width (px) for label collision math.
_CHAR_W = 7.5
# Estimated line height (px) for label collision math.
_LINE_H = 16.0
# Candidates tried when nudging a label off a collision (px offsets).
_NUDGE_OFFSETS: list[tuple[float, float]] = [
    (0, -20), (0, 20), (-30, 0), (30, 0),
    (-30, -20), (30, -20), (-30, 20), (30, 20),
    (0, -36), (0, 36),
]


# ── helpers ───────────────────────────────────────────────────────────────────

def _canvas_box(scene: SceneGraph, margin: float = _CANVAS_MARGIN) -> BoundingBox:
    return BoundingBox(
        x=margin, y=margin,
        w=scene.canvas.width - 2 * margin,
        h=scene.canvas.height - 2 * margin,
    )


def _force_scale(scene: SceneGraph) -> float:
    max_mag = max((f.magnitude_n for f in scene.forces), default=1.0)
    return _MAX_ARROW_PX / max(max_mag, 1.0)


def _compute_arrow(
    anchor: tuple[float, float],
    direction_deg: float,
    magnitude_n: float,
    scale: float,
    canvas: BoundingBox,
) -> tuple[float, float, float, float]:
    """Return (x1, y1, x2, y2) with tip clamped inside *canvas*.

    The arrow length is at least _MIN_ARROW_PX so it is always visible.
    """
    rad = direction_deg * pi / 180
    raw_len = max(_MIN_ARROW_PX, magnitude_n * scale)
    ax, ay = anchor
    tx = ax + raw_len * cos(rad)
    ty = ay - raw_len * sin(rad)   # SVG y-axis is flipped

    # Clamp tip to canvas
    tx, ty = canvas.clamp_point(tx, ty, margin=_CANVAS_MARGIN)

    # Re-check actual length after clamping — enforce minimum
    actual = hypot(tx - ax, ty - ay)
    if actual < _MIN_ARROW_PX:
        # Scale tip away from anchor along the same direction to meet minimum
        scale_factor = _MIN_ARROW_PX / max(actual, 1e-6)
        tx = ax + (tx - ax) * scale_factor
        ty = ay + (ty - ay) * scale_factor
        tx, ty = canvas.clamp_point(tx, ty, margin=_CANVAS_MARGIN)

    return ax, ay, tx, ty


def _label_pos_default(tx: float, ty: float, direction_deg: float) -> tuple[float, float]:
    """Default label position: offset slightly beyond the arrow tip."""
    rad = direction_deg * pi / 180
    return tx + 14 * cos(rad), ty - 14 * sin(rad) - 4


def _label_bbox(lx: float, ly: float, text: str) -> BoundingBox:
    w = len(text) * _CHAR_W
    return BoundingBox(x=lx - w / 2, y=ly - _LINE_H, w=w, h=_LINE_H)


def _resolve_label(
    lx: float,
    ly: float,
    label_text: str,
    occupied: list[BoundingBox],
    canvas: BoundingBox,
) -> tuple[float, float]:
    """Nudge (lx, ly) until its bbox no longer overlaps any occupied box.

    Tries _NUDGE_OFFSETS in order; returns the first non-colliding position.
    Falls back to the last candidate if all collide.
    """
    bb = _label_bbox(lx, ly, label_text)
    if not any(bb.overlaps(o, padding=_LABEL_PADDING) for o in occupied):
        if canvas.contains(bb.cx, bb.cy):
            return lx, ly

    best: tuple[float, float] = (lx, ly)
    for dx, dy in _NUDGE_OFFSETS:
        cx2, cy2 = lx + dx, ly + dy
        bb2 = _label_bbox(cx2, cy2, label_text)
        if not any(bb2.overlaps(o, padding=_LABEL_PADDING) for o in occupied):
            if canvas.contains(bb2.cx, bb2.cy):
                return cx2, cy2
        best = (cx2, cy2)   # track last; return it if nothing clean found
    return best


def _assign_ids(scene: SceneGraph) -> None:
    """Assign stable element_id values where not already set."""
    for i, obj in enumerate(scene.objects):
        if not obj.element_id:
            obj.element_id = f"obj-{obj.id}"
    for i, surf in enumerate(scene.surfaces):
        if not surf.element_id:
            surf.element_id = f"surf-{surf.kind}-{i}"
    for i, force in enumerate(scene.forces):
        if not force.element_id:
            force.element_id = f"force-{force.name}-{i}"
    for i, ann in enumerate(scene.annotations):
        if not ann.element_id:
            ann.element_id = f"ann-{i}"


def _check_invariants(scene: SceneGraph, canvas: BoundingBox) -> list[str]:
    """Return a list of human-readable invariant violations (empty = all clear)."""
    warnings: list[str] = []
    for obj in scene.objects:
        bb = obj.bbox()
        if bb.x < canvas.x or bb.y < canvas.y or bb.x2 > canvas.x2 or bb.y2 > canvas.y2:
            warnings.append(
                f"{obj.element_id}: object bbox {bb} outside canvas {canvas}"
            )
    for force in scene.forces:
        length = force.arrow_length()
        if length < _MIN_ARROW_PX - 1:     # 1 px tolerance
            warnings.append(
                f"{force.element_id}: arrow length {length:.1f} px < minimum {_MIN_ARROW_PX} px"
            )
        if not canvas.contains(force.x2, force.y2):
            warnings.append(
                f"{force.element_id}: tip ({force.x2:.1f},{force.y2:.1f}) outside canvas"
            )
    obj_boxes = [obj.bbox() for obj in scene.objects]
    for force in scene.forces:
        lb = force.label_bbox(_CHAR_W, _LINE_H)
        if not canvas.contains(lb.cx, lb.cy):
            warnings.append(
                f"{force.element_id}: label centre outside canvas"
            )
        for ob in obj_boxes:
            if lb.overlaps(ob, padding=_LABEL_PADDING):
                warnings.append(
                    f"{force.element_id}: label overlaps object {ob}"
                )
    return warnings


def _build_diagnostics(scene: SceneGraph, warnings: list[str]) -> DiagnosticsData:
    diag = DiagnosticsData(layout_warnings=warnings)
    for obj in scene.objects:
        diag.bounding_boxes.append((obj.element_id, obj.bbox()))
    for force in scene.forces:
        diag.bounding_boxes.append((force.element_id, force.label_bbox(_CHAR_W, _LINE_H)))
    for ann in scene.annotations:
        diag.bounding_boxes.append((ann.element_id, ann.bbox()))
    return diag


# ── per-scenario positioning ──────────────────────────────────────────────────

def _layout_inclined_plane(scene: SceneGraph, canvas: BoundingBox, scale: float) -> None:
    angle = (
        scene.source_result.geometry.incline_angle_deg or 0.0
        if scene.source_result else 0.0
    )
    rad = angle * pi / 180
    start = (120.0, 500.0)
    length = 570.0
    end = (start[0] + length * cos(rad), start[1] - length * sin(rad))
    cx = start[0] + 300 * cos(rad) - 22 * sin(rad)
    cy = start[1] - 300 * sin(rad) - 22 * cos(rad)

    if scene.objects:
        obj = scene.objects[0]
        obj.x, obj.y = cx, cy
        obj.width, obj.height = 88.0, 56.0
        obj.rotation_deg = -angle

    if scene.surfaces:
        s = scene.surfaces[0]
        s.x1, s.y1 = start
        s.x2, s.y2 = end

    occupied = [scene.objects[0].bbox()] if scene.objects else []
    for force in scene.forces:
        x1, y1, x2, y2 = _compute_arrow((cx, cy), force.direction_deg, force.magnitude_n, scale, canvas)
        force.x1, force.y1, force.x2, force.y2 = x1, y1, x2, y2
        label_text = _force_label_text(force)
        lx, ly = _label_pos_default(x2, y2, force.direction_deg)
        lx, ly = _resolve_label(lx, ly, label_text, occupied, canvas)
        force.label_x, force.label_y = lx, ly
        occupied.append(_label_bbox(lx, ly, label_text))


def _layout_horizontal_friction(scene: SceneGraph, canvas: BoundingBox, scale: float) -> None:
    anchor = (450.0, 365.0)
    if scene.objects:
        obj = scene.objects[0]
        obj.x, obj.y = anchor
        obj.width, obj.height = 90.0, 60.0

    if scene.surfaces:
        s = scene.surfaces[0]
        s.x1, s.y1 = 100.0, 420.0
        s.x2, s.y2 = 800.0, 420.0

    occupied = [scene.objects[0].bbox()] if scene.objects else []
    for force in scene.forces:
        x1, y1, x2, y2 = _compute_arrow(anchor, force.direction_deg, force.magnitude_n, scale, canvas)
        force.x1, force.y1, force.x2, force.y2 = x1, y1, x2, y2
        label_text = _force_label_text(force)
        lx, ly = _label_pos_default(x2, y2, force.direction_deg)
        lx, ly = _resolve_label(lx, ly, label_text, occupied, canvas)
        force.label_x, force.label_y = lx, ly
        occupied.append(_label_bbox(lx, ly, label_text))


def _layout_atwood_pulley(scene: SceneGraph, canvas: BoundingBox, scale: float) -> None:
    anchors: dict[str, tuple[float, float]] = {}
    if len(scene.objects) >= 2:
        anchors = {
            scene.objects[0].id: (350.0, 410.0),
            scene.objects[1].id: (550.0, 410.0),
        }
    for obj in scene.objects[:2]:
        x, y = anchors.get(obj.id, (450.0, 410.0))
        obj.x, obj.y = x, y
        obj.width, obj.height = 76.0, 56.0

    occupied = [obj.bbox() for obj in scene.objects[:2]]
    for force in scene.forces:
        anchor = anchors.get(force.anchor_id, (450.0, 410.0))
        x1, y1, x2, y2 = _compute_arrow(anchor, force.direction_deg, force.magnitude_n, scale, canvas)
        force.x1, force.y1, force.x2, force.y2 = x1, y1, x2, y2
        label_text = _force_label_text(force)
        lx, ly = _label_pos_default(x2, y2, force.direction_deg)
        lx, ly = _resolve_label(lx, ly, label_text, occupied, canvas)
        force.label_x, force.label_y = lx, ly
        occupied.append(_label_bbox(lx, ly, label_text))


def _layout_projectile(scene: SceneGraph, canvas: BoundingBox, scale: float) -> None:
    anchor = (350.0, 370.0)
    if scene.objects:
        obj = scene.objects[0]
        obj.x, obj.y = anchor
        obj.width, obj.height = 22.0, 22.0

    if scene.surfaces:
        s = scene.surfaces[0]
        s.x1, s.y1 = 100.0, 490.0
        s.x2, s.y2 = 800.0, 490.0

    occupied = [scene.objects[0].bbox()] if scene.objects else []
    for force in scene.forces:
        x1, y1, x2, y2 = _compute_arrow(anchor, force.direction_deg, force.magnitude_n, scale, canvas)
        force.x1, force.y1, force.x2, force.y2 = x1, y1, x2, y2
        label_text = _force_label_text(force)
        lx, ly = _label_pos_default(x2, y2, force.direction_deg)
        lx, ly = _resolve_label(lx, ly, label_text, occupied, canvas)
        force.label_x, force.label_y = lx, ly
        occupied.append(_label_bbox(lx, ly, label_text))


def _layout_generic(scene: SceneGraph, canvas: BoundingBox, scale: float) -> None:
    anchor = (450.0, 330.0)
    if scene.objects:
        obj = scene.objects[0]
        obj.x, obj.y = anchor
        obj.width, obj.height = 90.0, 60.0

    occupied = [scene.objects[0].bbox()] if scene.objects else []
    for force in scene.forces:
        x1, y1, x2, y2 = _compute_arrow(anchor, force.direction_deg, force.magnitude_n, scale, canvas)
        force.x1, force.y1, force.x2, force.y2 = x1, y1, x2, y2
        label_text = _force_label_text(force)
        lx, ly = _label_pos_default(x2, y2, force.direction_deg)
        lx, ly = _resolve_label(lx, ly, label_text, occupied, canvas)
        force.label_x, force.label_y = lx, ly
        occupied.append(_label_bbox(lx, ly, label_text))


def _force_label_text(force: SceneForce) -> str:
    label = force.name.replace("_", " ").title()
    return f"{label} = {force.magnitude_n:.1f} N"


# ── public entry point ────────────────────────────────────────────────────────

def layout_scene(scene: SceneGraph, diagnostics: bool = False) -> SceneGraph:
    """Position all scene elements; optionally populate scene.diagnostics."""
    _assign_ids(scene)
    canvas = _canvas_box(scene)
    scale = _force_scale(scene)

    dispatch = {
        "inclined_plane":     _layout_inclined_plane,
        "horizontal_friction": _layout_horizontal_friction,
        "atwood_pulley":      _layout_atwood_pulley,
        "projectile_motion":  _layout_projectile,
    }
    handler = dispatch.get(scene.scenario_type or "", _layout_generic)
    handler(scene, canvas, scale)

    warnings = _check_invariants(scene, canvas)
    if diagnostics:
        scene.diagnostics = _build_diagnostics(scene, warnings)
    return scene
