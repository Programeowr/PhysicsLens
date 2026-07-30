"""Scene graph layout for the supported PhysicsLens scenarios."""

from __future__ import annotations

from math import cos, pi, sin

from .schema import SceneGraph


def _force_scale(scene: SceneGraph) -> float:
    return 140.0 / max((force.magnitude_n for force in scene.forces), default=1.0)


def _position_force(anchor: tuple[float, float], direction_deg: float, magnitude_n: float, scale: float) -> tuple[float, float, float, float, float, float]:
    radians = direction_deg * pi / 180
    length = max(36.0, magnitude_n * scale)
    x1, y1 = anchor
    x2, y2 = x1 + length * cos(radians), y1 - length * sin(radians)
    return x1, y1, x2, y2, x2, y2 - 8


def layout_scene(scene: SceneGraph) -> SceneGraph:
    scale = _force_scale(scene)

    if scene.scenario_type == "inclined_plane":
        angle = scene.source_result.geometry.incline_angle_deg or 0.0 if scene.source_result else 0.0
        radians = angle * pi / 180
        start, length = (120.0, 500.0), 570.0
        end = (start[0] + length * cos(radians), start[1] - length * sin(radians))
        cx = start[0] + 300 * cos(radians) - 22 * sin(radians)
        cy = start[1] - 300 * sin(radians) - 22 * cos(radians)
        if scene.objects:
            obj = scene.objects[0]
            obj.x, obj.y = cx, cy
            obj.width, obj.height = 88.0, 56.0
            obj.rotation_deg = -angle
        if scene.surfaces:
            scene.surfaces[0].x1, scene.surfaces[0].y1 = start
            scene.surfaces[0].x2, scene.surfaces[0].y2 = end
        for force in scene.forces:
            force.x1, force.y1, force.x2, force.y2, force.label_x, force.label_y = _position_force((cx, cy), force.direction_deg, force.magnitude_n, scale)
    elif scene.scenario_type == "horizontal_friction":
        anchor = (450.0, 365.0)
        if scene.objects:
            obj = scene.objects[0]
            obj.x, obj.y = anchor
            obj.width, obj.height = 90.0, 60.0
        if scene.surfaces:
            scene.surfaces[0].x1, scene.surfaces[0].y1 = 100.0, 420.0
            scene.surfaces[0].x2, scene.surfaces[0].y2 = 800.0, 420.0
        for force in scene.forces:
            force.x1, force.y1, force.x2, force.y2, force.label_x, force.label_y = _position_force(anchor, force.direction_deg, force.magnitude_n, scale)
    elif scene.scenario_type == "atwood_pulley":
        anchors = {scene.objects[0].id: (350.0, 410.0), scene.objects[1].id: (550.0, 410.0)} if len(scene.objects) >= 2 else {}
        for obj in scene.objects[:2]:
            x, y = anchors[obj.id]
            obj.x, obj.y = x, y
            obj.width, obj.height = 76.0, 56.0
        for force in scene.forces:
            anchor = anchors.get(force.anchor_id, (450.0, 410.0))
            force.x1, force.y1, force.x2, force.y2, force.label_x, force.label_y = _position_force(anchor, force.direction_deg, force.magnitude_n, scale)
    elif scene.scenario_type == "projectile_motion":
        anchor = (350.0, 370.0)
        if scene.objects:
            obj = scene.objects[0]
            obj.x, obj.y = anchor
            obj.width, obj.height = 22.0, 22.0
        for force in scene.forces:
            force.x1, force.y1, force.x2, force.y2, force.label_x, force.label_y = _position_force(anchor, force.direction_deg, force.magnitude_n, scale)
    else:
        anchor = (450.0, 330.0)
        if scene.objects:
            obj = scene.objects[0]
            obj.x, obj.y = anchor
            obj.width, obj.height = 90.0, 60.0
        for force in scene.forces:
            force.x1, force.y1, force.x2, force.y2, force.label_x, force.label_y = _position_force(anchor, force.direction_deg, force.magnitude_n, scale)

    return scene
