"""Generator for ARC task 586104ae308e (original task 2685904e).

The top header contains N leading 8-cells.  A full row of 5s separates the
header area from one non-zero data row.  Keep exactly the data-row colours
whose frequency is N, then repeat that filtered row in the N blank rows
immediately above the separator.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "586104ae308e"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "47d0892dcd9c"

SUMMARY = (
    "Count the leading colour-8 cells in the top row (N). Find the sole "
    "non-zero data row below the full colour-5 separator. Keep data-row "
    "colours occurring exactly N times and repeat that filtered row in the "
    "N rows immediately above the separator."
)

INVARIANTS = [
    "row 0 is N leading colour-8 cells followed only by zeros, with 1 <= N <= 4",
    "there is exactly one full-width colour-5 separator row, at row 5..7",
    "all non-header rows above the separator are zero in the input",
    "there is exactly one non-zero row below the separator, one or two rows away",
    "the data row is full, contains no colour 5, and has both qualifying and non-qualifying colours",
    "a qualifying colour occurs exactly N times; every distractor colour occurs a different number of times",
]

# All exact axes are recoverable from the returned grid.  Their Cartesian
# boundary combinations are deliberately all valid, so no hidden incompatibility
# declaration is needed.
AXES = {
    "grid_h": {"type": "int", "default": "four-profile schedule", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "four-profile schedule", "valid": "10..18"},
    "n8": {"type": "int", "default": "sample_index cycle 1..4", "valid": "1..4"},
    "sep_row": {"type": "int", "default": "four-profile schedule", "valid": "5..7"},
    "data_gap": {"type": "int", "default": "four-profile schedule", "valid": "1..2"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = (0, 1, 2, 3)

# (height, width, N, separator row, data-row gap, requested target-colour count)
_PROFILES = (
    (10, 10, 1, 6, 2, 1),  # exact canonical-scale anchor
    (10, 10, 2, 6, 2, 2),
    (14, 14, 3, 7, 2, 3),
    (18, 18, 4, 6, 1, 2),
)
_DATA_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the four-step lesson schedule to the semantic gate."""
    del seed, difficulty
    return int(sample_index) % 4


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    """Record a deterministic ordinary value while preserving exact overrides."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not 10 <= height <= 18:
        errors.append(f"height must be in 10..18, found {height}")
    if not 10 <= width <= 18:
        errors.append(f"width must be in 10..18, found {width}")

    header = list(grid[0])
    n8 = 0
    while n8 < width and header[n8] == 8:
        n8 += 1
    if not 1 <= n8 <= 4:
        errors.append(f"top row must begin with 1..4 colour-8 cells, found {n8}")
    if any(value != 0 for value in header[n8:]):
        errors.append("top row must contain only a leading colour-8 run and zeros")

    separator_rows = [
        row for row in range(height) if all(grid[row][col] == 5 for col in range(width))
    ]
    if len(separator_rows) != 1:
        errors.append(f"expected exactly one full colour-5 row, found {len(separator_rows)}")
        separator = None
    else:
        separator = separator_rows[0]
        if not 5 <= separator <= 7:
            errors.append(f"separator row must be in 5..7, found {separator}")

    data_row = None
    data_gap = None
    if separator is not None:
        dirty_above = [
            row
            for row in range(1, separator)
            if any(grid[row][col] != 0 for col in range(width))
        ]
        if dirty_above:
            errors.append(f"non-zero cells above separator outside header: rows {dirty_above[:4]}")

        nonzero_below = [
            row
            for row in range(separator + 1, height)
            if any(grid[row][col] != 0 for col in range(width))
        ]
        if len(nonzero_below) != 1:
            errors.append(f"expected exactly one non-zero row below separator, found {len(nonzero_below)}")
        else:
            data_row = nonzero_below[0]
            data_gap = data_row - separator
            if not 1 <= data_gap <= 2:
                errors.append(f"data row must be 1..2 rows below separator, found gap {data_gap}")

    data: list[int] = []
    counts: Counter[int] = Counter()
    targets: set[int] = set()
    distractors: set[int] = set()
    filtered: list[int] = []
    if data_row is not None:
        data = list(grid[data_row])
        if any(value == 0 for value in data):
            errors.append("data row must be full (no zero cells)")
        if any(value == 5 for value in data):
            errors.append("colour 5 is reserved for the separator and may not appear in data")
        counts = Counter(data)
        targets = {color for color, count in counts.items() if count == n8}
        distractors = set(counts) - targets
        if not targets:
            errors.append("data row has no colour occurring exactly N times")
        if not distractors:
            errors.append("data row has no non-qualifying distractor colour")
        if len(counts) < 2:
            errors.append("data row must contain at least two distinct colours")
        filtered = [value if value in targets else 0 for value in data]

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "n8": n8,
        "separator": separator,
        "data_row": data_row,
        "data_gap": data_gap,
        "data": data,
        "counts": counts,
        "targets": targets,
        "distractors": distractors,
        "filtered": filtered,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, no-op, and rule-hiding inputs."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The lawful teaching grammar is intentionally canonical-like."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact caller-facing axis from a lawful grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n8": analysis["n8"],
        "sep_row": analysis["separator"],
        "data_gap": analysis["data_gap"],
    }


def _partitions(total: int, max_parts: int, forbidden: int) -> list[tuple[int, ...]]:
    """All non-decreasing positive partitions, excluding one forbidden count."""
    result: list[tuple[int, ...]] = []

    def visit(remaining: int, minimum: int, parts: list[int]) -> None:
        if remaining == 0:
            if parts:
                result.append(tuple(parts))
            return
        if len(parts) >= max_parts:
            return
        for value in range(minimum, remaining + 1):
            if value == forbidden:
                continue
            parts.append(value)
            visit(remaining - value, value, parts)
            parts.pop()

    visit(total, 1, [])
    return result


def _choose_distractor_counts(total: int, n8: int, profile: int, max_parts: int) -> tuple[int, ...]:
    candidates = _partitions(total, max_parts, n8)
    if not candidates:
        raise ValueError(f"cannot partition {total} distractor cells without count {n8}")

    def preference(parts: tuple[int, ...]) -> tuple[int, int, int, tuple[int, ...]]:
        if profile == 0:
            preferred = len(parts) == 1 and max(parts) > n8
        elif profile in (1, 2):
            preferred = len(parts) >= 2 and max(parts) > n8
        else:
            preferred = len(parts) >= 2 and max(parts) < n8
        # Prefer the requested semantic shape, then fewer colours and balanced counts.
        return (0 if preferred else 1, len(parts), max(parts) - min(parts), parts)

    return min(candidates, key=preference)


def _select_colors(rng, needed: int, profile: int, target_count: int) -> list[int]:
    pool = list(_DATA_COLORS)
    rng.shuffle(pool)
    if profile in (1, 2):
        pool.remove(8)
        insert_at = target_count if profile == 1 else 0
        pool.insert(insert_at, 8)
    else:
        pool.remove(8)
    return pool[:needed]


def _paint_rows(grid: Any, stripe_height: int, values: list[int]) -> list[list[int]]:
    output = [list(row) for row in grid]
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    separator = analysis["separator"]
    for row in range(separator - stripe_height, separator):
        if 0 <= row < len(output):
            output[row] = list(values)
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    return _paint_rows(grid, analysis["n8"], analysis["filtered"])


def _rival_copy_all(grid):
    analysis = _analysis(grid)
    return _paint_rows(grid, analysis["n8"], analysis["data"])


def _rival_modal_only(grid):
    analysis = _analysis(grid)
    modal = max(analysis["counts"].values())
    kept = [value if analysis["counts"][value] == modal else 0 for value in analysis["data"]]
    return _paint_rows(grid, analysis["n8"], kept)


def _rival_fixed_frequency(grid, fixed: int):
    analysis = _analysis(grid)
    kept = [
        value if analysis["counts"][value] == fixed else 0
        for value in analysis["data"]
    ]
    return _paint_rows(grid, fixed, kept)


def _rival_first_qualifying_only(grid):
    analysis = _analysis(grid)
    first = next(value for value in analysis["data"] if value in analysis["targets"])
    kept = [value if value == first else 0 for value in analysis["data"]]
    return _paint_rows(grid, analysis["n8"], kept)


def _rival_ignore_data_color_8(grid):
    analysis = _analysis(grid)
    kept = [value if value in analysis["targets"] and value != 8 else 0 for value in analysis["data"]]
    return _paint_rows(grid, analysis["n8"], kept)


def _rival_header_mask(grid):
    analysis = _analysis(grid)
    return _paint_rows(grid, analysis["n8"], list(grid[0]))


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "copy_all_data": _rival_copy_all,
    "keep_modal_only": _rival_modal_only,
    "fixed_frequency_1": lambda grid: _rival_fixed_frequency(grid, 1),
    "fixed_frequency_2": lambda grid: _rival_fixed_frequency(grid, 2),
    "first_qualifying_only": _rival_first_qualifying_only,
    "ignore_data_color_8": _rival_ignore_data_color_8,
    "repeat_header_mask": _rival_header_mask,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"ignore_data_color_8": _rival_ignore_data_color_8}


def _valid_analysis(grid):
    analysis = _analysis(grid)
    return analysis if not analysis["errors"] else None


def _witness_n8(value: int):
    return lambda grid: bool((analysis := _valid_analysis(grid)) and analysis["n8"] == value)


def _single_target(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and len(analysis["targets"]) == 1)


def _multiple_targets(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and len(analysis["targets"]) >= 2)


def _target_not_modal(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and max(analysis["counts"][color] for color in analysis["distractors"])
        > analysis["n8"]
    )


def _marker_8_is_target(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and 8 in analysis["targets"])


def _filtered_differs_header(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["filtered"] != list(grid[0]))


SEMANTIC_WITNESSES = {
    "n8_equals_1": _witness_n8(1),
    "n8_equals_2": _witness_n8(2),
    "n8_equals_3": _witness_n8(3),
    "n8_equals_4": _witness_n8(4),
    "single_qualifying_color": _single_target,
    "multiple_qualifying_colors": _multiple_targets,
    "qualifying_color_is_not_modal": _target_not_modal,
    "header_marker_color_8_is_qualifying_data": _marker_8_is_target,
    "filtered_row_differs_from_header_mask": _filtered_differs_header,
}

WITNESS_RIVALS = {
    "n8_equals_1": ["fixed_frequency_2"],
    "n8_equals_2": ["fixed_frequency_1"],
    "n8_equals_3": ["fixed_frequency_2"],
    "n8_equals_4": ["fixed_frequency_2"],
    "single_qualifying_color": ["copy_all_data"],
    "multiple_qualifying_colors": ["first_qualifying_only"],
    "qualifying_color_is_not_modal": ["keep_modal_only"],
    "header_marker_color_8_is_qualifying_data": ["ignore_data_color_8"],
    "filtered_row_differs_from_header_mask": ["repeat_header_mask"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo lesson to defeat the named shortcut family."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    n8_values: set[int] = set()
    analyses: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analysis(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the exact-frequency stripe rule")
        analyses.append(analysis)
        n8_values.add(analysis["n8"])

    if n8_values != {1, 2, 3, 4}:
        reasons.append(f"demonstrations do not cover N=1,2,3,4 (saw {sorted(n8_values)})")
    if analyses and not any(len(analysis["targets"]) >= 2 for analysis in analyses):
        reasons.append("demonstrations never show multiple qualifying colours")
    if analyses and not any(8 in analysis["targets"] for analysis in analyses):
        reasons.append("demonstrations never show colour 8 acting as ordinary qualifying data")
    if analyses and not any(
        max(analysis["counts"][color] for color in analysis["distractors"]) > analysis["n8"]
        for analysis in analyses
    ):
        reasons.append("demonstrations never refute modal-colour selection")

    for name, competitor in LESSON_COMPETITORS.items():
        if analyses and len(analyses) == len(demos):
            if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the canonical Racket rule owns output."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = int(sample_index) % 4
    default_h, default_w, default_n8, default_sep, default_gap, desired_targets = _PROFILES[profile]
    height = _scheduled_int(ctx, "grid_h", 10, 18, default_h)
    width = _scheduled_int(ctx, "grid_w", 10, 18, default_w)
    n8 = _scheduled_int(ctx, "n8", 1, 4, default_n8)
    separator = _scheduled_int(ctx, "sep_row", 5, 7, default_sep)
    data_gap = _scheduled_int(ctx, "data_gap", 1, 2, default_gap)

    if separator <= n8:
        raise ValueError("internal contract violated: separator must leave N blank stripe rows")
    data_row = separator + data_gap
    if data_row >= height:
        raise ValueError("internal contract violated: data row does not fit")

    max_targets = min(3, (width - 1) // n8)
    target_count = min(desired_targets, max_targets)
    remaining = width - target_count * n8
    distractor_counts = _choose_distractor_counts(
        remaining,
        n8,
        profile,
        max_parts=min(4, len(_DATA_COLORS) - target_count),
    )

    rng = ctx.draw_rng(f"data-layout:{difficulty or 'medium'}")
    colors = _select_colors(rng, target_count + len(distractor_counts), profile, target_count)
    target_colors = colors[:target_count]
    distractor_colors = colors[target_count:]

    data: list[int] = []
    for color in target_colors:
        data.extend([color] * n8)
    for color, count in zip(distractor_colors, distractor_counts):
        data.extend([color] * count)
    rng.shuffle(data)

    # The fixed-position/header-mask rival must not survive by accidental layout.
    for _ in range(width):
        counts = Counter(data)
        targets = {color for color, count in counts.items() if count == n8}
        filtered = [value if value in targets else 0 for value in data]
        header = [8] * n8 + [0] * (width - n8)
        if filtered != header:
            break
        data = data[1:] + data[:1]
    else:  # pragma: no cover - construction guarantees a different palette/mask
        raise ValueError("could not separate filtered data from header-mask rival")

    grid = full_grid(height, width, 0)
    grid[0][:n8] = [8] * n8
    grid[separator] = [5] * width
    grid[data_row] = list(data)

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {name: value for name, value in overrides.items()}},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [row[:] for row in grid]
