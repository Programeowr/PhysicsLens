"""Category 3: Render Features — How to visualize the scene.

These features are ONLY used by the renderer. They must never affect physics
calculations. They describe camera angles, styles, labels, and layout preferences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CameraView:
    """Camera/viewing perspective."""
    type: str = "side"  # side | top | front | isometric | perspective | cross_section
    zoom: float = 1.0
    focus_object: Optional[str] = None  # object ID to center on
    rotation_deg: float = 0.0


@dataclass
class DiagramStyle:
    """Overall diagram presentation style."""
    type: str = "fbd"  # fbd | scene_and_fbd | motion_diagram | energy_diagram | components | textbook | simplified
    show_grid: bool = False
    show_axes: bool = False
    show_dimensions: bool = False
    show_scale: bool = False
    emphasize_components: bool = False
    style_preset: str = "clean"  # clean | technical | educational | sketch


@dataclass
class LabelConfig:
    """Which labels to show and how."""
    show_object_labels: bool = True
    show_force_labels: bool = True
    show_angle_labels: bool = True
    show_distance_labels: bool = False
    show_velocity_labels: bool = False
    show_acceleration_labels: bool = False
    show_mass_labels: bool = True
    show_coefficient_labels: bool = True
    
    label_style: str = "symbolic"  # symbolic | numeric | both | mixed
    
    # Specific label requests
    required_labels: list[str] = field(default_factory=list)  # ["m", "F", "N", "T", "θ", "μ", "v", "a", "mg"]


@dataclass
class ForceVisualization:
    """How to draw a specific force arrow."""
    force_id: str
    name: str
    magnitude_n: float
    direction_deg: float
    anchor_object: str
    
    # Rendering properties
    arrow_scale: float = 1.0  # scaling factor for arrow length
    arrow_priority: int = 0  # higher priority drawn on top
    arrow_color: str = "#333"
    arrow_style: str = "solid"  # solid | dashed | dotted
    show_components: bool = False
    show_magnitude_label: bool = True
    label_offset_x: float = 0.0
    label_offset_y: float = 0.0
    line_width: float = 2.0


@dataclass
class AngleMarker:
    """Where to draw angle arcs."""
    object_id: str
    angle_deg: float
    label: str  # "θ", "α", "30°", "φ"
    arc_radius: float = 20.0
    position: str = "auto"  # auto | top_left | top_right | bottom_left | bottom_right
    color: str = "#666"
    show_arc: bool = True
    show_label: bool = True


@dataclass
class CoordinateAxes:
    """Coordinate system to draw."""
    type: str = "cartesian"  # cartesian | inclined | radial_tangential | none
    origin_object: Optional[str] = None  # object ID to anchor axes to
    rotation_deg: float = 0.0  # for inclined axes
    show_x_axis: bool = True
    show_y_axis: bool = True
    show_x_label: bool = True
    show_y_label: bool = True
    axis_length: float = 100.0
    axis_color: str = "#888"
    axis_style: str = "arrow"  # arrow | line | dashed


@dataclass
class ObjectAlignment:
    """How objects should be positioned relative to each other."""
    object_id: str
    alignment_type: str  # centered_on | hanging_from | touching | aligned_with | above | below | left_of | right_of
    reference: str  # surface ID, connection ID, or other object ID
    offset_x: float = 0.0
    offset_y: float = 0.0


@dataclass
class LayoutPreferences:
    """General layout and spacing preferences."""
    minimum_object_spacing: float = 40.0
    minimum_force_spacing: float = 30.0
    minimum_label_spacing: float = 15.0
    preferred_object_scale: float = 1.0
    label_offset: float = 20.0
    collision_avoidance: bool = True
    auto_arrange: bool = True
    z_order: dict = field(default_factory=dict)  # object_id -> z_index
    
    # Alignment preferences
    object_alignment_preference: str = "centered"  # centered | left | right | top | bottom
    force_arrow_placement: str = "from_center"  # from_center | from_edge | from_contact_point
    angle_marker_placement: str = "optimal"  # optimal | inside | outside


@dataclass
class SVGComponent:
    """Reusable SVG component specification."""
    type: str  # Ground | InclinedPlane | Block | Sphere | Cylinder | Wheel | Spring | Pulley | Wall | Person | Rope | Arrow | AngleMarker | Label | CoordinateAxes | DimensionLine
    object_id: str
    properties: dict = field(default_factory=dict)  # width, height, color, texture, rotation, etc.
    z_index: int = 0


@dataclass
class RenderingHint:
    """Additional rendering hints for specific elements."""
    element_id: str
    hint_type: str  # scaling | positioning | styling | visibility
    value: any = None
    description: str = ""


@dataclass
class RenderFeatures:
    """Complete rendering specification — input to renderer only.
    
    This contains NO physics and NO scene structure, only visualization preferences.
    """
    # View and style
    camera: CameraView = field(default_factory=CameraView)
    diagram_style: DiagramStyle = field(default_factory=DiagramStyle)
    
    # Labels and annotations
    label_config: LabelConfig = field(default_factory=LabelConfig)
    angle_markers: list[AngleMarker] = field(default_factory=list)
    
    # Force visualization
    force_visualizations: list[ForceVisualization] = field(default_factory=list)
    
    # Coordinate system
    coordinate_axes: Optional[CoordinateAxes] = None
    
    # Layout
    object_alignments: list[ObjectAlignment] = field(default_factory=list)
    layout_preferences: LayoutPreferences = field(default_factory=LayoutPreferences)
    
    # SVG components to use
    svg_components: list[SVGComponent] = field(default_factory=list)
    
    # Additional rendering hints
    rendering_hints: list[RenderingHint] = field(default_factory=list)
    
    # Canvas
    canvas_width: float = 900.0
    canvas_height: float = 620.0
    canvas_background: str = "white"
    canvas_padding: float = 40.0
    
    # Title and metadata
    title: str = ""
    subtitle: str = ""
    show_title: bool = True
    show_subtitle: bool = False
    
    # Color scheme
    color_scheme: str = "default"  # default | monochrome | high_contrast | colorblind_friendly
    
    def predict_required_components(self) -> list[str]:
        """Predict which SVG components will be needed based on the scene."""
        components = []
        for svg_comp in self.svg_components:
            if svg_comp.type not in components:
                components.append(svg_comp.type)
        return components
