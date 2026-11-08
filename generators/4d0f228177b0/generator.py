"""Semantic generator for ARC task 4d0f228177b0 / ac605cbb.

The input contains one copy at most of cue colors 1, 2, 3, and 6.
Each cue has a fixed expansion:

* 6 is the lower endpoint of a seven-cell vertical segment; its upper endpoint
  is also 6 and the five interior cells are gray (5).
* 3 is the upper endpoint of a four-cell vertical segment; its lower endpoint
  is also 3 and the two interior cells are gray.
* 1 grows a two-cell gray arm to the right and places a second 1 one row above
  the arm's far endpoint.
* 2 is the right endpoint of a five-cell horizontal segment centered on the
  rightmost non-2 cue strictly to its left.  If that center column contains a
  6/3 vertical segment and the 2-row crosses its interior, a yellow (4)
  diagonal continues down-left from the crossing.

The seven ordinary scene types mirror the seven canonical train/test cue
configurations.  A seven-demo lesson covers every type; the query repeats one
on a new placement template, so fixed-position and independent-symbol
shortcuts do not identify the answer.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4d0f228177b0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8c19064b012d"
EXAMPLES_NEEDED = 7
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "A square 9..11 zero-background grid contains one copy at most of cue "
    "colors 1, 2, 3, and 6. Color 6 grows upward into a seven-cell vertical "
    "segment, color 3 grows downward into a four-cell vertical segment, color "
    "1 grows a two-cell right arm with a second 1 above its tip, and color 2 "
    "is the right endpoint of a five-cell horizontal segment centered on the "
    "rightmost non-2 cue to its left. If that horizontal segment crosses the "
    "interior of a 6/3 vertical segment, paint a yellow diagonal down-left "
    "from the crossing. Ordinary seven-demo lessons cover every canonical cue "
    "configuration before querying the same rule on a new placement."
)

INVARIANTS = [
    "square 9..11 grid with background 0",
    "cue colors are a duplicate-free subset of {1,2,3,6}",
    "all cue-specific expansions fit in bounds and preserve every input cue",
    "a 2 is exactly two columns right of the rightmost non-2 cue to its left",
    "yellow 4 appears only when a 2-segment crosses a 6/3 vertical interior",
    "ordinary lessons cover all seven canonical cue configurations",
]

SCENARIOS = (
    "single_six",
    "three_one",
    "three_two_cross",
    "one_two_three_plain",
    "one_two_plain",
    "six_two_cross_one",
    "all_four_cross_six",
)
LAYOUT_TEMPLATES = tuple(f"p{i:02d}" for i in range(12))
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES = (
    "no_cue",
    "duplicate_cue",
    "orphan_two",
    "clipped_six",
    "unexpected_color",
)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

AXES = {
    "grid_size": {
        "type": "int",
        "default": "scenario-correlated canonical size",
        "valid": "9..11",
    },
    "scenario": {
        "type": "enum",
        "default": "seven-slot lesson schedule",
        "valid": "single_six|three_one|three_two_cross|one_two_three_plain|one_two_plain|six_two_cross_one|all_four_cross_six",
    },
    "layout_template": {
        "type": "enum",
        "default": "twelve-slot placement schedule",
        "valid": "p00|p01|p02|p03|p04|p05|p06|p07|p08|p09|p10|p11",
    },
}

_CANONICAL_SIZE = {
    "single_six": 9,
    "three_one": 10,
    "three_two_cross": 10,
    "one_two_three_plain": 11,
    "one_two_plain": 10,
    "six_two_cross_one": 11,
    "all_four_cross_six": 11,
}
_SCENARIO_COLOR_SETS = {
    "single_six": frozenset({6}),
    "three_one": frozenset({1, 3}),
    "three_two_cross": frozenset({2, 3}),
    "one_two_three_plain": frozenset({1, 2, 3}),
    "one_two_plain": frozenset({1, 2}),
    "six_two_cross_one": frozenset({1, 2, 6}),
    "all_four_cross_six": frozenset({1, 2, 3, 6}),
}


def _schedule_index(seed: int, sample_index: int, difficulty: str | None) -> int:
    band_offset = {None: 0, "easy": 97, "medium": 211, "hard": 353}[difficulty]
    return int(seed) * 136 + int(sample_index) + band_offset


def schedule_profile(seed, sample_index, difficulty=None):
    """The seven-way scenario schedule audited by the semantic gate."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    t = _schedule_index(seed, sample_index, difficulty)
    return SCENARIOS[t % len(SCENARIOS)]


