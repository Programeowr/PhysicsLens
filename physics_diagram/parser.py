"""Natural-language parser composed of deterministic, testable stages."""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from .classifier import REQUIRED_SLOTS, classify_scenario
from .schema import ParseResult
from .slots import extract_applied_forces, extract_friction, extract_geometry, extract_objects, extract_unknowns
from .visual_features import extract_visual_features

logger = logging.getLogger(__name__)

# ── Log file for incomplete parses ───────────────────────────────────────────
_PARSE_FAILURE_LOG = Path("parse_failures.log")


def _log_incomplete_parse(text: str, missing: list[str]) -> None:
    """Append incomplete parse attempts to a log file for review."""
    try:
        with _PARSE_FAILURE_LOG.open("a", encoding="utf-8") as f:
            import datetime
            timestamp = datetime.datetime.now(datetime.UTC).isoformat()
            f.write(f"[{timestamp}] Missing: {', '.join(missing)}\n")
            f.write(f"Text: {text.strip()}\n\n")
    except OSError as exc:
        logger.warning("Failed to write parse failure log: %s", exc)


# ── Text normalization ───────────────────────────────────────────────────────

def _normalize_text(text: str) -> str:
    """Rewrite common phrasings to canonical forms that extractors recognize.
    
    This preprocessing step handles synonyms and word order variations without
    requiring new regex patterns for every variation.
    """
    normalized = text.lower()
    
    # Unit normalization (must come before number replacement)
    normalized = re.sub(r'\bkilograms?\b', 'kg', normalized)
    normalized = re.sub(r'\bgrams?\b', 'g', normalized)
    normalized = re.sub(r'\bpounds?\b', 'lb', normalized)
    normalized = re.sub(r'\bdegrees?\b', 'degree', normalized)
    normalized = re.sub(r'\bradians?\b', 'radian', normalized)
    normalized = re.sub(r'\bnewtons?\b', 'n', normalized)
    normalized = re.sub(r'\bmeters?\s+per\s+second\b', 'm/s', normalized)
    
    # Remove "at an angle" phrasing to avoid projectile mis-classification
    # Only keep it when projectile keywords are present
    if not any(kw in normalized for kw in ["throw", "launch", "projectile", "fired", "trajectory"]):
        normalized = re.sub(r'\bat\s+an?\s+angle\b', '', normalized)
    
    # Angle variations → canonical "at X degrees" or "X degree"
    normalized = re.sub(r'(?:making|at|with)\s+an?\s+angle\s+of\s+', '', normalized)
    normalized = re.sub(r'inclined\s+at\s+', 'incline ', normalized)
    normalized = re.sub(r'tilted\s+(?:at\s+)?', 'incline ', normalized)
    
    # Mass variations → "mass X kg" or "X kg"
    normalized = re.sub(r'(?:has|with)\s+a\s+mass\s+of\s+', 'mass ', normalized)
    normalized = re.sub(r'weighing\s+', 'mass ', normalized)
    normalized = re.sub(r'weight\s+(?:of\s+)?(\d)', r'mass \1', normalized)
    
    # Force variations → "applied force"
    normalized = re.sub(r'force\s+(?:is\s+)?applied', 'applied force', normalized)
    normalized = re.sub(r'push(?:ed|ing)?\s+by', 'applied force', normalized)
    normalized = re.sub(r'pull(?:ed|ing)?\s+(?:using|with|by)', 'applied force', normalized)
    
    # Direction normalization
    normalized = re.sub(r'\bto\s+the\s+(right|left)\b', r'\1', normalized)
    normalized = re.sub(r'\bupward\b', 'up', normalized)
    normalized = re.sub(r'\bdownward\b', 'down', normalized)
    
    # Friction variations
    normalized = re.sub(r'coefficient\s+of\s+(?:kinetic\s+)?friction\s+(?:is|=)\s+', 'mu=', normalized)
    normalized = re.sub(r'μ\s*=\s*', 'mu=', normalized)
    normalized = re.sub(r'(?:with\s+)?(?:kinetic\s+)?friction\s+(?:coefficient\s+)?(?:of\s+)?mu\s*=\s*', 'mu=', normalized)
    
    # Remove filler words
    normalized = re.sub(r'\b(?:equals?|is)\b', '', normalized)
    
    return normalized


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
    """Parse one question into the project's stable schema.
    
    This deterministic parser normalizes input text, then extracts quantities
    and keywords using regex patterns. Incomplete parses are logged to
    parse_failures.log for review.
    """
    normalized = _normalize_text(text)
    scenario, confidence = classify_scenario(normalized)
    objects = extract_objects(normalized)
    _attach_spacy_nouns(normalized, objects)
    geometry = extract_geometry(normalized)
    # A generic angle follows classifier context when geometry extraction was ambiguous.
    if scenario == "inclined_plane" and geometry.incline_angle_deg is None and geometry.projectile_angle_deg is not None:
        geometry.incline_angle_deg = geometry.projectile_angle_deg
    if scenario == "projectile_motion" and geometry.projectile_angle_deg is None and geometry.incline_angle_deg is not None:
        geometry.projectile_angle_deg = geometry.incline_angle_deg
    friction, mu = extract_friction(normalized)
    object_ids = [o.id for o in objects]
    visual_features = extract_visual_features(normalized, object_ids, scenario)
    missing = _missing_slots(scenario, objects, geometry)
    
    # Log incomplete parses for review
    if missing:
        _log_incomplete_parse(text, missing)
    
    return ParseResult(
        scenario_type=scenario,
        confidence=confidence,
        objects=objects,
        geometry=geometry,
        friction=friction,
        mu=mu,
        applied_forces=extract_applied_forces(normalized),
        unknowns=extract_unknowns(normalized),
        missing_required=missing,
        raw_text=text,
        visual_features=visual_features,
    )
