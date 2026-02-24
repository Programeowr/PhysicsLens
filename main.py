from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
import os
import json

# ----------------------------
# CONFIGURE GEMINI API KEY
# ----------------------------

GEMINI_API_KEY = "AIzaSyA9TS43rDrJ6H76n7WNbOFkzF5VCJZtB_U"
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
            "temperature": 0
        }
    )

    raw_text = response.text.strip()

    try:
        parsed_json = json.loads(raw_text)
        return {"status": "success", "data": parsed_json}
    except:
        return {
            "status": "error",
            "raw_output": raw_text
        }