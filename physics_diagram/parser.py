"""Ollama-backed natural-language parser that returns the stable project schema."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from .classifier import REQUIRED_SLOTS
from .schema import AppliedForce, Geometry, ObjectSpec, ParseResult

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
SCENARIOS = ["inclined_plane", "horizontal_friction", "atwood_pulley", "projectile_motion", "circular_motion", "spring_mass"]

PARSER_SCHEMA: dict[str, Any] = {
    "type": "object", "additionalProperties": False,
    "required": ["scenario_type", "confidence", "objects", "geometry", "friction", "mu", "applied_forces", "unknowns"],
    "properties": {
        "scenario_type": {"anyOf": [{"type": "string", "enum": SCENARIOS}, {"type": "null"}]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "objects": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["id", "shape", "mass_kg", "label"], "properties": {"id": {"type": "string"}, "shape": {"type": "string", "enum": ["box", "sphere", "block", "particle"]}, "mass_kg": {"anyOf": [{"type": "number"}, {"type": "null"}]}, "label": {"anyOf": [{"type": "string"}, {"type": "null"}]}}}},
        "geometry": {"type": "object", "additionalProperties": False, "required": ["incline_angle_deg", "projectile_angle_deg", "initial_speed_ms"], "properties": {"incline_angle_deg": {"anyOf": [{"type": "number"}, {"type": "null"}]}, "projectile_angle_deg": {"anyOf": [{"type": "number"}, {"type": "null"}]}, "initial_speed_ms": {"anyOf": [{"type": "number"}, {"type": "null"}]}}},
        "friction": {"anyOf": [{"type": "string", "enum": ["frictionless", "kinetic"]}, {"type": "null"}]},
        "mu": {"anyOf": [{"type": "number", "minimum": 0}, {"type": "null"}]},
        "applied_forces": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["magnitude_n", "direction"], "properties": {"magnitude_n": {"type": "number", "minimum": 0}, "direction": {"type": "string"}}}},
        "unknowns": {"type": "array", "items": {"type": "string"}},
    },
}

SYSTEM_PROMPT = """You are a precise physics information extractor. Extract facts only from the user's question. Return JSON conforming exactly to the provided schema. Never solve the physics problem and never invent values.

Use only these scenario_type values: inclined_plane, horizontal_friction, atwood_pulley, projectile_motion, circular_motion, spring_mass. Use null if no scenario is clear.

Normalize all values to SI: mass_kg (g / 1000, lb * 0.45359237), angles in degrees (radians converted to degrees), and initial_speed_ms (km/h / 3.6, mph * 0.44704). A frictionless statement means friction='frictionless' and mu=0. Use friction='kinetic' only when a coefficient is given. Leave absent facts null or [] rather than guessing.

For multiple masses, create objects in textual order with stable IDs object_1, object_2, etc. Recognize requested targets in unknowns using: required_force, tension, acceleration, normal_force, range, max_height. Applied forces explicitly stated in newtons belong in applied_forces; preserve a stated direction, otherwise use 'unspecified'. Set confidence based only on how clearly the scenario is stated."""


class OllamaParserError(RuntimeError):
    """Raised when the required local Ollama parser is unavailable or invalid."""


def _missing_slots(scenario: str | None, objects: list[ObjectSpec], geometry: Geometry) -> list[str]:
    if scenario is None:
        return ["scenario_type"]
    present = {
        "mass_kg": bool(objects and objects[0].mass_kg is not None),
        "mass_kg_list_min2": len([obj for obj in objects if obj.mass_kg is not None]) >= 2,
        "incline_angle_deg": geometry.incline_angle_deg is not None,
        "projectile_angle_deg": geometry.projectile_angle_deg is not None,
        "initial_speed_ms": geometry.initial_speed_ms is not None,
    }
    return [slot for slot in REQUIRED_SLOTS.get(scenario, []) if not present.get(slot, False)]


def _ollama_extract(text: str) -> dict[str, Any]:
    payload = {"model": OLLAMA_MODEL, "system": SYSTEM_PROMPT, "prompt": text, "format": PARSER_SCHEMA, "stream": False, "options": {"temperature": 0, "seed": 42, "num_predict": 700}}
    request = Request(f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=120) as response:  # local endpoint configured by OLLAMA_BASE_URL
            body = json.loads(response.read().decode("utf-8"))
        return json.loads(body["response"])
    except (URLError, TimeoutError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise OllamaParserError(f"Could not parse with Ollama model '{OLLAMA_MODEL}'. Ensure Ollama is running and the model is installed.") from exc


def _optional_float(value: Any) -> float | None:
    return float(value) if value is not None else None


def parse(text: str) -> ParseResult:
    """Use local Qwen via Ollama to convert text into the existing ParseResult schema."""
    data = _ollama_extract(text)
    objects = [ObjectSpec(id=str(item.get("id") or f"object_{index}"), shape=str(item.get("shape") or "box"), mass_kg=_optional_float(item.get("mass_kg")), label=item.get("label")) for index, item in enumerate(data.get("objects", []), start=1)]
    geometry_data = data.get("geometry", {})
    geometry = Geometry(incline_angle_deg=_optional_float(geometry_data.get("incline_angle_deg")), projectile_angle_deg=_optional_float(geometry_data.get("projectile_angle_deg")), initial_speed_ms=_optional_float(geometry_data.get("initial_speed_ms")))
    scenario = data.get("scenario_type") if data.get("scenario_type") in SCENARIOS else None
    friction = data.get("friction") if data.get("friction") in {"frictionless", "kinetic"} else None
    mu = 0.0 if friction == "frictionless" else _optional_float(data.get("mu"))
    return ParseResult(scenario_type=scenario, confidence=max(0.0, min(1.0, float(data.get("confidence", 0.0)))), objects=objects, geometry=geometry, friction=friction, mu=mu, applied_forces=[AppliedForce(float(item["magnitude_n"]), str(item.get("direction") or "unspecified")) for item in data.get("applied_forces", [])], unknowns=[str(value) for value in data.get("unknowns", [])], missing_required=_missing_slots(scenario, objects, geometry), raw_text=text)
