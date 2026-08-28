"""Tests for the three-layer architecture separation.

Validates that Physics, Scene, and Render features are properly separated.
"""

import pytest

from physics_diagram.unified_parser import parse_unified


def test_inclined_plane_separation():
    """Test that inclined plane problem separates features correctly."""
    text = "A 5 kg block is placed on a frictionless incline of 30 degrees."
    result = parse_unified(text)
    
    # ═══ PHYSICS FEATURES ═══
    assert result.physics.scenario_type == "inclined_plane"
    assert result.physics.confidence > 0
    assert len(result.physics.objects) == 1
    assert result.physics.objects[0].mass_kg == 5.0
    assert result.physics.geometry.incline_angle_deg == 30.0
    assert result.physics.friction.type == "frictionless"
    assert result.physics.friction.coefficient == 0.0
    assert result.physics.is_complete
    
    # Physics features should NOT contain rendering info
    assert not hasattr(result.physics, "camera")
    assert not hasattr(result.physics, "diagram_style")
    assert not hasattr(result.physics, "canvas_width")
    
    # ═══ SCENE FEATURES ═══
    assert len(result.scene.objects) == 1
    assert result.scene.objects[0].type == "block"
    assert result.scene.objects[0].shape == "box"
    assert result.scene.objects[0].current_state == "at_rest"
    
    # Should have incline surface
    assert len(result.scene.surfaces) == 1
    assert result.scene.surfaces[0].type == "incline"
    assert result.scene.surfaces[0].angle_deg == 30.0
    
    # Should have relationship: block rests_on incline
    assert len(result.scene.relationships) >= 1
    rel = result.scene.relationships[0]
    assert rel.subject == result.scene.objects[0].id
    assert rel.predicate == "rests_on"
    assert rel.object == "incline_surface"
    
    # Should have frictionless constraint
    assert len(result.scene.constraints) >= 1
    assert result.scene.constraints[0].type == "frictionless"
    
    # Scene features should NOT contain physics calculations
    assert not hasattr(result.scene, "forces")
    assert not hasattr(result.scene, "acceleration")
    
    # ═══ RENDER FEATURES ═══
    assert result.render.camera.type == "side"
    assert result.render.diagram_style.type in {"fbd", "scene_and_fbd"}
    assert result.render.label_config.show_object_labels
    assert result.render.label_config.show_force_labels
    assert result.render.title != ""
    assert result.render.canvas_width > 0
    assert result.render.canvas_height > 0
    
    # Render features should NOT contain physics or scene structure
    assert not hasattr(result.render, "mass_kg")
    assert not hasattr(result.render, "objects")
    assert not hasattr(result.render, "scenario_type")


def test_horizontal_friction_with_angle():
    """Test suitcase pulled at an angle — all three layers."""
    text = "A 20 kg suitcase is pulled using a 100 N force making an angle of 30° above the horizontal."
    result = parse_unified(text)
    
    # ═══ PHYSICS FEATURES ═══
    assert result.physics.scenario_type == "horizontal_friction"
    assert len(result.physics.objects) == 1
    assert result.physics.objects[0].mass_kg == 20.0
    
    # Applied force with angle
    assert len(result.physics.applied_forces) == 1
    force = result.physics.applied_forces[0]
    assert force.magnitude_n == 100.0
    assert force.angle_deg == 30.0
    assert force.reference_frame == "horizontal"
    
    # ═══ SCENE FEATURES ═══
    assert len(result.scene.objects) == 1
    assert result.scene.objects[0].type in {"cart", "block"}  # suitcase → cart or block
    
    # Should have ground surface
    assert len(result.scene.surfaces) == 1
    assert result.scene.surfaces[0].type in {"ground", "floor"}
    
    # Should have contact
    assert len(result.scene.contacts) >= 1
    
    # ═══ RENDER FEATURES ═══
    assert result.render.camera.type == "side"
    assert result.render.diagram_style.type == "fbd"
    assert "Horizontal" in result.render.title or "Friction" in result.render.title


