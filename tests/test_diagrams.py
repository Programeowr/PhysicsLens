"""
Tests for diagram generators — verifies each generator produces valid SVG.
"""

import pytest

from app.models import ParsedPhysicsProblem
from app.diagrams.incline import generate_incline_diagram
from app.diagrams.horizontal import generate_horizontal_diagram
from app.diagrams.pulley import generate_pulley_diagram
from app.diagrams.vertical import generate_vertical_diagram


# ── Sample data ──────────────────────────────────────────────────────────

INCLINE_DATA = ParsedPhysicsProblem.model_validate({
    "objects": [{"id": "block_1", "type": "block", "mass": 5}],
    "surfaces": [{"id": "incline_1", "type": "inclined_plane", "angle": 30}],
    "placements": [{"object_id": "block_1", "surface_id": "incline_1"}],
    "forces": [
        {"type": "gravity", "magnitude": 49.0, "direction": "vertical_down", "object_id": "block_1"},
        {"type": "normal", "magnitude": None, "direction": "perpendicular_to_surface", "object_id": "block_1"},
        {"type": "applied", "magnitude": 20, "direction": "up_along_plane", "object_id": "block_1"},
    ],
    "friction": {"object_id": "block_1", "coefficient": 0.2},
    "constants": {"gravity": 9.8},
})

HORIZONTAL_DATA = ParsedPhysicsProblem.model_validate({
    "objects": [{"id": "box_1", "type": "block", "mass": 10}],
    "surfaces": [{"id": "floor_1", "type": "horizontal_surface"}],
    "placements": [{"object_id": "box_1", "surface_id": "floor_1"}],
    "forces": [
        {"type": "gravity", "magnitude": 98.0, "direction": "vertical_down", "object_id": "box_1"},
        {"type": "normal", "magnitude": None, "direction": "up", "object_id": "box_1"},
        {"type": "applied", "magnitude": 50, "direction": "right", "object_id": "box_1"},
        {"type": "friction_force", "magnitude": None, "direction": "left", "object_id": "box_1"},
    ],
    "friction": {"object_id": "box_1", "coefficient": 0.3},
    "constants": {"gravity": 9.8},
})

PULLEY_DATA = ParsedPhysicsProblem.model_validate({
    "objects": [
        {"id": "m1", "type": "block", "mass": 3},
        {"id": "m2", "type": "block", "mass": 5},
        {"id": "rope", "type": "rope"},
    ],
    "surfaces": [{"id": "pulley_1", "type": "pulley"}],
    "placements": [
        {"object_id": "m1", "surface_id": "pulley_1"},
        {"object_id": "m2", "surface_id": "pulley_1"},
    ],
    "forces": [
        {"type": "gravity", "magnitude": 29.4, "direction": "vertical_down", "object_id": "m1"},
        {"type": "tension", "magnitude": None, "direction": "vertical_up", "object_id": "m1"},
        {"type": "gravity", "magnitude": 49.0, "direction": "vertical_down", "object_id": "m2"},
        {"type": "tension", "magnitude": None, "direction": "vertical_up", "object_id": "m2"},
    ],
    "constants": {"gravity": 9.8},
})

VERTICAL_DATA = ParsedPhysicsProblem.model_validate({
    "objects": [{"id": "person_1", "type": "body", "mass": 60}],
    "surfaces": [{"id": "elevator_floor", "type": "horizontal_surface"}],
    "placements": [{"object_id": "person_1", "surface_id": "elevator_floor"}],
    "forces": [
        {"type": "gravity", "magnitude": 588.0, "direction": "vertical_down", "object_id": "person_1"},
        {"type": "normal", "magnitude": None, "direction": "vertical_up", "object_id": "person_1"},
    ],
    "constants": {"gravity": 9.8},
})


# ── Tests ────────────────────────────────────────────────────────────────

class TestInclineDiagram:
    def test_produces_svg(self):
        svg = generate_incline_diagram(INCLINE_DATA)
        assert svg.strip().startswith("<?xml")
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_contains_force_arrows(self):
        svg = generate_incline_diagram(INCLINE_DATA)
        assert "mg" in svg  # gravity label
        assert "N" in svg   # normal force label

    def test_contains_block(self):
        svg = generate_incline_diagram(INCLINE_DATA)
        assert "5kg" in svg

    def test_contains_angle(self):
        svg = generate_incline_diagram(INCLINE_DATA)
        # Check angle value appears in the SVG (avoid encoding issues with °)
        assert ">30" in svg


class TestHorizontalDiagram:
    def test_produces_svg(self):
        svg = generate_horizontal_diagram(HORIZONTAL_DATA)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_contains_forces(self):
        svg = generate_horizontal_diagram(HORIZONTAL_DATA)
        assert "mg" in svg
        assert "F=50N" in svg

    def test_contains_mass_label(self):
        svg = generate_horizontal_diagram(HORIZONTAL_DATA)
        assert "10kg" in svg


class TestPulleyDiagram:
    def test_produces_svg(self):
        svg = generate_pulley_diagram(PULLEY_DATA)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_contains_both_masses(self):
        svg = generate_pulley_diagram(PULLEY_DATA)
        assert "3kg" in svg
        assert "5kg" in svg

    def test_contains_pulley_wheel(self):
        svg = generate_pulley_diagram(PULLEY_DATA)
        assert "<circle" in svg  # pulley wheel

    def test_contains_tension(self):
        svg = generate_pulley_diagram(PULLEY_DATA)
        assert "T" in svg  # tension label


class TestVerticalDiagram:
    def test_produces_svg(self):
        svg = generate_vertical_diagram(VERTICAL_DATA)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_contains_mass(self):
        svg = generate_vertical_diagram(VERTICAL_DATA)
        assert "60kg" in svg

    def test_contains_elevator(self):
        svg = generate_vertical_diagram(VERTICAL_DATA)
        assert "Elevator" in svg

    def test_contains_gravity(self):
        svg = generate_vertical_diagram(VERTICAL_DATA)
        assert "mg=588N" in svg
