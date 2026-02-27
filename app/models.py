"""
Pydantic v2 models for validated physics problem parsing output.

These models define the strict schema that the AI parser must produce.
Referential integrity is enforced: all object_id and surface_id references
must point to valid entries in the objects/surfaces lists.
"""

from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field, model_validator


# ── Enums ────────────────────────────────────────────────────────────────

class ObjectType(str, Enum):
    block = "block"
    sphere = "sphere"
    body = "body"
    cart = "cart"
    rope = "rope"
    pulley_wheel = "pulley_wheel"
    wedge = "wedge"
    spring_obj = "spring_obj"


class SurfaceType(str, Enum):
    horizontal_surface = "horizontal_surface"
    inclined_plane = "inclined_plane"
    vertical_wall = "vertical_wall"
    pulley = "pulley"
    circular_path = "circular_path"
    fluid_surface = "fluid_surface"


class ForceType(str, Enum):
    applied = "applied"
    gravity = "gravity"
    normal = "normal"
    tension = "tension"
    spring = "spring"
    friction_force = "friction_force"
    buoyancy = "buoyancy"
    centripetal_force = "centripetal_force"
    drag = "drag"


class ForceDirection(str, Enum):
    up = "up"
    down = "down"
    left = "left"
    right = "right"
    up_along_plane = "up_along_plane"
    down_along_plane = "down_along_plane"
    vertical_down = "vertical_down"
    vertical_up = "vertical_up"
    perpendicular_to_surface = "perpendicular_to_surface"
    centripetal = "centripetal"
    tangential = "tangential"
    radially_outward = "radially_outward"


# ── Sub-models ───────────────────────────────────────────────────────────

class PhysicsObject(BaseModel):
    """A physical object in the problem (block, sphere, etc.)."""
    id: str = Field(..., description="Unique identifier for this object")
    type: ObjectType = Field(..., description="Type of object")
    mass: Optional[float] = Field(None, description="Mass in kg", ge=0)


class Surface(BaseModel):
    """A surface or constraint in the problem."""
    id: str = Field(..., description="Unique identifier for this surface")
    type: SurfaceType = Field(..., description="Type of surface")
    angle: Optional[float] = Field(None, description="Angle in degrees", ge=0, le=360)
    friction_coefficient: Optional[float] = Field(None, description="Coefficient of friction", ge=0, le=2.0)


class Placement(BaseModel):
    """Links an object to the surface it rests on."""
    object_id: str = Field(..., description="ID of the object")
    surface_id: str = Field(..., description="ID of the surface")


class Force(BaseModel):
    """A force acting on an object."""
    type: ForceType = Field(..., description="Type of force")
    magnitude: Optional[float] = Field(None, description="Force magnitude in Newtons", ge=0)
    direction: ForceDirection = Field(..., description="Direction of the force")
    object_id: str = Field(..., description="ID of the object this force acts on")


class Friction(BaseModel):
    """Friction information for an object."""
    object_id: str = Field(..., description="ID of the object")
    coefficient: Optional[float] = Field(None, description="Coefficient of friction", ge=0, le=2.0)


class PhysicsConstants(BaseModel):
    """Physical constants used in the problem."""
    gravity: float = Field(default=9.8, description="Acceleration due to gravity (m/s²)")


# ── Top-level parsed result ─────────────────────────────────────────────

class ParsedPhysicsProblem(BaseModel):
    """
    Complete parsed physics problem.

    Validates referential integrity: all object_id and surface_id
    references in placements and forces must exist in the objects
    and surfaces lists.
    """
    objects: list[PhysicsObject] = Field(default_factory=list)
    surfaces: list[Surface] = Field(default_factory=list)
    placements: list[Placement] = Field(default_factory=list)
    forces: list[Force] = Field(default_factory=list)
    friction: Optional[Friction] = None
    constants: PhysicsConstants = Field(default_factory=PhysicsConstants)

    @model_validator(mode="after")
    def validate_references(self) -> "ParsedPhysicsProblem":
        """Ensure all object_id and surface_id references are valid."""
        object_ids = {obj.id for obj in self.objects}
        surface_ids = {s.id for s in self.surfaces}

        # Check placements
        for p in self.placements:
            if p.object_id not in object_ids:
                raise ValueError(
                    f"Placement references unknown object_id '{p.object_id}'. "
                    f"Available objects: {object_ids}"
                )
            if p.surface_id not in surface_ids:
                raise ValueError(
                    f"Placement references unknown surface_id '{p.surface_id}'. "
                    f"Available surfaces: {surface_ids}"
                )

        # Check forces
        for f in self.forces:
            if f.object_id not in object_ids:
                raise ValueError(
                    f"Force references unknown object_id '{f.object_id}'. "
                    f"Available objects: {object_ids}"
                )

        # Check friction
        if self.friction and self.friction.object_id not in object_ids:
            raise ValueError(
                f"Friction references unknown object_id '{self.friction.object_id}'. "
                f"Available objects: {object_ids}"
            )

        return self

    def get_primary_surface_type(self) -> Optional[SurfaceType]:
        """Return the type of the first surface, used for diagram routing."""
        if self.surfaces:
            return self.surfaces[0].type
        return None

    def has_pulley(self) -> bool:
        """Check if any surface is a pulley."""
        return any(s.type == SurfaceType.pulley for s in self.surfaces)


# ── Request model ────────────────────────────────────────────────────────

class ProblemInput(BaseModel):
    """Input model for the /parse endpoint."""
    problem: str = Field(..., min_length=10, max_length=2000, description="Physics problem text")