def test_atwood_pulley_relationships():
    """Test that Atwood pulley creates proper scene relationships."""
    text = "Two masses of 3 kg and 5 kg are connected by a rope over a pulley."
    result = parse_unified(text)
    
    # ═══ PHYSICS FEATURES ═══
    assert result.physics.scenario_type == "atwood_pulley"
    assert len(result.physics.objects) == 2
    assert result.physics.objects[0].mass_kg == 3.0
    assert result.physics.objects[1].mass_kg == 5.0
    
    # ═══ SCENE FEATURES ═══
    assert len(result.scene.objects) == 2
    
    # Should have pulley support surface
    assert any(s.type in {"ceiling", "support"} for s in result.scene.surfaces)
    
    # Should have pulley connection between objects
    assert len(result.scene.connections) >= 1
    conn = result.scene.connections[0]
    assert conn.type == "pulley"
    assert conn.from_object in {result.scene.objects[0].id, result.scene.objects[1].id}
    assert conn.to_object in {result.scene.objects[0].id, result.scene.objects[1].id}
    
    # ═══ RENDER FEATURES ═══
    assert result.render.diagram_style.type == "fbd"
    assert "Atwood" in result.render.title or "Pulley" in result.render.title


def test_independence_physics_scene():
    """Verify physics and scene features are truly independent."""
    text = "A 10 kg block on a 45 degree incline with coefficient of friction 0.2"
    result = parse_unified(text)
    
    # Physics should only contain computation inputs
    physics_keys = {k for k in dir(result.physics) if not k.startswith("_")}
    assert "scenario_type" in physics_keys
    assert "objects" in physics_keys
    assert "geometry" in physics_keys
    assert "friction" in physics_keys
    
    # These rendering concepts should NOT be in physics
    assert "camera" not in physics_keys
    assert "diagram_style" not in physics_keys
    assert "canvas_width" not in physics_keys
    
    # Scene should only contain structure
    scene_keys = {k for k in dir(result.scene) if not k.startswith("_")}
    assert "objects" in scene_keys
    assert "surfaces" in scene_keys
    assert "relationships" in scene_keys
    
    # These physics concepts should NOT be in scene
    assert "scenario_type" not in scene_keys
    assert "geometry" not in scene_keys
    assert "applied_forces" not in scene_keys
    
    # Render should only contain visualization
    render_keys = {k for k in dir(result.render) if not k.startswith("_")}
    assert "camera" in render_keys
    assert "diagram_style" in render_keys
    assert "label_config" in render_keys
    
    # These physics/scene concepts should NOT be in render
    assert "objects" not in render_keys  # render has alignments, not objects
    assert "scenario_type" not in render_keys
    assert "mass_kg" not in render_keys


def test_scene_graph_completeness():
    """Verify scene graph contains enough info to render without original text."""
    text = "A 7 kg box is pushed up a 25° incline by a 100 N force parallel to the incline. The surface is rough with μ = 0.15."
    result = parse_unified(text)
    
    # Scene should be self-contained
    scene = result.scene
    
    # Should have objects
    assert len(scene.objects) >= 1
    obj = scene.objects[0]
    assert obj.id != ""
    assert obj.type != ""
    assert obj.shape != ""
    
    # Should have surfaces with angle
    assert len(scene.surfaces) >= 1
    surface = scene.surfaces[0]
    assert surface.type == "incline"
    assert surface.angle_deg == 25.0
    
    # Should have relationships showing object-surface contact
    assert len(scene.relationships) >= 1
    
    # Should NOT have frictionless constraint (μ=0.15 means friction present)
    frictionless_constraints = [c for c in scene.constraints if c.type == "frictionless"]
    assert len(frictionless_constraints) == 0
    
    # A renderer should be able to rebuild this scene from scene features alone
    # without looking at physics or render


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
