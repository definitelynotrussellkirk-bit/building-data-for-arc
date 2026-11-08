"""Constructive sampler for 7e7614405852.

Rule: scan each row for maximal non-zero monochromatic runs.  When (and only
when) a run has length exactly three, recolor its middle cell to 8.

The public axes are deliberately structural and exactly recoverable from the
returned input.  Ordinary lessons always include two counterexamples that are
absent from the canonical examples: a horizontal run of length five and a
vertical run of length three.  Those witnesses rule out the plausible
"mark every odd run" and "mark triples in either orientation" shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7e7614405852"
TASK_ID = GENERATOR_ID
RULE_HASH = "5eb06a6d574a"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "Generate separated horizontal runs of lengths 2-5 and an optional "
    "vertical length-3 distractor. Recolor only the middle of maximal "
    "horizontal runs whose length is exactly three."
)

INVARIANTS = [
    "background is color 0 and input never contains output color 8",
    "every non-background color names exactly one straight run object",
    "horizontal object lengths are 2..5 and at least one has length 3",
    "there is at most one vertical object, of length exactly 3",
    "ordinary draws include a length-5 run and a vertical triple witness",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile-weighted draw",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile-weighted draw",
        "valid": "8..16",
    },
    "n_len2": {
        "type": "int",
        "default": "canonical-profile-weighted draw",
        "valid": "0..1",
    },
    "n_len3": {
        "type": "int",
        "default": "difficulty/profile-weighted draw",
        "valid": "1..3",
    },
    "n_len4": {
        "type": "int",
        "default": "canonical-profile-weighted draw",
        "valid": "0..2",
    },
    "n_len5": {
        "type": "int",
        "default": "1 (exact override 0 also supported)",
        "valid": "0..1",
    },
    "n_vertical3": {
        "type": "int",
        "default": "1 (exact override 0 also supported)",
        "valid": "0..1",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_AXIS_BOUNDS = {
    "grid_h": (5, 12),
    "grid_w": (8, 16),
    "n_len2": (0, 1),
    "n_len3": (1, 3),
    "n_len4": (0, 2),
    "n_len5": (0, 1),
    "n_vertical3": (0, 1),
}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_SOURCE_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

Grid = list[list[int]]
Cell = tuple[int, int]

# The three preferred profiles mirror canonical shape/palette profiles while
# retaining structural witnesses.  Full public domains remain available on
# every draw and through every exact override.
_PREFERRED_PROFILES = (
    {"grid_h": 6, "grid_w": 8, "n_len2": 1, "n_len3": 1, "n_len4": 0},
    {"grid_h": 5, "grid_w": 9, "n_len2": 0, "n_len3": 1, "n_len4": 0},
    {"grid_h": 7, "grid_w": 10, "n_len2": 0, "n_len3": 2, "n_len4": 1},
)
_BAND_OFFSETS = {None: 0, "easy": 1, "medium": 2, "hard": 0}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def _draw_weighted_axis(ctx, label: str, preferred: int, weight: int = 24) -> int:
    """Draw a full-domain integer while heavily weighting one legal value."""
    lo, hi = _AXIS_BOUNDS[label]
    if label in ctx.overrides:
        return ctx.draw_int_strict(label, lo, hi)
    domain = tuple(range(lo, hi + 1))
    options = (preferred,) * weight + domain
    return int(ctx.draw_choice(label, options))


def _draw_default_one_axis(ctx, label: str) -> int:
    """Default to a required witness while preserving an exact zero override."""
    lo, hi = _AXIS_BOUNDS[label]
    if label in ctx.overrides:
        return ctx.draw_int_strict(label, lo, hi)
    return int(ctx.draw_choice(label, (1,)))


def _row_cost(lengths: Sequence[int]) -> int:
    return sum(lengths) + max(0, len(lengths) - 1)


def _pack_runs(
    run_lengths: Sequence[int], capacities: Sequence[int], rng
) -> list[list[int]] | None:
    """Pack run indices into row capacities, charging one zero between runs."""
    order = list(range(len(run_lengths)))
    rng.shuffle(order)
    order.sort(key=lambda index: run_lengths[index], reverse=True)
    rows: list[list[int]] = [[] for _ in capacities]
    used = [0 for _ in capacities]
    failed: set[tuple[int, tuple[int, ...], tuple[int, ...]]] = set()

    def search(position: int) -> bool:
        if position == len(order):
            return True
        state = (position, tuple(used), tuple(len(row) for row in rows))
        if state in failed:
            return False
        object_index = order[position]
        length = run_lengths[object_index]
        candidates = list(range(len(capacities)))
        rng.shuffle(candidates)
        # Prefer a tight fit; random shuffling above varies equal-score rows.
        candidates.sort(
            key=lambda row: capacities[row]
            - used[row]
            - length
            - (1 if rows[row] else 0)
        )
        seen_signatures: set[tuple[int, bool]] = set()
        for row in candidates:
            signature = (capacities[row] - used[row], bool(rows[row]))
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            cost = length + (1 if rows[row] else 0)
            if used[row] + cost > capacities[row]:
                continue
            rows[row].append(object_index)
            used[row] += cost
            if search(position + 1):
                return True
            used[row] -= cost
            rows[row].pop()
        failed.add(state)
        return False

    return rows if search(0) else None


def _choose_layout(
    height: int,
    width: int,
    run_lengths: Sequence[int],
    vertical_count: int,
    rng,
) -> tuple[list[list[int]], int | None, int | None]:
    """Choose a feasible row packing plus optional vertical top/edge."""
    if vertical_count:
        candidates = [
            (top, side)
            for top in range(height - 2)
            for side in (0, width - 1)
        ]
    else:
        candidates = [(None, None)]
    rng.shuffle(candidates)
    for top, side in candidates:
        capacities = [width] * height
        if top is not None:
            for row in range(top, top + 3):
                capacities[row] -= 1
        packed = _pack_runs(run_lengths, capacities, rng)
        if packed is not None:
            return packed, top, side
    raise RuntimeError(
        "declared run counts unexpectedly do not fit the selected grid shape"
    )


def _paint_row_runs(
    grid: Grid,
    row: int,
    object_indices: Sequence[int],
    run_lengths: Sequence[int],
    colors: Sequence[int],
    vertical_top: int | None,
    vertical_side: int | None,
    rng,
) -> None:
    if not object_indices:
        return
    indices = list(object_indices)
    rng.shuffle(indices)
    if vertical_top is not None and vertical_top <= row < vertical_top + 3:
        if vertical_side == 0:
            start, stop = 1, len(grid[0])
        else:
            start, stop = 0, len(grid[0]) - 1
    else:
        start, stop = 0, len(grid[0])
    capacity = stop - start
    minimal = _row_cost([run_lengths[index] for index in indices])
    slack = capacity - minimal
    if slack < 0:
        raise RuntimeError("internal row packing/layout disagreement")
    slots = [0] * (len(indices) + 1)
    for _ in range(slack):
        slots[rng.randrange(len(slots))] += 1
    col = start + slots[0]
    for position, object_index in enumerate(indices):
        length = run_lengths[object_index]
        color = colors[object_index]
        for cc in range(col, col + length):
            grid[row][cc] = color
        col += length
        if position + 1 < len(indices):
            col += 1 + slots[position + 1]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, override-exact lawful input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_index = (sample_index + _BAND_OFFSETS[difficulty]) % len(
        _PREFERRED_PROFILES
    )
    preferred = _PREFERRED_PROFILES[profile_index]
    height = _draw_weighted_axis(ctx, "grid_h", preferred["grid_h"])
    width = _draw_weighted_axis(ctx, "grid_w", preferred["grid_w"])
    n_len2 = _draw_weighted_axis(ctx, "n_len2", preferred["n_len2"], weight=12)
    n_len3 = _draw_weighted_axis(ctx, "n_len3", preferred["n_len3"], weight=12)
    n_len4 = _draw_weighted_axis(ctx, "n_len4", preferred["n_len4"], weight=12)
    n_len5 = _draw_default_one_axis(ctx, "n_len5")
    n_vertical3 = _draw_default_one_axis(ctx, "n_vertical3")

    run_lengths = (
        [2] * n_len2
        + [3] * n_len3
        + [4] * n_len4
        + [5] * n_len5
    )
    object_count = len(run_lengths) + n_vertical3
    if object_count > len(_SOURCE_COLORS):
        raise RuntimeError("declared axes require more source colors than available")

    layout_rng = ctx.draw_rng("constructive_layout")
    rows, vertical_top, vertical_side = _choose_layout(
        height, width, run_lengths, n_vertical3, layout_rng
    )
    colors = list(_SOURCE_COLORS[:object_count])
    ctx.draw_rng("object_colors").shuffle(colors)
    grid = full_grid(height, width, 0)

    for row, object_indices in enumerate(rows):
        _paint_row_runs(
            grid,
            row,
            object_indices,
            run_lengths,
            colors,
            vertical_top,
            vertical_side,
            ctx.draw_rng(f"row_layout_{row}"),
        )
    if n_vertical3:
        assert vertical_top is not None and vertical_side is not None
        vertical_color = colors[len(run_lengths)]
        for row in range(vertical_top, vertical_top + 3):
            grid[row][vertical_side] = vertical_color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructive generator produced invalid grid: {errors}")
    if observe_overrides(grid) != {
        "grid_h": height,
        "grid_w": width,
        "n_len2": n_len2,
        "n_len3": n_len3,
        "n_len4": n_len4,
        "n_len5": n_len5,
        "n_vertical3": n_vertical3,
    }:
        raise RuntimeError("constructive generator failed exact override recovery")
    return grid


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a non-empty sequence of rows"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "grid rows must be non-empty sequences"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid rows must have equal width"
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "grid cells must be integer ARC colors 0..9 (not bools)"
    return None


def _cells_by_color(grid: Sequence[Sequence[int]]) -> dict[int, list[Cell]]:
    cells: dict[int, list[Cell]] = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                cells.setdefault(color, []).append((row, col))
    return cells


def _classify_object(cells: Sequence[Cell]) -> tuple[str, int] | None:
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    if len(rows) == 1:
        ordered = sorted(col for _, col in cells)
        if ordered == list(range(ordered[0], ordered[-1] + 1)):
            return "horizontal", len(ordered)
    if len(cols) == 1:
        ordered = sorted(row for row, _ in cells)
        if ordered == list(range(ordered[0], ordered[-1] + 1)):
            return "vertical", len(ordered)
    return None


def _analyze(grid: Sequence[Sequence[int]]) -> tuple[dict[str, int], list[str]]:
    error = _grid_error(grid)
    empty = {
        "grid_h": 0,
        "grid_w": 0,
        "n_len2": 0,
        "n_len3": 0,
        "n_len4": 0,
        "n_len5": 0,
        "n_vertical3": 0,
    }
    if error:
        return empty, [error]
    height, width = len(grid), len(grid[0])
    stats = dict(empty)
    stats["grid_h"] = height
    stats["grid_w"] = width
    errors: list[str] = []
    if not 5 <= height <= 12:
        errors.append(f"grid height {height} outside 5..12")
    if not 8 <= width <= 16:
        errors.append(f"grid width {width} outside 8..16")
    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("input must contain background color 0")
    if 8 in palette:
        errors.append("input must not contain output color 8")

    for color, cells in sorted(_cells_by_color(grid).items()):
        if color == 8:
            continue
        classification = _classify_object(cells)
        if classification is None:
            errors.append(
                f"color {color} must form exactly one straight contiguous run"
            )
            continue
        orientation, length = classification
        if orientation == "horizontal":
            if length not in (2, 3, 4, 5):
                errors.append(
                    f"horizontal color-{color} run has illegal length {length}"
                )
            else:
                stats[f"n_len{length}"] += 1
        elif length != 3:
            errors.append(f"vertical color-{color} run must have length 3")
        else:
            stats["n_vertical3"] += 1

    for name, (lo, hi) in _AXIS_BOUNDS.items():
        if name in ("grid_h", "grid_w"):
            continue
        value = stats[name]
        if not lo <= value <= hi:
            errors.append(f"observed {name}={value} outside [{lo}, {hi}]")
    return stats, errors


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int]:
    """Recover every public axis exactly from the returned input grid."""
    stats, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    return stats


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete declared input grammar, including canonicals."""
    del difficulty, meta
    _, errors = _analyze(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _horizontal_runs(grid: Sequence[Sequence[int]]):
    for row, values in enumerate(grid):
        col = 0
        while col < len(values):
            color = values[col]
            if color == 0:
                col += 1
                continue
            stop = col + 1
            while stop < len(values) and values[stop] == color:
                stop += 1
            yield row, col, stop, color
            col = stop


def _vertical_runs(grid: Sequence[Sequence[int]]):
    height, width = len(grid), len(grid[0])
    for col in range(width):
        row = 0
        while row < height:
            color = grid[row][col]
            if color == 0:
                row += 1
                continue
            stop = row + 1
            while stop < height and grid[stop][col] == color:
                stop += 1
            yield col, row, stop, color
            row = stop


def _apply_rule(grid: Sequence[Sequence[int]]) -> Grid:
    output = [list(row) for row in grid]
    for row, start, stop, _ in _horizontal_runs(grid):
        if stop - start == 3:
            output[row][start + 1] = 8
    return output


def _mark_all_at_least_three(grid: Sequence[Sequence[int]]) -> Grid:
    output = [list(row) for row in grid]
    for row, start, stop, _ in _horizontal_runs(grid):
        if stop - start >= 3:
            output[row][start + (stop - start) // 2] = 8
    return output


def _mark_all_odd_runs(grid: Sequence[Sequence[int]]) -> Grid:
    output = [list(row) for row in grid]
    for row, start, stop, _ in _horizontal_runs(grid):
        length = stop - start
        if length >= 3 and length % 2 == 1:
            output[row][start + length // 2] = 8
    return output


def _mark_horizontal_and_vertical_three(grid: Sequence[Sequence[int]]) -> Grid:
    output = _apply_rule(grid)
    for col, start, stop, _ in _vertical_runs(grid):
        if stop - start == 3:
            output[start + 1][col] = 8
    return output


def _has_length_five(grid: Sequence[Sequence[int]]) -> bool:
    return any(stop - start == 5 for _, start, stop, _ in _horizontal_runs(grid))


def _has_vertical_triple(grid: Sequence[Sequence[int]]) -> bool:
    return any(stop - start == 3 for _, start, stop, _ in _vertical_runs(grid))


SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "horizontal_length_five": _has_length_five,
    "vertical_length_three_distractor": _has_vertical_triple,
}
SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "mark_all_horizontal_runs_at_least_three": _mark_all_at_least_three,
    "mark_all_odd_horizontal_runs": _mark_all_odd_runs,
    "mark_exact_triples_in_both_orientations": _mark_horizontal_and_vertical_three,
}
WITNESS_RIVALS = {
    "horizontal_length_five": [
        "mark_all_horizontal_runs_at_least_three",
        "mark_all_odd_horizontal_runs",
    ],
    "vertical_length_three_distractor": [
        "mark_exact_triples_in_both_orientations"
    ],
}
CANONICAL_SHORTCUTS = {
    "mark_all_odd_horizontal_runs": _mark_all_odd_runs,
    "mark_exact_triples_in_both_orientations": _mark_horizontal_and_vertical_three,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _validate_pair(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input is outside the declared grammar: {errors[0]}"]
    if pair["output"] != _apply_rule(pair["input"]):
        return [f"{label} output disagrees with exact-horizontal-triple rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute every declared plausible competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        reasons.extend(_validate_pair(demo, f"demo {index}"))
    reasons.extend(_validate_pair(query, "query"))
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(deepcopy(demo["input"])) == demo["output"] for demo in demos):
            reasons.append(f"named rival {name!r} survives every demonstration")
    return reasons
