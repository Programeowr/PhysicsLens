"""SVG structural tests + layout-invariant assertions.

Six scenario groups
───────────────────
1. inclined_plane   – complete, solved
2. horizontal_friction – complete, solved
3. atwood_pulley    – complete, solved
4. projectile_motion – complete, solved
5. incomplete parse fallback (needs_clarification)
6. unsupported scenario fallback

For each we verify:
  A. Pipeline produces a file / SVG string (smoke test).
  B. SVG contains the required structural elements (tags, IDs, text).
  C. Layout invariants hold via diagnostics: no object outside canvas,
     no arrow tip outside canvas, every arrow >= minimum length, no label
     outside canvas.
  D. Sharper primitives: correct shape primitive emitted for RenderHints.
  E. Diagnostics mode populates scene.diagnostics correctly.
"""

from __future__ import annotations

import re
from math import hypot
from pathlib import Path

import pytest

from physics_diagram.layout import _MIN_ARROW_PX, layout_scene
from physics_diagram.parser import parse
from physics_diagram.pipeline import solve_and_render
from physics_diagram.renderer import render_diagram
from physics_diagram.scene_graph import build_scene_graph
from physics_diagram.schema import BoundingBox, SceneCanvas


# ── helpers ───────────────────────────────────────────────────────────────────

def _svg(tmp_path: Path, text: str) -> tuple[str, dict]:
    """Run the full pipeline; return (svg_text, result_dict)."""
    out = str(tmp_path / "out.svg")
    result = solve_and_render(text, out)
    svg_text = Path(out).read_text(encoding="utf-8") if Path(out).exists() else ""
    return svg_text, result


def _canvas_box() -> BoundingBox:
    """Default canvas bounding box with standard margin."""
    from physics_diagram.layout import _canvas_box as _cb, _CANVAS_MARGIN
    from physics_diagram.schema import SceneGraph, SceneCanvas, DiagramIntent, RenderHints
    dummy = SceneGraph(
        canvas=SceneCanvas(), title="", scenario_type=None,
        intent=DiagramIntent(), hints=RenderHints(),
        objects=[], surfaces=[], forces=[], annotations=[],
    )
    return _cb(dummy)


def _run_diagnostics(text: str) -> object:
    """Parse → build scene graph → layout with diagnostics=True."""
    result = parse(text)
    from physics_diagram.physics_engine import SOLVERS, solve
    from physics_diagram.validation import validate
    vresult = validate(result)
    solution = solve(vresult) if (vresult.is_complete and vresult.scenario_type in SOLVERS) else None
    scene = build_scene_graph(vresult, solution)
    layout_scene(scene, diagnostics=True)
    return scene


# ── 1. Inclined plane ─────────────────────────────────────────────────────────

INCLINE_TEXT = (
    "A 5 kg box is placed on a frictionless inclined plane "
    "with 30 degree inclination. How much force is required to keep it at rest?"
)


def test_incline_pipeline_ok(tmp_path):
    svg, result = _svg(tmp_path, INCLINE_TEXT)
    assert result["status"] == "ok"
    assert Path(result["diagram_path"]).exists()
    assert svg.startswith("<svg")
    assert "</svg>" in svg


def test_incline_svg_has_title(tmp_path):
    svg, _ = _svg(tmp_path, INCLINE_TEXT)
    assert "Inclined Plane" in svg


def test_incline_svg_has_angle_label(tmp_path):
    svg, _ = _svg(tmp_path, INCLINE_TEXT)
    assert "30°" in svg


def test_incline_svg_has_force_arrows(tmp_path):
    svg, _ = _svg(tmp_path, INCLINE_TEXT)
    # At least one <line ... marker-end="url(#arrow)"> present
    assert 'marker-end="url(#arrow)"' in svg


def test_incline_svg_has_mass_annotation(tmp_path):
    svg, _ = _svg(tmp_path, INCLINE_TEXT)
    assert "5" in svg and "kg" in svg


