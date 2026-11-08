"""Generator for ARC task b5df32f2dc17 — sort row-runs by length.

Each input row contains zero or more separated monochrome runs.  The
authoritative rule extracts the runs independently per row, sorts them
longest-to-shortest, and re-packs them from column 0 with exactly one black
separator.  Ordinary draws mix a true sorting witness with already-sorted,
single-run, and (when capacity permits) blank control rows.  This makes the
row-wise scope and the separate re-packing step visible instead of teaching a
homogeneous "every row has the same number of runs" shortcut.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b5df32f2dc17"
TASK_ID = GENERATOR_ID
RULE_HASH = "5afe989c75c5"  # sha256[:12] of whitespace-normalized canonical rule
VERSION = "3.1.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "For each row independently, extract every monochrome nonzero run, sort "
    "those runs by descending length, preserve each run's color and length, "
    "then rebuild the row from column 0 with one 0 separator between runs. "
    "Generated lessons combine a genuine sorting witness with already-sorted, "
    "single-run, and blank controls so both row-wise scope and left-packing are "
    "identifiable rather than inferred from homogeneous rows."
)

INVARIANTS = [
    "inputs are 3..5 rows by 11..14 columns with background 0",
    "nonblank rows contain zero-separated monochrome runs of length 2..5",
    "within a multi-run row, run lengths are distinct and colors are distinct",
    "every ordinary scene has a reorder witness, an already-sorted control, and a singleton control",
    "n_runs is the maximum number of runs in any row, not a per-row uniform count",
]

# Only caller-facing controls that are exactly recoverable from a generated grid
# are declared.  The old palette/texture/bias aliases were unobservable or dead.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 3..5", "valid": "3..5"},
    "grid_w": {"type": "int", "default": "difficulty-aware 11..14", "valid": "11..14"},
    "n_runs": {"type": "int", "default": "maximum per-row count, scheduled 2..3", "valid": "2..3"},
    "palette_size": {"type": "int", "default": "difficulty-aware 3..6", "valid": "3..6"},
}

SCHEDULE_PROFILES = (
    "two_run_with_controls",
    "three_run_middle_longest_with_controls",
    "three_run_tail_longest_with_controls",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic three-slot lesson schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    errors: list[str] = []
    for r, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {r} is ragged")
            continue
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be literal ARC integers 0..9")
                return errors
    return errors


def _row_runs(row):
    """Return (start, length, color) for zero-separated monochrome runs."""
    runs = []
    c = 0
    while c < len(row):
        if row[c] == 0:
            c += 1
            continue
        start = c
        color = row[c]
        while c + 1 < len(row) and row[c + 1] == color:
            c += 1
        runs.append((start, c - start + 1, color))
        c += 1
    return runs


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "rows": []}
    h, w = len(grid), len(grid[0])
    if not 3 <= h <= 5:
        errors.append(f"height must be in 3..5, found {h}")
    if not 11 <= w <= 14:
        errors.append(f"width must be in 11..14, found {w}")

    row_infos = []
    saw_reordering = False
    for r, row in enumerate(grid):
        # Different nonzero colors touching are distinct according to the Racket
        # implementation, but the teaching grammar deliberately requires a 0 gap
        # so a learner can see the run boundaries unambiguously.
        for c in range(1, w):
            if row[c - 1] != 0 and row[c] != 0 and row[c - 1] != row[c]:
                errors.append(f"row {r}: adjacent differently-colored runs need a 0 separator")
                break
        runs = _row_runs(row)
        lengths = [length for _, length, _ in runs]
        colors = [color for _, _, color in runs]
        if any(length < 2 or length > 5 for length in lengths):
            errors.append(f"row {r}: run lengths must be in 2..5")
        if len(lengths) >= 2 and len(set(lengths)) != len(lengths):
            errors.append(f"row {r}: multi-run lengths must be distinct")
        if len(colors) >= 2 and len(set(colors)) != len(colors):
            errors.append(f"row {r}: run colors must be distinct")
        if len(runs) >= 2 and lengths != sorted(lengths, reverse=True):
            saw_reordering = True
        row_infos.append({"runs": runs, "lengths": lengths, "colors": colors})

    if not any(len(info["runs"]) >= 2 for info in row_infos):
        errors.append("scene needs at least one row with multiple runs")
    if not saw_reordering:
        errors.append("scene hides the sorting rule: all multi-run rows are already longest-first")

    palette = {value for row in grid for value in row if value != 0}
    if len(palette) < 2:
        errors.append("scene needs at least two non-background colors")
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "rows": row_infos,
        "palette": palette,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, and rule-hiding teaching scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The task-linked grammar shared by canonical and generated inputs."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact generated axis from the returned grid."""
    if _grid_errors(grid):
        return {}
    rows = [_row_runs(row) for row in grid]
    positive_counts = [len(runs) for runs in rows if runs]
    result = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len({v for row in grid for v in row if v != 0}),
    }
    if positive_counts:
        result["n_runs"] = max(positive_counts)
    return result


