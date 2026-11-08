"""Generator for ARC task 63a780e1d475: fill clear aligned endpoint spans.

Every pair of consecutive blue cells in a row or column is considered.  When
there is at least one cell between the pair and that whole interior is zero in
the original input, the complete inclusive span is recolored red.  Generated
inputs use disjoint endpoint incidences, while crossing horizontal/vertical
spans deliberately exercise the rule's original-input semantics.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "63a780e1d475"
TASK_ID = "63a780e1d475"
VERSION = "3.0.0"
RULE_HASH = "b3ad5e9b6be9"
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 20
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "An 8..14 by 9..14 zero-background grid contains 2..4 clear blue(1) "
    "endpoint pairs aligned in rows, columns, or both. For every consecutive "
    "aligned pair whose original interior is all background, recolor the "
    "entire inclusive segment, including both endpoints, red(2)."
)

INVARIANTS = [
    "input colors are exactly background 0 and blue endpoints 1",
    "there are 2..4 clear horizontal or vertical endpoint spans",
    "every blue endpoint belongs to exactly one span",
    "mixed_crossing examples contain an interior horizontal/vertical crossing",
    "the rule tests clear interiors against the original input",
]

ORIENTATION_MODES = (
    "horizontal_only",
    "vertical_only",
    "mixed_clear",
    "mixed_crossing",
)
CANONICAL_SHAPES = ((8, 9), (9, 9), (8, 10), (10, 10), (9, 10))
SCHEDULE_MODES = (
    "mixed_crossing",
    "horizontal_only",
    "mixed_crossing",
    "vertical_only",
)
SCHEDULE_COUNTS = (3, 3, 4, 2)
BAND_COUNTS = {
    "easy": (3, 2, 3, 2),
    "medium": SCHEDULE_COUNTS,
    "hard": (4, 4, 4, 3),
}

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical shape", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "scheduled canonical shape", "valid": "9..14"},
    "n_pairs": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
    "orientation_mode": {
        "type": "str",
        "default": "scheduled crossing/horizontal/vertical curriculum",
        "valid": "|".join(ORIENTATION_MODES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
HorizontalSpan = tuple[int, int, int]  # row, left, right
VerticalSpan = tuple[int, int, int]  # column, top, bottom


def _difficulty_band(difficulty: Any) -> str:
    if difficulty == "easy" or (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and float(difficulty) < 0.34
    ):
        return "easy"
    if difficulty == "hard" or (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and float(difficulty) >= 0.67
    ):
        return "hard"
    return "medium"


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic curriculum slot used by the lesson sampler."""
    del seed
    mode = SCHEDULE_MODES[sample_index % len(SCHEDULE_MODES)]
    counts = BAND_COUNTS[_difficulty_band(difficulty)]
    count = counts[sample_index % len(counts)]
    h, w = CANONICAL_SHAPES[sample_index % len(CANONICAL_SHAPES)]
    return f"{mode}:pairs={count}:shape={h}x{w}"


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty in (None, "easy", "medium", "hard"):
        return
    if (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and 0.0 <= float(difficulty) <= 1.0
    ):
        return
    raise ValueError(
        "difficulty must be easy, medium, hard, None, or a number in [0,1]"
    )


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    for name, lo, hi in (("grid_h", 8, 14), ("grid_w", 9, 14), ("n_pairs", 2, 4)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} is outside [{lo}, {hi}]")

    if "orientation_mode" in overrides and overrides["orientation_mode"] is not None:
        value = overrides["orientation_mode"]
        if not isinstance(value, str) or value not in ORIENTATION_MODES:
            raise ValueError(
                "orientation_mode must be one of " + ", ".join(ORIENTATION_MODES)
            )


