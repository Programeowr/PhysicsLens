"""Build an abstract scene graph from parsed physics facts and solved values."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .schema import (
    DiagramIntent,
    ForceSolution,
    ParseResult,
    RenderHints,
    SceneAnnotation,
    SceneCanvas,
    SceneForce,
    SceneGraph,
    SceneObject,
    SceneSurface,
)


def _default_intent(result: ParseResult) -> DiagramIntent:
    title = {
        "inclined_plane": "Inclined Plane Free-Body Diagram",
        "horizontal_friction": "Horizontal Free-Body Diagram",
        "atwood_pulley": "Atwood Pulley Free-Body Diagram",
        "projectile_motion": "Projectile Motion Force Diagram",
    }.get(result.scenario_type or "", "Generic Free-Body Diagram")
    return DiagramIntent(title=title)


def _default_hints(result: ParseResult) -> RenderHints:
    return RenderHints(scene_style=result.scenario_type or "generic", object_shape=result.objects[0].shape if result.objects else "box")


def _object_label(result: ParseResult, index: int) -> str:
    if index < len(result.objects) and result.objects[index].label:
        return result.objects[index].label or ""
    if index < len(result.objects) and result.objects[index].mass_kg is not None:
        return f"{result.objects[index].mass_kg:g} kg"
    return "object"


def _scene_object(result: ParseResult, index: int) -> SceneObject:
    spec = result.objects[index]
    return SceneObject(id=spec.id, label=_object_label(result, index), shape=spec.shape, mass_kg=spec.mass_kg)


def _scene_forces(solution: ForceSolution) -> list[SceneForce]:
    return [SceneForce(name=force.name, magnitude_n=force.magnitude_n, direction_deg=force.direction_deg, anchor_id=force.anchor) for force in solution.forces]


def build_scene_graph(result: ParseResult, solution: ForceSolution | None, render_options: dict[str, Any] | None = None) -> SceneGraph:
    intent = _default_intent(result)
    hints = _default_hints(result)
    if render_options:
        intent = replace(
            intent,
            title=str(render_options.get("title", intent.title)),
            view_mode=str(render_options.get("view_mode", intent.view_mode)),
            emphasize_components=bool(render_options.get("emphasize_components", intent.emphasize_components)),
            show_annotations=bool(render_options.get("show_annotations", intent.show_annotations)),
        )
        hints = replace(
            hints,
            scene_style=str(render_options.get("scene_style", hints.scene_style)),
            object_shape=str(render_options.get("object_shape", hints.object_shape)),
            show_surface=bool(render_options.get("show_surface", hints.show_surface)),
            show_title=bool(render_options.get("show_title", hints.show_title)),
        )

    objects = [_scene_object(result, index) for index in range(len(result.objects))]
    surfaces: list[SceneSurface] = []
    annotations: list[SceneAnnotation] = []
    if result.scenario_type == "inclined_plane":
        surfaces.append(SceneSurface("inclined_plane", angle_deg=float(result.geometry.incline_angle_deg or 0.0)))
    elif result.scenario_type == "horizontal_friction":
        surfaces.append(SceneSurface("horizontal_surface"))
    elif result.scenario_type == "atwood_pulley":
        surfaces.append(SceneSurface("pulley_support"))
    elif result.scenario_type == "projectile_motion":
        surfaces.append(SceneSurface("ground"))

    if result.scenario_type == "projectile_motion" and result.geometry.projectile_angle_deg is not None:
        annotations.append(SceneAnnotation(text=f"Launch angle: {result.geometry.projectile_angle_deg:g}°", x=120.0, y=70.0, align="start"))
    if result.scenario_type in {"inclined_plane", "horizontal_friction"} and result.objects and result.objects[0].mass_kg is not None:
        annotations.append(SceneAnnotation(text=f"Mass: {result.objects[0].mass_kg:g} kg", x=120.0, y=100.0, align="start"))

    return SceneGraph(
        canvas=SceneCanvas(),
        title=intent.title,
        scenario_type=result.scenario_type,
        intent=intent,
        hints=hints,
        objects=objects,
        surfaces=surfaces,
        forces=_scene_forces(solution) if solution else [],
        annotations=annotations,
        source_result=result,
        source_solution=solution,
    )
