"""
AI prompt templates with few-shot examples for physics problem parsing.

The prompt uses 4 real NCERT/JEE-style examples covering:
1. Block on inclined plane with friction
2. Block on horizontal surface with applied force
3. Atwood machine (pulley system)
4. Object in an elevator (vertical scenario)
"""

FEW_SHOT_EXAMPLES = """
### Example 1 — Inclined Plane
Problem: "A 5 kg block slides down a smooth inclined plane of angle 30 degrees."
Output:
{
  "objects": [{"id": "block_1", "type": "block", "mass": 5}],
  "surfaces": [{"id": "incline_1", "type": "inclined_plane", "angle": 30, "friction_coefficient": null}],
  "placements": [{"object_id": "block_1", "surface_id": "incline_1"}],
  "forces": [
    {"type": "gravity", "magnitude": 49.0, "direction": "vertical_down", "object_id": "block_1"},
    {"type": "normal", "magnitude": null, "direction": "perpendicular_to_surface", "object_id": "block_1"}
  ],
  "friction": null,
  "constants": {"gravity": 9.8}
}

### Example 2 — Horizontal Surface with Friction
Problem: "A 10 kg box is pushed with a force of 50 N to the right on a rough horizontal surface. The coefficient of friction is 0.3."
Output:
{
  "objects": [{"id": "box_1", "type": "block", "mass": 10}],
  "surfaces": [{"id": "floor_1", "type": "horizontal_surface", "angle": null, "friction_coefficient": 0.3}],
  "placements": [{"object_id": "box_1", "surface_id": "floor_1"}],
  "forces": [
    {"type": "gravity", "magnitude": 98.0, "direction": "vertical_down", "object_id": "box_1"},
    {"type": "normal", "magnitude": null, "direction": "up", "object_id": "box_1"},
    {"type": "applied", "magnitude": 50, "direction": "right", "object_id": "box_1"},
    {"type": "friction_force", "magnitude": null, "direction": "left", "object_id": "box_1"}
  ],
  "friction": {"object_id": "box_1", "coefficient": 0.3},
  "constants": {"gravity": 9.8}
}

### Example 3 — Atwood Machine (Pulley)
Problem: "Two masses of 3 kg and 5 kg are connected by a light string passing over a frictionless pulley."
Output:
{
  "objects": [
    {"id": "mass_1", "type": "block", "mass": 3},
    {"id": "mass_2", "type": "block", "mass": 5},
    {"id": "string_1", "type": "rope", "mass": null}
  ],
  "surfaces": [{"id": "pulley_1", "type": "pulley", "angle": null, "friction_coefficient": null}],
  "placements": [
    {"object_id": "mass_1", "surface_id": "pulley_1"},
    {"object_id": "mass_2", "surface_id": "pulley_1"}
  ],
  "forces": [
    {"type": "gravity", "magnitude": 29.4, "direction": "vertical_down", "object_id": "mass_1"},
    {"type": "tension", "magnitude": null, "direction": "vertical_up", "object_id": "mass_1"},
    {"type": "gravity", "magnitude": 49.0, "direction": "vertical_down", "object_id": "mass_2"},
    {"type": "tension", "magnitude": null, "direction": "vertical_up", "object_id": "mass_2"}
  ],
  "friction": null,
  "constants": {"gravity": 9.8}
}

### Example 4 — Elevator (Vertical Scenario)
Problem: "A person of mass 60 kg stands on a weighing scale in an elevator that accelerates upward at 2 m/s²."
Output:
{
  "objects": [{"id": "person_1", "type": "body", "mass": 60}],
  "surfaces": [{"id": "elevator_floor", "type": "horizontal_surface", "angle": null, "friction_coefficient": null}],
  "placements": [{"object_id": "person_1", "surface_id": "elevator_floor"}],
  "forces": [
    {"type": "gravity", "magnitude": 588.0, "direction": "vertical_down", "object_id": "person_1"},
    {"type": "normal", "magnitude": null, "direction": "vertical_up", "object_id": "person_1"}
  ],
  "friction": null,
  "constants": {"gravity": 9.8}
}

### Example 5 — Connected Blocks
Problem: "Two blocks of masses 4 kg and 6 kg are connected by a string on a frictionless horizontal surface. A force of 30 N is applied to the 6 kg block."
Output:
{
  "objects": [
    {"id": "block_1", "type": "block", "mass": 4},
    {"id": "block_2", "type": "block", "mass": 6},
    {"id": "string_1", "type": "rope", "mass": null}
  ],
  "surfaces": [{"id": "floor_1", "type": "horizontal_surface", "angle": null, "friction_coefficient": null}],
  "placements": [
    {"object_id": "block_1", "surface_id": "floor_1"},
    {"object_id": "block_2", "surface_id": "floor_1"}
  ],
  "forces": [
    {"type": "gravity", "magnitude": 39.2, "direction": "vertical_down", "object_id": "block_1"},
    {"type": "normal", "magnitude": null, "direction": "vertical_up", "object_id": "block_1"},
    {"type": "tension", "magnitude": null, "direction": "right", "object_id": "block_1"},
    {"type": "gravity", "magnitude": 58.8, "direction": "vertical_down", "object_id": "block_2"},
    {"type": "normal", "magnitude": null, "direction": "vertical_up", "object_id": "block_2"},
    {"type": "tension", "magnitude": null, "direction": "left", "object_id": "block_2"},
    {"type": "applied", "magnitude": 30, "direction": "right", "object_id": "block_2"}
  ],
  "friction": null,
  "constants": {"gravity": 9.8}
}

### Example 6 — Spring-Mass System
Problem: "A 2 kg block is attached to a horizontal spring with spring constant 200 N/m on a frictionless surface. The spring is compressed by 0.1 m."
Output:
{
  "objects": [
    {"id": "block_1", "type": "block", "mass": 2},
    {"id": "spring_1", "type": "spring_obj", "mass": null}
  ],
  "surfaces": [{"id": "floor_1", "type": "horizontal_surface", "angle": null, "friction_coefficient": null}],
  "placements": [{"object_id": "block_1", "surface_id": "floor_1"}],
  "forces": [
    {"type": "gravity", "magnitude": 19.6, "direction": "vertical_down", "object_id": "block_1"},
    {"type": "normal", "magnitude": null, "direction": "vertical_up", "object_id": "block_1"},
    {"type": "spring", "magnitude": 20, "direction": "right", "object_id": "block_1"}
  ],
  "friction": null,
  "constants": {"gravity": 9.8}
}
"""