def _draw_int_with_default(ctx, label: str, lo: int, hi: int, default: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_with_default(
    ctx, label: str, options: Sequence[str], default: str
) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _pair_values(values: Iterable[int], count: int, rng) -> list[tuple[int, int]]:
    """Choose disjoint coordinate pairs, each separated by at least one cell."""
    pool = sorted(set(values))
    if count == 0:
        return []
    if len(pool) < 2 * count:
        raise ValueError(f"need {2 * count} distinct coordinates, found {len(pool)}")

    # Pair the lower half to the upper half.  For count>=2 the separation is
    # automatically >=2; for a singleton we retry/exhaustively avoid adjacency.
    for _ in range(256):
        selected = sorted(rng.sample(pool, 2 * count))
        pairs = list(zip(selected[:count], selected[count:]))
        if all(b - a > 1 for a, b in pairs):
            rng.shuffle(pairs)
            return pairs

    candidates = []
    for selected in combinations(pool, 2 * count):
        pairs = list(zip(selected[:count], selected[count:]))
        if all(b - a > 1 for a, b in pairs):
            candidates.append(pairs)
    if not candidates:
        raise ValueError("no clear endpoint-pair placement exists")
    pairs = [tuple(pair) for pair in rng.choice(candidates)]
    rng.shuffle(pairs)
    return pairs


def _mixed_counts(n_pairs: int, rng) -> tuple[int, int]:
    if n_pairs == 2:
        return 1, 1
    if n_pairs == 4:
        return 2, 2
    return (2, 1) if rng.randrange(2) == 0 else (1, 2)


def _draw_horizontal_only(h: int, w: int, n_pairs: int, rng) -> Grid:
    rows = rng.sample(range(h), n_pairs)
    pairs = _pair_values(range(w), n_pairs, rng)
    grid = full_grid(h, w, 0)
    for row, (left, right) in zip(rows, pairs):
        grid[row][left] = 1
        grid[row][right] = 1
    return grid


def _draw_vertical_only(h: int, w: int, n_pairs: int, rng) -> Grid:
    columns = rng.sample(range(w), n_pairs)
    pairs = _pair_values(range(h), n_pairs, rng)
    grid = full_grid(h, w, 0)
    for column, (top, bottom) in zip(columns, pairs):
        grid[top][column] = 1
        grid[bottom][column] = 1
    return grid


def _draw_mixed_clear(h: int, w: int, n_pairs: int, rng) -> Grid:
    horizontal_count, vertical_count = _mixed_counts(n_pairs, rng)

    # Place horizontal rows strictly above every vertical span.  This gives an
    # observable mixed-but-noncrossing branch without relying on rejection.
    split = horizontal_count
    horizontal_rows = rng.sample(range(split), horizontal_count)
    vertical_row_pairs = _pair_values(range(split + 1, h), vertical_count, rng)

    vertical_columns = rng.sample(range(w), vertical_count)
    horizontal_column_pairs = _pair_values(
        (c for c in range(w) if c not in set(vertical_columns)),
        horizontal_count,
        rng,
    )

    grid = full_grid(h, w, 0)
    for row, (left, right) in zip(horizontal_rows, horizontal_column_pairs):
        grid[row][left] = 1
        grid[row][right] = 1
    for column, (top, bottom) in zip(vertical_columns, vertical_row_pairs):
        grid[top][column] = 1
        grid[bottom][column] = 1
    return grid


def _draw_mixed_crossing(h: int, w: int, n_pairs: int, rng) -> Grid:
    horizontal_count, vertical_count = _mixed_counts(n_pairs, rng)

    # Retry a compact constructive layout.  Endpoint rows/columns are kept
    # disjoint across orientations, so every blue cell participates exactly
    # once; the reserved central intersection remains original background.
    for _ in range(1024):
        horizontal_row = rng.randrange(1, h - 1)
        vertical_column = rng.randrange(1, w - 1)
        cross_vertical = (
            rng.randrange(0, horizontal_row),
            rng.randrange(horizontal_row + 1, h),
        )
        cross_horizontal = (
            rng.randrange(0, vertical_column),
            rng.randrange(vertical_column + 1, w),
        )

        try:
            extra_vertical_rows = _pair_values(
                (
                    r
                    for r in range(h)
                    if r not in {horizontal_row, *cross_vertical}
                ),
                vertical_count - 1,
                rng,
            )
            all_vertical_endpoint_rows = {
                *cross_vertical,
                *(r for pair in extra_vertical_rows for r in pair),
            }
            extra_horizontal_rows = rng.sample(
                [
                    r
                    for r in range(h)
                    if r != horizontal_row and r not in all_vertical_endpoint_rows
                ],
                horizontal_count - 1,
            )

            extra_horizontal_columns = _pair_values(
                (
                    c
                    for c in range(w)
                    if c not in {vertical_column, *cross_horizontal}
                ),
                horizontal_count - 1,
                rng,
            )
            all_horizontal_endpoint_columns = {
                *cross_horizontal,
                *(c for pair in extra_horizontal_columns for c in pair),
            }
            extra_vertical_columns = rng.sample(
                [
                    c
                    for c in range(w)
                    if c != vertical_column
                    and c not in all_horizontal_endpoint_columns
                ],
                vertical_count - 1,
            )
        except (ValueError, IndexError):
            continue

        horizontal_rows = [horizontal_row, *extra_horizontal_rows]
        horizontal_pairs = [cross_horizontal, *extra_horizontal_columns]
        vertical_columns = [vertical_column, *extra_vertical_columns]
        vertical_pairs = [cross_vertical, *extra_vertical_rows]

        grid = full_grid(h, w, 0)
        for row, (left, right) in zip(horizontal_rows, horizontal_pairs):
            grid[row][left] = 1
            grid[row][right] = 1
        for column, (top, bottom) in zip(vertical_columns, vertical_pairs):
            grid[top][column] = 1
            grid[bottom][column] = 1
        return grid

    raise ValueError(
        f"could not construct {n_pairs} mixed crossing pairs on {h}x{w}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_difficulty(difficulty)
    _validate_overrides(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w = CANONICAL_SHAPES[sample_index % len(CANONICAL_SHAPES)]
    default_mode = SCHEDULE_MODES[sample_index % len(SCHEDULE_MODES)]
    counts = BAND_COUNTS[_difficulty_band(difficulty)]
    default_count = counts[sample_index % len(counts)]

    h = _draw_int_with_default(ctx, "grid_h", 8, 14, default_h)
    w = _draw_int_with_default(ctx, "grid_w", 9, 14, default_w)
    n_pairs = _draw_int_with_default(ctx, "n_pairs", 2, 4, default_count)
    mode = _draw_choice_with_default(
        ctx, "orientation_mode", ORIENTATION_MODES, default_mode
    )
    rng = ctx.draw_rng("endpoint_placement")

    drawers: dict[str, Callable[[int, int, int, Any], Grid]] = {
        "horizontal_only": _draw_horizontal_only,
        "vertical_only": _draw_vertical_only,
        "mixed_clear": _draw_mixed_clear,
        "mixed_crossing": _draw_mixed_crossing,
    }
    grid = drawers[mode](h, w, n_pairs, rng)
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {k: v for k, v in overrides.items() if v is not None}},
    )
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid


def _spans(grid: Grid) -> tuple[list[HorizontalSpan], list[VerticalSpan]]:
    h, w = len(grid), len(grid[0])
    horizontal: list[HorizontalSpan] = []
    vertical: list[VerticalSpan] = []
    for row in range(h):
        columns = [column for column in range(w) if grid[row][column] == 1]
        for left, right in zip(columns, columns[1:]):
            if right - left > 1 and all(
                grid[row][column] == 0 for column in range(left + 1, right)
            ):
                horizontal.append((row, left, right))
    for column in range(w):
        rows = [row for row in range(h) if grid[row][column] == 1]
        for top, bottom in zip(rows, rows[1:]):
            if bottom - top > 1 and all(
                grid[row][column] == 0 for row in range(top + 1, bottom)
            ):
                vertical.append((column, top, bottom))
    return horizontal, vertical


def _crossing_count(grid: Grid) -> int:
    horizontal, vertical = _spans(grid)
    return sum(
        left < column < right and top < row < bottom
        for row, left, right in horizontal
        for column, top, bottom in vertical
    )


def _orientation_mode(grid: Grid) -> str | None:
    horizontal, vertical = _spans(grid)
    if horizontal and vertical:
        return "mixed_crossing" if _crossing_count(grid) else "mixed_clear"
    if horizontal:
        return "horizontal_only"
    if vertical:
        return "vertical_only"
    return None


def observe_overrides(grid) -> dict[str, int | str | None]:
    if (
        not isinstance(grid, list)
        or not grid
        or not all(isinstance(row, list) and row for row in grid)
        or len({len(row) for row in grid}) != 1
    ):
        return {}
    horizontal, vertical = _spans(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(horizontal) + len(vertical),
        "orientation_mode": _orientation_mode(grid),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact generated endpoint grammar and realized controls."""
    del difficulty
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty list of rows"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or next(iter(widths)) == 0:
        return ["grid must be rectangular and non-empty"]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not 8 <= h <= 14:
        errors.append(f"grid_h={h} is outside 8..14")
    if not 9 <= w <= 14:
        errors.append(f"grid_w={w} is outside 9..14")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1)
        for row in grid
        for value in row
    ):
        errors.append("input cells must be integer colors 0 or 1")
        return errors

    horizontal, vertical = _spans(grid)
    spans = [
        {(row, column) for column in (left, right)}
        for row, left, right in horizontal
    ] + [
        {(row, column) for row in (top, bottom)}
        for column, top, bottom in vertical
    ]
    count = len(spans)
    if not 2 <= count <= 4:
        errors.append(f"expected 2..4 clear endpoint spans; found {count}")

    blue = {
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 1
    }
    membership = {
        cell: sum(cell in endpoints for endpoints in spans)
        for cell in blue
    }
    bad = sorted(cell for cell, uses in membership.items() if uses != 1)
    if bad:
        errors.append(
            "every blue endpoint must belong to exactly one span; bad cells "
            + repr(bad[:6])
        )
    represented = set().union(*spans) if spans else set()
    if represented != blue:
        missing = sorted(blue - represented)
        errors.append(f"unpaired blue endpoint cells: {missing[:6]!r}")

    mode = _orientation_mode(grid)
    if mode not in ORIENTATION_MODES:
        errors.append("orientation pattern is not an advertised mode")

    overrides = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    observed = observe_overrides(grid)
    if isinstance(overrides, dict):
        for axis, requested in overrides.items():
            if axis in AXES and observed.get(axis) != requested:
                errors.append(
                    f"override {axis} requested {requested!r}, observed "
                    f"{observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Ordinary samples and canonical inputs share this defended manifold."""
    return self_check(grid)


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror; production labels still come from canonical Racket."""
    output = deepcopy(grid)
    horizontal, vertical = _spans(grid)
    for row, left, right in horizontal:
        for column in range(left, right + 1):
            output[row][column] = 2
    for column, top, bottom in vertical:
        for row in range(top, bottom + 1):
            output[row][column] = 2
    return output


def _horizontal_only_rival(grid: Grid) -> Grid:
    output = deepcopy(grid)
    horizontal, _ = _spans(grid)
    for row, left, right in horizontal:
        for column in range(left, right + 1):
            output[row][column] = 2
    return output


def _vertical_only_rival(grid: Grid) -> Grid:
    output = deepcopy(grid)
    _, vertical = _spans(grid)
    for column, top, bottom in vertical:
        for row in range(top, bottom + 1):
            output[row][column] = 2
    return output


def _interior_only_rival(grid: Grid) -> Grid:
    output = deepcopy(grid)
    horizontal, vertical = _spans(grid)
    for row, left, right in horizontal:
        for column in range(left + 1, right):
            output[row][column] = 2
    for column, top, bottom in vertical:
        for row in range(top + 1, bottom):
            output[row][column] = 2
    return output


def _first_per_orientation(grid: Grid) -> Grid:
    output = deepcopy(grid)
    horizontal, vertical = _spans(grid)
    if horizontal:
        row, left, right = horizontal[0]
        for column in range(left, right + 1):
            output[row][column] = 2
    if vertical:
        column, top, bottom = vertical[0]
        for row in range(top, bottom + 1):
            output[row][column] = 2
    return output


def _sequential_block_crossings(grid: Grid) -> Grid:
    """Rival that incorrectly checks vertical clearance after row painting."""
    output = deepcopy(grid)
    horizontal, vertical = _spans(grid)
    for row, left, right in horizontal:
        for column in range(left, right + 1):
            output[row][column] = 2
    for column, top, bottom in vertical:
        if all(output[row][column] == 0 for row in range(top + 1, bottom)):
            for row in range(top, bottom + 1):
                output[row][column] = 2
    return output


def _identity_rival(grid: Grid) -> Grid:
    return deepcopy(grid)


SEMANTIC_RIVALS = {
    "sequential_block_crossings": _sequential_block_crossings,
    "horizontal_only": _horizontal_only_rival,
    "vertical_only": _vertical_only_rival,
    "interior_only": _interior_only_rival,
    "first_per_orientation": _first_per_orientation,
    "identity": _identity_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "sequential_block_crossings": _sequential_block_crossings,
}


def _has_horizontal(grid: Grid) -> bool:
    return not self_check(grid) and bool(_spans(grid)[0])


def _has_vertical(grid: Grid) -> bool:
    return not self_check(grid) and bool(_spans(grid)[1])


def _has_crossing(grid: Grid) -> bool:
    return not self_check(grid) and _crossing_count(grid) > 0


def _has_multiple_same_orientation(grid: Grid) -> bool:
    if self_check(grid):
        return False
    horizontal, vertical = _spans(grid)
    return len(horizontal) > 1 or len(vertical) > 1


def _has_span(grid: Grid) -> bool:
    return not self_check(grid) and any(_spans(grid))


SEMANTIC_WITNESSES = {
    "crossing_spans": _has_crossing,
    "horizontal_span": _has_horizontal,
    "vertical_span": _has_vertical,
    "multiple_same_orientation": _has_multiple_same_orientation,
    "endpoint_recoloring": _has_span,
}
WITNESS_RIVALS = {
    "crossing_spans": ["sequential_block_crossings"],
    "horizontal_span": ["vertical_only"],
    "vertical_span": ["horizontal_only"],
    "multiple_same_orientation": ["first_per_orientation"],
    "endpoint_recoloring": ["interior_only", "identity"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson where a named rival fits every demo but changes query."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
        demos = demos if isinstance(demos, (list, tuple)) else []

    for index, pair in enumerate(demos):
        grid = pair.get("input") if isinstance(pair, dict) else None
        if self_check(grid):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if pair.get("output") != rule_mirror(grid):
            reasons.append(f"demo {index} output disagrees with the span rule")

    query_grid = query.get("input") if isinstance(query, dict) else None
    if self_check(query_grid):
        reasons.append("query input is outside the teaching grammar")
    elif query.get("output") != rule_mirror(query_grid):
        reasons.append("query output disagrees with the span rule")

    for name, competitor in LESSON_COMPETITORS.items():
        if demos and all(
            competitor(pair["input"]) == pair.get("output")
            for pair in demos
            if isinstance(pair, dict) and "input" in pair
        ):
            if isinstance(query, dict) and competitor(query_grid) != query.get("output"):
                reasons.append(
                    f"named competitor {name!r} fits every demo but changes the query"
                )
    return reasons
