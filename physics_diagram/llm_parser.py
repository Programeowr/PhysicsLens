"""LLM-based parser using Ollama (qwen2.5:7b).

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/solve" `-ContentType "application/json" `-Body '{"text": "A 5kg box on a frictionless 30 degree inclined plane. How much force to keep it at rest?"}'

Sends a structured prompt to a locally running Ollama instance and maps the
JSON response back to the project's stable ``ParseResult`` schema.  The LLM
is *only* responsible for extracting the physics quantities; all downstream
validation, solving, and rendering remain identical to the deterministic path.

Usage (programmatic):
    from physics_diagram.llm_parser import parse_with_llm
    result = parse_with_llm("A 5 kg block on a 30° incline…")

Ollama must be running locally (default: http://localhost:11434) with the
qwen2.5:7b model already pulled::

    ollama pull qwen2.5:7b
    ollama serve          # starts the REST server on :11434
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .classifier import REQUIRED_SLOTS, classify_scenario
from .schema import (
    AmbiguityFlag,
    AppliedForce,
    ConstraintRelationship,
    ForceMention,
    Geometry,
    ObjectSpec,
    ParseResult,
    VisualFeatures,
)

logger = logging.getLogger(__name__)

# ── Ollama connection ─────────────────────────────────────────────────────────

import os

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "qwen2.5:7b"
)
OLLAMA_BASE_URL = OLLAMA_URL
OLLAMA_MODEL = LLM_MODEL
OLLAMA_TIMEOUT = 60.0   # seconds — LLM inference can be slow on CPU
OLLAMA_NUM_CTX = 2048   # reduced context window for faster inference


# ── JSON schema sent to the model ─────────────────────────────────────────────

_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["scenario_type", "confidence", "objects", "geometry", "friction", "applied_forces", "unknowns", "visual_features"],
    "properties": {
        "scenario_type": {
            "type": ["string", "null"],
            "enum": ["inclined_plane", "horizontal_friction", "atwood_pulley", "projectile_motion",
                     "circular_motion", "spring_mass", None],
            "description": "Best matching physics scenario, or null if none fits."
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "How confident you are in the scenario classification (0-1)."
        },
        "objects": {
            "type": "array",
            "description": "One entry per physical object in the problem.",
            "items": {
                "type": "object",
                "required": ["id", "shape", "mass_kg", "label"],
                "properties": {
                    "id":      {"type": "string", "description": "e.g. 'object_1'"},
                    "shape":   {"type": "string", "enum": ["box", "sphere", "block", "particle", "cart", "hanging_mass"]},
                    "mass_kg": {"type": ["number", "null"], "description": "Mass in kilograms, null if not given."},
                    "label":   {"type": ["string", "null"]}
                }
            }
        },
        "geometry": {
            "type": "object",
            "required": ["incline_angle_deg", "projectile_angle_deg", "initial_speed_ms"],
            "properties": {
                "incline_angle_deg":   {"type": ["number", "null"]},
                "projectile_angle_deg":{"type": ["number", "null"]},
                "initial_speed_ms":    {"type": ["number", "null"]}
            }
        },
        "friction": {
            "type": ["string", "null"],
            "enum": ["frictionless", "kinetic", "static", None],
            "description": "Friction condition, or null if not mentioned."
        },
        "mu": {
            "type": ["number", "null"],
            "description": "Coefficient of friction, or null if not given."
        },
        "applied_forces": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["magnitude_n", "direction"],
                "properties": {
                    "magnitude_n": {"type": "number"},
                    "direction":   {"type": "string", "enum": ["right", "left", "uphill", "down", "unspecified"]},
                    "angle_deg":   {"type": ["number", "null"], "description": "Force angle in degrees (e.g., 30° above horizontal)"},
                    "reference_frame": {"type": "string", "enum": ["horizontal", "incline", "vertical"], "description": "What the angle is measured from"}
                }
            }
        },
        "unknowns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of quantities the problem is asking to find."
        },
        "visual_features": {
            "type": "object",
            "description": "Visual-semantic cues for the renderer.",
            "required": ["object_types", "surface_type", "motion_state", "requested_view"],
            "properties": {
                "object_types": {
                    "type": "array",
                    "items": {"type": "string",
                              "enum": ["box","cart","ball","sphere","crate","block","particle",
                                       "hanging_mass","pulley_mass","spring_endpoint","projectile","unknown"]}
                },
                "surface_type": {
                    "type": "string",
                    "enum": ["rough_floor","smooth_floor","frictionless_ramp","inclined_plane",
                             "ground","pulley_support","spring_anchor","air","table","unknown"]
                },
                "motion_state": {
                    "type": "string",
                    "enum": ["at_rest","moving_right","moving_left","moving_up_incline",
                             "moving_down_incline","accelerating","decelerating",
                             "launched_upward","descending","equilibrium","unknown"]
                },
                "requested_view": {
                    "type": "string",
                    "enum": ["fbd","scene_and_fbd","components","trajectory",
                             "velocity_diagram","acceleration_diagram","symbolic","numeric","unknown"]
                },
                "force_mentions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["force_type", "provenance", "direction_hint"],
                        "properties": {
                            "force_type":     {"type": "string"},
                            "provenance":     {"type": "string"},
                            "direction_hint": {"type": "string"}
                        }
                    }
                },
                "constraint_relationships": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["kind", "object_a_id", "object_b_id"],
                        "properties": {
                            "kind":        {"type": "string"},
                            "object_a_id": {"type": "string"},
                            "object_b_id": {"type": "string"}
                        }
                    }
                },
                "known_quantities":   {"type": "array", "items": {"type": "string"}},
                "unknown_quantities": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
}

# ── Prompt construction ───────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a precise physics parser. Your only job is to extract structured
information from a natural-language physics problem and return valid JSON
that matches the provided schema exactly.

Rules:
- Use SI units (kg, m/s, degrees). Convert any other units before inserting.
- Set numeric fields to null when the value is not stated in the problem.
- Set scenario_type to null if none of the supported types fit.
- Do not invent values. Do not hallucinate numbers.
- Return ONLY the JSON object — no markdown fences, no extra commentary.
"""