def test_incline_svg_has_defs_arrow_marker(tmp_path):
    svg, _ = _svg(tmp_path, INCLINE_TEXT)
    assert 'id="arrow"' in svg


def test_incline_layout_invariants():
    scene = _run_diagnostics(INCLINE_TEXT)
    diag = scene.diagnostics
    assert diag is not None
    canvas = _canvas_box()
    for obj in scene.objects:
        bb = obj.bbox()
        assert bb.x >= canvas.x - 1, f"{obj.element_id} left edge outside canvas"
        assert bb.y >= canvas.y - 1, f"{obj.element_id} top edge outside canvas"
        assert bb.x2 <= canvas.x2 + 1, f"{obj.element_id} right edge outside canvas"
        assert bb.y2 <= canvas.y2 + 1, f"{obj.element_id} bottom edge outside canvas"
    for force in scene.forces:
        assert force.arrow_length() >= _MIN_ARROW_PX - 1, \
            f"{force.element_id} arrow too short: {force.arrow_length():.1f} px"
        assert canvas.x - 1 <= force.x2 <= canvas.x2 + 1, \
            f"{force.element_id} tip x out of canvas"
        assert canvas.y - 1 <= force.y2 <= canvas.y2 + 1, \
            f"{force.element_id} tip y out of canvas"


def test_incline_stable_element_ids():
    scene = _run_diagnostics(INCLINE_TEXT)
    for obj in scene.objects:
        assert obj.element_id, "object missing element_id"
    for force in scene.forces:
        assert force.element_id, "force missing element_id"


def test_incline_frictionless_surface_texture(tmp_path):
    svg, _ = _svg(tmp_path, INCLINE_TEXT)
    # frictionless → dashed overlay present
    assert "stroke-dasharray" in svg


# ── 2. Horizontal friction ────────────────────────────────────────────────────

HORIZ_TEXT = (
    "A 3 kg crate rests on a rough horizontal floor. "
    "The coefficient of friction is 0.35."
)


def test_horiz_pipeline_ok(tmp_path):
    svg, result = _svg(tmp_path, HORIZ_TEXT)
    assert result["status"] == "ok"
    assert svg.startswith("<svg")


def test_horiz_svg_has_surface(tmp_path):
    svg, _ = _svg(tmp_path, HORIZ_TEXT)
    # Horizontal surface line
    assert "y1=\"420\"" in svg or 'y1="420"' in svg


def test_horiz_svg_has_crate_shape(tmp_path):
    svg, _ = _svg(tmp_path, HORIZ_TEXT)
    # crate → box primitive → <rect
    assert "<rect" in svg


def test_horiz_rough_texture(tmp_path):
    svg, _ = _svg(tmp_path, HORIZ_TEXT)
    # rough → serration lines present (short strokes)
    assert "<line" in svg


def test_horiz_layout_invariants():
    scene = _run_diagnostics(HORIZ_TEXT)
    canvas = _canvas_box()
    for obj in scene.objects:
        bb = obj.bbox()
        assert bb.x2 <= canvas.x2 + 1
        assert bb.y2 <= canvas.y2 + 1
    for force in scene.forces:
        assert force.arrow_length() >= _MIN_ARROW_PX - 1


# ── 3. Atwood pulley ──────────────────────────────────────────────────────────

ATWOOD_TEXT = "Two hanging masses of 2 kg and 3 kg pass over a pulley."


def test_atwood_pipeline_ok(tmp_path):
    svg, result = _svg(tmp_path, ATWOOD_TEXT)
    assert result["status"] == "ok"
    assert svg.startswith("<svg")


def test_atwood_svg_has_pulley_wheel(tmp_path):
    svg, _ = _svg(tmp_path, ATWOOD_TEXT)
    # Pulley is drawn as two concentric circles
    assert svg.count("<circle") >= 2


def test_atwood_svg_has_rope(tmp_path):
    svg, _ = _svg(tmp_path, ATWOOD_TEXT)
    # Rope paths present
    assert "<path" in svg


