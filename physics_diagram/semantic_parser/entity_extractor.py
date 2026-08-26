"""Entity extraction module - identifies all physical entities in a problem.

Extracts:
- Objects (blocks, spheres, carts)
- Actors (person, worker, child)
- Surfaces (ground, incline, table, ceiling, wall)
- Connections (already identified as entities)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .semantic_features import Entity

if TYPE_CHECKING:
    from ..schema import ParseResult


# ═══════════════════════════════════════════════════════════════════════════
# ENTITY TYPE MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════

# Map common object names to standardized types
OBJECT_TYPE_MAP = {
    "block": ("block", "rigid_body", "box"),
    "box": ("block", "rigid_body", "box"),
    "crate": ("block", "rigid_body", "box"),
    "cube": ("block", "rigid_body", "box"),
    "ball": ("sphere", "rigid_body", "sphere"),
    "sphere": ("sphere", "rigid_body", "sphere"),
    "mass": ("block", "rigid_body", "box"),  # Generic mass
    "weight": ("block", "rigid_body", "box"),
    "cart": ("cart", "rigid_body", "box"),
    "wagon": ("cart", "rigid_body", "box"),
    "suitcase": ("cart", "rigid_body", "box"),
    "cylinder": ("cylinder", "rigid_body", "cylinder"),
    "wheel": ("wheel", "rigid_body", "cylinder"),
    "disk": ("disk", "rigid_body", "cylinder"),
    "projectile": ("projectile", "rigid_body", "sphere"),
    "stone": ("stone", "rigid_body", "sphere"),
}

ACTOR_KEYWORDS = ["person", "worker", "child", "boy", "girl", "man", "woman", 
                  "cyclist", "driver", "student", "player"]

SURFACE_KEYWORDS = {
    "ground": ("ground", "surface"),
    "floor": ("floor", "surface"),
    "incline": ("incline", "surface"),
    "ramp": ("incline", "surface"),
    "slope": ("incline", "surface"),
    "plane": ("incline", "surface"),
    "table": ("table", "surface"),
    "ceiling": ("ceiling", "surface"),
    "wall": ("wall", "surface"),
    "road": ("road", "surface"),
}

CONNECTION_KEYWORDS = {
    "rope": ("rope", "connection"),
    "string": ("rope", "connection"),
    "cable": ("cable", "connection"),
    "cord": ("rope", "connection"),
    "spring": ("spring", "connection"),
    "rod": ("rod", "connection"),
    "chain": ("chain", "connection"),
    "pulley": ("pulley", "connection"),
}


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def extract_entities(text: str, parse_result: ParseResult) -> list[Entity]:
    """Extract all entities from the problem text.
    
    Strategy:
    1. Start with objects from deterministic parser (explicit entities with mass)
    2. Add actors mentioned in text
    3. Add surfaces (some inferred from scenario, some explicit)
    4. Add connections mentioned in text
    5. Deduplicate and assign IDs
    """
    normalized = text.lower()
    entities: list[Entity] = []
    entity_ids: set[str] = set()
    
    # ── Step 1: Extract objects from ParseResult ────────────────────────────
    for i, obj in enumerate(parse_result.objects, 1):
        obj_label = obj.label or "object"
        obj_type, category, shape = OBJECT_TYPE_MAP.get(obj_label, ("object", "rigid_body", "box"))
        
        entity_id = f"{obj_type}_{i}"
        if entity_id in entity_ids:
            entity_id = f"{obj_type}_{i}_{obj.id}"
        
        entities.append(Entity(
            id=entity_id,
            type=obj_type,
            category=category,
            shape=shape,
            mentioned_explicitly=True,
            confidence=0.95,
        ))
        entity_ids.add(entity_id)
    
    # ── Step 2: Extract actors ───────────────────────────────────────────────
    actor_count = 1
    for actor_kw in ACTOR_KEYWORDS:
        if re.search(rf'\b{actor_kw}\b', normalized):
            entity_id = f"{actor_kw}_{actor_count}"
            if entity_id not in entity_ids:
                entities.append(Entity(
                    id=entity_id,
                    type=actor_kw,
                    category="actor",
                    mentioned_explicitly=True,
                    confidence=0.9,
                ))
                entity_ids.add(entity_id)
                actor_count += 1
    
    # ── Step 3: Extract surfaces ─────────────────────────────────────────────
    # Explicit surfaces from text
    for surface_kw, (surface_type, category) in SURFACE_KEYWORDS.items():
        if re.search(rf'\b{surface_kw}\b', normalized):
            entity_id = f"{surface_type}_1"
            if entity_id not in entity_ids:
                entities.append(Entity(
                    id=entity_id,
                    type=surface_type,
                    category=category,
                    mentioned_explicitly=True,
                    confidence=0.9,
                ))
                entity_ids.add(entity_id)
    
    # Implicit surfaces from scenario type
    scenario = parse_result.scenario_type
    if scenario == "inclined_plane":
        if "incline_1" not in entity_ids:
            entities.append(Entity(
                id="incline_1",
                type="incline",
                category="surface",
                mentioned_explicitly=False,
                confidence=1.0,
            ))
            entity_ids.add("incline_1")
        if "ground_1" not in entity_ids:
            entities.append(Entity(
                id="ground_1",
                type="ground",
                category="surface",
                mentioned_explicitly=False,
                confidence=0.8,
            ))
    elif scenario == "horizontal_friction":
        if "floor_1" not in entity_ids and "ground_1" not in entity_ids:
            entities.append(Entity(
                id="ground_1",
                type="ground",
                category="surface",
                mentioned_explicitly=False,
                confidence=0.9,
            ))
    elif scenario == "atwood_pulley":
        if "ceiling_1" not in entity_ids:
            entities.append(Entity(
                id="ceiling_1",
                type="ceiling",
                category="surface",
                mentioned_explicitly=False,
                confidence=0.8,
            ))
    elif scenario == "projectile_motion":
        if "ground_1" not in entity_ids:
            entities.append(Entity(
                id="ground_1",
                type="ground",
                category="surface",
                mentioned_explicitly=False,
                confidence=0.9,
            ))
    
    # ── Step 4: Extract connections ──────────────────────────────────────────
    conn_count = 1
    for conn_kw, (conn_type, category) in CONNECTION_KEYWORDS.items():
        if re.search(rf'\b{conn_kw}\b', normalized):
            entity_id = f"{conn_type}_{conn_count}"
            if entity_id not in entity_ids:
                entities.append(Entity(
                    id=entity_id,
                    type=conn_type,
                    category=category,
                    mentioned_explicitly=True,
                    confidence=0.9,
                ))
                entity_ids.add(entity_id)
                conn_count += 1
    
    return entities
