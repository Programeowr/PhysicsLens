# `app/models.py` — Pydantic Data Models

## What It Does
Defines the complete data schema for parsed physics problems using Pydantic v2 models. This is the "contract" between the AI parser and the diagram generators.

## Why It Exists
The AI (Gemini) returns unstructured JSON. Without validation, malformed data would crash the diagram generators or produce incorrect diagrams. These models enforce:
- **Type safety** — every field has a strict type
- **Enum constraints** — only valid force types, directions, and surface types
- **Referential integrity** — object/surface IDs referenced in placements and forces must actually exist

## How It Works

### Enums
Constrain values to a known set:
- `ObjectType` — `block`, `sphere`, `body`, `cart`, `rope`, `pulley_wheel`
- `ForceType` — `applied`, `gravity`, `normal`, `tension`, `spring`, `friction_force`
- `Direction` — `up`, `down`, `left`, `right`, `vertical_up`, `vertical_down`, `up_along_plane`, `down_along_plane`, `perpendicular_to_surface`
- `SurfaceType` — `horizontal_surface`, `inclined_plane`, `vertical_wall`, `pulley`

### Core Models
- `PhysicsObject` — an object with `id`, `type`, `mass`
- `Surface` — a surface with `id`, `type`, `angle`, `friction_coefficient`
- `Placement` — links an object to a surface
- `Force` — a force with `type`, `magnitude`, `direction`, `object_id`
- `Friction` — friction data with `object_id` and `coefficient`
- `PhysicsConstants` — constants like gravity (default 9.8)

### `ParsedPhysicsProblem` (root model)
Contains all the above plus a `@model_validator` that scans every `object_id` and `surface_id` reference and raises `ValidationError` if any ID doesn't match an existing object/surface.

### `ProblemInput`
Simple model for the `/parse` endpoint: validates that the `problem` text is at least 10 characters.

## Dependencies
- `pydantic` v2 — data validation, serialization, model validators