SCHEDULE_PROFILES = SCENARIOS


def _layout_index(template: str) -> int:
    try:
        return LAYOUT_TEMPLATES.index(template)
    except ValueError as exc:
        raise ValueError(
            f"unknown layout_template {template!r}; valid={LAYOUT_TEMPLATES}"
        ) from exc


def _base_anchor(size: int, column_slot: int) -> int:
    anchors = (2, max(3, (size - 1) // 2 - 1), size - 5)
    return anchors[column_slot]


def _safe_one_column(size: int, blocked_columns: set[int]) -> int:
    candidates = (0, size - 3, 1, size - 4, 2, size - 5)
    for column in candidates:
        if not 0 <= column <= size - 3:
            continue
        if {column, column + 1, column + 2}.isdisjoint(blocked_columns):
            return column
    raise ValueError(
        f"no lawful color-1 arm column in size={size} with blocked={sorted(blocked_columns)}"
    )


def _build_scene(size: int, scenario: str, layout_template: str) -> list[list[int]]:
    """Build one deterministic placement template for a semantic scenario."""
    if not 9 <= size <= 11:
        raise ValueError(f"grid_size must be 9..11, got {size}")
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario!r}")
    layout = _layout_index(layout_template)
    column_slot = layout % 3
    row_slot = layout // 3
    anchor = _base_anchor(size, column_slot)
    grid = full_grid(size, size, 0)

    if scenario == "single_six":
        columns = (1, max(2, (size - 1) // 3), max(4, 2 * (size - 1) // 3), size - 2)
        row = 6 + (layout // 4)
        column = columns[layout % 4]
        grid[row][column] = 6
        return grid

    if scenario == "three_one":
        row3 = 1 + (row_slot % 3)
        column1 = min(size - 3, anchor + 3)
        row1 = size - 2 - (row_slot % 2)
        if row_slot == 3:
            column1 = max(0, anchor - 2)
        grid[row3][anchor] = 3
        grid[row1][column1] = 1
        return grid

    if scenario == "three_two_cross":
        row3 = 1 + (row_slot % 3)
        row2 = row3 + (1 if row_slot % 2 == 0 else 2)
        grid[row3][anchor] = 3
        grid[row2][anchor + 2] = 2
        return grid

    if scenario == "one_two_plain":
        row1 = 1 + row_slot
        row2 = size - 2 - (row_slot % 2)
        grid[row1][anchor] = 1
        grid[row2][anchor + 2] = 2
        return grid

    if scenario == "one_two_three_plain":
        row1 = 1 + row_slot
        row2 = size - 2 - (row_slot % 2)
        row3 = 1 + ((row_slot + 1) % 3)
        grid[row1][anchor] = 1
        grid[row2][anchor + 2] = 2
        grid[row3][anchor + 4] = 3
        return grid

    if scenario == "six_two_cross_one":
        row6 = min(size - 1, 6 + (row_slot % 3))
        row2 = row6 - (1 if row_slot % 2 == 0 else 2)
        column1 = _safe_one_column(size, {anchor, anchor + 2})
        row1 = 1 + row_slot
        grid[row6][anchor] = 6
        grid[row2][anchor + 2] = 2
        grid[row1][column1] = 1
        return grid

    # all_four_cross_six: keep the right-side 3 strictly to the right of the 2,
    # so it is deliberately ignored by the 2-center rule.
    anchor = max(4, anchor)
    anchor = min(anchor, size - 5)
    row6 = min(size - 1, 6 + (row_slot % 3))
    row2 = row6 - (1 if row_slot % 2 == 0 else 2)
    row3 = 1 + ((row_slot + column_slot + 1) % 3)
    column1 = (row_slot + column_slot) % 2
    row1 = 1 + row_slot
    grid[row6][anchor] = 6
    grid[row2][anchor + 2] = 2
    grid[row3][anchor + 4] = 3
    grid[row1][column1] = 1
    return grid


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(9, 9, 0)
    if name == "no_cue":
        return grid
    if name == "duplicate_cue":
        grid[6][2] = 6
        grid[7][5] = 6
        return grid
    if name == "orphan_two":
        grid[5][6] = 2
        return grid
    if name == "clipped_six":
        grid[5][4] = 6
        return grid
    if name == "unexpected_color":
        grid[4][4] = 8
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")


def _copy_grid(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _valid_cell(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9


def _put(grid: list[list[int]], row: int, column: int, value: int) -> None:
    if 0 <= row < len(grid) and 0 <= column < len(grid[0]):
        grid[row][column] = value


def _points(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (row, column, grid[row][column])
        for row in range(len(grid))
        for column in range(len(grid[0]))
        if grid[row][column] != 0
    ]


def _apply_rule_core(
    grid: list[list[int]],
    *,
    vertical_mode: str = "canonical",
    one_mode: str = "up",
    yellow_mode: str = "conditional",
    center_mode: str = "left_only",
    horizontal_radius: int = 2,
) -> list[list[int]]:
    """Input-pure Python mirror with knobs used by named rival rules."""
    height, width = len(grid), len(grid[0])
    points = _points(grid)
    output = _copy_grid(grid)

    segments: list[tuple[int, int, int, int]] = []  # column, top, bottom, endpoint color
    for row, column, value in points:
        if vertical_mode == "canonical":
            if value == 6:
                segments.append((column, row - 6, row, 6))
            elif value == 3:
                segments.append((column, row, row + 3, 3))
        elif vertical_mode == "swapped":
            if value == 6:
                segments.append((column, row, row + 3, 6))
            elif value == 3:
                segments.append((column, row - 6, row, 3))
        else:
            raise ValueError(f"unknown vertical_mode: {vertical_mode}")

    for column, top, bottom, endpoint_color in segments:
        for row in range(top, bottom + 1):
            _put(
                output,
                row,
                column,
                endpoint_color if row in (top, bottom) else 5,
            )

    for row, column, value in points:
        if value != 1:
            continue
        tip_row = row - 1 if one_mode == "up" else row + 1
        _put(output, tip_row, column + 2, 1)
        _put(output, row, column, 1)
        _put(output, row, column + 1, 5)
        _put(output, row, column + 2, 5)

    def segment_at(column: int):
        return next((segment for segment in segments if segment[0] == column), None)

    for row, column, value in points:
        if value != 2:
            continue
        if center_mode == "left_only":
            candidate_columns = [
                other_column
                for _, other_column, other_value in points
                if other_value != 2 and other_column < column
            ]
        elif center_mode == "rightmost_any":
            candidate_columns = [
                other_column
                for _, other_column, other_value in points
                if other_value != 2
            ]
        else:
            raise ValueError(f"unknown center_mode: {center_mode}")
        center = max(candidate_columns) if candidate_columns else column - 1
        for current_column in range(center - horizontal_radius, center + horizontal_radius + 1):
            _put(
                output,
                row,
                current_column,
                2 if current_column in (center - horizontal_radius, center + horizontal_radius) else 5,
            )
        segment = segment_at(center)
        crossing = bool(segment and segment[1] < row < segment[2])
        draw_yellow = yellow_mode == "always" or (
            yellow_mode == "conditional" and crossing
        )
        if yellow_mode not in {"always", "conditional", "never"}:
            raise ValueError(f"unknown yellow_mode: {yellow_mode}")
        if draw_yellow:
            for offset in range(max(height, width)):
                _put(output, row + offset, center - offset, 4)
    return output


def rule_mirror(grid):
    """Public input-pure mirror of the canonical Racket rule."""
    return _apply_rule_core(_copy_grid(grid))


def _classify_scenario(
    cues: dict[int, tuple[int, int]],
    *,
    two_center_color: int | None,
    crossing_color: int | None,
) -> str | None:
    colors = frozenset(cues)
    if colors == _SCENARIO_COLOR_SETS["single_six"]:
        return "single_six"
    if colors == _SCENARIO_COLOR_SETS["three_one"]:
        return "three_one"
    if colors == _SCENARIO_COLOR_SETS["three_two_cross"]:
        if two_center_color == 3 and crossing_color == 3:
            return "three_two_cross"
        return None
    if colors == _SCENARIO_COLOR_SETS["one_two_plain"]:
        if two_center_color == 1 and crossing_color is None:
            return "one_two_plain"
        return None
    if colors == _SCENARIO_COLOR_SETS["one_two_three_plain"]:
        if (
            two_center_color == 1
            and crossing_color is None
            and cues[3][1] > cues[2][1]
        ):
            return "one_two_three_plain"
        return None
    if colors == _SCENARIO_COLOR_SETS["six_two_cross_one"]:
        if two_center_color == 6 and crossing_color == 6:
            return "six_two_cross_one"
        return None
    if colors == _SCENARIO_COLOR_SETS["all_four_cross_six"]:
        if (
            two_center_color == 6
            and crossing_color == 6
            and cues[3][1] > cues[2][1]
        ):
            return "all_four_cross_six"
        return None
    return None


def _analyse(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list"], "facts": {}}
    if not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["grid rows must be non-empty lists"], "facts": {}}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": {}}
    height = len(grid)
    if height != width or not 9 <= height <= 11:
        errors.append(f"expected a square grid of size 9..11, got {height}x{width}")
    bad_cells = [
        value
        for row in grid
        for value in row
        if not _valid_cell(value) or value not in (0, 1, 2, 3, 6)
    ]
    if bad_cells:
        errors.append(
            "unexpected cell values outside {0,1,2,3,6}: "
            f"{sorted({repr(value) for value in bad_cells})}"
        )

    cue_positions: dict[int, list[tuple[int, int]]] = {1: [], 2: [], 3: [], 6: []}
    if not bad_cells:
        for row in range(height):
            for column in range(width):
                value = grid[row][column]
                if value in cue_positions:
                    cue_positions[value].append((row, column))
    duplicates = {
        color: positions for color, positions in cue_positions.items() if len(positions) > 1
    }
    if duplicates:
        errors.append(
            "each cue color may appear at most once; duplicates="
            + repr({color: positions for color, positions in duplicates.items()})
        )
    cues = {
        color: positions[0]
        for color, positions in cue_positions.items()
        if len(positions) == 1
    }
    if not cues:
        errors.append("expected at least one cue color from {1,2,3,6}")

    if 6 in cues and cues[6][0] < 6:
        errors.append(f"color 6 at {cues[6]} cannot extend six cells upward")
    if 3 in cues and cues[3][0] + 3 >= height:
        errors.append(f"color 3 at {cues[3]} cannot extend three cells downward")
    if 1 in cues:
        row1, column1 = cues[1]
        if row1 < 1 or column1 + 2 >= width:
            errors.append(f"color 1 at {cues[1]} cannot fit its upward-right arm")

    two_center_color: int | None = None
    crossing_color: int | None = None
    center_column: int | None = None
    if 2 in cues:
        row2, column2 = cues[2]
        left = [
            (column, color)
            for color, (_, column) in cues.items()
            if color != 2 and column < column2
        ]
        if not left:
            errors.append("color 2 needs a non-2 cue strictly to its left")
        else:
            center_column, two_center_color = max(left)
            if column2 != center_column + 2:
                errors.append(
                    "color 2 must be exactly two columns right of its selected center; "
                    f"center={center_column}, color-2 column={column2}"
                )
            if center_column - 2 < 0 or center_column + 2 >= width:
                errors.append(
                    f"five-cell color-2 segment centered at column {center_column} clips"
                )
            if two_center_color in (3, 6):
                rowv, _ = cues[two_center_color]
                top, bottom = ((rowv, rowv + 3) if two_center_color == 3 else (rowv - 6, rowv))
                if top < row2 < bottom:
                    crossing_color = two_center_color

    scenario = _classify_scenario(
        cues,
        two_center_color=two_center_color,
        crossing_color=crossing_color,
    )
    if cues and scenario is None:
        errors.append(
            "cue configuration is outside the seven canonical scene types: "
            f"colors={sorted(cues)}, center_color={two_center_color}, "
            f"crossing_color={crossing_color}"
        )

    if not errors:
        output = rule_mirror(grid)
        overwritten = [
            (color, position, output[position[0]][position[1]])
            for color, position in cues.items()
            if output[position[0]][position[1]] != color
        ]
        if overwritten:
            errors.append(f"expansions overwrite input cues: {overwritten}")
        if output == grid:
            errors.append("scene produces an identity transformation")

    return {
        "errors": errors,
        "facts": {
            "grid_size": height,
            "cues": cues,
            "scenario": scenario,
            "two_center_color": two_center_color,
            "center_column": center_column,
            "crossing_color": crossing_color,
        },
    }


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact axis from the returned input grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}
    size = len(grid)
    observed: dict[str, Any] = {"grid_size": size}
    for scenario in SCENARIOS:
        for template in LAYOUT_TEMPLATES:
            try:
                candidate = _build_scene(size, scenario, template)
            except ValueError:
                continue
            if candidate == grid:
                observed["scenario"] = scenario
                observed["layout_template"] = template
                return observed
    analysis = _analyse(grid)
    scenario = analysis.get("facts", {}).get("scenario")
    if scenario is not None:
        observed["scenario"] = scenario
    return observed


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, clipped, ambiguous, and shortcut-hiding scenes."""
    del difficulty
    analysis = _analyse(grid)
    errors = list(analysis["errors"])
    requested = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    if isinstance(requested, dict):
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in AXES and observed.get(axis) != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Exact task-linked input grammar shared by canonical and generated scenes."""
    return self_check(grid)


def _scenario_witness(name: str):
    def witness(grid) -> bool:
        return _analyse(grid)["facts"].get("scenario") == name

    return witness


SEMANTIC_WITNESSES = {
    "single_six_vertical": _scenario_witness("single_six"),
    "three_and_one_independent": _scenario_witness("three_one"),
    "three_crossing_two": _scenario_witness("three_two_cross"),
    "right_side_three_ignored": _scenario_witness("one_two_three_plain"),
    "one_centers_plain_two": _scenario_witness("one_two_plain"),
    "six_crossing_two_with_one": _scenario_witness("six_two_cross_one"),
    "all_four_composed": _scenario_witness("all_four_cross_six"),
}


def _no_yellow(grid):
    return _apply_rule_core(_copy_grid(grid), yellow_mode="never")


def _always_yellow(grid):
    return _apply_rule_core(_copy_grid(grid), yellow_mode="always")


def _swapped_vertical_lengths(grid):
    return _apply_rule_core(_copy_grid(grid), vertical_mode="swapped")


def _one_bends_down(grid):
    return _apply_rule_core(_copy_grid(grid), one_mode="down")


def _rightmost_non_two_center(grid):
    return _apply_rule_core(_copy_grid(grid), center_mode="rightmost_any")


def _three_cell_two_segment(grid):
    return _apply_rule_core(_copy_grid(grid), horizontal_radius=1)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "omit_yellow_crossing_trail": _no_yellow,
    "always_draw_yellow_trail": _always_yellow,
    "swap_3_and_6_vertical_lengths": _swapped_vertical_lengths,
    "bend_color_1_downward": _one_bends_down,
    "center_2_on_rightmost_non2_anywhere": _rightmost_non_two_center,
    "draw_three_cell_2_segment": _three_cell_two_segment,
}

WITNESS_RIVALS = {
    "single_six_vertical": ["swap_3_and_6_vertical_lengths"],
    "three_and_one_independent": [
        "swap_3_and_6_vertical_lengths",
        "bend_color_1_downward",
    ],
    "three_crossing_two": [
        "omit_yellow_crossing_trail",
        "draw_three_cell_2_segment",
    ],
    "right_side_three_ignored": [
        "center_2_on_rightmost_non2_anywhere",
        "draw_three_cell_2_segment",
    ],
    "one_centers_plain_two": [
        "always_draw_yellow_trail",
        "bend_color_1_downward",
    ],
    "six_crossing_two_with_one": [
        "omit_yellow_crossing_trail",
        "bend_color_1_downward",
    ],
    "all_four_composed": [
        "omit_yellow_crossing_trail",
        "center_2_on_rightmost_non2_anywhere",
    ],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "independent_symbols_without_yellow": _no_yellow,
    "two_uses_rightmost_non2_even_to_its_right": _rightmost_non_two_center,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that do not refute the plausible rival rules above."""
    reasons: list[str] = []
    try:
        query_input = query["input"]
        query_output = query["output"]
    except (KeyError, TypeError):
        return ["query must contain input and output grids"]
    if rule_mirror(query_input) != query_output:
        reasons.append("query output disagrees with the canonical glyph-expansion rule")

    demo_scenarios: set[str] = set()
    demo_sizes: set[int] = set()
    demo_inputs: list[Any] = []
    for index, demo in enumerate(demos):
        try:
            demo_input = demo["input"]
            demo_output = demo["output"]
        except (KeyError, TypeError):
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyse(demo_input)
        if analysis["errors"]:
            reasons.append(f"demo {index} is not a lawful scene: {analysis['errors']}")
            continue
        if rule_mirror(demo_input) != demo_output:
            reasons.append(f"demo {index} output disagrees with the canonical rule")
        demo_scenarios.add(analysis["facts"]["scenario"])
        demo_sizes.add(len(demo_input))
        demo_inputs.append(demo_input)

    missing = sorted(set(SCENARIOS) - demo_scenarios)
    if missing:
        reasons.append(f"demonstrations omit canonical scene types: {missing}")
    if demo_sizes != {9, 10, 11}:
        reasons.append(f"demonstrations must expose all canonical sizes 9/10/11, got {sorted(demo_sizes)}")
    query_analysis = _analyse(query_input)
    if query_analysis["errors"]:
        reasons.append(f"query is not a lawful scene: {query_analysis['errors']}")
    elif query_analysis["facts"]["scenario"] not in demo_scenarios:
        reasons.append("query scene type was not demonstrated")
    if any(query_input == demo_input for demo_input in demo_inputs):
        reasons.append("query input duplicates a demonstration instead of changing placement")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
            competing_query = competitor(query_input)
        except Exception as exc:
            return [f"competitor audit failed for {name!r}: {type(exc).__name__}: {exc}"]
        if survives and competing_query != query_output:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query"
            )
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unsupported override(s): {sorted(unknown)}")

    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(
                f"unknown texture {texture!r}; valid diagnostics={DEGENERATE_TEXTURES}"
            )
        extra = sorted(
            name
            for name, value in overrides.items()
            if name != "texture" and value is not None
        )
        if extra:
            raise ValueError(f"degenerate texture {texture!r} cannot combine with {extra}")
        return _draw_from_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    t = _schedule_index(seed, sample_index, difficulty)
    scheduled_scenario = SCENARIOS[t % len(SCENARIOS)]
    scheduled_layout = LAYOUT_TEMPLATES[(t // len(SCENARIOS)) % len(LAYOUT_TEMPLATES)]

    if overrides.get("scenario") is not None:
        scenario = ctx.draw_choice("scenario", SCENARIOS)
    else:
        scenario = ctx.draw_choice("scenario", (scheduled_scenario,))

    if overrides.get("layout_template") is not None:
        layout_template = ctx.draw_choice("layout_template", LAYOUT_TEMPLATES)
    else:
        layout_template = ctx.draw_choice("layout_template", (scheduled_layout,))

    if overrides.get("grid_size") is not None:
        grid_size = ctx.draw_int("grid_size", 9, 11)
    else:
        canonical_size = _CANONICAL_SIZE[scenario]
        grid_size = ctx.draw_int("grid_size", canonical_size, canonical_size)

    return _build_scene(grid_size, scenario, layout_template)
