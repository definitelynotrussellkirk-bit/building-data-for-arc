"""Generator for arc_puzzle_bank_twentythird21:H157.

Five panels are separated by four full-height color-8 columns.  Panels A, B,
and O demonstrate one binary support operation; panels X and Y are the query.
The selected canonical Racket program's reachable operations are union,
intersection, and xor, and all three emit a binary 0/1 output.

The selected source contains a syntactic ``left-minus`` name after those three,
but its matching predicate falls through the same ``else`` branch as xor.
Consequently it cannot identify a fourth behavior: whenever that predicate
matches, xor has already matched first.  This generator follows the reachable
canonical semantics rather than inventing an unexecutable fourth branch.

Normal draws make A/B and X/Y contain all four binary cell relations
(off/off, A-only, B-only, overlap), so the embedded demonstration identifies a
unique operation and every fixed-operation shortcut disagrees on the query.
The structural checker also accepts a canonical ambiguous demonstration when
all matching operations produce the same query answer; canonical train[0] is
exactly that lawful union/xor case.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "59d647aebebb"
TASK_ID = "59d647aebebb"
VERSION = "3.0.0"
RULE_HASH = "a5b2f7cc2e55"

SUMMARY = (
    "Five equal-width panels split by four full-height color-8 columns. A, B, "
    "and O demonstrate the first matching reachable operation in canonical "
    "order union/intersection/xor; apply it to X and Y and emit a binary 0/1 "
    "grid. Normal draws contain every binary relation in both operand pairs, "
    "making the operation and query answer identifiable."
)

EXAMPLES_NEEDED = 2
SCHEDULE_PROFILES = tuple(range(EXAMPLES_NEEDED + 1))

INVARIANTS = [
    "background is 0 and exactly four single full-height separator columns are color 8",
    "all five panels have one shared width; A/B/O and X/Y therefore align cellwise",
    "each panel is non-empty and monochrome on background 0",
    "O is the support result of the first matching reachable operation on A and B",
    "normal generated A/B and X/Y pairs contain off/off, A-only, B-only, and overlap cells",
    "an ambiguous canonical-style demo is lawful only when every match gives the same query output",
]

OPS = ("union", "intersection", "xor")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-scaled 4..10",
        "valid": "4..10",
    },
    "panel_w": {
        "type": "int",
        "default": "scheduled canonical anchors plus 3..5",
        "valid": "3..5",
    },
    "operation": {
        "type": "str",
        "default": "sample_index modulo three",
        "valid": "union|intersection|xor",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 1..4 distinct panel colors",
        "valid": "1..4",
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)
_RELATIONS = ((0, 0), (1, 0), (0, 1), (1, 1))


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        value = max(0.0, min(1.0, float(difficulty)))
        if value < 1 / 3:
            return "easy"
        if value >= 2 / 3:
            return "hard"
        return "medium"
    raise ValueError(f"unsupported difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Three-slot lesson schedule; boundary slots are canonical-profile anchors."""
    del seed, difficulty
    return int(sample_index) % (EXAMPLES_NEEDED + 1)


def _scheduled_axes(sample_index: int, band: str) -> tuple[int, int, int, str]:
    slot = int(sample_index) % (EXAMPLES_NEEDED + 1)
    episode = int(sample_index) // (EXAMPLES_NEEDED + 1)
    operation = OPS[int(sample_index) % len(OPS)]
    if slot in (0, EXAMPLES_NEEDED):
        return 4, 4, 1, operation

    height_ranges = {
        "easy": (4, 6),
        "medium": (5, 8),
        "hard": (7, 10),
    }
    lo, hi = height_ranges[band]
    height = lo + ((episode + slot) % (hi - lo + 1))
    panel_w = 3 + ((episode * 2 + slot) % 3)
    palette_size = 1 + ((episode + slot) % 4)
    return height, panel_w, palette_size, operation


def _draw_scheduled_int(
    ctx: Any,
    overrides: dict[str, Any],
    label: str,
    scheduled: int,
    lo: int,
    hi: int,
) -> int:
    if overrides.get(label) is not None:
        return int(ctx.draw_int(label, lo, hi))
    return int(ctx.draw_int(label, scheduled, scheduled))


