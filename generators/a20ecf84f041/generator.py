"""Semantic generator for ARC task a20ecf84f041.

Maroon separators split the input into a 2x3 grid of square panels.  The top
row is a worked Boolean-mask example ``A, B, OP(A, B)``; the bottom row is the
query ``D, E, blank``.  Infer union, intersection, or XOR from the worked
example and write the query result in red into the blank panel.

Generated lessons deliberately contain all four occupancy states (00, 10, 01,
11) in both operand pairs.  That makes the demonstrated operator unique and
prevents copy-one-side, count-only, and no-overlap shortcuts.  Operand colors
vary across the legal non-divider palette and may themselves be red, as in one
canonical example; every computed result is red.  This prevents a fixed
"non-red means operand" role shortcut while preserving the authored rule.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "a20ecf84f041"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "94bd99d7c7c5"
SUMMARY = (
    "Maroon dividers form two rows by three equal square panels. The top row "
    "demonstrates union, intersection, or XOR on occupancy masks; the bottom "
    "row supplies a new pair and a blank answer panel. Operand pairs use one "
    "non-divider color each (including red on some draws), computed masks are "
    "red, and generated demo/query "
    "pairs each contain 00, 10, 01, and 11 witnesses."
)

_OPS = ("union", "intersection", "xor")
_COLOR_RELATIONS = ("same", "different")
_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

INVARIANTS = [
    "exactly one full maroon row and two full maroon columns form six equal square panels",
    "the two operands in each row share one non-divider color; the answer color is red",
    "the top-right panel equals at least one of union/intersection/xor on the top masks",
    "if several operations fit the demonstration, they agree on the query answer",
    "the bottom-right panel is blank and the inferred query answer is non-empty",
    "generated demo and query pairs contain witnesses for all four Boolean occupancy states",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ()

AXES = {
    "panel_size": {
        "type": "int",
        "default": "difficulty-skewed rng",
        "valid": "3..6",
        "doc": "side length of every square panel",
    },
    "op": {
        "type": "str",
        "default": "uniform rng",
        "valid": "union|intersection|xor",
        "doc": "Boolean operation demonstrated in the top row and applied below",
    },
    "operand_color_relation": {
        "type": "str",
        "default": "uniform rng",
        "valid": "same|different",
        "doc": "whether the top and bottom operand pairs use the same data color",
    },
}


def _validate_grid(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty grid"], 0, 0
    height, width = len(grid), len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append("grid must be rectangular")
            break
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 9
            for value in row
        ):
            errors.append("grid colors must be integers in 0..9")
            break
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    return errors, height, width


def _subgrid(grid, top, left, bottom, right):
    return [list(row[left : right + 1]) for row in grid[top : bottom + 1]]


def _apply(left, right, op):
    height, width = len(left), len(left[0])
    output = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            a_on = left[row][col] != 0
            b_on = right[row][col] != 0
            keep = (
                a_on or b_on
                if op == "union"
                else a_on and b_on
                if op == "intersection"
                else a_on != b_on
            )
            output[row][col] = 2 if keep else 0
    return output


def _truth_state_counts(left, right):
    counts = [0, 0, 0, 0]
    for row in range(len(left)):
        for col in range(len(left[0])):
            state = int(left[row][col] != 0) + 2 * int(right[row][col] != 0)
            counts[state] += 1
    return tuple(counts)


def _operand_color(panel, name, errors):
    colors = {value for row in panel for value in row if value != 0}
    if len(colors) != 1:
        errors.append(f"{name} must contain exactly one nonzero operand color, found {sorted(colors)}")
        return None
    color = next(iter(colors))
    if color == 9:
        errors.append(f"{name} uses divider color 9 as operand data")
        return None
    return color


def _analyze(grid):
    errors, height, width = _validate_grid(grid)
    result = {"errors": errors, "facts": {}}
    if errors:
        return result

    full_rows = [
        row for row in range(height) if all(grid[row][col] == 9 for col in range(width))
    ]
    full_cols = [
        col for col in range(width) if all(grid[row][col] == 9 for row in range(height))
    ]
    if len(full_rows) != 1:
        errors.append(f"expected exactly one full maroon divider row, found {len(full_rows)}")
    if len(full_cols) != 2:
        errors.append(f"expected exactly two full maroon divider columns, found {len(full_cols)}")
    if errors:
        return result

    divider_row = full_rows[0]
    left_divider, right_divider = full_cols
    panel_size = divider_row
    expected_geometry = (
        3 <= panel_size <= 6
        and height == 2 * panel_size + 1
        and width == 3 * panel_size + 2
        and left_divider == panel_size
        and right_divider == 2 * panel_size + 1
    )
    if not expected_geometry:
        errors.append(
            "divider geometry must be p x p panels with p in 3..6: "
            f"shape={height}x{width}, row={divider_row}, cols={full_cols}"
        )
        return result

    panels = (
        _subgrid(grid, 0, 0, divider_row - 1, left_divider - 1),
        _subgrid(grid, 0, left_divider + 1, divider_row - 1, right_divider - 1),
        _subgrid(grid, 0, right_divider + 1, divider_row - 1, width - 1),
        _subgrid(grid, divider_row + 1, 0, height - 1, left_divider - 1),
        _subgrid(grid, divider_row + 1, left_divider + 1, height - 1, right_divider - 1),
        _subgrid(grid, divider_row + 1, right_divider + 1, height - 1, width - 1),
    )
    demo_left, demo_right, demo_result, query_left, query_right, query_blank = panels

    top_left_color = _operand_color(demo_left, "top-left panel", errors)
    top_right_color = _operand_color(demo_right, "top-middle panel", errors)
    bottom_left_color = _operand_color(query_left, "bottom-left panel", errors)
    bottom_right_color = _operand_color(query_right, "bottom-middle panel", errors)
    if top_left_color is not None and top_right_color is not None and top_left_color != top_right_color:
        errors.append("top operand panels must use the same data color")
    if bottom_left_color is not None and bottom_right_color is not None and bottom_left_color != bottom_right_color:
        errors.append("bottom operand panels must use the same data color")

    demo_palette = {value for row in demo_result for value in row}
    if not demo_palette <= {0, 2}:
        errors.append(f"top-right result panel must contain only 0/2, found {sorted(demo_palette)}")
    if any(value != 0 for row in query_blank for value in row):
        errors.append("bottom-right query panel must be blank")
    if errors:
        return result

    matching_ops = tuple(
        op for op in _OPS if _apply(demo_left, demo_right, op) == demo_result
    )
    if not matching_ops:
        errors.append("top result matches none of union, intersection, or xor")
        return result

    candidate_answers = [_apply(query_left, query_right, op) for op in matching_ops]
    if any(answer != candidate_answers[0] for answer in candidate_answers[1:]):
        errors.append(
            "demonstration is ambiguous and matching operations disagree on the query answer"
        )
        return result
    answer = candidate_answers[0]
    if not any(value == 2 for row in answer for value in row):
        errors.append("inferred query answer must contain at least one red cell")
        return result

    output = copy.deepcopy(grid)
    for row in range(panel_size):
        for col in range(panel_size):
            output[divider_row + 1 + row][right_divider + 1 + col] = answer[row][col]

    top_color = top_left_color
    bottom_color = bottom_left_color
    facts = {
        "panel_size": panel_size,
        "divider_row": divider_row,
        "divider_cols": (left_divider, right_divider),
        "panels": panels,
        "matching_ops": matching_ops,
        "op": matching_ops[0] if len(matching_ops) == 1 else "|".join(matching_ops),
        "top_operand_color": top_color,
        "bottom_operand_color": bottom_color,
        "operand_color_relation": "same" if top_color == bottom_color else "different",
        "top_truth_states": _truth_state_counts(demo_left, demo_right),
        "bottom_truth_states": _truth_state_counts(query_left, query_right),
        "answer": answer,
        "output": output,
    }
    result["facts"] = facts
    return result


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - set(AXES)
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        if not errors:
            facts = analysis["facts"]
            if "panel_size" in overrides and facts["panel_size"] != int(overrides["panel_size"]):
                errors.append(
                    f"requested panel_size {overrides['panel_size']}, observed {facts['panel_size']}"
                )
            if "op" in overrides and facts["matching_ops"] != (overrides["op"],):
                errors.append(
                    f"requested op {overrides['op']!r}, observed {facts['matching_ops']!r}"
                )
            if (
                "operand_color_relation" in overrides
                and facts["operand_color_relation"] != overrides["operand_color_relation"]
            ):
                errors.append(
                    "requested operand_color_relation "
                    f"{overrides['operand_color_relation']!r}, observed "
                    f"{facts['operand_color_relation']!r}"
                )
    return errors


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    if len(facts["matching_ops"]) != 1:
        raise ValueError(f"operation is not uniquely observable: {facts['matching_ops']!r}")
    return {
        "panel_size": facts["panel_size"],
        "op": facts["matching_ops"][0],
        "operand_color_relation": facts["operand_color_relation"],
    }


def rule_mirror(grid):
    """Input-pure Python mirror used only for focused structural tests."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["facts"]["output"])


