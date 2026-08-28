"""Semantic Parser - Extracts scene understanding beyond numerical quantities.

This module enriches the deterministic parser's output with:
- Entities (objects, actors, surfaces, connections)
- Relationships (spatial and causal)
- Motion states
- Force semantics (source, target, application points)
- Physical constraints
- Material properties
- Visual rendering hints

Usage:
    from physics_diagram.parser import parse
    from physics_diagram.semantic_parser import parse_semantic
    
    # Get deterministic parse
    parse_result = parse("A 5 kg block on a 30° incline")
    
    # Enrich with semantic features
    semantic = parse_semantic(text, parse_result)
    
    # Access semantic features
    print(semantic.entities)
    print(semantic.relations)
    print(semantic.enriched_forces)
"""

from .constraint_extractor import extract_constraints
from .connection_extractor import extract_connections
from .entity_extractor import extract_entities
from .force_enricher import enrich_forces
from .material_extractor import extract_materials
from .relation_extractor import extract_relations
from .semantic_features import (
    Connection,
    Constraint,
    EnrichedForce,
    Entity,
    EntityState,
    MaterialInfo,
    Relation,
    RenderHints,
    SemanticFeatures,
)
from .state_extractor import extract_states
from .visual_hint_extractor import extract_visual_hints

__all__ = [
    # Main function
    "parse_semantic",
    # Data structures
    "SemanticFeatures",
    "Entity",
    "Relation",
    "Connection",
    "EntityState",
    "EnrichedForce",
    "Constraint",
    "MaterialInfo",
    "RenderHints",
    # Individual extractors (for advanced usage)
    "extract_entities",
    "extract_relations",
    "extract_connections",
    "extract_states",
    "enrich_forces",
    "extract_constraints",
    "extract_materials",
    "extract_visual_hints",
]


def parse_semantic(text: str, parse_result) -> SemanticFeatures:
    """Parse semantic features from a physics problem.
    
    This is the main entry point for semantic parsing. It orchestrates all
    extraction modules to produce a complete SemanticFeatures object.
    
    Args:
        text: The original problem text
        parse_result: ParseResult from the deterministic parser
    
    Returns:
        SemanticFeatures containing all extracted semantic information
    
    Example:
        >>> from physics_diagram.parser import parse
        >>> from physics_diagram.semantic_parser import parse_semantic
        >>> 
        >>> text = "A 5 kg wooden block is pushed up a 30° ramp by a person."
        >>> parse_result = parse(text)
        >>> semantic = parse_semantic(text, parse_result)
        >>> 
        >>> # Access entities
        >>> print(f"Found {len(semantic.entities)} entities")
        >>> for entity in semantic.entities:
        ...     print(f"  - {entity.type} ({entity.category})")
        >>> 
        >>> # Access relationships
        >>> for rel in semantic.relations:
        ...     print(f"  {rel.subject} {rel.predicate} {rel.object}")
    """
    
    # Step 1: Extract entities
    entities = extract_entities(text, parse_result)
    
    # Step 2: Extract relationships (depends on entities)
    relations = extract_relations(text, entities, parse_result)
    
    # Step 3: Extract connections (depends on entities)
    connections = extract_connections(text, entities)
    
    # Step 4: Extract motion states (depends on entities)
    states = extract_states(text, entities)
    
    # Step 5: Enrich forces (depends on entities, relations, connections)
    enriched_forces = enrich_forces(parse_result, entities, relations, connections)
    
    # Step 6: Extract constraints (depends on entities)
    constraints = extract_constraints(text, entities, parse_result)
    
    # Step 7: Extract materials (depends on entities)
    materials = extract_materials(text, entities)
    
    # Step 8: Extract visual hints
    render_hints = extract_visual_hints(text, parse_result)
    
    # Construct and return SemanticFeatures
    return SemanticFeatures(
        entities=entities,
        relations=relations,
        connections=connections,
        states=states,
        enriched_forces=enriched_forces,
        constraints=constraints,
        materials=materials,
        render_hints=render_hints,
        extraction_method="rule_based",
        confidence=_calculate_confidence(
            entities, relations, connections, states, 
            enriched_forces, constraints, materials
        ),
        validation_warnings=_validate_semantic_features(
            entities, relations, connections, enriched_forces
        ),
    )


