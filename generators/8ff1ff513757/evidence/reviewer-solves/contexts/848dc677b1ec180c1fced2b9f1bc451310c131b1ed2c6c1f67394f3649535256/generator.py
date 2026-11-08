"""Generator for ARC task 8ff1ff513757 — nonempty-row compression.

The Racket oracle removes every all-zero row, preserves every nonempty row
byte-for-byte and in order, and leaves the column count unchanged.  Ordinary
lessons therefore contain separated nonempty rows plus blank rows at varied
leading, trailing, internal, and consecutive positions.  A globally blank
column and varied row textures rebut crop-to-content and blank-column removal
shortcuts.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8ff1ff513757"
TASK_ID = GENERATOR_ID
VERSION = "2.2.0"
RULE_HASH = "ed6dfa957511"

SUMMARY = (
    "A 0-background grid contains two through six pairwise separated nonempty "
    "rows and at least two all-zero rows.  Delete every all-zero row while "
    "preserving each nonempty row, its order, and the original width."
)

INVARIANTS = [
    "background is 0 and at least one entire column remains all-zero",
    "2-6 nonempty rows are pairwise separated by at least one all-zero row",
    "at least two all-zero rows make the transformation visibly non-identity",
    "at least two nonzero colors and two distinct row masks prevent constant-row shortcuts",
    "at least one nonempty row is singleton or has separated nonzero cells",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three canonical anchors then one difficulty-skewed 6..12 draw",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "three canonical anchors then one difficulty-skewed 5..12 draw",
        "valid": "5..12",
    },
    "n_active_rows": {
        "type": "int",
        "default": "difficulty-skewed 2..6 subject to nonadjacency",
        "valid": "2..6",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "canonical 4/3/4 anchors then one difficulty-skewed 2..6 draw",
        "valid": "2..6",
    },
}

LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_6x6",
    "canonical_7x7",
    "canonical_8x8",
    "broad",
)
_CANONICAL_PROFILE_AXES = {
    "canonical_6x6": (6, 6, 4),
    "canonical_7x7": (7, 7, 3),
    "canonical_8x8": (8, 8, 4),
}

# Pairwise-separated active rows, while forbidding both boundary rows at once,
# require at least two physical rows per active row.  These are the complete
# incompatible exact (height, active-row-count) pairs in the declared domain.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"grid_h": height, "n_active_rows": active_rows}
    for height in range(6, 13)
    for active_rows in range(2, 7)
    if height < 2 * active_rows
]

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the four-slot canonical-anchor / broad lesson profile."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    _band(difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_int_axis(ctx, overrides, name: str, lo: int, hi: int, default=None) -> int:
    """Draw an exact integer axis without coercing caller-provided scalars."""
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if default is not None and lo <= default <= hi:
        return ctx.draw_int(name, default, default)
    return ctx.draw_int_diff(name, lo, hi)


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9
        for row in grid
        for v in row
    ):
        return ["cells must be ARC colors 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    active_rows = [r for r, row in enumerate(grid) if any(v != 0 for v in row)]
    blank_rows = [r for r in range(h) if r not in active_rows]
    nonzero_colors = sorted({v for row in grid for v in row if v != 0})
    row_masks = [tuple(c for c, v in enumerate(grid[r]) if v != 0) for r in active_rows]
    blank_columns = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    has_sparse_signature = any(
        len(mask) == 1
        or any(b - a > 1 for a, b in zip(mask, mask[1:]))
        for mask in row_masks
    )

    if not (6 <= h <= 12 and 5 <= w <= 12):
        errors.append(f"dims {h}x{w} outside declared envelope 6..12 x 5..12")
    if not (2 <= len(active_rows) <= 6):
        errors.append(f"need 2..6 nonempty rows, found {len(active_rows)}")
    if len(blank_rows) < 2:
        errors.append(f"need at least two all-zero rows, found {len(blank_rows)}")
    if any(b == a + 1 for a, b in zip(active_rows, active_rows[1:])):
        errors.append("nonempty rows must be separated by all-zero rows")
    if len(nonzero_colors) < 2:
        errors.append("need at least two distinct nonzero colors")
    if len(set(row_masks)) < 2:
        errors.append("need at least two distinct nonempty-row masks")
    if not blank_columns:
        errors.append("need at least one all-zero column")
    if not has_sparse_signature:
        errors.append("need a singleton or a row with separated nonzero cells")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "active_rows": active_rows,
        "blank_rows": blank_rows,
        "n_active_rows": len(active_rows),
        "n_distinct_colors": len(nonzero_colors),
        "row_masks": row_masks,
        "blank_columns": blank_columns,
        "has_leading_blank": bool(blank_rows and blank_rows[0] == 0),
        "has_trailing_blank": bool(blank_rows and blank_rows[-1] == h - 1),
        "has_consecutive_blanks": any(
            b == a + 1 for a, b in zip(blank_rows, blank_rows[1:])
        ),
        "has_consecutive_internal_blanks": bool(active_rows)
        and any(
            active_rows[0] < r
            and r + 1 < active_rows[-1]
            and r + 1 in blank_rows
            for r in blank_rows
        ),
        "has_internal_blank": any(
            active_rows and active_rows[0] < r < active_rows[-1] for r in blank_rows
        ),
        "has_multicolor_row": any(
            len({v for v in grid[r] if v != 0}) >= 2 for r in active_rows
        ),
        "has_sparse_signature": has_sparse_signature,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding row-compression lessons."""
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """The teaching grammar is intentionally the task's canonical manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis directly from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_active_rows": analysis["n_active_rows"],
        "n_distinct_colors": analysis["n_distinct_colors"],
    }


def _active_row_candidates(h: int, n: int, slot: int) -> list[tuple[int, ...]]:
    candidates = [
        rows
        for rows in combinations(range(h), n)
        if all(b > a + 1 for a, b in zip(rows, rows[1:]))
        and (0 not in rows or h - 1 not in rows)
    ]
    def has_consecutive_internal_blanks(rows: tuple[int, ...]) -> bool:
        occupied = set(rows)
        return any(
            rows[0] < r
            and r + 1 < rows[-1]
            and r not in occupied
            and r + 1 not in occupied
            for r in range(h - 1)
        )

    if slot == 0:
        preferred = [rows for rows in candidates if 0 not in rows]
    elif slot == 1:
        preferred = [rows for rows in candidates if h - 1 not in rows]
    elif slot == 2:
        preferred = [rows for rows in candidates if has_consecutive_internal_blanks(rows)]
    else:
        preferred = [
            rows
            for rows in candidates
            if 0 not in rows
            and h - 1 not in rows
            and has_consecutive_internal_blanks(rows)
        ]
    return preferred or candidates


def _row_positions(
    *, w: int, blank_col: int, count: int, row_index: int, rng
) -> tuple[int, ...]:
    available = [c for c in range(w) if c != blank_col]
    if count > len(available):
        raise ValueError("requested row density exceeds non-blank columns")

    if row_index == 0 and count >= 2:
        chosen = {available[0], available[-1]}
        middle = [c for c in available[1:-1]]
        chosen.update(rng.sample(middle, count - 2))
        return tuple(sorted(chosen))

    if row_index == 1:
        runs = [
            tuple(range(start, start + count))
            for start in range(w - count + 1)
            if blank_col not in range(start, start + count)
        ]
        if runs:
            return rng.choice(runs)

    return tuple(sorted(rng.sample(available, count)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be a literal integer")

    band = _band(difficulty)
    slot = sample_index % LESSON_SCHEDULE_PERIOD
    profile = schedule_profile(seed, sample_index, band)
    canonical_axes = _CANONICAL_PROFILE_AXES.get(profile)

    requested_n = overrides.get("n_active_rows")
    if requested_n is not None and not 2 <= requested_n <= 6:
        raise ValueError("n_active_rows must be in 2..6")

    # A single legal n_active_rows override should succeed without depending on
    # a hidden random height.  Exact incompatible combinations still reject.
    min_h = max(6, 2 * requested_n) if requested_n is not None else 6
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _draw_int_axis(
        ctx,
        overrides,
        "grid_h",
        min_h,
        12,
        canonical_axes[0] if canonical_axes else None,
    )
    w = _draw_int_axis(
        ctx,
        overrides,
        "grid_w",
        5,
        12,
        canonical_axes[1] if canonical_axes else None,
    )

    max_active = min(6, h // 2)
    # Slots 2 and 3 teach that *every* row in a multi-row internal blank run
    # disappears.  Keep enough default slack for two consecutive internal
    # blanks; exact overrides remain supported and may fall back to the broad
    # lawful candidate set when that teaching witness is impossible.
    default_max_active = (
        min(max_active, (h - 2) // 2) if slot in (2, 3) else max_active
    )
    n_active = _draw_int_axis(
        ctx,
        overrides,
        "n_active_rows",
        2,
        max_active if requested_n is not None else max(2, default_max_active),
    )
    n_colors = _draw_int_axis(
        ctx,
        overrides,
        "n_distinct_colors",
        2,
        6,
        canonical_axes[2] if canonical_axes else None,
    )

    rng = ctx.draw_rng("layout")
    candidates = _active_row_candidates(h, n_active, slot)
    if not candidates:
        raise ValueError(
            f"no lawful nonadjacent placement for h={h}, n_active_rows={n_active}"
        )
    active_rows = list(rng.choice(candidates))
    blank_col = rng.randrange(w)

    # At least two cells per active row gives enough capacity for all six exact
    # colors even at the minimum two-row setting, while the reserved blank
    # column leaves the width-preservation shortcut witness visible.
    counts = [2] * n_active
    extra_needed = max(0, n_colors - sum(counts))
    cursor = 0
    while extra_needed:
        if counts[cursor] < w - 1:
            counts[cursor] += 1
            extra_needed -= 1
        cursor = (cursor + 1) % n_active

    positions: list[tuple[int, int]] = []
    row_masks: list[tuple[int, ...]] = []
    for index, row in enumerate(active_rows):
        mask = _row_positions(
            w=w,
            blank_col=blank_col,
            count=counts[index],
            row_index=index,
            rng=rng,
        )
        row_masks.append(mask)
        positions.extend((row, c) for c in mask)

    if len(set(row_masks)) < 2:
        # Deterministic boundary fallback: alter the final row's mask without
        # changing any declared axis or the reserved all-zero column.
        available = [c for c in range(w) if c != blank_col]
        replacement = tuple(available[-counts[-1] :])
        old = row_masks[-1]
        positions = [p for p in positions if p[0] != active_rows[-1]]
        if replacement == old:
            replacement = tuple(available[: counts[-1]])
        row_masks[-1] = replacement
        positions.extend((active_rows[-1], c) for c in replacement)

    colors = list(ctx.draw_distinct_colors("colors", n=n_colors, exclude={0}))
    rng.shuffle(colors)
    assignments = colors + [rng.choice(colors) for _ in range(len(positions) - n_colors)]
    # Force the first sparse row to carry two different colors, rebutting a
    # modal-color echo while preserving the exact color cardinality.
    if len(positions) >= 2:
        assignments[0], assignments[1] = colors[0], colors[1]

    grid = full_grid(h, w, 0)
    for (r, c), color in zip(positions, assignments):
        grid[r][c] = color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid row-compression lesson: " + "; ".join(errors))
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror of the selected Racket rule, for audits and rival checks."""
    errors = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    kept = [list(row) for row in grid if any(value != 0 for value in row)]
    return kept or [[0] * len(grid[0])]


