# PhysicsLens — Physics Question to Force Diagram

PhysicsLens turns supported natural-language physics questions into labeled SVG force diagrams. Parsing uses the local Ollama `qwen2.5:7b` model; no cloud API is used.

The rendering path now builds a `SceneGraph`, applies a dedicated layout pass, and then renders pure SVG from structured scene data. This makes diagram generation more modular, scalable, and easier to extend.

Supported scenarios are inclined planes, horizontal friction, Atwood pulleys, and projectile motion.

## Requirements

- Windows PowerShell
- Python 3.14 (the project was verified with Python 3.14)
- [Ollama](https://ollama.com/) with `qwen2.5:7b`

## Install

From the project root, create a virtual environment and install dependencies:

```powershell
py -3.14 -m venv .venv314
& .\.venv314\Scripts\python.exe -m pip install -r physics_diagram\requirements.txt
ollama pull qwen2.5:7b
```

> You do not need to activate the environment. The commands below invoke its Python executable directly.
> Ollama must be running before the API receives a request. The parser uses `http://127.0.0.1:11434` and `qwen2.5:7b` by default. Override them with `OLLAMA_BASE_URL` and `OLLAMA_MODEL` environment variables if needed.

## Start the API

```powershell
& .\.venv314\Scripts\python.exe -m uvicorn physics_diagram.api:app --reload
```

Open the interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Generate a diagram

The `/solve` endpoint returns JSON, including a Base64-encoded SVG. The `/solve.svg` endpoint returns the SVG image directly.

Under the hood, the pipeline now uses:
- `scene_graph.build_scene_graph()` to create a generic drawing model,
- `layout.layout_scene()` to position objects, forces, and annotations,
- `svg_renderer.render_scene()` to emit the final SVG markup.

In a second PowerShell window, save a diagram file with:

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

Open `diagram.svg` in a browser to view the force diagram.

## Run tests

```powershell
& .\.venv314\Scripts\python.exe -m pytest physics_diagram\tests -q -p no:cacheprovider
```

## Example question

```text
A box of mass 5kg is placed on a frictionless inclined plane with 30 degree inclination. How much force is required to keep it at rest?
```

The required holding force is 24.5 N.
