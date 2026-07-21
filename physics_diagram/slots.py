"""Convert extracted quantities into parser slots."""

from __future__ import annotations

import re
from typing import Optional

from .quantities import Quantity, angle_to_degrees, extract_quantities, mass_to_kg, replace_spelled_numbers, speed_to_ms
from .schema import AppliedForce, Geometry, ObjectSpec


def _mass_quantities(text: str) -> list[Quantity]:
    return [q for q in extract_quantities(text) if q.unit.lower() in {"kg", "kgs", "g", "gram", "grams", "lb", "lbs"}]


def extract_objects(text: str) -> list[ObjectSpec]:
    """Extract mass-bearing objects in text order.

    The parser module also uses spaCy dependencies when its model is present;
    this deterministic fallback makes the project usable before model download.
    """
    normalized = replace_spelled_numbers(text.lower())
    nouns = r"box|block|crate|mass|object|ball|sphere|body|cart|weight"
    objects: list[ObjectSpec] = []
    for index, quantity in enumerate(_mass_quantities(normalized), start=1):
        before = normalized[max(0, quantity.start - 50):quantity.start]
        noun_match = list(re.finditer(rf"\b({nouns})\b", before))
        noun = noun_match[-1].group(1) if noun_match else "mass"
        shape = "sphere" if noun in {"ball", "sphere"} else "box"
        objects.append(ObjectSpec(id=f"object_{index}", shape=shape, mass_kg=mass_to_kg(quantity.value, quantity.unit), label=noun))
    return objects


def extract_geometry(text: str) -> Geometry:
    quantities = extract_quantities(text)
    angles = [angle_to_degrees(q.value, q.unit) for q in quantities if q.unit.lower() in {"degree", "degrees", "deg", "°", "radian", "radians", "rad"}]
    speeds = [speed_to_ms(q.value, q.unit) for q in quantities if q.unit.lower() in {"m/s", "mps", "km/h", "kmph", "mph"}]
    lower = text.lower()
    incline_angle = angles[0] if angles and any(k in lower for k in ("incline", "ramp", "slope", "inclination")) else None
    projectile_angle = angles[0] if angles and any(k in lower for k in ("launch", "throw", "fired", "projectile", "trajectory")) else None
    # A sentence may say only 'at 30 degrees'; parser classification resolves the use later.
    return Geometry(incline_angle_deg=incline_angle, projectile_angle_deg=projectile_angle, initial_speed_ms=speeds[0] if speeds else None)


def extract_friction(text: str) -> tuple[Optional[str], Optional[float]]:
    lower = replace_spelled_numbers(text.lower())
    if "frictionless" in lower or "no friction" in lower:
        return "frictionless", 0.0
    match = re.search(r"(?:coefficient of friction|coefficient|\bmu\b|μ)\s*(?:is|of|=)?\s*([-+]?\d+(?:\.\d+)?)", lower)
    if match:
        return "kinetic", float(match.group(1))
    return None, None


def extract_applied_forces(text: str) -> list[AppliedForce]:
    forces: list[AppliedForce] = []
    for quantity in extract_quantities(text):
        if quantity.unit.lower() in {"n", "newton", "newtons"}:
            nearby = text[max(0, quantity.start - 35):quantity.end + 35].lower()
            direction = "right" if "right" in nearby else "left" if "left" in nearby else "uphill" if "uphill" in nearby else "unspecified"
            forces.append(AppliedForce(quantity.value, direction))
    return forces


def extract_unknowns(text: str) -> list[str]:
    question = text.lower().split("?")[0].split(".")[-1]
    patterns = {
        "required_force": ("how much force", "what force", "force required", "keep it at rest"),
        "tension": ("tension",),
        "acceleration": ("acceleration", "accelerate"),
        "normal_force": ("normal force",),
        "range": ("range", "how far"),
        "max_height": ("maximum height", "max height"),
    }
    return [name for name, phrases in patterns.items() if any(phrase in question for phrase in phrases)]
