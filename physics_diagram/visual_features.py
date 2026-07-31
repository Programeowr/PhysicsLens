"""Extract visual-semantic features from raw problem text.

These features drive renderer decisions (shape, surface texture, arrow style,
diagram mode) without changing the solver inputs.  Every function in this
module is deterministic and side-effect free so it is safe to cache.
"""

from __future__ import annotations

import re

from .schema import (
    AmbiguityFlag,
    ConstraintRelationship,
    ForceMention,
    VisualFeatures,
)

# ──────────────────────────────────────────────────────────────────────────────
# Object-appearance extraction
# ──────────────────────────────────────────────────────────────────────────────

# Maps raw noun → canonical object_type value used by the renderer.
_OBJECT_TYPE_MAP: dict[str, str] = {
    "box": "box",
    "crate": "crate",
    "block": "block",
    "cart": "cart",
    "ball": "ball",
    "sphere": "sphere",
    "projectile": "projectile",
    "bullet": "projectile",
    "particle": "particle",
    "body": "block",
    "object": "block",
    "mass": "block",
    "masses": "block",          # plural form
    "weight": "hanging_mass",
    "weights": "hanging_mass",  # plural form
    "hanging mass": "hanging_mass",
    "hanging masses": "hanging_mass",
    "hanging weight": "hanging_mass",
    "hanging weights": "hanging_mass",
    "pulley mass": "pulley_mass",
    "pulley masses": "pulley_mass",
    "spring endpoint": "spring_endpoint",
    "spring end": "spring_endpoint",
    "bob": "hanging_mass",
}