def _draw_scheduled_choice(
    ctx: Any,
    overrides: dict[str, Any],
    label: str,
    scheduled: str,
    options: tuple[str, ...],
) -> str:
    if overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _apply_support_op(
    name: str,
    left: list[list[int]],
    right: list[list[int]],
) -> list[list[int]]:
    height, width = len(left), len(left[0])
    output = [[0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            a_on = left[row][col] != 0
            b_on = right[row][col] != 0
            if name == "union":
                keep = a_on or b_on
            elif name == "intersection":
                keep = a_on and b_on
            elif name == "xor":
                keep = a_on != b_on
            else:
                raise ValueError(f"unknown operation: {name!r}")
            output[row][col] = int(keep)
    return output


def _relation_pair(
    rng: Any,
    height: int,
    width: int,
    band: str,
) -> tuple[list[list[int]], list[list[int]]]:
    """Build two masks with all four binary relations represented."""
    positions = [(row, col) for row in range(height) for col in range(width)]
    rng.shuffle(positions)
    assignments = list(_RELATIONS)
    weighted = {
        "easy": ((0, 0), (0, 0), (1, 0), (0, 1), (1, 1)),
        "medium": ((0, 0), (1, 0), (0, 1), (1, 1), (1, 1)),
        "hard": ((1, 0), (0, 1), (1, 1), (1, 1), (0, 0)),
    }[band]
    assignments.extend(
        rng.choice(weighted) for _ in range(len(positions) - len(assignments))
    )
    rng.shuffle(assignments)

    left = [[0] * width for _ in range(height)]
    right = [[0] * width for _ in range(height)]
    for (row, col), (a_on, b_on) in zip(positions, assignments):
        left[row][col] = a_on
        right[row][col] = b_on
    return left, right


def _paint_panel(
    grid: list[list[int]],
    panel: list[list[int]],
    color: int,
    left: int,
) -> None:
    for row, values in enumerate(panel):
        for col, value in enumerate(values):
            if value:
                grid[row][left + col] = color


def _panel_colors(
    ctx: Any,
    palette_size: int,
    *,
    canonical_slot: bool,
    palette_overridden: bool,
) -> list[int]:
    if canonical_slot and palette_size == 1 and not palette_overridden:
        palette = [1]
    else:
        palette = list(
            ctx.draw_distinct_colors(
                "panel_colors", n=palette_size, exclude={0, 8}
            )
        )
    colors = [palette[index % palette_size] for index in range(5)]
    ctx.draw_rng("panel_color_assignment").shuffle(colors)
    return colors


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    unknown = sorted(
        name
        for name, value in overrides.items()
        if value is not None and name not in _ALLOWED_OVERRIDES
    )
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
    scheduled_h, scheduled_w, scheduled_palette, scheduled_op = _scheduled_axes(
        sample_index, band
    )
    height = _draw_scheduled_int(ctx, overrides, "grid_h", scheduled_h, 4, 10)
    panel_w = _draw_scheduled_int(
        ctx, overrides, "panel_w", scheduled_w, 3, 5
    )
    palette_size = _draw_scheduled_int(
        ctx, overrides, "palette_size", scheduled_palette, 1, 4
    )
    operation = _draw_scheduled_choice(
        ctx, overrides, "operation", scheduled_op, OPS
    )

    demo_a, demo_b = _relation_pair(
        ctx.draw_rng("demo_masks"), height, panel_w, band
    )
    query_x, query_y = _relation_pair(
        ctx.draw_rng("query_masks"), height, panel_w, band
    )
    demo_o = _apply_support_op(operation, demo_a, demo_b)
    canonical_slot = schedule_profile(seed, sample_index, difficulty) in (
        0,
        EXAMPLES_NEEDED,
    )
    colors = _panel_colors(
        ctx,
        palette_size,
        canonical_slot=canonical_slot,
        palette_overridden=overrides.get("palette_size") is not None,
    )

    panels = (demo_a, demo_b, demo_o, query_x, query_y)
    total_width = 5 * panel_w + 4
    grid = full_grid(height, total_width, 0)
    left = 0
    for index, (panel, color) in enumerate(zip(panels, colors)):
        _paint_panel(grid, panel, color, left)
        left += panel_w
        if index < 4:
            for row in range(height):
                grid[row][left] = 8
            left += 1

    observed = observe_overrides(grid)
    for axis, requested in ctx.recorded_draws().items():
        if axis in AXES and observed.get(axis) != requested:
            raise RuntimeError(
                f"axis realization mismatch for {axis}: requested {requested!r}, "
                f"observed {observed.get(axis)!r}"
            )
    return [row[:] for row in grid]


def _split_panels(
    grid: list[list[int]],
) -> tuple[list[int], list[list[list[int]]]]:
    height, width = len(grid), len(grid[0])
    separators = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    panels: list[list[list[int]]] = []
    start = 0
    for separator in separators + [width]:
        panels.append([row[start:separator] for row in grid])
        start = separator + 1
    return separators, panels


def _support(panel: list[list[int]]) -> list[list[int]]:
    return [[int(value != 0) for value in row] for row in panel]


def _relations(
    left: list[list[int]],
    right: list[list[int]],
) -> set[tuple[int, int]]:
    return {
        (int(left[row][col] != 0), int(right[row][col] != 0))
        for row in range(len(left))
        for col in range(len(left[0]))
    }


def _single_color(panel: list[list[int]]) -> int | None:
    colors = {value for row in panel for value in row if value != 0}
    return next(iter(colors)) if len(colors) == 1 else None


def _analysis(grid: Any) -> tuple[dict[str, Any], list[str]]:
    facts: dict[str, Any] = {}
    errors: list[str] = []
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return facts, ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return facts, ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return facts, ["cells must be integer ARC colors in 0..9"]

    height = len(grid)
    if not 4 <= height <= 10:
        errors.append(f"grid height must be 4..10, got {height}")

    separators, panels = _split_panels(grid)
    if len(separators) != 4 or len(panels) != 5:
        errors.append(
            "expected five panels split by four full-height color-8 columns, "
            f"got {len(panels)} panels and {len(separators)} separators"
        )
        return facts, errors
    widths = [len(panel[0]) if panel and panel[0] else 0 for panel in panels]
    if len(set(widths)) != 1 or not 3 <= widths[0] <= 5:
        errors.append(f"all panel widths must be equal and in 3..5, got {widths}")
        return facts, errors
    panel_w = widths[0]
    expected_separators = [
        panel_w + index * (panel_w + 1) for index in range(4)
    ]
    if separators != expected_separators:
        errors.append(
            "separator columns must be single and evenly spaced at "
            f"{expected_separators}, got {separators}"
        )
    if any(value == 8 for panel in panels for row in panel for value in row):
        errors.append("separator color 8 leaked inside a data panel")

    panel_colors = [_single_color(panel) for panel in panels]
    for index, color in enumerate(panel_colors):
        if color is None:
            errors.append(f"panel {index + 1} must be non-empty and monochrome")
    if errors:
        return facts, errors

    supports = [_support(panel) for panel in panels]
    matches = [
        operation
        for operation in OPS
        if _apply_support_op(operation, supports[0], supports[1]) == supports[2]
    ]
    if not matches:
        errors.append("demonstration output does not match a reachable operation")

    required_relations = set(_RELATIONS)
    missing_relations = {
        "demo": required_relations - _relations(supports[0], supports[1]),
        "query": required_relations - _relations(supports[3], supports[4]),
    }
    answer_equivalent_ambiguity = False
    if len(matches) > 1:
        candidate_outputs = {
            tuple(
                map(
                    tuple,
                    _apply_support_op(operation, supports[3], supports[4]),
                )
            )
            for operation in matches
        }
        answer_equivalent_ambiguity = len(candidate_outputs) == 1
        if not answer_equivalent_ambiguity:
            errors.append(
                f"demonstration matches {matches}, which disagree on the query answer"
            )
    elif len(matches) == 1:
        for label, missing in missing_relations.items():
            if missing:
                errors.append(
                    f"{label} operand pair misses binary relations {sorted(missing)}"
                )

    palette_size = len({int(color) for color in panel_colors if color is not None})
    if not 1 <= palette_size <= 4:
        errors.append(f"panel palette must contain 1..4 colors, got {palette_size}")

    facts.update(
        {
            "grid_h": height,
            "panel_w": panel_w,
            "palette_size": palette_size,
            "operation": matches[0] if matches else None,
            "operation_matches": tuple(matches),
            "answer_equivalent_ambiguity": answer_equivalent_ambiguity,
            "missing_relations": missing_relations,
            "separators": tuple(separators),
            "panel_colors": tuple(panel_colors),
            "panels": panels,
            "supports": supports,
        }
    )
    return facts, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    facts, errors = _analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": facts["grid_h"],
        "panel_w": facts["panel_w"],
        "operation": facts["operation"],
        "palette_size": facts["palette_size"],
    }


def self_check(
    grid: Any,
    *,
    difficulty: Any = None,
    meta: Any = None,
) -> list[str]:
    del difficulty
    facts, errors = _analysis(grid)
    requested = (
        ((meta or {}).get("overrides") or {})
        if isinstance(meta, dict)
        else {}
    )
    unknown = sorted(set(requested) - _ALLOWED_OVERRIDES)
    if unknown:
        errors.append(f"unknown override(s): {', '.join(unknown)}")
    if not errors and requested:
        observed = {
            "grid_h": facts["grid_h"],
            "panel_w": facts["panel_w"],
            "operation": facts["operation"],
            "palette_size": facts["palette_size"],
        }
        for axis, expected in requested.items():
            if expected is not None and observed.get(axis) != expected:
                errors.append(
                    f"override {axis} requested {expected!r}, observed "
                    f"{observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Own the canonical grammar while rejecting malformed or rule-hiding scenes."""
    return _analysis(grid)[1]


def _fixed_operation_solver(operation: str) -> Callable[[Any], list[list[int]]]:
    def solve(grid: Any) -> list[list[int]]:
        facts, errors = _analysis(grid)
        if errors:
            raise ValueError("invalid five-panel input: " + "; ".join(errors))
        supports = facts["supports"]
        return _apply_support_op(operation, supports[3], supports[4])

    return solve


SEMANTIC_RIVALS = {
    f"always_{operation}": _fixed_operation_solver(operation)
    for operation in OPS
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _operation_witness(operation: str) -> Callable[[Any], bool]:
    def witness(grid: Any) -> bool:
        facts, errors = _analysis(grid)
        return not errors and facts["operation_matches"] == (operation,)

    return witness


SEMANTIC_WITNESSES = {
    f"operation_{operation}": _operation_witness(operation)
    for operation in OPS
}
WITNESS_RIVALS = {
    f"operation_{operation}": [
        f"always_{other}" for other in OPS if other != operation
    ]
    for operation in OPS
}


def _pair_operation(pair: Any, label: str, reasons: list[str]) -> str | None:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        reasons.append(f"{label} is not an input/output pair")
        return None
    facts, errors = _analysis(pair["input"])
    if errors:
        reasons.append(f"{label} input invalid: {'; '.join(errors)}")
        return None
    matches = facts["operation_matches"]
    if len(matches) != 1:
        reasons.append(f"{label} demonstration is not unique: {list(matches)}")
        return None
    supports = facts["supports"]
    expected = _apply_support_op(matches[0], supports[3], supports[4])
    if pair["output"] != expected:
        reasons.append(
            f"{label} output disagrees with selected operation {matches[0]}"
        )
    return str(matches[0])


def lesson_identifiable(
    demos: list[dict[str, Any]],
    query: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    demo_operations = [
        operation
        for index, pair in enumerate(demos[:EXAMPLES_NEEDED])
        if (
            operation := _pair_operation(pair, f"demo[{index}]", reasons)
        )
        is not None
    ]
    if len(set(demo_operations)) != EXAMPLES_NEEDED:
        reasons.append("the two demonstrations must exercise distinct operations")
    query_operation = _pair_operation(query, "query", reasons)
    covered = set(demo_operations)
    if query_operation is not None:
        covered.add(query_operation)
    missing = set(OPS) - covered
    if missing:
        reasons.append(
            f"demonstrations plus query do not cover operations {sorted(missing)}"
        )
    if query_operation is not None and query_operation in set(demo_operations):
        reasons.append("query repeats a demonstrated operation instead of testing the third")
    return reasons
