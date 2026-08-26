"""Scene Graph Builder - merges ParseResult + SemanticFeatures into SceneGraph.

This module is the integration point between:
- Deterministic parser (quantities, physics data)
- Semantic parser (scene understanding)
- Physics solver (force solutions)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .scene_graph_schema import SceneGraph
from .semantic_parser.semantic_features import SemanticFeatures

if TYPE_CHECKING:
    from .schema import ForceSolution, ParseResult


def build_scene_graph(
    parse_result: ParseResult,
    semantic_features: SemanticFeatures,
    force_solution: ForceSolution | None = None,
) -> SceneGraph:
    """Construct the scene graph from all available data sources.
    
    Algorithm:
    1. Start with entities from semantic parser
    2. Merge physics objects from ParseResult
    3. Build hierarchy (e.g., person→block→incline→ground)
    4. Add all relationships
    5. Integrate force solutions
    6. Validate completeness
    
    Args:
        parse_result: Output from deterministic parser
        semantic_features: Output from semantic parser
        force_solution: Optional physics solution (if problem was solved)
    
    Returns:
        Complete SceneGraph ready for layout and rendering
    """
    
    # ── Step 1: Initialize with metadata ─────────────────────────────────────
    scene = SceneGraph(
        scenario_type=parse_result.scenario_type,
        raw_text=parse_result.raw_text,
    )
    
    # ── Step 2: Add entities ─────────────────────────────────────────────────
    scene.entities = semantic_features.entities
    
    # ── Step 3: Add relationships ────────────────────────────────────────────
    scene.relationships = semantic_features.relations
    
    # ── Step 4: Add connections ──────────────────────────────────────────────
    scene.connections = semantic_features.connections
    
    # ── Step 5: Build hierarchy ──────────────────────────────────────────────
    scene.hierarchy = _build_hierarchy(semantic_features.relations)
    
    # ── Step 6: Add physics data ─────────────────────────────────────────────
    # Masses
    for i, obj in enumerate(parse_result.objects, 1):
        # Find corresponding entity
        entity = None
        for e in scene.entities:
            if e.category == "rigid_body":
                entity = e
                break
        
        if entity and obj.mass_kg is not None:
            scene.masses[entity.id] = obj.mass_kg
    
    # Geometry
    scene.incline_angle_deg = parse_result.geometry.incline_angle_deg
    scene.projectile_angle_deg = parse_result.geometry.projectile_angle_deg
    scene.initial_speed_ms = parse_result.geometry.initial_speed_ms
    
    # ── Step 7: Add forces ───────────────────────────────────────────────────
    scene.forces = semantic_features.enriched_forces
    
    # Add force solutions if available
    if force_solution:
        scene.force_solutions = _extract_force_solutions(force_solution)
    
    # ── Step 8: Add motion states ────────────────────────────────────────────
    for state in semantic_features.states:
        scene.states[state.entity_id] = state
    
    # ── Step 9: Add constraints ──────────────────────────────────────────────
    scene.constraints = semantic_features.constraints
    
    # ── Step 10: Add materials ───────────────────────────────────────────────
    for material in semantic_features.materials:
        scene.materials[material.entity_id] = material
    
    # ── Step 11: Add rendering hints ─────────────────────────────────────────
    scene.render_hints = semantic_features.render_hints
    
    # ── Step 12: Validate and compute confidence ─────────────────────────────
    scene.is_complete = len(parse_result.missing_required) == 0
    scene.missing_data = parse_result.missing_required
    scene.warnings = semantic_features.validation_warnings
    scene.confidence = (
        parse_result.confidence * 0.5 + 
        semantic_features.confidence * 0.5
    )
    
    return scene


def _build_hierarchy(relations: list) -> dict[str, list[str]]:
    """Build entity hierarchy from relationships.
    
    Hierarchy construction rules:
    - Actor (person) → Object (block)
    - Object → Surface (incline, table)
    - Surface → Support (ground, ceiling)
    
    Returns dict mapping parent_id → [child_ids]
    """
    hierarchy: dict[str, list[str]] = {}
    
    # Causal relationships create parent-child (actor pushes object)
    causal_predicates = {"pushes", "pulls", "supports", "holds"}
    
    for relation in relations:
        if relation.predicate in causal_predicates:
            # Subject is parent of object
            if relation.subject not in hierarchy:
                hierarchy[relation.subject] = []
            hierarchy[relation.subject].append(relation.object)
        
        # Spatial relationships create parent-child (object rests_on surface)
        elif relation.predicate in {"rests_on", "hangs_from", "attached_to"}:
            # Object is parent of surface (in scene hierarchy)
            if relation.subject not in hierarchy:
                hierarchy[relation.subject] = []
            hierarchy[relation.subject].append(relation.object)
    
    return hierarchy


def _extract_force_solutions(force_solution: ForceSolution) -> dict[str, float]:
    """Extract force magnitudes from ForceSolution.
    
    Maps force names to their calculated magnitudes.
    """
    solutions: dict[str, float] = {}
    
    # Extract from force_solution.forces list
    if hasattr(force_solution, 'forces'):
        for i, force in enumerate(force_solution.forces, 1):
            if hasattr(force, 'magnitude_n') and force.magnitude_n is not None:
                # Try to match with enriched force IDs
                force_type = getattr(force, 'type', 'unknown')
                force_id = f"F_{force_type}_{i}"
                solutions[force_id] = force.magnitude_n
    
    # Also extract known values
    if hasattr(force_solution, 'normal_force_n'):
        solutions['F_normal'] = force_solution.normal_force_n
    if hasattr(force_solution, 'friction_force_n'):
        solutions['F_friction'] = force_solution.friction_force_n
    if hasattr(force_solution, 'tension_n'):
        solutions['F_tension'] = force_solution.tension_n
    
    return solutions


def merge_scene_graphs(graphs: list[SceneGraph]) -> SceneGraph:
    """Merge multiple scene graphs (for multi-part problems).
    
    This is a utility for future extension when handling problems
    with multiple scenarios or time steps.
    """
    if not graphs:
        return SceneGraph(scenario_type=None)
    
    if len(graphs) == 1:
        return graphs[0]
    
    # Start with first graph
    merged = SceneGraph(
        scenario_type="composite",
        raw_text=" | ".join(g.raw_text for g in graphs),
    )
    
    # Merge entities (with ID disambiguation)
    entity_id_map: dict[str, str] = {}
    for i, graph in enumerate(graphs):
        for entity in graph.entities:
            new_id = f"{entity.id}_scene{i}" if i > 0 else entity.id
            entity_id_map[entity.id] = new_id
            entity.id = new_id
            merged.entities.append(entity)
    
    # Merge other components (update IDs)
    for graph in graphs:
        for rel in graph.relationships:
            rel.subject = entity_id_map.get(rel.subject, rel.subject)
            rel.object = entity_id_map.get(rel.object, rel.object)
            merged.relationships.append(rel)
        
        merged.connections.extend(graph.connections)
        merged.forces.extend(graph.forces)
        merged.constraints.extend(graph.constraints)
    
    return merged
