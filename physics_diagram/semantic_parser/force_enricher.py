"""Force enrichment module - adds semantic context to forces.

Enriches forces extracted by deterministic parser with:
- Source entity (who/what applies the force)
- Target entity (what the force acts on)
- Application point (center, edge, contact surface)
- Line of action (parallel_to_incline, perpendicular_to_surface)
- Infers missing forces (gravity, normal, friction)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .semantic_features import EnrichedForce, Entity, Relation

if TYPE_CHECKING:
    from ..schema import ParseResult


# ═══════════════════════════════════════════════════════════════════════════
# FORCE INFERENCE RULES
# ═══════════════════════════════════════════════════════════════════════════

def _infer_gravity_forces(entities: list[Entity], parse_result: ParseResult) -> list[EnrichedForce]:
    """Infer gravity forces for all objects with mass."""
    forces: list[EnrichedForce] = []
    
    for i, obj in enumerate(parse_result.objects, 1):
        if obj.mass_kg is not None:
            # Find corresponding entity
            entity_id = f"block_{i}" if len(entities) > 0 else f"object_{i}"
            for entity in entities:
                if entity.category == "rigid_body":
                    entity_id = entity.id
                    break
            
            forces.append(EnrichedForce(
                id=f"F_gravity_{i}",
                type="gravity",
                source_entity=None,  # Gravity has no source entity
                target_entity=entity_id,
                magnitude_n=obj.mass_kg * 9.8 if obj.mass_kg else None,
                direction="down",
                line_of_action="vertical",
                reference_frame="horizontal",
                is_known=True,
            ))
    
    return forces


def _infer_normal_forces(
    entities: list[Entity],
    relations: list[Relation],
    parse_result: ParseResult
) -> list[EnrichedForce]:
    """Infer normal forces from contact relationships."""
    forces: list[EnrichedForce] = []
    force_id = 1
    
    # Find all "rests_on" or "touches" relationships
    contact_relations = [
        r for r in relations 
        if r.predicate in {"rests_on", "touches"}
    ]
    
    for relation in contact_relations:
        # Normal force acts on the subject, perpendicular to the object surface
        surface_entity = next(
            (e for e in entities if e.id == relation.object),
            None
        )
        
        if surface_entity:
            # Determine line of action based on surface type
            if surface_entity.type == "incline":
                line_of_action = "perpendicular_to_incline"
            else:
                line_of_action = "vertical"
            
            forces.append(EnrichedForce(
                id=f"F_normal_{force_id}",
                type="normal",
                source_entity=relation.object,  # Surface provides normal force
                target_entity=relation.subject,
                application_point="contact_surface",
                line_of_action=line_of_action,
                reference_frame="incline_parallel" if surface_entity.type == "incline" else "horizontal",
                is_known=False,  # Usually calculated
            ))
            force_id += 1
    
    return forces


def _infer_friction_forces(
    entities: list[Entity],
    relations: list[Relation],
    parse_result: ParseResult
) -> list[EnrichedForce]:
    """Infer friction forces from contact + friction coefficient."""
    forces: list[EnrichedForce] = []
    
    if not parse_result.friction or parse_result.mu is None or parse_result.mu == 0:
        return forces
    
    force_id = 1
    contact_relations = [
        r for r in relations 
        if r.predicate in {"rests_on", "touches"}
    ]
    
    for relation in contact_relations:
        surface_entity = next(
            (e for e in entities if e.id == relation.object),
            None
        )
        
        if surface_entity:
            # Friction acts parallel to surface, opposes motion
            if surface_entity.type == "incline":
                line_of_action = "parallel_to_incline"
                direction = "down_incline"  # Opposes motion up incline
            else:
                line_of_action = "horizontal"
                direction = "left"  # Default opposing direction
            
            forces.append(EnrichedForce(
                id=f"F_friction_{force_id}",
                type="friction",
                source_entity=relation.object,
                target_entity=relation.subject,
                application_point="contact_surface",
                line_of_action=line_of_action,
                direction=direction,
                reference_frame="incline_parallel" if surface_entity.type == "incline" else "horizontal",
                is_known=False,
            ))
            force_id += 1
    
    return forces


def _infer_tension_forces(
    entities: list[Entity],
    connections: list,
    parse_result: ParseResult
) -> list[EnrichedForce]:
    """Infer tension forces from rope/string connections."""
    forces: list[EnrichedForce] = []
    
    for conn in connections:
        if conn.type in {"rope", "string", "cable"}:
            # Tension acts on both endpoints, pulling toward the other end
            forces.append(EnrichedForce(
                id=f"F_tension_{conn.from_entity}",
                type="tension",
                source_entity=conn.id,  # Rope provides tension
                target_entity=conn.from_entity,
                line_of_action="along_rope",
                is_known=False,
            ))
            forces.append(EnrichedForce(
                id=f"F_tension_{conn.to_entity}",
                type="tension",
                source_entity=conn.id,
                target_entity=conn.to_entity,
                line_of_action="along_rope",
                is_known=False,
            ))
    
    return forces


def _infer_spring_forces(
    entities: list[Entity],
    connections: list,
    parse_result: ParseResult
) -> list[EnrichedForce]:
    """Infer spring forces from spring connections."""
    forces: list[EnrichedForce] = []
    
    for conn in connections:
        if conn.type == "spring":
            k_spring = conn.properties.get('k_spring')
            
            forces.append(EnrichedForce(
                id=f"F_spring_{conn.from_entity}",
                type="spring",
                source_entity=conn.id,
                target_entity=conn.from_entity,
                line_of_action="along_spring",
                is_known=k_spring is not None,
            ))
    
    return forces


def _enrich_applied_forces(
    applied_forces: list,
    entities: list[Entity],
    relations: list[Relation]
) -> list[EnrichedForce]:
    """Enrich applied forces from ParseResult with source information."""
    enriched: list[EnrichedForce] = []
    
    # Find actor entities (source of applied forces)
    actors = [e for e in entities if e.category == "actor"]
    
    # Find rigid body entities (targets of applied forces)
    targets = [e for e in entities if e.category == "rigid_body"]
    
    for i, force in enumerate(applied_forces, 1):
        # Find source from "pushes" or "pulls" relations
        source_entity = None
        target_entity = targets[0].id if targets else "object_1"
        
        for relation in relations:
            if relation.predicate in {"pushes", "pulls"}:
                source_entity = relation.subject
                target_entity = relation.object
                break
        
        # If no relation found, use first actor if available
        if source_entity is None and actors:
            source_entity = actors[0].id
        
        enriched.append(EnrichedForce(
            id=f"F_applied_{i}",
            type="applied",
            source_entity=source_entity,
            target_entity=target_entity,
            magnitude_n=force.magnitude_n,
            direction=force.direction,
            angle_deg=force.angle_deg,
            reference_frame=force.reference_frame,
            is_known=True,
        ))
    
    return enriched


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENRICHMENT FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def enrich_forces(
    parse_result: ParseResult,
    entities: list[Entity],
    relations: list[Relation],
    connections: list
) -> list[EnrichedForce]:
    """Enrich forces with semantic information and infer missing forces.
    
    Strategy:
    1. Enrich applied forces from ParseResult (add source/target)
    2. Infer gravity forces (always present for objects with mass)
    3. Infer normal forces (from contact relationships)
    4. Infer friction forces (if coefficient given)
    5. Infer tension forces (from rope connections)
    6. Infer spring forces (from spring connections)
    """
    all_forces: list[EnrichedForce] = []
    
    # Step 1: Enrich applied forces
    all_forces.extend(_enrich_applied_forces(
        parse_result.applied_forces,
        entities,
        relations
    ))
    
    # Step 2: Infer gravity
    all_forces.extend(_infer_gravity_forces(entities, parse_result))
    
    # Step 3: Infer normal forces
    all_forces.extend(_infer_normal_forces(entities, relations, parse_result))
    
    # Step 4: Infer friction forces
    all_forces.extend(_infer_friction_forces(entities, relations, parse_result))
    
    # Step 5: Infer tension forces
    all_forces.extend(_infer_tension_forces(entities, connections, parse_result))
    
    # Step 6: Infer spring forces
    all_forces.extend(_infer_spring_forces(entities, connections, parse_result))
    
    return all_forces
