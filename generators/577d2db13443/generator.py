"""Generator for ``577d2db13443``: recolor horizontal-run endpoints.

The canonical task uses a 6x12 black grid with seven foreground colors.  Every
maximal same-color horizontal run is preserved except that its left and right
endpoint cells become color 1.  Singleton runs therefore become one color-1
cell; length-two runs become two color-1 cells; longer runs keep their interior.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "577d2db13443"
TASK_ID = "577d2db13443"
VERSION = "2.0.0"  # exact axes, canonical palette/profile, shortcut witnesses
RULE_HASH = "a811558a15fb"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a 6x12 black grid, find every maximal same-color horizontal nonzero "
    "run independently. Recolor its left and right endpoints to 1, including "
    "singleton and length-two runs, while preserving every longer interior cell."
)

INVARIANTS = [
    "the input is 6x12 with black background 0 and exactly seven foreground colors",
    "foreground colors are selected from 2..9; input color 1 is reserved for output caps",
    "there are 7..9 maximal same-color horizontal runs",
    "every scene contains at least one singleton, one length-two run, and one run of length at least three",
    "same-color runs never touch vertically, so every foreground component is one horizontal run",
]

AXES = {
    "run_count": {
        "type": "int",
        "default": "scheduled 7,8,9,8",
        "valid": "7..9",
    },
    "singleton_count": {
        "type": "int",
        "default": "scheduled 2,1,2,1",
        "valid": "1..2",
    },
    "pair_count": {
        "type": "int",
        "default": "scheduled 1,3,1,2",
        "valid": "1..3",
    },
    "max_run_length": {
        "type": "int",
        "default": "scheduled 3,4,5,6",
        "valid": "3..6",
    },
    "separator_style": {
        "type": "str",
        "default": "scheduled zero_gaps,color_boundary,color_boundary,zero_gaps",
        "valid": "zero_gaps|color_boundary",
    },
    "border_style": {
        "type": "str",
        "default": "scheduled interior,has_border,has_border,interior",
        "valid": "interior|has_border",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_AXIS_RANGES = {
    "run_count": (7, 9),
    "singleton_count": (1, 2),
    "pair_count": (1, 3),
    "max_run_length": (3, 6),
}
_AXIS_OPTIONS = {
    "separator_style": ("zero_gaps", "color_boundary"),
    "border_style": ("interior", "has_border"),
}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_DIFFICULTY_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}
_SCHEDULE = (
    {
        "run_count": 7,
        "singleton_count": 2,
        "pair_count": 1,
        "max_run_length": 3,
        "separator_style": "zero_gaps",
        "border_style": "interior",
    },
    {
        "run_count": 8,
        "singleton_count": 1,
        "pair_count": 3,
        "max_run_length": 4,
        "separator_style": "color_boundary",
        "border_style": "has_border",
    },
    {
        "run_count": 9,
        "singleton_count": 2,
        "pair_count": 1,
        "max_run_length": 5,
        "separator_style": "color_boundary",
        "border_style": "has_border",
    },
    {
        "run_count": 8,
        "singleton_count": 1,
        "pair_count": 2,
        "max_run_length": 6,
        "separator_style": "zero_gaps",
        "border_style": "interior",
    },
)
_FOREGROUND_POOL = tuple(range(2, 10))
_NEIGHBORS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the four-slot curriculum schedule to the semantic gate."""
    del seed
    return (sample_index + _DIFFICULTY_OFFSET[difficulty]) % len(_SCHEDULE)


SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _AXIS_RANGES:
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer")
            lo, hi = _AXIS_RANGES[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside declared range {lo}..{hi}")
        elif value not in _AXIS_OPTIONS[name]:
            raise ValueError(
                f"{name}={value!r} outside declared options {_AXIS_OPTIONS[name]}"
            )


def _draw_scheduled_int(ctx, name: str, scheduled: int) -> int:
    lo, hi = _AXIS_RANGES[name]
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _draw_scheduled_choice(ctx, name: str, scheduled: str) -> str:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, _AXIS_OPTIONS[name])
    return ctx.draw_choice(name, (scheduled,))


