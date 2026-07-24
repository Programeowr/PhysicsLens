"""Build an abstract scene graph from parsed physics and solved forces."""

from __future__ import annotations

from math import cos, pi, sin
from typing import Iterable

from .schema import (
    ForceSolution,
    ParseResult,
    SceneAnnotation,
    SceneCanvas,
    SceneForce,
    SceneGraph,
    SceneObject,
    SceneSurface,
)

FORCE_LABELS = {
    "weight": "W",
    "normal_force": "N",
    "friction": "f",
    "tension": "T",
    "applied_force": "F",
}

FORCE_COLORS = {
    "weight": "#d62728",
    "normal_force": "#1f77b4",
    "friction": "#2ca02c",
    "tension": "#ff7f0e",
    "applied_force": "#9467bd",
}

SCENARIO_TITLES = {
    "inclined_plane": "Inclined Plane Free-Body Diagram",
    "horizontal_friction": "Horizontal Free-Body Diagram",
    "atwood_pulley": "Atwood Pulley Free-Body Diagram",
    "projectile_motion": "Projectile Motion Force Diagram",
}


def build_scene_graph(
    result: ParseResult,
    solution: ForceSolution | None,
    width: int = 900,
    height: int = 620,
) -> SceneGraph:
    canvas = SceneCanvas(width=width, height=height, margin=56)
    title = SCENARIO_TITLES.get(result.scenario_type or "", "PhysicsLens Diagram")
    scene = SceneGraph(canvas=canvas, title=title)

    scene.objects = [
        SceneObject(
            id=obj.id,
            type="block",
            label=obj.label or f"Object {i + 1}",
            mass_kg=obj.mass_kg,
        )
        for i, obj in enumerate(result.objects)
    ]

    if result.scenario_type == "inclined_plane":
        _build_incline(scene, result)
    elif result.scenario_type == "horizontal_friction":
        _build_horizontal(scene, result)
    elif result.scenario_type == "atwood_pulley":
        _build_atwood(scene, result)
    elif result.scenario_type == "projectile_motion":
        _build_projectile(scene, result, solution)
    else:
        _build_generic(scene, result)

    if solution is not None:
        scene.forces = [
            SceneForce(
                label=FORCE_LABELS.get(force.name, force.name.replace("_", " ").title()),
                origin=force.anchor,
                magnitude_n=force.magnitude_n,
                direction_deg=force.direction_deg,
                color=FORCE_COLORS.get(force.name, "#333333"),
            )
            for force in solution.forces
        ]

    return scene


def _build_incline(scene: SceneGraph, result: ParseResult) -> None:
    angle = result.geometry.incline_angle_deg or 0.0
    scene.surfaces.append(SceneSurface(type="incline", angle=angle))
    if scene.objects:
        scene.annotations.append(
            SceneAnnotation(type="angle", value=angle, origin=scene.objects[0].id)
        )


def _build_horizontal(scene: SceneGraph, result: ParseResult) -> None:
    scene.surfaces.append(SceneSurface(type="ground"))


def _build_atwood(scene: SceneGraph, result: ParseResult) -> None:
    scene.surfaces.append(SceneSurface(type="pulley"))


def _build_projectile(
    scene: SceneGraph,
    result: ParseResult,
    solution: ForceSolution | None,
) -> None:
    range_m = float(solution.derived_values.get("range_m") or 1.0) if solution else 1.0
    height_m = float(solution.derived_values.get("max_height_m") or 1.0) if solution else 1.0
    angle = result.geometry.projectile_angle_deg or 45.0
    points: list[tuple[float, float]] = []
    if range_m > 0 and height_m >= 0:
        for index in range(61):
            x = range_m * index / 60
            y = x * sin(angle * pi / 180) - 9.8 * x * x / (2 * (result.geometry.initial_speed_ms or 1.0) ** 2 * cos(angle * pi / 180) ** 2)
            points.append((x, max(0.0, y)))
    scene.surfaces.append(SceneSurface(type="trajectory", points=points))
    scene.surfaces.append(SceneSurface(type="ground"))


def _build_generic(scene: SceneGraph, result: ParseResult) -> None:
    scene.surfaces.append(SceneSurface(type="ground"))


def scene_object_by_id(scene: SceneGraph, object_id: str) -> SceneObject | None:
    for obj in scene.objects:
        if obj.id == object_id:
            return obj
    return None


def has_scene_object(scene: SceneGraph) -> bool:
    return bool(scene.objects)
