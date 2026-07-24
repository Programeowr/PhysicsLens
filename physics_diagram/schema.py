"""Typed data structures shared by the PhysicsLens pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ObjectSpec:
    id: str
    shape: str = "box"  # box | sphere | block | particle
    mass_kg: Optional[float] = None
    label: Optional[str] = None


@dataclass
class Geometry:
    incline_angle_deg: Optional[float] = None
    projectile_angle_deg: Optional[float] = None
    initial_speed_ms: Optional[float] = None


@dataclass
class AppliedForce:
    magnitude_n: float
    direction: str = "unspecified"


@dataclass
class ParseResult:
    scenario_type: Optional[str]
    confidence: float
    objects: list[ObjectSpec]
    geometry: Geometry
    friction: Optional[str]
    mu: Optional[float]
    applied_forces: list[AppliedForce]
    unknowns: list[str]
    dimension: str = "2d"
    missing_required: list[str] = None  # type: ignore[assignment]
    raw_text: str = ""

    def __post_init__(self) -> None:
        if self.missing_required is None:
            self.missing_required = []

    @property
    def is_complete(self) -> bool:
        return self.scenario_type is not None and not self.missing_required


@dataclass
class ForceVector:
    name: str  # normal_force | weight | friction | tension | applied_force
    magnitude_n: float
    direction_deg: float  # 0 right, 90 up; counter-clockwise
    anchor: str


@dataclass
class ForceSolution:
    scenario_type: str
    forces: list[ForceVector]
    derived_values: dict[str, float | str | None]


@dataclass
class SceneCanvas:
    width: int
    height: int
    margin: int = 56


@dataclass
class SceneSurface:
    type: str
    angle: Optional[float] = None
    start: tuple[float, float] | None = None
    end: tuple[float, float] | None = None
    center: tuple[float, float] | None = None
    radius: Optional[float] = None
    points: list[tuple[float, float]] | None = None
    label: str = ""


@dataclass
class SceneObject:
    id: str
    type: str = "block"
    rotation_deg: float = 0.0
    position: tuple[float, float] = (0.0, 0.0)
    width: float = 88.0
    height: float = 56.0
    radius: float = 16.0
    label: str = ""
    mass_kg: Optional[float] = None


@dataclass
class SceneForce:
    label: str
    origin: str
    magnitude_n: float
    direction_deg: float
    anchor_position: tuple[float, float] | None = None
    tip_position: tuple[float, float] | None = None
    label_position: tuple[float, float] | None = None
    offset: float = 0.0
    color: str = ""


@dataclass
class SceneAnnotation:
    type: str
    value: float
    origin: Optional[str] = None
    position: tuple[float, float] | None = None
    radius: Optional[float] = None
    label_position: tuple[float, float] | None = None


@dataclass
class SceneGraph:
    canvas: SceneCanvas
    surfaces: list[SceneSurface] = field(default_factory=list)
    objects: list[SceneObject] = field(default_factory=list)
    forces: list[SceneForce] = field(default_factory=list)
    annotations: list[SceneAnnotation] = field(default_factory=list)
    title: str = "PhysicsLens Diagram"
