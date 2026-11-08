"""Truthful sampler for the Bar Caps task.

The unchanged Racket authority paints color 8 in a background cell exactly when
that cell is immediately beyond two consecutive horizontal color-6 cells.  Each
ordinary generated input teaches the three relevant boundaries directly:
singletons stay uncapped, bars longer than the canonical 2/3-cell examples are
still capped, and bars touching an edge receive their one available cap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1bc09b475319"
TASK_ID = GENERATOR_ID
RULE_HASH = "187795461399"
VERSION = "3.1.0"
SUMMARY = (
    "Place three or four mixed-length horizontal color-6 bars plus two isolated "
    "color-6 singleton distractors. The topmost bar has the requested "
    "bar_length; the remaining bars ensure both a short (2/3) and long (4/5) "
    "example are present. The authority preserves every 6 and paints color 8 "
    "only immediately beyond at least two consecutive horizontal 6s. Ordinary "
    "samples include an edge-touching bar, while an exact edge_bar=false "
    "override produces only interior bars. Singletons receive no cap."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid is 7..18 by 7..20 with colors 0 and 6 only",
    "there are three or four horizontal bars in distinct rows, each length 2..5",
    "generated inputs mix at least one short (2/3) and one long (4/5) bar",
    "there are exactly two interior singleton 6-cells, separate or vertically aligned",
    "at least one bar has background on both horizontal sides",
    "edge_bar exactly records whether at least one bar touches a horizontal edge",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-scale square by difficulty",
        "valid": "7..18",
        "doc": "Input/output height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-scale square by difficulty",
        "valid": "7..20",
        "doc": "Input/output width.",
    },
    "n_bars": {
        "type": "int",
        "default": "difficulty-weighted 3..4",
        "valid": "3..4",
        "doc": "Number of horizontal length-at-least-two bars.",
    },
    "bar_length": {
        "type": "int",
        "default": "difficulty-weighted 2..5",
        "valid": "2..5",
        "doc": (
            "Length of the topmost bar. Other bars include a complementary "
            "short or long length so the lesson distinguishes the general rule."
        ),
    },
    "edge_bar": {
        "type": "bool",
        "default": "true (exact false override is supported)",
        "valid": "false|true",
        "doc": "Whether at least one bar touches the left or right edge.",
    },
    "singleton_layout": {
        "type": "enum",
        "default": "rng separate|vertical",
        "valid": "separate|vertical",
        "doc": "Whether the two singleton distractors are separate or vertically adjacent.",
    },
}

# Every Cartesian combination of the advertised domains is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "n_bars", "bar_length"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    value = overrides.get("edge_bar")
    if value is not None and type(value) is not bool:
        raise TypeError("edge_bar must be a boolean")
    value = overrides.get("singleton_layout")
    if value is not None and type(value) is not str:
        raise TypeError("singleton_layout must be a string")


def _has_override(ctx, label: str) -> bool:
    return label in ctx.overrides and ctx.overrides[label] is not None


def _draw_int_axis(ctx, label: str, lo: int, hi: int, defaults) -> int:
    """Honor the full override domain while keeping deliberate defaults exact."""
    if _has_override(ctx, label):
        return ctx.draw_int_strict(label, lo, hi)
    options = tuple(defaults) if isinstance(defaults, (tuple, list)) else (defaults,)
    return ctx.draw_choice(label, options)


def _default_size(difficulty, sample_index: int) -> int:
    if difficulty == "easy":
        return 7
    if difficulty == "medium":
        return 8
    if difficulty == "hard":
        return 9
    return (7, 8, 9)[sample_index % 3]


def _bar_rows(ctx, h: int, n_bars: int, singleton_rows: tuple[int, int]) -> list[int]:
    available = [row for row in range(h) if row not in singleton_rows]
    return sorted(ctx.draw_rng("bar_rows").sample(available, n_bars))


def _singleton_rows(ctx, h: int, layout: str) -> tuple[int, int]:
    rng = ctx.draw_rng("singleton_rows")
    if layout == "vertical":
        top = rng.randrange(0, h - 1)
        return top, top + 1
    pairs = [(a, b) for a in range(h) for b in range(a + 2, h)]
    return rng.choice(pairs)


def _bar_lengths(anchor: int, count: int) -> list[int]:
    """Keep the requested top bar exact while teaching short/long generality."""
    contrast = 4 if anchor in (2, 3) else 2
    return [anchor if index % 2 == 0 else contrast for index in range(count)]


def _bar_starts(ctx, w: int, lengths: list[int], edge_bar: bool) -> list[int]:
    rng = ctx.draw_rng("bar_starts")
    edge_index = rng.randrange(len(lengths)) if edge_bar else None
    starts: list[int] = []
    for index, length in enumerate(lengths):
        interior = list(range(1, w - length))
        if not interior:
            raise ValueError("grid width cannot fit an interior bar with two open ends")
        if index == edge_index:
            starts.append(rng.choice((0, w - length)))
        else:
            starts.append(rng.choice(interior))
    return starts


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

    size = _default_size(difficulty, sample_index)
    h = _draw_int_axis(ctx, "grid_h", 7, 18, size)
    w = _draw_int_axis(ctx, "grid_w", 7, 20, size)
    n_bars = _draw_int_axis(
        ctx,
        "n_bars",
        3,
        4,
        {"easy": (3,), "medium": (3, 4), "hard": (4,)}.get(difficulty, (3, 4)),
    )
    bar_length = _draw_int_axis(
        ctx,
        "bar_length",
        2,
        5,
        {"easy": (2, 3), "medium": (2, 3, 4), "hard": (3, 4, 5)}.get(
            difficulty, (2, 3, 4, 5)
        ),
    )
    edge_options = (False, True) if _has_override(ctx, "edge_bar") else (True,)
    edge_bar = ctx.draw_choice("edge_bar", edge_options)
    singleton_layout = ctx.draw_choice("singleton_layout", ("separate", "vertical"))

    singleton_rows = _singleton_rows(ctx, h, singleton_layout)
    bar_rows = _bar_rows(ctx, h, n_bars, singleton_rows)
    lengths = _bar_lengths(bar_length, n_bars)
    starts = _bar_starts(ctx, w, lengths, edge_bar)

    grid = full_grid(h, w, 0)
    for row, start, length in zip(bar_rows, starts, lengths):
        for col in range(start, start + length):
            grid[row][col] = 6

    singleton_rng = ctx.draw_rng("singleton_columns")
    if singleton_layout == "vertical":
        col = singleton_rng.randrange(1, w - 1)
        singleton_cols = (col, col)
    else:
        singleton_cols = (
            singleton_rng.randrange(1, w - 1),
            singleton_rng.randrange(1, w - 1),
        )
    for row, col in zip(singleton_rows, singleton_cols):
        grid[row][col] = 6

    return grid


def _row_runs(grid) -> list[tuple[int, int, int]]:
    runs: list[tuple[int, int, int]] = []
    for row_index, row in enumerate(grid):
        col = 0
        while col < len(row):
            if row[col] != 6:
                col += 1
                continue
            start = col
            while col < len(row) and row[col] == 6:
                col += 1
            runs.append((row_index, start, col - 1))
    return runs


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical manifold and this sampler's boundary-rich extension."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or value not in (0, 6) for row in grid for value in row):
        return ["cells must be integer colors 0 or 6"]

    height = len(grid)
    errors: list[str] = []
    if not 7 <= height <= 18:
        errors.append(f"grid_h={height} outside [7,18]")
    if not 7 <= width <= 20:
        errors.append(f"grid_w={width} outside [7,20]")

    runs = _row_runs(grid)
    per_row: dict[int, int] = {}
    for row, _start, _end in runs:
        per_row[row] = per_row.get(row, 0) + 1
    if any(count != 1 for count in per_row.values()):
        errors.append("each active row must contain exactly one contiguous color-6 run")

    singletons = [run for run in runs if run[1] == run[2]]
    bars = [run for run in runs if run[2] > run[1]]
    if len(bars) not in (3, 4):
        errors.append(f"expected 3 or 4 bars, found {len(bars)}")
    lengths = [end - start + 1 for _row, start, end in bars]
    if any(not 2 <= length <= 5 for length in lengths):
        errors.append("bar lengths must be in [2,5]")
    if len(singletons) == 2:
        if not any(length in (2, 3) for length in lengths):
            errors.append("generated bars must include a short length 2 or 3")
        if not any(length in (4, 5) for length in lengths):
            errors.append("generated bars must include a long length 4 or 5")
    if len(singletons) not in (0, 2):
        errors.append(
            f"expected zero canonical or two generated singletons, found {len(singletons)}"
        )
    if any(start in (0, width - 1) for _row, start, _end in singletons):
        errors.append("singleton distractors must be interior")
    if bars and not any(start > 0 and end < width - 1 for _row, start, end in bars):
        errors.append("at least one bar must have two open horizontal sides")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    runs = _row_runs(grid)
    bars = [run for run in runs if run[2] > run[1]]
    singletons = [run for run in runs if run[1] == run[2]]
    if len(singletons) != 2:
        raise ValueError("override observation requires the generated two-singleton profile")
    vertical = (
        singletons[0][2] == singletons[1][2]
        and abs(singletons[0][0] - singletons[1][0]) == 1
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_bars": len(bars),
        "bar_length": bars[0][2] - bars[0][1] + 1,
        "edge_bar": any(start == 0 or end == len(grid[0]) - 1 for _row, start, end in bars),
        "singleton_layout": "vertical" if vertical else "separate",
    }


def _cap_runs_matching(grid, predicate):
    out = [list(row) for row in grid]
    width = len(grid[0]) if grid else 0
    for row, start, end in _row_runs(grid):
        length = end - start + 1
        if length < 2 or not predicate(row, start, end, length, width):
            continue
        if start > 0 and grid[row][start - 1] == 0:
            out[row][start - 1] = 8
        if end + 1 < width and grid[row][end + 1] == 0:
            out[row][end + 1] = 8
    return out


def _adjacent_any_six(grid):
    """Wrong rule: paint beside one horizontal 6, not two."""
    out = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        for col, value in enumerate(row):
            if value != 0:
                continue
            if (col > 0 and row[col - 1] == 6) or (
                col + 1 < len(row) and row[col + 1] == 6
            ):
                out[row_index][col] = 8
    return out


def _canonical_lengths_only(grid):
    """Wrong rule: cap only lengths 2/3, the lengths seen canonically."""
    return _cap_runs_matching(
        grid, lambda _row, _start, _end, length, _width: length in (2, 3)
    )


def _interior_bars_only(grid):
    """Wrong rule: cap only bars with background on both sides."""
    return _cap_runs_matching(
        grid,
        lambda _row, start, end, _length, width: start > 0 and end < width - 1,
    )


def _singleton_exclusion(grid) -> bool:
    """True when an isolated 6 gives the adjacent-any-6 rival a false cap."""
    for row, start, end in _row_runs(grid):
        if start != end:
            continue
        if (start > 0 and grid[row][start - 1] == 0) or (
            start + 1 < len(grid[row]) and grid[row][start + 1] == 0
        ):
            return True
    return False


def _long_bar(grid) -> bool:
    return any(end - start + 1 in (4, 5) for _row, start, end in _row_runs(grid))


def _edge_bar(grid) -> bool:
    if not grid:
        return False
    width = len(grid[0])
    return any(
        end > start and (start == 0 or end == width - 1)
        for _row, start, end in _row_runs(grid)
    )


def _pair_refutes(pair, rival) -> bool:
    if not isinstance(pair, dict):
        return False
    grid = pair.get("input")
    output = pair.get("output")
    if not isinstance(grid, list) or not grid or not isinstance(output, list):
        return False
    if len(grid) != len(output):
        return False
    if any(not isinstance(a, list) or not isinstance(b, list) or len(a) != len(b) for a, b in zip(grid, output)):
        return False
    return rival(grid) != output


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not demos:
        return ["lesson has no demonstrations"]
    for name, rival in LESSON_COMPETITORS.items():
        if not any(_pair_refutes(pair, rival) for pair in demos):
            reasons.append(f"demonstrations do not refute semantic rival {name}")
    return reasons


SEMANTIC_RIVALS = {
    "adjacent_any_six": _adjacent_any_six,
    "canonical_lengths_only": _canonical_lengths_only,
    "interior_bars_only": _interior_bars_only,
}
CANONICAL_SHORTCUTS = {
    "adjacent_any_six": _adjacent_any_six,
    "canonical_lengths_only": _canonical_lengths_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "singleton_exclusion": _singleton_exclusion,
    "long_bar": _long_bar,
    "edge_bar": _edge_bar,
}
WITNESS_RIVALS = {
    "singleton_exclusion": ["adjacent_any_six"],
    "long_bar": ["canonical_lengths_only"],
    "edge_bar": ["interior_bars_only"],
}