def _truth_table_pair(rng, panel_size, color):
    states = [0, 1, 2, 3]
    states.extend(rng.randrange(4) for _ in range(panel_size * panel_size - 4))
    rng.shuffle(states)
    left = full_grid(panel_size, panel_size, 0)
    right = full_grid(panel_size, panel_size, 0)
    for index, state in enumerate(states):
        row, col = divmod(index, panel_size)
        if state & 1:
            left[row][col] = color
        if state & 2:
            right[row][col] = color
    return left, right


def _assemble(panel_size, panels):
    height, width = 2 * panel_size + 1, 3 * panel_size + 2
    grid = full_grid(height, width, 0)
    for col in range(width):
        grid[panel_size][col] = 9
    for row in range(height):
        grid[row][panel_size] = 9
        grid[row][2 * panel_size + 1] = 9

    placements = (
        (0, 0),
        (0, panel_size + 1),
        (0, 2 * panel_size + 2),
        (panel_size + 1, 0),
        (panel_size + 1, panel_size + 1),
    )
    for panel, (top, left) in zip(panels, placements):
        for row in range(panel_size):
            for col in range(panel_size):
                grid[top + row][left + col] = panel[row][col]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=None if difficulty == "default" else difficulty,
        overrides=overrides,
    )
    panel_size = context.draw_int_diff("panel_size", 3, 6)
    op = context.draw_choice("op", _OPS)
    color_relation = context.draw_choice("operand_color_relation", _COLOR_RELATIONS)
    color_a, color_b = context.draw_distinct_colors(
        "operand_colors", n=2, exclude={0, 9}
    )
    top_color = color_a
    bottom_color = color_a if color_relation == "same" else color_b

    demo_left, demo_right = _truth_table_pair(
        context.draw_rng("demo_truth_table"), panel_size, top_color
    )
    query_left, query_right = _truth_table_pair(
        context.draw_rng("query_truth_table"), panel_size, bottom_color
    )
    demo_result = _apply(demo_left, demo_right, op)
    grid = _assemble(
        panel_size,
        (demo_left, demo_right, demo_result, query_left, query_right),
    )

    analysis = _analyze(grid)
    expected_observation = {
        "panel_size": panel_size,
        "op": op,
        "operand_color_relation": color_relation,
    }
    if analysis["errors"]:
        raise RuntimeError("internal construction error: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    if not all(facts["top_truth_states"]) or not all(facts["bottom_truth_states"]):
        raise RuntimeError("internal construction error: missing Boolean truth-state witness")
    if observe_overrides(grid) != expected_observation:
        raise RuntimeError(
            f"internal construction mismatch: expected {expected_observation}, "
            f"observed {observe_overrides(grid)}"
        )
    return [row[:] for row in grid]
