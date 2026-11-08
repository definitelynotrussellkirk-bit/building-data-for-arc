"""Generator for ARC task c7e57ac1ddec: bridge single horizontal gaps.

The canonical rule scans each row and changes exactly the middle zero of every
``2, 0, 2`` pattern to orange (7).  Longer horizontal gaps, vertical
``2, 0, 2`` patterns, adjacent red pairs, and isolated red cells are deliberate
distractors and remain unchanged.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c7e57ac1ddec"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6002ec5a82cc"

SUMMARY = (
    "On a zero background, fill with orange (7) every zero that has red (2) "
    "immediately to its left and right in the same row. Leave vertical 2-0-2 "
    "patterns, adjacent red pairs, isolated red cells, and horizontal gaps of "
    "two or more zeros unchanged."
)

INVARIANTS = [
    "the input is a rectangular 7..12 by 10..14 grid using only colors 0 and 2",
    "there are exactly 4..8 horizontal single-cell 2-0-2 targets",
    "there are exactly 1..3 longer horizontal red-to-red gaps",
    "at least one vertical 2-0-2 distractor is present",
    "ordinary draws also contain an adjacent red pair and multiple targets in one row",
]

# Every declared axis is exact and is recovered directly from the returned grid
# by observe_overrides().  All Cartesian boundary combinations fit in 7x10.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "10..14",
    },
    "n_targets": {
        "type": "int",
        "default": "scheduled 4..6",
        "valid": "4..8",
    },
    "n_long_gaps": {
        "type": "int",
        "default": "scheduled 1..3",
        "valid": "1..3",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

# The four profiles mirror the real task's four (height, width) profiles and its
# observed target/long-gap counts.  Placement mode is not an override axis; it
# is a deterministic lesson-schedule branch used to expose both grid edges.
_PROFILES = (
    {
        "name": "canonical_7x11_dense",
        "grid_h": 7,
        "grid_w": 11,
        "n_targets": 5,
        "n_long_gaps": 1,
        "placement": "left_edge",
    },
    {
        "name": "canonical_7x10_compact",
        "grid_h": 7,
        "grid_w": 10,
        "n_targets": 4,
        "n_long_gaps": 1,
        "placement": "interior",
    },
    {
        "name": "canonical_8x12_complex",
        "grid_h": 8,
        "grid_w": 12,
        "n_targets": 6,
        "n_long_gaps": 3,
        "placement": "right_edge",
    },
    {
        "name": "canonical_7x12_wide",
        "grid_h": 7,
        "grid_w": 12,
        "n_targets": 4,
        "n_long_gaps": 2,
        "placement": "left_edge",
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)
_CANONICAL_DIMS = {(7, 10), (7, 11), (7, 12), (8, 12)}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum profile for semantic-gate auditing."""
    del seed
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    if difficulty not in offsets:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _PROFILES[(int(sample_index) + offsets[difficulty]) % len(_PROFILES)][
        "name"
    ]


def _profile_for(sample_index: int, difficulty: str | None) -> dict[str, object]:
    name = schedule_profile(0, sample_index, difficulty)
    return next(profile for profile in _PROFILES if profile["name"] == name)


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    bounds = {
        "grid_h": (7, 12),
        "grid_w": (10, 14),
        "n_targets": (4, 8),
        "n_long_gaps": (1, 3),
    }
    for name, (lo, hi) in bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _draw_exact_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence of rows")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if isinstance(row, str):
            values = [int(ch) for ch in row.strip()]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            raise ValueError("every grid row must be a sequence")
        if width is None:
            width = len(values)
            if width == 0:
                raise ValueError("grid rows must be non-empty")
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in values):
            raise ValueError("grid cells must be integer ARC colors in 0..9")
        rows.append(values)
    return rows


def _analyze(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}

    h, w = len(values), len(values[0])
    colors = {value for row in values for value in row}
    targets: list[tuple[int, int]] = []
    long_gaps: list[tuple[int, int, int, int]] = []
    adjacent_pairs: list[tuple[int, int]] = []
    row_target_counts: list[int] = []

    for r, row in enumerate(values):
        row_targets = [
            (r, c + 1)
            for c in range(w - 2)
            if row[c] == 2 and row[c + 1] == 0 and row[c + 2] == 2
        ]
        targets.extend(row_targets)
        row_target_counts.append(len(row_targets))
        adjacent_pairs.extend(
            (r, c) for c in range(w - 1) if row[c] == 2 and row[c + 1] == 2
        )
        red_cols = [c for c, value in enumerate(row) if value == 2]
        for left, right in zip(red_cols, red_cols[1:]):
            gap = right - left - 1
            if gap >= 2:
                long_gaps.append((r, left, right, gap))

    vertical_targets = [
        (r + 1, c)
        for r in range(h - 2)
        for c in range(w)
        if values[r][c] == 2
        and values[r + 1][c] == 0
        and values[r + 2][c] == 2
    ]
    target_set = set(targets)
    vertical_only = [cell for cell in vertical_targets if cell not in target_set]

    errors: list[str] = []
    if not 7 <= h <= 12 or not 10 <= w <= 14:
        errors.append(f"grid dimensions {h}x{w} must be within 7..12 by 10..14")
    if not colors <= {0, 2}:
        errors.append(f"input colors must be a subset of {{0,2}}, found {sorted(colors)}")
    if not 4 <= len(targets) <= 8:
        errors.append(f"expected 4..8 horizontal 2-0-2 targets, found {len(targets)}")
    if not 1 <= len(long_gaps) <= 3:
        errors.append(f"expected 1..3 longer horizontal gaps, found {len(long_gaps)}")
    if not vertical_only:
        errors.append("expected at least one vertical 2-0-2 distractor left unchanged")

    return {
        "errors": errors,
        "grid": values,
        "height": h,
        "width": w,
        "colors": colors,
        "red_count": sum(value == 2 for row in values for value in row),
        "targets": targets,
        "target_count": len(targets),
        "long_gaps": long_gaps,
        "long_gap_count": len(long_gaps),
        "vertical_targets": vertical_targets,
        "vertical_only": vertical_only,
        "adjacent_pairs": adjacent_pairs,
        "row_target_counts": row_target_counts,
    }


