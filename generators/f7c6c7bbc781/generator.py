"""Generator for ARC task 85c4e7cd / f7c6c7bbc781.

The input is a clean onion of concentric rectangular rings.  The output keeps
all geometry fixed and reverses the ordered ring-color sequence: the outermost
ring receives the innermost color, the next ring receives the next-to-innermost
color, and so on.

The canonical five inputs are even square onions of sizes 6, 8, 10, 12, and 14
with a distinct nonzero color on every ring.  Default generation preserves that
linked manifold with a deliberate square prior in every difficulty band while
also adding lawful even rectangles.  Odd dimensions are excluded because the
canonical Racket rule indexes exactly ``min(h, w) / 2`` colors.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f7c6c7bbc781"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "d13744bc8c60"

SUMMARY = (
    "Generate a clean even-sized square or rectangle filled by concentric "
    "rings. Every ring has a distinct color from 1..9. The Racket rule keeps "
    "the geometry and reverses the ring-color order (outermost <-> innermost). "
    "A controlled square prior covers the exact canonical sizes 6, 8, 10, 12, "
    "and 14 in their corresponding difficulty bands; the remaining draws add "
    "lawful even rectangular extrapolations."
)

INVARIANTS = [
    "the input is a non-empty rectangular grid with even height and width",
    "height and width are chosen from 4,6,8,10,12,14,16,18",
    "each cell equals the color of its Chebyshev-distance ring",
    "every ring color is a distinct nonzero ARC color from 1..9",
    "there are at least two rings, so reversing the colors changes the grid",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_EVEN_SIZES = (4, 6, 8, 10, 12, 14, 16, 18)
_CANONICAL_SIZES = frozenset((6, 8, 10, 12, 14))
_BAND_SIZES = {
    "easy": (4, 6, 8),
    "medium": (8, 10, 12, 14),
    "hard": (14, 16, 18),
}
_CANONICAL_BY_BAND = {
    "easy": (6, 8),
    "medium": (10, 12),
    "hard": (14,),
}
_CANONICAL_PRIOR = 0.40

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware even size with a canonical-square prior",
        "valid": "4|6|8|10|12|14|16|18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware even size with a canonical-square prior",
        "valid": "4|6|8|10|12|14|16|18",
    },
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and (type(value) is not int or value not in _EVEN_SIZES):
            raise ValueError(
                f"{label} must be one of {','.join(map(str, _EVEN_SIZES))}"
            )


def _build_onion(height: int, width: int, colors: tuple[int, ...] | list[int]):
    grid = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            depth = min(row, col, height - 1 - row, width - 1 - col)
            grid[row][col] = int(colors[depth])
    return grid


def _ring_colors(grid) -> list[int]:
    ring_count = min(len(grid), len(grid[0])) // 2
    return [int(grid[depth][depth]) for depth in range(ring_count)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete onion grammar, not only its diagonal cue."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be non-empty lists"]

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors: list[str] = []
    height = len(grid)
    if height not in _EVEN_SIZES:
        errors.append(f"grid height must be one of {_EVEN_SIZES}, got {height}")
    if width not in _EVEN_SIZES:
        errors.append(f"grid width must be one of {_EVEN_SIZES}, got {width}")
    if errors:
        return errors

    bad_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is not int or not 1 <= value <= 9
    ]
    if bad_cells:
        row, col, value = bad_cells[0]
        errors.append(
            f"all cells must be integer colors 1..9; got {value!r} at {row},{col}"
        )
        return errors

    colors = _ring_colors(grid)
    if len(colors) < 2:
        errors.append("the onion must contain at least two rings")
    if len(set(colors)) != len(colors):
        errors.append(f"ring colors must be pairwise distinct, got {colors}")

    mismatch = None
    for row in range(height):
        for col in range(width):
            depth = min(row, col, height - 1 - row, width - 1 - col)
            expected = colors[depth]
            if grid[row][col] != expected:
                mismatch = (row, col, expected, grid[row][col])
                break
        if mismatch is not None:
            break
    if mismatch is not None:
        row, col, expected, actual = mismatch
        errors.append(
            "grid is not a clean concentric-ring onion: "
            f"cell {row},{col} should be ring color {expected}, got {actual}"
        )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def rule_mirror(grid):
    """Python test mirror of the Racket rule; never used as output authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid onion: " + "; ".join(errors))
    return _build_onion(len(grid), len(grid[0]), list(reversed(_ring_colors(grid))))


def canonical_profile_signature(grid):
    """Strict linked empirical-manifold signature for the five canonical inputs."""
    if self_check(grid):
        return None
    height, width = len(grid), len(grid[0])
    if height == width and height in _CANONICAL_SIZES:
        return (height, width, tuple(_ring_colors(grid)))
    return None


def is_canonical_profile(grid) -> bool:
    return canonical_profile_signature(grid) is not None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(overrides.get(label) is not None for label in AXES)

    canonical_size = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _CANONICAL_PRIOR:
            canonical_size = ctx.draw_choice(
                f"canonical_size|{band}", _CANONICAL_BY_BAND[band]
            )

    if canonical_size is not None:
        height = ctx.draw_choice("grid_h", (canonical_size,))
        width = ctx.draw_choice("grid_w", (canonical_size,))
    else:
        height_options = (
            _EVEN_SIZES
            if overrides.get("grid_h") is not None
            else _BAND_SIZES[band]
        )
        width_options = (
            _EVEN_SIZES
            if overrides.get("grid_w") is not None
            else _BAND_SIZES[band]
        )
        height = ctx.draw_choice("grid_h", height_options)
        width = ctx.draw_choice("grid_w", width_options)

    ring_count = min(height, width) // 2
    colors = ctx.draw_distinct_colors(
        "ring_colors", n=ring_count, exclude={0}
    )
    grid = _build_onion(height, width, colors)
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid onion: " + "; ".join(errors))
    return grid
