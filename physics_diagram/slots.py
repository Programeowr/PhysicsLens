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
    """Extract friction type and coefficient with improved pattern matching.
    
    Handles:
    - "frictionless" / "no friction" → ("frictionless", 0.0)
    - "coefficient of friction is 0.3" → ("kinetic", 0.3)
    - "μ = 0.25" → ("kinetic", 0.25)
    - "mu = 0.15" → ("kinetic", 0.15)
    - "static friction coefficient 0.4" → ("static", 0.4)
    - "kinetic friction 0.2" → ("kinetic", 0.2)
    - "rough surface" → (None, None) — indicates friction present but value unknown
    """
    lower = replace_spelled_numbers(text.lower())
    
    # Explicit frictionless
    if any(phrase in lower for phrase in ["frictionless", "no friction", "without friction", "zero friction"]):
        return "frictionless", 0.0
    
    # Try multiple coefficient patterns (most specific first)
    patterns = [
        # "coefficient of kinetic friction = 0.3" or "μ_k = 0.3"
        (r'coefficient\s+of\s+kinetic\s+friction\s*(?:is|=)?\s*([-+]?\d+(?:\.\d+)?)', "kinetic"),
        (r'μ_?k\s*=\s*([-+]?\d+(?:\.\d+)?)', "kinetic"),
        (r'mu_?k\s*=\s*([-+]?\d+(?:\.\d+)?)', "kinetic"),
        
        # "coefficient of static friction = 0.4" or "μ_s = 0.4"
        (r'coefficient\s+of\s+static\s+friction\s*(?:is|=)?\s*([-+]?\d+(?:\.\d+)?)', "static"),
        (r'μ_?s\s*=\s*([-+]?\d+(?:\.\d+)?)', "static"),
        (r'mu_?s\s*=\s*([-+]?\d+(?:\.\d+)?)', "static"),
        
        # Generic "coefficient of friction = 0.3" or "μ = 0.3"
        (r'coefficient\s+of\s+friction\s+(?:between\s+.{1,50}?\s+)?(?:is|=)?\s*([-+]?\d+(?:\.\d+)?)', "kinetic"),
        (r'friction\s+coefficient\s*(?:is|=)?\s*([-+]?\d+(?:\.\d+)?)', "kinetic"),
        (r'μ\s*=\s*([-+]?\d+(?:\.\d+)?)', "kinetic"),
        (r'\bmu\s*=\s*([-+]?\d+(?:\.\d+)?)', "kinetic"),
        
        # "kinetic friction 0.2" or "static friction 0.4"
        (r'kinetic\s+friction\s*(?:is|of|:)?\s*([-+]?\d+(?:\.\d+)?)', "kinetic"),
        (r'static\s+friction\s*(?:is|of|:)?\s*([-+]?\d+(?:\.\d+)?)', "static"),
        
        # "with friction 0.15" or "friction of 0.25"
        (r'(?:with\s+)?friction\s+(?:of\s+)?([-+]?\d+(?:\.\d+)?)(?!\s*n\b)', "kinetic"),  # negative lookahead to avoid "friction force 30 N"
    ]
    
    for pattern, friction_type in patterns:
        match = re.search(pattern, lower)
        if match:
            return friction_type, float(match.group(1))
    
    # Qualitative friction indicators (no numeric value)
    if any(phrase in lower for phrase in ["rough surface", "rough floor", "rough incline", "with friction"]):
        return "kinetic", None  # indicates friction present but magnitude unknown
    
    return None, None


def extract_applied_forces(text: str) -> list[AppliedForce]:
    """Extract applied forces with magnitude, direction, and angle information.
    
    Handles patterns like:
    - "60 N force" → 60 N, unspecified direction
    - "100 N to the right" → 100 N, right
    - "50 N at 30° above horizontal" → 50 N, angle=30°
    - "80 N parallel to incline" → 80 N, reference_frame=incline
    """
    forces: list[AppliedForce] = []
    quantities = extract_quantities(text)
    
    for quantity in quantities:
        if quantity.unit.lower() not in {"n", "newton", "newtons"}:
            continue
            
        # Look at context around the force mention (±50 chars)
        nearby = text[max(0, quantity.start - 50):quantity.end + 50].lower()
        
        # Detect angle specification
        angle_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:degree|°)\s*(?:above|below)?\s*(?:the\s+)?(?:horizontal|vertical)?', nearby)
        angle_deg = float(angle_match.group(1)) if angle_match else None
        
        # Detect reference frame
        if any(phrase in nearby for phrase in ["parallel to incline", "parallel to ramp", "parallel to slope", "along incline", "along ramp"]):
            reference_frame = "incline"
        elif any(phrase in nearby for phrase in ["above horizontal", "below horizontal", "angle with horizontal", "horizontal"]):
            reference_frame = "horizontal"
        elif "vertical" in nearby:
            reference_frame = "vertical"
        else:
            reference_frame = "horizontal"  # default
        
        # Detect direction (simple left/right/up/down)
        if "right" in nearby:
            direction = "right"
        elif "left" in nearby:
            direction = "left"
        elif "uphill" in nearby or "up" in nearby:
            direction = "uphill"
        elif "down" in nearby:
            direction = "down"
        else:
            direction = "unspecified"
        
        forces.append(AppliedForce(
            magnitude_n=quantity.value,
            direction=direction,
            angle_deg=angle_deg,
            reference_frame=reference_frame
        ))
    
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
