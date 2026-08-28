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

# ──────────────────────────────────────────────────────────────────────────────
# Visual-features → RenderHints mapping helpers
# ──────────────────────────────────────────────────────────────────────────────

_OBJECT_TYPE_TO_SHAPE: dict[str, str] = {
    "box": "box",
    "crate": "box",
    "block": "box",
    "cart": "cart",
    "ball": "sphere",
    "sphere": "sphere",
    "projectile": "projectile",
    "particle": "sphere",
    "hanging_mass": "hanging_mass",
    "pulley_mass": "hanging_mass",
    "spring_endpoint": "box",
    "unknown": "box",
}

_SURFACE_TO_TEXTURE: dict[str, str] = {
    "rough_floor": "rough",
    "smooth_floor": "smooth",
    "frictionless_ramp": "frictionless",
    "inclined_plane": "smooth",
    "ground": "smooth",
    "pulley_support": "none",
    "spring_anchor": "none",
    "table": "smooth",
    "air": "none",
    "unknown": "none",
}

_VIEW_TO_MODE: dict[str, str] = {
    "fbd": "fbd",
    "scene_and_fbd": "scene_and_fbd",
    "components": "components",
    "trajectory": "trajectory",
    "velocity_diagram": "fbd",
    "acceleration_diagram": "fbd",
    "symbolic": "fbd",
    "numeric": "fbd",
    "unknown": "fbd",
}


def _intent_from_visual(result: ParseResult) -> DiagramIntent:
    """Derive DiagramIntent from visual_features, falling back to scenario defaults."""
    vf = result.visual_features

    # Title: prefer scenario-specific label
    title = {
        "inclined_plane": "Inclined Plane Free-Body Diagram",
        "horizontal_friction": "Horizontal Free-Body Diagram",
        "atwood_pulley": "Atwood Pulley Free-Body Diagram",
        "projectile_motion": "Projectile Motion Force Diagram",
    }.get(result.scenario_type or "", "Generic Free-Body Diagram")

    view_mode = _VIEW_TO_MODE.get(vf.requested_view, "fbd")
    emphasize_components = vf.requested_view in {"components", "symbolic"}

    return DiagramIntent(
        title=title,
        view_mode=view_mode,
        emphasize_components=emphasize_components,
        show_annotations=True,
    )


def _hints_from_visual(result: ParseResult) -> RenderHints:
    """Derive RenderHints from visual_features for richer shape/texture/vector output."""
    vf = result.visual_features

    # Object shape: use the first extracted object type, fall back to ObjectSpec.shape
    primary_type = vf.primary_object_type
    if primary_type != "unknown":
        shape = _OBJECT_TYPE_TO_SHAPE.get(primary_type, "box")
    elif result.objects:
        shape = result.objects[0].shape
    else:
        shape = "box"

    surface_texture = _SURFACE_TO_TEXTURE.get(vf.surface_type, "none")

    show_velocity = vf.requested_view == "velocity_diagram" or vf.motion_state not in {
        "at_rest", "equilibrium", "unknown"
    }
    show_acceleration = (
        vf.requested_view == "acceleration_diagram"
        or vf.motion_state in {"accelerating", "decelerating"}
    )
    show_components = vf.requested_view in {"components", "symbolic"}

    return RenderHints(
        scene_style=result.scenario_type or "generic",
        object_shape=shape,
        show_surface=True,
        show_title=True,
        surface_texture=surface_texture,
        show_velocity_vector=show_velocity,
        show_acceleration_vector=show_acceleration,
        show_components=show_components,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Scene-object helpers
# ──────────────────────────────────────────────────────────────────────────────

def _object_label(result: ParseResult, index: int) -> str:
    if index < len(result.objects) and result.objects[index].label:
        return result.objects[index].label or ""
    if index < len(result.objects) and result.objects[index].mass_kg is not None:
        return f"{result.objects[index].mass_kg:g} kg"
    return "object"


def _scene_object(result: ParseResult, index: int) -> SceneObject:
    spec = result.objects[index]
    vf = result.visual_features
    # Per-object shape: use visual_features.object_types when available
    if index < len(vf.object_types):
        shape = _OBJECT_TYPE_TO_SHAPE.get(vf.object_types[index], spec.shape)
    else:
        shape = spec.shape
    return SceneObject(
        id=spec.id,
        label=_object_label(result, index),
        shape=shape,
        mass_kg=spec.mass_kg,
    )


def _scene_forces(solution: ForceSolution) -> list[SceneForce]:
    return [
        SceneForce(
            name=force.name,
            magnitude_n=force.magnitude_n,
            direction_deg=force.direction_deg,
            anchor_id=force.anchor,
        )
        for force in solution.forces
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Public builder
# ──────────────────────────────────────────────────────────────────────────────

def build_scene_graph(
    result: ParseResult,
    solution: ForceSolution | None,
    render_options: dict[str, Any] | None = None,
) -> SceneGraph:
    intent = _intent_from_visual(result)
    hints = _hints_from_visual(result)

    # render_options (from the API caller) can override any intent/hints field.
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

    objects = [_scene_object(result, i) for i in range(len(result.objects))]

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
        annotations.append(SceneAnnotation(
            text=f"Launch angle: {result.geometry.projectile_angle_deg:g}°",
            x=120.0, y=70.0, align="start",
        ))
    if result.scenario_type in {"inclined_plane", "horizontal_friction"} and result.objects and result.objects[0].mass_kg is not None:
        annotations.append(SceneAnnotation(
            text=f"Mass: {result.objects[0].mass_kg:g} kg",
            x=120.0, y=100.0, align="start",
        ))

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
