"""Generator for de6d50ef73a3 — move the global nonzero crop top-left.

The exact rule takes the tight bounding box of every nonzero cell, preserves all
colors and internal zeros, and pastes that crop at canvas coordinate (0, 0).
Canonical examples show that the nonzero support need not be monochrome or even
4-connected, so validation deliberately follows the global-crop authority.
"""
from __future__ import annotations

from collections.abc import Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "de6d50ef73a3"
VERSION = "3.0.0"
TASK_ID = "de6d50ef73a3"
SUMMARY = (
    "Tightly crop the global nonzero pattern, preserving all colors and internal "
    "zeros, then paste it at the top-left of an equal-size zero canvas."
)

INVARIANTS = [
    "background is 0 and cells are exact integer colors 0..9",
    "the global nonzero support contains at least two cells",
    "the tight nonzero bounding box does not already begin at (0,0)",
    "the crop may be multicolor or disconnected and its internal layout is preserved",
    "output keeps the original canvas size",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
# Diagnostic names remain documented for audits but are not label-preserving
# generation controls and therefore are not advertised as valid textures.
DEGENERATE_TEXTURES = ("object_at_top_left", "multi_object", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed rng 5..18", "valid": "5..18"},
    "grid_w": {"type": "int", "default": "difficulty-skewed rng 5..22", "valid": "5..22"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
    },
    "shape_choice": {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_size": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "position_bias": {
        "type": "str",
        "default": "single_offset_pattern",
        "valid": "single_offset_pattern",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "alias for palette_size",
        "valid": "1..3",
    },
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_PALETTE_POOLS = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (1, 2, 3, 4),
    "cool": (5, 6, 7, 8, 9),
    "varied": (9, 2, 6, 1, 8, 3, 7, 4, 5),
}
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 3)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1), (3, 2)),
    ((0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
)


def _normalize_overrides(overrides: dict) -> dict:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    normalized = dict(overrides)
    texture = normalized.get("texture")
    palette_kind = normalized.get("palette_kind")
    if texture is not None and texture not in HELPFUL_TEXTURES:
        raise ValueError(
            f"texture override {texture!r} is not label-preserving; "
            f"expected one of {HELPFUL_TEXTURES}"
        )
    if texture is not None and palette_kind is not None and texture != palette_kind:
        raise ValueError(
            f"conflicting palette_kind={palette_kind!r} and texture={texture!r}"
        )
    if texture is not None:
        normalized["palette_kind"] = texture
    elif palette_kind is not None:
        normalized["texture"] = palette_kind

    palette_size = normalized.get("palette_size")
    distinct = normalized.get("n_distinct_colors")
    if palette_size is not None and distinct is not None and palette_size != distinct:
        raise ValueError(
            f"conflicting palette_size={palette_size!r} and "
            f"n_distinct_colors={distinct!r}"
        )
    if distinct is not None:
        normalized["palette_size"] = distinct
    elif palette_size is not None:
        normalized["n_distinct_colors"] = palette_size

    # draw_int_diff intentionally retains legacy coercion, so reject non-exact
    # integer dimension overrides before they reach it.
    for name in ("grid_h", "grid_w"):
        if name in normalized and normalized[name] is not None and type(normalized[name]) is not int:
            raise TypeError(f"{name} override must be an exact integer (not bool)")
    return normalized


def _grid_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid:
        return ["empty grid"], 0, 0
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be nonempty lists"], 0, 0
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"], len(grid), width

    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an exact integer color in 0..9")
    return errors, len(grid), width


def _nonzero_cells(grid: Sequence[Sequence[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _components(grid) -> list[list[tuple[int, int]]]:
    """Return 4-connected nonzero components, ignoring color boundaries."""
    errors, height, width = _grid_errors(grid)
    if errors:
        return []
    occupied = set(_nonzero_cells(grid))
    components: list[list[tuple[int, int]]] = []
    while occupied:
        start = min(occupied)
        occupied.remove(start)
        stack = [start]
        cells: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in occupied and 0 <= neighbor[0] < height and 0 <= neighbor[1] < width:
                    occupied.remove(neighbor)
                    stack.append(neighbor)
        components.append(sorted(cells))
    return components


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate a nontrivial global-crop lesson without imposing connectivity."""
    errors, height, width = _grid_errors(grid)
    if errors:
        return errors
    if difficulty not in _VALID_DIFFICULTIES:
        errors.append(f"difficulty must be one of easy, medium, hard or None; got {difficulty!r}")
    if not 2 <= height <= 30 or not 2 <= width <= 30:
        errors.append("canvas dimensions must each be in 2..30")

    cells = _nonzero_cells(grid)
    if not cells:
        errors.append("input must contain at least one nonzero cell")
        return errors
    if len(cells) == 1:
        errors.append("single-cell crop is an uninformative degenerate")
    min_row = min(r for r, _ in cells)
    min_col = min(c for _, c in cells)
    if min_row == 0 and min_col == 0:
        errors.append("nonzero crop already begins at the top-left origin")
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the exact canonical global-crop rule."""
    errors, height, width = _grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    cells = _nonzero_cells(grid)
    if not cells:
        return full_grid(height, width, 0)
    min_row = min(r for r, _ in cells)
    max_row = max(r for r, _ in cells)
    min_col = min(c for _, c in cells)
    max_col = max(c for _, c in cells)
    output = full_grid(height, width, 0)
    for r in range(min_row, max_row + 1):
        for c in range(min_col, max_col + 1):
            value = grid[r][c]
            if value != 0:
                output[r - min_row][c - min_col] = value
    return output


def _paint_shape(
    shape: Sequence[tuple[int, int]],
    colors: Sequence[int],
    rng,
) -> dict[tuple[int, int], int]:
    order = list(shape)
    rng.shuffle(order)
    painted: dict[tuple[int, int], int] = {}
    # Seed every requested color once, then fill the remaining occupied cells.
    for cell, color in zip(order, colors):
        painted[cell] = color
    for cell in order[len(colors) :]:
        painted[cell] = rng.choice(list(colors))
    return painted


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of easy, medium, hard or None; got {difficulty!r}"
        )
    normalized = _normalize_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=normalized,
    )

    height = ctx.draw_int_diff("grid_h", 5, 18)
    width = ctx.draw_int_diff("grid_w", 5, 22)
    shape_choice = ctx.draw_int_strict("shape_choice", 0, 3)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    ctx.draw_choice("texture", (palette_kind,))
    palette_size = ctx.draw_int_strict("palette_size", 1, 3)
    ctx.draw_choice("n_distinct_colors", (palette_size,))
    ctx.draw_choice("position_bias", ("single_offset_pattern",))
    ctx.draw_choice("density", ("sparse",))

    shape = _SHAPES[shape_choice]
    shape_height = max(r for r, _ in shape) + 1
    shape_width = max(c for _, c in shape) + 1
    if height < shape_height + 1 or width < shape_width + 1:
        raise ValueError(
            f"grid_h/grid_w {height}x{width} cannot fit shape_choice={shape_choice} "
            "with a nonzero offset"
        )

    color_rng = ctx.draw_rng("colors")
    colors = color_rng.sample(list(_PALETTE_POOLS[palette_kind]), palette_size)
    painted = _paint_shape(shape, colors, ctx.draw_rng("paint"))

    position_rng = ctx.draw_rng("position")
    top = position_rng.randint(1, height - shape_height)
    left = position_rng.randint(1, width - shape_width)
    grid = full_grid(height, width, 0)
    for (r, c), color in painted.items():
        grid[top + r][left + c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    return grid
