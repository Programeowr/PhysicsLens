"""Scene Graph data structures - the single source of truth for rendering.

The Scene Graph is analogous to an Abstract Syntax Tree (AST) in compilers.
It represents the complete physical scene in a renderer-agnostic way.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .semantic_parser.semantic_features import (
    Connection,
    Constraint,
    Entity,
    EnrichedForce,
    EntityState,
    MaterialInfo,
    Relation,
    RenderHints,
)


@dataclass
class SceneGraph:
    """Complete scene representation - the renderer's single source of truth.
    
    This structure contains everything needed to render a physics diagram
    without referring back to the original problem text or ParseResult.
    
    It merges:
    - Physics data (from deterministic parser + solver)
    - Scene semantics (from semantic parser)
    - Rendering preferences
    """
    
    # ── Metadata ─────────────────────────────────────────────────────────────
    scenario_type: str | None
    physics_topic: str = "mechanics"
    dimensionality: str = "2d"
    
    # ── Entities (from semantic parser) ──────────────────────────────────────
    entities: list[Entity] = field(default_factory=list)
    
    # ── Hierarchy (parent-child relationships) ───────────────────────────────
    # Example: {"person_1": ["block_1"], "block_1": ["incline_1"]}
    hierarchy: dict[str, list[str]] = field(default_factory=dict)
    
    # ── Relationships (spatial and causal) ───────────────────────────────────
    relationships: list[Relation] = field(default_factory=list)
    
    # ── Connections (mechanical) ─────────────────────────────────────────────
    connections: list[Connection] = field(default_factory=list)
    
    # ── Physics data (from deterministic parser + solver) ────────────────────
    masses: dict[str, float] = field(default_factory=dict)  # {entity_id: mass_kg}
    forces: list[EnrichedForce] = field(default_factory=list)
    force_solutions: dict[str, float] = field(default_factory=dict)  # {force_id: magnitude_n}
    
    # ── Geometry (from deterministic parser) ─────────────────────────────────
    incline_angle_deg: float | None = None
    projectile_angle_deg: float | None = None
    initial_speed_ms: float | None = None
    
    # ── Motion and state ─────────────────────────────────────────────────────
    states: dict[str, EntityState] = field(default_factory=dict)  # {entity_id: state}
    
    # ── Constraints ──────────────────────────────────────────────────────────
    constraints: list[Constraint] = field(default_factory=list)
    
    # ── Materials and appearance ─────────────────────────────────────────────
    materials: dict[str, MaterialInfo] = field(default_factory=dict)  # {entity_id: material}
    
    # ── Rendering hints ──────────────────────────────────────────────────────
    render_hints: RenderHints = field(default_factory=RenderHints)
    
    # ── Validation ───────────────────────────────────────────────────────────
    is_complete: bool = True
    missing_data: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # ── Metadata ─────────────────────────────────────────────────────────────
    raw_text: str = ""
    confidence: float = 1.0
    
    def get_entity(self, entity_id: str) -> Entity | None:
        """Get entity by ID."""
        return next((e for e in self.entities if e.id == entity_id), None)
    
    def get_rigid_bodies(self) -> list[Entity]:
        """Get all rigid body entities (main objects in physics problems)."""
        return [e for e in self.entities if e.category == "rigid_body"]
    
    def get_surfaces(self) -> list[Entity]:
        """Get all surface entities."""
        return [e for e in self.entities if e.category == "surface"]
    
    def get_actors(self) -> list[Entity]:
        """Get all actor entities (people, workers, etc)."""
        return [e for e in self.entities if e.category == "actor"]
    
    def get_relationships_for(self, entity_id: str) -> list[Relation]:
        """Get all relationships involving an entity."""
        return [
            r for r in self.relationships 
            if r.subject == entity_id or r.object == entity_id
        ]
    
    def get_forces_on(self, entity_id: str) -> list[EnrichedForce]:
        """Get all forces acting on an entity."""
        return [f for f in self.forces if f.target_entity == entity_id]
    
    def get_material_for(self, entity_id: str) -> MaterialInfo | None:
        """Get material info for an entity."""
        return self.materials.get(entity_id)
    
    def get_state_for(self, entity_id: str) -> EntityState | None:
        """Get motion state for an entity."""
        return self.states.get(entity_id)
