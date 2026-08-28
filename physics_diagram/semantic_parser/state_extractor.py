"""State extraction module - determines motion and kinematic state of entities.

Extracts:
- Kinematic state (at_rest, moving, accelerating, rotating, suspended)
- Velocity direction (up_incline, down_incline, left, right, up, down)
- Angular motion (clockwise, counterclockwise)
- Motion type (sliding, rolling, rolling_without_slipping)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .semantic_features import Entity, EntityState

if TYPE_CHECKING:
    pass


# ═══════════════════════════════════════════════════════════════════════════
# STATE KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════

KINEMATIC_STATE_KEYWORDS = {
    'at_rest': [
        r'\bat rest\b',
        r'\bstationary\b',
        r'\bequilibrium\b',
        r'\bremains at rest\b',
        r'\bheld in place\b',
        r'\bstatic\b',
        r'\bnot moving\b',
    ],
    'moving': [
        r'\bmoving\b',
        r'\btravels?\b',
        r'\bgoes\b',
        r'\bslides?\b',
        r'\bsliding\b',
        r'\bmoves?\b',
    ],
    'accelerating': [
        r'\baccelerating\b',
        r'\bspeeding up\b',
        r'\bslowing down\b',
        r'\bdecelerating\b',
    ],
    'suspended': [
        r'\bhangs?\b',
        r'\bhanging\b',
        r'\bsuspended\b',
        r'\bdangles?\b',
    ],
    'rotating': [
        r'\brotating\b',
        r'\bspinning\b',
        r'\bturning\b',
        r'\brevolving\b',
    ],
}

VELOCITY_DIRECTION_KEYWORDS = {
    'up_incline': [
        r'\bup\s+(?:the\s+)?(?:incline|ramp|slope|plane)\b',
        r'\bupward\s+along\s+(?:the\s+)?(?:incline|ramp)\b',
    ],
    'down_incline': [
        r'\bdown\s+(?:the\s+)?(?:incline|ramp|slope|plane)\b',
        r'\bslides?\s+down\b',
        r'\brolls?\s+down\b',
    ],
    'right': [
        r'\bto\s+the\s+right\b',
        r'\brightward\b',
        r'\beast\b',
    ],
    'left': [
        r'\bto\s+the\s+left\b',
        r'\bleftward\b',
        r'\bwest\b',
    ],
    'up': [
        r'\bupward\b',
        r'\bup\b(?!\s+(?:incline|ramp))',  # "up" but not "up incline"
        r'\bvertically\s+up\b',
    ],
    'down': [
        r'\bdownward\b',
        r'\bdown\b(?!\s+(?:incline|ramp))',
        r'\bfalls?\b',
        r'\bfalling\b',
    ],
}

MOTION_TYPE_KEYWORDS = {
    'rolling_without_slipping': [
        r'\brolls?\s+without\s+slipping\b',
        r'\brolling\s+without\s+slipping\b',
        r'\bno\s+slipping\b',
    ],
    'rolling': [
        r'\brolls?\b',
        r'\brolling\b',
    ],
    'sliding': [
        r'\bslides?\b',
        r'\bsliding\b',
    ],
}


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _determine_kinematic_state(text: str) -> str:
    """Determine overall kinematic state from text."""
    normalized = text.lower()
    
    # Check each state (order matters - specific before general)
    for state, patterns in KINEMATIC_STATE_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                return state
    
    # Default: if no explicit state mentioned, assume at_rest
    # unless projectile/launch keywords present
    if any(kw in normalized for kw in ['throw', 'thrown', 'launch', 'launched', 'fire', 'fired']):
        return 'moving'
    
    return 'at_rest'


def _determine_velocity_direction(text: str) -> str | None:
    """Determine velocity direction from text."""
    normalized = text.lower()
    
    for direction, patterns in VELOCITY_DIRECTION_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                return direction
    
    return None


def _determine_motion_type(text: str) -> str | None:
    """Determine specific motion type (rolling, sliding, etc)."""
    normalized = text.lower()
    
    # Check specific motion types (order matters)
    for motion_type, patterns in MOTION_TYPE_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                return motion_type
    
    return None


def _determine_angular_motion(text: str) -> str | None:
    """Determine angular motion direction if mentioned."""
    normalized = text.lower()
    
    if re.search(r'\bclockwise\b', normalized):
        return 'clockwise'
    elif re.search(r'\bcounterclockwise\b|\banti-clockwise\b', normalized):
        return 'counterclockwise'
    
    return None


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXTRACTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_states(text: str, entities: list[Entity]) -> list[EntityState]:
    """Extract motion states for all entities.
    
    Strategy:
    1. Determine global kinematic state (applies to main object(s))
    2. Extract velocity direction if moving
    3. Extract motion type (rolling, sliding, etc)
    4. Extract angular motion if rotating
    5. Assign states to appropriate entities
    """
    states: list[EntityState] = []
    
    # Determine global state properties
    kinematic_state = _determine_kinematic_state(text)
    velocity_direction = _determine_velocity_direction(text)
    motion_type = _determine_motion_type(text)
    angular_motion = _determine_angular_motion(text)
    
    # Assign states to rigid body entities (primary actors in physics problems)
    rigid_bodies = [e for e in entities if e.category == "rigid_body"]
    
    for entity in rigid_bodies:
        # Override state for hanging masses
        if entity.type in {'mass', 'weight'} and any(
            e.type == 'pulley' for e in entities
        ):
            entity_state = 'suspended'
        else:
            entity_state = kinematic_state
        
        states.append(EntityState(
            entity_id=entity.id,
            kinematic_state=entity_state,  # type: ignore
            velocity_direction=velocity_direction,
            angular_motion=angular_motion,
            motion_type=motion_type,
        ))
    
    return states
