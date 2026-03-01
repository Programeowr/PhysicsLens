# `app/prompts.py` — AI Prompt Templates

## What It Does
Contains the carefully crafted prompts sent to the Gemini AI for both text-based and image-based physics problem parsing.

## Why It Exists
The quality of AI output depends heavily on the prompt. This module:
- Provides a strict JSON schema so the AI knows exactly what format to return
- Includes **4 few-shot examples** so the AI understands the pattern
- Specifies rules (e.g., always include gravity, calculate magnitudes)
- Separates prompt logic from parsing logic for cleaner code

## How It Works

### `FEW_SHOT_EXAMPLES`
A string containing 4 complete input→output examples:

| # | Scenario | Key Learning |
|---|----------|-------------|
| 1 | Block on 30° incline | Inclined plane, gravity + normal forces |
| 2 | Box pushed on rough surface | Horizontal, friction + applied force |
| 3 | Atwood machine | Pulley, two masses, tension forces |
| 4 | Person in elevator | Vertical scenario, acceleration |

### `build_prompt(problem_text)`
Builds the full prompt for **text** problems. Includes:
1. Role assignment ("You are a physics semantic parser")
2. JSON schema with all field descriptions and allowed enum values
3. Rules (always include gravity, calculate mg, etc.)
4. Few-shot examples
5. The actual problem text to parse

### `build_image_prompt()`
Builds the prompt for **image** problems. Same schema and rules, but adds:
- Instructions to OCR/read the image first
- Handle handwritten, printed, and screenshot inputs
- Parse only the first problem if multiple are present

## Dependencies
- None (pure Python string formatting)
