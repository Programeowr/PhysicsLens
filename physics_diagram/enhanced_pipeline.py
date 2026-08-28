"""Enhanced Pipeline - Integrates semantic parsing layer with existing pipeline.

This module provides the full pipeline with semantic enrichment:
    Text → Deterministic Parser → Semantic Parser → Scene Graph → Solver → Renderer

The original pipeline (pipeline.py) remains unchanged for backward compatibility.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .parser import parse
from .physics_engine import solve
from .scene_graph_builder import build_scene_graph
from .semantic_parser import parse_semantic
from .validation import validate

logger = logging.getLogger(__name__)


def solve_and_render_enhanced(
    text: str,
    output_path: str | Path | None = None,
    parser: str = "deterministic",
) -> dict:
    """Enhanced pipeline with semantic parsing.
    
    Pipeline stages:
    1. Deterministic parsing (quantities extraction)
    2. Semantic parsing (scene understanding)
    3. Scene graph construction (merge all data)
    4. Validation
    5. Physics solving (if complete)
    6. Rendering (using scene graph)
    
    Args:
        text: Physics problem text
        output_path: Optional path to save SVG
        parser: "deterministic" or "llm" (for stage 1)
    
    Returns:
        dict with keys:
            - status: "success", "needs_clarification", "unsupported_scenario", "error"
            - scene_graph: SceneGraph object
            - svg: SVG string (if successful)
            - message: Human-readable message
            - missing_required: List of missing fields (if needs_clarification)
            - semantic_confidence: Confidence score from semantic parser
            - warnings: List of validation warnings
    """
    
    try:
        # ── Stage 1: Deterministic Parsing ───────────────────────────────────
        logger.info(f"Stage 1: Parsing with {parser} parser")
        
        if parser == "llm":
            # Use LLM parser if requested
            try:
                from .llm_parser import parse_with_llm
                parse_result = parse_with_llm(text)
                parser_used = "llm"
            except Exception as e:
                logger.warning(f"LLM parser failed: {e}, falling back to deterministic")
                parse_result = parse(text)
                parser_used = "deterministic"
        else:
            parse_result = parse(text)
            parser_used = "deterministic"
        
        logger.info(f"Parsed as {parse_result.scenario_type} (confidence: {parse_result.confidence:.2f})")
        
        # ── Stage 2: Semantic Parsing ────────────────────────────────────────
        logger.info("Stage 2: Semantic parsing")
        semantic_features = parse_semantic(text, parse_result)
        
        logger.info(
            f"Extracted: {len(semantic_features.entities)} entities, "
            f"{len(semantic_features.relations)} relations, "
            f"{len(semantic_features.enriched_forces)} forces"
        )
        
        # ── Stage 3: Scene Graph Construction ────────────────────────────────
        logger.info("Stage 3: Building scene graph")
        scene_graph = build_scene_graph(parse_result, semantic_features)
        
        # ── Stage 4: Validation ──────────────────────────────────────────────
        logger.info("Stage 4: Validation")
        validation_result = validate(parse_result)
        
        if validation_result["status"] == "needs_clarification":
            logger.warning(f"Incomplete parse: {validation_result['missing_required']}")
            return {
                "status": "needs_clarification",
                "message": validation_result["message"],
                "missing_required": validation_result["missing_required"],
                "scene_graph": scene_graph,
                "parser_used": parser_used,
                "semantic_confidence": semantic_features.confidence,
                "warnings": scene_graph.warnings,
            }
        
        # ── Stage 5: Physics Solving ─────────────────────────────────────────
        logger.info("Stage 5: Solving physics")
        
        try:
            force_solution = solve(parse_result)
            
            # Re-build scene graph with solutions
            scene_graph = build_scene_graph(parse_result, semantic_features, force_solution)
            
            logger.info("Physics solved successfully")
        except NotImplementedError as e:
            logger.warning(f"Solver not implemented: {e}")
            return {
                "status": "unsupported_scenario",
                "message": str(e),
                "scene_graph": scene_graph,
                "parser_used": parser_used,
                "semantic_confidence": semantic_features.confidence,
            }
        
        # ── Stage 6: Rendering (TODO: Use scene graph) ──────────────────────
        # For now, use existing rendering pipeline
        # Future: Implement scene-graph-based renderer
        logger.info("Stage 6: Rendering")
        
        from .renderer import render
        
        svg = render(parse_result, force_solution)
        
        # Save to file if requested
        if output_path:
            output_path = Path(output_path)
            output_path.write_text(svg, encoding="utf-8")
            logger.info(f"Saved SVG to {output_path}")
        
        return {
            "status": "success",
            "svg": svg,
            "scene_graph": scene_graph,
            "force_solution": force_solution,
            "parser_used": parser_used,
            "semantic_confidence": semantic_features.confidence,
            "warnings": scene_graph.warnings,
            "message": f"Solved {parse_result.scenario_type} problem successfully",
        }
    
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "error_type": type(e).__name__,
        }


def parse_and_build_scene_graph(
    text: str,
    parser: str = "deterministic",
) -> tuple[dict, object, object]:
    """Parse text and build scene graph without solving or rendering.
    
    Useful for:
    - Testing semantic parser
    - Inspecting scene graph
    - Building UI/visualization tools
    
    Args:
        text: Physics problem text
        parser: "deterministic" or "llm"
    
    Returns:
        Tuple of (parse_result, semantic_features, scene_graph)
    """
    
    # Stage 1: Deterministic parsing
    if parser == "llm":
        try:
            from .llm_parser import parse_with_llm
            parse_result = parse_with_llm(text)
        except Exception:
            parse_result = parse(text)
    else:
        parse_result = parse(text)
    
    # Stage 2: Semantic parsing
    semantic_features = parse_semantic(text, parse_result)
    
    # Stage 3: Scene graph
    scene_graph = build_scene_graph(parse_result, semantic_features)
    
    return parse_result, semantic_features, scene_graph


def inspect_semantic_features(text: str) -> dict:
    """Inspect semantic features extracted from text (for debugging).
    
    Returns a dict with human-readable representation of all semantic features.
    """
    
    parse_result = parse(text)
    semantic = parse_semantic(text, parse_result)
    
    return {
        "text": text,
        "scenario": parse_result.scenario_type,
        "entities": [
            {
                "id": e.id,
                "type": e.type,
                "category": e.category,
                "material": e.material,
                "confidence": e.confidence,
            }
            for e in semantic.entities
        ],
        "relationships": [
            {
                "subject": r.subject,
                "predicate": r.predicate,
                "object": r.object,
                "confidence": r.confidence,
            }
            for r in semantic.relations
        ],
        "connections": [
            {
                "id": c.id,
                "type": c.type,
                "from": c.from_entity,
                "to": c.to_entity,
                "properties": c.properties,
            }
            for c in semantic.connections
        ],
        "states": [
            {
                "entity": s.entity_id,
                "state": s.kinematic_state,
                "velocity_dir": s.velocity_direction,
                "motion_type": s.motion_type,
            }
            for s in semantic.states
        ],
        "forces": [
            {
                "id": f.id,
                "type": f.type,
                "source": f.source_entity,
                "target": f.target_entity,
                "magnitude": f.magnitude_n,
            }
            for f in semantic.enriched_forces
        ],
        "constraints": [
            {
                "entity": c.entity_id,
                "type": c.type,
                "description": c.description,
            }
            for c in semantic.constraints
        ],
        "materials": [
            {
                "entity": m.entity_id,
                "material": m.material,
                "texture": m.texture,
            }
            for m in semantic.materials
        ],
        "render_hints": {
            "diagram_style": semantic.render_hints.diagram_style,
            "camera_view": semantic.render_hints.camera_view,
            "show_axes": semantic.render_hints.show_coordinate_axes,
            "coordinate_type": semantic.render_hints.coordinate_type,
            "label_style": semantic.render_hints.label_style,
        },
        "confidence": semantic.confidence,
        "warnings": semantic.validation_warnings,
    }
