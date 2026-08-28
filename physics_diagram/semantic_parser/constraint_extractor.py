"""Constraint extraction module - identifies physical constraints and idealizations.

Extracts:
- Friction constraints (frictionless, rough, coefficient_given)
- Idealization constraints (massless_rope, ideal_pulley, light_string, rigid_body)
- Motion constraints (no_slipping, rolling_without_slipping, constant_speed)
- Support constraints (fixed_support, pinned, hinged)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .semantic_features import Constraint, Entity

if TYPE_CHECKING:
    from ..schema import ParseResult


# ═══════════════════════════════════════════════════════════════════════════
# CONSTRAINT PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

CONSTRAINT_PATTERNS = {
    # Friction-related
    'frictionless': [
        r'\bfrictionless\b',
        r'\bsmooth\s+(?:surface|incline|plane)\b',
        r'\bno\s+friction\b',
    ],
    'rough': [
        r'\brough\s+(?:surface|incline|plane|floor)\b',
    ],
    
    # Idealization - ropes/strings
    'massless_rope': [
        r'\bmassless\s+(?:rope|string|cable|cord)\b',
    ],
    'light_string': [
        r'\blight\s+(?:rope|string|cable)\b',
    ],
    'inextensible': [
        r'\binextensible\s+(?:rope|string)\b',
        r'\binelastic\s+(?:rope|string)\b',
    ],
    
    # Idealization - pulleys
    'ideal_pulley': [
        r'\bideal\s+pulley\b',
    ],
    'massless_pulley': [
        r'\bmassless\s+pulley\b',
    ],
    'frictionless_pulley': [
        r'\bfrictionless\s+pulley\b',
    ],
    
    # Motion constraints
    'rolling_without_slipping': [
        r'\brolls?\s+without\s+slipping\b',
        r'\bno\s+slipping\b',
    ],
    'constant_speed': [
        r'\bconstant\s+speed\b',
        r'\bconstant\s+velocity\b',
        r'\buniform\s+motion\b',
    ],
    'constant_acceleration': [
        r'\bconstant\s+acceleration\b',
        r'\buniformly\s+accelerating\b',
    ],
    
    # Support/body constraints
    'rigid_body': [
        r'\brigid\s+(?:body|rod|bar)\b',
    ],
    'fixed_support': [
        r'\bfixed\s+(?:support|end|point)\b',
    ],
    'pinned': [
        r'\bpinned\s+(?:at|to)\b',
    ],
    'hinged': [
        r'\bhinged\s+(?:at|to)\b',
    ],
}


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _extract_explicit_constraints(text: str) -> list[Constraint]:
    """Extract constraints explicitly mentioned in text."""
    normalized = text.lower()
    constraints: list[Constraint] = []
    
    for constraint_type, patterns in CONSTRAINT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                # Create a descriptive string
                description = constraint_type.replace('_', ' ').title()
                
                constraints.append(Constraint(
                    entity_id=None,  # Will be assigned later if entity-specific
                    type=constraint_type,
                    description=description,
                ))
                break  # Only add once per constraint type
    
    return constraints


def _infer_constraints_from_parse_result(parse_result: ParseResult) -> list[Constraint]:
    """Infer constraints from ParseResult data."""
    constraints: list[Constraint] = []
    
    # Friction-based constraints
    if not parse_result.friction or parse_result.mu == 0:
        constraints.append(Constraint(
            entity_id=None,
            type="frictionless",
            description="Frictionless surface",
        ))
    elif parse_result.mu is not None and parse_result.mu > 0:
        constraints.append(Constraint(
            entity_id=None,
            type="friction_coefficient_given",
            description=f"Friction coefficient μ = {parse_result.mu}",
        ))
    
    return constraints


def _assign_entity_specific_constraints(
    constraints: list[Constraint],
    entities: list[Entity],
    text: str
) -> list[Constraint]:
    """Assign constraints to specific entities when possible."""
    normalized = text.lower()
    entity_constraints: list[Constraint] = []
    
    for constraint in constraints:
        assigned = False
        
        # Try to assign rope/string constraints to rope entities
        if 'rope' in constraint.type or 'string' in constraint.type:
            rope_entities = [e for e in entities if e.type in {'rope', 'string', 'cable'}]
            for rope in rope_entities:
                entity_constraints.append(Constraint(
                    entity_id=rope.id,
                    type=constraint.type,
                    description=constraint.description,
                ))
                assigned = True
        
        # Try to assign pulley constraints
        elif 'pulley' in constraint.type:
            pulley_entities = [e for e in entities if e.type == 'pulley']
            for pulley in pulley_entities:
                entity_constraints.append(Constraint(
                    entity_id=pulley.id,
                    type=constraint.type,
                    description=constraint.description,
                ))
                assigned = True
        
        # Try to assign surface constraints (frictionless, rough)
        elif constraint.type in {'frictionless', 'rough'}:
            surface_entities = [e for e in entities if e.category == 'surface']
            for surface in surface_entities:
                entity_constraints.append(Constraint(
                    entity_id=surface.id,
                    type=constraint.type,
                    description=constraint.description,
                ))
                assigned = True
        
        # Try to assign motion constraints to rigid bodies
        elif constraint.type in {'rolling_without_slipping', 'constant_speed', 'constant_acceleration'}:
            rigid_bodies = [e for e in entities if e.category == 'rigid_body']
            for body in rigid_bodies:
                entity_constraints.append(Constraint(
                    entity_id=body.id,
                    type=constraint.type,
                    description=constraint.description,
                ))
                assigned = True
        
        # If not assigned to specific entity, keep as global constraint
        if not assigned:
            entity_constraints.append(constraint)
    
    return entity_constraints


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXTRACTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_constraints(
    text: str,
    entities: list[Entity],
    parse_result: ParseResult
) -> list[Constraint]:
    """Extract all physical constraints from the problem.
    
    Strategy:
    1. Extract explicit constraints from text (keywords)
    2. Infer constraints from ParseResult (friction data)
    3. Assign constraints to specific entities when possible
    4. Deduplicate
    """
    all_constraints: list[Constraint] = []
    
    # Step 1: Extract explicit constraints
    all_constraints.extend(_extract_explicit_constraints(text))
    
    # Step 2: Infer from ParseResult
    all_constraints.extend(_infer_constraints_from_parse_result(parse_result))
    
    # Step 3: Assign to entities
    entity_specific = _assign_entity_specific_constraints(
        all_constraints,
        entities,
        text
    )
    
    # Deduplicate based on (entity_id, type)
    seen: set[tuple] = set()
    deduplicated: list[Constraint] = []
    
    for constraint in entity_specific:
        key = (constraint.entity_id, constraint.type)
        if key not in seen:
            deduplicated.append(constraint)
            seen.add(key)
    
    return deduplicated
