"""Stage-level pipeline exceptions for PhysicsLens.

Each exception carries the stage name, a human-readable message, and a stable
``error_code`` string that API handlers can forward directly to callers without
leaking internal details.
"""

from __future__ import annotations


class PhysicsLensError(Exception):
    """Base class for all pipeline errors."""

    error_code: str = "internal_error"

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.detail = detail or message


class ParseError(PhysicsLensError):
    """Raised when the parser cannot produce a usable ParseResult."""

    error_code = "parse_error"


class ValidationError(PhysicsLensError):
    """Raised when a ParseResult fails semantic validation."""

    error_code = "validation_error"


class SolveError(PhysicsLensError):
    """Raised when the physics solver cannot produce a ForceSolution."""

    error_code = "solver_error"


class UnsupportedScenarioError(SolveError):
    """Raised when no solver exists for the classified scenario."""

    error_code = "unsupported_scenario"


class LayoutError(PhysicsLensError):
    """Raised when scene-graph layout fails."""

    error_code = "layout_error"


class RenderError(PhysicsLensError):
    """Raised when SVG rendering fails."""

    error_code = "render_error"


class NeedsClärificationError(PhysicsLensError):
    """Raised when required parse slots are missing; caller may retry with more text."""

    error_code = "needs_clarification"

    def __init__(self, message: str, *, missing_fields: list[str] | None = None) -> None:
        super().__init__(message, detail=message)
        self.missing_fields: list[str] = missing_fields or []