# Order matters: longer phrases before shorter ones so "hanging masses" beats "masses".
_OBJECT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(_OBJECT_TYPE_MAP, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def extract_object_types(text: str, num_objects: int) -> tuple[list[str], list[AmbiguityFlag]]:
    """Return one object_type string per parsed object plus any ambiguity flags.

    We walk through all noun matches in text order and take the first
    ``num_objects`` distinct positions.  When ``num_objects`` is 0 but the
    text still contains a recognisable object noun (e.g. "A ball is launched")
    we still return it so callers that only have the raw text get useful data.
    When no noun is found for a slot we fall back to "block" (conservative
    default) and flag the ambiguity.
    """
    matches = _OBJECT_PATTERN.findall(text.lower())
    # Deduplicate while preserving order (first occurrence wins for each slot).
    seen: list[str] = []
    for m in matches:
        canonical = _OBJECT_TYPE_MAP.get(m, "block")
        if canonical not in seen:
            seen.append(canonical)

    # When the mass extractor found no objects but the text has recognisable
    # nouns (e.g. "A ball is launched…"), honour whatever num_objects the
    # caller requests but use the nouns we found.
    effective_n = max(num_objects, len(seen)) if num_objects == 0 else num_objects

    flags: list[AmbiguityFlag] = []
    result: list[str] = []
    for i in range(effective_n):
        if i < len(seen):
            result.append(seen[i])
        else:
            result.append("block")
            flags.append(AmbiguityFlag(
                field="object_type",
                reason=f"No recognisable object noun found for object {i + 1}; defaulting to 'block'.",
                confidence=0.0,
            ))
    return result, flags


# ──────────────────────────────────────────────────────────────────────────────
# Surface / environment extraction
# ──────────────────────────────────────────────────────────────────────────────

_SURFACE_RULES: list[tuple[re.Pattern[str], str]] = [
    # Most-specific patterns first.
    (re.compile(r"\bfrictionless\s+(?:inclined?\s+)?(?:plane|ramp|slope|surface)\b", re.I), "frictionless_ramp"),
    (re.compile(r"\bfrictionless\b", re.I), "frictionless_ramp"),
    (re.compile(r"\brough\s+(?:inclined?\s+)?(?:plane|ramp|slope)\b", re.I), "inclined_plane"),
    (re.compile(r"\b(?:inclined?\s+plane|incline|ramp|slope)\b", re.I), "inclined_plane"),
    (re.compile(r"\brough\s+(?:floor|surface|ground)\b", re.I), "rough_floor"),
    (re.compile(r"\brough\b", re.I), "rough_floor"),
    (re.compile(r"\bsmooth\s+(?:floor|surface|table)\b", re.I), "smooth_floor"),
    (re.compile(r"\bpulley\b", re.I), "pulley_support"),
    (re.compile(r"\batwood\b", re.I), "pulley_support"),
    (re.compile(r"\bspring\s+anchor\b", re.I), "spring_anchor"),
    (re.compile(r"\bspring\b", re.I), "spring_anchor"),
    (re.compile(r"\btable\b", re.I), "table"),
    (re.compile(r"\bfloor\b", re.I), "rough_floor"),
    (re.compile(r"\bground\b", re.I), "ground"),
    (re.compile(r"\bhorizontal\s+(?:surface|plane)\b", re.I), "smooth_floor"),
    (re.compile(r"\bflat\s+surface\b", re.I), "smooth_floor"),
    (re.compile(r"\bair\s+resistance\b", re.I), "air"),
    (re.compile(r"\b(?:thrown|launched|projectile|fired)\b", re.I), "ground"),
]


def extract_surface_type(text: str) -> tuple[str, list[AmbiguityFlag]]:
    """Return the dominant surface/environment cue and any ambiguity flag."""
    for pattern, surface in _SURFACE_RULES:
        if pattern.search(text):
            return surface, []
    return "unknown", [AmbiguityFlag(
        field="surface_type",
        reason="No recognisable surface or environment cue found.",
        confidence=0.0,
    )]


# ──────────────────────────────────────────────────────────────────────────────
# Motion-state extraction
# ──────────────────────────────────────────────────────────────────────────────

_MOTION_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bat\s+rest\b", re.I), "at_rest"),
    (re.compile(r"\bkeep\s+it\s+at\s+rest\b", re.I), "at_rest"),
    (re.compile(r"\bstationary\b", re.I), "at_rest"),
    (re.compile(r"\bequilibrium\b", re.I), "equilibrium"),
    (re.compile(r"\bmoving\s+up\s+(?:the\s+)?incline\b", re.I), "moving_up_incline"),
    (re.compile(r"\bsliding\s+up\b", re.I), "moving_up_incline"),
    (re.compile(r"\bslides\s+up\b", re.I), "moving_up_incline"),
    (re.compile(r"\bmoves?\s+up\s+(?:the\s+)?incline\b", re.I), "moving_up_incline"),
    (re.compile(r"\bmoving\s+down\s+(?:the\s+)?incline\b", re.I), "moving_down_incline"),
    (re.compile(r"\bsliding\s+down\b", re.I), "moving_down_incline"),
    (re.compile(r"\bslides\s+down\b", re.I), "moving_down_incline"),
    (re.compile(r"\bmoves?\s+down\s+(?:the\s+)?(?:incline|slope|ramp)\b", re.I), "moving_down_incline"),
    (re.compile(r"\bdescend(?:ing|s)?\b", re.I), "descending"),
    (re.compile(r"\blaunch(?:ed|es)?\b", re.I), "launched_upward"),
    (re.compile(r"\bthrown\s+upward\b", re.I), "launched_upward"),
    (re.compile(r"\bfired\b", re.I), "launched_upward"),
    (re.compile(r"\bproject(?:ile|ed)\b", re.I), "launched_upward"),
    (re.compile(r"\baccelerat(?:ing|es|ion)\b", re.I), "accelerating"),
    (re.compile(r"\bdecelerat(?:ing|es|ion)\b", re.I), "decelerating"),
    # left/right sliding/moving — handled by special-case below; listed here
    # only to document the canonical states; the special-case runs first.
    (re.compile(r"\bmoving\s+(?:to\s+the\s+)?right\b", re.I), "moving_right"),
    (re.compile(r"\bmoving\s+(?:to\s+the\s+)?left\b", re.I), "moving_left"),
    (re.compile(r"\bmoves\s+(?:to\s+the\s+)?right\b", re.I), "moving_right"),
    (re.compile(r"\bmoves\s+(?:to\s+the\s+)?left\b", re.I), "moving_left"),
    (re.compile(r"\bmoves?\b", re.I), "unknown"),  # motion mentioned but direction unclear
]

