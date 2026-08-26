"""Typed data structures shared by the PhysicsLens pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# Layout / collision helpers
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class BoundingBox:
    """Axis-aligned bounding box used for collision detection and clamping."""
    x: float       # left edge
    y: float       # top edge
    w: float       # width  (>= 0)
    h: float       # height (>= 0)

    # ── derived geometry ─────────────────────────────────────────────────────
    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def overlaps(self, other: "BoundingBox", padding: float = 4.0) -> bool:
        """True when the two boxes overlap (with optional padding expansion)."""
        return (
            self.x - padding < other.x2 + padding
            and self.x2 + padding > other.x - padding
            and self.y - padding < other.y2 + padding
            and self.y2 + padding > other.y - padding
        )

    def clamp_point(self, px: float, py: float, margin: float = 0.0) -> tuple[float, float]:
        """Return (px, py) clamped so it lies inside this box (with margin)."""
        return (
            max(self.x + margin, min(self.x2 - margin, px)),
            max(self.y + margin, min(self.y2 - margin, py)),
        )

    def contains(self, px: float, py: float) -> bool:
        return self.x <= px <= self.x2 and self.y <= py <= self.y2


# ──────────────────────────────────────────────────────────────────────────────
# Primitive extraction slots
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ObjectSpec:
    id: str
    shape: str = "box"          # box | sphere | block | particle
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
    direction: str = "unspecified"  # right | left | uphill | unspecified
    angle_deg: Optional[float] = None  # angle relative to horizontal (for angled pulls/pushes)
    reference_frame: str = "horizontal"  # horizontal | incline | vertical


# ──────────────────────────────────────────────────────────────────────────────
# Visual-semantic feature layer
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ForceMention:
    """A force named in the problem text together with how it was worded.

    ``provenance`` records the exact verb or noun the user wrote
    (e.g. "push", "pull", "acts on", "tension in the string") so arrow labels
    and diagram captions can mirror the user's own language.
    """
    force_type: str          # weight | normal | friction | tension | applied | spring | air_resistance | component
    provenance: str          # raw phrase from the text, e.g. "pushed to the right"
    direction_hint: str = "unspecified"   # left | right | up | down | up_incline | down_incline | unspecified


@dataclass
class ConstraintRelationship:
    """Structural link between two objects (rope, pulley rope, spring, contact)."""
    kind: str                # rope | pulley_rope | spring | contact | string
    object_a_id: str
    object_b_id: str = ""    # empty when only one end is named


@dataclass
class AmbiguityFlag:
    """Records a feature that could not be resolved confidently.

    The renderer uses conservative defaults when a flag is present.
    """
    field: str               # e.g. "object_type", "motion_state", "view_mode"
    reason: str              # human-readable explanation
    confidence: float = 0.0  # 0 = no signal, 1 = clear


@dataclass
class VisualFeatures:
    """Visual-semantic features extracted alongside physics quantities.

    These fields drive renderer decisions (shape, surface texture, arrow style,
    diagram mode) without changing the solver inputs.
    """

    # ── Object appearance ────────────────────────────────────────────────────
    # One entry per parsed object, parallel to ParseResult.objects.
    # Values: box | cart | ball | sphere | crate | block | particle |
    #         hanging_mass | pulley_mass | spring_endpoint | projectile | unknown
    object_types: list[str] = field(default_factory=list)

    # ── Surface / environment ────────────────────────────────────────────────
    # Values: rough_floor | smooth_floor | frictionless_ramp | inclined_plane |
    #         ground | pulley_support | spring_anchor | air | table | unknown
    surface_type: str = "unknown"

    # ── Motion state ─────────────────────────────────────────────────────────
    # Values: at_rest | moving_right | moving_left | moving_up_incline |
    #         moving_down_incline | accelerating | decelerating |
    #         launched_upward | descending | equilibrium | unknown
    motion_state: str = "unknown"

    # ── Requested diagram view ───────────────────────────────────────────────
    # Values: fbd | scene_and_fbd | components | trajectory |
    #         velocity_diagram | acceleration_diagram |
    #         symbolic | numeric | unknown
    requested_view: str = "unknown"

    # ── Force mentions with provenance ───────────────────────────────────────
    force_mentions: list[ForceMention] = field(default_factory=list)

    # ── Structural constraints between objects ───────────────────────────────
    constraint_relationships: list[ConstraintRelationship] = field(default_factory=list)

    # ── Known vs unknown quantities ──────────────────────────────────────────
    # e.g. ["mass", "angle"] known, ["required_force"] unknown
    known_quantities: list[str] = field(default_factory=list)
    unknown_quantities: list[str] = field(default_factory=list)

    # ── Ambiguity flags ──────────────────────────────────────────────────────
    ambiguity_flags: list[AmbiguityFlag] = field(default_factory=list)

    @property
    def is_ambiguous(self) -> bool:
        """True when any visual feature could not be resolved confidently."""
        return bool(self.ambiguity_flags)

    @property
    def primary_object_type(self) -> str:
        """Convenience: first object type, or 'unknown'."""
        return self.object_types[0] if self.object_types else "unknown"


# ──────────────────────────────────────────────────────────────────────────────
# Diagram intent / render hints (consumed by scene_graph → renderer)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class DiagramIntent:
    title: str = ""
    view_mode: str = "fbd"           # fbd | scene_and_fbd | components | trajectory
    emphasize_components: bool = False
    show_annotations: bool = True


@dataclass
class RenderHints:
    scene_style: str = "default"
    object_shape: str = "box"        # box | sphere | cart | hanging_mass | projectile
    show_surface: bool = True
    show_title: bool = True
    surface_texture: str = "none"    # none | rough | smooth | frictionless
    show_velocity_vector: bool = False
    show_acceleration_vector: bool = False
    show_components: bool = False


# ──────────────────────────────────────────────────────────────────────────────
# Scene graph primitives
# ──────────────────────────────────────────────────────────────────────────────

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
    # Stable element ID for diagnostics / testing (set by layout_scene)
    element_id: str = ""

    def bbox(self) -> BoundingBox:
        """Axis-aligned bounding box (ignores rotation for simplicity)."""
        return BoundingBox(
            x=self.x - self.width / 2,
            y=self.y - self.height / 2,
            w=self.width,
            h=self.height,
        )


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
    # Stable element ID for diagnostics
    element_id: str = ""


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
    # Stable element ID for diagnostics
    element_id: str = ""

    def arrow_length(self) -> float:
        from math import hypot
        return hypot(self.x2 - self.x1, self.y2 - self.y1)

    def label_bbox(self, char_w: float = 7.5, line_h: float = 16.0) -> BoundingBox:
        """Approximate bounding box of the force label text."""
        # label text is like "Applied Force = 12.3 N" — rough width estimate
        label = self.name.replace("_", " ").title()
        chars = len(f"{label} = {self.magnitude_n:.1f} N")
        w = chars * char_w
        return BoundingBox(x=self.label_x - w / 2, y=self.label_y - line_h, w=w, h=line_h)


@dataclass
class SceneAnnotation:
    text: str
    x: float
    y: float
    anchor_id: Optional[str] = None
    align: str = "middle"
    fill: str = "#222"
    size: float = 14.0
    # Stable element ID for diagnostics
    element_id: str = ""

    def bbox(self, char_w: float = 7.0, line_h: float = 16.0) -> BoundingBox:
        w = len(self.text) * char_w
        offset = {"start": 0.0, "middle": -w / 2, "end": -w}.get(self.align, 0.0)
        return BoundingBox(x=self.x + offset, y=self.y - line_h, w=w, h=line_h)


@dataclass
class DiagnosticsData:
    """Emitted when layout diagnostics mode is active.

    Each entry is a (element_id, BoundingBox) pair so the renderer can draw
    coloured outlines and callers can assert no overlaps.
    """
    bounding_boxes: list[tuple[str, BoundingBox]] = field(default_factory=list)
    layout_warnings: list[str] = field(default_factory=list)


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
    diagnostics: Optional[DiagnosticsData] = None


# ──────────────────────────────────────────────────────────────────────────────
# Parse result and force solution
# ──────────────────────────────────────────────────────────────────────────────

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
    # Visual-semantic features — populated by parser, consumed by scene_graph
    visual_features: VisualFeatures = field(default_factory=VisualFeatures)

    def __post_init__(self) -> None:
        if self.missing_required is None:
            self.missing_required = []

    @property
    def is_complete(self) -> bool:
        return self.scenario_type is not None and not self.missing_required


@dataclass
class ForceVector:
    name: str           # normal_force | weight | friction | tension | applied_force
    magnitude_n: float
    direction_deg: float    # 0 = right, 90 = up; counter-clockwise
    anchor: str


@dataclass
class ForceSolution:
    scenario_type: str
    forces: list[ForceVector]
    derived_values: dict[str, float | str | None]
