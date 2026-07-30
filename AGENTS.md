# AGENTS.md

This repository contains a Python physics solver plus a React frontend.

## Layout
- `physics_diagram/` contains the backend solver, API, parser, and renderer.
- `frontend/` contains the React UI.

## Frontend rules
- Run frontend commands from `frontend/`, not the repo root.
- Use `npm --prefix frontend run dev` for local development.
- Use `npm --prefix frontend run build` to verify the UI.
- Keep shared UI primitives in `frontend/src/components/ui/`.

## Backend rules
- Start the API with `py -m uvicorn physics_diagram.api:app --host 127.0.0.1 --port 8000`.
- The frontend expects the API at `http://127.0.0.1:8000` unless `VITE_API_BASE` overrides it.

## Editing rules
- Prefer minimal, focused changes.
- Do not revert user changes unless explicitly asked.
- Preserve the existing brutalist visual direction for the frontend.

## Shared Agent Memory
- Treat `todo.md` as the active working roadmap for this repo.
- Keep frontend UI changes aligned with the notes in `todo.md` so future agents can continue from the same context.
- Prefer updating this file and `todo.md` before starting larger UI or architecture edits.
