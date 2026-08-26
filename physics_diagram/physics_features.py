"""Category 1: Physics Features — Input to the physics solver only.

These features contain ONLY information required to compute forces, motion, energy,
momentum, etc. They must NEVER contain rendering information such as positions,
colors, spacing, or camera angles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PhysicsObject:
    """A physical object with mass and identity."""
    id: str
    name: str = ""  # "block", "sphere", "cart"
    mass_kg: Optional[float] = None
    label: Optional[str] = None
    moment_of_inertia_kgm2: Optional[float] = None  # for rotational motion
    charge_c: Optional[float] = None  # for electric forces
    volume_m3: Optional[float] = None  # for buoyancy


@dataclass
class PhysicsGeometry:
    """Geometric parameters required for physics calculations."""
    # Angles
    incline_angle_deg: Optional[float] = None
    projectile_angle_deg: Optional[float] = None
    
    # Distances and dimensions
    distance_m: Optional[float] = None
    height_m: Optional[float] = None
    length_m: Optional[float] = None
    width_m: Optional[float] = None
    radius_m: Optional[float] = None
    diameter_m: Optional[float] = None
    
    # Motion parameters
    initial_speed_ms: Optional[float] = None
    final_speed_ms: Optional[float] = None
    
    # Coordinates (if specified)
    coordinates: dict = field(default_factory=dict)  # {"x": 0, "y": 5}


@dataclass
class PhysicsForce:
    """A force with all properties needed for calculation."""
    id: str
    type: str  # gravity | normal | friction | applied | tension | spring | air_resistance | electric | magnetic | buoyant
    magnitude_n: Optional[float] = None  # None if unknown
    direction: str = "unspecified"  # right | left | uphill | down | up | unspecified
    angle_deg: Optional[float] = None
    reference_frame: str = "horizontal"  # horizontal | incline | vertical
    
    # Force relationships
    source_object: str = ""  # what causes this force
    target_object: str = ""  # what receives this force
    application_point: str = "center"  # center | edge | top | bottom | left | right
    line_of_action: str = ""  # description of force line
    
    # Status
    is_known: bool = False  # True if magnitude is given
    is_unknown: bool = False  # True if we need to solve for it


@dataclass
class PhysicsFriction:
    """Friction properties."""
    type: Optional[str] = None  # frictionless | kinetic | static
    coefficient: Optional[float] = None  # μ value
    coefficient_kinetic: Optional[float] = None  # μ_k
    coefficient_static: Optional[float] = None  # μ_s


@dataclass
class PhysicsConstraint:
    """Physical constraints between objects."""
    type: str  # rope | pulley_rope | spring | contact | string | fixed | pinned | hinge
    object_a_id: str
    object_b_id: str = ""
    properties: dict = field(default_factory=dict)  # spring_constant_nm, length_m, rope_length_m, etc.
    is_inextensible: bool = False  # for ropes
    is_massless: bool = False  # for ropes, pulleys
    is_ideal: bool = False  # for pulleys, springs


@dataclass
class MotionState:
    """Current motion state of an object."""
    object_id: str
    velocity_ms: Optional[float] = None
    velocity_direction: Optional[str] = None  # right | left | up | down | up_incline | down_incline
    acceleration_ms2: Optional[float] = None
    acceleration_direction: Optional[str] = None
    angular_velocity_rads: Optional[float] = None
    angular_acceleration_rads2: Optional[float] = None
    is_constant_speed: bool = False
    is_accelerating: bool = False
    is_rotating: bool = False
    rotation_direction: Optional[str] = None  # clockwise | counterclockwise


@dataclass
class InitialConditions:
    """Initial state of the system."""
    motion_states: list[MotionState] = field(default_factory=list)
    time_s: float = 0.0


@dataclass
class PhysicsEnvironment:
    """Environmental parameters."""
    gravity_ms2: float = 9.8
    atmosphere: str = "air"  # air | vacuum | water
    temperature_k: Optional[float] = None
    pressure_pa: Optional[float] = None
    fluid_density_kgm3: Optional[float] = None  # for buoyancy


@dataclass
class PhysicsFeatures:
    """Complete physics specification — input to solver.
    
    This contains ONLY physics information. No rendering hints.
    """
    # Scenario metadata
    scenario_type: Optional[str]  # inclined_plane | horizontal_friction | atwood_pulley | projectile_motion | circular_motion
    subscenario: Optional[str] = None  # rolling_without_slipping | elastic_collision | inelastic_collision
    physics_topic: str = "mechanics"  # mechanics | thermodynamics | electromagnetism | optics | quantum
    confidence: float = 0.0
    dimensionality: str = "2d"  # 1d | 2d | 3d
    is_static: bool = True  # static equilibrium vs dynamic
    
    # Objects and environment
    objects: list[PhysicsObject] = field(default_factory=list)
    environment: PhysicsEnvironment = field(default_factory=PhysicsEnvironment)
    
    # Geometry
    geometry: PhysicsGeometry = field(default_factory=PhysicsGeometry)
    
    # Forces (all forces, known and unknown)
    forces: list[PhysicsForce] = field(default_factory=list)
    friction: PhysicsFriction = field(default_factory=PhysicsFriction)
    
    # Constraints
    constraints: list[PhysicsConstraint] = field(default_factory=list)
    
    # Motion
    initial_conditions: InitialConditions = field(default_factory=InitialConditions)
    
    # Knowns and unknowns
    unknowns: list[str] = field(default_factory=list)  # what to solve for
    known_quantities: list[str] = field(default_factory=list)
    
    # Validation
    missing_required: list[str] = field(default_factory=list)
    
    @property
    def is_complete(self) -> bool:
        """True when all required fields for the scenario are present."""
        return len(self.missing_required) == 0
    
    @property
    def num_objects(self) -> int:
        """Number of objects in the problem."""
        return len(self.objects)


@dataclass
class ForceSolution:
    """Output from physics solver — computed force values."""
    scenario_type: str
    forces: list[ForceVector]
    derived_values: dict  # normal_force_n, acceleration_ms2, tension_n, etc.


@dataclass
class ForceVector:
    """A computed force with magnitude, direction in screen coordinates."""
    name: str
    magnitude_n: float
    direction_deg: float  # screen coordinates: 0=right, 90=down, 180=left, 270=up
    anchor: str  # object ID this force acts on