def _group_width(group: list[int], lengths: list[int], *, joined_pair: bool) -> int:
    if not group:
        return 0
    gaps = len(group) - 1
    if joined_pair and len(group) >= 2:
        gaps -= 1
    return sum(lengths[index] for index in group) + gaps


def _pack_runs(
    lengths: list[int],
    separator_style: str,
    border_style: str,
    rng,
) -> tuple[list[list[int]], int | None]:
    """Pack run IDs into six rows without count drift.

    A color-boundary scene reserves the longest run and one singleton as an
    adjacent differently colored pair.  All other neighboring runs have a
    black gap.  A tiny deterministic backtracking search guarantees every
    legal override tuple fits instead of retrying until counts silently clamp.
    """
    usable_width = 10 if border_style == "interior" else 12
    groups: list[list[int]] = [[] for _ in range(6)]
    special_group: int | None = None
    remaining = list(range(len(lengths)))

    if separator_style == "color_boundary":
        max_id = max(remaining, key=lambda index: (lengths[index], -index))
        singleton_id = next(index for index in remaining if lengths[index] == 1)
        groups[0] = [max_id, singleton_id]
        special_group = 0
        remaining.remove(max_id)
        remaining.remove(singleton_id)

    tie_noise = {index: rng.random() for index in remaining}
    remaining.sort(key=lambda index: (-lengths[index], tie_noise[index]))

    def fits(group_index: int, run_id: int) -> bool:
        trial = groups[group_index] + [run_id]
        return _group_width(
            trial,
            lengths,
            joined_pair=(group_index == special_group),
        ) <= usable_width

    def search(position: int) -> bool:
        if position == len(remaining):
            return True
        run_id = remaining[position]
        order = list(range(6))
        rng.shuffle(order)
        order.sort(key=lambda index: _group_width(
            groups[index],
            lengths,
            joined_pair=(index == special_group),
        ))
        seen_shapes: set[tuple[int, tuple[int, ...]]] = set()
        for group_index in order:
            shape = (
                _group_width(
                    groups[group_index],
                    lengths,
                    joined_pair=(group_index == special_group),
                ),
                tuple(lengths[index] for index in groups[group_index]),
            )
            if shape in seen_shapes:
                continue
            seen_shapes.add(shape)
            if not fits(group_index, run_id):
                continue
            groups[group_index].append(run_id)
            if search(position + 1):
                return True
            groups[group_index].pop()
        return False

    if not search(0):
        raise AssertionError(
            f"could not pack lengths={lengths} style={separator_style}/{border_style}"
        )
    return groups, special_group


def _place_intervals(
    groups: list[list[int]],
    special_group: int | None,
    lengths: list[int],
    border_style: str,
    rng,
) -> dict[int, tuple[int, int, int]]:
    row_order = list(range(6))
    rng.shuffle(row_order)
    intervals: dict[int, tuple[int, int, int]] = {}

    nonempty_groups = [index for index, group in enumerate(groups) if group]
    anchor_group = special_group if special_group is not None else nonempty_groups[0]
    align_left = rng.choice((True, False))

    for group_index, group in enumerate(groups):
        if not group:
            continue
        width = _group_width(
            group,
            lengths,
            joined_pair=(group_index == special_group),
        )
        if border_style == "interior":
            start = rng.randint(1, 11 - width)
        elif group_index == anchor_group:
            start = 0 if align_left else 12 - width
        else:
            start = rng.randint(0, 12 - width)

        row = row_order[group_index]
        cursor = start
        for position, run_id in enumerate(group):
            length = lengths[run_id]
            intervals[run_id] = (row, cursor, cursor + length - 1)
            cursor += length
            if position + 1 < len(group):
                joined = group_index == special_group and position == 0
                cursor += 0 if joined else 1
    return intervals


def _run_adjacency(
    intervals: dict[int, tuple[int, int, int]],
) -> dict[int, set[int]]:
    adjacency = {run_id: set() for run_id in intervals}
    ids = sorted(intervals)
    for offset, left_id in enumerate(ids):
        row_a, start_a, end_a = intervals[left_id]
        for right_id in ids[offset + 1 :]:
            row_b, start_b, end_b = intervals[right_id]
            horizontal_touch = (
                row_a == row_b
                and (end_a + 1 == start_b or end_b + 1 == start_a)
            )
            vertical_touch = (
                abs(row_a - row_b) == 1
                and max(start_a, start_b) <= min(end_a, end_b)
            )
            if horizontal_touch or vertical_touch:
                adjacency[left_id].add(right_id)
                adjacency[right_id].add(left_id)
    return adjacency


