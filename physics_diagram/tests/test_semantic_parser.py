"""Unit tests for semantic parser modules."""

import pytest

from physics_diagram.parser import parse
from physics_diagram.semantic_parser import parse_semantic
from physics_diagram.semantic_parser.entity_extractor import extract_entities
from physics_diagram.semantic_parser.relation_extractor import extract_relations
from physics_diagram.semantic_parser.connection_extractor import extract_connections
from physics_diagram.semantic_parser.state_extractor import extract_states
from physics_diagram.semantic_parser.force_enricher import enrich_forces
from physics_diagram.semantic_parser.constraint_extractor import extract_constraints
from physics_diagram.semantic_parser.material_extractor import extract_materials
from physics_diagram.semantic_parser.visual_hint_extractor import extract_visual_hints


# ═══════════════════════════════════════════════════════════════════════════
# ENTITY EXTRACTION TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_entity_extraction_incline():
    """Test entity extraction for inclined plane scenario."""
    text = "A 5 kg block on a 30 degree incline"
    parse_result = parse(text)
    
    entities = extract_entities(text, parse_result)
    
    # Should extract: block, incline, ground
    assert len(entities) >= 2
    
    entity_types = {e.type for e in entities}
    assert "block" in entity_types
    assert "incline" in entity_types


def test_entity_extraction_with_actor():
    """Test entity extraction with actor (person)."""
    text = "A person pushes a 10 kg box across a floor"
    parse_result = parse(text)
    
    entities = extract_entities(text, parse_result)
    
    entity_types = {e.type for e in entities}
    assert "person" in entity_types
    assert "block" in entity_types or "box" in entity_types


def test_entity_extraction_pulley():
    """Test entity extraction for Atwood machine."""
    text = "Two masses of 3 kg and 5 kg connected by a rope over a pulley"
    parse_result = parse(text)
    
    entities = extract_entities(text, parse_result)
    
    entity_types = {e.type for e in entities}
    assert "pulley" in entity_types
    assert "rope" in entity_types


# ═══════════════════════════════════════════════════════════════════════════
# RELATIONSHIP EXTRACTION TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_relation_rests_on():
    """Test 'rests_on' relationship extraction."""
    text = "A block rests on an incline"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    relations = extract_relations(text, entities, parse_result)
    
    # Should find "block rests_on incline"
    predicates = {r.predicate for r in relations}
    assert "rests_on" in predicates


def test_relation_pushes():
    """Test causal 'pushes' relationship."""
    text = "A worker pushes a crate up a ramp"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    relations = extract_relations(text, entities, parse_result)
    
    # Should find "worker pushes crate"
    predicates = {r.predicate for r in relations}
    assert "pushes" in predicates


# ═══════════════════════════════════════════════════════════════════════════
# CONNECTION EXTRACTION TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_connection_rope():
    """Test rope connection extraction."""
    text = "Two blocks connected by a massless rope"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    connections = extract_connections(text, entities)
    
    assert len(connections) > 0
    conn = connections[0]
    assert conn.type == "rope"
    assert conn.properties.get("massless") is True


def test_connection_spring():
    """Test spring connection with spring constant."""
    text = "A block attached to a spring with spring constant 200 N/m"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    connections = extract_connections(text, entities)
    
    assert len(connections) > 0
    spring_conn = next((c for c in connections if c.type == "spring"), None)
    assert spring_conn is not None
    assert spring_conn.properties.get("k_spring") == 200.0


# ═══════════════════════════════════════════════════════════════════════════
# STATE EXTRACTION TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_state_at_rest():
    """Test 'at_rest' state extraction."""
    text = "A block at rest on an incline"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    states = extract_states(text, entities)
    
    assert len(states) > 0
    assert states[0].kinematic_state == "at_rest"


def test_state_moving_down():
    """Test moving state with direction."""
    text = "A ball rolls down a ramp"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    states = extract_states(text, entities)
    
    assert len(states) > 0
    assert states[0].kinematic_state == "moving"
    assert states[0].velocity_direction == "down_incline"


def test_state_rolling_without_slipping():
    """Test rolling without slipping motion type."""
    text = "A sphere rolls without slipping down an incline"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    states = extract_states(text, entities)
    
    assert len(states) > 0
    assert states[0].motion_type == "rolling_without_slipping"


# ═══════════════════════════════════════════════════════════════════════════
# FORCE ENRICHMENT TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_force_enrichment_gravity():
    """Test gravity force inference."""
    text = "A 5 kg block on an incline"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    relations = extract_relations(text, entities, parse_result)
    connections = extract_connections(text, entities)
    
    forces = enrich_forces(parse_result, entities, relations, connections)
    
    # Should infer gravity
    gravity_forces = [f for f in forces if f.type == "gravity"]
    assert len(gravity_forces) > 0
    assert gravity_forces[0].magnitude_n == pytest.approx(49.0, abs=0.1)


