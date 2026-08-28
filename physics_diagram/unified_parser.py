"""Unified parser that extracts Physics, Scene, and Render features separately.

This replaces the old ParseResult with three independent feature sets.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .classifier import REQUIRED_SLOTS, classify_scenario
from .physics_features import (
    InitialConditions,
    PhysicsConstraint,
    PhysicsFeatures,
    PhysicsFriction,
    PhysicsForce,
    PhysicsGeometry,
    PhysicsObject,
)
from .render_features import CameraView, DiagramStyle, LabelConfig, RenderFeatures
from .scene_features import (
    ContactInfo,
    SceneConstraint,
    SceneConnection,
    SceneFeatures,
    SceneObject,
    SceneRelationship,
    SceneSurface,
)
from .slots import extract_applied_forces, extract_friction, extract_geometry, extract_objects, extract_unknowns

logger = logging.getLogger(__name__)

_PARSE_FAILURE_LOG = Path("parse_failures.log")


def _log_incomplete_parse(text: str, missing: list[str]) -> None:
    """Append incomplete parse attempts to a log file for review."""
    try:
        with _PARSE_FAILURE_LOG.open("a", encoding="utf-8") as f:
            import datetime
            timestamp = datetime.datetime.now(datetime.UTC).isoformat()
            f.write(f"[{timestamp}] Missing: {', '.join(missing)}\n")
            f.write(f"Text: {text.strip()}\n\n")
    except OSError as exc:
        logger.warning("Failed to write parse failure log: %s", exc)


def _normalize_text(text: str) -> str:
    """Rewrite common phrasings to canonical forms."""
    normalized = text.lower()
    
    # Unit normalization
    normalized = re.sub(r'\bkilograms?\b', 'kg', normalized)
    normalized = re.sub(r'\bgrams?\b', 'g', normalized)
    normalized = re.sub(r'\bpounds?\b', 'lb', normalized)
    normalized = re.sub(r'\bdegrees?\b', 'degree', normalized)
    normalized = re.sub(r'\bradians?\b', 'radian', normalized)
    normalized = re.sub(r'\bnewtons?\b', 'n', normalized)
    normalized = re.sub(r'\bmeters?\s+per\s+second\b', 'm/s', normalized)
    
    # Angle/direction/force normalization
    if not any(kw in normalized for kw in ["throw", "launch", "projectile", "fired", "trajectory"]):
        normalized = re.sub(r'\bat\s+an?\s+angle\b', '', normalized)
    normalized = re.sub(r'(?:making|at|with)\s+an?\s+angle\s+of\s+', '', normalized)
    normalized = re.sub(r'inclined\s+at\s+', 'incline ', normalized)
    normalized = re.sub(r'tilted\s+(?:at\s+)?', 'incline ', normalized)
    normalized = re.sub(r'(?:has|with)\s+a\s+mass\s+of\s+', 'mass ', normalized)
    normalized = re.sub(r'weighing\s+', 'mass ', normalized)
    normalized = re.sub(r'force\s+(?:is\s+)?applied', 'applied force', normalized)
    normalized = re.sub(r'push(?:ed|ing)?\s+by', 'applied force', normalized)
    normalized = re.sub(r'pull(?:ed|ing)?\s+(?:using|with|by)', 'applied force', normalized)
    normalized = re.sub(r'\bto\s+the\s+(right|left)\b', r'\1', normalized)
    normalized = re.sub(r'\bupward\b', 'up', normalized)
    normalized = re.sub(r'\bdownward\b', 'down', normalized)
    normalized = re.sub(r'coefficient\s+of\s+(?:kinetic\s+)?friction\s+(?:is|=)\s+', 'mu=', normalized)
    normalized = re.sub(r'μ\s*=\s*', 'mu=', normalized)
    normalized = re.sub(r'\b(?:equals?|is)\b', '', normalized)
    
    return normalized


def _extract_physics_features(text: str, normalized: str) -> PhysicsFeatures:
    """Extract Category 1: Physics Features."""
    scenario, confidence = classify_scenario(normalized)
    
    # Extract objects
    object_specs = extract_objects(normalized)
    physics_objects = [
        PhysicsObject(id=obj.id, name=obj.label or "object", mass_kg=obj.mass_kg, label=obj.label)
        for obj in object_specs
    ]
    
    # Extract geometry
    geometry_data = extract_geometry(normalized)
    physics_geometry = PhysicsGeometry(
        incline_angle_deg=geometry_data.incline_angle_deg,
        projectile_angle_deg=geometry_data.projectile_angle_deg,
        initial_speed_ms=geometry_data.initial_speed_ms,
    )
    
    # Resolve ambiguous angles
    if scenario == "inclined_plane" and physics_geometry.incline_angle_deg is None and physics_geometry.projectile_angle_deg is not None:
        physics_geometry.incline_angle_deg = physics_geometry.projectile_angle_deg
    if scenario == "projectile_motion" and physics_geometry.projectile_angle_deg is None and physics_geometry.incline_angle_deg is not None:
        physics_geometry.projectile_angle_deg = physics_geometry.incline_angle_deg
    
    # Extract friction
    friction_type, mu = extract_friction(normalized)
    physics_friction = PhysicsFriction(type=friction_type, coefficient=mu)
    
    # Extract applied forces
    applied_forces_data = extract_applied_forces(normalized)
    physics_forces = [
        PhysicsForce(
            id=f"applied_force_{i}",
            type="applied",
            magnitude_n=f.magnitude_n,
            direction=f.direction,
            angle_deg=f.angle_deg,
            reference_frame=f.reference_frame,
            target_object=physics_objects[0].id if physics_objects else "object_1",
            is_known=True,
        )
        for i, f in enumerate(applied_forces_data, 1)
    ]
    
    # Extract unknowns
    unknowns = extract_unknowns(normalized)
    
    # Check for missing required fields
    missing = []
    if scenario is None:
        missing.append("scenario_type")
    else:
        for slot in REQUIRED_SLOTS.get(scenario, []):
            present = {
                "mass_kg": bool(physics_objects and physics_objects[0].mass_kg is not None),
                "mass_kg_list_min2": len([o for o in physics_objects if o.mass_kg is not None]) >= 2,
                "incline_angle_deg": physics_geometry.incline_angle_deg is not None,
                "projectile_angle_deg": physics_geometry.projectile_angle_deg is not None,
                "initial_speed_ms": physics_geometry.initial_speed_ms is not None,
            }.get(slot, False)
            if not present:
                missing.append(slot)
    
    if missing:
        _log_incomplete_parse(text, missing)
    
    return PhysicsFeatures(
        scenario_type=scenario,
        subscenario=None,
        physics_topic="mechanics",
        confidence=confidence,
        dimensionality="2d",
        is_static="at rest" in normalized or "equilibrium" in normalized,
        objects=physics_objects,
        geometry=physics_geometry,
        forces=physics_forces,
        friction=physics_friction,
        unknowns=unknowns,
        missing_required=missing,
    )


def _extract_scene_features(text: str, normalized: str, physics: PhysicsFeatures) -> SceneFeatures:
    """Extract Category 2: Scene Features."""
    scene = SceneFeatures()
    
    # Convert physics objects to scene objects
    for phys_obj in physics.objects:
        # Infer object type from label or default to block
        obj_type_map = {
            "box": "block", "block": "block", "crate": "block",
            "ball": "sphere", "sphere": "sphere",
            "cart": "cart", "suitcase": "cart",
            "mass": "hanging_mass" if "hang" in normalized or "pulley" in normalized else "block",
        }
        obj_type = obj_type_map.get(phys_obj.label or "block", "block")
        
        # Infer shape
        shape = "sphere" if obj_type in {"sphere", "ball"} else "box"
        
        # Infer material
        material = "generic"
        if "wood" in normalized:
            material = "wood"
        elif "metal" in normalized:
            material = "metal"
        elif "rubber" in normalized:
            material = "rubber"
        
        # Infer current state
        if "at rest" in normalized or "rests" in normalized:
            state = "at_rest"
        elif "moving" in normalized or "sliding" in normalized:
            state = "moving"
        elif "accelerating" in normalized:
            state = "moving"  # accelerating implies moving
        elif "hanging" in normalized:
            state = "suspended"
        else:
            state = "at_rest"
        
        # Infer motion direction
        motion_dir = None
        if "up" in normalized and ("incline" in normalized or "ramp" in normalized):
            motion_dir = "up_incline"
        elif "down" in normalized and ("incline" in normalized or "ramp" in normalized):
            motion_dir = "down_incline"
        elif "right" in normalized:
            motion_dir = "right"
        elif "left" in normalized:
            motion_dir = "left"
        
        scene.objects.append(SceneObject(
            id=phys_obj.id,
            name=phys_obj.name or phys_obj.label or "object",
            category="rigid_body",
            shape=shape,
            material=material,
            current_state=state,
            motion_direction=motion_dir,
        ))
    
    # Add surfaces based on scenario
    if physics.scenario_type == "inclined_plane":
        scene.surfaces.append(SceneSurface(
            id="incline_surface",
            type="incline",
            angle_deg=physics.geometry.incline_angle_deg,
        ))
        if scene.objects:
            scene.relationships.append(SceneRelationship(
                subject=scene.objects[0].id,
                predicate="rests_on",
                object="incline_surface",
            ))
            scene.contacts.append(ContactInfo(
                object_a=scene.objects[0].id,
                object_b="incline_surface",
                contact_type="rests_on",
            ))
    elif physics.scenario_type in {"horizontal_friction", "projectile_motion"}:
        scene.surfaces.append(SceneSurface(
            id="ground",
            type="ground" if physics.scenario_type == "projectile_motion" else "floor",
        ))
        if scene.objects and physics.scenario_type == "horizontal_friction":
            scene.relationships.append(SceneRelationship(
                subject=scene.objects[0].id,
                predicate="rests_on",
                object="ground",
            ))
            scene.contacts.append(ContactInfo(
                object_a=scene.objects[0].id,
                object_b="ground",
                contact_type="rests_on",
            ))
    elif physics.scenario_type == "atwood_pulley":
        scene.surfaces.append(SceneSurface(
            id="pulley_support",
            type="ceiling",
        ))
        scene.connections.append(SceneConnection(
            id="pulley_rope",
            type="pulley",
            from_object=scene.objects[0].id if len(scene.objects) > 0 else "object_1",
            to_object=scene.objects[1].id if len(scene.objects) > 1 else "object_2",
        ))
    
    # Add constraints
    if physics.friction.type == "frictionless":
        for obj in scene.objects:
            scene.constraints.append(SceneConstraint(
                object_id=obj.id,
                type="frictionless",
            ))
    
    return scene


def _extract_render_features(text: str, normalized: str, physics: PhysicsFeatures, scene: SceneFeatures) -> RenderFeatures:
    """Extract Category 3: Render Features."""
    render = RenderFeatures()
    
    # Determine diagram style
    if "fbd" in normalized or "free body" in normalized or "free-body" in normalized:
        render.diagram_style = DiagramStyle(type="fbd")
    elif "component" in normalized:
        render.diagram_style = DiagramStyle(type="components", emphasize_components=True)
    elif "trajectory" in normalized:
        render.diagram_style = DiagramStyle(type="motion_diagram")
    else:
        # Default based on scenario
        style_map = {
            "projectile_motion": "motion_diagram",
            "atwood_pulley": "fbd",
            "inclined_plane": "fbd",
            "horizontal_friction": "fbd",
        }
        render.diagram_style = DiagramStyle(type=style_map.get(physics.scenario_type or "fbd", "fbd"))
    
    # Camera view
    render.camera = CameraView(type="side")
    
    # Label configuration
    render.label_config = LabelConfig(
        show_object_labels=True,
        show_force_labels=True,
        show_angle_labels=True,
        label_style="numeric" if "numeric" in normalized else "symbolic",
    )
    
    # Title
    title_map = {
        "inclined_plane": "Inclined Plane Free-Body Diagram",
        "horizontal_friction": "Horizontal Free-Body Diagram",
        "atwood_pulley": "Atwood Pulley Free-Body Diagram",
        "projectile_motion": "Projectile Motion Diagram",
    }
    render.title = title_map.get(physics.scenario_type or "", "Free-Body Diagram")
    
    return render


@dataclass
class UnifiedParseResult:
    """Container for all three feature categories."""
    physics: PhysicsFeatures
    scene: SceneFeatures
    render: RenderFeatures
    raw_text: str


def parse_unified(text: str) -> UnifiedParseResult:
    """Parse a physics problem into three independent feature sets.
    
    Returns:
        UnifiedParseResult with physics, scene, and render features separated.
    """
    normalized = _normalize_text(text)
    
    physics = _extract_physics_features(text, normalized)
    scene = _extract_scene_features(text, normalized, physics)
    render = _extract_render_features(text, normalized, physics, scene)
    
    return UnifiedParseResult(
        physics=physics,
        scene=scene,
        render=render,
        raw_text=text,
    )