# Covers "sliding/slides/slide left/right"
_SLIDE_DIRECTION_RE = re.compile(
    r"\bslid(?:ing|es?)\s+(?:to\s+the\s+)?(left|right)\b", re.I
)


def extract_motion_state(text: str) -> tuple[str, list[AmbiguityFlag]]:
    """Return the best-matching motion state and any ambiguity flag."""
    # Special case: sliding/slides left/right (runs before the main rule table)
    slide_match = _SLIDE_DIRECTION_RE.search(text)
    if slide_match:
        return f"moving_{slide_match.group(1).lower()}", []

    for pattern, state in _MOTION_RULES:
        if pattern.search(text):
            if state == "unknown":
                return "unknown", [AmbiguityFlag(
                    field="motion_state",
                    reason="Motion mentioned but direction/state cannot be inferred from the text.",
                    confidence=0.3,
                )]
            return state, []

    return "unknown", [AmbiguityFlag(
        field="motion_state",
        reason="No motion cue found; state is indeterminate.",
        confidence=0.0,
    )]


# ──────────────────────────────────────────────────────────────────────────────
# Requested diagram view extraction
# ──────────────────────────────────────────────────────────────────────────────

_VIEW_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bfull\s+scene\b.*\bfbd\b|\bfbd\b.*\bfull\s+scene\b", re.I), "scene_and_fbd"),
    (re.compile(r"\bfree[- ]?body\s+diagram\b", re.I), "fbd"),
    (re.compile(r"\bfbd\b", re.I), "fbd"),
    (re.compile(r"\bshow\s+(?:force\s+)?components\b", re.I), "components"),
    (re.compile(r"\bcomponent\s+diagram\b", re.I), "components"),
    (re.compile(r"\btrajectory\b", re.I), "trajectory"),
    (re.compile(r"\bshow\s+(?:the\s+)?trajectory\b", re.I), "trajectory"),
    (re.compile(r"\bshow\s+(?:the\s+)?velocity\b", re.I), "velocity_diagram"),
    (re.compile(r"\bvelocity\s+diagram\b", re.I), "velocity_diagram"),
    (re.compile(r"\bshow\s+(?:the\s+)?acceleration\b", re.I), "acceleration_diagram"),
    (re.compile(r"\bsymbolic\s+(?:labels?|only)\b", re.I), "symbolic"),
    (re.compile(r"\bnumeric\s+(?:labels?|only)\b", re.I), "numeric"),
]


def extract_requested_view(text: str) -> tuple[str, list[AmbiguityFlag]]:
    """Return the explicit diagram view requested in the text, or 'unknown'."""
    for pattern, view in _VIEW_RULES:
        if pattern.search(text):
            return view, []
    return "unknown", []   # no flag — 'unknown' just means use the default


# ──────────────────────────────────────────────────────────────────────────────
# Force-mention extraction (provenance)
# ──────────────────────────────────────────────────────────────────────────────

