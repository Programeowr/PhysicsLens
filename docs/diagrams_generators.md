# `app/diagrams/horizontal.py` — Horizontal Surface Diagram

## What It Does
Generates an SVG Free Body Diagram for a block on a flat horizontal surface with force arrows for gravity, normal, applied, and friction forces.

## Why It Exists
Horizontal surface problems (pushing a box, friction on a floor) are fundamental in introductory physics. This generator visualizes the flat surface setup with all relevant forces.

## How It Works
1. **Draws the ground** — a horizontal line with hatching below
2. **Places the block** — a rectangle sitting on the surface with mass label
3. **Adds force arrows**:
   - Gravity → straight down
   - Normal → straight up
   - Applied → horizontal (left or right)
   - Friction → opposing direction of applied force

## Dependencies
- `app.diagrams.base` — shared SVG utilities

---

# `app/diagrams/pulley.py` — Atwood Machine Diagram

## What It Does
Generates an SVG diagram of an Atwood machine: a pulley wheel at the top, two masses hanging on either side connected by a rope, with gravity and tension force arrows on each mass.

## Why It Exists
Pulley/Atwood machine problems involve two connected masses and are a key topic in Newton's Laws. The diagram shows the physical setup clearly.

## How It Works
1. **Draws the support** — a horizontal bar at the top
2. **Draws the pulley** — a circle (wheel) centered at the top
3. **Draws the rope** — lines from each mass up to the pulley
4. **Places two blocks** — one on each side, labeled with mass
5. **Adds force arrows** — gravity (down) and tension (up) on each mass

## Dependencies
- `math` — circle geometry
- `app.diagrams.base` — shared SVG utilities

---

# `app/diagrams/vertical.py` — Vertical / Elevator Diagram

## What It Does
Generates an SVG diagram for vertical scenarios like a person standing in an elevator, showing the enclosure, scale, acceleration indicator, and force arrows.

## Why It Exists
Elevator/vertical problems test understanding of apparent weight and Newton's 2nd Law in non-inertial frames. The diagram makes the physical situation concrete.

## How It Works
1. **Draws the elevator** — a rectangle enclosure with open top
2. **Draws the scale** — a small platform inside the elevator
3. **Places the person/block** — on the scale with mass label
4. **Draws acceleration arrow** — indicating elevator movement direction
5. **Adds force arrows** — gravity (down) and normal (up)

## Dependencies
- `app.diagrams.base` — shared SVG utilities
