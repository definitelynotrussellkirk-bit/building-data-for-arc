"""Generator for completing the missing fourth copy of a rectangle-corner motif.

A lawful input contains exactly three translated copies of one connected shape,
all in one non-zero color.  The copies occupy the top-left, top-right, and
bottom-left corners of an axis-aligned rectangle.  The rule adds the same shape,
without rotation or recoloring, at the empty bottom-right corner.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "441c97bcdb07"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a51bdd8a29a6"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Place three identical translated copies of one 3..5-cell 4-connected "
    "shape, in one color, at the top-left, top-right, and bottom-left corners "
    "of an axis-aligned rectangle. Complete the empty bottom-right corner with "
    "a fourth copy in the same orientation and color."
)

INVARIANTS = [
    "background is 0 and every cell is an ARC color 0..9",
    "there is exactly one non-zero color",
    "there are exactly three 4-connected components with the same normalized shape",
    "component origins are exactly TL, TR, and BL of one axis-aligned rectangle",
    "the translated BR target is in bounds, empty, and separated by a blank gap",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-size counterexample or broader band anchor",
        "valid": "9..22",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-size counterexample or broader band anchor",
        "valid": "9..22",
    },
    "shape_id": {
        "type": "int",
        "default": "cyclic teaching schedule",
        "valid": "0..9",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# All shapes are normalized, 4-connected, occupy at least two rows and columns,
# and are not solid rectangles.  IDs 4 and 7 deliberately have non-four cell
# counts; the remaining IDs are four-cell anchors.  The three canonical
# orientations occur at IDs 0, 8, and 1 respectively.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
)
_SHAPE_TO_ID = {shape: index for index, shape in enumerate(_SHAPES)}

# Alternating non-four/four-cell motifs means every three consecutive examples,
# and every three-of-four query rotation, contains a counterexample to the
# canonical-fitting four-cell-only shortcut.  The 16-step period still visits
# every advertised shape ID.
_SHAPE_SCHEDULE = (4, 0, 7, 1, 4, 2, 7, 3, 4, 5, 7, 6, 4, 8, 7, 9)
SCHEDULE_PROFILES = (
    "non_four_cell_counterexample",
    "four_cell_anchor",
)
_BROAD_DIMS_BY_BAND = {
    "easy": (9, 11),
    "medium": (14, 16),
    "hard": (20, 22),
    None: (12, 14),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic teaching role of this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % 2]


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")

    limits = {"grid_h": (9, 22), "grid_w": (9, 22), "shape_id": (0, 9)}
    for name, (lo, hi) in limits.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} override must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} is outside {lo}..{hi}")


def _draw_int_axis(ctx, label: str, lo: int, hi: int, default: int) -> int:
    """Honor an exact override or record one deterministic scheduled default."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return int(ctx.draw_choice(label, (int(default),)))


