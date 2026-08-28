# Physics Question → Force Diagram Generator

This package converts a constrained natural-language physics question into a deterministic, labeled SVG force diagram. It uses no LLMs, no network calls at runtime, and no native graphics dependencies.

## Setup

Python 3.11 or newer is required.

```powershell
cd physics_diagram
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

The spaCy model supplies dependency parsing to improve noun-to-quantity attachment. The parser retains a rule-based fallback if it has not yet been installed.

## Run tests

```powershell
python -m pytest tests -q
```

## Use from Python

```python
from physics_diagram.pipeline import solve_and_render

result = solve_and_render(
    "A box of mass 5kg is placed on a frictionless inclined plane with 30 degree inclination. How much force is required to keep it at rest?",
    "incline.svg",
)
print(result["force_solution"].derived_values)
```

## Run the API

From the project root:

```powershell
uvicorn physics_diagram.api:app --reload
```

POST `{"text": "A 5 kg box is on a frictionless 30 degree ramp."}` to `/solve`. A successful result contains `diagram_svg_base64`; incomplete inputs contain `missing_fields`.
