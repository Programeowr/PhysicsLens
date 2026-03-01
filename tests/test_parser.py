"""
Tests for the physics problem parser — uses mocked Gemini API responses.
Tests the Flash→Pro fallback, JSON recovery, physics fixes, and caching.
"""

import json
from unittest.mock import patch, MagicMock, call

import pytest

from app.parser import (
    parse_physics_problem,
    ParsingError,
    _recover_json,
    _apply_physics_fixes,
    _result_cache,
    _cache_order,
)


MOCK_VALID_RESPONSE = json.dumps({
    "objects": [{"id": "block_1", "type": "block", "mass": 5}],
    "surfaces": [{"id": "incline_1", "type": "inclined_plane", "angle": 30}],
    "placements": [{"object_id": "block_1", "surface_id": "incline_1"}],
    "forces": [
        {"type": "gravity", "magnitude": 49.0, "direction": "vertical_down", "object_id": "block_1"},
        {"type": "normal", "magnitude": None, "direction": "perpendicular_to_surface", "object_id": "block_1"},
    ],
    "friction": {"object_id": "block_1", "coefficient": 0.2},
    "constants": {"gravity": 9.8},
})

MOCK_INVALID_JSON = "This is not JSON at all {{{bad"

MOCK_INVALID_SCHEMA = json.dumps({
    "objects": [{"id": "block_1", "type": "block", "mass": 5}],
    "surfaces": [],
    "forces": [
        {"type": "gravity", "magnitude": 49.0, "direction": "vertical_down", "object_id": "NONEXISTENT"},
    ],
})


class TestParser:
    def setup_method(self):
        """Clear cache before each test."""
        _result_cache.clear()
        _cache_order.clear()

    @patch("app.parser._call_gemini")
    def test_successful_parse(self, mock_gemini):
        mock_gemini.return_value = MOCK_VALID_RESPONSE

        result = parse_physics_problem("A 5kg block on a 30 degree incline with friction")

        assert len(result.objects) == 1
        assert result.objects[0].id == "block_1"
        assert result.objects[0].mass == 5.0
        assert result.surfaces[0].angle == 30
        # Should only call Flash (success on first try)
        assert mock_gemini.call_count == 1

    @patch("app.parser._call_gemini")
    def test_flash_fails_pro_succeeds(self, mock_gemini):
        """Test Flash→Pro fallback: Flash returns bad JSON, Pro returns valid."""
        mock_gemini.side_effect = [
            MOCK_INVALID_JSON,      # Flash: bad JSON
            MOCK_VALID_RESPONSE,    # Pro: valid
        ]

        result = parse_physics_problem("A 5kg block on a 30 degree incline test fallback")

        assert len(result.objects) == 1
        assert mock_gemini.call_count == 2  # Both Flash and Pro called

    @patch("app.parser._call_gemini")
    def test_both_models_fail_raises_error(self, mock_gemini):
        """Both Flash and Pro fail → ParsingError."""
        mock_gemini.return_value = MOCK_INVALID_JSON

        with pytest.raises(ParsingError, match="invalid JSON"):
            parse_physics_problem("both models fail test problem")

    @patch("app.parser._call_gemini")
    def test_api_failure_falls_back_to_pro(self, mock_gemini):
        """Flash API crashes → falls back to Pro."""
        mock_gemini.side_effect = [
            RuntimeError("Flash down"),    # Flash: API error
            MOCK_VALID_RESPONSE,           # Pro: valid
        ]

        result = parse_physics_problem("api failure fallback test problem")
        assert len(result.objects) == 1

    @patch("app.parser._call_gemini")
    def test_both_api_failures_raises_error(self, mock_gemini):
        """Both models fail at API level → ParsingError."""
        mock_gemini.side_effect = RuntimeError("All APIs down")

        with pytest.raises(ParsingError, match="unavailable"):
            parse_physics_problem("both apis down test problem")

    @patch("app.parser._call_gemini")
    def test_parsed_result_has_correct_forces(self, mock_gemini):
        mock_gemini.return_value = MOCK_VALID_RESPONSE

        result = parse_physics_problem("test forces correctly parsed result problem")

        force_types = [f.type.value for f in result.forces]
        assert "gravity" in force_types
        assert "normal" in force_types

    @patch("app.parser._call_gemini")
    def test_caching_avoids_second_call(self, mock_gemini):
        """Same problem text should use cache on second call."""
        mock_gemini.return_value = MOCK_VALID_RESPONSE

        result1 = parse_physics_problem("cached problem text test here hello")
        result2 = parse_physics_problem("cached problem text test here hello")

        assert result1.objects[0].id == result2.objects[0].id
        assert mock_gemini.call_count == 1  # Only called once, second is cached


class TestJsonRecovery:
    def test_strips_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        cleaned = _recover_json(raw)
        assert json.loads(cleaned) == {"key": "value"}

    def test_removes_trailing_commas(self):
        raw = '{"a": 1, "b": 2,}'
        cleaned = _recover_json(raw)
        assert json.loads(cleaned) == {"a": 1, "b": 2}

    def test_fixes_single_quotes(self):
        raw = "{'key': 'value'}"
        cleaned = _recover_json(raw)
        assert json.loads(cleaned) == {"key": "value"}

    def test_valid_json_unchanged(self):
        raw = '{"a": 1}'
        assert _recover_json(raw) == '{"a": 1}'


class TestPhysicsFixes:
    def test_adds_missing_gravity(self):
        data = {
            "objects": [{"id": "b1", "type": "block", "mass": 10}],
            "surfaces": [],
            "placements": [],
            "forces": [],
            "friction": None,
            "constants": {"gravity": 9.8},
        }
        fixed = _apply_physics_fixes(data)
        gravity_forces = [f for f in fixed["forces"] if f["type"] == "gravity"]
        assert len(gravity_forces) == 1
        assert gravity_forces[0]["magnitude"] == 98.0

    def test_corrects_wrong_gravity(self):
        data = {
            "objects": [{"id": "b1", "type": "block", "mass": 5}],
            "surfaces": [],
            "placements": [],
            "forces": [
                {"type": "gravity", "magnitude": 100.0, "direction": "vertical_down", "object_id": "b1"}
            ],
            "friction": None,
            "constants": {"gravity": 9.8},
        }
        fixed = _apply_physics_fixes(data)
        assert fixed["forces"][0]["magnitude"] == 49.0

    def test_fixes_negative_mass(self):
        data = {
            "objects": [{"id": "b1", "type": "block", "mass": -5}],
            "surfaces": [],
            "placements": [],
            "forces": [],
            "friction": None,
            "constants": {"gravity": 9.8},
        }
        fixed = _apply_physics_fixes(data)
        assert fixed["objects"][0]["mass"] == 5
