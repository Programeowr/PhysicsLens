from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
import math
import json

# ----------------------------
# CONFIGURE GEMINI API KEY
# ----------------------------

GEMINI_API_KEY = "AIzaSyABNu94NyLgg7kVVen_yO7thKF6ILEz54g"
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# REQUEST MODEL
# ----------------------------

class ProblemInput(BaseModel):
    problem: str


# ----------------------------
# PROMPT TEMPLATE
# ----------------------------

def build_prompt(problem_text: str) -> str:
    return f"""
You are a physics semantic parser.

Extract entities from this Newton's Laws problem.

Return STRICTLY valid JSON with this structure:

{{
  "objects": [
    {{
      "id": "string",
      "type": "block | sphere | body | cart",
      "mass": number
    }}
  ],
  "surfaces": [
    {{
      "id": "string",
      "type": "horizontal_surface | inclined_plane",
      "angle": number or null
    }}
  ],
  "placements": [
    {{
      "object_id": "string",
      "surface_id": "string"
    }}
  ],
  "forces": [
    {{
      "type": "applied | gravity",
      "magnitude": number or null,
      "direction": "left | right | up_along_plane | down_along_plane | vertical_down",
      "object_id": "string"
    }}
  ],
  "friction": {{
    "object_id": "string",
    "coefficient": number or null
  }},
  "constants": {{
    "gravity": 9.8
  }}
}}

Rules:
- Use only allowed direction values.
- If something is not mentioned, use null.
- Do NOT add explanation.
- Do NOT use markdown.
- Return raw JSON only.

Problem:
{problem_text}
"""


# ----------------------------
# API ENDPOINT
# ----------------------------

@app.post("/parse")
def parse_problem(data: ProblemInput):
    prompt = build_prompt(data.problem)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "temperature": 0,
            "response_mime_type": "application/json"
        }
    )

    try:
        parsed_json = json.loads(response.text)
        return {"status": "success", "data": parsed_json}
    except:
        return {
            "status": "error",
        }
    
import math

def force_arrow(x, y, dx, dy, label, color="#1f77b4"):

    end_x = x + dx
    end_y = y + dy

    # Offset label slightly in arrow direction
    label_x = end_x + (8 if dx >= 0 else -25)
    label_y = end_y - 8

    marker_id = f"arrowhead_{color.replace('#','')}"

    return f'''
    <line x1="{x}" y1="{y}"
          x2="{end_x}" y2="{end_y}"
          stroke="{color}" stroke-width="4"
          marker-end="url(#{marker_id})"/>

    <text x="{label_x}" y="{label_y}"
          font-size="18"
          font-weight="bold"
          fill="{color}">
          {label}
    </text>
    '''

