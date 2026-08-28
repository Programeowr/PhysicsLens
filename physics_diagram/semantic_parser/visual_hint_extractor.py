"""Visual hint extraction module - extracts rendering preferences from text.

Extracts:
- Diagram style (fbd, motion_diagram, components, energy)
- Camera view (side, top, front, isometric)
- Coordinate system preferences (cartesian, inclined, polar)
- Component display preferences
- Label style (symbolic, numeric, mixed)
- Arrow style preferences
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .semantic_features import RenderHints

if TYPE_CHECKING:
    from ..schema import ParseResult


# ═══════════════════════════════════════════════════════════════════════════
# VISUAL HINT PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

DIAGRAM_STYLE_PATTERNS = {
    'fbd': [
        r'\bfree\s+body\s+diagram\b',
        r'\bfbd\b',
        r'\bfree-body\s+diagram\b',
        r'\bforces?\s+on\s+(?:the\s+)?(?:block|object|mass)\b',
    ],
    'motion_diagram': [
        r'\bmotion\s+diagram\b',
        r'\btrajectory\b',
        r'\bpath\s+of\s+(?:the\s+)?(?:projectile|ball|object)\b',
    ],
    'components': [
        r'\bshow\s+components\b',
        r'\bresolve\s+(?:forces?|vectors?)\b',
        r'\bx-component\b',
        r'\by-component\b',
        r'\bforce\s+components\b',
    ],
    'energy': [
        r'\benergy\s+diagram\b',
        r'\benergy\s+bar\s+chart\b',
    ],
}

COORDINATE_PATTERNS = {
    'inclined': [
        r'\btilted\s+(?:coordinate\s+)?axes\b',
        r'\binclined\s+coordinate\s+(?:system|axes)\b',
        r'\bparallel\s+and\s+perpendicular\s+(?:to\s+(?:the\s+)?incline)?\b',
        r'\brotated\s+axes\b',
    ],
    'polar': [
        r'\bpolar\s+coordinates\b',
        r'\bradial\s+and\s+tangential\b',
    ],
}

LABEL_STYLE_PATTERNS = {
    'symbolic': [
        r'\buse\s+symbols\b',
        r'\bsymbolic\b',
        r'\blabel\s+as\s+m\b',  # "label as m, θ, μ"
        # Check for presence of Greek letters or variables
        r'[θμωαβγ]',
        r'\bm\b.*\bθ\b.*\bμ\b',  # m, θ, μ together
    ],
    'numeric': [
        r'\bnumeric\b',
        r'\bactual\s+values\b',
        r'\bshow\s+numbers\b',
    ],
}


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _determine_diagram_style(text: str, parse_result: ParseResult) -> str:
    """Determine preferred diagram style."""
    normalized = text.lower()
    
    # Check explicit requests
    for style, patterns in DIAGRAM_STYLE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                return style
    
    # Default based on scenario
    scenario = parse_result.scenario_type
    if scenario == 'projectile_motion':
        return 'motion_diagram'
    else:
        return 'fbd'  # Default to free body diagram


def _determine_camera_view(text: str, parse_result: ParseResult) -> str:
    """Determine camera view preference."""
    normalized = text.lower()
    
    if re.search(r'\btop\s+view\b', normalized):
        return 'top'
    elif re.search(r'\bfront\s+view\b', normalized):
        return 'front'
    elif re.search(r'\bisometric\b', normalized):
        return 'isometric'
    
    # Default is side view for most physics problems
    return 'side'


def _should_show_coordinate_axes(text: str) -> bool:
    """Check if coordinate axes should be shown."""
    normalized = text.lower()
    
    keywords = [
        r'\bshow\s+(?:coordinate\s+)?axes\b',
        r'\bdraw\s+(?:coordinate\s+)?axes\b',
        r'\binclude\s+(?:coordinate\s+)?axes\b',
        r'\bx-axis\b',
        r'\by-axis\b',
    ]
    
    return any(re.search(kw, normalized) for kw in keywords)


def _determine_coordinate_type(text: str) -> str | None:
    """Determine coordinate system type."""
    normalized = text.lower()
    
    for coord_type, patterns in COORDINATE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                return coord_type
    
    return None  # None means default Cartesian


def _should_show_components(text: str) -> bool:
    """Check if force/vector components should be emphasized."""
    normalized = text.lower()
    
    return bool(
        re.search(r'\bshow\s+components\b', normalized) or
        re.search(r'\bresolve\s+(?:forces?|into\s+components)\b', normalized) or
        re.search(r'\bcomponent\s+form\b', normalized)
    )


def _should_show_angle_markers(text: str) -> bool:
    """Check if angle markers should be shown (default True)."""
    # Angles are shown by default unless explicitly hidden
    return not re.search(r'\bhide\s+angles?\b', text.lower())


def _determine_label_style(text: str, parse_result: ParseResult) -> str:
    """Determine label style (symbolic vs numeric)."""
    normalized = text.lower()
    
    # Check explicit requests
    for style, patterns in LABEL_STYLE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                return style
    
    # Default: numeric if values are known, symbolic otherwise
    if parse_result.missing_required:
        return 'symbolic'  # Incomplete data → use symbols
    else:
        return 'numeric'  # Complete data → use numbers


def _determine_force_arrow_style(text: str) -> str:
    """Determine force arrow visual style."""
    normalized = text.lower()
    
    if re.search(r'\bthick\s+arrows?\b', normalized):
        return 'thick'
    elif re.search(r'\bdashed\s+arrows?\b', normalized):
        return 'dashed'
    
    return 'standard'


def _determine_scaling_preference(text: str) -> str:
    """Determine scaling/sizing preference."""
    normalized = text.lower()
    
    if re.search(r'\bto\s+scale\b', normalized):
        return 'actual_scale'
    elif re.search(r'\bfit\s+(?:to\s+)?width\b', normalized):
        return 'fit_to_width'
    
    return 'auto'


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXTRACTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_visual_hints(text: str, parse_result: ParseResult) -> RenderHints:
    """Extract all visual rendering preferences from the problem.
    
    Strategy:
    1. Check for explicit rendering instructions in text
    2. Use scenario-based defaults when no explicit instruction
    3. Return complete RenderHints object
    """
    
    return RenderHints(
        diagram_style=_determine_diagram_style(text, parse_result),
        camera_view=_determine_camera_view(text, parse_result),
        show_coordinate_axes=_should_show_coordinate_axes(text),
        coordinate_type=_determine_coordinate_type(text),
        show_components=_should_show_components(text),
        show_angle_markers=_should_show_angle_markers(text),
        label_style=_determine_label_style(text, parse_result),
        force_arrow_style=_determine_force_arrow_style(text),
        scaling_preference=_determine_scaling_preference(text),
    )
