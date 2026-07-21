import pytest

from physics_diagram.parser import parse
from physics_diagram.physics_engine import solve


def test_inclined_plane_required_force():
    solution = solve(parse("A 5 kg box is on a frictionless 30 degree inclined plane. How much force keeps it at rest?"))
    assert solution.derived_values["required_force_to_hold_at_rest_n"] == pytest.approx(24.5)


def test_inclined_plane_with_friction():
    solution = solve(parse("A 10 kg crate is on a 30 degree ramp, coefficient of friction is 0.2."))
    assert solution.derived_values["normal_force_n"] == pytest.approx(98 * .8660254)
    assert solution.derived_values["friction_force_n"] == pytest.approx(98 * .8660254 * .2)


def test_horizontal_friction():
    solution = solve(parse("A 10 kg box is on a horizontal table with coefficient of friction 0.3."))
    assert solution.derived_values["friction_force_n"] == pytest.approx(29.4)


def test_horizontal_frictionless():
    solution = solve(parse("A 2 kg cart is on a frictionless flat surface."))
    assert solution.derived_values["normal_force_n"] == pytest.approx(19.6)
    assert solution.derived_values["friction_force_n"] == 0


def test_atwood_values():
    solution = solve(parse("Two hanging masses of 2 kg and 3 kg are connected by a pulley."))
    assert solution.derived_values["acceleration_ms2"] == pytest.approx(1.96)
    assert solution.derived_values["tension_n"] == pytest.approx(23.52)


def test_atwood_equal_masses():
    solution = solve(parse("An Atwood pulley holds a 4 kg mass and a 4 kg mass."))
    assert solution.derived_values["acceleration_ms2"] == pytest.approx(0)
    assert solution.derived_values["tension_n"] == pytest.approx(39.2)


def test_projectile_values():
    solution = solve(parse("A 1 kg ball is launched at 20 m/s at 45 degrees."))
    assert solution.derived_values["range_m"] == pytest.approx(400 / 9.8)
    assert solution.derived_values["max_height_m"] == pytest.approx(100 / 9.8)


def test_projectile_time():
    solution = solve(parse("A ball is fired at 19.6 m/s at 30 degrees."))
    assert solution.derived_values["time_of_flight_s"] == pytest.approx(2)
