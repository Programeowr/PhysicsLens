# PhysicsLens — Physics Question to Force Diagram

PhysicsLens turns supported natural-language physics questions into deterministic, labeled SVG force diagrams. It is fully rule-based: it uses no LLMs or external APIs at runtime.

Supported scenarios are inclined planes, horizontal friction, Atwood pulleys, and projectile motion.

## Requirements

- Windows PowerShell
- Python 3.14 (the project was verified with Python 3.14)

## Install

From the project root, create a virtual environment and install dependencies:

```powershell
py -3.14 -m venv .venv314
& .\.venv314\Scripts\python.exe -m pip install -r physics_diagram\requirements.txt
& .\.venv314\Scripts\python.exe -m spacy download en_core_web_sm
```

> You do not need to activate the environment. The commands below invoke its Python executable directly.

## Start the API

```powershell
& .\.venv314\Scripts\python.exe -m uvicorn physics_diagram.api:app --reload
```

Open the interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Generate a diagram

The `/solve` endpoint returns JSON, including a Base64-encoded SVG. The `/solve.svg` endpoint returns the SVG image directly.

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
