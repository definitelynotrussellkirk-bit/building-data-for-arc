"""Semantic curriculum generator for ARC task ``d8b498586958``.

A two-row header contains one color-5 corner marker.  Its corner chooses one
of four cellwise Boolean operations over the occupied coordinates of two
same-size panels separated by full color-9 rows:

* top-left: union
* top-right: intersection
* bottom-left: symmetric difference (XOR)
* bottom-right: A minus B

The selected support is rendered in cyan (8) on a panel-sized zero background.
Generated operands always have non-empty shared, A-only, and B-only regions, so
all four operations are observably different.  Four consecutive examples cover
all four operation markers.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d8b498586958"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "10616a474432"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A color-5 header corner selects union, intersection, XOR, or A-minus-B "
    "over two same-size occupancy panels. Four-example lessons cover every "
    "corner, and every operand pair makes all four outputs distinct."
)

INVARIANTS = [
    "a two-row header and two square operand panels are separated by single full color-9 rows",
    "the header contains exactly one color-5 marker at one of its four corners",
    "panel A uses color 2 and panel B uses one of 3/4/6/7",
    "shared, A-only, and B-only supports are all non-empty, making all four operations distinct",
]

_OPERATION_NAMES = ("union", "intersection", "xor", "a_minus_b")
_B_COLORS = (3, 4, 6, 7)
_HEADER_MARKERS = ((0, 0), (0, -1), (1, 0), (1, -1))

AXES = {
    "panel_side": {
        "type": "int",
        "default": "scheduled 4..9 with canonical side 5 in every four-draw window",
        "valid": "4..9",
    },
    "operation": {
        "type": "int",
        "default": "seed-phased four-example cycle 0..3",
        "valid": "0..3",
    },
    "shared_cells": {
        "type": "int",
        "default": "keyed draw 1..5",
        "valid": "1..5",
    },
    "a_only_cells": {
        "type": "int",
        "default": "keyed draw 1..5",
        "valid": "1..5",
    },
    "b_only_cells": {
        "type": "int",
        "default": "keyed draw 1..5",
        "valid": "1..5",
    },
    "b_color": {
        "type": "int",
        "default": "scheduled 3|4|6|7",
        "valid": "3|4|6|7",
    },
}

# The maximum occupied support is 5+5+5=15, which fits the minimum 4x4 panel.
# Therefore every Cartesian combination of advertised overrides is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = tuple(f"operation_{name}" for name in _OPERATION_NAMES)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _scheduled_operation(seed: int, sample_index: int) -> int:
    return (int(seed) + int(sample_index)) % 4


def _scheduled_panel_side(sample_index: int, band: str) -> int:
    schedules = {
        "easy": (5, 4, 5, 6),
        "medium": (5, 6, 5, 7),
        "hard": (5, 7, 8, 9),
    }
    return schedules[band][int(sample_index) % 4]


def _scheduled_b_color(seed: int, sample_index: int) -> int:
    # Holding each color for a four-example lesson keeps color nuisance
    # independent of the operation dictionary while cycling all legal colors.
    return _B_COLORS[((int(sample_index) // 4) + int(seed)) % len(_B_COLORS)]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    _band(difficulty)
    return SCHEDULE_PROFILES[_scheduled_operation(seed, sample_index)]


def _requested_int(name: str, value: Any, lo: int, hi: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if not lo <= value <= hi:
        raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    return value


def _requested_choice(name: str, value: Any, legal: Sequence[int]) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if value not in legal:
        raise ValueError(f"{name}={value} not in {tuple(legal)}")
    return value


def _paint(grid: list[list[int]], top: int, cells: Sequence[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        grid[top + row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    count_rng = ctx.draw_rng("default-counts")

    requested = {
        "panel_side": _requested_int(
            "panel_side",
            overrides.get("panel_side", _scheduled_panel_side(sample_index, band)),
            4,
            9,
        ),
        "operation": _requested_int(
            "operation",
            overrides.get("operation", _scheduled_operation(seed, sample_index)),
            0,
            3,
        ),
        "shared_cells": _requested_int(
            "shared_cells", overrides.get("shared_cells", count_rng.randint(1, 5)), 1, 5
        ),
        "a_only_cells": _requested_int(
            "a_only_cells", overrides.get("a_only_cells", count_rng.randint(1, 5)), 1, 5
        ),
        "b_only_cells": _requested_int(
            "b_only_cells", overrides.get("b_only_cells", count_rng.randint(1, 5)), 1, 5
        ),
        "b_color": _requested_choice(
            "b_color", overrides.get("b_color", _scheduled_b_color(seed, sample_index)), _B_COLORS
        ),
    }

    # Singleton typed draws preserve keyed provenance for both defaults and
    # explicit exact overrides after the full-domain validation above.
    panel_side = ctx.draw_choice("panel_side", [requested["panel_side"]])
    operation = ctx.draw_choice("operation", [requested["operation"]])
    shared_n = ctx.draw_choice("shared_cells", [requested["shared_cells"]])
    a_only_n = ctx.draw_choice("a_only_cells", [requested["a_only_cells"]])
    b_only_n = ctx.draw_choice("b_only_cells", [requested["b_only_cells"]])
    b_color = ctx.draw_choice("b_color", [requested["b_color"]])

    occupied = shared_n + a_only_n + b_only_n
    if occupied > panel_side * panel_side:
        raise RuntimeError("advertised override domain no longer fits the minimum panel")

    cells = [(row, col) for row in range(panel_side) for col in range(panel_side)]
    ctx.draw_rng("layout").shuffle(cells)
    shared = cells[:shared_n]
    a_only = cells[shared_n : shared_n + a_only_n]
    b_only = cells[shared_n + a_only_n : occupied]

    height = 2 * panel_side + 4
    grid = full_grid(height, panel_side, 0)
    marker_row, marker_col = _HEADER_MARKERS[operation]
    if marker_col < 0:
        marker_col = panel_side - 1
    grid[marker_row][marker_col] = 5
    grid[2] = [9] * panel_side
    grid[panel_side + 3] = [9] * panel_side
    _paint(grid, 3, shared + a_only, 2)
    _paint(grid, panel_side + 4, shared + b_only, b_color)
    return grid


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty rectangular sequence"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid must contain nonempty rows"]}

    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid is ragged"]}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"invalid ARC color {value!r} at {(row_index, col_index)}")
    if errors:
        return {"errors": errors}

    panel_side = width
    if not 4 <= panel_side <= 9:
        errors.append(f"panel_side {panel_side} outside [4, 9]")
    expected_height = 2 * panel_side + 4
    if height != expected_height:
        errors.append(f"height {height} does not equal 2*panel_side+4 ({expected_height})")
    if errors:
        return {"errors": errors}

    divider_rows = [row for row in range(height) if all(grid[row][col] == 9 for col in range(width))]
    expected_dividers = [2, panel_side + 3]
    if divider_rows != expected_dividers:
        errors.append(f"expected single divider rows {expected_dividers}, found {divider_rows}")

    header_values = [
        (row, col, grid[row][col])
        for row in range(2)
        for col in range(panel_side)
        if grid[row][col] != 0
    ]
    marker_positions = [(row, col) for row, col, value in header_values if value == 5]
    if len(marker_positions) != 1 or len(header_values) != 1:
        errors.append("header must contain exactly one color-5 marker and otherwise zeros")
        operation = None
    else:
        marker = marker_positions[0]
        markers = ((0, 0), (0, panel_side - 1), (1, 0), (1, panel_side - 1))
        if marker not in markers:
            errors.append(f"header marker {marker} is not a corner")
            operation = None
        else:
            operation = markers.index(marker)

    a_rows = grid[3 : 3 + panel_side]
    b_rows = grid[panel_side + 4 : panel_side + 4 + panel_side]
    if any(value not in (0, 2) for row in a_rows for value in row):
        errors.append("panel A must use only background 0 and operand color 2")
    b_colors = {value for row in b_rows for value in row if value != 0}
    if len(b_colors) != 1 or next(iter(b_colors), None) not in _B_COLORS:
        errors.append(f"panel B must use exactly one color from {_B_COLORS}, found {sorted(b_colors)}")
        b_color = None
    else:
        b_color = next(iter(b_colors))

    a_cells = {
        (row, col)
        for row, values in enumerate(a_rows)
        for col, value in enumerate(values)
        if value == 2
    }
    b_cells = {
        (row, col)
        for row, values in enumerate(b_rows)
        for col, value in enumerate(values)
        if b_color is not None and value == b_color
    }
    shared = a_cells & b_cells
    a_only = a_cells - b_cells
    b_only = b_cells - a_cells
    for name, cells in (("shared_cells", shared), ("a_only_cells", a_only), ("b_only_cells", b_only)):
        if not 1 <= len(cells) <= 5:
            errors.append(f"{name}={len(cells)} outside [1, 5]")

    return {
        "errors": errors,
        "panel_side": panel_side,
        "operation": operation,
        "shared_cells": len(shared),
        "a_only_cells": len(a_only),
        "b_only_cells": len(b_only),
        "b_color": b_color,
        "a_cells": frozenset(a_cells),
        "b_cells": frozenset(b_cells),
    }


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {name: analysis[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the complete lawful generalized grammar used by this sampler."""
    return self_check(grid)