def _assign_colors(
    intervals: dict[int, tuple[int, int, int]],
    palette: tuple[int, ...],
    rng,
) -> dict[int, int]:
    adjacency = _run_adjacency(intervals)
    ids = list(intervals)
    rng.shuffle(ids)
    ids.sort(key=lambda run_id: -len(adjacency[run_id]))

    # Seven distinct anchor runs guarantee exact canonical palette support.
    anchors = ids[: len(palette)]
    colors = list(palette)
    rng.shuffle(colors)
    assigned = {run_id: color for run_id, color in zip(anchors, colors)}

    for run_id in ids[len(palette) :]:
        forbidden = {assigned[neighbor] for neighbor in adjacency[run_id] if neighbor in assigned}
        choices = [color for color in palette if color not in forbidden]
        if not choices:
            raise AssertionError("seven-color graph coloring unexpectedly exhausted")
        assigned[run_id] = rng.choice(choices)
    return assigned


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
    scheduled = _SCHEDULE[schedule_profile(seed, sample_index, difficulty)]
    run_count = _draw_scheduled_int(ctx, "run_count", scheduled["run_count"])
    singleton_count = _draw_scheduled_int(
        ctx, "singleton_count", scheduled["singleton_count"]
    )
    pair_count = _draw_scheduled_int(ctx, "pair_count", scheduled["pair_count"])
    max_run_length = _draw_scheduled_int(
        ctx, "max_run_length", scheduled["max_run_length"]
    )
    separator_style = _draw_scheduled_choice(
        ctx, "separator_style", scheduled["separator_style"]
    )
    border_style = _draw_scheduled_choice(
        ctx, "border_style", scheduled["border_style"]
    )

    layout_rng = ctx.draw_rng("layout")
    long_count = run_count - singleton_count - pair_count
    if long_count < 1:
        raise AssertionError("declared axis ranges must leave at least one long run")
    lengths = [1] * singleton_count + [2] * pair_count + [max_run_length]
    lengths.extend(layout_rng.randint(3, max_run_length) for _ in range(long_count - 1))
    layout_rng.shuffle(lengths)

    groups, special_group = _pack_runs(
        lengths, separator_style, border_style, layout_rng
    )
    intervals = _place_intervals(
        groups, special_group, lengths, border_style, layout_rng
    )

    palette_rng = ctx.draw_rng("palette")
    omitted = palette_rng.choice(_FOREGROUND_POOL)
    palette = tuple(color for color in _FOREGROUND_POOL if color != omitted)
    colors = _assign_colors(intervals, palette, palette_rng)

    grid = full_grid(6, 12, 0)
    for run_id, (row, start, end) in intervals.items():
        for column in range(start, end + 1):
            grid[row][column] = colors[run_id]

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("internal generation error: " + "; ".join(errors))
    return grid


