"""Generator for ``468bf8d62f3a``.

The input contains vertical same-colour runs on a zero background.  The
canonical rule keeps exactly the first (topmost) cell of every run.  A run is
maximal only with respect to vertical adjacency and colour: a different colour
immediately below starts a new run even when there is no zero gap.

The ordinary schedule deliberately cycles through three layouts:

* separate columns, including a 1/3 canonical-profile anchor;
* two runs in one column separated by zero;
* two different-colour runs touching in one column.

Those layouts respectively preserve the official manifold and refute the
"one answer per column", "only cells above zero", and "first cell per colour"
shortcuts.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "468bf8d62f3a"
TASK_ID = "468bf8d62f3a"
VERSION = "2.0.0"  # honest axes, canonical anchor, and shortcut witnesses
RULE_HASH = "7fb4ccc318f8"

SUMMARY = (
    "A zero-background grid contains 3-6 vertical same-colour runs.  Keep only "
    "the top cell of every maximal run; a touching colour change begins a new run."
)

_H_LO, _H_HI = 6, 11
_W_LO, _W_HI = 7, 11
_RUN_LO, _RUN_HI = 3, 6
_COLOR_LO, _COLOR_HI = 2, 3
_LAYOUTS = ("separate_columns", "stacked_gaps", "touching_colors")
_CANONICAL_PROFILES = ((7, 8), (8, 7), (6, 9), (7, 9))
_CANONICAL_LENGTHS = {(2, 3, 3), (2, 2, 4)}

INVARIANTS = [
    "background is 0",
    "there are 3-6 maximal vertical same-colour runs",
    "every run is contiguous and has length at least 2",
    "exactly 2-3 nonzero colours are used",
    "different-colour runs may touch vertically and still remain distinct runs",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 6..11; every third ordinary draw uses a canonical profile",
        "valid": "6..11",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 7..11; every third ordinary draw uses a canonical profile",
        "valid": "7..11",
    },
    "run_count": {
        "type": "int",
        "default": "3 on canonical anchors; otherwise difficulty-skewed 3..6",
        "valid": "3..6",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "3 on canonical anchors; otherwise difficulty-skewed 2..3",
        "valid": "2..3",
    },
    "layout_mode": {
        "type": "enum",
        "default": "sample_index cycle: separate_columns, stacked_gaps, touching_colors",
        "valid": "separate_columns|stacked_gaps|touching_colors",
    },
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _vertical_runs(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return maximal nonzero same-colour runs, scanning by column."""
    if not _is_arc_grid(grid):
        return []
    h, w = len(grid), len(grid[0])
    runs: list[dict[str, Any]] = []
    for c in range(w):
        r = 0
        while r < h:
            color = grid[r][c]
            if color == 0:
                r += 1
                continue
            start = r
            while r + 1 < h and grid[r + 1][c] == color:
                r += 1
            end = r
            runs.append(
                {
                    "color": color,
                    "col": c,
                    "start": start,
                    "end": end,
                    "length": end - start + 1,
                }
            )
            r += 1
    return runs