def _repack(grid, key):
    out = []
    width = len(grid[0])
    for row in grid:
        runs = _row_runs(row)
        ordered = key(runs)
        new_row = [0] * width
        c = 0
        for index, (_, length, color) in enumerate(ordered):
            for offset in range(length):
                if c + offset < width:
                    new_row[c + offset] = color
            c += length + (1 if index + 1 < len(ordered) else 0)
        out.append(new_row)
    return out


def rule_mirror(grid):
    """Independent Python mirror for tests; the canonical Racket remains authority."""
    return _repack(grid, lambda runs: sorted(runs, key=lambda run: (-run[1], run[0])))


def _rival_keep_order(grid):
    return _repack(grid, lambda runs: list(runs))


def _rival_ascending_length(grid):
    return _repack(grid, lambda runs: sorted(runs, key=lambda run: (run[1], run[0])))


def _rival_reverse_input(grid):
    return _repack(grid, lambda runs: list(reversed(runs)))


def _rival_color_desc(grid):
    return _repack(grid, lambda runs: sorted(runs, key=lambda run: (-run[2], run[0])))


def _rival_multi_run_rows_only(grid):
    """Wrong shortcut: transform multi-run rows but ignore singleton rows."""
    intended = rule_mirror(grid)
    return [
        intended[index] if len(_row_runs(row)) >= 2 else list(row)
        for index, row in enumerate(grid)
    ]


def _rival_leave_already_sorted_rows(grid):
    """Wrong shortcut: sort disorderly rows but skip re-packing sorted ones."""
    intended = rule_mirror(grid)
    out = []
    for index, row in enumerate(grid):
        runs = _row_runs(row)
        lengths = [length for _, length, _ in runs]
        if len(runs) >= 2 and lengths == sorted(lengths, reverse=True):
            out.append(list(row))
        else:
            out.append(intended[index])
    return out


SEMANTIC_RIVALS = {
    "preserve_run_order": _rival_keep_order,
    "sort_shortest_first": _rival_ascending_length,
    "reverse_run_order": _rival_reverse_input,
    "sort_by_color": _rival_color_desc,
    "multi_run_rows_only": _rival_multi_run_rows_only,
    "leave_already_sorted_rows": _rival_leave_already_sorted_rows,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# These four were the prior task-local canonical hypotheses.  The two row-role
# rivals above are lesson competitors, but they do not reproduce every labelled
# canonical pair (the held-out canonical input contains a singleton row).
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "preserve_run_order",
        "sort_shortest_first",
        "reverse_run_order",
        "sort_by_color",
    )
}


def _differs_from(rival):
    def predicate(grid):
        return not self_check(grid) and rule_mirror(grid) != rival(grid)
    return predicate


SEMANTIC_WITNESSES = {
    "requires_reordering": _differs_from(_rival_keep_order),
    "descending_not_ascending": _differs_from(_rival_ascending_length),
    "nontrivial_three_run_order": _differs_from(_rival_reverse_input),
    "length_not_color": _differs_from(_rival_color_desc),
    "singleton_rows_are_repacked": _differs_from(_rival_multi_run_rows_only),
    "already_sorted_rows_are_repacked": _differs_from(_rival_leave_already_sorted_rows),
}

WITNESS_RIVALS = {
    "requires_reordering": ["preserve_run_order"],
    "descending_not_ascending": ["sort_shortest_first"],
    "nontrivial_three_run_order": ["reverse_run_order"],
    "length_not_color": ["sort_by_color"],
    "singleton_rows_are_repacked": ["multi_run_rows_only"],
    "already_sorted_rows_are_repacked": ["leave_already_sorted_rows"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each three-demo lesson to kill every declared shortcut rule."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with longest-first sorting")
            continue
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    # Schedule-profile coverage is audited independently.  Do not reject a
    # query rotation merely because its remaining demonstrations share one
    # max-run count when those demonstrations already refute every named rival.

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos if isinstance(pair, dict) and "input" in pair and "output" in pair):
            reasons.append(f"named rival {name!r} survives every demonstration")
    return reasons


def _scheduled_n_runs(sample_index: int) -> int:
    return 2 if int(sample_index) % 3 == 0 else 3


def _length_order(n_runs: int, sample_index: int, row: int = 0) -> list[int]:
    """A nontrivial order whose descending sort is not simple reversal."""
    if n_runs == 2:
        pairs = ((2, 4), (3, 5), (2, 5), (3, 4))
        return list(pairs[(int(sample_index) + row) % len(pairs)])
    # All patterns total 9, so three runs plus two separators fit width 11.
    patterns = ((2, 4, 3), (3, 2, 4), (3, 4, 2), (4, 2, 3))
    return list(patterns[(int(sample_index) + row) % len(patterns)])


