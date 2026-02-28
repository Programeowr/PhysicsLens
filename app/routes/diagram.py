"""
Diagram routes — generates SVG free body diagrams from parsed physics data.
"""

import logging

from fastapi import APIRouter, HTTPException, Response

from app.models import ParsedPhysicsProblem, SurfaceType
from app.diagrams.incline import generate_incline_diagram
from app.diagrams.horizontal import generate_horizontal_diagram
from app.diagrams.pulley import generate_pulley_diagram
from app.diagrams.vertical import generate_vertical_diagram

logger = logging.getLogger(__name__)

router = APIRouter()


def route_to_diagram(data: ParsedPhysicsProblem) -> str:
    """Auto-detect diagram type from parsed data and generate the SVG."""
    if data.has_pulley():
        return generate_pulley_diagram(data)

    surface_type = data.get_primary_surface_type()

    if surface_type == SurfaceType.inclined_plane:
        return generate_incline_diagram(data)
    elif surface_type == SurfaceType.vertical_wall:
        return generate_vertical_diagram(data)
    elif surface_type == SurfaceType.elevator_floor:
        return generate_vertical_diagram(data)
    elif surface_type == SurfaceType.horizontal_surface:
        return generate_horizontal_diagram(data)
    else:
        # Default fallback to horizontal
        return generate_horizontal_diagram(data)


@router.post("/diagram")
async def create_diagram(data: dict):
    """
    Generate an SVG free body diagram from parsed physics data.

    Accepts the parsed physics problem JSON (from /parse endpoint)
    and returns an SVG image.
    """
    try:
        # Validate input against our model
        parsed_data = data.get("data", data)
        problem = ParsedPhysicsProblem.model_validate(parsed_data)
        svg = route_to_diagram(problem)
        return Response(content=svg, media_type="image/svg+xml")
    except Exception as e:
        logger.error(f"Diagram generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": f"Diagram generation failed: {e}"},
        )


@router.get("/test-diagram")
async def test_diagram():
    """Render a sample inclined plane FBD for quick testing."""
    sample = ParsedPhysicsProblem.model_validate({
        "objects": [{"id": "block_1", "type": "block", "mass": 5}],
        "surfaces": [{"id": "incline_1", "type": "inclined_plane", "angle": 30}],
        "placements": [{"object_id": "block_1", "surface_id": "incline_1"}],
        "forces": [
            {"type": "applied", "magnitude": 20, "direction": "up_along_plane", "object_id": "block_1"},
            {"type": "gravity", "magnitude": 49.0, "direction": "vertical_down", "object_id": "block_1"},
            {"type": "normal", "magnitude": None, "direction": "perpendicular_to_surface", "object_id": "block_1"},
        ],
        "friction": {"object_id": "block_1", "coefficient": 0.2},
        "constants": {"gravity": 9.8},
    })

    svg = generate_incline_diagram(sample)
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/test-diagram/horizontal")
async def test_horizontal():
    """Render a sample horizontal surface FBD."""
    sample = ParsedPhysicsProblem.model_validate({
        "objects": [{"id": "box_1", "type": "block", "mass": 10}],
        "surfaces": [{"id": "floor_1", "type": "horizontal_surface"}],
        "placements": [{"object_id": "box_1", "surface_id": "floor_1"}],
        "forces": [
            {"type": "gravity", "magnitude": 98.0, "direction": "vertical_down", "object_id": "box_1"},
            {"type": "normal", "magnitude": None, "direction": "up", "object_id": "box_1"},
            {"type": "applied", "magnitude": 50, "direction": "right", "object_id": "box_1"},
            {"type": "friction_force", "magnitude": None, "direction": "left", "object_id": "box_1"},
        ],
        "friction": {"object_id": "box_1", "coefficient": 0.3},
        "constants": {"gravity": 9.8},
    })

    svg = generate_horizontal_diagram(sample)
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/test-diagram/pulley")
async def test_pulley():
    """Render a sample Atwood machine FBD."""
    sample = ParsedPhysicsProblem.model_validate({
        "objects": [
            {"id": "mass_1", "type": "block", "mass": 3},
            {"id": "mass_2", "type": "block", "mass": 5},
            {"id": "string_1", "type": "rope"},
        ],
        "surfaces": [{"id": "pulley_1", "type": "pulley"}],
        "placements": [
            {"object_id": "mass_1", "surface_id": "pulley_1"},
            {"object_id": "mass_2", "surface_id": "pulley_1"},
        ],
        "forces": [
            {"type": "gravity", "magnitude": 29.4, "direction": "vertical_down", "object_id": "mass_1"},
            {"type": "tension", "magnitude": None, "direction": "vertical_up", "object_id": "mass_1"},
            {"type": "gravity", "magnitude": 49.0, "direction": "vertical_down", "object_id": "mass_2"},
            {"type": "tension", "magnitude": None, "direction": "vertical_up", "object_id": "mass_2"},
        ],
        "constants": {"gravity": 9.8},
    })

    svg = generate_pulley_diagram(sample)
    return Response(content=svg, media_type="image/svg+xml")


@router.get("/test-diagram/vertical")
async def test_vertical():
    """Render a sample elevator FBD."""
    sample = ParsedPhysicsProblem.model_validate({
        "objects": [{"id": "person_1", "type": "body", "mass": 60}],
        "surfaces": [{"id": "elevator_floor", "type": "elevator_floor"}],
        "placements": [{"object_id": "person_1", "surface_id": "elevator_floor"}],
        "forces": [
            {"type": "gravity", "magnitude": 588.0, "direction": "vertical_down", "object_id": "person_1"},
            {"type": "normal", "magnitude": None, "direction": "vertical_up", "object_id": "person_1"},
        ],
        "acceleration": {"magnitude": 2, "direction": "vertical_up", "object_id": "person_1"},
        "constants": {"gravity": 9.8},
    })

    svg = generate_vertical_diagram(sample)
    return Response(content=svg, media_type="image/svg+xml")