def _layout_mode(grid: list[list[int]], runs: list[dict[str, Any]] | None = None) -> str:
    runs = _vertical_runs(grid) if runs is None else runs
    if not runs:
        return "separate_columns"
    h, w = len(grid), len(grid[0])
    for c in range(w):
        for r in range(1, h):
            if grid[r - 1][c] != 0 and grid[r][c] != 0 and grid[r - 1][c] != grid[r][c]:
                return "touching_colors"
    by_col: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        by_col[run["col"]].append(run)
    if any(len(column_runs) >= 2 for column_runs in by_col.values()):
        return "stacked_gaps"
    return "separate_columns"


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact semantic axis from the returned grid."""
    runs = _vertical_runs(grid)
    return {
        "run_count": len(runs),
        "n_distinct_colors": len({run["color"] for run in runs}),
        "layout_mode": _layout_mode(grid, runs),
    }


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _effective_overrides(
    seed: int,
    sample_index: int,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> tuple[dict[str, Any], bool, tuple[int, int] | None]:
    """Build an exact, observable default schedule without weakening overrides."""
    del difficulty
    effective = dict(overrides)
    no_explicit_axes = not any(value is not None for value in overrides.values())

    if effective.get("layout_mode") is None:
        effective["layout_mode"] = _LAYOUTS[sample_index % len(_LAYOUTS)]

    canonical_anchor = no_explicit_axes and effective["layout_mode"] == "separate_columns"
    profile: tuple[int, int] | None = None
    if canonical_anchor:
        profile_rng = stable_rng(
            seed,
            f"{TASK_ID}|{sample_index}|canonical_profile",
            VERSION,
        )
        profile = profile_rng.choice(_CANONICAL_PROFILES)
        effective.update(
            {
                "grid_h": profile[0],
                "grid_w": profile[1],
                "run_count": 3,
                "n_distinct_colors": 3,
            }
        )
    elif no_explicit_axes:
        # Every non-anchor lesson contains repeated colours, which makes
        # "keep the first cell of each colour" observably wrong.
        effective["run_count"] = 4 + (sample_index % 2)
        effective["n_distinct_colors"] = 2 + (sample_index % 2)

    return effective, canonical_anchor, profile


def _choose_columns(rng, w: int, count: int, *, include_border: bool = False) -> list[int]:
    if count > w:
        raise ValueError(f"cannot place {count} separate columns in width {w}")
    columns = list(range(w))
    chosen: list[int] = []
    if include_border:
        chosen.append(rng.choice((0, w - 1)))
        columns.remove(chosen[0])
    chosen.extend(rng.sample(columns, count - len(chosen)))
    return chosen


def _general_length(rng, h: int) -> int:
    return rng.randint(2, min(5, h))


def _place_separate(
    grid: list[list[int]],
    colors: tuple[int, ...],
    run_count: int,
    rng,
    *,
    canonical_anchor: bool,
    canonical_profile: tuple[int, int] | None,
) -> None:
    h, w = len(grid), len(grid[0])
    columns = _choose_columns(rng, w, run_count, include_border=True)

    if canonical_anchor:
        assert canonical_profile is not None
        signature = (2, 3, 3) if canonical_profile in ((7, 8), (6, 9)) else (2, 2, 4)
        lengths = list(signature)
        rng.shuffle(lengths)
    else:
        lengths = [_general_length(rng, h) for _ in range(run_count)]

    for index, (column, length) in enumerate(zip(columns, lengths)):
        if canonical_anchor and index == 0:
            start = 0
        else:
            start = rng.randint(0, h - length)
        color = colors[index % len(colors)]
        for r in range(start, start + length):
            grid[r][column] = color


def _pair_lengths(rng, h: int, *, gap: int) -> tuple[int, int, int]:
    available = h - gap
    if available < 4:
        raise ValueError(f"height {h} cannot hold two length-2 runs with gap {gap}")
    first = rng.randint(2, min(4, available - 2))
    second = rng.randint(2, min(4, available - first))
    total = first + gap + second
    start = rng.randint(0, h - total)
    return first, second, start


def _place_shared_column(
    grid: list[list[int]],
    colors: tuple[int, ...],
    run_count: int,
    rng,
    *,
    touching: bool,
) -> None:
    h, w = len(grid), len(grid[0])
    shared_col = rng.choice((0, w - 1, rng.randrange(w)))
    gap = 0 if touching else 1
    first_len, second_len, start = _pair_lengths(rng, h, gap=gap)

    first_color = colors[0]
    second_color = colors[1]
    for r in range(start, start + first_len):
        grid[r][shared_col] = first_color
    second_start = start + first_len + gap
    for r in range(second_start, second_start + second_len):
        grid[r][shared_col] = second_color

    remaining = run_count - 2
    columns = [c for c in range(w) if c != shared_col]
    chosen = rng.sample(columns, remaining)
    for offset, column in enumerate(chosen, start=2):
        length = _general_length(rng, h)
        row = rng.randint(0, h - length)
        color = colors[offset % len(colors)]
        for r in range(row, row + length):
            grid[r][column] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    effective, canonical_anchor, canonical_profile = _effective_overrides(
        seed, sample_index, difficulty, overrides
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    h = ctx.draw_int_diff("grid_h", _H_LO, _H_HI)
    w = ctx.draw_int_diff("grid_w", _W_LO, _W_HI)
    run_count = ctx.draw_int_diff("run_count", _RUN_LO, _RUN_HI)
    n_colors = ctx.draw_int_diff("n_distinct_colors", _COLOR_LO, _COLOR_HI)
    layout_mode = ctx.draw_choice("layout_mode", _LAYOUTS)

    if n_colors > run_count:
        raise ValueError("n_distinct_colors cannot exceed run_count")
    if layout_mode == "separate_columns" and run_count > w:
        raise ValueError("run_count cannot exceed grid_w for separate_columns")
    if layout_mode in {"stacked_gaps", "touching_colors"} and run_count - 2 > w - 1:
        raise ValueError("remaining runs do not fit outside the shared column")

    colors = ctx.draw_distinct_colors("colors", n=n_colors, exclude={0})
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)

    if layout_mode == "separate_columns":
        _place_separate(
            grid,
            colors,
            run_count,
            rng,
            canonical_anchor=canonical_anchor,
            canonical_profile=canonical_profile,
        )
    elif layout_mode == "stacked_gaps":
        _place_shared_column(grid, colors, run_count, rng, touching=False)
    elif layout_mode == "touching_colors":
        _place_shared_column(grid, colors, run_count, rng, touching=True)
    else:  # draw_choice already protects this; keep failure explicit for edits.
        raise ValueError(f"unsupported layout_mode {layout_mode!r}")

    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete generated/canonical input grammar."""
    del difficulty, meta
    if not _is_arc_grid(grid):
        return ["grid must be a nonempty rectangular ARC grid"]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (_H_LO <= h <= _H_HI and _W_LO <= w <= _W_HI):
        errors.append(
            f"dimensions {h}x{w} outside {_H_LO}..{_H_HI} by {_W_LO}..{_W_HI}"
        )

    runs = _vertical_runs(grid)
    if not (_RUN_LO <= len(runs) <= _RUN_HI):
        errors.append(f"expected {_RUN_LO}-{_RUN_HI} vertical runs, found {len(runs)}")
    short = [run for run in runs if run["length"] < 2]
    if short:
        errors.append(f"every vertical run must have length >=2; found {len(short)} singleton run(s)")

    colors = {run["color"] for run in runs}
    if not (_COLOR_LO <= len(colors) <= _COLOR_HI):
        errors.append(
            f"expected {_COLOR_LO}-{_COLOR_HI} distinct nonzero colours, found {len(colors)}"
        )

    # A nonzero cell is lawful only when it belongs to one of the extracted
    # vertical runs.  The equality catches horizontal bars and isolated noise.
    covered = sum(run["length"] for run in runs)
    nonzero = sum(value != 0 for row in grid for value in row)
    if covered != nonzero:
        errors.append("some nonzero cells are not represented by vertical runs")

    mode = _layout_mode(grid, runs)
    if mode not in _LAYOUTS:
        errors.append(f"unrecognized layout mode {mode!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Exact empirical manifold, quotienting only nuisance colour renaming."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    h, w = len(grid), len(grid[0])
    runs = _vertical_runs(grid)
    if (h, w) not in _CANONICAL_PROFILES:
        reasons.append(f"dimensions {h}x{w} are not a canonical joint profile")
    if len(runs) != 3:
        reasons.append("canonical inputs contain exactly three runs")
    if len({run["color"] for run in runs}) != 3:
        reasons.append("canonical inputs use three distinct run colours")
    if _layout_mode(grid, runs) != "separate_columns":
        reasons.append("canonical inputs place one run in each occupied column")
    lengths = tuple(sorted(run["length"] for run in runs))
    if lengths not in _CANONICAL_LENGTHS:
        reasons.append(f"run-length multiset {lengths} is not canonical")
    if len({run["col"] for run in runs}) != len(runs):
        reasons.append("canonical inputs do not stack runs in one column")
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python test mirror; the canonical Racket program remains authoritative."""
    if not _is_arc_grid(grid):
        raise ValueError("rule_mirror expects a rectangular ARC grid")
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value != 0 and (r == 0 or grid[r - 1][c] != value):
                out[r][c] = value
    return out


def _column_top_rule(grid: list[list[int]]) -> list[list[int]]:
    out = full_grid(len(grid), len(grid[0]), 0)
    for c in range(len(grid[0])):
        for r in range(len(grid)):
            if grid[r][c] != 0:
                out[r][c] = grid[r][c]
                break
    return out


def _zero_exposed_rule(grid: list[list[int]]) -> list[list[int]]:
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0 and (r == 0 or grid[r - 1][c] == 0):
                out[r][c] = value
    return out


def _first_per_color_rule(grid: list[list[int]]) -> list[list[int]]:
    out = full_grid(len(grid), len(grid[0]), 0)
    seen: set[int] = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0 and value not in seen:
                out[r][c] = value
                seen.add(value)
    return out


_RIVAL_RULES: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "one_top_cell_per_column": _column_top_rule,
    "keep_only_cells_exposed_to_zero_above": _zero_exposed_rule,
    "keep_only_first_cell_of_each_colour": _first_per_color_rule,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut predicts another query."""
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"pair {index} output does not match the canonical rule")
    if reasons:
        return reasons

    for name, rival in _RIVAL_RULES.items():
        rival_fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        rival_query = rival(query["input"])
        if rival_fits_demos and rival_query != query["output"]:
            reasons.append(f"demos do not refute rival rule: {name}")
    return reasons


def _has_zero_gap_stack(grid) -> bool:
    runs = _vertical_runs(grid)
    by_col: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        by_col[run["col"]].append(run)
    return any(len(items) >= 2 for items in by_col.values()) and _layout_mode(grid, runs) == "stacked_gaps"


def _has_touching_colour_change(grid) -> bool:
    return _layout_mode(grid) == "touching_colors"


def _has_repeated_colour_runs(grid) -> bool:
    counts = Counter(run["color"] for run in _vertical_runs(grid))
    return any(count >= 2 for count in counts.values())


def _has_top_row_run(grid) -> bool:
    return any(run["start"] == 0 for run in _vertical_runs(grid))


def _has_long_run(grid) -> bool:
    return any(run["length"] >= 4 for run in _vertical_runs(grid))


SEMANTIC_WITNESSES = {
    "same_column_runs_with_zero_gap": _has_zero_gap_stack,
    "touching_different_colour_runs": _has_touching_colour_change,
    "repeated_colour_in_multiple_runs": _has_repeated_colour_runs,
    "run_starts_on_top_border": _has_top_row_run,
    "run_length_at_least_four": _has_long_run,
}
