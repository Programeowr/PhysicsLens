# Prompt: Redesign the PhysicsLens SVG Rendering Engine

## Background

PhysicsLens is an AI-powered educational application that converts natural-language physics problems into accurate Free Body Diagrams (FBDs). The system uses a hybrid architecture:

* Fine-tuned Open-Source LLM → Parses the question into structured JSON (`ParseResult`)
* Deterministic Physics Engine → Computes all physical quantities
* SVG Renderer → Generates textbook-quality diagrams

The parser and physics engine are already implemented.

The goal is **not** to change the parser or solver.

The objective is to redesign the **rendering pipeline** to generate professional, scalable, textbook-quality SVG diagrams.

---

# Current Problems

The existing renderer is entirely hardcoded.

Issues include:

* Fixed object positions
* Fixed arrow lengths
* Labels frequently overlap
* Poor spacing
* Difficult to extend for new scenarios
* Repeated rendering logic
* Basic visuals
* Low-quality typography
* No layout engine
* No scaling based on canvas size

As more physics scenarios are added, maintaining the renderer becomes increasingly difficult.

---

# Goal

Redesign the rendering architecture to make it:

* Modular
* Scalable
* Extensible
* Maintainable
* Visually professional
* Deterministic

The renderer must continue producing **accurate SVG diagrams**, not AI-generated images.

---

# New Rendering Pipeline

The rendering pipeline should follow this architecture:

```text
ParseResult
      │
      ▼
Physics Engine
      │
      ▼
ForceSolution
      │
      ▼
Scene Graph Generator
      │
      ▼
Layout Engine
      │
      ▼
SVG Renderer
      │
      ▼
SVG Output
```

Each stage should have a single responsibility.

---

# Scene Graph

Introduce a Scene Graph that completely separates physics from rendering.

The Scene Graph should describe **what** needs to be drawn instead of **how** it is drawn.

Example structure:

```json
{
  "canvas": {
    "width": 900,
    "height": 700
  },

  "surfaces": [
    {
      "type": "incline",
      "angle": 30
    }
  ],

  "objects": [
    {
      "id": "block1",
      "type": "block",
      "rotation": 30,
      "position": [0,0]
    }
  ],

  "forces": [
    {
      "label": "W",
      "origin": "block1",
      "direction": "down",
      "magnitude": 49
    },
    {
      "label": "N",
      "origin": "block1",
      "direction": "normal"
    }
  ],

  "annotations": [
    {
      "type":"angle",
      "value":30
    }
  ]
}
```

The Scene Graph must be generic enough to support every future physics scenario.

---

# Layout Engine

Introduce a dedicated Layout Engine.

Its responsibility is to compute positions automatically.

It should:

* Center the main object
* Position surfaces
* Compute force origins
* Avoid label overlap
* Keep arrows inside the canvas
* Maintain margins
* Scale the scene to different canvas sizes
* Rotate objects appropriately
* Place angle annotations
* Support responsive rendering

The layout engine should never perform physics calculations.

---

# SVG Renderer

The renderer should only convert the Scene Graph into SVG.

It should not:

* Solve physics
* Compute geometry
* Decide positions
* Calculate vectors

Its responsibility is only drawing.

---

# Visual Improvements

Upgrade the overall visual quality.

## Objects

Objects should have:

* Rounded corners
* Soft fills
* Consistent outlines
* Rotation support

Surfaces should include:

* Horizontal ground
* Inclined planes
* Pulley supports
* Circular tracks
* Spring anchors

---

## Force Arrows

Force arrows should have:

* Consistent stroke width
* Rounded joins
* Professional arrowheads
* Adjustable arrowhead size
* Smooth rendering

Arrow lengths should scale according to force magnitude while respecting minimum and maximum lengths.

Example:

```
Displayed Length

= clamp(
    magnitude × scaleFactor,
    minimumLength,
    maximumLength
)
```

---

## Color Scheme

Use consistent colors throughout the application.

Suggested palette:

Weight → Red

Normal → Blue

Applied Force → Purple

Friction → Green

Tension → Orange

Spring Force → Cyan

Reaction Forces → Dark Blue

Dashed construction lines → Gray

Ground → Neutral Gray

Objects → Light Gray

---

# Typography

Replace default SVG fonts.

Use modern fonts such as:

* Inter
* Roboto
* Source Sans Pro

Labels should:

* Scale automatically
* Never overlap
* Maintain readable spacing
* Remain horizontal even when objects rotate

---

# Force Labels

Labels should automatically position themselves.

Rules:

* Stay near arrow tips
* Never overlap arrows
* Never overlap other labels
* Maintain minimum padding
* Avoid object boundaries

---

# Angle Rendering

For inclined planes:

Draw:

* Angle arc
* Degree label
* Inclined surface
* Rotated object

The angle annotation should resemble standard physics textbook diagrams.

---

# Components View

Support optional rendering of force components.

Example:

Weight

↓

Resolve into

* mg sin θ
* mg cos θ

Displayed using dashed construction lines.

This mode should be toggleable.

---

# Responsive Scaling

The renderer should support arbitrary canvas sizes.

Examples:

* 600×400
* 900×700
* 1600×1200

All objects should scale proportionally.

---

# SVG Structure

Organize the SVG using logical groups.

Example:

```
<svg>

<g id="background">

<g id="surfaces">

<g id="objects">

<g id="forces">

<g id="labels">

<g id="annotations">

</svg>
```

This makes future animations and interactions easier.

---

# Future Extensibility

The renderer should be designed to easily support future scenarios such as:

* Circular Motion
* Spring-Mass Systems
* Multiple Pulley Systems
* Connected Blocks
* Trusses
* Electric Field Diagrams
* Magnetic Force Diagrams
* Momentum Collision Diagrams

Adding a new scenario should require only:

1. Scene Graph generation
2. Layout rules
3. Rendering logic

without modifying existing scenarios.

---

# Optional Frontend Enhancements

If integrated with a web frontend, support:

* SVG animations
* Hover tooltips
* Force highlighting
* Interactive labels
* Zoom
* Pan
* Dark mode
* Export to PNG
* Export to PDF

---

# Constraints

* Do **not** use AI image generation models.
* Do **not** use raster graphics.
* Continue generating pure SVG output.
* Keep the renderer deterministic.
* Separate rendering completely from physics calculations.
* Maintain compatibility with the existing `ParseResult` and `ForceSolution` data structures.
* Follow SOLID design principles.
* Prefer reusable components and modular architecture over hardcoded drawing logic.

---

# Expected Outcome

The redesigned renderer should produce clean, publication-quality, textbook-style SVG free-body diagrams that are scalable, maintainable, and easily extensible. The rendering pipeline should consist of a **Scene Graph**, **Layout Engine**, and **SVG Renderer**, ensuring a clear separation of concerns and allowing PhysicsLens to support increasingly complex mechanics scenarios without architectural changes.
