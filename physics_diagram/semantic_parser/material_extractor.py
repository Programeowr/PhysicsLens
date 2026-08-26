"""Material extraction module - identifies materials and textures.

Extracts:
- Material (wood, metal, rubber, concrete, ice, steel, etc.)
- Texture (smooth, rough, polished)
- Density hint (heavy, light)
- Color hint (rare in physics problems, but possible)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .semantic_features import Entity, MaterialInfo

if TYPE_CHECKING:
    pass


# ═══════════════════════════════════════════════════════════════════════════
# MATERIAL KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════

MATERIAL_KEYWORDS = {
    'wood': ['wood', 'wooden', 'timber', 'plank'],
    'metal': ['metal', 'metallic', 'iron', 'aluminum', 'aluminium'],
    'steel': ['steel'],
    'rubber': ['rubber'],
    'plastic': ['plastic'],
    'concrete': ['concrete', 'cement'],
    'ice': ['ice', 'icy'],
    'glass': ['glass'],
    'stone': ['stone', 'rock'],
    'brick': ['brick'],
    'rope': ['rope', 'string', 'cord'],
    'fabric': ['fabric', 'cloth'],
}

TEXTURE_KEYWORDS = {
    'smooth': ['smooth', 'polished', 'slippery'],
    'rough': ['rough', 'coarse', 'textured'],
    'slippery': ['slippery'],
}

DENSITY_KEYWORDS = {
    'heavy': ['heavy', 'massive', 'dense'],
    'light': ['light', 'lightweight'],
}

COLOR_KEYWORDS = [
    'red', 'blue', 'green', 'yellow', 'black', 'white',
    'brown', 'gray', 'grey', 'orange', 'purple'
]


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _extract_material_for_entity(text: str, entity: Entity) -> str | None:
    """Extract material for a specific entity.
    
    Strategy:
    1. Look for "wooden block", "metal sphere" patterns near entity name
    2. Check entity.material if already set
    3. Look for material keywords near entity type
    """
    normalized = text.lower()
    
    # If entity already has material (from entity extractor), use it
    if entity.material:
        return entity.material
    
    # Build pattern: "material entity_type" or "entity_type made of material"
    entity_pattern = rf'(?:^|\s)(\w+)\s+{entity.type}\b'
    for match in re.finditer(entity_pattern, normalized):
        material_word = match.group(1)
        for material, keywords in MATERIAL_KEYWORDS.items():
            if material_word in keywords:
                return material
    
    # Pattern: "entity_type made of material"
    made_of_pattern = rf'{entity.type}\s+made\s+of\s+(\w+)'
    match = re.search(made_of_pattern, normalized)
    if match:
        material_word = match.group(1)
        for material, keywords in MATERIAL_KEYWORDS.items():
            if material_word in keywords:
                return material
    
    # Default materials based on entity type
    default_materials = {
        'rope': 'rope',
        'string': 'rope',
        'cable': 'metal',
        'spring': 'steel',
        'rod': 'metal',
        'chain': 'metal',
    }
    
    return default_materials.get(entity.type, None)


def _extract_texture_for_entity(text: str, entity: Entity) -> str | None:
    """Extract texture/surface quality for entity."""
    normalized = text.lower()
    
    # Look for texture keywords near entity
    for texture, keywords in TEXTURE_KEYWORDS.items():
        for keyword in keywords:
            # Pattern: "smooth block" or "block with smooth surface"
            pattern = rf'(?:{keyword}\s+{entity.type}|{entity.type}\s+(?:with\s+)?{keyword})'
            if re.search(pattern, normalized):
                return texture
    
    # For surfaces specifically, check general surface descriptions
    if entity.category == 'surface':
        for texture, keywords in TEXTURE_KEYWORDS.items():
            for keyword in keywords:
                if re.search(rf'\b{keyword}\s+(?:surface|incline|plane|floor)\b', normalized):
                    return texture
    
    return None


def _extract_density_hint(text: str, entity: Entity) -> str | None:
    """Extract density hint (heavy/light) for entity."""
    normalized = text.lower()
    
    for density, keywords in DENSITY_KEYWORDS.items():
        for keyword in keywords:
            pattern = rf'(?:{keyword}\s+{entity.type}|{entity.type}.*{keyword})'
            if re.search(pattern, normalized):
                return density
    
    return None


def _extract_color_hint(text: str, entity: Entity) -> str | None:
    """Extract color if mentioned (rare in physics)."""
    normalized = text.lower()
    
    for color in COLOR_KEYWORDS:
        pattern = rf'(?:{color}\s+{entity.type}|{entity.type}.*{color})'
        if re.search(pattern, normalized):
            return color
    
    return None


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXTRACTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_materials(text: str, entities: list[Entity]) -> list[MaterialInfo]:
    """Extract material information for all entities.
    
    Strategy:
    1. For each entity, extract material, texture, density, color
    2. Only create MaterialInfo if at least one property found
    3. Prioritize explicit mentions over defaults
    """
    materials: list[MaterialInfo] = []
    
    for entity in entities:
        material = _extract_material_for_entity(text, entity)
        texture = _extract_texture_for_entity(text, entity)
        density_hint = _extract_density_hint(text, entity)
        color_hint = _extract_color_hint(text, entity)
        
        # Only create MaterialInfo if we found something
        if any([material, texture, density_hint, color_hint]):
            materials.append(MaterialInfo(
                entity_id=entity.id,
                material=material or "generic",
                texture=texture,
                density_hint=density_hint,
                color_hint=color_hint,
            ))
    
    return materials