def _normalize(cells: set[tuple[int, int]] | list[tuple[int, int]]):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    """Parse the exact task grammar without mutating or raising on bad input."""
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return None, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid rows must have equal width"]

    height = len(grid)
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"grid is too large: {height}x{width}")

    positions_by_color: dict[int, set[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) is not an integer ARC color 0..9: {value!r}"
                )
                if len(errors) >= 4:
                    return None, errors
                continue
            if value:
                positions_by_color.setdefault(value, set()).add((row_index, col_index))
    if errors:
        return None, errors
    if len(positions_by_color) != 1:
        return None, [
            f"expected exactly one non-zero color; found {len(positions_by_color)}"
        ]

    color, colored = next(iter(positions_by_color.items()))
    components = _components(colored)
    if len(components) != 3:
        return None, [f"expected exactly three 4-connected copies; found {len(components)}"]

    normalized = [_normalize(component) for component in components]
    if len(set(normalized)) != 1:
        return None, ["the three components are not identical translated shapes"]
    shape = normalized[0]
    cell_count = len(shape)
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    if not 3 <= cell_count <= 5:
        return None, [f"shape has {cell_count} cells; expected 3..5"]
    if shape_h < 2 or shape_w < 2:
        return None, ["shape must occupy at least two rows and two columns"]
    if cell_count == shape_h * shape_w:
        return None, ["solid rectangular components are not part of this task grammar"]

    origins = {
        (min(row for row, _ in component), min(col for _, col in component))
        for component in components
    }
    origin_rows = sorted({row for row, _ in origins})
    origin_cols = sorted({col for _, col in origins})
    if len(origin_rows) != 2 or len(origin_cols) != 2:
        return None, ["component origins do not define two rectangle rows and columns"]
    top, bottom = origin_rows
    left, right = origin_cols
    expected = {(top, left), (top, right), (bottom, left)}
    if origins != expected:
        return None, [
            "component origins must occupy exactly top-left, top-right, and bottom-left"
        ]

    row_span = bottom - top
    col_span = right - left
    if row_span < shape_h + 1 or col_span < shape_w + 1:
        return None, ["copies must be separated by at least one blank row and column"]
    if bottom + shape_h > height or right + shape_w > width:
        return None, ["the missing bottom-right copy would extend outside the grid"]

    target_cells = {(bottom + row, right + col) for row, col in shape}
    occupied = {cell for component in components for cell in component}
    if target_cells & occupied:
        return None, ["the missing bottom-right target is not empty"]

    return {
        "height": height,
        "width": width,
        "color": color,
        "components": components,
        "shape": shape,
        "shape_h": shape_h,
        "shape_w": shape_w,
        "cell_count": cell_count,
        "origins": origins,
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "target_cells": target_cells,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return exact input-grammar violations; all canonical inputs pass."""
    del difficulty, meta
    _analysis, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws stay on the selected task's semantic manifold."""
    _analysis, errors = _analyze(grid)
    return errors


def _paint(
    grid: list[list[int]],
    top: int,
    left: int,
    cells: tuple[tuple[int, int], ...],
    color: int,
) -> None:
    for row, col in cells:
        grid[top + row][left + col] = color


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python diagnostic mirror; canonical Racket remains authority."""
    analysis, errors = _analyze(grid)
    if errors or analysis is None:
        raise ValueError("rule_mirror expects a lawful input: " + "; ".join(errors))
    output = [list(row) for row in grid]
    _paint(
        output,
        analysis["bottom"],
        analysis["right"],
        analysis["shape"],
        analysis["color"],
    )
    return output


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact public axis directly from the returned pixels."""
    analysis, errors = _analyze(grid)
    if errors or analysis is None:
        raise ValueError("cannot observe axes from malformed grid: " + "; ".join(errors))
    shape = analysis["shape"]
    if shape not in _SHAPE_TO_ID:
        raise ValueError(f"lawful shape {shape!r} is not in the generated shape bank")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "shape_id": _SHAPE_TO_ID[shape],
    }


def semantic_profile(grid: Any) -> dict[str, Any]:
    analysis, errors = _analyze(grid)
    if errors or analysis is None:
        return {"valid": False, "errors": errors}
    return {
        "valid": True,
        "shape_cells": analysis["cell_count"],
        "shape_id": _SHAPE_TO_ID.get(analysis["shape"]),
        "row_span": analysis["bottom"] - analysis["top"],
        "col_span": analysis["right"] - analysis["left"],
    }