def _rival_preserve_trailing_blank_rows(grid) -> list[list[int]]:
    """Delete blank rows only through the final nonempty row.

    Every canonical input ends on a nonempty row, so this wrong rule agrees
    with all canonical outputs while diverging on a trailing-blank witness.
    """
    errors = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    active = [index for index, row in enumerate(grid) if any(value != 0 for value in row)]
    if not active:
        return rule_mirror(grid)
    last_active = active[-1]
    return [
        list(row)
        for index, row in enumerate(grid)
        if any(value != 0 for value in row) or index > last_active
    ]


def _rival_remove_one_internal_separator(grid) -> list[list[int]]:
    """Remove one row from each internal blank run, not the entire run.

    Canonical internal separators are all one row deep.  Consecutive internal
    blanks therefore provide the exact counterexample this rival needs.
    """
    errors = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    active = [index for index, row in enumerate(grid) if any(value != 0 for value in row)]
    if not active:
        return rule_mirror(grid)

    first_active, last_active = active[0], active[-1]
    out: list[list[int]] = []
    row_index = 0
    while row_index < len(grid):
        if any(value != 0 for value in grid[row_index]):
            out.append(list(grid[row_index]))
            row_index += 1
            continue

        run_start = row_index
        while row_index < len(grid) and not any(
            value != 0 for value in grid[row_index]
        ):
            row_index += 1
        run_end = row_index
        if first_active < run_start and run_end - 1 < last_active:
            out.extend(list(grid[index]) for index in range(run_start + 1, run_end))
    return out or [[0] * len(grid[0])]


