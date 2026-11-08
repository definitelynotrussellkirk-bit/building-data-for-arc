"""Generator for ARC task cf976dae6b92 (canonical slug 0e671a1a).

The input contains exactly one marker of each color 2, 4, and 3 on a black
background.  The oracle connects 2 -> 4 -> 3.  Each connection is routed
*horizontally from the source marker and then vertically into the destination
marker*, using gray (5), while preserving the three colored marker cells.

The teaching schedule covers all six row orders crossed with all six column
orders.  That makes every left/right and up/down branch observable and breaks
position-, direction-, and color-order shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cf976dae6b92"
TASK_ID = GENERATOR_ID
VERSION = "2.0.2"
RULE_HASH = "a90d595f69e2"
SUMMARY = (
    "Exactly one marker each of colors 2, 4, and 3. Connect 2 to 4 and then "
    "4 to 3 with gray paths that move horizontally first and vertically "
    "second; preserve all marker colors."
)

INVARIANTS = [
    "the grid is rectangular with height and width in 7..18",
    "the background is 0 and the only nonzero input colors are 2, 4, and 3",
    "exactly one marker of each color 2, 4, and 3 is present",
    "the three marker rows are distinct and the three marker columns are distinct",
    "all 36 row-order/column-order profiles occur in every 36-sample schedule cycle",
]

ROW_ORDERS = ("243", "234", "423", "432", "324", "342")
COL_ORDERS = ROW_ORDERS

AXES = {
    "grid_h": {
        "type": "int",
        "default": "13 every fifth sample; otherwise difficulty-aware 7..18",
        "valid": "7..18",
    },
    "grid_w": {
        "type": "int",
        "default": "13 every fifth sample; otherwise difficulty-aware 7..18",
        "valid": "7..18",
    },
    "row_order": {
        "type": "str",
        "default": "six-profile sample_index schedule",
        "valid": "|".join(ROW_ORDERS),
    },
    "col_order": {
        "type": "str",
        "default": "six-profile block schedule crossed with row_order",
        "valid": "|".join(COL_ORDERS),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15
SCHEDULE_PROFILES = tuple(
    f"rows={row_order}|cols={col_order}"
    for col_order in COL_ORDERS
    for row_order in ROW_ORDERS
)

_BAND_RANGES = {
    "easy": (7, 10),
    "medium": (9, 14),
    "hard": (13, 18),
}


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _BAND_RANGES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    return str(difficulty)


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    normalized = {key: value for key, value in overrides.items() if value is not None}
    unknown = sorted(set(normalized) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    return normalized


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic 6x6 row/column-order schedule profile."""
    del seed, difficulty
    index = int(sample_index)
    row_index = index % len(ROW_ORDERS)
    block_index = (index // len(ROW_ORDERS)) % len(COL_ORDERS)
    row_order = ROW_ORDERS[row_index]
    col_order = COL_ORDERS[(row_index + block_index) % len(COL_ORDERS)]
    return f"rows={row_order}|cols={col_order}"


def _draw_dimension(ctx, overrides, name: str, band: str, sample_index: int) -> int:
    if name in overrides:
        return ctx.draw_int_strict(name, 7, 18)
    if sample_index % 5 == 0:
        return int(ctx.draw_int(name, 13, 13))
    lo, hi = _BAND_RANGES[band]
    return int(ctx.draw_int(name, lo, hi))


def _draw_order(ctx, overrides, name: str, scheduled: str, valid: tuple[str, ...]) -> str:
    if name in overrides:
        return str(ctx.draw_choice(name, valid))
    return str(ctx.draw_choice(name, (scheduled,)))


def _coordinate_map(order: str, size: int, rng) -> dict[int, int]:
    coordinates = sorted(rng.sample(range(1, size - 1), 3))
    return {int(color): coordinate for color, coordinate in zip(order, coordinates)}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _normalize_overrides(overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = _draw_dimension(ctx, overrides, "grid_h", band, int(sample_index))
    w = _draw_dimension(ctx, overrides, "grid_w", band, int(sample_index))
    schedule_index = int(sample_index)
    row_index = schedule_index % len(ROW_ORDERS)
    block_index = (schedule_index // len(ROW_ORDERS)) % len(COL_ORDERS)
    scheduled_row = ROW_ORDERS[row_index]
    scheduled_col = COL_ORDERS[(row_index + block_index) % len(COL_ORDERS)]
    row_order = _draw_order(ctx, overrides, "row_order", scheduled_row, ROW_ORDERS)
    col_order = _draw_order(ctx, overrides, "col_order", scheduled_col, COL_ORDERS)

    row_by_color = _coordinate_map(row_order, h, ctx.draw_rng("marker_rows"))
    col_by_color = _coordinate_map(col_order, w, ctx.draw_rng("marker_cols"))

    grid = full_grid(h, w, 0)
    for color in (2, 4, 3):
        grid[row_by_color[color]][col_by_color[color]] = color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise AssertionError("constructed invalid marker scene: " + "; ".join(errors))
    return grid


def _marker_positions(grid: Iterable[Iterable[int]]) -> dict[int, tuple[int, int]]:
    positions: dict[int, tuple[int, int]] = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value in (2, 4, 3):
                positions[int(value)] = (row_index, col_index)
    return positions


def analyze_scene(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty row sequence"], "facts": None}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["rows must be nonempty sequences"], "facts": None}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": None}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["cells must be integer ARC colors in 0..9"], "facts": None}

    height = len(grid)
    if not 7 <= height <= 18:
        errors.append(f"grid_h must be in 7..18, got {height}")
    if not 7 <= width <= 18:
        errors.append(f"grid_w must be in 7..18, got {width}")

    unexpected = sorted(
        {value for row in grid for value in row if value not in (0, 2, 4, 3)}
    )
    if unexpected:
        errors.append(f"unexpected input colors: {unexpected}; only 0,2,4,3 are lawful")

    locations: dict[int, list[tuple[int, int]]] = {2: [], 4: [], 3: []}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value in locations:
                locations[value].append((row_index, col_index))
    for color in (2, 4, 3):
        count = len(locations[color])
        if count != 1:
            errors.append(f"color {color} must appear exactly once, got {count}")

    if errors:
        return {"errors": errors, "facts": None}

    positions = {color: locations[color][0] for color in (2, 4, 3)}
    rows = [positions[color][0] for color in (2, 4, 3)]
    cols = [positions[color][1] for color in (2, 4, 3)]
    if len(set(rows)) != 3:
        errors.append("marker rows must be pairwise distinct")
    if len(set(cols)) != 3:
        errors.append("marker columns must be pairwise distinct")
    if errors:
        return {"errors": errors, "facts": None}

    row_order = "".join(str(color) for color in sorted(positions, key=lambda c: positions[c][0]))
    col_order = "".join(str(color) for color in sorted(positions, key=lambda c: positions[c][1]))
    facts = {
        "grid_h": height,
        "grid_w": width,
        "row_order": row_order,
        "col_order": col_order,
        "positions": positions,
        "direction_signature": _direction_signature_from_positions(positions),
    }
    return {"errors": [], "facts": facts}


def observe_overrides(grid: Any) -> dict[str, int | str]:
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid marker scene: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {axis: facts[axis] for axis in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = analyze_scene(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
    if requested:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis not in AXES or expected is None:
                continue
            normalized_expected: int | str
            if axis in ("grid_h", "grid_w"):
                normalized_expected = int(expected)
            else:
                normalized_expected = str(expected)
            if observed[axis] != normalized_expected:
                errors.append(
                    f"override {axis} requested {normalized_expected!r}, "
                    f"observed {observed[axis]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical manifold: lawful marker scenes on the official 13x13 canvas."""
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    facts = analysis["facts"]
    reasons: list[str] = []
    if (facts["grid_h"], facts["grid_w"]) != (13, 13):
        reasons.append(
            f"official inputs are 13x13; got {facts['grid_h']}x{facts['grid_w']}"
        )
    return reasons


def _paint_horizontal(grid: list[list[int]], row: int, col_a: int, col_b: int, color: int) -> None:
    for col in range(min(col_a, col_b), max(col_a, col_b) + 1):
        grid[row][col] = color


def _paint_vertical(grid: list[list[int]], col: int, row_a: int, row_b: int, color: int) -> None:
    for row in range(min(row_a, row_b), max(row_a, row_b) + 1):
        grid[row][col] = color


def _connect_sequence(
    grid: list[list[int]],
    sequence: tuple[int, int, int],
    *,
    horizontal_first: bool,
    line_color: int = 5,
) -> list[list[int]]:
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid marker scene: " + "; ".join(analysis["errors"]))
    positions = analysis["facts"]["positions"]
    output = full_grid(len(grid), len(grid[0]), 0)
    for source, destination in zip(sequence, sequence[1:]):
        source_row, source_col = positions[source]
        destination_row, destination_col = positions[destination]
        if horizontal_first:
            _paint_horizontal(output, source_row, source_col, destination_col, line_color)
            _paint_vertical(output, destination_col, source_row, destination_row, line_color)
        else:
            _paint_vertical(output, source_col, source_row, destination_row, line_color)
            _paint_horizontal(output, destination_row, source_col, destination_col, line_color)
    for marker_color, (row, col) in positions.items():
        output[row][col] = marker_color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned canonical Racket rule."""
    return _connect_sequence(grid, (2, 4, 3), horizontal_first=True)


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_vertical_first_elbows(grid):
    return _connect_sequence(grid, (2, 4, 3), horizontal_first=False)


def _rival_row_sorted_marker_order(grid):
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid marker scene")
    positions = analysis["facts"]["positions"]
    sequence = tuple(sorted(positions, key=lambda color: positions[color][0]))
    return _connect_sequence(grid, sequence, horizontal_first=True)


def _rival_col_sorted_marker_order(grid):
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid marker scene")
    positions = analysis["facts"]["positions"]
    sequence = tuple(sorted(positions, key=lambda color: positions[color][1]))
    return _connect_sequence(grid, sequence, horizontal_first=True)


def _rival_only_transform_13x13(grid):
    if len(grid) == 13 and len(grid[0]) == 13:
        return rule_mirror(grid)
    return _rival_identity(grid)


def _rival_recolor_path_with_2(grid):
    return _connect_sequence(grid, (2, 4, 3), horizontal_first=True, line_color=2)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity_marker_as_answer": _rival_identity,
    "vertical_first_elbows": _rival_vertical_first_elbows,
    "row_sorted_marker_order": _rival_row_sorted_marker_order,
    "col_sorted_marker_order": _rival_col_sorted_marker_order,
    "only_transform_13x13": _rival_only_transform_13x13,
    "recolor_path_with_2": _rival_recolor_path_with_2,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "only_transform_13x13": _rival_only_transform_13x13,
}


def _direction_signature_from_positions(positions: dict[int, tuple[int, int]]) -> str:
    r2, c2 = positions[2]
    r4, c4 = positions[4]
    r3, c3 = positions[3]
    return "".join(
        (
            "R" if c4 > c2 else "L",
            "D" if r4 > r2 else "U",
            "R" if c3 > c4 else "L",
            "D" if r3 > r4 else "U",
        )
    )


def _direction_signature(grid) -> str | None:
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        return None
    return str(analysis["facts"]["direction_signature"])


def _rival_differs(grid, rival_name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "segment_2_to_4_moves_right": lambda grid: (
        (_direction_signature(grid) or "").startswith("R")
    ),
    "segment_2_to_4_moves_left": lambda grid: (
        (_direction_signature(grid) or "").startswith("L")
    ),
    "segment_2_to_4_moves_down": lambda grid: (
        len(_direction_signature(grid) or "") == 4
        and (_direction_signature(grid) or "")[1] == "D"
    ),
    "segment_2_to_4_moves_up": lambda grid: (
        len(_direction_signature(grid) or "") == 4
        and (_direction_signature(grid) or "")[1] == "U"
    ),
    "segment_4_to_3_moves_right": lambda grid: (
        len(_direction_signature(grid) or "") == 4
        and (_direction_signature(grid) or "")[2] == "R"
    ),
    "segment_4_to_3_moves_left": lambda grid: (
        len(_direction_signature(grid) or "") == 4
        and (_direction_signature(grid) or "")[2] == "L"
    ),
    "segment_4_to_3_moves_down": lambda grid: (
        len(_direction_signature(grid) or "") == 4
        and (_direction_signature(grid) or "")[3] == "D"
    ),
    "segment_4_to_3_moves_up": lambda grid: (
        len(_direction_signature(grid) or "") == 4
        and (_direction_signature(grid) or "")[3] == "U"
    ),
}
SEMANTIC_WITNESSES.update(
    {
        "path_adds_gray_cells": lambda grid: _rival_differs(
            grid, "identity_marker_as_answer"
        ),
        "horizontal_first_refutes_vertical_first": lambda grid: _rival_differs(
            grid, "vertical_first_elbows"
        ),
        "color_order_refutes_row_sorted": lambda grid: _rival_differs(
            grid, "row_sorted_marker_order"
        ),
        "color_order_refutes_col_sorted": lambda grid: _rival_differs(
            grid, "col_sorted_marker_order"
        ),
        "noncanonical_size_refutes_13_only": lambda grid: _rival_differs(
            grid, "only_transform_13x13"
        ),
        "gray_path_refutes_marker_color_echo": lambda grid: _rival_differs(
            grid, "recolor_path_with_2"
        ),
    }
)

WITNESS_RIVALS = {
    "path_adds_gray_cells": ["identity_marker_as_answer"],
    "horizontal_first_refutes_vertical_first": ["vertical_first_elbows"],
    "color_order_refutes_row_sorted": ["row_sorted_marker_order"],
    "color_order_refutes_col_sorted": ["col_sorted_marker_order"],
    "noncanonical_size_refutes_13_only": ["only_transform_13x13"],
    "gray_path_refutes_marker_color_echo": ["recolor_path_with_2"],
}


def _validate_pair(pair: Any, label: str) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return None, [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return None, [f"{label} input: {reason}" for reason in errors]
    expected = rule_mirror(pair["input"])
    if pair["output"] != expected:
        return expected, [f"{label} output does not match the canonical rule"]
    return expected, []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives its demonstrations."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration pair is required"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        _expected, pair_errors = _validate_pair(demo, f"demo {index}")
        reasons.extend(pair_errors)
    query_expected, query_errors = _validate_pair(query, "query")
    reasons.extend(query_errors)
    if reasons or query_expected is None:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"]
            for demo in demos
        )
        if survives and competitor(query["input"]) != query_expected:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Malformed scenes that exercise distinct structural rejection paths."""
    base = generate(99173, 17, difficulty="medium")
    analysis = analyze_scene(base)
    positions = analysis["facts"]["positions"]

    missing_three = deepcopy(base)
    r3, c3 = positions[3]
    missing_three[r3][c3] = 0

    duplicate_two = deepcopy(base)
    for row in range(len(base)):
        for col in range(len(base[0])):
            if duplicate_two[row][col] == 0:
                duplicate_two[row][col] = 2
                break
        else:
            continue
        break

    shared_row = deepcopy(base)
    r4, c4 = positions[4]
    shared_row[r4][c4] = 0
    row2, col2 = positions[2]
    free_col = next(
        col
        for col in range(1, len(base[0]) - 1)
        if col not in {col2, positions[3][1]} and shared_row[row2][col] == 0
    )
    shared_row[row2][free_col] = 4

    shared_col = deepcopy(base)
    shared_col[r4][c4] = 0
    free_row = next(
        row
        for row in range(1, len(base) - 1)
        if row not in {row2, positions[3][0]} and shared_col[row][col2] == 0
    )
    shared_col[free_row][col2] = 4

    unexpected_gray = deepcopy(base)
    for row in range(len(base)):
        for col in range(len(base[0])):
            if unexpected_gray[row][col] == 0:
                unexpected_gray[row][col] = 5
                break
        else:
            continue
        break

    return [
        ("missing_color_3", missing_three),
        ("duplicate_color_2", duplicate_two),
        ("markers_share_a_row", shared_row),
        ("markers_share_a_column", shared_col),
        ("unexpected_gray_input_cell", unexpected_gray),
    ]
