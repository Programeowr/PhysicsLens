"""Rule-based natural-language physics force diagram generator."""


def solve_and_render(text: str, output_path: str):
    """Lazily import rendering dependencies for the package convenience API."""
    from .pipeline import solve_and_render as _solve_and_render
    return _solve_and_render(text, output_path)


__all__ = ["solve_and_render"]
