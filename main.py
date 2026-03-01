from fastapi import FastAPI, Response
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import math
import json
import os

# ----------------------------
# LOAD ENVIRONMENT VARIABLES
# ----------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()


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
    


def generate_incline_diagram(data):
    angle = data["surfaces"][0]["angle"]
    mass = data["objects"][0]["mass"]
    forces = data["forces"]
    g = data["constants"]["gravity"]

    angle_rad = math.radians(angle)

    width = 600
    height = 500

    base = 300
    x1, y1 = 100, 400
    x2 = x1 + base
    y2 = y1 - base * math.tan(angle_rad)

    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2

    block_size = 50
    block_x = mid_x - block_size / 2
    block_y = mid_y - block_size / 2

    arrows_svg = ""
    for force in data["forces"]:
      start_x = mid_x
      start_y = mid_y
      scale = 10

      if force["type"] == "gravity":
          dx = 0
          dy = scale * 10
          label = "mg"

      elif force["type"] == "applied":
          mag = force["magnitude"]
          dx = scale * mag * math.cos(angle_rad) / 10
          dy = -scale * mag * math.sin(angle_rad) / 10
          label = f"{mag}N"

      end_x = start_x + dx
      end_y = start_y + dy

      arrows_svg += f'''
      <line x1="{start_x}" y1="{start_y}"
            x2="{end_x}" y2="{end_y}"
            stroke="red" stroke-width="2"
            marker-end="url(#arrowhead)"/>
      <text x="{end_x + 5}" y="{end_y + 5}" font-size="14" fill="white">{label}</text>
      '''

    svg = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">

        <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7"
                    refX="10" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="red"/>
            </marker>
        </defs>

        <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
              stroke="black" stroke-width="3"/>

        <rect x="{block_x}" y="{block_y}"
              width="{block_size}" height="{block_size}"
              fill="gray"
              transform="rotate({-angle} {mid_x} {mid_y})"/>

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