# Architecture

PhysicsLens converts a natural-language physics question into a labeled SVG force diagram. A local Ollama `qwen2.5:7b` model extracts structured facts; all physics calculations and SVG generation remain local and deterministic.

## Data flow

```text
Question text
    │
    ▼
parser.parse()
    │  Ollama JSON-schema extraction
    ▼
ParseResult
    │
    ▼
validation.validate()
    │
    ├── incomplete → generic SVG + missing-field response
    │
    ▼ complete
physics_engine.solve()
    │  Newtonian calculations
    ▼
ForceSolution
    │
    ▼
renderer.render()
    │
    ▼
SVG file / API response
```

## Modules

| Module | Responsibility |
| --- | --- |
| `schema.py` | Typed dataclasses shared throughout the application: `ParseResult`, `ForceSolution`, and force/object specifications. |
| `classifier.py` | Keyword-trigger scenario classification and each scenario's required slot list. |
| `quantities.py` | Regex extraction plus unit conversion for mass, angle, speed, and force values; also supports common spelled-out numbers. |
| `slots.py` | Converts extracted quantities and keywords into objects, geometry, friction, applied forces, and requested unknowns. |
| `parser.py` | Calls local Ollama with a JSON-schema-constrained prompt and converts the result into a `ParseResult`. |
| `validation.py` | Validation gate. Incomplete parses are returned without reaching a solver. |
| `physics_engine.py` | Scenario-specific physics calculations and the solver dispatcher. The Atwood solver uses SymPy equations. |
| `renderer.py` | Dependency-free SVG generation for each supported scenario. It draws surfaces, objects, force arrows, labels, and geometry. |
| `pipeline.py` | Main orchestration function: `solve_and_render(text, output_path)`. |
| `api.py` | FastAPI interface exposing JSON (`POST /solve`) and direct SVG (`POST /solve.svg`) responses. |

## Core data structures

`ParseResult` represents what the parser understood from the question. It contains the selected scenario, confidence, objects and masses, geometry, friction information, applied forces, and missing fields.

The Ollama parser requests JSON constrained by a schema and uses temperature `0` with a fixed seed. The prompt instructs Qwen to normalize units to SI and never infer missing numerical values. `parser.py` then validates that JSON while constructing the typed `ParseResult` used by the rest of the pipeline.

`ForceSolution` is created only after a complete parse. It contains `ForceVector` values with a numeric magnitude, direction in screen coordinates, and the object each force acts on. Renderer code never calculates physics values; it only displays the solution.

## Supported scenarios

The current solver and renderer registry supports:

- Inclined plane
- Horizontal friction
- Atwood pulley
- Projectile motion

The classifier also recognizes circular motion and spring-mass prompts. They return an `unsupported_scenario` response until their solver and renderer are added.

## API behavior

`POST /solve` returns JSON with a status and a Base64-encoded SVG for successful requests.

`POST /solve.svg` returns the SVG directly with the `image/svg+xml` content type. This is useful for downloading an image or embedding it in a web page:

```html
<img src="diagram.svg" alt="Physics force diagram">
```

Incomplete questions return `needs_clarification` and list the missing required fields. For example, an incline question without mass or angle will not reach the physics engine.

## Extending the system

To add a scenario without changing `pipeline.py`:

1. Add keywords and required slots in `classifier.py`.
2. Extend `slots.py` if new quantities or domain fields are needed.
3. Add a solver in `physics_engine.py` and register it in `SOLVERS`.
4. Add an SVG renderer in `renderer.py` and register it in `RENDERERS`.
5. Add parser, solver, and integration tests under `physics_diagram/tests/`.

The pipeline dispatches through these registries, keeping scenario additions localized.