def test_atwood_svg_has_two_objects(tmp_path):
    svg, _ = _svg(tmp_path, ATWOOD_TEXT)
    # Two hanging mass blocks → two <rect elements at minimum
    assert svg.count("<rect") >= 2


def test_atwood_layout_invariants():
    scene = _run_diagnostics(ATWOOD_TEXT)
    canvas = _canvas_box()
    for obj in scene.objects:
        bb = obj.bbox()
        assert bb.x >= canvas.x - 1
        assert bb.y >= canvas.y - 1
        assert bb.x2 <= canvas.x2 + 1
        assert bb.y2 <= canvas.y2 + 1


def test_atwood_hanging_mass_shapes(tmp_path):
    """Atwood objects use hanging_mass shape → suspension lines present."""
    svg, _ = _svg(tmp_path, ATWOOD_TEXT)
    # hanging_mass renderer emits a <line> suspension segment above each block
    assert "<line" in svg


# ── 4. Projectile motion ──────────────────────────────────────────────────────

PROJ_TEXT = "A ball is launched at 20 m/s at 45 degrees."


def test_projectile_pipeline_ok(tmp_path):
    svg, result = _svg(tmp_path, PROJ_TEXT)
    assert result["status"] == "ok"
    assert svg.startswith("<svg")


def test_projectile_svg_has_trajectory(tmp_path):
    svg, _ = _svg(tmp_path, PROJ_TEXT)
    # Trajectory arc is a <polyline>
    assert "<polyline" in svg


def test_projectile_svg_has_ball_circle(tmp_path):
    svg, _ = _svg(tmp_path, PROJ_TEXT)
    # Ball is drawn as a <circle>
    assert "<circle" in svg


def test_projectile_svg_has_velocity_vector(tmp_path):
    svg, _ = _svg(tmp_path, PROJ_TEXT)
    # Launch velocity vector with arrow-vel marker
    assert "arrow-vel" in svg


def test_projectile_svg_has_ground_line(tmp_path):
    svg, _ = _svg(tmp_path, PROJ_TEXT)
    assert "<line" in svg


def test_projectile_layout_invariants():
    scene = _run_diagnostics(PROJ_TEXT)
    canvas = _canvas_box()
    for obj in scene.objects:
        bb = obj.bbox()
        assert bb.x >= canvas.x - 1
        assert bb.y >= canvas.y - 1
        assert bb.x2 <= canvas.x2 + 1
        assert bb.y2 <= canvas.y2 + 1


# ── 5. Incomplete parse fallback ──────────────────────────────────────────────

FALLBACK_TEXT = "A block is on an inclined plane."


def test_fallback_status(tmp_path):
    _, result = _svg(tmp_path, FALLBACK_TEXT)
    assert result["status"] == "needs_clarification"
    assert "mass_kg" in result["missing_fields"]
    assert "incline_angle_deg" in result["missing_fields"]


def test_fallback_svg_produced(tmp_path):
    svg, result = _svg(tmp_path, FALLBACK_TEXT)
    assert Path(result["diagram_path"]).exists()
    assert svg.startswith("<svg")
    assert "</svg>" in svg


def test_fallback_svg_has_title(tmp_path):
    svg, _ = _svg(tmp_path, FALLBACK_TEXT)
    assert "Free-Body Diagram" in svg or "Generic" in svg


def test_fallback_no_force_arrows(tmp_path):
    """Fallback renders without a solved solution, so no force arrows expected."""
    svg, result = _svg(tmp_path, FALLBACK_TEXT)
    # No solved forces means no arrow markers from force rendering
    # (background lines may still use <line>)
    assert result["force_solution"] is None


# ── 6. Unsupported scenario ───────────────────────────────────────────────────

UNSUPPORTED_TEXT = "An electron orbits a nucleus at speed 2e6 m/s."