def _operation_cells(a_cells: frozenset[tuple[int, int]], b_cells: frozenset[tuple[int, int]], operation: int):
    if operation == 0:
        return a_cells | b_cells
    if operation == 1:
        return a_cells & b_cells
    if operation == 2:
        return a_cells ^ b_cells
    if operation == 3:
        return a_cells - b_cells
    raise ValueError(f"unknown operation {operation!r}")


def _render(analysis: dict[str, Any], operation: int) -> list[list[int]]:
    output = full_grid(analysis["panel_side"], analysis["panel_side"], 0)
    for row, col in _operation_cells(analysis["a_cells"], analysis["b_cells"], operation):
        output[row][col] = 8
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror; the synchronized Racket program remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    return _render(analysis, analysis["operation"])


def _operation_alias(source: int, target: int) -> Callable[[Any], list[list[int]]]:
    def rival(grid):
        analysis = _analysis(grid)
        if analysis["errors"]:
            raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
        operation = target if analysis["operation"] == source else analysis["operation"]
        return _render(analysis, operation)

    return rival


def _column_only_header(grid) -> list[list[int]]:
    """Plausible shortcut: left means union and right means intersection; ignore row."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    operation = 0 if analysis["operation"] in (0, 2) else 1
    return _render(analysis, operation)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "union_as_intersection": _operation_alias(0, 1),
    "union_as_xor": _operation_alias(0, 2),
    "union_as_a_minus_b": _operation_alias(0, 3),
    "intersection_as_union": _operation_alias(1, 0),
    "intersection_as_xor": _operation_alias(1, 2),
    "intersection_as_a_minus_b": _operation_alias(1, 3),
    "xor_as_union": _operation_alias(2, 0),
    "xor_as_intersection": _operation_alias(2, 1),
    "xor_as_a_minus_b": _operation_alias(2, 3),
    "a_minus_b_as_union": _operation_alias(3, 0),
    "a_minus_b_as_intersection": _operation_alias(3, 1),
    "a_minus_b_as_xor": _operation_alias(3, 2),
    "column_only_header": _column_only_header,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"column_only_header": _column_only_header}

_OPERATION_RIVALS = {
    0: ["union_as_intersection", "union_as_xor", "union_as_a_minus_b"],
    1: ["intersection_as_union", "intersection_as_xor", "intersection_as_a_minus_b"],
    2: ["xor_as_union", "xor_as_intersection", "xor_as_a_minus_b", "column_only_header"],
    3: [
        "a_minus_b_as_union",
        "a_minus_b_as_intersection",
        "a_minus_b_as_xor",
        "column_only_header",
    ],
}


def _branch_witness(operation: int, rivals: Sequence[str]):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        if analysis["errors"] or analysis["operation"] != operation:
            return False
        truth = _render(analysis, operation)
        return all(SEMANTIC_RIVALS[name](grid) != truth for name in rivals)

    return witness


SEMANTIC_WITNESSES = {
    f"operation_{_OPERATION_NAMES[operation]}": _branch_witness(operation, rivals)
    for operation, rivals in _OPERATION_RIVALS.items()
}
WITNESS_RIVALS = {
    f"operation_{_OPERATION_NAMES[operation]}": list(rivals)
    for operation, rivals in _OPERATION_RIVALS.items()
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is missing input/output")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors}")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the intended rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the teaching grammar: {query_errors}")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        except Exception as exc:  # contracts should report rather than crash
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if fits:
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons
