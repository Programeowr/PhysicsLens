import pytest

from physics_diagram.parser import parse


@pytest.mark.parametrize(("text", "scenario"), [
    ("A 5 kg box sits on a 30 degree incline.", "inclined_plane"),
    ("A block of mass 5kg is on a ramp with thirty degrees inclination.", "inclined_plane"),
    ("A 2 kg cart moves on a horizontal table.", "horizontal_friction"),
    ("A 2000 g box is on a flat surface.", "horizontal_friction"),
    ("Two hanging masses of 2 kg and 3 kg pass over a pulley.", "atwood_pulley"),
    ("An Atwood machine has a 1kg block and a 4kg weight.", "atwood_pulley"),
    ("A ball is launched at 20 m/s at 45 degrees.", "projectile_motion"),
    ("A projectile is fired with speed 72 km/h at thirty degrees.", "projectile_motion"),
])
def test_parser_scenario_paraphrases(text, scenario):
    assert parse(text).scenario_type == scenario


def test_incline_slots_and_friction():
    result = parse("A box of mass 5kg is on a frictionless inclined plane with 30 degree inclination.")
    assert result.objects[0].mass_kg == 5
    assert result.geometry.incline_angle_deg == 30
    assert (result.friction, result.mu) == ("frictionless", 0.0)
    assert not result.missing_required


def test_mu_and_unit_conversion():
    result = parse("A 2000 g crate rests on a horizontal floor; coefficient of friction is 0.25.")
    assert result.objects[0].mass_kg == 2
    assert result.mu == .25
