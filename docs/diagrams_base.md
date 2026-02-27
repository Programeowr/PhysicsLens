# `app/diagrams/base.py` — SVG Drawing Utilities

## What It Does
Provides shared SVG primitives used by all 4 diagram generators: force arrows, blocks, ground hatching, color palette, and the SVG wrapper.

## Why It Exists
All diagram types share common elements (arrows, blocks, colors). Centralizing these avoids code duplication and ensures visual consistency across incline, horizontal, pulley, and vertical diagrams.

## How It Works

### `FORCE_COLORS`
Maps force types to hex colors (matching the frontend legend):
| Force | Color | Hex |
|-------|-------|-----|
| Gravity | Blue | `#3B82F6` |
| Normal | Green | `#22C55E` |
| Friction | Orange | `#F97316` |
| Applied | Red | `#EF4444` |
| Tension | Purple | `#A855F7` |
| Spring | Cyan | `#06B6D4` |

### Key Functions
- `get_force_color(force_type)` — returns the hex color for a force type
- `force_label(force)` — generates a label like `mg=49N` or `F=20N`
- `svg_arrow(x1, y1, x2, y2, color, label)` — SVG `<line>` + `<text>` with arrowhead marker
- `svg_block(cx, cy, w, h, label, angle)` — rotated rectangle with mass label
- `svg_ground_hatching(x, y, width)` — diagonal hatch lines for ground surface
- `svg_wrapper(content, width, height)` — wraps content in `<svg>` with viewBox, white background, and arrowhead marker definitions for all colors

## Dependencies
- `math` — trigonometry for arrow angles
- None external (pure SVG string generation)