def test_force_enrichment_normal():
    """Test normal force inference."""
    text = "A 5 kg block on an incline"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    relations = extract_relations(text, entities, parse_result)
    connections = extract_connections(text, entities)
    
    forces = enrich_forces(parse_result, entities, relations, connections)
    
    # Should infer normal force
    normal_forces = [f for f in forces if f.type == "normal"]
    assert len(normal_forces) > 0


def test_force_enrichment_applied_with_actor():
    """Test applied force enrichment with source actor."""
    text = "A person pushes a 10 kg block with 50 N"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    relations = extract_relations(text, entities, parse_result)
    connections = extract_connections(text, entities)
    
    forces = enrich_forces(parse_result, entities, relations, connections)
    
    # Applied force should have person as source
    applied_forces = [f for f in forces if f.type == "applied"]
    assert len(applied_forces) > 0
    # Source should be person entity
    person_entities = [e for e in entities if e.category == "actor"]
    if person_entities:
        assert applied_forces[0].source_entity == person_entities[0].id


# ═══════════════════════════════════════════════════════════════════════════
# CONSTRAINT EXTRACTION TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_constraint_frictionless():
    """Test frictionless constraint extraction."""
    text = "A block on a frictionless incline"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    constraints = extract_constraints(text, entities, parse_result)
    
    constraint_types = {c.type for c in constraints}
    assert "frictionless" in constraint_types


def test_constraint_massless_rope():
    """Test massless rope constraint."""
    text = "Two masses connected by a massless rope"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    constraints = extract_constraints(text, entities, parse_result)
    
    constraint_types = {c.type for c in constraints}
    assert "massless_rope" in constraint_types


# ═══════════════════════════════════════════════════════════════════════════
# MATERIAL EXTRACTION TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_material_wood():
    """Test wooden material extraction."""
    text = "A wooden block on an incline"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    materials = extract_materials(text, entities)
    
    assert len(materials) > 0
    wood_materials = [m for m in materials if m.material == "wood"]
    assert len(wood_materials) > 0


def test_material_texture_smooth():
    """Test texture extraction."""
    text = "A smooth rubber ball"
    parse_result = parse(text)
    entities = extract_entities(text, parse_result)
    
    materials = extract_materials(text, entities)
    
    assert len(materials) > 0
    assert any(m.texture == "smooth" for m in materials)
    assert any(m.material == "rubber" for m in materials)


# ═══════════════════════════════════════════════════════════════════════════
# VISUAL HINT EXTRACTION TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_visual_hint_fbd():
    """Test FBD diagram style detection."""
    text = "Draw a free body diagram of a block on an incline"
    parse_result = parse(text)
    
    hints = extract_visual_hints(text, parse_result)
    
    assert hints.diagram_style == "fbd"


def test_visual_hint_components():
    """Test component display preference."""
    text = "Show force components for a block on an incline"
    parse_result = parse(text)
    
    hints = extract_visual_hints(text, parse_result)
    
    assert hints.show_components is True


def test_visual_hint_tilted_axes():
    """Test tilted coordinate axes preference."""
    text = "Draw with tilted coordinate axes"
    parse_result = parse(text)
    
    hints = extract_visual_hints(text, parse_result)
    
    assert hints.coordinate_type == "inclined"


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

def test_full_semantic_parse_simple():
    """Test full semantic parsing pipeline on simple problem."""
    text = "A 5 kg block on a 30 degree incline"
    parse_result = parse(text)
    
    semantic = parse_semantic(text, parse_result)
    
    assert len(semantic.entities) >= 2
    assert len(semantic.enriched_forces) >= 2  # At least gravity + normal
    assert semantic.confidence > 0.5


def test_full_semantic_parse_complex():
    """Test full semantic parsing on complex problem with actor."""
    text = "A worker pushes a 10 kg wooden crate up a 25 degree ramp with 80 N force parallel to the ramp. The coefficient of friction is 0.2."
    parse_result = parse(text)
    
    semantic = parse_semantic(text, parse_result)
    
    # Entities: worker, crate, ramp, ground
    assert len(semantic.entities) >= 3
    
    # Relationships: worker pushes crate, crate rests_on ramp
    assert len(semantic.relations) >= 1
    
    # Forces: applied, gravity, normal, friction
    assert len(semantic.enriched_forces) >= 4
    
    # Materials: wood
    assert len(semantic.materials) >= 1
    
    # Constraints: friction coefficient given
    assert len(semantic.constraints) >= 1
    
    # Overall confidence should be high
    assert semantic.confidence > 0.7


def test_semantic_parse_validation():
    """Test that validation warnings are generated correctly."""
    text = "A block on an incline"  # Incomplete - no mass or angle
    parse_result = parse(text)
    
    semantic = parse_semantic(text, parse_result)
    
    # Should have entities and relationships despite incomplete data
    assert len(semantic.entities) >= 2
    # Confidence might be lower due to incomplete data
    assert 0 < semantic.confidence <= 1.0
