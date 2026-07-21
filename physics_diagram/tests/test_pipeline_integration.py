from pathlib import Path

import pytest

from physics_diagram.pipeline import solve_and_render


def test_worked_integration_example(tmp_path: Path):
    result = solve_and_render(
        "A box of mass 5kg is placed on a frictionless inclined plane with 30 degree inclination. How much force is required to keep it at rest?",
        str(tmp_path / "incline.svg"),
    )
    parsed = result["parse_result"]
    assert result["status"] == "ok"
    assert parsed.scenario_type == "inclined_plane"
    assert parsed.objects[0].mass_kg == 5
    assert parsed.geometry.incline_angle_deg == 30
    assert (parsed.friction, parsed.mu) == ("frictionless", 0.0)
    assert result["force_solution"].derived_values["required_force_to_hold_at_rest_n"] == pytest.approx(24.5)
    assert Path(result["diagram_path"]).exists()


def test_incomplete_problem_returns_clarification(tmp_path: Path):
    result = solve_and_render("A block is on an inclined plane.", str(tmp_path / "fallback.svg"))
    assert result["status"] == "needs_clarification"
    assert {"mass_kg", "incline_angle_deg"}.issubset(result["missing_fields"])