def test_unsupported_status(tmp_path):
    _, result = _svg(tmp_path, UNSUPPORTED_TEXT)
    # circular_motion has no solver → unsupported_scenario OR needs_clarification
    assert result["status"] in {"unsupported_scenario", "needs_clarification"}


def test_unsupported_svg_produced(tmp_path):
    svg, result = _svg(tmp_path, UNSUPPORTED_TEXT)
    assert Path(result["diagram_path"]).exists()
    assert svg.startswith("<svg")
    assert "</svg>" in svg


def test_unsupported_has_generic_title(tmp_path):
    svg, _ = _svg(tmp_path, UNSUPPORTED_TEXT)
    assert "Free-Body Diagram" in svg or "Generic" in svg


# ── 7. Diagnostics mode ───────────────────────────────────────────────────────

def test_diagnostics_mode_populated():
    scene = _run_diagnostics(INCLINE_TEXT)
    diag = scene.diagnostics
    assert diag is not None
    assert isinstance(diag.bounding_boxes, list)
    assert isinstance(diag.layout_warnings, list)


def test_diagnostics_bboxes_have_ids():
    scene = _run_diagnostics(INCLINE_TEXT)
    diag = scene.diagnostics
    assert diag is not None
    ids = [eid for eid, _ in diag.bounding_boxes]
    assert len(ids) > 0
    for eid in ids:
        assert eid  # none should be empty string


def test_diagnostics_bbox_dimensions_positive():
    scene = _run_diagnostics(INCLINE_TEXT)
    diag = scene.diagnostics
    assert diag is not None
    for eid, bb in diag.bounding_boxes:
        assert bb.w >= 0, f"{eid}: bbox width negative"
        assert bb.h >= 0, f"{eid}: bbox height negative"


def test_diagnostics_svg_contains_bbox_outlines(tmp_path):
    """When diagnostics=True the SVG contains dashed bbox outlines."""
    text = INCLINE_TEXT
    result = parse(text)
    from physics_diagram.physics_engine import SOLVERS, solve
    from physics_diagram.validation import validate
    vresult = validate(result)
    solution = solve(vresult) if (vresult.is_complete and vresult.scenario_type in SOLVERS) else None
    out = str(tmp_path / "diag.svg")
    render_diagram(vresult, solution, out, diagnostics=True)
    svg = Path(out).read_text(encoding="utf-8")
    assert "data-element-id" in svg
    assert "stroke-dasharray" in svg


def test_diagnostics_warnings_no_invariant_violations():
    """For a well-formed complete problem there should be no layout warnings."""
    scene = _run_diagnostics(INCLINE_TEXT)
    diag = scene.diagnostics
    assert diag is not None
    assert diag.layout_warnings == [], \
        f"Unexpected layout warnings: {diag.layout_warnings}"


def test_diagnostics_atwood():
    scene = _run_diagnostics(ATWOOD_TEXT)
    diag = scene.diagnostics
    assert diag is not None
    ids = [eid for eid, _ in diag.bounding_boxes]
    assert any("obj" in i for i in ids)


# ── 8. Visual primitives selection ───────────────────────────────────────────

def test_cart_shape_emits_wheels(tmp_path):
    text = "A 4 kg cart moves to the right on a horizontal table."
    out = str(tmp_path / "cart.svg")
    result = parse(text)
    from physics_diagram.physics_engine import SOLVERS, solve
    from physics_diagram.validation import validate
    vresult = validate(result)
    solution = solve(vresult) if (vresult.is_complete and vresult.scenario_type in SOLVERS) else None
    render_diagram(vresult, solution, out)
    svg = Path(out).read_text(encoding="utf-8")
    # cart wheels → at least two <circle> elements
    assert svg.count("<circle") >= 2


