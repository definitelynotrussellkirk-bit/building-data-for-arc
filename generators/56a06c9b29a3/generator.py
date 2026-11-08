"""Generator for 56a06c9b29a3 — infer one binary support operation.

The input is five equal panels separated by full-height color-9 columns.
Panels 1 and 2 are operands, panel 3 is their demonstrated result in color 2,
and panels 4 and 5 are a fresh operand pair.  The canonical Racket program
infers the first matching operation in this order:

    union, intersection, xor, a-minus-b, b-minus-a

and applies it to panels 4 and 5.  Normal draws construct witnesses for all
four cell relations (off/off, on/off, off/on, on/on), so every operation is
non-empty and the demonstration identifies exactly one operation.  The
structural checker also accepts a broader canonical-style case only when every
operation matching the demonstration yields the same query answer.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "56a06c9b29a3"
TASK_ID = "56a06c9b29a3"
VERSION = "4.0.0"  # keyed/observable axes, canonical palette lessons, structural self-check
RULE_HASH = "d79838837a8c"  # sha256 of whitespace-normalized canonical target rule

SUMMARY = (
    "Exactly five equal panels separated by single full-height color-9 columns. "
    "Panels 1 and 2 demonstrate one support operation by producing panel 3 in "
    "color 2; panels 4 and 5 are a new query pair.  Infer the unique operation "
    "from union/intersection/xor/A-minus-B/B-minus-A and apply it to the query. "
    "Every generated operand pair contains overlap, A-only, B-only, and empty "
    "cells, so all five operations are distinguishable and non-empty."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0 and divider columns are 9",
    "exactly five equal-width panels are separated by four single full-height 9 columns",
    "panels 1, 2, 4, and 5 are non-empty monochrome operand masks",
    "panel 3 contains only 0/2 and matches at least one ordered operation",
    "normal generated pairs contain off/off, A-only, B-only, and overlap witnesses",
    "a non-unique canonical-style demo is lawful only when all matching operations agree on the query answer",
]

OPS = ("union", "intersection", "xor", "a-minus-b", "b-minus-a")
PALETTE_KINDS = ("paired", "demo_mixed", "query_mixed", "all_distinct")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "panel_h": {
        "type": "int",
        "default": "difficulty-skewed 3..6",
        "valid": "3..6",
    },
    "panel_w": {
        "type": "int",
        "default": "difficulty-skewed 3..5",
        "valid": "3..5",
    },
    "operation": {
        "type": "str",
        "default": "rng",
        "valid": "union|intersection|xor|a-minus-b|b-minus-a",
    },
    "op1_color": {
        "type": "color",
        "default": "rng excluding 0 and 9",
        "valid": "1..8",
    },
    "palette_kind": {
        "type": "str",
        "default": "paired-biased rng",
        "valid": "paired|demo_mixed|query_mixed|all_distinct",
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_PALETTE_PRIOR = (
    "paired",
    "paired",
    "paired",
    "paired",
    "demo_mixed",
    "query_mixed",
    "all_distinct",
)
_RELATION_WEIGHTS = {
    "easy": (6, 2, 2, 1),
    "medium": (4, 3, 3, 2),
    "hard": (2, 3, 3, 4),
}


def _band(difficulty) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return difficulty
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        value = max(0.0, min(1.0, float(difficulty)))
        return "easy" if value < 1 / 3 else "hard" if value >= 2 / 3 else "medium"
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _applyop(name, a, b):
    """Apply a support operation and render true cells as color 2."""
    height, width = len(a), len(a[0])
    out = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            av = a[row][col] != 0
            bv = b[row][col] != 0
            if name == "union":
                on = av or bv
            elif name == "intersection":
                on = av and bv
            elif name == "xor":
                on = av != bv
            elif name == "a-minus-b":
                on = av and not bv
            elif name == "b-minus-a":
                on = bv and not av
            else:
                raise ValueError(f"unknown operation: {name!r}")
            out[row][col] = 2 if on else 0
    return out


def _operand_pair(rng, height: int, width: int, band: str):
    """Construct masks with all four binary cell relations represented."""
    cells = [(row, col) for row in range(height) for col in range(width)]
    rng.shuffle(cells)
    relations = [(False, False), (True, False), (False, True), (True, True)]
    weights = _RELATION_WEIGHTS[band]
    relations.extend(rng.choices(relations, weights=weights, k=len(cells) - 4))
    rng.shuffle(relations)

    left = full_grid(height, width, 0)
    right = full_grid(height, width, 0)
    for (row, col), (left_on, right_on) in zip(cells, relations):
        left[row][col] = int(left_on)
        right[row][col] = int(right_on)
    return left, right


def _operand_colors(ctx, palette_kind: str, op1_color: int):
    legal = [color for color in range(1, 9) if color != op1_color]
    rng = ctx.draw_rng("operand_colors")
    rng.shuffle(legal)
    if palette_kind == "paired":
        return op1_color, op1_color, legal[0], legal[0]
    if palette_kind == "demo_mixed":
        return op1_color, legal[0], legal[1], legal[1]
    if palette_kind == "query_mixed":
        return op1_color, op1_color, legal[0], legal[1]
    if palette_kind == "all_distinct":
        return op1_color, legal[0], legal[1], legal[2]
    raise ValueError(f"unknown palette_kind: {palette_kind!r}")


def _paint_panel(grid, panel, color: int, left: int) -> None:
    for row, values in enumerate(panel):
        for col, value in enumerate(values):
            if value:
                grid[row][left + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("panel_h", 3, 6)
    width = ctx.draw_int_diff("panel_w", 3, 5)
    operation = ctx.draw_choice("operation", OPS)
    op1_color = ctx.draw_color("op1_color", exclude={0, 9})
    palette_kind = ctx.draw_choice("palette_kind", _PALETTE_PRIOR)

    demo_a, demo_b = _operand_pair(ctx.draw_rng("demo_masks"), height, width, band)
    query_a, query_b = _operand_pair(ctx.draw_rng("query_masks"), height, width, band)
    demo_out = _applyop(operation, demo_a, demo_b)
    colors = _operand_colors(ctx, palette_kind, op1_color)
    panels = (
        (demo_a, colors[0]),
        (demo_b, colors[1]),
        (demo_out, 2),
        (query_a, colors[2]),
        (query_b, colors[3]),
    )

    total_width = 5 * width + 4
    grid = full_grid(height, total_width, 0)
    left = 0
    for index, (panel, color) in enumerate(panels):
        _paint_panel(grid, panel, color, left)
        left += width
        if index < 4:
            for row in range(height):
                grid[row][left] = 9
            left += 1
    return grid


def _split_panels(grid):
    height, width = len(grid), len(grid[0])
    separators = [
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    ]
    panels = []
    start = 0
    for separator in separators + [width]:
        panels.append([row[start:separator] for row in grid])
        start = separator + 1
    return separators, panels


def _support(panel):
    return [[int(value != 0) for value in row] for row in panel]


def _relations(left, right):
    return {
        (bool(left[row][col]), bool(right[row][col]))
        for row in range(len(left))
        for col in range(len(left[0]))
    }


def _single_color(panel):
    colors = {value for row in panel for value in row if value != 0}
    return next(iter(colors)) if len(colors) == 1 else None


def _palette_kind(colors):
    first, second, fourth, fifth = colors
    demo_same = first == second
    query_same = fourth == fifth
    if demo_same and query_same and first != fourth:
        return "paired"
    if not demo_same and query_same and fourth not in {first, second}:
        return "demo_mixed"
    if demo_same and not query_same and first not in {fourth, fifth}:
        return "query_mixed"
    if len(set(colors)) == 4:
        return "all_distinct"
    return None


def _analysis(grid):
    errors = []
    facts = {}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return facts, ["empty or non-grid value"]
    height, total_width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != total_width for row in grid):
        return facts, ["ragged grid"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid has a non-integer or non-ARC color")
    if not 3 <= height <= 6:
        errors.append(f"panel height must be 3..6, got {height}")

    separators, panels = _split_panels(grid)
    if len(separators) != 4 or len(panels) != 5:
        errors.append(
            f"expected five panels split by four full-height 9 columns, got "
            f"{len(panels)} panels and {len(separators)} separators"
        )
        return facts, errors
    widths = [len(panel[0]) for panel in panels]
    if len(set(widths)) != 1 or not 3 <= widths[0] <= 5:
        errors.append(f"panel widths must be equal and in 3..5, got {widths}")
    expected_separators = [widths[0] + index * (widths[0] + 1) for index in range(4)]
    if separators != expected_separators:
        errors.append(
            f"divider columns must be single and evenly spaced at {expected_separators}, "
            f"got {separators}"
        )
    if any(value == 9 for panel in panels for row in panel for value in row):
        errors.append("divider color 9 leaked inside a data panel")

    operand_indices = (0, 1, 3, 4)
    operand_colors = [_single_color(panels[index]) for index in operand_indices]
    for index, color in zip(operand_indices, operand_colors):
        if color is None:
            errors.append(f"operand panel {index + 1} must be non-empty and monochrome")
    if any(value not in (0, 2) for row in panels[2] for value in row):
        errors.append("panel 3 must contain only background 0 and result color 2")
    if not any(value == 2 for row in panels[2] for value in row):
        errors.append("panel 3 result must be non-empty")

    supports = [_support(panel) for panel in panels]
    required_relations = {(False, False), (True, False), (False, True), (True, True)}
    relation_missing = {}
    for label, left, right in (
        ("demo", supports[0], supports[1]),
        ("query", supports[3], supports[4]),
    ):
        relation_missing[label] = required_relations - _relations(left, right)

    matches = [
        operation
        for operation in OPS
        if _applyop(operation, supports[0], supports[1]) == panels[2]
    ]
    answer_equivalent_ambiguity = False
    if not matches:
        errors.append("panel 3 does not match any declared operation")
    elif len(matches) == 1:
        for label, missing in relation_missing.items():
            if missing:
                errors.append(
                    f"{label} operand pair misses binary relations {sorted(missing)}"
                )
    else:
        candidate_outputs = {
            tuple(map(tuple, _applyop(operation, supports[3], supports[4])))
            for operation in matches
        }
        answer_equivalent_ambiguity = len(candidate_outputs) == 1
        if not answer_equivalent_ambiguity:
            errors.append(
                f"demo matches {matches}, which disagree on the query answer"
            )
    palette_kind = None
    if all(color is not None for color in operand_colors):
        palette_kind = _palette_kind(operand_colors)
        if palette_kind is None:
            errors.append(f"operand colors do not match a declared palette lesson: {operand_colors}")

    facts.update(
        {
            "panel_h": height,
            "panel_w": widths[0],
            "operation": matches[0] if matches else None,
            "operation_matches": tuple(matches),
            "answer_equivalent_ambiguity": answer_equivalent_ambiguity,
            "relation_missing": relation_missing,
            "op1_color": operand_colors[0],
            "palette_kind": palette_kind,
            "separators": tuple(separators),
            "panels": panels,
        }
    )
    return facts, errors


def observe_overrides(grid):
    facts, errors = _analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "panel_h": facts["panel_h"],
        "panel_w": facts["panel_w"],
        "operation": facts["operation"],
        "op1_color": facts["op1_color"],
        "palette_kind": facts["palette_kind"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts, errors = _analysis(grid)
    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if not errors and requested:
        observed = {
            "panel_h": facts["panel_h"],
            "panel_w": facts["panel_w"],
            "operation": facts["operation"],
            "op1_color": facts["op1_color"],
            "palette_kind": facts["palette_kind"],
        }
        for axis, expected in requested.items():
            if axis in observed and observed[axis] != expected:
                errors.append(
                    f"override {axis} requested {expected!r}, observed {observed[axis]!r}"
                )
    return errors
