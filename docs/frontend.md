# `frontend/src/App.tsx` — Main React Component

## What It Does
The single-page application component that renders the entire PhysicsLens UI: header, input panel (text/image), diagram viewer, export buttons, and force legend.

## Why It Exists
This is the frontend entry point. It manages all UI state (input mode, loading, errors, parsed data, SVG content) and orchestrates the flow from user input → API call → diagram display.

## How It Works

### State Management
Uses React `useState` hooks for:
| State | Type | Purpose |
|-------|------|---------|
| `mode` | `'text' \| 'image'` | Active input tab |
| `problem` | `string` | Text input value |
| `imageFile` | `File \| null` | Uploaded image |
| `imagePreview` | `string \| null` | Base64 preview of uploaded image |
| `appState` | `'idle' \| 'loading' \| 'ready' \| 'error'` | Current app state |
| `svgContent` | `string \| null` | Generated SVG HTML |
| `parsedData` | `ParsedData \| null` | Structured AI output |
| `showJson` | `boolean` | Toggle for JSON viewer |

### User Flow
1. User types a problem or uploads an image
2. Clicks "Generate Free Body Diagram"
3. App calls `/parse` or `/parse-image` API
4. On success, calls `/diagram` with parsed data
5. Renders SVG in the diagram panel
6. User can export as SVG or PNG

### Key Features
- **Tab switching** — text vs image input
- **Drag-and-drop** — file upload with `onDragOver`/`onDrop`
- **Example chips** — 4 pre-written problems that fill the textarea
- **Export SVG** — creates a Blob and triggers download
- **Export PNG** — renders SVG to Canvas at 2x resolution, exports as PNG
- **JSON viewer** — collapsible `<pre>` showing the raw parsed data

## Dependencies
- `react` — component framework
- `./api.ts` — typed API client functions

---

# `frontend/src/api.ts` — API Client

## What It Does
Typed TypeScript functions for calling the backend API. Handles fetch requests, error formatting, and response typing.

## Why It Exists
Separates network logic from UI code. Provides typed interfaces so TypeScript catches schema mismatches at compile time.

## Functions
| Function | Input | Output | Endpoint |
|----------|-------|--------|----------|
| `parseTextProblem(text)` | problem string | `ParseResponse` | `POST /parse` |
| `parseImageProblem(file)` | File object | `ParseResponse` | `POST /parse-image` |
| `generateDiagram(data)` | ParsedData | SVG string | `POST /diagram` |

## Dependencies
- Native `fetch` API (no external HTTP library)

---

# `frontend/src/index.css` — Design System

## What It Does
Defines the global CSS custom properties (variables) that create the dark theme, typography, spacing, colors, and reusable visual tokens.

## Key Design Tokens
- **Colors** — navy/slate dark palette with indigo (#6366F1) accent
- **Force colors** — matching backend (blue/green/orange/red/purple)
- **Typography** — Inter (sans) + JetBrains Mono (code)
- **Spacing** — 4px base scale (4, 8, 12, 16, 20, 24, 32, 40, 48)
- **Radius** — 6px → 20px
- **Shadows** — sm/md/lg + glow effect
- **Transitions** — 150ms (fast) / 250ms (base) / 400ms (slow)

Also includes CSS reset, scrollbar styling, and selection color.

---

# `frontend/src/App.css` — Component Styles

## What It Does
All component-level styles for the app: header, input panel, tabs, textarea, upload zone, parse button, diagram viewer, toolbar, force legend, and parsed data viewer.

## Key CSS Features
- **Gradient header** — brand name uses `background-clip: text` gradient
- **Input tabs** — pill-style toggle with active state
- **Upload zone** — dashed border with hover/dragover glow effects
- **Parse button** — gradient background with `::before` hover overlay
- **Spinner** — CSS keyframe animation for loading state
- **Diagram container** — white background card with fadeIn animation
- **Force legend** — color-coded dots matching the SVG arrows