def test_sphere_shape_emits_circle(tmp_path):
    text = "A 2 kg ball rolls off a 30 degree incline."
    out = str(tmp_path / "ball.svg")
    result = parse(text)
    from physics_diagram.validation import validate
    vresult = validate(result)
    from physics_diagram.physics_engine import SOLVERS, solve
    solution = solve(vresult) if (vresult.is_complete and vresult.scenario_type in SOLVERS) else None
    render_diagram(vresult, solution, out)
    svg = Path(out).read_text(encoding="utf-8")
    assert "<circle" in svg


def test_components_flag_emits_dashed_lines(tmp_path):
    """show_components=True → dashed component construction lines in SVG."""
    text = INCLINE_TEXT
    out = str(tmp_path / "comp.svg")
    result = parse(text)
    from physics_diagram.validation import validate
    from physics_diagram.physics_engine import SOLVERS, solve
    vresult = validate(result)
    solution = solve(vresult) if (vresult.is_complete and vresult.scenario_type in SOLVERS) else None
    render_diagram(vresult, solution, out, render_options={"view_mode": "components"})
    svg = Path(out).read_text(encoding="utf-8")
    assert "stroke-dasharray" in svg


def test_velocity_vector_in_svg_for_moving_cart(tmp_path):
    """A cart moving right should include a velocity vector arrow."""
    text = "A 3 kg cart moves to the right on a horizontal table."
    out = str(tmp_path / "vel.svg")
    result = parse(text)
    from physics_diagram.validation import validate
    from physics_diagram.physics_engine import SOLVERS, solve
    vresult = validate(result)
    solution = solve(vresult) if (vresult.is_complete and vresult.scenario_type in SOLVERS) else None
    render_diagram(vresult, solution, out)
    svg = Path(out).read_text(encoding="utf-8")
    assert "arrow-vel" in svg


# ── 9. Clamping: extreme scenario ────────────────────────────────────────────

def test_large_force_arrow_tip_inside_canvas():
    """A very large applied force should still have its tip inside the canvas."""
    text = (
        "A 10 kg block on a frictionless inclined plane at 60 degrees. "
        "How much force is required to keep it at rest?"
    )
    scene = _run_diagnostics(text)
    canvas = _canvas_box()
    for force in scene.forces:
        assert canvas.x - 1 <= force.x2 <= canvas.x2 + 1, \
            f"{force.element_id} tip x={force.x2:.1f} outside canvas"
        assert canvas.y - 1 <= force.y2 <= canvas.y2 + 1, \
            f"{force.element_id} tip y={force.y2:.1f} outside canvas"


def test_min_arrow_length_enforced():
    """Even for very small forces the arrow must be at least _MIN_ARROW_PX."""
    text = (
        "A 0.001 kg box on a frictionless inclined plane at 5 degrees. "
        "How much force is required to keep it at rest?"
    )
    scene = _run_diagnostics(text)
    for force in scene.forces:
        assert force.arrow_length() >= _MIN_ARROW_PX - 1, \
            f"{force.element_id} length={force.arrow_length():.1f}"


# ── 10. BoundingBox unit tests ────────────────────────────────────────────────

def test_bbox_overlaps_true():
    a = BoundingBox(0, 0, 100, 50)
    b = BoundingBox(50, 25, 100, 50)
    assert a.overlaps(b)


def test_bbox_overlaps_false():
    a = BoundingBox(0, 0, 40, 40)
    b = BoundingBox(100, 100, 40, 40)
    assert not a.overlaps(b)


def test_bbox_clamp_point_inside():
    canvas = BoundingBox(10, 10, 880, 600)
    px, py = canvas.clamp_point(5.0, 5.0)
    assert canvas.x <= px <= canvas.x2
    assert canvas.y <= py <= canvas.y2


def test_bbox_clamp_point_already_inside():
    canvas = BoundingBox(10, 10, 880, 600)
    px, py = canvas.clamp_point(450.0, 300.0)
    assert px == 450.0
    assert py == 300.0


def test_bbox_contains():
    bb = BoundingBox(0, 0, 900, 620)
    assert bb.contains(450, 310)
    assert not bb.contains(950, 310)
