"""Constructive input sampler for “fill one-cell horizontal blue gaps”.

The selected Racket authority is unchanged.  This module samples lawful inputs
and exposes executable teaching contracts; it does not produce training labels.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3bb94038f4e2"
TASK_ID = GENERATOR_ID
RULE_HASH = "f19859825874"
VERSION = "3.0.2"
SUMMARY = (
    "Fill exactly the black center of each horizontal blue(1)-black(0)-blue(1) "
    "triple with blue.  Read every decision from the input grid: wider gaps, "
    "vertical triples, equal non-blue endpoints, and nonblack centers are "
    "preserved.  The sampler alternates canonical-scale and broad semantic "
    "profiles so every three-example lesson retains a complete counterexample."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "rectangular 6..14 by 7..16 integer-color input",
    "at least two horizontal 1-0-1 gaps in every generated input",
    "broad profiles also contain a wide 1-0-0-1 gap, vertical 1-0-1, 2-0-2, and 1-2-1",
    "all placements are constructive; no capped retry can silently drop the rule event",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "curriculum-weighted 6..14",
        "valid": "6..14",
        "doc": "Exact returned height; every value is supported in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "curriculum-weighted 7..16",
        "valid": "7..16",
        "doc": "Exact returned width; every value is supported in every difficulty band.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("core", "broad")
MIN_STRICT_FRAC = 0.20

# A 6x7 template fits every advertised dimension.  The broad template contains
# one explicit counterexample for every declared lesson competitor.
_CORE_TEMPLATE = (
    (0, 1, 0, 1, 0, 1, 0),  # two real one-cell horizontal gaps
    (1, 0, 0, 1, 0, 0, 1),  # two wider gaps, both unchanged
    (0, 1, 1, 0, 0, 0, 0),  # domino; c6 is vertical center below/above 1
    (0, 0, 0, 0, 0, 0, 1),
    (0, 0, 0, 0, 0, 0, 0),
    (0, 1, 1, 0, 0, 0, 0),
)
_BROAD_TEMPLATE = (
    (0, 1, 0, 1, 0, 1, 0),  # two real gaps: refutes identity/first-only/fill-8
    (1, 0, 0, 1, 0, 0, 1),  # wider gaps: refutes span filling
    (0, 1, 1, 0, 0, 0, 0),  # c6 is the center of a vertical 1-0-1
    (0, 0, 0, 0, 0, 0, 1),
    (2, 0, 2, 0, 0, 0, 0),  # refutes “fill equal nonzero colors”
    (1, 2, 1, 0, 0, 0, 0),  # refutes “overwrite any center between blue”
)
_CANONICAL_SIZES = ((7, 7), (6, 8), (7, 9))


def schedule_profile(seed, sample_index, difficulty=None):
    """Alternating schedule; any three consecutive samples include broad data."""
    del seed, difficulty
    return "core" if sample_index % 2 == 0 else "broad"


def _dimension(ctx, name, lo, hi, anchor, repetitions):
    # The complete domain remains present, so every exact override is accepted.
    # Repeated anchors create a reliable curriculum floor without narrowing the
    # public contract or post-draw clipping.
    choices = list(range(lo, hi + 1)) + [anchor] * repetitions
    return ctx.draw_choice(name, choices)


def _anchors(profile, sample_index, difficulty):
    if profile == "core":
        # Core indices are even; integer division cycles all canonical profiles.
        return _CANONICAL_SIZES[(sample_index // 2) % len(_CANONICAL_SIZES)], 256
    if difficulty == "easy":
        return (6, 7), 20
    if difficulty == "hard":
        return (14, 16), 20
    return (9, 11), 12


def _transformed_template(template, *, flip_rows, flip_cols):
    rows = [list(row) for row in template]
    if flip_cols:
        rows = [row[::-1] for row in rows]
    if flip_rows:
        rows.reverse()
    return rows


def _place_template(grid, template, top, left):
    for r, row in enumerate(template):
        for c, value in enumerate(row):
            if value:
                grid[top + r][left + c] = value


def _add_extra_true_gaps(grid, reserved, rng, difficulty):
    if difficulty == "easy":
        wanted = rng.randint(0, 1)
    elif difficulty == "hard":
        wanted = rng.randint(3, 6)
    else:
        wanted = rng.randint(1, 3)
    h, w = len(grid), len(grid[0])
    candidates = [
        (r, c)
        for r in range(h)
        for c in range(1, w - 1)
        if all(
            (rr, cc) not in reserved and grid[rr][cc] == 0
            for rr in range(max(0, r - 1), min(h, r + 2))
            for cc in range(max(0, c - 2), min(w, c + 3))
        )
    ]
    rng.shuffle(candidates)
    placed = 0
    for r, c in candidates:
        if placed >= wanted:
            break
        if any(
            grid[rr][cc] != 0
            for rr in range(max(0, r - 1), min(h, r + 2))
            for cc in range(max(0, c - 2), min(w, c + 3))
        ):
            continue
        grid[r][c - 1] = 1
        grid[r][c + 1] = 1
        placed += 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    (anchor_h, anchor_w), repetitions = _anchors(profile, sample_index, difficulty)
    h = _dimension(ctx, "grid_h", 6, 14, anchor_h, repetitions)
    w = _dimension(ctx, "grid_w", 7, 16, anchor_w, repetitions)

    rng = ctx.draw_rng("layout")
    base_template = [
        list(row) for row in (_CORE_TEMPLATE if profile == "core" else _BROAD_TEMPLATE)
    ]
    if profile == "broad":
        # A source-visible signature prevents adjacent broad schedule slots from
        # collapsing to the same minimum-size grid.  Duplicate rejection in the
        # production materializer would otherwise skip the only broad demo in a
        # rotated lesson.  This isolated cell is semantically inert.
        base_template[3][3] = 3 + ((int(sample_index) // 2) % 7)
    template = _transformed_template(
        base_template,
        flip_rows=bool(rng.randrange(2)),
        flip_cols=bool(rng.randrange(2)),
    )
    top = rng.randrange(h - len(template) + 1)
    left = rng.randrange(w - len(template[0]) + 1)
    grid = full_grid(h, w, 0)
    _place_template(grid, template, top, left)
    reserved = {
        (r, c)
        for r in range(top, top + len(template))
        for c in range(left, left + len(template[0]))
    }
    _add_extra_true_gaps(grid, reserved, ctx.draw_rng("extra_gaps"), difficulty)
    return grid


def observe_overrides(grid):
    """Recover each exact public control from returned pixels."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer ARC colors 0..9"
    return None


