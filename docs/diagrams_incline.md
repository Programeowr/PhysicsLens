# `app/diagrams/incline.py` — Inclined Plane Diagram

## What It Does
Generates an SVG Free Body Diagram for a block on an inclined plane, showing the slope, angle arc, ground hatching, and color-coded force arrows.

## Why It Exists
Inclined plane problems are one of the most common Newton's Laws scenarios in physics education. This generator visualizes the geometry and all forces acting on the block.

## How It Works
1. **Reads parsed data** — extracts the inclined surface angle, the block mass, and all forces
2. **Draws the incline** — a triangle from bottom-left to top-right with hatched ground
3. **Places the block** — rotated rectangle sitting on the slope surface
4. **Draws the angle arc** — shows the incline angle (e.g., 30°) at the base
5. **Adds force arrows** — gravity (straight down), normal (perpendicular to surface), friction (along surface), applied (along surface)
6. **Wraps in SVG** — uses `svg_wrapper()` from base module

### Force Arrow Directions
| Force | Direction in Diagram |
|-------|---------------------|
| Gravity | Straight down from block center |
| Normal | Perpendicular to incline surface (outward) |
| Friction | Along incline surface (opposing motion) |
| Applied | Along incline surface (up or down) |

## Dependencies
- `math` — sin, cos, radians for incline geometry
- `app.diagrams.base` — shared SVG utilities
