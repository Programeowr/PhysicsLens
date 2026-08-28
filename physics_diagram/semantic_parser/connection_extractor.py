"""Connection extraction module - identifies mechanical connections.

Extracts:
- Ropes, strings, cables, cords
- Springs
- Rods, chains
- Pulleys (as connection facilitators)
- Connection properties (length, massless, ideal, spring constant)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .semantic_features import Connection, Entity

if TYPE_CHECKING:
    pass


# ═══════════════════════════════════════════════════════════════════════════
# CONNECTION PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

CONNECTION_PATTERNS = [
    # Rope/string connections
    (r'connected\s+by\s+(?:a|an)?\s*(rope|string|cable|cord)', 'rope'),
    (r'(rope|string|cable|cord)\s+connects?\s+', 'rope'),
    (r'tied\s+(?:to|with)\s+(?:a|an)?\s*(rope|string)', 'rope'),
    (r'hung?\s+(?:from|by)\s+(?:a|an)?\s*(rope|string|cable)', 'rope'),
    
    # Spring connections
    (r'attached\s+to\s+(?:a|an)?\s*spring', 'spring'),
    (r'spring\s+connects?', 'spring'),
    (r'connected\s+by\s+(?:a|an)?\s*spring', 'spring'),
    
    # Rod connections
    (r'connected\s+by\s+(?:a|an)?\s*rod', 'rod'),
    (r'rigid\s+rod', 'rod'),
    
    # Chain connections
    (r'connected\s+by\s+(?:a|an)?\s*chain', 'chain'),
    (r'chain\s+connects?', 'chain'),
    
    # Over pulley
    (r'over\s+(?:a|an)?\s*pulley', 'pulley'),
    (r'through\s+(?:a|an)?\s*pulley', 'pulley'),
    (r'via\s+(?:a|an)?\s*pulley', 'pulley'),
]

# Property extraction patterns
PROPERTY_PATTERNS = {
    'length_m': r'([\d.]+)\s*(?:m|meter|metre)s?\s+(?:long\s+)?(?:rope|string|cable|rod|chain)',
    'massless': r'massless\s+(?:rope|string|cable|rod)',
    'light': r'light\s+(?:rope|string|pulley)',
    'inextensible': r'inextensible\s+(?:rope|string)',
    'k_spring': r'spring\s+constant\s+(?:k\s*=\s*)?([\d.]+)\s*(?:N/m)?',
    'ideal_pulley': r'ideal\s+pulley',
    'frictionless_pulley': r'frictionless\s+pulley',
}


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _extract_connection_properties(text: str, conn_type: str) -> dict:
    """Extract properties for a specific connection."""
    normalized = text.lower()
    properties: dict = {}
    
    # Length
    if conn_type in {'rope', 'rod', 'chain', 'cable'}:
        length_match = re.search(PROPERTY_PATTERNS['length_m'], normalized)
        if length_match:
            try:
                properties['length_m'] = float(length_match.group(1))
            except (ValueError, IndexError):
                pass
    
    # Massless/light
    if re.search(PROPERTY_PATTERNS['massless'], normalized):
        properties['massless'] = True
    if re.search(PROPERTY_PATTERNS['light'], normalized):
        properties['light'] = True
        properties['massless'] = True  # "light" implies massless
    
    # Inextensible
    if conn_type in {'rope', 'string'}:
        if re.search(PROPERTY_PATTERNS['inextensible'], normalized):
            properties['inextensible'] = True
    
    # Spring constant
    if conn_type == 'spring':
        k_match = re.search(PROPERTY_PATTERNS['k_spring'], normalized)
        if k_match:
            try:
                properties['k_spring'] = float(k_match.group(1))
            except (ValueError, IndexError):
                pass
    
    # Pulley properties
    if conn_type == 'pulley':
        if re.search(PROPERTY_PATTERNS['ideal_pulley'], normalized):
            properties['ideal'] = True
            properties['massless'] = True
            properties['frictionless'] = True
        elif re.search(PROPERTY_PATTERNS['frictionless_pulley'], normalized):
            properties['frictionless'] = True
    
    return properties


def _find_connection_endpoints(
    text: str,
    conn_keyword: str,
    entities: list[Entity]
) -> tuple[str | None, str | None]:
    """Try to identify which entities are connected.
    
    Strategy:
    1. Look for "A connected to B by rope" pattern
    2. For pulleys, look for objects on either side
    3. For springs, look for "attached to X" pattern
    4. Fall back to first two rigid_body entities
    """
    normalized = text.lower()
    
    # Pattern: "A connected to B by/with connection"
    connect_pattern = r'(\w+)\s+connected\s+to\s+(\w+)\s+(?:by|with|via)\s+' + conn_keyword
    match = re.search(connect_pattern, normalized)
    if match:
        entity1_kw = match.group(1)
        entity2_kw = match.group(2)
        
        # Find entities
        entity1 = next((e.id for e in entities if e.type == entity1_kw or entity1_kw in e.type), None)
        entity2 = next((e.id for e in entities if e.type == entity2_kw or entity2_kw in e.type), None)
        
        if entity1 and entity2:
            return entity1, entity2
    
    # Pattern for springs: "block attached to spring" + "spring attached to wall"
    if conn_keyword == 'spring':
        attach_pattern = r'(\w+)\s+attached\s+to\s+(?:a|an)?\s*spring'
        matches = list(re.finditer(attach_pattern, normalized))
        if matches:
            entity_kw = matches[0].group(1)
            entity1 = next((e.id for e in entities if e.type == entity_kw or entity_kw in e.type), None)
            # Check if spring is attached to wall/ceiling
            wall_entity = next((e.id for e in entities if e.type in {'wall', 'ceiling', 'support'}), None)
            if entity1:
                return entity1, wall_entity
    
    # Fall back: connect first two rigid_body entities
    rigid_bodies = [e for e in entities if e.category == "rigid_body"]
    if len(rigid_bodies) >= 2:
        return rigid_bodies[0].id, rigid_bodies[1].id
    elif len(rigid_bodies) == 1:
        # One object connected to a surface/support
        surface = next((e.id for e in entities if e.category == "surface"), None)
        if surface:
            return rigid_bodies[0].id, surface
    
    return None, None


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXTRACTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_connections(text: str, entities: list[Entity]) -> list[Connection]:
    """Extract all mechanical connections from the problem.
    
    Strategy:
    1. Search for connection keywords (rope, spring, pulley, etc.)
    2. Extract properties for each connection
    3. Identify endpoints (which entities are connected)
    4. Handle special case: Atwood machines (implied rope over pulley)
    """
    normalized = text.lower()
    connections: list[Connection] = []
    conn_id_counter = 1
    seen_types: set[str] = set()
    
    # ── Step 1: Extract explicit connections ────────────────────────────────
    for pattern, conn_type in CONNECTION_PATTERNS:
        if re.search(pattern, normalized) and conn_type not in seen_types:
            # Extract properties
            properties = _extract_connection_properties(text, conn_type)
            
            # Find endpoints
            from_entity, to_entity = _find_connection_endpoints(text, conn_type, entities)
            
            if from_entity and to_entity:
                connections.append(Connection(
                    id=f"{conn_type}_{conn_id_counter}",
                    type=conn_type,
                    from_entity=from_entity,
                    to_entity=to_entity,
                    properties=properties,
                ))
                conn_id_counter += 1
                seen_types.add(conn_type)
    
    # ── Step 2: Infer connections for Atwood machines ───────────────────────
    # If we have a pulley entity but no rope, infer rope connection
    pulley_entities = [e for e in entities if e.type == "pulley"]
    if pulley_entities and 'rope' not in seen_types:
        rigid_bodies = [e for e in entities if e.category == "rigid_body"]
        if len(rigid_bodies) >= 2:
            # Atwood machine: two masses connected by rope over pulley
            connections.append(Connection(
                id=f"rope_{conn_id_counter}",
                type="rope",
                from_entity=rigid_bodies[0].id,
                to_entity=rigid_bodies[1].id,
                properties={"massless": True, "inextensible": True, "via_pulley": pulley_entities[0].id},
            ))
    
    return connections
