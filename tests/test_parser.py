"""
Tests for the physics problem parser — uses mocked Gemini API responses.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from app.parser import parse_physics_problem, ParsingError


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
    @patch("app.parser._call_gemini")
    def test_successful_parse(self, mock_gemini):
        mock_gemini.return_value = MOCK_VALID_RESPONSE

        result = parse_physics_problem("A 5kg block on a 30 degree incline")

        assert len(result.objects) == 1
        assert result.objects[0].id == "block_1"
        assert result.objects[0].mass == 5.0
        assert result.surfaces[0].angle == 30
        mock_gemini.assert_called_once()

    @patch("app.parser._call_gemini")
    def test_invalid_json_raises_parsing_error(self, mock_gemini):
        mock_gemini.return_value = MOCK_INVALID_JSON

        with pytest.raises(ParsingError, match="invalid JSON"):
            parse_physics_problem("some problem")

    @patch("app.parser._call_gemini")
    def test_invalid_schema_raises_parsing_error(self, mock_gemini):
        mock_gemini.return_value = MOCK_INVALID_SCHEMA

        with pytest.raises(ParsingError, match="validation"):
            parse_physics_problem("some problem")

    @patch("app.parser._call_gemini")
    def test_api_failure_raises_parsing_error(self, mock_gemini):
        mock_gemini.side_effect = RuntimeError("API down")

        with pytest.raises(ParsingError, match="unavailable"):
            parse_physics_problem("some problem")

    @patch("app.parser._call_gemini")
    def test_parsed_result_has_correct_forces(self, mock_gemini):
        mock_gemini.return_value = MOCK_VALID_RESPONSE

        result = parse_physics_problem("test problem")

        force_types = [f.type.value for f in result.forces]
        assert "gravity" in force_types
        assert "normal" in force_types
