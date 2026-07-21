"""Keyword based, deterministic scenario classification."""

from __future__ import annotations

SCENARIO_TRIGGERS: dict[str, list[str]] = {
    "inclined_plane": ["incline", "inclined plane", "ramp", "slope", "inclination", "slanted plane"],
    "atwood_pulley": ["pulley", "atwood", "hanging mass", "hanging masses", "two masses"],
    "horizontal_friction": ["horizontal surface", "flat surface", "floor", "table", "horizontal plane"],
    "projectile_motion": ["thrown", "launched", "projectile", "trajectory", "fired", "at an angle"],
    "circular_motion": ["circular", "orbit", "loop", "centripetal", "revolves"],
    "spring_mass": ["spring", "spring constant", "hooke's law"],
}

REQUIRED_SLOTS: dict[str, list[str]] = {
    "inclined_plane": ["mass_kg", "incline_angle_deg"],
    "horizontal_friction": ["mass_kg"],
    "atwood_pulley": ["mass_kg_list_min2"],
    "projectile_motion": ["initial_speed_ms", "projectile_angle_deg"],
    "circular_motion": ["mass_kg"],
    "spring_mass": ["mass_kg"],
}


def classify_scenario(text: str) -> tuple[str | None, float]:
    """Return the highest keyword-hit scenario and a reproducible confidence."""
    lowered = text.lower()
    scored = {
        scenario: sum(1 for trigger in triggers if trigger in lowered)
        for scenario, triggers in SCENARIO_TRIGGERS.items()
    }
    best, hits = max(scored.items(), key=lambda item: item[1])
    if hits == 0:
        return None, 0.0
    # Saturates at one while remaining easy to reason about in tests.
    return best, min(1.0, hits / max(1, len(SCENARIO_TRIGGERS[best]) / 2))