def build_prompt(problem_text: str) -> str:
    """Build the full prompt with few-shot examples for Gemini."""
    return f"""You are a physics semantic parser specializing in Newton's Laws problems.

Extract all physical entities from the given problem and return STRICTLY valid JSON.

## JSON Schema

{{
  "objects": [
    {{
      "id": "string (unique identifier, e.g. block_1, mass_a)",
      "type": "block | sphere | body | cart | rope | pulley_wheel | wedge | spring_obj",
      "mass": number or null (kg)
    }}
  ],
  "surfaces": [
    {{
      "id": "string (unique identifier)",
      "type": "horizontal_surface | inclined_plane | vertical_wall | pulley | circular_path | fluid_surface",
      "angle": number or null (degrees, for inclined planes),
      "friction_coefficient": number or null
    }}
  ],
  "placements": [
    {{
      "object_id": "string (must match an object id)",
      "surface_id": "string (must match a surface id)"
    }}
  ],
  "forces": [
    {{
      "type": "applied | gravity | normal | tension | spring | friction_force | buoyancy | centripetal_force | drag",
      "magnitude": number or null (Newtons),
      "direction": "up | down | left | right | up_along_plane | down_along_plane | vertical_down | vertical_up | perpendicular_to_surface | centripetal | tangential | radially_outward",
      "object_id": "string (must match an object id)"
    }}
  ],
  "friction": {{
    "object_id": "string",
    "coefficient": number or null
  }} or null,
  "constants": {{
    "gravity": 9.8
  }}
}}

## Rules
- Always include gravity for each object with mass.
- Always include normal force for objects resting on surfaces.
- If friction is mentioned, add both a friction entry AND a friction_force in forces.
- For pulleys, add tension forces on each connected mass.
- Calculate gravity magnitude as mass × 9.8 when mass is given.
- Use only the allowed enum values for type and direction.
- All object_id and surface_id references must match existing entries.
- If something is not mentioned, use null for its value.
- Do NOT add explanation or commentary.
- Do NOT use markdown formatting.
- Return raw JSON only.

## Few-Shot Examples
{FEW_SHOT_EXAMPLES}

## Problem to Parse
{problem_text}
"""


def build_image_prompt() -> str:
    """Build the prompt for image-based physics problem parsing via Gemini Vision."""
    return f"""You are a physics semantic parser specializing in Newton's Laws problems.

You will be given an IMAGE of a physics problem. This could be:
- A photo of a textbook page
- A screenshot of a question
- A handwritten problem on paper
- A printed worksheet or exam question

## Your Task
1. FIRST, read and extract the physics problem text from the image using OCR.
2. THEN, parse the extracted problem into structured JSON following the schema below.

If the image contains multiple problems, parse only the FIRST one.
If the image is unclear or doesn't contain a physics problem, return an empty structure.

## JSON Schema

{{
  "objects": [
    {{
      "id": "string (unique identifier, e.g. block_1, mass_a)",
      "type": "block | sphere | body | cart | rope | pulley_wheel | wedge | spring_obj",
      "mass": number or null (kg)
    }}
  ],
  "surfaces": [
    {{
      "id": "string (unique identifier)",
      "type": "horizontal_surface | inclined_plane | vertical_wall | pulley | circular_path | fluid_surface",
      "angle": number or null (degrees, for inclined planes),
      "friction_coefficient": number or null
    }}
  ],
  "placements": [
    {{
      "object_id": "string (must match an object id)",
      "surface_id": "string (must match a surface id)"
    }}
  ],
  "forces": [
    {{
      "type": "applied | gravity | normal | tension | spring | friction_force | buoyancy | centripetal_force | drag",
      "magnitude": number or null (Newtons),
      "direction": "up | down | left | right | up_along_plane | down_along_plane | vertical_down | vertical_up | perpendicular_to_surface | centripetal | tangential | radially_outward",
      "object_id": "string (must match an object id)"
    }}
  ],
  "friction": {{
    "object_id": "string",
    "coefficient": number or null
  }} or null,
  "constants": {{
    "gravity": 9.8
  }}
}}

## Rules
- Always include gravity for each object with mass.
- Always include normal force for objects resting on surfaces.
- If friction is mentioned, add both a friction entry AND a friction_force in forces.
- For pulleys, add tension forces on each connected mass.
- Calculate gravity magnitude as mass x 9.8 when mass is given.
- Use only the allowed enum values for type and direction.
- All object_id and surface_id references must match existing entries.
- If something is not mentioned, use null for its value.
- Do NOT add explanation or commentary.
- Do NOT use markdown formatting.
- Return raw JSON only.

## Few-Shot Examples
{FEW_SHOT_EXAMPLES}
"""
