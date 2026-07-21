"""Validation gate for parsed scenarios."""

from .schema import ParseResult


def validate(result: ParseResult) -> ParseResult:
    """Return incomplete parses unchanged; callers must not solve them."""
    return result