def _four_cell_only(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong shortcut: complete the rectangle only for tetrominoes."""
    analysis, errors = _analyze(grid)
    if errors or analysis is None or analysis["cell_count"] != 4:
        return [list(row) for row in grid]
    return rule_mirror(grid)


def _non_four_cell_shape(grid: list[list[int]]) -> bool:
    profile = semantic_profile(grid)
    return bool(profile.get("valid") and profile.get("shape_cells") != 4)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "non_four_cell_shape": _non_four_cell_shape,
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "four_cell_only": _four_cell_only,
}
WITNESS_RIVALS = {"non_four_cell_shape": ["four_cell_only"]}
CANONICAL_SHORTCUTS = {"four_cell_only": _four_cell_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named rival survives demos and changes the query."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    pairs = [*demos, query]
    reasons: list[str] = []
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{role} input is not lawful: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with fourth-corner completion")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def _layout_options(length: int, shape_extent: int) -> list[tuple[int, int]]:
    """All (first-origin, origin-span) pairs with a one-cell gap and in-bounds BR."""
    return [
        (origin, span)
        for origin in range(length)
        for span in range(shape_extent + 1, length)
        if origin + span + shape_extent <= length
    ]


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

    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "non_four_cell_counterexample":
        default_h, default_w = (10, 10) if int(sample_index) % 4 == 0 else (10, 12)
    else:
        default_h, default_w = _BROAD_DIMS_BY_BAND[difficulty]
    default_shape = _SHAPE_SCHEDULE[int(sample_index) % len(_SHAPE_SCHEDULE)]

    height = _draw_int_axis(ctx, "grid_h", 9, 22, default_h)
    width = _draw_int_axis(ctx, "grid_w", 9, 22, default_w)
    shape_id = _draw_int_axis(ctx, "shape_id", 0, 9, default_shape)
    shape = _SHAPES[shape_id]
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1

    row_options = _layout_options(height, shape_h)
    col_options = _layout_options(width, shape_w)
    if not row_options or not col_options:
        raise ValueError(
            f"grid {height}x{width} cannot realize shape_id={shape_id} with blank gaps"
        )
    band_key = difficulty or "default"
    layout_rng = ctx.draw_rng(f"layout:{band_key}")
    pivot_row, row_span = layout_rng.choice(row_options)
    pivot_col, col_span = layout_rng.choice(col_options)
    color = ctx.draw_color(f"shape_color:{band_key}", exclude=(0,))

    grid = full_grid(height, width, 0)
    _paint(grid, pivot_row, pivot_col, shape, color)
    _paint(grid, pivot_row, pivot_col + col_span, shape, color)
    _paint(grid, pivot_row + row_span, pivot_col, shape, color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator produced malformed scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    recorded = ctx.recorded_draws()
    for axis in AXES:
        if observed[axis] != recorded[axis]:
            raise AssertionError(
                f"axis {axis!r} drifted: keyed={recorded[axis]!r} "
                f"observed={observed[axis]!r}"
            )
    return grid


def mutation_fixtures():
    """Task-local malformed near-misses for the defect linter and regressions."""
    blank = full_grid(10, 10, 0)

    singletons = full_grid(10, 10, 0)
    for row, col in ((1, 1), (1, 7), (7, 1)):
        singletons[row][col] = 2

    short_lines = full_grid(10, 10, 0)
    for top, left in ((1, 1), (1, 7), (7, 1)):
        short_lines[top][left] = 2
        short_lines[top][left + 1] = 2

    solid_2x2 = full_grid(10, 10, 0)
    for top, left in ((1, 1), (1, 7), (7, 1)):
        for drow in range(2):
            for dcol in range(2):
                solid_2x2[top + drow][left + dcol] = 2

    base = generate(20261006, 1, grid_h=10, grid_w=10, shape_id=0)
    analysis, errors = _analyze(base)
    if errors or analysis is None:
        raise AssertionError("fixture base unexpectedly failed analysis")
    ordered_components = sorted(
        analysis["components"],
        key=lambda component: (min(row for row, _ in component), min(col for _, col in component)),
    )

    missing_copy = copy_grid = [row[:] for row in base]
    for row, col in ordered_components[-1]:
        copy_grid[row][col] = 0

    mismatched_copy = [row[:] for row in base]
    row, col = max(ordered_components[1])
    mismatched_copy[row][col] = 0

    filled_bottom_right = rule_mirror(base)
    ragged = [[0, 2, 0], [0, 0]]

    return [
        ("blank", blank),
        ("singletons", singletons),
        ("short_lines", short_lines),
        ("solid_2x2", solid_2x2),
        ("missing_copy", missing_copy),
        ("mismatched_copy", mismatched_copy),
        ("filled_bottom_right", filled_bottom_right),
        ("ragged", ragged),
    ]