def _calculate_confidence(
    entities: list[Entity],
    relations: list[Relation],
    connections: list[Connection],
    states: list[EntityState],
    forces: list[EnrichedForce],
    constraints: list[Constraint],
    materials: list[MaterialInfo],
) -> float:
    """Calculate overall confidence score for semantic extraction.
    
    Confidence is based on:
    - Number of explicit vs inferred entities
    - Number of explicit vs inferred relationships
    - Completeness of force enrichment
    """
    total_weight = 0.0
    confidence_sum = 0.0
    
    # Entity confidence (weight: 0.3)
    if entities:
        entity_conf = sum(e.confidence for e in entities) / len(entities)
        confidence_sum += entity_conf * 0.3
        total_weight += 0.3
    
    # Relation confidence (weight: 0.2)
    if relations:
        relation_conf = sum(r.confidence for r in relations) / len(relations)
        confidence_sum += relation_conf * 0.2
        total_weight += 0.2
    
    # Force enrichment completeness (weight: 0.3)
    if forces:
        # Higher confidence if sources/targets are assigned
        enriched_count = sum(1 for f in forces if f.source_entity or f.target_entity)
        force_conf = enriched_count / len(forces)
        confidence_sum += force_conf * 0.3
        total_weight += 0.3
    
    # State extraction (weight: 0.1)
    if states:
        confidence_sum += 0.9 * 0.1  # States are fairly reliable
        total_weight += 0.1
    
    # Material extraction (weight: 0.1)
    if materials:
        confidence_sum += 0.8 * 0.1
        total_weight += 0.1
    
    if total_weight > 0:
        return confidence_sum / total_weight
    else:
        return 0.5  # Neutral confidence if no features extracted


def _validate_semantic_features(
    entities: list[Entity],
    relations: list[Relation],
    connections: list[Connection],
    forces: list[EnrichedForce],
) -> list[str]:
    """Validate semantic features and return warnings.
    
    Checks:
    - All referenced entity IDs exist
    - Relationships reference valid entities
    - Forces reference valid entities
    - No orphaned entities (no relationships)
    """
    warnings: list[str] = []
    entity_ids = {e.id for e in entities}
    
    # Check relationship references
    for relation in relations:
        if relation.subject not in entity_ids:
            warnings.append(f"Relation references unknown subject: {relation.subject}")
        if relation.object not in entity_ids:
            warnings.append(f"Relation references unknown object: {relation.object}")
    
    # Check connection references
    for conn in connections:
        if conn.from_entity not in entity_ids:
            warnings.append(f"Connection references unknown from_entity: {conn.from_entity}")
        if conn.to_entity not in entity_ids:
            warnings.append(f"Connection references unknown to_entity: {conn.to_entity}")
    
    # Check force references
    for force in forces:
        if force.source_entity and force.source_entity not in entity_ids:
            warnings.append(f"Force {force.id} references unknown source: {force.source_entity}")
        if force.target_entity and force.target_entity not in entity_ids:
            warnings.append(f"Force {force.id} references unknown target: {force.target_entity}")
    
    # Check for orphaned entities (rigid bodies with no relationships)
    rigid_bodies = [e for e in entities if e.category == "rigid_body"]
    for entity in rigid_bodies:
        has_relation = any(
            r.subject == entity.id or r.object == entity.id 
            for r in relations
        )
        if not has_relation and len(rigid_bodies) > 1:
            warnings.append(f"Entity {entity.id} has no relationships")
    
    return warnings
