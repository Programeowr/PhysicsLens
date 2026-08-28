"""Relation extraction module - identifies spatial and causal relationships.

Extracts:
- Spatial relationships (rests_on, hangs_from, attached_to, touches, above, below)
- Causal relationships (pushes, pulls, supports, constrains)
- Containment relationships (inside, on_top_of)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .semantic_features import Entity, Relation

if TYPE_CHECKING:
    from ..schema import ParseResult


# ═══════════════════════════════════════════════════════════════════════════
# RELATIONSHIP PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

# Regex patterns for extracting relationships
# Format: (pattern, predicate, subject_group, object_group)
RELATION_PATTERNS = [
    # Spatial - resting/contact
    (r'(\w+)\s+rests?\s+on\s+(?:a|an|the)?\s*(\w+)', 'rests_on', 1, 2),
    (r'(\w+)\s+(?:is|are)\s+on\s+(?:a|an|the)?\s*(\w+)', 'rests_on', 1, 2),
    (r'(\w+)\s+placed\s+on\s+(?:a|an|the)?\s*(\w+)', 'rests_on', 1, 2),
    (r'(\w+)\s+sits?\s+on\s+(?:a|an|the)?\s*(\w+)', 'rests_on', 1, 2),
    
    # Spatial - hanging/suspension
    (r'(\w+)\s+hangs?\s+from\s+(?:a|an|the)?\s*(\w+)', 'hangs_from', 1, 2),
    (r'(\w+)\s+suspended\s+(?:by|from)\s+(?:a|an|the)?\s*(\w+)', 'hangs_from', 1, 2),
    (r'(\w+)\s+dangles?\s+from\s+(?:a|an|the)?\s*(\w+)', 'hangs_from', 1, 2),
    
    # Spatial - attachment
    (r'(\w+)\s+attached\s+to\s+(?:a|an|the)?\s*(\w+)', 'attached_to', 1, 2),
    (r'(\w+)\s+connected\s+to\s+(?:a|an|the)?\s*(\w+)', 'connected_to', 1, 2),
    (r'(\w+)\s+fixed\s+to\s+(?:a|an|the)?\s*(\w+)', 'attached_to', 1, 2),
    (r'(\w+)\s+mounted\s+on\s+(?:a|an|the)?\s*(\w+)', 'attached_to', 1, 2),
    
    # Spatial - contact
    (r'(\w+)\s+touches\s+(?:a|an|the)?\s*(\w+)', 'touches', 1, 2),
    (r'(\w+)\s+(?:is\s+)?in\s+contact\s+with\s+(?:a|an|the)?\s*(\w+)', 'touches', 1, 2),
    
    # Spatial - position
    (r'(\w+)\s+(?:is\s+)?above\s+(?:a|an|the)?\s*(\w+)', 'above', 1, 2),
    (r'(\w+)\s+(?:is\s+)?below\s+(?:a|an|the)?\s*(\w+)', 'below', 1, 2),
    (r'(\w+)\s+(?:is\s+)?on\s+top\s+of\s+(?:a|an|the)?\s*(\w+)', 'on_top_of', 1, 2),
    
    # Causal - pushing
    (r'(\w+)\s+push(?:es|ed|ing)\s+(?:a|an|the)?\s*(\w+)', 'pushes', 1, 2),
    (r'(\w+)\s+(?:is\s+)?pushed\s+by\s+(?:a|an|the)?\s*(\w+)', 'pushes', 2, 1),
    
    # Causal - pulling
    (r'(\w+)\s+pull(?:s|ed|ing)\s+(?:a|an|the)?\s*(\w+)', 'pulls', 1, 2),
    (r'(\w+)\s+(?:is\s+)?pulled\s+by\s+(?:a|an|the)?\s*(\w+)', 'pulls', 2, 1),
    (r'(\w+)\s+drags?\s+(?:a|an|the)?\s*(\w+)', 'pulls', 1, 2),
    
    # Causal - supporting
    (r'(\w+)\s+supports?\s+(?:a|an|the)?\s*(\w+)', 'supports', 1, 2),
    (r'(\w+)\s+holds?\s+(?:a|an|the)?\s*(\w+)', 'supports', 1, 2),
]


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _find_entity_by_keyword(keyword: str, entities: list[Entity]) -> str | None:
    """Find entity ID that matches a keyword from text.
    
    Strategy:
    1. Direct type match (keyword == entity.type)
    2. Partial match (keyword in entity.type or entity.type in keyword)
    3. Category match for generic keywords
    """
    keyword = keyword.lower().strip()
    
    # Direct match
    for entity in entities:
        if entity.type == keyword:
            return entity.id
    
    # Partial match
    for entity in entities:
        if keyword in entity.type or entity.type in keyword:
            return entity.id
    
    # Generic keyword mapping
    generic_map = {
        "object": lambda e: e.category == "rigid_body",
        "surface": lambda e: e.category == "surface",
        "incline": lambda e: e.type in {"incline", "ramp", "slope"},
        "plane": lambda e: e.type in {"incline", "ramp", "slope"},
        "ramp": lambda e: e.type in {"incline", "ramp", "slope"},
        "ground": lambda e: e.type in {"ground", "floor"},
        "floor": lambda e: e.type in {"ground", "floor"},
    }
    
    if keyword in generic_map:
        for entity in entities:
            if generic_map[keyword](entity):
                return entity.id
    
    return None


def _infer_scenario_relationships(
    scenario: str | None,
    entities: list[Entity]
) -> list[Relation]:
    """Infer implicit relationships based on scenario type."""
    relations: list[Relation] = []
    
    if scenario == "inclined_plane":
        # Find block/object and incline
        obj_entities = [e for e in entities if e.category == "rigid_body"]
        incline_entities = [e for e in entities if e.type == "incline"]
        ground_entities = [e for e in entities if e.type == "ground"]
        
        if obj_entities and incline_entities:
            relations.append(Relation(
                subject=obj_entities[0].id,
                predicate="rests_on",
                object=incline_entities[0].id,
                confidence=0.9,
            ))
        
        if incline_entities and ground_entities:
            relations.append(Relation(
                subject=incline_entities[0].id,
                predicate="attached_to",
                object=ground_entities[0].id,
                confidence=0.8,
            ))
    
    elif scenario == "horizontal_friction":
        # Object rests on ground
        obj_entities = [e for e in entities if e.category == "rigid_body"]
        ground_entities = [e for e in entities if e.type in {"ground", "floor"}]
        
        if obj_entities and ground_entities:
            relations.append(Relation(
                subject=obj_entities[0].id,
                predicate="rests_on",
                object=ground_entities[0].id,
                confidence=0.9,
            ))
    
    elif scenario == "atwood_pulley":
        # Masses hang from pulley
        obj_entities = [e for e in entities if e.category == "rigid_body"]
        pulley_entities = [e for e in entities if e.type == "pulley"]
        ceiling_entities = [e for e in entities if e.type == "ceiling"]
        
        if pulley_entities:
            for obj in obj_entities:
                relations.append(Relation(
                    subject=obj.id,
                    predicate="hangs_from",
                    object=pulley_entities[0].id,
                    confidence=0.85,
                ))
            
            if ceiling_entities:
                relations.append(Relation(
                    subject=pulley_entities[0].id,
                    predicate="attached_to",
                    object=ceiling_entities[0].id,
                    confidence=0.8,
                ))
    
    elif scenario == "projectile_motion":
        # Projectile above ground (initially)
        obj_entities = [e for e in entities if e.category == "rigid_body"]
        ground_entities = [e for e in entities if e.type == "ground"]
        
        if obj_entities and ground_entities:
            relations.append(Relation(
                subject=obj_entities[0].id,
                predicate="above",
                object=ground_entities[0].id,
                confidence=0.7,
            ))
    
    return relations


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXTRACTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_relations(
    text: str,
    entities: list[Entity],
    parse_result: ParseResult
) -> list[Relation]:
    """Extract all relationships between entities.
    
    Strategy:
    1. Apply regex patterns to find explicit relationships
    2. Infer implicit relationships from scenario type
    3. Deduplicate (keep higher confidence if duplicate)
    """
    normalized = text.lower()
    relations: list[Relation] = []
    seen_relations: set[tuple[str, str, str]] = set()  # (subject, predicate, object)
    
    # ── Step 1: Extract explicit relationships from text ────────────────────
    for pattern, predicate, subj_group, obj_group in RELATION_PATTERNS:
        for match in re.finditer(pattern, normalized):
            subject_keyword = match.group(subj_group)
            object_keyword = match.group(obj_group)
            
            # Find corresponding entities
            subject_id = _find_entity_by_keyword(subject_keyword, entities)
            object_id = _find_entity_by_keyword(object_keyword, entities)
            
            if subject_id and object_id:
                relation_key = (subject_id, predicate, object_id)
                if relation_key not in seen_relations:
                    relations.append(Relation(
                        subject=subject_id,
                        predicate=predicate,
                        object=object_id,
                        confidence=0.9,
                    ))
                    seen_relations.add(relation_key)
    
    # ── Step 2: Infer implicit relationships ────────────────────────────────
    implicit_relations = _infer_scenario_relationships(
        parse_result.scenario_type,
        entities
    )
    
    for relation in implicit_relations:
        relation_key = (relation.subject, relation.predicate, relation.object)
        if relation_key not in seen_relations:
            relations.append(relation)
            seen_relations.add(relation_key)
    
    return relations