# (regex pattern, force_type, direction_hint)
_FORCE_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    # Weight / gravity
    (re.compile(r"\b(?:weight|gravitational\s+force|force\s+of\s+gravity|gravity)\b", re.I), "weight", "down"),
    # Normal force
    (re.compile(r"\bnormal\s+force\b", re.I), "normal", "up"),
    # Friction variants
    (re.compile(r"\bkinetic\s+friction\b", re.I), "friction", "unspecified"),
    (re.compile(r"\bstatic\s+friction\b", re.I), "friction", "unspecified"),
    (re.compile(r"\bfriction\s+force\b|\bfrictional\s+force\b", re.I), "friction", "unspecified"),
    (re.compile(r"\bfriction\b", re.I), "friction", "unspecified"),
    # Tension
    (re.compile(r"\btension\s+in\s+the\s+(?:string|rope|cord|cable)\b", re.I), "tension", "up"),
    (re.compile(r"\btension\b", re.I), "tension", "unspecified"),
    # Spring force
    (re.compile(r"\bspring\s+(?:force|constant)\b|\bhooke['']?s\s+law\b", re.I), "spring", "unspecified"),
    # Air resistance
    (re.compile(r"\bair\s+resistance\b|\bdrag\b", re.I), "air_resistance", "unspecified"),
    # Push / applied rightward — allow up to ~5 words between verb and direction
    (re.compile(r"\bpush(?:ed|es|ing)?\b(?:\s+\w+){0,5}\s+(?:to\s+the\s+)?right\b", re.I), "applied", "right"),
    (re.compile(r"\bpush(?:ed|es|ing)?\b(?:\s+\w+){0,5}\s+(?:to\s+the\s+)?left\b", re.I), "applied", "left"),
    (re.compile(r"\bpush(?:ed|es|ing)?\b", re.I), "applied", "unspecified"),
    # Pull
    (re.compile(r"\bpull(?:ed|s|ing)?\b(?:\s+\w+){0,5}\s+(?:to\s+the\s+)?right\b", re.I), "applied", "right"),
    (re.compile(r"\bpull(?:ed|s|ing)?\b(?:\s+\w+){0,5}\s+(?:to\s+the\s+)?left\b", re.I), "applied", "left"),
    (re.compile(r"\bpull(?:ed|s|ing)?\b", re.I), "applied", "unspecified"),
    # Applied force generic
    (re.compile(r"\bapplied\s+force\b", re.I), "applied", "unspecified"),
    (re.compile(r"\bacts?\s+on\b", re.I), "applied", "unspecified"),
    # Component forces
    (re.compile(r"\b(?:horizontal|vertical)\s+component\s+of\b", re.I), "component", "unspecified"),
]


def extract_force_mentions(text: str) -> list[ForceMention]:
    """Extract every force the problem text names, preserving the raw phrase."""
    mentions: list[ForceMention] = []
    seen_types: set[str] = set()

    for pattern, force_type, direction_hint in _FORCE_PATTERNS:
        match = pattern.search(text)
        if match:
            provenance = match.group(0)
            # Allow the same force_type to appear more than once only when the
            # provenance differs (e.g. "friction" and "kinetic friction").
            key = (force_type, provenance.lower())
            if key not in seen_types:
                seen_types.add(key)
                mentions.append(ForceMention(
                    force_type=force_type,
                    provenance=provenance,
                    direction_hint=direction_hint,
                ))
    return mentions


# ──────────────────────────────────────────────────────────────────────────────
# Constraint-relationship extraction
# ──────────────────────────────────────────────────────────────────────────────

_CONSTRAINT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bpulley\b", re.I), "pulley_rope"),
    (re.compile(r"\bstring\b", re.I), "string"),
    (re.compile(r"\brope\b", re.I), "rope"),
    (re.compile(r"\bcord\b", re.I), "rope"),
    (re.compile(r"\bcable\b", re.I), "rope"),
    (re.compile(r"\bspring\b", re.I), "spring"),
    (re.compile(r"\bcontact\b", re.I), "contact"),
]


def extract_constraint_relationships(text: str, object_ids: list[str]) -> list[ConstraintRelationship]:
    """Return structural links implied by the problem text."""
    constraints: list[ConstraintRelationship] = []
    seen_kinds: set[str] = set()
    a_id = object_ids[0] if object_ids else "object_1"
    b_id = object_ids[1] if len(object_ids) > 1 else ""

    for pattern, kind in _CONSTRAINT_PATTERNS:
        if kind in seen_kinds:
            continue
        if pattern.search(text):
            seen_kinds.add(kind)
            constraints.append(ConstraintRelationship(kind=kind, object_a_id=a_id, object_b_id=b_id))
    return constraints


# ──────────────────────────────────────────────────────────────────────────────
# Known / unknown quantity classification
# ──────────────────────────────────────────────────────────────────────────────