def generate_incline_diagram(data):
    surface = data["surfaces"][0]
    angle = surface["angle"]
    mass = data["objects"][0]["mass"]
    forces = data["forces"]
    g = data["constants"]["gravity"]

    angle_rad = math.radians(angle)

    width = 800
    height = 550

    # ----------------------------
    # Incline Geometry
    # ----------------------------

    base = 450
    x1, y1 = 150, 450
    x2 = x1 + base
    y2 = y1 - base * math.tan(angle_rad)

    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2

    block_size = 75
    block_x = mid_x - block_size / 2
    block_y = mid_y - block_size / 2

    arrows_svg = ""

    # ----------------------------
    # UNIT VECTORS
    # ----------------------------

    ux = math.cos(angle_rad)
    uy = -math.sin(angle_rad)

    dx_plane = -ux
    dy_plane = -uy

    nx = -math.sin(angle_rad)
    ny = -math.cos(angle_rad)

    scale_force = 100

    start_x = mid_x
    start_y = mid_y

    # ----------------------------
    # GRAVITY
    # ----------------------------

    arrows_svg += force_arrow(start_x, start_y,
                              0, scale_force,
                              "mg", "#d62728")

    # ----------------------------
    # NORMAL
    # ----------------------------

    arrows_svg += force_arrow(start_x, start_y,
                              scale_force * nx,
                              scale_force * ny,
                              "N", "#2ca02c")

    # ----------------------------
    # FRICTION
    # ----------------------------

    if data.get("friction") and data["friction"].get("coefficient"):

        mg = mass * g
        mg_along = mg * math.sin(angle_rad)

        applied_along = 0
        for force in forces:
            if force["type"] == "applied" and force["magnitude"]:
                applied_along += force["magnitude"]

        net_tendency = mg_along - applied_along

        if net_tendency > 0:
            fr_dx = scale_force * ux
            fr_dy = scale_force * uy
        else:
            fr_dx = scale_force * dx_plane
            fr_dy = scale_force * dy_plane

        arrows_svg += force_arrow(start_x, start_y,
                                  fr_dx, fr_dy,
                                  f"{data['friction']['coefficient']}μN (f)", "#9467bd")

    # ----------------------------
    # APPLIED FORCES
    # ----------------------------

    for force in forces:
        if force["type"] == "applied" and force["magnitude"]:

            mag = force["magnitude"]

            if force["direction"] == "down_along_plane":
              dx = (mag / 50) * scale_force * dx_plane
              dy = (mag / 50) * scale_force * dy_plane

            elif force["direction"] == "up_along_plane":
              dx = (mag / 50) * scale_force * ux
              dy = (mag / 50) * scale_force * uy

            arrows_svg += force_arrow(start_x, start_y,
                                      dx, dy,
                                      f"{mag}N", "#1f77b4")

    # ----------------------------
    # Angle Arc
    # ----------------------------

    arc_radius = 70
    arc_svg = f'''
    <path d="M {x1 + arc_radius} {y1}
             A {arc_radius} {arc_radius} 0 0 0
             {x1 + arc_radius * math.cos(angle_rad)}
             {y1 - arc_radius * math.sin(angle_rad)}"
          fill="none"
          stroke="black"
          stroke-width="3"/>

    <text x="{x1 + 50}" y="{y1 - 15}"
          font-size="20"
          font-weight="bold">
          {angle}°
    </text>
    '''

    # ----------------------------
    # FINAL SVG
    # ----------------------------

    svg = f"""
    <svg width="{width}" height="{height}"
         xmlns="http://www.w3.org/2000/svg">

        <defs>

            <marker id="arrowhead_1f77b4" markerWidth="12" markerHeight="8"
                    refX="12" refY="4" orient="auto">
                <polygon points="0 0, 12 4, 0 8" fill="#1f77b4"/>
            </marker>

            <marker id="arrowhead_d62728" markerWidth="12" markerHeight="8"
                    refX="12" refY="4" orient="auto">
                <polygon points="0 0, 12 4, 0 8" fill="#d62728"/>
            </marker>

            <marker id="arrowhead_2ca02c" markerWidth="12" markerHeight="8"
                    refX="12" refY="4" orient="auto">
                <polygon points="0 0, 12 4, 0 8" fill="#2ca02c"/>
            </marker>

            <marker id="arrowhead_9467bd" markerWidth="12" markerHeight="8"
                    refX="12" refY="4" orient="auto">
                <polygon points="0 0, 12 4, 0 8" fill="#9467bd"/>
            </marker>

        </defs>

        <!-- Background -->
        <rect width="100%" height="100%" fill="#f8f9fa"/>

        <!-- Incline -->
        <line x1="{x1}" y1="{y1}"
              x2="{x2}" y2="{y2}"
              stroke="black"
              stroke-width="5"/>

        <!-- Block -->
        <rect x="{block_x}" y="{block_y}"
              width="{block_size}"
              height="{block_size}"
              fill="#6c757d"
              rx="10"
              transform="rotate({-angle} {mid_x} {mid_y})"/>

        <!-- Mass Label -->
        <text x="{mid_x}"
              y="{mid_y - block_size}"
              text-anchor="middle"
              font-size="18"
              font-weight="bold">
              {mass} kg
        </text>

        {arc_svg}
        {arrows_svg}

    </svg>
    """

    return svg