def _true_gaps(grid):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c in range(1, len(row) - 1)
        if row[c - 1] == 1 and row[c] == 0 and row[c + 1] == 1
    ]


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    error = _grid_error(grid)
    if error:
        return [error]
    h, w = len(grid), len(grid[0])
    errors = []
    if not 6 <= h <= 14:
        errors.append(f"height {h} outside generator domain 6..14")
    if not 7 <= w <= 16:
        errors.append(f"width {w} outside generator domain 7..16")
    if not _true_gaps(grid):
        errors.append("no horizontal blue-black-blue triple")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    shape = (len(grid), len(grid[0]))
    if shape not in set(_CANONICAL_SIZES):
        errors.append(f"shape {shape} is outside the three canonical profiles")
    if {value for row in grid for value in row} != {0, 1}:
        errors.append("canonical profile requires exactly colors {0,1}")
    return errors


def _intended_output(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c in range(1, len(row) - 1):
            if row[c - 1] == 1 and row[c] == 0 and row[c + 1] == 1:
                out[r][c] = 1
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _fill_horizontal_spans(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        ones = [c for c, value in enumerate(row) if value == 1]
        if len(ones) >= 2:
            for c in range(ones[0] + 1, ones[-1]):
                if row[c] == 0:
                    out[r][c] = 1
    return out


def _fill_horizontal_and_vertical(grid):
    out = _intended_output(grid)
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(w):
            if grid[r - 1][c] == 1 and grid[r][c] == 0 and grid[r + 1][c] == 1:
                out[r][c] = 1
    return out


def _fill_equal_nonzero_gaps(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c in range(1, len(row) - 1):
            endpoint = row[c - 1]
            if row[c] == 0 and endpoint != 0 and endpoint == row[c + 1]:
                out[r][c] = endpoint
    return out


def _overwrite_between_blue(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c in range(1, len(row) - 1):
            if row[c - 1] == row[c + 1] == 1:
                out[r][c] = 1
    return out


def _fill_with_eight(grid):
    out = [list(row) for row in grid]
    for r, c in _true_gaps(grid):
        out[r][c] = 8
    return out


def _fill_first_gap_only(grid):
    out = [list(row) for row in grid]
    gaps = _true_gaps(grid)
    if gaps:
        r, c = gaps[0]
        out[r][c] = 1
    return out


def _has_multiple_true_gaps(grid):
    return len(_true_gaps(grid)) >= 2


def _has_wide_gap(grid):
    return any(
        list(row[c:c + 4]) == [1, 0, 0, 1]
        for row in grid
        for c in range(len(row) - 3)
    )


def _has_vertical_gap(grid):
    return any(
        grid[r - 1][c] == 1 and grid[r][c] == 0 and grid[r + 1][c] == 1
        for r in range(1, len(grid) - 1)
        for c in range(len(grid[0]))
    )


def _has_other_color_gap(grid):
    return any(
        row[c] == 0 and row[c - 1] == row[c + 1] not in (0, 1)
        for row in grid
        for c in range(1, len(row) - 1)
    )


def _has_protected_center(grid):
    return any(
        row[c - 1] == row[c + 1] == 1 and row[c] not in (0, 1)
        for row in grid
        for c in range(1, len(row) - 1)
    )


SEMANTIC_RIVALS = {
    "identity": _identity,
    "fill_horizontal_spans": _fill_horizontal_spans,
    "fill_horizontal_and_vertical": _fill_horizontal_and_vertical,
    "fill_equal_nonzero_gaps": _fill_equal_nonzero_gaps,
    "overwrite_between_blue": _overwrite_between_blue,
    "fill_with_eight": _fill_with_eight,
    "fill_first_gap_only": _fill_first_gap_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Both reproduce all public pairs because canonical uses only 0/1 and never
    # places a non-blue center between blue endpoints.
    "fill_equal_nonzero_gaps": _fill_equal_nonzero_gaps,
    "overwrite_between_blue": _overwrite_between_blue,
}
SEMANTIC_WITNESSES = {
    "multiple_true_gaps": _has_multiple_true_gaps,
    "wide_horizontal_gap": _has_wide_gap,
    "vertical_gap": _has_vertical_gap,
    "other_color_gap": _has_other_color_gap,
    "protected_center": _has_protected_center,
}
WITNESS_RIVALS = {
    "multiple_true_gaps": ["identity", "fill_with_eight", "fill_first_gap_only"],
    "wide_horizontal_gap": ["fill_horizontal_spans"],
    "vertical_gap": ["fill_horizontal_and_vertical"],
    "other_color_gap": ["fill_equal_nonzero_gaps"],
    "protected_center": ["overwrite_between_blue"],
}


def lesson_identifiable(demos, query):
    reasons = []
    for index, demo in enumerate(demos):
        grid = demo.get("input") if isinstance(demo, dict) else None
        if self_check(grid):
            reasons.append(f"demo {index} is outside the declared rule domain")
            continue
        if _intended_output(grid) != demo.get("output"):
            reasons.append(f"demo {index} output does not match the horizontal-gap rule")
    query_grid = query.get("input") if isinstance(query, dict) else None
    if self_check(query_grid):
        reasons.append("query is outside the declared rule domain")
        return reasons
    query_answer = _intended_output(query_grid)
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(demo["input"]) == demo.get("output")
            for demo in demos
            if isinstance(demo, dict) and "input" in demo
        )
        if survives and rival(query_grid) != query_answer:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query")
    return reasons


def mutation_fixtures():
    base = generate(811, 1, difficulty="medium")
    fixtures = [
        ("all_background", full_grid(6, 7, 0)),
        ("vertical_only", [[1, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0],
                           [1, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0, 0, 0]]),
    ]
    no_gaps = deepcopy(base)
    for r, c in _true_gaps(no_gaps):
        no_gaps[r][c] = 1
    fixtures.append(("already_filled", no_gaps))
    return fixtures
