"""Generator for ``b47adc50b675`` — normalize one green shape to the origin.

The input contains exactly one connected green component on a black canvas.
The component is deliberately offset from both the top and left borders.  The
canonical rule discards the absolute position and paints the same normalized
shape with its bounding-box top-left at ``(0, 0)`` on a fresh black canvas of
the same dimensions.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "b47adc50b675"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "df98ae7438e1"

SUMMARY = (
    "Place one 4-connected green(3) component, four to six cells large, on a "
    "black(0) grid. The component is offset from both top and left borders. "
    "Translate every green cell by the negative of the component bounding-box "
    "top-left so the same shape begins at row 0 and column 0; preserve the "
    "input grid dimensions and clear every other cell to black."
)

INVARIANTS = [
    "the grid is 5..14 rows by 6..16 columns with background color 0",
    "there is exactly one 4-connected color-3 component",
    "the component has four to six cells and a 2x3 or 3x2 bounding box",
    "the component bounding box starts strictly below row 0 and right of column 0",
    "the output preserves dimensions and the component shape while removing position",
]

COUNTER_HYPOTHESES = [
    "return a fixed marker, count, or color swatch instead of the whole shape",
    "copy the input unchanged or move only one edge of the component",
    "move the component to a fixed non-origin position",
    "infer the answer from canvas size, placement, or a texture cue",
    "use a fixed canonical shape instead of preserving the input occupancy",
]

EXAMPLES_NEEDED = 3
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Every 4-connected subset of a 2x3 bounding box that touches all four bbox
# sides and has four through six cells.  This is the complete finite morphology
# codomain for the non-transposed orientation; ``transpose=True`` supplies the
# corresponding 3x2 forms.  It includes all published train/test morphologies.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
)
_SHAPE_TO_ID = {frozenset(shape): index for index, shape in enumerate(_SHAPES)}

AXES = {
    "shape_id": {
        "type": "int",
        "default": "uniform over the complete 2x3 connected-shape codomain",
        "valid": "0..14",
    },
    "transpose": {
        "type": "bool",
        "default": "uniform false|true when compatible with explicit bounds",
        "valid": "false|true",
    },
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed within 5..14",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed within 6..16",
        "valid": "6..16",
    },
    "row_offset": {
        "type": "int",
        "default": "uniform legal positive bbox row",
        "valid": "1..h-2",
    },
    "col_offset": {
        "type": "int",
        "default": "uniform legal positive bbox column",
        "valid": "1..w-2",
    },
}


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for label, lower, upper in (
        ("shape_id", 0, 14),
        ("grid_h", 5, 14),
        ("grid_w", 6, 16),
        ("row_offset", 1, 12),
        ("col_offset", 1, 14),
    ):
        value = overrides.get(label)
        if value is not None and (
            type(value) is not int or not lower <= value <= upper
        ):
            raise ValueError(f"{label} must be an integer in [{lower}, {upper}]")
    value = overrides.get("transpose")
    if value is not None and type(value) is not bool:
        raise ValueError("transpose must be a boolean")


def _transpose(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return tuple(sorted((col, row) for row, col in shape))


def _shape_extent(transpose: bool) -> tuple[int, int]:
    return (3, 2) if transpose else (2, 3)


def _compatible_transposes(overrides) -> tuple[bool, ...]:
    """Return orientations that can satisfy all explicit dimension/offset data."""
    grid_h = overrides.get("grid_h")
    grid_w = overrides.get("grid_w")
    row = overrides.get("row_offset")
    col = overrides.get("col_offset")
    max_h = grid_h if grid_h is not None else 14
    max_w = grid_w if grid_w is not None else 16
    min_row = row if row is not None else 1
    min_col = col if col is not None else 1
    legal = tuple(
        transpose
        for transpose in (False, True)
        if min_row + _shape_extent(transpose)[0] <= max_h
        and min_col + _shape_extent(transpose)[1] <= max_w
    )
    requested = overrides.get("transpose")
    if requested is not None:
        if requested not in legal:
            raise ValueError(
                "transpose is incompatible with the requested grid dimensions "
                "and component offsets"
            )
        return (requested,)
    if not legal:
        raise ValueError(
            "requested grid dimensions and offsets leave no legal component orientation"
        )
    return legal


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

    if overrides.get("shape_id") is not None:
        shape_id = ctx.draw_int("shape_id", 0, len(_SHAPES) - 1)
    else:
        lesson_group = sample_index // EXAMPLES_NEEDED
        lesson_phase = sample_index % EXAMPLES_NEEDED
        base_shape = stable_rng(
            seed, f"{TASK_ID}|{lesson_group}|shape_schedule", VERSION
        ).randrange(len(_SHAPES))
        scheduled_shape = (base_shape + 5 * lesson_phase) % len(_SHAPES)
        shape_id = ctx.draw_choice("shape_id", (scheduled_shape,))
    transpose = ctx.draw_choice("transpose", _compatible_transposes(overrides))
    shape = _transpose(_SHAPES[shape_id]) if transpose else _SHAPES[shape_id]
    shape_h, shape_w = _shape_extent(transpose)

    requested_row = overrides.get("row_offset")
    requested_col = overrides.get("col_offset")
    min_h = max(5, (requested_row if requested_row is not None else 1) + shape_h)
    min_w = max(6, (requested_col if requested_col is not None else 1) + shape_w)
    h = ctx.draw_int_diff("grid_h", min_h, 14)
    w = ctx.draw_int_diff("grid_w", min_w, 16)
    def scheduled_offset(label: str, upper: int, salt: str) -> int:
        if overrides.get(label) is not None:
            return ctx.draw_int(label, 1, upper)
        phase = sample_index % EXAMPLES_NEEDED
        if phase == 0:
            value = 1
        elif phase == 1:
            value = upper
        else:
            value = ctx.draw_rng(salt).randint(1, upper)
        return ctx.draw_choice(label, (value,))

    row_offset = scheduled_offset("row_offset", h - shape_h, "row_offset_schedule")
    col_offset = scheduled_offset("col_offset", w - shape_w, "col_offset_schedule")

    grid = full_grid(h, w, 0)
    for row, col in shape:
        grid[row_offset + row][col_offset + col] = 3
    return grid


def _coerce_grid(grid) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a non-empty rectangular grid")
    rows: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            if not row or not row.isdigit():
                raise ValueError("string rows must contain digits")
            rows.append([int(value) for value in row])
        elif isinstance(row, (list, tuple)) and row:
            rows.append(list(row))
        else:
            raise ValueError("expected non-empty list, tuple, or digit-string rows")
    if len({len(row) for row in rows}) != 1:
        raise ValueError("expected a rectangular grid")
    return rows


def _color_components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == color
    }
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        cells = [start]
        while stack:
            row, col = stack.pop()
            for next_cell in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if next_cell in unseen:
                    unseen.remove(next_cell)
                    stack.append(next_cell)
                    cells.append(next_cell)
        components.append(sorted(cells))
    return components


def _normalized(cells) -> frozenset[tuple[int, int]]:
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def _inspect(grid) -> tuple[list[list[int]], list[tuple[int, int]]]:
    normalized_grid = _coerce_grid(grid)
    h, w = len(normalized_grid), len(normalized_grid[0])
    if not (5 <= h <= 14 and 6 <= w <= 16):
        raise ValueError(f"expected dimensions within 5..14 by 6..16, got {h}x{w}")
    if any(
        type(value) is not int or value not in (0, 3)
        for row in normalized_grid
        for value in row
    ):
        raise ValueError("only background color 0 and component color 3 are allowed")
    components = _color_components(normalized_grid, 3)
    if len(components) != 1:
        raise ValueError(f"expected exactly one color-3 component, got {len(components)}")
    cells = components[0]
    if not 4 <= len(cells) <= 6:
        raise ValueError(f"expected four to six component cells, got {len(cells)}")
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_row = max(row for row, _ in cells)
    max_col = max(col for _, col in cells)
    if min_row == 0 or min_col == 0:
        raise ValueError("component bounding box must be offset from both top and left borders")
    bbox = (max_row - min_row + 1, max_col - min_col + 1)
    if bbox not in ((2, 3), (3, 2)):
        raise ValueError(f"expected a 2x3 or 3x2 component bounding box, got {bbox[0]}x{bbox[1]}")
    return normalized_grid, cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes outside the canonical one-component normalization lesson."""
    del difficulty, meta
    try:
        _inspect(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def observe_overrides(grid) -> dict[str, int | bool]:
    """Recover every exact public axis from a returned grid."""
    normalized_grid, cells = _inspect(grid)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    shape = _normalized(cells)
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    transpose = (height, width) == (3, 2)
    canonical_shape = frozenset((col, row) for row, col in shape) if transpose else shape
    if canonical_shape not in _SHAPE_TO_ID:
        raise ValueError("component morphology is outside the declared shape_id codomain")
    return {
        "shape_id": _SHAPE_TO_ID[canonical_shape],
        "transpose": transpose,
        "grid_h": len(normalized_grid),
        "grid_w": len(normalized_grid[0]),
        "row_offset": min_row,
        "col_offset": min_col,
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only Python mirror; the canonical Racket program is authoritative."""
    normalized_grid, cells = _inspect(grid)
    out = full_grid(len(normalized_grid), len(normalized_grid[0]), 0)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    for row, col in cells:
        out[row - min_row][col - min_col] = 3
    return out