def generate_horizontal_diagram(data):
    mass = data["objects"][0]["mass"]
    forces = data["forces"]
    friction_data = data.get("friction")

    width = 700
    height = 450

    ground_y = 320
    block_size = 70
    block_x = width // 2 - block_size // 2
    block_y = ground_y - block_size

    arrows_svg = ""

    # Physics constants
    g = data.get("constants", {}).get("gravity", 9.8)
    scale = 4

    start_x = block_x + block_size / 2
    start_y = block_y + block_size / 2

    # ---------------------------------------------------
    # 1️⃣ COMPUTE NET HORIZONTAL APPLIED FORCE
    # ---------------------------------------------------

    net_horizontal = 0

    for force in forces:
        if force.get("direction") == "right" and force.get("magnitude"):
            net_horizontal += force["magnitude"]
        elif force.get("direction") == "left" and force.get("magnitude"):
            net_horizontal -= force["magnitude"]

    # ---------------------------------------------------
    # 2️⃣ DRAW APPLIED FORCES
    # ---------------------------------------------------

    for force in forces:

        dx = 0
        dy = 0
        label = ""
        color = "#1f77b4"  # blue for applied

        if force.get("direction") == "right" and force.get("magnitude"):
            dx = scale * force["magnitude"]
            label = f'{force["magnitude"]}N'

        elif force.get("direction") == "left" and force.get("magnitude"):
            dx = -scale * force["magnitude"]
            label = f'{force["magnitude"]}N'

        else:
            continue

        end_x = start_x + dx
        end_y = start_y + dy

        arrows_svg += f'''
        <line x1="{start_x}" y1="{start_y}"
              x2="{end_x}" y2="{end_y}"
              stroke="{color}" stroke-width="3"
              marker-end="url(#arrowhead_1f77b4)"/>

        <text x="{end_x + (8 if dx >= 0 else -25)}"
              y="{end_y - 8}"
              font-size="16"
              font-weight="bold"
              fill="{color}">
              {label}
        </text>
        '''

    # ---------------------------------------------------
    # 3️⃣ DRAW GRAVITY
    # ---------------------------------------------------

    mg = mass * g
    dy = scale * mg

    arrows_svg += f'''
    <line x1="{start_x}" y1="{start_y}"
          x2="{start_x}" y2="{start_y + dy}"
          stroke="#d62728" stroke-width="3"
          marker-end="url(#arrowhead_d62728)"/>

    <text x="{start_x + 8}"
          y="{start_y + dy - 8}"
          font-size="16"
          font-weight="bold"
          fill="#d62728">
          mg
    </text>
    '''

    # ---------------------------------------------------
    # 4️⃣ DRAW NORMAL (Automatically = mg)
    # ---------------------------------------------------

    dy_normal = -scale * mg

    arrows_svg += f'''
    <line x1="{start_x}" y1="{start_y}"
          x2="{start_x}" y2="{start_y + dy_normal}"
          stroke="#2ca02c" stroke-width="3"
          marker-end="url(#arrowhead_2ca02c)"/>

    <text x="{start_x + 8}"
          y="{start_y + dy_normal - 8}"
          font-size="16"
          font-weight="bold"
          fill="#2ca02c">
          N
    </text>
    '''

    # ---------------------------------------------------
    # 5️⃣ DRAW FRICTION (μN)
    # ---------------------------------------------------

    if friction_data and friction_data.get("coefficient"):

        mu = friction_data["coefficient"]
        normal_force = mg
        friction_magnitude = mu * normal_force
        friction_scale_multiplier = 1.8

        # Smart friction direction
        if net_horizontal > 0:
            dx_friction = -scale * friction_magnitude * friction_scale_multiplier
        elif net_horizontal < 0:
            dx_friction = scale * friction_magnitude * friction_scale_multiplier
        else:
            dx_friction = 0

        end_x = start_x + dx_friction
        end_y = start_y

        arrows_svg += f'''
        <line x1="{start_x}" y1="{start_y}"
              x2="{end_x}" y2="{end_y}"
              stroke="#9467bd" stroke-width="3"
              marker-end="url(#arrowhead_9467bd)"/>

        <text x="{end_x + (8 if dx_friction >= 0 else -25)}"
              y="{end_y - 8}"
              font-size="16"
              font-weight="bold"
              fill="#9467bd">
              {mu}uN (f)
        </text>
        '''

    # ---------------------------------------------------
    # FINAL SVG
    # ---------------------------------------------------

    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">

        <defs>
            <marker id="arrowhead_1f77b4" markerWidth="10" markerHeight="7"
                    refX="10" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#1f77b4"/>
            </marker>

            <marker id="arrowhead_d62728" markerWidth="10" markerHeight="7"
                    refX="10" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#d62728"/>
            </marker>

            <marker id="arrowhead_2ca02c" markerWidth="10" markerHeight="7"
                    refX="10" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#2ca02c"/>
            </marker>

            <marker id="arrowhead_9467bd" markerWidth="10" markerHeight="7"
                    refX="10" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#9467bd"/>
            </marker>
        </defs>

        <rect width="100%" height="100%" fill="#f8f9fa"/>

        <line x1="0" y1="{ground_y}"
              x2="{width}" y2="{ground_y}"
              stroke="black" stroke-width="4"/>

        <rect x="{block_x}" y="{block_y}"
              width="{block_size}" height="{block_size}"
              fill="#6c757d" rx="8"/>

        <text x="{block_x + block_size/2}"
              y="{block_y - 10}"
              text-anchor="middle"
              font-size="16"
              font-weight="bold">
              {mass} kg
        </text>

        {arrows_svg}

    </svg>
    """

    return svg


@app.post("/diagram")
def diagram(data: dict):
    svg = generate_incline_diagram(data["data"])
    return svg, 200, {"Content-Type": "image/svg+xml"}


@app.get("/test-diagram")
def test_diagram():
    sample_data = {
    "objects": [
      {
        "id": "block_1",
        "type": "block",
        "mass": 5
      }
    ],
    "surfaces": [
      {
        "id": "incline_1",
        "type": "inclined_plane",
        "angle": 30
      }
    ],
    "placements": [
      {
        "object_id": "block_1",
        "surface_id": "incline_1"
      }
    ],
    "forces": [
      {
        "type": "applied",
        "magnitude": 20,
        "direction": "up_along_plane",
        "object_id": "block_1"
      },
      {
        "type": "gravity",
        "magnitude": 9.8 * 5,
        "direction": "vertical_down",
        "object_id": "block_1"
      }
    ],
    "friction": {
      "object_id": "block_1",
      "coefficient": 0.2
    },
    "constants": {
      "gravity": 9.8
    }
  }

    svg = generate_incline_diagram(sample_data)
    return Response(content=svg, media_type="image/svg+xml")

@app.post("/solve-and-diagram")
def solve_and_diagram(data: ProblemInput):
    # Step 1: Build prompt
    prompt = build_prompt(data.problem)

    # Step 2: Call Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "temperature": 0,
            "response_mime_type": "application/json"
        }
    )

    # Step 3: Parse JSON
    try:
        parsed_json = json.loads(response.text)
    except:
        return {"status": "error", "message": "Invalid JSON from model"}

    # Step 4: Generate SVG
    surface = parsed_json["surfaces"][0]

    if surface["type"] == "inclined_plane":
        svg = generate_incline_diagram(parsed_json)

    elif surface["type"] == "horizontal_surface":
        svg = generate_horizontal_diagram(parsed_json)

    else:
        return {"status": "error", "message": "Unsupported surface type"}

    # Step 5: Return SVG directly
    return Response(content=svg, media_type="image/svg+xml")