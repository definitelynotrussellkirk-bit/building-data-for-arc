"""Input generator for "Control cell chooses OR, XOR, or AND".

The selected Racket rule is unchanged and remains the label authority.  Inputs
contain one control cell at (0, 0), one connected color-1 operand, and one
connected color-2 operand.  Each operand is cropped to its own bounding box;
the control chooses union (3), symmetric difference (4), or intersection (5)
of those normalized masks.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3020cc038f3f"
TASK_ID = GENERATOR_ID
RULE_HASH = "d73f3f4b1c32"
VERSION = "4.0.0"
SUMMARY = (
    "A 7..9 by 9..11 zero-background grid has one control at (0,0): "
    "3=union, 4=XOR, 5=intersection.  Separate connected color-1 and color-2 "
    "polyominoes (3..6 cells) are bbox-normalized before the operation.  Their "
    "normalized masks may partially overlap or be identical; the result is "
    "painted color 8 on the maximum operand bounding box (or [[0]] if empty)."
)

INVARIANTS = [
    "the only control-colored cell is (0,0), with value 3, 4, or 5",
    "colors 1 and 2 each form one connected 3..6-cell polyomino",
    "operand bounding boxes are separated by at least one blank row or column",
    "normalized operands are either partially overlapping or identical",
    "control and normalized-shape relation are sampled independently",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted 7..9; 7/8 favored for canonical profile support",
        "valid": "7..9",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted 9..11; 10 favored for canonical profile support",
        "valid": "9..11",
    },
    "ctrl": {"type": "int", "default": "uniform 3..5", "valid": "3..5"},
    "overlap_kind": {
        "type": "str",
        "default": "weighted partial|identical",
        "valid": "partial|identical",
    },
}

# Every value and Cartesian combination in AXES is constructively supported in
# every difficulty band.  Keep this explicit so override rejection is strict.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _normalize(cells):
    cells = frozenset(cells)
    if not cells:
        return frozenset()
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r - top, c - left) for r, c in cells)


def _extent(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


@lru_cache(maxsize=1)
def _shape_bank():
    """All fixed connected 3..6-cell masks that fit in a 4x4 bbox.

    Constructive enumeration avoids capped rejection sampling and guarantees
    that every requested overlap relation can be realized deterministically.
    """
    current = {frozenset({(0, 0)})}
    by_size = {}
    for size in range(2, 7):
        grown = set()
        for shape in current:
            for r, c in shape:
                for dr, dc in _CARDINAL:
                    point = (r + dr, c + dc)
                    if point in shape:
                        continue
                    candidate = _normalize(set(shape) | {point})
                    height, width = _extent(candidate)
                    if height <= 4 and width <= 4:
                        grown.add(candidate)
        current = grown
        if size >= 3:
            by_size[size] = tuple(
                sorted(current, key=lambda cells: tuple(sorted(cells)))
            )
    return by_size


def _size_options(difficulty):
    if difficulty == "easy":
        return (3, 3, 3, 4, 4, 5, 6)
    if difficulty == "hard":
        return (3, 4, 4, 5, 5, 6, 6)
    return (3, 3, 4, 4, 5, 5, 6)


def _draw_operands(rng, overlap_kind, difficulty):
    bank = _shape_bank()
    sizes = _size_options(difficulty)
    size1 = rng.choice(sizes)
    first = rng.choice(bank[size1])
    if overlap_kind == "identical":
        return first, first

    # Do not commit to a second size before feasibility is known: some valid
    # six-cell masks contain every intersecting normalized triomino.  Pool all
    # difficulty-allowed sizes, then draw uniformly from actual partial partners.
    candidates = [
        shape
        for size2 in sorted(set(sizes))
        for shape in bank[size2]
        if first & shape and first - shape and shape - first
    ]
    if not candidates:
        raise RuntimeError(f"no partial-overlap partner for size {size1} shape")
    return first, rng.choice(candidates)


def _translated(shape, row, col):
    return frozenset((row + r, col + c) for r, c in shape)


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _boxes_have_blank_separator(first, second):
    a = _bbox(first)
    b = _bbox(second)
    return (
        a[2] + 1 < b[0]
        or b[2] + 1 < a[0]
        or a[3] + 1 < b[1]
        or b[3] + 1 < a[1]
    )


def _place_operands(first, second, height, width, rng):
    """Construct a separated layout directly, without quadratic pair search."""
    h1, w1 = _extent(first)
    h2, w2 = _extent(second)
    feasible = []
    if w1 + w2 + 1 <= width:
        feasible.append("horizontal")
    if h1 + h2 + 1 <= height:
        feasible.append("vertical")
    if not feasible:
        raise RuntimeError(
            f"no separated placement for operand extents {(h1, w1)} and "
            f"{(h2, w2)} in {height}x{width}"
        )

    orientation = rng.choice(feasible)
    swap = bool(rng.randrange(2))
    if orientation == "horizontal":
        left_shape, right_shape = ((second, first) if swap else (first, second))
        lh, lw = _extent(left_shape)
        rh, rw = _extent(right_shape)
        free = width - lw - rw - 1
        left_margin = rng.randint(0, free)
        remaining = free - left_margin
        extra_gap = rng.randint(0, remaining)
        left_origin = (rng.randint(0, height - lh), left_margin)
        right_origin = (
            rng.randint(0, height - rh),
            left_margin + lw + 1 + extra_gap,
        )
        if (0, 0) in _translated(left_shape, *left_origin):
            # Shift only on the non-separation axis, preserving the guaranteed
            # blank column between operand bounding boxes.
            left_origin = (rng.randint(1, height - lh), left_origin[1])
        left_cells = _translated(left_shape, *left_origin)
        right_cells = _translated(right_shape, *right_origin)
        pair = (right_cells, left_cells) if swap else (left_cells, right_cells)
    else:
        top_shape, bottom_shape = ((second, first) if swap else (first, second))
        th, tw = _extent(top_shape)
        bh, bw = _extent(bottom_shape)
        free = height - th - bh - 1
        top_margin = rng.randint(0, free)
        remaining = free - top_margin
        extra_gap = rng.randint(0, remaining)
        top_origin = (top_margin, rng.randint(0, width - tw))
        bottom_origin = (
            top_margin + th + 1 + extra_gap,
            rng.randint(0, width - bw),
        )
        if (0, 0) in _translated(top_shape, *top_origin):
            # Shift only on the non-separation axis, preserving the guaranteed
            # blank row between operand bounding boxes.
            top_origin = (top_origin[0], rng.randint(1, width - tw))
        top_cells = _translated(top_shape, *top_origin)
        bottom_cells = _translated(bottom_shape, *bottom_origin)
        pair = (bottom_cells, top_cells) if swap else (top_cells, bottom_cells)

    first_cells, second_cells = pair
    if (
        (0, 0) in first_cells
        or (0, 0) in second_cells
        or not first_cells.isdisjoint(second_cells)
        or not _boxes_have_blank_separator(first_cells, second_cells)
    ):
        # This is an internal construction invariant, not a recoverable fallback.
        raise RuntimeError("constructive operand placement violated its invariant")
    return first_cells, second_cells


def _validate_request(difficulty, overrides):
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of None/easy/medium/hard, got {difficulty!r}"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in {"grid_h", "grid_w", "ctrl"}:
            if type(value) is not int:
                raise ValueError(
                    f"{name} must be an integer, not {type(value).__name__}"
                )
        elif name == "overlap_kind" and type(value) is not str:
            raise ValueError(
                f"overlap_kind must be a string, not {type(value).__name__}"
            )


def _dimension_options(difficulty):
    # All legal values remain present in every band, so exact overrides never
    # conflict with difficulty.  Repetition changes only the default weights.
    if difficulty == "easy":
        heights = (7, 7, 7, 7, 7, 8, 8, 8, 9)
    elif difficulty == "hard":
        heights = (7, 7, 8, 8, 8, 8, 8, 9, 9)
    else:
        heights = (7, 7, 7, 8, 8, 8, 8, 9, 9)
    widths = (9, 10, 10, 10, 10, 10, 10, 10, 11)
    return heights, widths


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height_options, width_options = _dimension_options(difficulty)
    height = ctx.draw_choice("grid_h", height_options)
    width = ctx.draw_choice("grid_w", width_options)
    ctrl = ctx.draw_int("ctrl", 3, 5)
    overlap_kind = ctx.draw_choice(
        "overlap_kind", ("partial", "partial", "partial", "identical")
    )

    first, second = _draw_operands(
        ctx.draw_rng("operand_shapes"), overlap_kind, difficulty
    )
    cells1, cells2 = _place_operands(
        first, second, height, width, ctx.draw_rng("operand_placement")
    )
    grid = full_grid(height, width, 0)
    grid[0][0] = ctrl
    for r, c in cells1:
        grid[r][c] = 1
    for r, c in cells2:
        grid[r][c] = 2
    return grid


def _grid_structure_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    return []


def _color_cells(grid, color):
    return frozenset(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    )


def _is_connected(cells):
    if not cells:
        return False
    todo = deque([next(iter(cells))])
    seen = {todo[0]}
    while todo:
        r, c = todo.popleft()
        for dr, dc in _CARDINAL:
            point = (r + dr, c + dc)
            if point in cells and point not in seen:
                seen.add(point)
                todo.append(point)
    return len(seen) == len(cells)


def _overlap_kind(first, second):
    if first == second:
        return "identical"
    if first & second and first - second and second - first:
        return "partial"
    return "other"


def self_check(grid, *, difficulty=None, meta=None):
    """Return diagnostics for inputs outside this generator's lawful manifold."""
    errors = _grid_structure_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 9:
        errors.append(f"grid height {height} outside 7..9")
    if not 9 <= width <= 11:
        errors.append(f"grid width {width} outside 9..11")

    bad_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or value not in {0, 1, 2, 3, 4, 5}
    ]
    if bad_cells:
        errors.append(
            "cells must be integer input colors from {0,1,2,3,4,5}; "
            f"first bad cell={bad_cells[0]!r}"
        )
        return errors

    ctrl = grid[0][0]
    if ctrl not in (3, 4, 5):
        errors.append(f"(0,0) control {ctrl!r} is not 3, 4, or 5")
    controls = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (3, 4, 5)
    ]
    if len(controls) != 1 or controls[0][:2] != (0, 0):
        errors.append("the only control-colored cell must be (0,0)")

    expected_palette = {0, 1, 2, ctrl} if ctrl in (3, 4, 5) else None
    palette = {value for row in grid for value in row}
    if expected_palette is not None and palette != expected_palette:
        errors.append(
            f"palette {sorted(palette)} must equal {sorted(expected_palette)}"
        )

    physical = {}
    normalized = {}
    for color in (1, 2):
        cells = _color_cells(grid, color)
        physical[color] = cells
        if not 3 <= len(cells) <= 6:
            errors.append(f"color-{color} cell count {len(cells)} outside 3..6")
        if cells and not _is_connected(cells):
            errors.append(f"color-{color} cells are not one 4-connected component")
        normalized[color] = _normalize(cells)

    if physical[1] and physical[2]:
        if not _boxes_have_blank_separator(physical[1], physical[2]):
            errors.append(
                "operand bounding boxes need at least one blank separator row or column"
            )
        relation = _overlap_kind(normalized[1], normalized[2])
        if relation not in {"partial", "identical"}:
            errors.append(
                "normalized operands must partially overlap or be identical; "
                f"observed {relation}"
            )
    return errors