_KNOWN_SIGNALS: dict[str, re.Pattern[str]] = {
    "mass": re.compile(r"\b\d[\d.]*\s*(?:kg|g|gram|lb)\b", re.I),
    "angle": re.compile(r"\b\d[\d.]*\s*(?:degree|degrees?|deg|°)\b", re.I),
    "speed": re.compile(r"\b\d[\d.]*\s*(?:m/s|km/h|mph|mps)\b", re.I),
    "friction_coefficient": re.compile(r"\b(?:coefficient\s+of\s+friction|mu|μ)\s*(?:is|=)?\s*[\d.]+", re.I),
    "applied_force": re.compile(r"\b\d[\d.]*\s*(?:n|newton|newtons)\b", re.I),
    "spring_constant": re.compile(r"\b\d[\d.]*\s*(?:n/m|n\s*/\s*m)\b", re.I),
}

_UNKNOWN_SIGNALS: dict[str, re.Pattern[str]] = {
    "required_force": re.compile(r"\bhow\s+much\s+force\b|\bforce\s+required\b|\bwhat\s+force\b", re.I),
    "tension": re.compile(r"\bfind\s+the\s+tension\b|\bwhat\s+is\s+the\s+tension\b", re.I),
    "acceleration": re.compile(r"\bfind\s+the\s+acceleration\b|\bwhat\s+is\s+the\s+acceleration\b|\bacceleration\s+of\b", re.I),
    "normal_force": re.compile(r"\bnormal\s+force\b.*\?|\bfind\s+(?:the\s+)?normal\b", re.I),
    "range": re.compile(r"\bhow\s+far\b|\brange\b.*\?", re.I),
    "max_height": re.compile(r"\bmaximum\s+height\b|\bmax\s+height\b", re.I),
    "velocity": re.compile(r"\bfind\s+(?:the\s+)?velocity\b|\bwhat\s+is\s+the\s+velocity\b", re.I),
}


def extract_known_unknown(text: str) -> tuple[list[str], list[str]]:
    """Return lists of known and unknown quantity names."""
    known = [name for name, pattern in _KNOWN_SIGNALS.items() if pattern.search(text)]
    unknown = [name for name, pattern in _UNKNOWN_SIGNALS.items() if pattern.search(text)]
    return known, unknown


# ──────────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────────

def extract_visual_features(
    text: str,
    object_ids: list[str],
    scenario_type: str | None,
) -> VisualFeatures:
    """Build the complete VisualFeatures for one problem statement.

    Parameters
    ----------
    text:
        The raw problem text as the user typed it.
    object_ids:
        The ``id`` fields of the ObjectSpec instances already extracted by
        ``extract_objects`` — used to label constraint relationships correctly.
    scenario_type:
        The classified scenario (may be None when classification failed).
    """
    num_objects = len(object_ids)
    all_flags: list[AmbiguityFlag] = []

    # Pass num_objects=0 only when there truly are no objects; the extractor
    # will still scan for nouns and return what it finds.
    object_types, obj_flags = extract_object_types(text, num_objects)
    all_flags.extend(obj_flags)

    surface_type, surf_flags = extract_surface_type(text)
    all_flags.extend(surf_flags)

    motion_state, motion_flags = extract_motion_state(text)
    all_flags.extend(motion_flags)

    requested_view, view_flags = extract_requested_view(text)
    all_flags.extend(view_flags)

    force_mentions = extract_force_mentions(text)

    # Use the richer object_ids list for constraint anchors; fall back to
    # synthetic ids when the type extractor found objects the mass extractor
    # missed (e.g. massless balls in projectile problems).
    effective_ids = object_ids or [f"object_{i+1}" for i in range(len(object_types))]
    constraints = extract_constraint_relationships(text, effective_ids)
    known_quantities, unknown_quantities = extract_known_unknown(text)

    # ── Scenario-level ambiguity: no object noun found at all ────────────────
    if not object_types and num_objects == 0 and scenario_type is None:
        all_flags.append(AmbiguityFlag(
            field="object_type",
            reason="No objects and no scenario could be identified.",
            confidence=0.0,
        ))

    return VisualFeatures(
        object_types=object_types,
        surface_type=surface_type,
        motion_state=motion_state,
        requested_view=requested_view,
        force_mentions=force_mentions,
        constraint_relationships=constraints,
        known_quantities=known_quantities,
        unknown_quantities=unknown_quantities,
        ambiguity_flags=all_flags,
    )