def _row_runs(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    runs: list[tuple[int, int, int, int]] = []
    for row_index, row in enumerate(grid):
        column = 0
        while column < len(row):
            color = row[column]
            if color == 0:
                column += 1
                continue
            end = column
            while end + 1 < len(row) and row[end + 1] == color:
                end += 1
            runs.append((row_index, column, end, color))
            column = end + 1
    return runs


def _same_color_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(len(grid)):
        for column in range(len(grid[0])):
            if grid[row][column] == 0 or (row, column) in seen:
                continue
            color = grid[row][column]
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _NEIGHBORS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < len(grid)
                        and 0 <= nc < len(grid[0])
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {}, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return {}, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]
    if len(grid) != 6 or width != 12:
        errors.append(f"grid must be canonical 6x12, got {len(grid)}x{width}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer colors 0..9")
        return {}, errors

    palette = {value for row in grid for value in row}
    foreground = palette - {0}
    if 0 not in palette:
        errors.append("background color 0 must be present")
    if 1 in foreground:
        errors.append("input color 1 is reserved for output endpoints")
    if len(foreground) != 7 or not foreground <= set(_FOREGROUND_POOL):
        errors.append(
            "input must use exactly seven foreground colors selected from 2..9"
        )

    runs = _row_runs(grid)
    lengths = [end - start + 1 for _row, start, end, _color in runs]
    run_count = len(runs)
    singleton_count = lengths.count(1)
    pair_count = lengths.count(2)
    max_run_length = max(lengths, default=0)
    if not 7 <= run_count <= 9:
        errors.append(f"expected 7..9 horizontal runs, found {run_count}")
    if not 1 <= singleton_count <= 2:
        errors.append(f"expected 1..2 singleton runs, found {singleton_count}")
    if not 1 <= pair_count <= 3:
        errors.append(f"expected 1..3 length-two runs, found {pair_count}")
    if not 3 <= max_run_length <= 6:
        errors.append(f"expected maximum run length 3..6, found {max_run_length}")

    for cells in _same_color_components(grid):
        rows = {row for row, _column in cells}
        columns = sorted(column for _row, column in cells)
        if len(rows) != 1 or columns != list(range(columns[0], columns[-1] + 1)):
            errors.append("every same-color component must be one horizontal run")
            break

    color_boundary = any(
        grid[row][column] != 0
        and grid[row][column + 1] != 0
        and grid[row][column] != grid[row][column + 1]
        for row in range(len(grid))
        for column in range(width - 1)
    )
    touches_border = any(start == 0 or end == width - 1 for _row, start, end, _color in runs)
    facts = {
        "run_count": run_count,
        "singleton_count": singleton_count,
        "pair_count": pair_count,
        "max_run_length": max_run_length,
        "separator_style": "color_boundary" if color_boundary else "zero_gaps",
        "border_style": "has_border" if touches_border else "interior",
        "foreground_colors": len(foreground),
        "repeated_color_runs": any(count > 1 for count in Counter(color for *_rest, color in runs).values()),
        "runs": tuple(runs),
        "lengths": tuple(lengths),
    }
    return facts, errors