def observe_overrides(grid):
    """Recover every advertised exact axis from the returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    first = _normalize(_color_cells(grid, 1))
    second = _normalize(_color_cells(grid, 2))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "ctrl": grid[0][0],
        "overlap_kind": _overlap_kind(first, second),
    }


def oracle_output(grid):
    """Independent Python cross-check of the selected Racket behavior.

    This helper is not used to produce dataset labels.  Tests and semantic
    rivals use it as a transparent supplementary oracle; Racket parity is
    checked separately by reviewer tooling.
    """
    errors = _grid_structure_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    first = _normalize(_color_cells(grid, 1))
    second = _normalize(_color_cells(grid, 2))
    height = max((_extent(shape)[0] if shape else 0) for shape in (first, second))
    width = max((_extent(shape)[1] if shape else 0) for shape in (first, second))
    ctrl = grid[0][0]
    if ctrl == 3:
        result = first | second
    elif ctrl == 4:
        result = first ^ second
    elif ctrl == 5:
        result = first & second
    else:
        result = frozenset()
    if not result:
        return [[0]]
    output = full_grid(height, width, 0)
    for r, c in result:
        output[r][c] = 8
    return output


def _shape_statistics_shortcut(grid):
    """WRONG rival: infer the operation from operand statistics, ignore ctrl."""
    first = _normalize(_color_cells(grid, 1))
    second = _normalize(_color_cells(grid, 2))
    if first == second:
        result = first
    elif len(first) == len(second) == 3:
        result = first | second
    else:
        result = first ^ second
    if not result:
        return [[0]]
    height = max(_extent(first)[0], _extent(second)[0])
    width = max(_extent(first)[1], _extent(second)[1])
    output = full_grid(height, width, 0)
    for r, c in result:
        output[r][c] = 8
    return output


def strict_canonical_like(grid):
    return self_check(grid)


def _ctrl_is(value):
    return lambda grid: bool(grid and grid[0] and grid[0][0] == value)


def _relation_is(value):
    def predicate(grid):
        try:
            return observe_overrides(grid)["overlap_kind"] == value
        except ValueError:
            return False
    return predicate


def _refutes_shape_statistics(grid):
    try:
        return oracle_output(grid) != _shape_statistics_shortcut(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    "union_control": _ctrl_is(3),
    "xor_control": _ctrl_is(4),
    "intersection_control": _ctrl_is(5),
    "partial_operands": _relation_is("partial"),
    "identical_operands": _relation_is("identical"),
    "control_not_shape_statistics": _refutes_shape_statistics,
}
BRANCH_WITNESSES = {
    "union_control",
    "xor_control",
    "intersection_control",
    "partial_operands",
    "identical_operands",
}
SEMANTIC_RIVALS = {"shape_statistics_shortcut": _shape_statistics_shortcut}
WITNESS_RIVALS = {
    "control_not_shape_statistics": ["shape_statistics_shortcut"]
}
CANONICAL_SHORTCUTS = {"shape_statistics_shortcut": _shape_statistics_shortcut}
LESSON_COMPETITORS = {"shape_statistics_shortcut": _shape_statistics_shortcut}