def _row_specs(h: int, n_runs: int, palette_size: int, sample_index: int):
    """Return mixed row roles with enough run slots to expose the palette."""
    specs = [
        {"role": "reorder", "lengths": _length_order(n_runs, sample_index)},
        {"role": "sorted", "lengths": [4, 2]},
        {"role": "single", "lengths": [2 + (int(sample_index) % 3)]},
    ]
    specs.extend({"role": "blank", "lengths": []} for _ in range(h - len(specs)))

    def slot_count() -> int:
        return sum(len(spec["lengths"]) for spec in specs)

    # Prefer consuming otherwise blank capacity.  The sole no-singleton corner
    # is the exact h=3/n_runs=2/palette_size=6 override, where six colors require
    # all three rows to have two runs.
    for index, spec in enumerate(specs):
        if slot_count() >= palette_size:
            break
        if spec["role"] == "blank":
            specs[index] = {"role": "single", "lengths": [2 + (index % 3)]}
    if slot_count() < palette_size:
        for index in range(len(specs) - 1, -1, -1):
            if specs[index]["role"] == "single":
                specs[index] = {"role": "sorted", "lengths": [5, 2]}
                break
    if slot_count() < palette_size:
        raise ValueError("grid does not have enough legal run slots for palette_size")

    # Rotate roles so control rows are not tied to fixed row indices.
    shift = int(sample_index) % h
    return specs[shift:] + specs[:shift]


def _ordered_colors(colors: list[int], role: str, sample_index: int, row: int) -> list[int]:
    if len(colors) < 2:
        return colors
    if role == "reorder":
        # Two-run scenes deliberately oppose numeric color order; three-run
        # scenes use ascending colors with a nontrivial length permutation.
        return sorted(colors, reverse=len(colors) == 2)
    if (int(sample_index) + row) % 2:
        return sorted(colors)
    return sorted(colors, reverse=True)


def _paint_spec_row(
    grid, row: int, width: int, spec, colors, layout_rng, sample_index: int
) -> None:
    lengths = list(spec["lengths"])
    if not lengths:
        return
    colors = _ordered_colors(list(colors), spec["role"], sample_index, row)
    minimum = sum(lengths) + max(0, len(lengths) - 1)
    slack = width - minimum
    if slack < 0:
        raise ValueError(f"row role {spec['role']!r} does not fit width {width}")

    if spec["role"] in {"sorted", "single"}:
        # These are explicit re-packing controls: even when no run order changes,
        # the authoritative output must shift left and normalize separators.
        start = 1 + layout_rng.randint(0, min(1, slack - 1)) if slack >= 1 else 0
    else:
        start = layout_rng.randint(0, min(2, slack)) if slack else 0
    slack -= start

    gaps = [1] * max(0, len(lengths) - 1)
    if spec["role"] == "sorted" and gaps and slack:
        gaps[0] += 1
        slack -= 1
    for index in range(len(gaps)):
        if slack <= 0:
            break
        extra = layout_rng.randint(0, slack)
        gaps[index] += extra
        slack -= extra

    column = start
    for index, (length, color) in enumerate(zip(lengths, colors)):
        for offset in range(length):
            grid[row][column + offset] = color
        column += length
        if index < len(gaps):
            column += gaps[index]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic mixed-role input grid; Racket owns the output."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_anchor = not overrides and int(sample_index) % 4 == 0
    if "grid_h" in overrides:
        h = ctx.draw_int("grid_h", 3, 5)
    elif canonical_anchor:
        h = ctx.draw_choice("grid_h", (4,))
    else:
        h = ctx.draw_int_diff("grid_h", 3, 5)

    if "grid_w" in overrides:
        w = ctx.draw_int("grid_w", 11, 14)
    elif canonical_anchor:
        w = ctx.draw_choice("grid_w", (12, 13))
    else:
        w = ctx.draw_int_diff("grid_w", 11, 14)

    if "n_runs" in overrides:
        n_runs = ctx.draw_choice("n_runs", (2, 3))
    else:
        n_runs = ctx.draw_choice("n_runs", (_scheduled_n_runs(sample_index),))

    if "palette_size" in overrides:
        palette_size = ctx.draw_int("palette_size", 3, 6)
    elif canonical_anchor:
        palette_size = ctx.draw_choice("palette_size", (6,))
    else:
        if difficulty == "easy":
            palette_options = (3, 4)
        elif difficulty == "hard":
            palette_options = (5, 6)
        else:
            palette_options = (3, 4, 5, 6)
        # Ordinary h=3/two-run lessons reserve one singleton row, leaving five
        # run slots.  Exact overrides may still request the legal six-color
        # corner, which upgrades that singleton to a second sorted control row.
        if h == 3 and n_runs == 2:
            palette_options = tuple(value for value in palette_options if value <= 5)
        palette_size = ctx.draw_choice("palette_size", palette_options)

    palette_rng = ctx.draw_rng("palette")
    palette = sorted(palette_rng.sample(list(range(1, 10)), palette_size))
    specs = _row_specs(h, n_runs, palette_size, sample_index)
    slot_count = sum(len(spec["lengths"]) for spec in specs)
    offset = palette_rng.randrange(palette_size)
    assigned = [palette[(offset + index) % palette_size] for index in range(slot_count)]

    layout_rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    cursor = 0
    for row, spec in enumerate(specs):
        count = len(spec["lengths"])
        colors = assigned[cursor:cursor + count]
        cursor += count
        _paint_spec_row(grid, row, w, spec, colors, layout_rng, sample_index)

    return grid
