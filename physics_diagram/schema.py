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
