"""Natural-language parser composed of deterministic, testable stages."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from .classifier import REQUIRED_SLOTS, classify_scenario
from .schema import ParseResult
from .slots import extract_applied_forces, extract_friction, extract_geometry, extract_objects, extract_unknowns


@lru_cache(maxsize=1)
def _spacy_model() -> Any | None:
    """Load spaCy's dependency parser when installed, otherwise remain offline."""
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except (ImportError, OSError):
        return None


def _attach_spacy_nouns(text: str, objects: list) -> None:
    """Use dependency parsing to improve object labels without affecting values."""
    nlp = _spacy_model()
    if nlp is None:
        return
    doc = nlp(text)
    noun_tokens = [token for token in doc if token.pos_ in {"NOUN", "PROPN"}]
    for obj, token in zip(objects, noun_tokens):
        # Prefer mass's governing noun, e.g. 'box of mass 5 kg'.
        if token.lemma_.lower() in {"box", "block", "crate", "ball", "sphere", "cart", "object"}:
            obj.label = token.text.lower()


def _missing_slots(scenario: str | None, objects: list, geometry) -> list[str]:
    if scenario is None:
        return ["scenario_type"]
    missing: list[str] = []
    for slot in REQUIRED_SLOTS[scenario]:
        present = {
            "mass_kg": bool(objects and objects[0].mass_kg is not None),
            "mass_kg_list_min2": len([o for o in objects if o.mass_kg is not None]) >= 2,
            "incline_angle_deg": geometry.incline_angle_deg is not None,
            "projectile_angle_deg": geometry.projectile_angle_deg is not None,
            "initial_speed_ms": geometry.initial_speed_ms is not None,
        }[slot]
        if not present:
            missing.append(slot)
    return missing


def parse(text: str) -> ParseResult:
    """Parse one question into the project's stable schema."""
    scenario, confidence = classify_scenario(text)
    objects = extract_objects(text)
    _attach_spacy_nouns(text, objects)
    geometry = extract_geometry(text)
    # A generic angle follows classifier context when geometry extraction was ambiguous.
    if scenario == "inclined_plane" and geometry.incline_angle_deg is None and geometry.projectile_angle_deg is not None:
        geometry.incline_angle_deg = geometry.projectile_angle_deg
    if scenario == "projectile_motion" and geometry.projectile_angle_deg is None and geometry.incline_angle_deg is not None:
        geometry.projectile_angle_deg = geometry.incline_angle_deg
    friction, mu = extract_friction(text)
    return ParseResult(
        scenario_type=scenario,
        confidence=confidence,
        objects=objects,
        geometry=geometry,
        friction=friction,
        mu=mu,
        applied_forces=extract_applied_forces(text),
        unknowns=extract_unknowns(text),
        missing_required=_missing_slots(scenario, objects, geometry),
        raw_text=text,
    )
