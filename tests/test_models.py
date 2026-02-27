"""
Tests for Pydantic models — schema validation and referential integrity.
"""

import pytest
from pydantic import ValidationError

from app.models import (
    ParsedPhysicsProblem,
    PhysicsObject,
    Surface,
    Force,
    Placement,
    Friction,
    ProblemInput,
)


# ── Valid data fixtures ──────────────────────────────────────────────────

VALID_INCLINE_DATA = {
    "objects": [{"id": "block_1", "type": "block", "mass": 5}],
    "surfaces": [{"id": "incline_1", "type": "inclined_plane", "angle": 30}],
    "placements": [{"object_id": "block_1", "surface_id": "incline_1"}],
    "forces": [
        {"type": "gravity", "magnitude": 49.0, "direction": "vertical_down", "object_id": "block_1"},
        {"type": "normal", "magnitude": None, "direction": "perpendicular_to_surface", "object_id": "block_1"},
    ],
    "friction": {"object_id": "block_1", "coefficient": 0.2},
    "constants": {"gravity": 9.8},
}

VALID_PULLEY_DATA = {
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
}


# ── Test valid parsing ───────────────────────────────────────────────────

class TestValidModels:
    def test_incline_data_parses(self):
        result = ParsedPhysicsProblem.model_validate(VALID_INCLINE_DATA)
        assert len(result.objects) == 1
        assert result.objects[0].mass == 5.0
        assert result.surfaces[0].angle == 30

    def test_pulley_data_parses(self):
        result = ParsedPhysicsProblem.model_validate(VALID_PULLEY_DATA)
        assert len(result.objects) == 3
        assert result.has_pulley() is True

    def test_primary_surface_type(self):
        result = ParsedPhysicsProblem.model_validate(VALID_INCLINE_DATA)
        assert result.get_primary_surface_type().value == "inclined_plane"

    def test_defaults_applied(self):
        minimal = {"objects": [], "surfaces": [], "forces": []}
        result = ParsedPhysicsProblem.model_validate(minimal)
        assert result.constants.gravity == 9.8
        assert result.friction is None

    def test_optional_mass_is_none(self):
        data = {
            "objects": [{"id": "obj1", "type": "body"}],
            "surfaces": [],
            "forces": [],
        }
        result = ParsedPhysicsProblem.model_validate(data)
        assert result.objects[0].mass is None


# ── Test referential integrity ───────────────────────────────────────────

class TestReferentialIntegrity:
    def test_invalid_object_in_placement(self):
        data = {
            "objects": [{"id": "block_1", "type": "block", "mass": 5}],
            "surfaces": [{"id": "s1", "type": "horizontal_surface"}],
            "placements": [{"object_id": "NONEXISTENT", "surface_id": "s1"}],
            "forces": [],
        }
        with pytest.raises(ValidationError, match="unknown object_id"):
            ParsedPhysicsProblem.model_validate(data)

    def test_invalid_surface_in_placement(self):
        data = {
            "objects": [{"id": "block_1", "type": "block", "mass": 5}],
            "surfaces": [{"id": "s1", "type": "horizontal_surface"}],
            "placements": [{"object_id": "block_1", "surface_id": "NONEXISTENT"}],
            "forces": [],
        }
        with pytest.raises(ValidationError, match="unknown surface_id"):
            ParsedPhysicsProblem.model_validate(data)

    def test_invalid_object_in_force(self):
        data = {
            "objects": [{"id": "block_1", "type": "block", "mass": 5}],
            "surfaces": [],
            "forces": [
                {"type": "gravity", "magnitude": 49, "direction": "vertical_down", "object_id": "WRONG"},
            ],
        }
        with pytest.raises(ValidationError, match="unknown object_id"):
            ParsedPhysicsProblem.model_validate(data)

    def test_invalid_object_in_friction(self):
        data = {
            "objects": [{"id": "block_1", "type": "block", "mass": 5}],
            "surfaces": [],
            "forces": [],
            "friction": {"object_id": "WRONG", "coefficient": 0.3},
        }
        with pytest.raises(ValidationError, match="unknown object_id"):
            ParsedPhysicsProblem.model_validate(data)


# ── Test enum validation ─────────────────────────────────────────────────

class TestEnumValidation:
    def test_invalid_object_type(self):
        with pytest.raises(ValidationError):
            PhysicsObject(id="x", type="airplane", mass=5)

    def test_invalid_force_type(self):
        with pytest.raises(ValidationError):
            Force(type="nuclear", magnitude=10, direction="up", object_id="x")

    def test_invalid_direction(self):
        with pytest.raises(ValidationError):
            Force(type="gravity", magnitude=10, direction="sideways", object_id="x")

    def test_invalid_surface_type(self):
        with pytest.raises(ValidationError):
            Surface(id="s", type="trampoline")


# ── Test ProblemInput ────────────────────────────────────────────────────

class TestProblemInput:
    def test_valid_input(self):
        inp = ProblemInput(problem="A 5 kg block is on a 30 degree incline")
        assert len(inp.problem) > 10

    def test_too_short(self):
        with pytest.raises(ValidationError):
            ProblemInput(problem="short")

    def test_empty(self):
        with pytest.raises(ValidationError):
            ProblemInput(problem="")
