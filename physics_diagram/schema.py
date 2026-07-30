"""Typed data structures shared by the PhysicsLens pipeline."""

from __future__ import annotations

from dataclasses import dataclass
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
class DiagramIntent:
    title: str = ""
    view_mode: str = "fbd"
    emphasize_components: bool = False
    show_annotations: bool = True


@dataclass
class RenderHints:
    scene_style: str = "default"
    object_shape: str = "box"
    show_surface: bool = True
    show_title: bool = True


@dataclass
class SceneCanvas:
    width: float = 900.0
    height: float = 620.0
    background: str = "white"


@dataclass
class SceneObject:
    id: str
    label: str
    shape: str = "box"
    mass_kg: Optional[float] = None
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    rotation_deg: float = 0.0
    fill: str = "#e6e6e6"
    stroke: str = "#222"


@dataclass
class SceneSurface:
    kind: str
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    stroke: str = "#555"
    stroke_width: float = 4.0
    angle_deg: Optional[float] = None


@dataclass
class SceneForce:
    name: str
    magnitude_n: float
    direction_deg: float
    anchor_id: str
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    label_x: float = 0.0
    label_y: float = 0.0
    color: str = "#333"


@dataclass
class SceneAnnotation:
    text: str
    x: float
    y: float
    anchor_id: Optional[str] = None
    align: str = "middle"
    fill: str = "#222"
    size: float = 14.0


@dataclass
class SceneGraph:
    canvas: SceneCanvas
    title: str
    scenario_type: Optional[str]
    intent: DiagramIntent
    hints: RenderHints
    objects: list[SceneObject]
    surfaces: list[SceneSurface]
    forces: list[SceneForce]
    annotations: list[SceneAnnotation]
    source_result: Optional[ParseResult] = None
    source_solution: Optional[ForceSolution] = None


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
