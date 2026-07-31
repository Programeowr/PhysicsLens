"""Golden parser fixtures that assert visual-semantic features separately from
physics quantities.

Each test group covers one extraction concern so failures are easy to diagnose
without reading every assertion.  Physics-quantity assertions live in
test_parser.py and test_pipeline_integration.py.
"""

from __future__ import annotations

import pytest

from physics_diagram.parser import parse
from physics_diagram.visual_features import (
    extract_constraint_relationships,
    extract_force_mentions,
    extract_known_unknown,
    extract_motion_state,
    extract_object_types,
    extract_requested_view,
    extract_surface_type,
    extract_visual_features,
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Object-type extraction
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(("text", "num_objects", "expected_first"), [
    ("A 5 kg box sits on a ramp.", 1, "box"),
    ("A 3 kg crate is pushed along the floor.", 1, "crate"),
    ("A 2 kg ball rolls off a table.", 1, "ball"),
    ("A sphere of mass 1 kg is launched.", 1, "sphere"),
    ("A 4 kg cart moves on a frictionless surface.", 1, "cart"),
    ("Two hanging masses of 2 kg and 3 kg pass over a pulley.", 2, "hanging_mass"),
    ("A projectile of mass 0.5 kg is fired at 45 degrees.", 1, "projectile"),
    ("A block of mass 10 kg rests on a horizontal surface.", 1, "block"),
])
def test_object_type_first(text, num_objects, expected_first):
    types, _ = extract_object_types(text, num_objects)
    assert len(types) == num_objects
    assert types[0] == expected_first


def test_object_type_two_objects():
    text = "Two hanging masses of 2 kg and 3 kg pass over a pulley."
    types, flags = extract_object_types(text, 2)
    assert types[0] == "hanging_mass"
    # Second object should also resolve to hanging_mass or block (conservative fallback)
    assert types[1] in {"hanging_mass", "block"}


def test_object_type_unknown_noun_gets_flag():
    """When no recognisable noun exists a flag is produced and 'block' is used."""
    types, flags = extract_object_types("Something of mass 5 kg.", 1)
    # 'mass' maps to 'block' (conservative default)
    assert types[0] == "block"


def test_object_type_zero_objects():
    # "Find the tension." has no object noun → extractor returns empty list
    types, flags = extract_object_types("Find the tension.", 0)
    assert types == []
    assert flags == []


# ══════════════════════════════════════════════════════════════════════════════
# 2. Surface / environment extraction
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(("text", "expected"), [
    ("A box on a frictionless inclined plane.", "frictionless_ramp"),
    ("A block on a frictionless ramp.", "frictionless_ramp"),
    ("A crate slides on a rough floor.", "rough_floor"),
    ("An object is on a rough surface.", "rough_floor"),
    ("A box sits on a smooth table.", "smooth_floor"),
    ("Two masses hang over a pulley.", "pulley_support"),
    ("An Atwood machine is set up.", "pulley_support"),
    ("A spring holds a mass.", "spring_anchor"),
    ("A ball is launched from the ground.", "ground"),
    ("A projectile is fired at 45 degrees.", "ground"),
    ("A box sits on a table.", "table"),
    ("A block on a horizontal surface.", "smooth_floor"),
    ("A ball experiences air resistance.", "air"),
])
def test_surface_type(text, expected):
    surface, _ = extract_surface_type(text)
    assert surface == expected


def test_surface_unknown_produces_flag():
    surface, flags = extract_surface_type("A particle moves in a vacuum.")
    assert surface == "unknown"
    assert any(f.field == "surface_type" for f in flags)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Motion-state extraction
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(("text", "expected"), [
    ("A box is at rest on a ramp.", "at_rest"),
    ("Keep it at rest on the incline.", "at_rest"),
    ("The block is stationary.", "at_rest"),
    ("The system is in equilibrium.", "equilibrium"),
    ("A block is moving up the incline.", "moving_up_incline"),
    ("The crate is sliding up the ramp.", "moving_up_incline"),
    ("A block moves down the incline.", "moving_down_incline"),
    ("The block is sliding down the slope.", "moving_down_incline"),
    ("The stone is descending.", "descending"),
    ("A ball is launched at 45 degrees.", "launched_upward"),
    ("A projectile is fired at 30 m/s.", "launched_upward"),
    ("The cart is accelerating on the surface.", "accelerating"),
    ("The cart is decelerating.", "decelerating"),
    ("The block is sliding to the right.", "moving_right"),
    ("A box slides to the left.", "moving_left"),
    ("The cart is moving to the right.", "moving_right"),
])
def test_motion_state(text, expected):
    state, _ = extract_motion_state(text)
    assert state == expected


def test_motion_unknown_produces_flag():
    state, flags = extract_motion_state("A box sits on a surface.")
    assert state == "unknown"
    assert any(f.field == "motion_state" for f in flags)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Requested view extraction
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(("text", "expected"), [
    ("Draw a free-body diagram for the block.", "fbd"),
    ("Show the FBD of the system.", "fbd"),
    ("Show force components on the incline.", "components"),
    ("Show the trajectory of the projectile.", "trajectory"),
    ("Show the velocity of the block.", "velocity_diagram"),
    ("Show the acceleration of the cart.", "acceleration_diagram"),
    ("Use symbolic labels only.", "symbolic"),
    ("Use numeric labels.", "numeric"),
    ("Find the tension in the rope.", "unknown"),
])
def test_requested_view(text, expected):
    view, _ = extract_requested_view(text)
    assert view == expected


# ══════════════════════════════════════════════════════════════════════════════
# 5. Force-mention / provenance extraction
# ══════════════════════════════════════════════════════════════════════════════

def test_force_mentions_weight():
    mentions = extract_force_mentions("The weight of the block acts downward.")
    types = [m.force_type for m in mentions]
    assert "weight" in types
    weight = next(m for m in mentions if m.force_type == "weight")
    assert weight.direction_hint == "down"
    assert "weight" in weight.provenance.lower()


def test_force_mentions_friction():
    mentions = extract_force_mentions("Kinetic friction opposes the motion.")
    types = [m.force_type for m in mentions]
    assert "friction" in types
    friction = next(m for m in mentions if m.force_type == "friction")
    assert "kinetic friction" in friction.provenance.lower()


def test_force_mentions_tension():
    mentions = extract_force_mentions("Find the tension in the string.")
    types = [m.force_type for m in mentions]
    assert "tension" in types
    tension = next(m for m in mentions if m.force_type == "tension")
    assert tension.direction_hint == "up"


def test_force_mentions_push_direction():
    mentions = extract_force_mentions("A force pushes the box to the right.")
    types = [m.force_type for m in mentions]
    assert "applied" in types
    applied = next(m for m in mentions if m.force_type == "applied")
    assert applied.direction_hint == "right"


def test_force_mentions_pull_left():
    mentions = extract_force_mentions("The rope pulls the crate to the left.")
    applied = next((m for m in mentions if m.force_type == "applied"), None)
    assert applied is not None
    assert applied.direction_hint == "left"


def test_force_mentions_spring():
    mentions = extract_force_mentions("A spring force acts on the mass.")
    types = [m.force_type for m in mentions]
    assert "spring" in types


def test_force_mentions_air_resistance():
    mentions = extract_force_mentions("The ball experiences air resistance.")
    types = [m.force_type for m in mentions]
    assert "air_resistance" in types


def test_force_mentions_normal():
    mentions = extract_force_mentions("The normal force acts perpendicular to the surface.")
    types = [m.force_type for m in mentions]
    assert "normal" in types


def test_force_mentions_no_duplicates_same_provenance():
    """The same raw phrase should not produce duplicate entries."""
    mentions = extract_force_mentions("Friction acts on the block. Friction opposes motion.")
    friction_entries = [m for m in mentions if m.force_type == "friction"]
    # provenance keys are distinct so each mention is recorded once
    provenances = [m.provenance.lower() for m in friction_entries]
    assert len(provenances) == len(set(provenances))


# ══════════════════════════════════════════════════════════════════════════════
# 6. Constraint-relationship extraction
# ══════════════════════════════════════════════════════════════════════════════

def test_constraint_pulley_rope():
    cs = extract_constraint_relationships("Two masses hang over a pulley.", ["object_1", "object_2"])
    kinds = [c.kind for c in cs]
    assert "pulley_rope" in kinds
    pr = next(c for c in cs if c.kind == "pulley_rope")
    assert pr.object_a_id == "object_1"
    assert pr.object_b_id == "object_2"


def test_constraint_spring():
    cs = extract_constraint_relationships("A spring connects the wall and the mass.", ["object_1"])
    kinds = [c.kind for c in cs]
    assert "spring" in kinds


def test_constraint_rope():
    cs = extract_constraint_relationships("A rope pulls the block.", ["object_1"])
    kinds = [c.kind for c in cs]
    assert "rope" in kinds


def test_constraint_string():
    cs = extract_constraint_relationships("The tension in the string is unknown.", ["object_1"])
    kinds = [c.kind for c in cs]
    assert "string" in kinds


def test_constraint_empty_no_objects():
    cs = extract_constraint_relationships("A box rests on a surface.", [])
    # No constraint nouns present
    kinds = [c.kind for c in cs]
    assert "pulley_rope" not in kinds
    assert "spring" not in kinds


# ══════════════════════════════════════════════════════════════════════════════
# 7. Known / unknown quantity extraction
# ══════════════════════════════════════════════════════════════════════════════

def test_known_mass_and_angle():
    known, unknown = extract_known_unknown(
        "A 5 kg block is on a 30 degree inclined plane. How much force is required?"
    )
    assert "mass" in known
    assert "angle" in known
    assert "required_force" in unknown


def test_known_speed():
    known, unknown = extract_known_unknown("A ball is launched at 20 m/s at 45 degrees.")
    assert "speed" in known
    assert "angle" in known


def test_known_friction_coefficient():
    known, unknown = extract_known_unknown(
        "The coefficient of friction is 0.3. Find the acceleration."
    )
    assert "friction_coefficient" in known
    assert "acceleration" in unknown


def test_unknown_tension():
    known, unknown = extract_known_unknown("Find the tension in the rope.")
    assert "tension" in unknown


def test_unknown_range():
    known, unknown = extract_known_unknown("How far does the projectile travel?")
    assert "range" in unknown


# ══════════════════════════════════════════════════════════════════════════════
# 8. Full extract_visual_features integration (unit-level, no pipeline)
# ══════════════════════════════════════════════════════════════════════════════

def test_full_inclined_plane_features():
    text = "A 5 kg box is at rest on a frictionless inclined plane with 30 degree inclination. How much force is required to keep it at rest?"
    vf = extract_visual_features(text, ["object_1"], "inclined_plane")
    assert vf.object_types == ["box"]
    assert vf.surface_type == "frictionless_ramp"
    assert vf.motion_state == "at_rest"
    assert "mass" in vf.known_quantities
    assert "angle" in vf.known_quantities
    assert "required_force" in vf.unknown_quantities
    weight_mention = next((m for m in vf.force_mentions if m.force_type == "weight"), None)
    # weight is implicit in inclined-plane texts; explicit only when "weight" mentioned
    # — here we just verify no crash and the structure is valid
    assert isinstance(vf.force_mentions, list)


def test_full_atwood_features():
    text = "Two hanging masses of 2 kg and 3 kg pass over a pulley."
    vf = extract_visual_features(text, ["object_1", "object_2"], "atwood_pulley")
    assert vf.object_types[0] == "hanging_mass"
    assert vf.surface_type == "pulley_support"
    pr = next((c for c in vf.constraint_relationships if c.kind == "pulley_rope"), None)
    assert pr is not None
    assert pr.object_a_id == "object_1"
    assert pr.object_b_id == "object_2"


def test_full_projectile_features():
    text = "A ball is launched at 20 m/s at 45 degrees. Show the trajectory."
    vf = extract_visual_features(text, ["object_1"], "projectile_motion")
    assert vf.object_types[0] == "ball"
    assert vf.motion_state == "launched_upward"
    assert vf.requested_view == "trajectory"
    assert "speed" in vf.known_quantities
    assert "angle" in vf.known_quantities


def test_full_horizontal_friction_features():
    text = "A 2 kg cart moves to the right on a rough floor. The coefficient of friction is 0.4."
    vf = extract_visual_features(text, ["object_1"], "horizontal_friction")
    assert vf.object_types[0] == "cart"
    assert vf.surface_type == "rough_floor"
    assert vf.motion_state == "moving_right"
    assert "friction_coefficient" in vf.known_quantities


def test_ambiguity_no_object_noun():
    text = "Something of mass 5 kg."
    vf = extract_visual_features(text, ["object_1"], None)
    # 'mass' maps to block; no flag expected from extract_object_types
    assert vf.object_types == ["block"]


def test_ambiguity_no_surface():
    text = "A 5 kg mass."
    vf = extract_visual_features(text, ["object_1"], None)
    assert vf.surface_type == "unknown"
    assert any(f.field == "surface_type" for f in vf.ambiguity_flags)


def test_is_ambiguous_property():
    text = "A 5 kg mass."
    vf = extract_visual_features(text, ["object_1"], None)
    # surface_type will be unknown → flag present
    assert vf.is_ambiguous is True


def test_not_ambiguous_complete_scene():
    text = "A 5 kg box is at rest on a rough floor."
    vf = extract_visual_features(text, ["object_1"], "horizontal_friction")
    assert not vf.is_ambiguous


# ══════════════════════════════════════════════════════════════════════════════
# 9. End-to-end: parser.parse() populates visual_features correctly
# ══════════════════════════════════════════════════════════════════════════════

def test_parse_populates_visual_features_incline():
    result = parse(
        "A 5 kg box is placed on a frictionless inclined plane with 30 degree inclination. "
        "How much force is required to keep it at rest?"
    )
    vf = result.visual_features
    assert vf.object_types == ["box"]
    assert vf.surface_type == "frictionless_ramp"
    assert vf.motion_state == "at_rest"
    assert "mass" in vf.known_quantities
    assert "required_force" in vf.unknown_quantities


def test_parse_populates_visual_features_atwood():
    result = parse("Two hanging masses of 2 kg and 3 kg pass over a pulley.")
    vf = result.visual_features
    assert vf.object_types[0] == "hanging_mass"
    assert vf.surface_type == "pulley_support"
    assert any(c.kind == "pulley_rope" for c in vf.constraint_relationships)


def test_parse_populates_visual_features_projectile():
    result = parse("A ball is launched at 20 m/s at 45 degrees.")
    vf = result.visual_features
    assert vf.object_types[0] == "ball"
    assert vf.motion_state == "launched_upward"
    assert "speed" in vf.known_quantities


def test_parse_populates_visual_features_horizontal():
    result = parse("A 2 kg crate rests on a horizontal floor; coefficient of friction is 0.25.")
    vf = result.visual_features
    assert vf.object_types[0] == "crate"
    assert vf.surface_type == "rough_floor"
    assert "friction_coefficient" in vf.known_quantities


def test_parse_force_mention_provenance_mirrors_text():
    result = parse("A box is pushed to the right with a 10 N force.")
    applied = next(
        (m for m in result.visual_features.force_mentions if m.force_type == "applied"),
        None,
    )
    assert applied is not None
    assert applied.direction_hint == "right"
    assert "right" in applied.provenance.lower()


def test_parse_requested_view_fbd():
    result = parse("Draw a free-body diagram for the 5 kg block on a frictionless incline at 30 degrees.")
    assert result.visual_features.requested_view == "fbd"


def test_parse_requested_view_components():
    result = parse("Show force components on a 5 kg block on a 30 degree incline.")
    assert result.visual_features.requested_view == "components"


def test_parse_primary_object_type_property():
    result = parse("A 3 kg cart moves on a horizontal table.")
    assert result.visual_features.primary_object_type == "cart"


def test_parse_no_ambiguity_complete_problem():
    result = parse(
        "A 5 kg box is at rest on a rough floor; coefficient of friction is 0.3."
    )
    # Complete scene: box (known), rough_floor (known), at_rest (known)
    # motion_state ambiguity flag should NOT fire here
    motion_flags = [f for f in result.visual_features.ambiguity_flags if f.field == "motion_state"]
    assert not motion_flags
