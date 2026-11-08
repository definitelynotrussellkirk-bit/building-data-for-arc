"""Generator for ARC task 9edfc990 / content family be05cee2806f.

Canonical rule: each 4-connected color-0 component touching an original
color-1 cell is recolored to 1; zero components without such contact remain 0.

Version 3 repairs the prior axis contract and semantic coverage while retaining
the canonical dense ten-color distribution.  Every ordinary draw contains both
branches of the discriminator and all ten ARC colors.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "be05cee2806f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "546de66737cf"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Dense ten-color fields containing both zero components adjacent to color 1 "
    "and zero components isolated from color 1; only the adjacent components are absorbed."
)

INVARIANTS = [
    "the input uses every ARC color 0..9",
    "at least one 4-connected zero component touches an original color-1 cell",
    "at least one 4-connected zero component is isolated from every color-1 cell",
]

DEGENERATE_TEXTURES = (
    "no_zero",
    "no_one",
    "all_zero",
    "no_holes",
    "all_holes",
    "single_hole",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-banded", "valid": "10..30"},
    "grid_w": {"type": "int", "default": "difficulty-banded", "valid": "10..30"},
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_OVERRIDES = frozenset((*AXES, "texture"))


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _bounds(difficulty):
    if difficulty == "easy":
        return (10, 14), (10, 14)
    if difficulty in (None, "medium"):
        return (13, 20), (13, 20)
    if difficulty == "hard":
        return (21, 30), (21, 30)
    raise ValueError("difficulty must be easy, medium, hard, or None")


def _validate_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)
    ):
        raise ValueError("grid must be a nonempty rectangular list of exact ARC integers")
    if len(grid) > 30 or len(grid[0]) > 30:
        raise ValueError("grid dimensions may not exceed 30")
    return [row[:] for row in grid]


def _zero_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
    }
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in _CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return components


def analyze_zero_components(grid: Any) -> dict[str, Any]:
    source = _validate_grid(grid)
    height, width = len(source), len(source[0])
    touching: list[list[tuple[int, int]]] = []
    isolated: list[list[tuple[int, int]]] = []
    for component in _zero_components(source):
        touches_one = any(
            0 <= r + dr < height
            and 0 <= c + dc < width
            and source[r + dr][c + dc] == 1
            for r, c in component
            for dr, dc in _CARDINAL
        )
        (touching if touches_one else isolated).append(component)
    return {
        "height": height,
        "width": width,
        "palette": sorted({value for row in source for value in row}),
        "zero_component_count": len(touching) + len(isolated),
        "touching_one_components": len(touching),
        "isolated_components": len(isolated),
        "touching_one_cells": [list(cell) for comp in touching for cell in comp],
        "isolated_cells": [list(cell) for comp in isolated for cell in comp],
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    """Diagnostic Python mirror of the selected Racket authority."""
    source = _validate_grid(grid)
    facts = analyze_zero_components(source)
    output = [row[:] for row in source]
    for r, c in facts["touching_one_cells"]:
        output[r][c] = 1
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"invalid difficulty {difficulty!r}"]
    try:
        facts = analyze_zero_components(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if not 1 <= facts["height"] <= 30 or not 1 <= facts["width"] <= 30:
        errors.append(f"grid shape {facts['height']}x{facts['width']} outside ARC bounds")
    if facts["palette"] != list(range(10)):
        errors.append(f"expected all ten ARC colors, got {facts['palette']}")
    if facts["touching_one_components"] < 1:
        errors.append("need at least one zero component touching color 1")
    if facts["isolated_components"] < 1:
        errors.append("need at least one zero component isolated from color 1")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    source = _validate_grid(grid)
    return {"grid_h": len(source), "grid_w": len(source[0])}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    (h_lo, h_hi), (w_lo, w_hi) = _bounds(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_strict("grid_h", h_lo, h_hi)
    w = ctx.draw_int_strict("grid_w", w_lo, w_hi)
    texture = overrides.get("texture")
    if texture is not None:
        if type(texture) is not str or texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"texture must be one of {DEGENERATE_TEXTURES}")
        return _draw_from_degenerate(texture, h, w)

    rng = ctx.draw_rng("dense-ten-color-field")
    pool = [0, 0, 0, 0, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    coordinates = [(r, c) for r in range(h) for c in range(w)]
    for _attempt in range(256):
        grid = full_grid(h, w, 0)
        for r, c in coordinates:
            grid[r][c] = rng.choice(pool)

        # Guarantee palette coverage without introducing a fixed-location cue.
        witnesses = coordinates[:]
        rng.shuffle(witnesses)
        colors = list(range(10))
        rng.shuffle(colors)
        for (r, c), color in zip(witnesses, colors, strict=False):
            grid[r][c] = color

        if self_check(grid, difficulty=difficulty) == []:
            return grid
    raise AssertionError("could not construct a dense field exercising both canonical branches")


def _draw_from_degenerate(name: str, h: int, w: int) -> list[list[int]]:
    if name in ("no_zero", "no_holes"):
        return [[1 + ((3 * r + 5 * c) % 9) for c in range(w)] for r in range(h)]
    if name == "no_one":
        return [[0 if (r + c) % 4 == 0 else 2 + ((3 * r + 5 * c) % 8) for c in range(w)] for r in range(h)]
    if name in ("all_zero", "all_holes"):
        return full_grid(h, w, 0)
    if name == "single_hole":
        grid = [[2 + ((3 * r + 5 * c) % 8) for c in range(w)] for r in range(h)]
        top, left = h // 2 - 1, w // 2 - 1
        for r in range(top, top + 2):
            for c in range(left, left + 2):
                grid[r][c] = 0
        grid[top][left - 1] = 1
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")
