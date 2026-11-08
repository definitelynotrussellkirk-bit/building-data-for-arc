"""Generator for ``additional_bank:E6`` (26cfe7595a4a).

Rule authority: crop the input to the tight bounding box of every non-zero cell.
The ordinary generator teaches that rule with one compact interior motif while
making all declared controls observable and retaining strict validation.
"""
from __future__ import annotations

from math import ceil
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "26cfe7595a4a"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
# sha256(" ".join(canonical program_solution.split()))[:12]
RULE_HASH = "a6ccad31118b"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Place one compact one-to-three-color motif strictly inside a 0-background "
    "grid. The output is the smallest rectangular crop containing every "
    "non-zero cell. Size, palette, color count, density, and interior position "
    "are independently controlled and observable."
)

INVARIANTS = [
    "background is 0 and all cells are exact ARC colors 0..9",
    "ordinary scenes contain at least two non-zero motif cells",
    "the non-zero bounding box is strictly inside the input grid",
    "motif_size exactly controls the square bounding-box height and width",
    "color_count is the exact number of distinct non-zero colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DENSITIES = ("sparse", "compact", "dense")
POSITION_BIASES = ("random", "near_top", "near_bottom", "center")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-shaped 6..30",
        "valid": "6..30",
        "doc": "Exactly observable as len(grid).",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-shaped 6..30",
        "valid": "6..30",
        "doc": "Exactly observable as len(grid[0]).",
    },
    "motif_size": {
        "type": "int",
        "default": "rng 2..4",
        "valid": "2..4",
        "doc": "Exact height and width of the tight non-zero bounding box.",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng helpful palette",
        "valid": "|".join(PALETTE_KINDS),
    },
    "color_count": {
        "type": "int",
        "default": "rng 1..3",
        "valid": "1..3",
        "doc": "Exact number of distinct non-zero motif colors.",
    },
    "density": {
        "type": "str",
        "default": "rng sparse|compact|dense",
        "valid": "|".join(DENSITIES),
    },
    "position_bias": {
        "type": "str",
        "default": "rng random|near_top|near_bottom|center",
        "valid": "|".join(POSITION_BIASES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (1, 2, 4, 7, 9),
    "cool": (1, 3, 5, 6, 8),
    "varied": (2, 3, 4, 6, 7, 9),
}
_DENSITY_FRACTIONS = {"sparse": 0.45, "compact": 0.70, "dense": 1.0}


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _draw_dimension(ctx, name: str) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, 6, 30)
    bands = {
        "easy": (6, 9),
        "medium": (9, 16),
        "hard": (16, 30),
    }
    lo, hi = bands.get(ctx.difficulty, (6, 16))
    return ctx.draw_int_strict(name, lo, hi)


def _choose_colors(ctx, palette_kind: str, count: int) -> tuple[int, ...]:
    palette = _PALETTES[palette_kind]
    rng = ctx.draw_rng("motif_colors")
    colors = tuple(rng.sample(list(palette), count))
    # Record the value under a stable public draw label without exposing a dead axis.
    ctx.drawn_store["motif_colors"] = colors
    return colors


def _position(ctx, h: int, w: int, size: int, bias: str) -> tuple[int, int]:
    max_r = h - size - 1
    max_c = w - size - 1
    if max_r < 1 or max_c < 1:
        raise ValueError("motif_size needs a one-cell background margin")
    rng = ctx.draw_rng("motif_position")
    if bias == "near_top":
        return 1, rng.randint(1, max_c)
    if bias == "near_bottom":
        return max_r, rng.randint(1, max_c)
    if bias == "center":
        return max(1, min(max_r, (h - size) // 2)), max(1, min(max_c, (w - size) // 2))
    return rng.randint(1, max_r), rng.randint(1, max_c)


def _motif_cells(ctx, size: int, color_count: int, density: str) -> list[tuple[int, int]]:
    total = size * size
    target = max(2, color_count, ceil(total * _DENSITY_FRACTIONS[density]))
    target = min(total, target)
    forced = [(0, 0), (size - 1, size - 1)]
    remaining = [(r, c) for r in range(size) for c in range(size) if (r, c) not in forced]
    rng = ctx.draw_rng("motif_mask")
    rng.shuffle(remaining)
    cells = forced + remaining[: target - len(forced)]
    # Ensure every requested color is representable even at the smallest size.
    if len(cells) < color_count:
        cells += remaining[target - len(forced): target - len(forced) + color_count - len(cells)]
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_dimension(ctx, "grid_h")
    w = _draw_dimension(ctx, "grid_w")
    size = ctx.draw_int_strict("motif_size", 2, 4)
    if size > h - 2 or size > w - 2:
        raise ValueError("motif_size must leave a one-cell margin in both dimensions")
    palette_kind = str(ctx.draw_choice("palette_kind", PALETTE_KINDS))
    color_count = ctx.draw_int_strict("color_count", 1, 3)
    density = str(ctx.draw_choice("density", DENSITIES))
    bias = str(ctx.draw_choice("position_bias", POSITION_BIASES))
    colors = _choose_colors(ctx, palette_kind, color_count)
    rr, rc = _position(ctx, h, w, size, bias)
    cells = _motif_cells(ctx, size, color_count, density)

    grid = full_grid(h, w, 0)
    # Put each requested color into the first positions, then continue a spatial
    # checker. This makes color_count exact and keeps motifs nontrivial.
    for index, (r, c) in enumerate(cells):
        color = colors[index] if index < color_count else colors[(r + c + index) % color_count]
        grid[rr + r][rc + c] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        return ["grid must be rectangular 1..30 with exact integer colors 0..9"]
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    errors: list[str] = []
    if len(cells) < 2:
        errors.append("at least two non-zero cells required")
    if not cells:
        return errors
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    if r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1:
        errors.append("non-zero bounding box must not touch the grid border")
    return errors
