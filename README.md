# PhysicsLens

**Turn natural-language physics questions into labeled SVG force diagrams — no LLMs, no external APIs, fully deterministic.**

PhysicsLens parses a constrained subset of English-language physics problems, solves the underlying Newtonian equations, and renders publication-ready SVG free-body diagrams — all at runtime with zero network calls.

---

## ✨ Features

- **Rule-based NLP pipeline** — keyword classification → regex quantity extraction → optional spaCy dependency parsing
- **Newtonian solvers** for four scenario types (see [Supported Scenarios](#-supported-scenarios))
- **Pure-SVG rendering** — no native graphics libraries, no Canvas, no Matplotlib
- **FastAPI server** with JSON (`/solve`) and direct SVG (`/solve.svg`) endpoints
- **Symbolic algebra** — the Atwood pulley solver uses SymPy to solve tension/acceleration analytically

## 🎯 Supported Scenarios

| Scenario | Example trigger words | Solver |
|---|---|---|
| **Inclined Plane** | *incline, ramp, slope, inclination* | Weight decomposition, normal force, optional friction & holding force |
| **Horizontal Friction** | *horizontal surface, flat surface, floor, table* | Normal force, kinetic friction, applied forces |
| **Atwood Pulley** | *pulley, atwood, hanging masses* | SymPy symbolic solve for acceleration & tension |
| **Projectile Motion** | *thrown, launched, projectile, trajectory* | Range, max height, time of flight |

> [!NOTE]
> The classifier also recognises **circular motion** and **spring-mass** keywords, but solvers for these are not yet implemented. Inputs that match these categories will receive a generic free-body diagram.

---

## 📋 Requirements

- **Python 3.11+** (verified with 3.11, 3.12, 3.13 and 3.14)
- Windows, macOS, or Linux

## 🚀 Quick Start

### 1. Create a virtual environment & install dependencies

```powershell
# Windows PowerShell
py -3 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r physics_diagram\requirements.txt
& .\.venv\Scripts\python.exe -m spacy download en_core_web_sm
```

```bash
# macOS / Linux
python3 -m venv .venv
.venv/bin/python -m pip install -r physics_diagram/requirements.txt
.venv/bin/python -m spacy download en_core_web_sm
```

> [!TIP]
> The spaCy model improves noun-to-quantity attachment via dependency parsing, but the parser includes a **rule-based fallback** — the project works without it.

### 2. Start the API server

```powershell
& .\.venv\Scripts\python.exe -m uvicorn physics_diagram.api:app --reload
```

The interactive API docs are at **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.

### 3. Generate a diagram

**PowerShell:**

```powershell
$body = @{
  text = "A box of mass 5kg is placed on a frictionless inclined plane with 30 degree inclination. How much force is required to keep it at rest?"
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "http://127.0.0.1:8000/solve.svg" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body `
  -OutFile "diagram.svg"
```

**curl:**

```bash
curl -X POST http://127.0.0.1:8000/solve.svg \
  -H "Content-Type: application/json" \
  -d '{"text": "A box of mass 5kg is on a frictionless 30 degree ramp."}' \
  -o diagram.svg
```

Open `diagram.svg` in a browser to view the rendered force diagram.

---

## 🐍 Use from Python

```python
from physics_diagram.pipeline import solve_and_render

result = solve_and_render(
    "A box of mass 5kg is placed on a frictionless inclined plane "
    "with 30 degree inclination. How much force is required to keep it at rest?",
    "incline.svg",
)

print(result["status"])                        # "ok"
print(result["force_solution"].derived_values) # {'normal_force_n': 42.43, ...}
```

---

## 🔬 API Reference

### `POST /solve`

Returns a JSON response with parsed results and a Base64-encoded SVG.

| Field | Type | Description |
|---|---|---|
| `status` | `string` | `"ok"`, `"needs_clarification"`, or `"unsupported_scenario"` |
| `missing_fields` | `string[]` | Slots the parser could not fill (e.g. `["mass_kg"]`) |
| `diagram_svg_base64` | `string` | Base64-encoded SVG (present only when `status` is `"ok"`) |

### `POST /solve.svg`

Returns the SVG image directly with `Content-Type: image/svg+xml`. Returns a `422` with a plain-text error if the input is incomplete.

Both endpoints accept `{"text": "..."}` as the JSON body.

---

## 🏗️ Architecture

```
Input text
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  classifier  │────▶│    parser     │────▶│  physics_engine  │────▶│   renderer   │
│  (keywords)  │     │  (slots +    │     │  (Newtonian      │     │  (pure SVG)  │
│              │     │   spaCy)     │     │   solvers)       │     │              │
└──────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
                                                                         │
                                                                         ▼
                                                                    diagram.svg
```

The pipeline flows through five stages:

1. **`classifier.py`** — Scores each scenario by keyword hits; returns the best match and a confidence value.
2. **`quantities.py`** — Regex-based extraction of masses, angles, speeds, and forces with unit conversion.
3. **`slots.py`** — Maps extracted quantities to typed schema fields (`ObjectSpec`, `Geometry`, `AppliedForce`).
4. **`parser.py`** — Orchestrates classification + slot extraction; optionally refines labels with spaCy.
5. **`validation.py`** — Gates incomplete parses so the solver is never called with missing data.
6. **`physics_engine.py`** — Scenario-specific Newtonian solvers producing `ForceVector` lists.
7. **`renderer.py`** — Converts solved forces into positioned SVG arrows with labels and colors.

---

## 📁 Project Layout

```
PhysicsLens/
├── README.md                        ← you are here
├── physics_diagram/
│   ├── __init__.py                  ← package entry point
│   ├── api.py                       ← FastAPI /solve and /solve.svg endpoints
│   ├── classifier.py                ← keyword-based scenario classification
│   ├── parser.py                    ← NLP pipeline orchestrator
│   ├── physics_engine.py            ← Newtonian force solvers (incline, friction, atwood, projectile)
│   ├── pipeline.py                  ← public solve_and_render() entry point
│   ├── quantities.py                ← regex quantity extraction & unit conversion
│   ├── renderer.py                  ← pure-SVG force diagram renderer
│   ├── schema.py                    ← shared dataclasses (ParseResult, ForceSolution, etc.)
│   ├── slots.py                     ← quantity → schema slot mapping
│   ├── validation.py                ← parse completeness gate
│   ├── requirements.txt             ← Python dependencies
│   ├── README.md                    ← package-level documentation
│   └── tests/
│       ├── test_parser.py           ← parser unit tests
│       ├── test_physics_engine.py   ← solver correctness tests
│       └── test_pipeline_integration.py  ← end-to-end integration tests
└── .gitignore
```

---

## 🧪 Running Tests

```powershell
& .\.venv\Scripts\python.exe -m pytest physics_diagram\tests -q -p no:cacheprovider
```

```bash
# macOS / Linux
.venv/bin/python -m pytest physics_diagram/tests -q -p no:cacheprovider
```

---

## 📝 Example

**Input:**

```text
A box of mass 5kg is placed on a frictionless inclined plane with 30 degree
inclination. How much force is required to keep it at rest?
```

**Output (derived values):**

| Quantity | Value |
|---|---|
| Normal force | 42.43 N |
| Gravity component along incline | 24.50 N |
| Friction force | 0.0 N |
| Required holding force | 24.50 N |

---

## ⚙️ Dependencies

| Package | Purpose |
|---|---|
| [spaCy](https://spacy.io/) ≥ 3.7 | Dependency parsing for noun–quantity attachment (optional at runtime) |
| [SymPy](https://www.sympy.org/) ≥ 1.12 | Symbolic algebra for the Atwood pulley solver |
| [FastAPI](https://fastapi.tiangolo.com/) ≥ 0.110 | HTTP API framework |
| [Uvicorn](https://www.uvicorn.org/) ≥ 0.27 | ASGI server |
| [pytest](https://pytest.org/) ≥ 8.0 | Test runner |

---

## 📄 License

This project does not currently include a license file. Please contact the maintainers for usage terms.
