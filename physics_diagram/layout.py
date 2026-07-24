"""Compute layout positions for a scene graph before SVG rendering."""

from __future__ import annotations

from math import cos, pi, sin

from .schema import SceneAnnotation, SceneCanvas, SceneForce, SceneGraph, SceneObject, SceneSurface
from .scene_graph import scene_object_by_id

MIN_FORCE_LENGTH = 48.0
MAX_FORCE_LENGTH = 180.0
FORCE_LENGTH_SCALE = 5.0
LABEL_PADDING = 12.0


def layout_scene(scene: SceneGraph) -> SceneGraph:
    _layout_canvas(scene.canvas)
    _layout_surfaces(scene)
    _layout_objects(scene)
    _layout_forces(scene)
    _layout_annotations(scene)
    return scene


def _layout_canvas(canvas: SceneCanvas) -> None:
    # The canvas dimensions are fixed by the loader; margin reserves breathing room.
    canvas.width = max(canvas.width, 400)
    canvas.height = max(canvas.height, 300)


def _layout_surfaces(scene: SceneGraph) -> None:
    width, height, m = scene.canvas.width, scene.canvas.height, scene.canvas.margin
    for surface in scene.surfaces:
        if surface.type == "incline":
            angle = surface.angle or 0.0
            theta = angle * pi / 180
            length = width - m * 2
            start = (m, height - m)
            end = (m + length * cos(theta), height - m - length * sin(theta))
            surface.start = start
            surface.end = end
        elif surface.type == "ground":
            surface.start = (m, height - m)
            surface.end = (width - m, height - m)
        elif surface.type == "pulley":
            surface.center = (width / 2, m + 80)
            surface.radius = 50.0
        elif surface.type == "trajectory" and surface.points:
            surface.start = (m, height - m)
            surface.end = (width - m, height - m)


def _layout_objects(scene: SceneGraph) -> None:
    width, height, m = scene.canvas.width, scene.canvas.height, scene.canvas.margin
    for obj in scene.objects:
        if scene.surfaces and scene.surfaces[0].type == "incline":
            incline = scene.surfaces[0]
            if incline.start and incline.end:
                obj.rotation_deg = incline.angle or 0.0
                center_x = (incline.start[0] + incline.end[0]) / 2
                center_y = (incline.start[1] + incline.end[1]) / 2
                offset_x = -obj.height * sin((incline.angle or 0.0) * pi / 180) / 2
                offset_y = obj.height * cos((incline.angle or 0.0) * pi / 180) / 2
                obj.position = (center_x + offset_x, center_y + offset_y)
        elif scene.surfaces and scene.surfaces[0].type == "pulley":
            if len(scene.objects) >= 2 and scene.surfaces[0].center:
                cx, cy = scene.surfaces[0].center
                spacing = 180.0
                scene.objects[0].position = (cx - spacing, cy + 210)
                scene.objects[1].position = (cx + spacing, cy + 210)
        elif scene.surfaces and scene.surfaces[0].type == "trajectory":
            obj.position = (scene.canvas.width / 2, scene.canvas.height - m - 16)
        else:
            obj.position = (scene.canvas.width / 2, scene.canvas.height / 2)


def _layout_forces(scene: SceneGraph) -> None:
    for force in scene.forces:
        origin_obj = scene_object_by_id(scene, force.origin)
        if origin_obj is None:
            continue
        anchor_x, anchor_y = origin_obj.position
        force.anchor_position = (anchor_x, anchor_y)
        length = min(MAX_FORCE_LENGTH, max(MIN_FORCE_LENGTH, force.magnitude_n * FORCE_LENGTH_SCALE))
        radians = force.direction_deg * pi / 180
        tip_x = anchor_x + length * cos(radians)
        tip_y = anchor_y - length * sin(radians)
        force.tip_position = (tip_x, tip_y)
        force.label_position = (tip_x, tip_y - LABEL_PADDING)


def _layout_annotations(scene: SceneGraph) -> None:
    for annotation in scene.annotations:
        if annotation.type == "angle":
            origin_obj = scene_object_by_id(scene, annotation.origin or "")
            if origin_obj and scene.surfaces and scene.surfaces[0].start and scene.surfaces[0].end:
                x1, y1 = scene.surfaces[0].start
                x2, y2 = scene.surfaces[0].end
                annotation.position = ((x1 + x2) / 2, (y1 + y2) / 2 + 24)
                annotation.radius = 40.0
                annotation.label_position = (annotation.position[0] + 24, annotation.position[1] - 24)