def observe_overrides(grid) -> dict[str, int | str]:
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if facts and not errors:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in AXES and value is not None and observed.get(name) != value:
                errors.append(
                    f"override {name} requested {value!r}, observed {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws remain on the fixed canonical size/palette manifold."""
    return _analyze(grid)[1]


def _oracle(grid):
    output = [row[:] for row in grid]
    for row, start, end, _color in _row_runs(grid):
        output[row][start] = 1
        output[row][end] = 1
    return output


def _rival_all_nonzero(grid):
    return [[1 if value != 0 else 0 for value in row] for row in grid]


def _rival_left_only(grid):
    output = [row[:] for row in grid]
    for row, start, _end, _color in _row_runs(grid):
        output[row][start] = 1
    return output


def _rival_right_only(grid):
    output = [row[:] for row in grid]
    for row, _start, end, _color in _row_runs(grid):
        output[row][end] = 1
    return output


def _rival_long_runs_only(grid):
    output = [row[:] for row in grid]
    for row, start, end, _color in _row_runs(grid):
        if end - start + 1 >= 3:
            output[row][start] = 1
            output[row][end] = 1
    return output


def _rival_row_outermost(grid):
    output = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        columns = [column for column, value in enumerate(row) if value != 0]
        if columns:
            output[row_index][columns[0]] = 1
            output[row_index][columns[-1]] = 1
    return output


def _rival_longest_per_row(grid):
    output = [row[:] for row in grid]
    by_row: dict[int, list[tuple[int, int, int, int]]] = {}
    for run in _row_runs(grid):
        by_row.setdefault(run[0], []).append(run)
    for row, runs in by_row.items():
        _rr, start, end, _color = max(
            runs, key=lambda run: (run[2] - run[1] + 1, -run[1])
        )
        output[row][start] = 1
        output[row][end] = 1
    return output


def _rival_zero_delimited_segments(grid):
    output = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        column = 0
        while column < len(row):
            if row[column] == 0:
                column += 1
                continue
            end = column
            while end + 1 < len(row) and row[end + 1] != 0:
                end += 1
            output[row_index][column] = 1
            output[row_index][end] = 1
            column = end + 1
    return output


def _rival_smallest_color_only(grid):
    output = [row[:] for row in grid]
    target = min(value for row in grid for value in row if value != 0)
    for row, start, end, color in _row_runs(grid):
        if color == target:
            output[row][start] = 1
            output[row][end] = 1
    return output


def _rival_first_run_per_color(grid):
    output = [row[:] for row in grid]
    seen: set[int] = set()
    for row, start, end, color in _row_runs(grid):
        if color in seen:
            continue
        seen.add(color)
        output[row][start] = 1
        output[row][end] = 1
    return output


LESSON_COMPETITORS: dict[str, Callable] = {
    "recolor_all_nonzero": _rival_all_nonzero,
    "left_endpoint_only": _rival_left_only,
    "right_endpoint_only": _rival_right_only,
    "ignore_short_runs": _rival_long_runs_only,
    "outermost_cells_per_row": _rival_row_outermost,
    "longest_run_per_row": _rival_longest_per_row,
    "zero_delimited_segment_endpoints": _rival_zero_delimited_segments,
    "smallest_color_only": _rival_smallest_color_only,
    "first_run_per_color": _rival_first_run_per_color,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
CANONICAL_SHORTCUTS = {
    "zero_delimited_segment_endpoints": _rival_zero_delimited_segments,
}


def _valid_facts(grid) -> dict[str, Any] | None:
    facts, errors = _analyze(grid)
    return facts if not errors else None


def _witness_singleton(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["singleton_count"] >= 1)


def _witness_pair(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["pair_count"] >= 1)


def _witness_long_interior(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["max_run_length"] >= 3)


def _witness_multiple_runs_same_row(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(
        facts
        and max(Counter(row for row, _start, _end, _color in facts["runs"]).values()) >= 2
    )


def _witness_color_boundary(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["separator_style"] == "color_boundary")


def _witness_multiple_colors(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["foreground_colors"] == 7)


def _witness_repeated_color_runs(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["repeated_color_runs"])


SEMANTIC_WITNESSES = {
    "singleton_run": _witness_singleton,
    "length_two_run": _witness_pair,
    "long_run_with_preserved_interior": _witness_long_interior,
    "multiple_runs_in_one_row": _witness_multiple_runs_same_row,
    "adjacent_different_color_runs": _witness_color_boundary,
    "seven_foreground_colors": _witness_multiple_colors,
    "same_color_reused_in_separate_runs": _witness_repeated_color_runs,
}
WITNESS_RIVALS = {
    "singleton_run": ["ignore_short_runs"],
    "length_two_run": ["left_endpoint_only", "right_endpoint_only", "ignore_short_runs"],
    "long_run_with_preserved_interior": ["recolor_all_nonzero"],
    "multiple_runs_in_one_row": ["outermost_cells_per_row", "longest_run_per_row"],
    "adjacent_different_color_runs": ["zero_delimited_segment_endpoints"],
    "seven_foreground_colors": ["smallest_color_only"],
    "same_color_reused_in_separate_runs": ["first_run_per_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    parsed: list[tuple[Any, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict):
            reasons.append(f"demo {index} is not a pair dictionary")
            continue
        grid = pair.get("input")
        output = pair.get("output")
        errors = strict_canonical_like(grid)
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
        elif output != _oracle(grid):
            reasons.append(f"demo {index} output disagrees with the endpoint rule")
        else:
            parsed.append((grid, output))
    if len(parsed) < EXAMPLES_NEEDED:
        return reasons or ["too few valid demonstrations"]

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(grid) == output for grid, output in parsed):
            reasons.append(f"competitor {name!r} survives every demonstration")

    if not isinstance(query, dict):
        reasons.append("query is not a pair dictionary")
    else:
        query_grid = query.get("input")
        query_output = query.get("output")
        query_errors = strict_canonical_like(query_grid)
        if query_errors:
            reasons.append(f"query input invalid: {query_errors[0]}")
        elif query_output is not None and query_output != _oracle(query_grid):
            reasons.append("query output disagrees with the endpoint rule")
    return reasons
