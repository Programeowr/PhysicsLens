"""Deterministic Newtonian solvers. All numerical results originate here."""

from __future__ import annotations

from math import cos, degrees, pi, sin

from .schema import ForceSolution, ForceVector, ParseResult

G = 9.8


def _mass(result: ParseResult, index: int = 0) -> float:
    mass = result.objects[index].mass_kg
    if mass is None:
        raise ValueError("A mass is required to solve this scenario")
    return mass


def _angle(result: ParseResult, attr: str) -> float:
    value = getattr(result.geometry, attr)
    if value is None:
        raise ValueError(f"{attr} is required to solve this scenario")
    return value


def solve_inclined_plane(result: ParseResult) -> ForceSolution:
    mass, angle = _mass(result), _angle(result, "incline_angle_deg")
    radians = angle * pi / 180
    normal = mass * G * cos(radians)
    along = mass * G * sin(radians)
    forces = [
        ForceVector("weight", mass * G, 270.0, result.objects[0].id),
        ForceVector("normal_force", normal, 90 + angle, result.objects[0].id),
    ]
    friction: float | None = None
    if result.friction == "frictionless":
        friction = 0.0
    elif result.mu is not None:
        friction = result.mu * normal
        if friction:
            forces.append(ForceVector("friction", friction, angle, result.objects[0].id))
    required = along - friction if friction is not None else None
    if required is not None and required > 0:
        forces.append(ForceVector("applied_force", required, angle, result.objects[0].id))
    elif required is not None and required < 0:
        forces.append(ForceVector("applied_force", abs(required), (angle + 180) % 360, result.objects[0].id))
    forces.extend(_applied_vectors(result, angle))
    return ForceSolution("inclined_plane", forces, {
        "normal_force_n": normal, "gravity_along_incline_n": along,
        "friction_force_n": friction, "required_force_to_hold_at_rest_n": required,
    })


def solve_horizontal_friction(result: ParseResult) -> ForceSolution:
    mass = _mass(result)
    normal = mass * G
    friction = result.mu * normal if result.mu is not None else (0.0 if result.friction == "frictionless" else None)
    forces = [
        ForceVector("weight", mass * G, 270.0, result.objects[0].id),
        ForceVector("normal_force", normal, 90.0, result.objects[0].id),
    ]
    if friction:
        forces.append(ForceVector("friction", friction, 180.0, result.objects[0].id))
    forces.extend(_applied_vectors(result, 0.0))
    return ForceSolution("horizontal_friction", forces, {"normal_force_n": normal, "friction_force_n": friction})


def solve_atwood_pulley(result: ParseResult) -> ForceSolution:
    """Solve the two Newton equations symbolically for a massless pulley."""
    if len(result.objects) < 2:
        raise ValueError("Atwood pulley needs two masses")
    m1, m2 = _mass(result, 0), _mass(result, 1)
    try:
        from sympy import Eq, solve, symbols
        acceleration, tension = symbols("a T")
        values = solve((Eq(tension - m1 * G, m1 * acceleration), Eq(m2 * G - tension, m2 * acceleration)), (acceleration, tension), dict=True)[0]
        a, t = float(values[acceleration]), float(values[tension])
    except ImportError as exc:  # requirements makes this unavailable only before installation
        raise RuntimeError("SymPy is required for the Atwood solver") from exc
    # Positive a means m2 moves down; directions are screen coordinates.
    return ForceSolution("atwood_pulley", [
        ForceVector("weight", m1 * G, 270.0, result.objects[0].id),
        ForceVector("tension", t, 90.0, result.objects[0].id),
        ForceVector("weight", m2 * G, 270.0, result.objects[1].id),
        ForceVector("tension", t, 90.0, result.objects[1].id),
    ], {"acceleration_ms2": a, "tension_n": t})


def solve_projectile_motion(result: ParseResult) -> ForceSolution:
    speed, angle = _angle(result, "initial_speed_ms"), _angle(result, "projectile_angle_deg")
    mass = result.objects[0].mass_kg if result.objects and result.objects[0].mass_kg is not None else 1.0
    radians = angle * pi / 180
    return ForceSolution("projectile_motion", [ForceVector("weight", mass * G, 270.0, result.objects[0].id if result.objects else "projectile")], {
        "range_m": speed**2 * sin(2 * radians) / G,
        "max_height_m": (speed * sin(radians))**2 / (2 * G),
        "time_of_flight_s": 2 * speed * sin(radians) / G,
    })


def _applied_vectors(result: ParseResult, default_angle: float) -> list[ForceVector]:
    mapping = {"right": 0.0, "left": 180.0, "uphill": default_angle}
    return [ForceVector("applied_force", force.magnitude_n, mapping.get(force.direction, default_angle), result.objects[0].id) for force in result.applied_forces]


SOLVERS = {
    "inclined_plane": solve_inclined_plane,
    "horizontal_friction": solve_horizontal_friction,
    "atwood_pulley": solve_atwood_pulley,
    "projectile_motion": solve_projectile_motion,
}


def solve(result: ParseResult) -> ForceSolution:
    if result.scenario_type not in SOLVERS:
        raise ValueError(f"Unsupported scenario: {result.scenario_type}")
    return SOLVERS[result.scenario_type](result)
