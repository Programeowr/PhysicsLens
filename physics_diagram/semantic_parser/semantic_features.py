"""Data structures for semantic features extracted from physics problems.

These structures capture scene understanding, relationships, and visual context
beyond the numerical quantities extracted by the deterministic parser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ═══════════════════════════════════════════════════════════════════════════
# ENTITIES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Entity:
    """A physical entity in the scene (object, actor, surface, connection)."""
    
    id: str
    type: str  # "block", "sphere", "rope", "spring", "pulley", "incline", "person", "ground"
    category: str  # "rigid_body", "deformable", "connection", "surface", "actor"
    subtype: str | None = None  # "wooden_block", "rubber_ball", "ideal_pulley"
    shape: str | None = None  # "box", "sphere", "cylinder"
    material: str | None = None  # "wood", "metal", "rubber", "rope", "steel"
    size_hint: str | None = None  # "small", "large", or extracted dimensions
    mentioned_explicitly: bool = True  # False for inferred entities
    confidence: float = 1.0


# ═══════════════════════════════════════════════════════════════════════════
# RELATIONSHIPS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Relation:
    """A spatial or causal relationship between two entities."""
    
    subject: str  # entity id
    predicate: str  # relationship type
    object: str  # entity id
    confidence: float = 1.0
    
    # Common predicates:
    # Spatial: "rests_on", "hangs_from", "attached_to", "touches", "above", "below"
    # Causal: "pushes", "pulls", "supports", "constrains"
    # Containment: "inside", "on_top_of"


# ═══════════════════════════════════════════════════════════════════════════
# CONNECTIONS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Connection:
    """A mechanical connection between entities (rope, spring, chain, etc)."""
    
    id: str
    type: str  # "rope", "spring", "rod", "chain", "cable", "hinge", "pulley"
    from_entity: str
    to_entity: str
    properties: dict[str, float | bool | str] = field(default_factory=dict)
    # Properties examples:
    # {"length_m": 2.0, "massless": True, "k_spring": 200.0, "inextensible": True}


# ═══════════════════════════════════════════════════════════════════════════
# OBJECT STATE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class EntityState:
    """Motion and kinematic state of an entity."""
    
    entity_id: str
    kinematic_state: Literal["at_rest", "moving", "accelerating", "rotating", "suspended"]
    velocity_direction: str | None = None  # "right", "left", "up_incline", "down_incline"
    angular_motion: str | None = None  # "clockwise", "counterclockwise"
    motion_type: str | None = None  # "sliding", "rolling", "rolling_without_slipping"


# ═══════════════════════════════════════════════════════════════════════════
# FORCES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class EnrichedForce:
    """Force with semantic enrichment (source, target, application point)."""
    
    id: str
    type: str  # "gravity", "normal", "friction", "applied", "tension", "spring", "drag", "buoyant"
    source_entity: str | None = None  # Who/what applies it (actor id, or None for gravity)
    target_entity: str | None = None  # What it acts on
    application_point: str | None = None  # "center", "edge", "contact_surface"
    line_of_action: str | None = None  # "parallel_to_incline", "perpendicular_to_surface"
    magnitude_n: float | None = None
    direction: str | None = None  # "horizontal", "vertical", "along_incline"
    angle_deg: float | None = None
    reference_frame: str = "horizontal"  # "horizontal", "incline_parallel", "radial"
    is_known: bool = False
    is_requested_unknown: bool = False


# ═══════════════════════════════════════════════════════════════════════════
# CONSTRAINTS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Constraint:
    """Physical constraint or idealization."""
    
    entity_id: str | None  # None = global constraint
    type: str
    description: str
    
    # Constraint types:
    # Friction: "frictionless", "rough", "coefficient_given"
    # Idealization: "massless_rope", "ideal_pulley", "light_string", "rigid_body"
    # Motion: "no_slipping", "rolling_without_slipping", "constant_speed"
    # Support: "fixed_support", "pinned", "hinged"


# ═══════════════════════════════════════════════════════════════════════════
# MATERIALS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MaterialInfo:
    """Material properties and appearance."""
    
    entity_id: str
    material: str  # "wood", "metal", "rubber", "concrete", "ice", "steel"
    texture: str | None = None  # "smooth", "rough", "polished"
    density_hint: str | None = None  # "heavy", "light"
    color_hint: str | None = None  # "red", "blue" (rare in physics problems)


# ═══════════════════════════════════════════════════════════════════════════
# RENDERING HINTS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class RenderHints:
    """Visual rendering preferences extracted from problem text."""
    
    diagram_style: str = "fbd"  # "fbd", "motion_diagram", "components", "energy"
    camera_view: str = "side"  # "side", "top", "front", "isometric"
    show_coordinate_axes: bool = False
    coordinate_type: str | None = None  # "cartesian", "inclined", "polar"
    show_components: bool = False
    show_angle_markers: bool = True
    label_style: str = "numeric"  # "symbolic", "numeric", "mixed"
    force_arrow_style: str = "standard"  # "standard", "thick", "dashed"
    scaling_preference: str = "auto"  # "auto", "fit_to_width", "actual_scale"


# ═══════════════════════════════════════════════════════════════════════════
# SEMANTIC FEATURES (Top-level container)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SemanticFeatures:
    """Complete semantic understanding of a physics problem.
    
    This is the output of the semantic parsing layer that enriches the
    deterministic parser's ParseResult with scene understanding.
    """
    
    entities: list[Entity] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    states: list[EntityState] = field(default_factory=list)
    enriched_forces: list[EnrichedForce] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    materials: list[MaterialInfo] = field(default_factory=list)
    render_hints: RenderHints = field(default_factory=RenderHints)
    
    # Metadata
    extraction_method: str = "rule_based"  # "llm", "rule_based", "hybrid"
    confidence: float = 1.0
    validation_warnings: list[str] = field(default_factory=list)
