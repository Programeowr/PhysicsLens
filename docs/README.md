# PhysicsLens — Architecture Documentation

> This `docs/` directory contains detailed documentation for every component of the PhysicsLens project. Each file explains **what** the component does, **why** it exists, **how** it works, and **what dependencies** it uses.

## Documentation Index

### Backend (`app/`)

| Doc | Component | Description |
|-----|-----------|-------------|
| [main.md](main.md) | `app/main.py` | FastAPI entry point, CORS, rate limiting, route registration |
| [config.md](config.md) | `app/config.py` | Environment config via pydantic-settings |
| [models.md](models.md) | `app/models.py` | Pydantic v2 schemas, enums, referential integrity |
| [prompts.md](prompts.md) | `app/prompts.py` | AI prompt templates with few-shot examples |
| [parser.md](parser.md) | `app/parser.py` | Gemini text + vision parsing with retry logic |
| [diagrams_base.md](diagrams_base.md) | `app/diagrams/base.py` | SVG utilities, force colors, arrows, blocks |
| [diagrams_incline.md](diagrams_incline.md) | `app/diagrams/incline.py` | Inclined plane FBD generator |
| [diagrams_generators.md](diagrams_generators.md) | `horizontal.py`, `pulley.py`, `vertical.py` | Horizontal, pulley, and vertical FBD generators |
| [routes.md](routes.md) | `app/routes/parse.py`, `diagram.py` | API endpoints for parsing and diagram generation |

### Frontend (`frontend/src/`)

| Doc | Component | Description |
|-----|-----------|-------------|
| [frontend.md](frontend.md) | `App.tsx`, `api.ts`, `index.css`, `App.css` | React UI, API client, design system, component styles |

### Tests (`tests/`)

| Doc | Component | Description |
|-----|-----------|-------------|
| [tests.md](tests.md) | `test_models.py`, `test_parser.py`, `test_diagrams.py` | 36 automated tests covering models, parser, and diagrams |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  App.tsx → api.ts → fetch() ──────────────────┐         │
│  index.css + App.css (dark theme)              │         │
└────────────────────────────────────────────────┼─────────┘
                                                 │ HTTP
┌────────────────────────────────────────────────┼─────────┐
│                  Backend (FastAPI)              │         │
│                                                ▼         │
│  main.py ──► routes/parse.py ──► parser.py ──► Gemini AI │
│         │                           │                    │
│         │    routes/diagram.py ◄────┘                    │
│         │         │                                      │
│         │         ▼                                      │
│         │    diagrams/                                   │
│         │    ├── base.py (shared SVG)                    │
│         │    ├── incline.py                              │
│         │    ├── horizontal.py                           │
│         │    ├── pulley.py                               │
│         │    └── vertical.py                             │
│         │                                                │
│         ├── config.py (.env)                             │
│         ├── models.py (Pydantic v2)                      │
│         └── prompts.py (few-shot)                        │
└──────────────────────────────────────────────────────────┘
```
