"""Category 2: Scene Features — What exists and how it's related.

This is the scene graph. It describes the physical setup independently of SVG.
A renderer should be able to recreate the scene without referring to the
original problem statement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SceneObject:
    """A physical object in the scene with visual properties."""
    id: str
    name: str  # "block", "sphere", "cart", "crate"
    category: str = "rigid_body"  # rigid_body | particle | fluid | deformable
    subtype: str = ""  # wooden_block | metal_sphere | rubber_ball
    shape: str = "box"  # box | sphere | cylinder | irregular | wheel
    material: str = "generic"  # wood | metal | plastic | rubber | generic
    approximate_size: str = "medium"  # small | medium | large
    orientation: str = "horizontal"  # horizontal | vertical | tilted
    texture: Optional[str] = None  # rough | smooth | patterned
    color: Optional[str] = None  # if mentioned in problem
    current_state: str = "at_rest"  # at_rest | moving | rotating | rolling | sliding | suspended
    motion_direction: Optional[str] = None  # right | left | up | down | up_incline | down_incline


@dataclass
class SceneActor:
    """A person or living entity in the scene."""
    id: str
    type: str  # person | child | boy | girl | worker | cyclist | driver
    action: str  # pushes | pulls | lifts | holds | rides | walks
    target_object: str  # object ID being acted upon
    posture: str = "standing"  # standing | sitting | crouching | lying
    position: str = "left"  # left | right | center | behind | in_front


@dataclass
class SceneSurface:
    """A surface in the scene."""
    id: str
    type: str  # ground | incline | table | wall | ceiling | floor | road
    material: str = "generic"  # rough | smooth | frictionless | ice | concrete | wood
    angle_deg: Optional[float] = None  # for inclined surfaces
    orientation: str = "horizontal"  # horizontal | vertical | tilted
    dimensions: dict = field(default_factory=dict)  # {"length_m": 5, "width_m": 2}


@dataclass
class SceneConnection:
    """A physical connection between objects."""
    id: str
    type: str  # rope | spring | cable | rod | pulley | hinge | chain | string
    from_object: str  # object ID
    to_object: str  # object ID or surface ID
    properties: dict = field(default_factory=dict)  # length_m, stiffness_nm, mass_kg
    length_m: Optional[float] = None
    is_extensible: bool = True
    is_massless: bool = False


@dataclass
class SceneRelationship:
    """Explicit spatial/semantic relationship between scene elements."""
    subject: str  # object/actor ID
    predicate: str  # pushes | rests_on | attached_to | supports | touches | connected_to | hangs_from | leans_against
    object: str  # object/surface ID


@dataclass
class ContactInfo:
    """Contact point between two scene elements."""
    object_a: str
    object_b: str
    contact_type: str  # touches | rests_on | pressed_against | sliding_on
    contact_location: str = "bottom"  # bottom | top | side | edge | corner


@dataclass
class SceneConstraint:
    """Physical constraint on an object."""
    object_id: str
    type: str  # fixed | pinned | suspended | rolling_without_slipping | frictionless | ideal_pulley | no_slipping
    reference: Optional[str] = None  # what it's constrained to (surface ID, anchor point)
    description: str = ""  # "rope is inextensible", "pulley is massless"


@dataclass
class MotionIndicator:
    """Visual motion indicator (velocity/acceleration vectors)."""
    object_id: str
    type: str  # velocity | acceleration | angular_velocity | trajectory
    magnitude: Optional[float] = None
    direction: Optional[str] = None  # right | left | up | down
    angle_deg: Optional[float] = None


@dataclass
class SceneFeatures:
    """Complete scene graph — what exists and how it's related.
    
    This contains NO physics calculations and NO rendering coordinates.
    It's a pure structural description of the scene.
    """
    # Scene elements
    objects: list[SceneObject] = field(default_factory=list)
    actors: list[SceneActor] = field(default_factory=list)
    surfaces: list[SceneSurface] = field(default_factory=list)
    connections: list[SceneConnection] = field(default_factory=list)
    
    # Relationships and spatial structure
    relationships: list[SceneRelationship] = field(default_factory=list)
    contacts: list[ContactInfo] = field(default_factory=list)
    constraints: list[SceneConstraint] = field(default_factory=list)
    
    # Motion indicators (for rendering velocity/acceleration arrows)
    motion_indicators: list[MotionIndicator] = field(default_factory=list)
    
    # Scene context
    environment: str = "generic"  # indoor | outdoor | laboratory | classroom
    scale: str = "human"  # microscopic | human | astronomical
    lighting: str = "daylight"  # daylight | artificial | dark
    
    def get_object(self, obj_id: str) -> Optional[SceneObject]:
        """Retrieve an object by ID."""
        for obj in self.objects:
            if obj.id == obj_id:
                return obj
        return None
    
    def get_relationships_for(self, subject_id: str) -> list[SceneRelationship]:
        """Get all relationships where this object is the subject."""
        return [r for r in self.relationships if r.subject == subject_id]
    
    def get_connections_for(self, obj_id: str) -> list[SceneConnection]:
        """Get all connections involving this object."""
        return [c for c in self.connections if c.from_object == obj_id or c.to_object == obj_id]
    
    def build_scene_graph_text(self) -> str:
        """Build a text representation of the scene graph for debugging."""
        lines = ["Scene Graph:"]
        for rel in self.relationships:
            lines.append(f"  {rel.subject} → {rel.predicate} → {rel.object}")
        for conn in self.connections:
            lines.append(f"  {conn.from_object} ⟷ {conn.type} ⟷ {conn.to_object}")
        return "\n".join(lines)