def _analysis_or_raise(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return analysis


def _target_rows(
    w: int,
    first_targets: int,
    second_targets: int,
    placement: str,
    rng,
) -> tuple[list[int], list[int], int]:
    """Build two target-chain rows plus an adjacent-pair distractor.

    The same chain anchor occurs in both rows.  Placing them two rows apart
    therefore guarantees a vertical 2-0-2 distractor in the blank row between.
    """
    first_len = 2 * first_targets + 2  # chain plus one adjacent red
    second_len = 2 * second_targets + 1
    footprint = max(first_len, second_len)
    if footprint > w:
        raise ValueError(f"width {w} cannot hold {first_targets}+{second_targets} targets")

    if placement == "left_edge":
        base = 0
        adjacent_side = "right"
    elif placement == "right_edge":
        base = w - footprint
        adjacent_side = "left"
    else:
        adjacent_side = rng.choice(("left", "right"))
        lo, hi = 0, w - footprint
        if hi <= 1:
            base = lo
        else:
            base = rng.randint(1, hi - 1) if hi >= 2 else rng.randint(lo, hi)

    if adjacent_side == "left":
        anchor = base + 1
        first_reds = [base, *range(anchor, anchor + 2 * first_targets + 1, 2)]
    else:
        anchor = base
        chain = list(range(anchor, anchor + 2 * first_targets + 1, 2))
        first_reds = [*chain, chain[-1] + 1]
    second_reds = list(range(anchor, anchor + 2 * second_targets + 1, 2))
    return first_reds, second_reds, anchor


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile = _profile_for(sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_exact_int(ctx, overrides, "grid_h", int(profile["grid_h"]), 7, 12)
    w = _draw_exact_int(ctx, overrides, "grid_w", int(profile["grid_w"]), 10, 14)
    n_targets = _draw_exact_int(
        ctx, overrides, "n_targets", int(profile["n_targets"]), 4, 8
    )
    n_long = _draw_exact_int(
        ctx, overrides, "n_long_gaps", int(profile["n_long_gaps"]), 1, 3
    )
    rng = ctx.draw_rng("layout")

    grid = full_grid(h, w, 0)
    triple_start = rng.randint(0, h - 3)
    first_row, middle_row, second_row = (
        triple_start,
        triple_start + 1,
        triple_start + 2,
    )

    first_targets = (n_targets + 1) // 2
    second_targets = n_targets // 2
    first_reds, second_reds, vertical_anchor = _target_rows(
        w,
        first_targets,
        second_targets,
        str(profile["placement"]),
        rng,
    )
    for col in first_reds:
        grid[first_row][col] = 2
    for col in second_reds:
        grid[second_row][col] = 2

    eligible_long_rows = [
        row
        for row in range(h)
        if row not in (first_row, middle_row, second_row)
    ]
    rng.shuffle(eligible_long_rows)
    long_rows = eligible_long_rows[:n_long]
    if len(long_rows) != n_long:
        raise ValueError(f"height {h} cannot place {n_long} long-gap distractors")
    for index, row in enumerate(long_rows):
        max_gap = min(6, w - 2)
        # Cycle 2..max_gap before adding keyed variation, matching the canonical
        # range (2, 3, 4, and 6 cells) without ever creating a single gap.
        gap = 2 + ((sample_index + index + rng.randint(0, max_gap - 2)) % (max_gap - 1))
        span = gap + 2
        start = rng.randint(0, w - span)
        grid[row][start] = 2
        grid[row][start + span - 1] = 2

    # Add isolated red cells until the total red mass is canonical-like (about
    # 14) without inventing another horizontal pair.  One isolated red per
    # otherwise blank row keeps the count observable and the grammar simple.
    occupied_rows = {first_row, second_row, *long_rows}
    blank_rows = [row for row in range(h) if row not in occupied_rows]
    rng.shuffle(blank_rows)
    current_red = sum(value == 2 for row in grid for value in row)
    isolated_needed = min(len(blank_rows), max(0, 14 - current_red))
    for row in blank_rows[:isolated_needed]:
        choices = list(range(w))
        if row == middle_row and vertical_anchor in choices:
            choices.remove(vertical_anchor)
        col = rng.choice(choices)
        grid[row][col] = 2

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": ctx.overrides_used()},
    )
    if errors:
        raise AssertionError("generator produced invalid task grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "grid_h": h,
        "grid_w": w,
        "n_targets": n_targets,
        "n_long_gaps": n_long,
    }
    if observed != requested:
        raise AssertionError(f"exact-axis mismatch: requested={requested}, observed={observed}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides")
    if isinstance(requested, dict):
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in observed and observed[axis] != value:
                errors.append(f"meta {axis} requested {value!r}, observed {observed[axis]!r}")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis_or_raise(grid)
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_targets": analysis["target_count"],
        "n_long_gaps": analysis["long_gap_count"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    reasons: list[str] = []
    dims = (analysis["height"], analysis["width"])
    if dims not in _CANONICAL_DIMS:
        reasons.append(f"dimensions {dims} are outside the four canonical profiles")
    if analysis["target_count"] not in (4, 5, 6):
        reasons.append("canonical inputs contain 4..6 horizontal single-gap targets")
    if not 11 <= analysis["red_count"] <= 15:
        reasons.append(
            f"canonical inputs contain 11..15 red cells, found {analysis['red_count']}"
        )
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic Python mirror; canonical Racket remains output authority."""
    analysis = _analysis_or_raise(grid)
    out = [row[:] for row in analysis["grid"]]
    for row, col in analysis["targets"]:
        out[row][col] = 7
    return out


def _rival_fill_all_horizontal_gaps(grid):
    analysis = _analysis_or_raise(grid)
    out = [row[:] for row in analysis["grid"]]
    for row, values in enumerate(analysis["grid"]):
        reds = [col for col, value in enumerate(values) if value == 2]
        for left, right in zip(reds, reds[1:]):
            for col in range(left + 1, right):
                out[row][col] = 7
    return out


def _rival_fill_horizontal_and_vertical(grid):
    analysis = _analysis_or_raise(grid)
    out = rule_mirror(analysis["grid"])
    for row, col in analysis["vertical_targets"]:
        if out[row][col] == 0:
            out[row][col] = 7
    return out


def _rival_first_target_only(grid):
    analysis = _analysis_or_raise(grid)
    out = [row[:] for row in analysis["grid"]]
    row, col = analysis["targets"][0]
    out[row][col] = 7
    return out


def _rival_fill_targets_with_red(grid):
    analysis = _analysis_or_raise(grid)
    out = [row[:] for row in analysis["grid"]]
    for row, col in analysis["targets"]:
        out[row][col] = 2
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "fill_all_horizontal_gaps": _rival_fill_all_horizontal_gaps,
    "fill_horizontal_and_vertical": _rival_fill_horizontal_and_vertical,
    "fill_first_target_only": _rival_first_target_only,
    "fill_targets_with_red": _rival_fill_targets_with_red,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis.get("errors") else analysis


def _has_unfilled_vertical_distractor(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and bool(analysis["vertical_only"])


def _has_left_edge_target(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and any(col == 1 for _, col in analysis["targets"])


def _has_right_edge_target(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and any(
        col == analysis["width"] - 2 for _, col in analysis["targets"]
    )


SEMANTIC_WITNESSES = {
    "canonical_linked_profile": lambda grid: strict_canonical_like(grid) == [],
    "multiple_targets": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["target_count"] >= 4
    ),
    "multiple_targets_same_row": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and max(analysis["row_target_counts"]) >= 2
    ),
    "long_gap_left_unchanged": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["long_gap_count"] >= 1
    ),
    "vertical_gap_left_unchanged": _has_unfilled_vertical_distractor,
    "left_edge_target": _has_left_edge_target,
    "right_edge_target": _has_right_edge_target,
    "orange_not_red": lambda grid: _valid_analysis(grid) is not None,
}

WITNESS_RIVALS = {
    "canonical_linked_profile": ["fill_first_target_only"],
    "multiple_targets": ["fill_first_target_only"],
    "multiple_targets_same_row": ["fill_first_target_only"],
    "long_gap_left_unchanged": ["fill_all_horizontal_gaps"],
    "vertical_gap_left_unchanged": ["fill_horizontal_and_vertical"],
    "left_edge_target": ["fill_first_target_only"],
    "right_edge_target": ["fill_first_target_only"],
    "orange_not_red": ["fill_targets_with_red"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{label} input violates teaching grammar: {errors[0]}")
            continue
        try:
            expected = rule_mirror(pair["input"])
            actual = _coerce_grid(pair["output"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"{label} could not be checked: {exc}")
            continue
        if expected != actual:
            reasons.append(f"{label} output disagrees with the horizontal single-gap rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == _coerce_grid(demo["output"])
            for demo in demos
        )
        if survives:
            if competitor(query["input"]) != _coerce_grid(query["output"]):
                reasons.append(
                    f"competing rule {name!r} fits every demo but answers the query differently"
                )
            else:
                reasons.append(
                    f"competing rule {name!r} survives every demo and the query"
                )
    return reasons
