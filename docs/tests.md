# `tests/test_models.py` — Model Validation Tests

## What It Does
Tests the Pydantic models to ensure they correctly validate physics data, reject invalid inputs, and enforce referential integrity.

## Test Classes
| Class | Tests | What It Validates |
|-------|-------|-------------------|
| `TestValidModels` | 5 | Valid incline/pulley data parses, surface type detection, default values, optional mass |
| `TestReferentialIntegrity` | 4 | Invalid object IDs in placements, forces, and friction raise `ValidationError` |
| `TestEnumValidation` | 4 | Invalid object type, force type, direction, and surface type are rejected |
| `TestProblemInput` | 3 | Valid input, too-short text, and empty text |

## Dependencies
- `pytest` — test runner
- `pydantic` — `ValidationError` for assertion checks

---

# `tests/test_parser.py` — Parser Tests

## What It Does
Tests the AI parser using **mocked** Gemini API responses. Ensures the parser correctly handles valid output, invalid JSON, schema violations, and API failures.

## How It Works
Uses `unittest.mock.patch` to replace `_call_gemini` with controlled outputs:
- Returns valid JSON → parser returns `ParsedPhysicsProblem`
- Returns invalid JSON → raises `ParsingError`
- Returns JSON that fails schema validation → raises `ParsingError`
- Raises `ConnectionError` → raises `ParsingError`

No actual AI API calls are made during testing.

## Test Cases
| Test | Input | Expected |
|------|-------|----------|
| `test_successful_parse` | Valid JSON string | `ParsedPhysicsProblem` instance |
| `test_invalid_json` | `"not json"` | `ParsingError` |
| `test_invalid_schema` | `"{}"` (missing fields) | `ParsingError` |
| `test_api_failure` | `ConnectionError` | `ParsingError` |
| `test_correct_forces` | Valid JSON with 3 forces | 3 forces in result |

## Dependencies
- `pytest` — test runner
- `unittest.mock` — `@patch` for mocking API calls

---

# `tests/test_diagrams.py` — Diagram Generator Tests

## What It Does
Tests all 4 diagram generators to verify they produce valid SVG output containing expected elements (forces, labels, structural components).

## How It Works
Each test class creates a sample `ParsedPhysicsProblem` and passes it to the corresponding generator function. Tests then check the SVG string for expected content.

## Test Classes
| Class | Generator | Checks |
|-------|-----------|--------|
| `TestInclineDiagram` | `generate_incline_diagram` | SVG tags, force arrow labels, block element, angle value |
| `TestHorizontalDiagram` | `generate_horizontal_diagram` | SVG tags, force labels (mg, N, F), mass label |
| `TestPulleyDiagram` | `generate_pulley_diagram` | SVG tags, both mass labels, pulley circle, tension label |
| `TestVerticalDiagram` | `generate_vertical_diagram` | SVG tags, mass label, elevator rectangle, gravity label |

## Dependencies
- `pytest` — test runner
- `app.diagrams.*` — all diagram generators
- `app.models` — `ParsedPhysicsProblem` for test data