SEMANTIC_RIVALS = {
    "preserve_trailing_blank_rows": _rival_preserve_trailing_blank_rows,
    "remove_one_internal_separator": _rival_remove_one_internal_separator,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness(name: str):
    def predicate(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(analysis[name])

    return predicate


# Keep this contract narrow: every declared witness names a concrete rival it
# disproves.  Other structural coverage remains available through _analysis and
# lesson_identifiable without being mislabeled as rival-disagreement evidence.
SEMANTIC_WITNESSES = {
    "trailing_blank_row": _witness("has_trailing_blank"),
    "consecutive_internal_blank_rows": _witness(
        "has_consecutive_internal_blanks"
    ),
}
WITNESS_RIVALS = {
    "trailing_blank_row": ["preserve_trailing_blank_rows"],
    "consecutive_internal_blank_rows": ["remove_one_internal_separator"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons a declared canonical shortcut can still change the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    analyses = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analysis(pair["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside teaching grammar")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} does not preserve nonempty rows exactly")
        if len(pair["output"]) >= len(pair["input"]):
            reasons.append(f"demo {index} does not visibly remove rows")
        if pair["output"] and len(pair["output"][0]) != len(pair["input"][0]):
            reasons.append(f"demo {index} changes width")
        analyses.append(analysis)

    query_analysis = _analysis(query["input"])
    if query_analysis["errors"]:
        reasons.append("query input is outside teaching grammar")
    elif "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the selected rule")

    if reasons:
        return reasons
    if not any(a["has_leading_blank"] for a in analyses):
        reasons.append("no demonstration removes a leading blank row")
    if not any(a["has_trailing_blank"] for a in analyses):
        reasons.append("no demonstration removes a trailing blank row")
    if not any(a["has_internal_blank"] for a in analyses):
        reasons.append("no demonstration removes an internal blank row")
    if not any(a["has_consecutive_internal_blanks"] for a in analyses):
        reasons.append("no demonstration removes consecutive internal blank rows")
    if not all(a["blank_columns"] for a in analyses):
        reasons.append("a demonstration lacks a preserved all-zero column")
    if not any(a["has_multicolor_row"] for a in analyses):
        reasons.append("no demonstration preserves a multicolor active row")

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"competitor {name!r} fits every demonstration and changes "
                    "the query answer"
                )
    return reasons