def _build_user_prompt(text: str) -> str:
    schema_str = json.dumps(_EXTRACTION_SCHEMA, indent=2)
    return (
        f"Physics problem:\n{text}\n\n"
        f"Return a JSON object conforming to this schema:\n{schema_str}"
    )


# ── Ollama API call ───────────────────────────────────────────────────────────

def _call_ollama(text: str) -> dict[str, Any]:
    """Send the problem to Ollama and return the parsed JSON dict.

    Raises:
        httpx.HTTPError: on connection / HTTP errors.
        ValueError: when the model returns non-JSON or schema-invalid output.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": _build_user_prompt(text)},
        ],
        "stream": False,
        "format": "json",   # Ollama native JSON mode — constrains output to valid JSON
        "options": {
            "temperature": 0.0,     # fully deterministic
            "num_predict": 1024,
        },
    }

    with httpx.Client(timeout=OLLAMA_TIMEOUT) as client:
        response = client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        response.raise_for_status()

    raw = response.json()
    content = raw["message"]["content"]

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Ollama returned non-JSON content: {content[:300]}") from exc


# ── Schema → ParseResult mapping ─────────────────────────────────────────────

def _map_objects(raw_objects: list[dict]) -> list[ObjectSpec]:
    out: list[ObjectSpec] = []
    for i, obj in enumerate(raw_objects):
        mass_raw = obj.get("mass_kg")
        mass_kg = float(mass_raw) if mass_raw is not None else None
        out.append(ObjectSpec(
            id=str(obj.get("id") or f"object_{i + 1}"),
            shape=str(obj.get("shape") or "box"),
            mass_kg=mass_kg,
            label=obj.get("label"),
        ))
    return out


def _map_geometry(raw_geo: dict) -> Geometry:
    def _f(key: str) -> float | None:
        v = raw_geo.get(key)
        return float(v) if v is not None else None

    return Geometry(
        incline_angle_deg=_f("incline_angle_deg"),
        projectile_angle_deg=_f("projectile_angle_deg"),
        initial_speed_ms=_f("initial_speed_ms"),
    )


def _map_applied_forces(raw_forces: list[dict]) -> list[AppliedForce]:
    out: list[AppliedForce] = []
    for f in raw_forces:
        mag_raw = f.get("magnitude_n")
        if mag_raw is None:
            continue  # skip forces with no magnitude
        
        angle_raw = f.get("angle_deg")
        angle_deg = float(angle_raw) if angle_raw is not None else None
        
        out.append(AppliedForce(
            magnitude_n=float(mag_raw),
            direction=str(f.get("direction") or "unspecified"),
            angle_deg=angle_deg,
            reference_frame=str(f.get("reference_frame") or "horizontal"),
        ))
    return out


def _map_visual_features(raw_vf: dict, object_ids: list[str]) -> VisualFeatures:
    force_mentions = [
        ForceMention(
            force_type=str(fm.get("force_type", "applied")),
            provenance=str(fm.get("provenance", "")),
            direction_hint=str(fm.get("direction_hint", "unspecified")),
        )
        for fm in raw_vf.get("force_mentions", [])
    ]

    constraints = [
        ConstraintRelationship(
            kind=str(cr.get("kind", "rope")),
            object_a_id=str(cr.get("object_a_id") or (object_ids[0] if object_ids else "object_1")),
            object_b_id=str(cr.get("object_b_id") or (object_ids[1] if len(object_ids) > 1 else "")),
        )
        for cr in raw_vf.get("constraint_relationships", [])
    ]

    return VisualFeatures(
        object_types=raw_vf.get("object_types") or [],
        surface_type=str(raw_vf.get("surface_type") or "unknown"),
        motion_state=str(raw_vf.get("motion_state") or "unknown"),
        requested_view=str(raw_vf.get("requested_view") or "unknown"),
        force_mentions=force_mentions,
        constraint_relationships=constraints,
        known_quantities=raw_vf.get("known_quantities") or [],
        unknown_quantities=raw_vf.get("unknown_quantities") or [],
        ambiguity_flags=[],   # LLM doesn't emit ambiguity flags in this schema
    )


def _missing_slots(scenario: str | None, objects: list[ObjectSpec], geometry: Geometry) -> list[str]:
    if scenario is None:
        return ["scenario_type"]
    missing: list[str] = []
    for slot in REQUIRED_SLOTS.get(scenario, []):
        present = {
            "mass_kg":            bool(objects and objects[0].mass_kg is not None),
            "mass_kg_list_min2":  len([o for o in objects if o.mass_kg is not None]) >= 2,
            "incline_angle_deg":  geometry.incline_angle_deg is not None,
            "projectile_angle_deg": geometry.projectile_angle_deg is not None,
            "initial_speed_ms":   geometry.initial_speed_ms is not None,
        }.get(slot, False)
        if not present:
            missing.append(slot)
    return missing


# ── Public entry point ────────────────────────────────────────────────────────

def parse_with_llm(text: str) -> ParseResult:
    """Parse a physics problem using the Ollama qwen2.5:7b model.

    Falls back gracefully: if Ollama is unreachable or returns garbage the
    exception propagates to the caller (pipeline.py catches it).

    Args:
        text: Raw natural-language physics problem.

    Returns:
        ParseResult populated from the LLM's JSON response.

    Raises:
        httpx.ConnectError: Ollama is not running.
        ValueError: Model returned unusable output.
    """
    logger.debug("LLM parse request: %s", text[:120])
    data = _call_ollama(text)

    scenario_type: str | None = data.get("scenario_type")
    confidence: float = float(data.get("confidence") or 0.0)

    # If the LLM skips classification, fall back to the deterministic classifier
    # so downstream code always gets a scenario.
    if scenario_type is None:
        scenario_type, confidence = classify_scenario(text)

    objects = _map_objects(data.get("objects") or [])
    geometry = _map_geometry(data.get("geometry") or {})
    applied_forces = _map_applied_forces(data.get("applied_forces") or [])
    unknowns: list[str] = data.get("unknowns") or []

    friction_raw = data.get("friction")
    friction: str | None = str(friction_raw) if friction_raw else None
    mu_raw = data.get("mu")
    mu: float | None = float(mu_raw) if mu_raw is not None else None

    object_ids = [o.id for o in objects]
    visual_features = _map_visual_features(data.get("visual_features") or {}, object_ids)

    # Reconcile angle ambiguity the same way the deterministic parser does.
    if scenario_type == "inclined_plane" and geometry.incline_angle_deg is None and geometry.projectile_angle_deg is not None:
        geometry.incline_angle_deg = geometry.projectile_angle_deg
    if scenario_type == "projectile_motion" and geometry.projectile_angle_deg is None and geometry.incline_angle_deg is not None:
        geometry.projectile_angle_deg = geometry.incline_angle_deg

    missing_required = _missing_slots(scenario_type, objects, geometry)

    logger.debug("LLM parse result: scenario=%s confidence=%.2f missing=%s", scenario_type, confidence, missing_required)

    return ParseResult(
        scenario_type=scenario_type,
        confidence=confidence,
        objects=objects,
        geometry=geometry,
        friction=friction,
        mu=mu,
        applied_forces=applied_forces,
        unknowns=unknowns,
        missing_required=missing_required,
        raw_text=text,
        visual_features=visual_features,
    )
