"""Generator for ARC task 6773b310 / a9c4475d7cda.

Two full color-8 rows and two full color-8 columns divide the input into
nine panels.  The output is a 3x3 mask: a panel is 1 exactly when it contains
at least two color-6 cells.

The public controls are deliberately small and exact.  Every generated lesson
contains count-1, count-2, and count-3 panels, so it distinguishes the true
``count >= 2`` rule from both ``count == 2`` and ``count > 0`` rivals.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a9c4475d7cda"
TASK_ID = GENERATOR_ID
RULE_HASH = "8cfb5cf9c2c4"
VERSION = "3.0.0"
SUMMARY = (
    "A 9x9..17x17 background-0 grid is split into a 3x3 array of panels by "
    "exactly two full color-8 rows and two full color-8 columns. Each panel "
    "contains a controlled number of color-6 cells. The output is a 3x3 "
    "binary mask whose entry is 1 iff the corresponding panel contains at "
    "least two color-6 cells. Every generated profile includes counts 1, 2, "
    "and 3 to teach the threshold rather than an exact-count shortcut."
)

INVARIANTS = [
    "grid dimensions are independently controllable from 9 through 17",
    "exactly two full color-8 divider rows and two full color-8 divider columns",
    "all nine panel row/column bands have size at least two",
    "only colors 0, 6, and 8 occur",
    "every generated count profile contains panel counts 1, 2, and 3",
]

COUNT_PROFILES = ("canonical_bridge", "balanced", "sparse", "dense")
_PROFILE_COUNTS = {
    "canonical_bridge": (1, 1, 1, 1, 1, 2, 2, 2, 3),
    "balanced": (0, 0, 1, 1, 2, 2, 2, 3, 3),
    "sparse": (0, 0, 0, 0, 1, 1, 1, 2, 3),
    "dense": (0, 1, 2, 2, 2, 3, 3, 3, 3),
}
_PROFILE_HISTOGRAMS = {
    name: Counter(counts) for name, counts in _PROFILE_COUNTS.items()
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted 9..17 with recurring canonical 11",
        "valid": "9..17",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted 9..17 with recurring canonical 11",
        "valid": "9..17",
    },
    "count_profile": {
        "type": "str",
        "default": "uniform semantic profile",
        "valid": "|".join(COUNT_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
LAWFUL_DEGENERATE_TEXTURES = ()
EXAMPLES_NEEDED = 1


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
            if not 9 <= value <= 17:
                raise ValueError(f"{name}={value} outside [9, 17]")
    if "count_profile" in overrides and overrides["count_profile"] is not None:
        value = overrides["count_profile"]
        if type(value) is not str:
            raise ValueError(
                f"count_profile must be a string, not {type(value).__name__}"
            )
        if value not in COUNT_PROFILES:
            raise ValueError(
                f"count_profile={value!r} not in {list(COUNT_PROFILES)}"
            )


def _dimension_options(*, core, difficulty):
    # Every documented value remains present in every band, so an override is
    # never clipped or made illegal by difficulty. Repetition changes only the
    # default sampling weights.
    options = list(range(9, 18))
    if core:
        return options + [11] * 100
    favored = {
        "easy": (9, 10, 11),
        "medium": (11, 12, 13),
        "hard": (15, 16, 17),
    }.get(difficulty, (10, 12, 14, 16))
    return options + list(favored) * 3


def _band_lengths(total, rng):
    """Choose three lengths >=2 summing to ``total - 2`` divider cells."""
    payload = total - 2
    choices = [
        (first, second, payload - first - second)
        for first in range(2, payload - 3)
        for second in range(2, payload - first - 1)
        if payload - first - second >= 2
    ]
    if not choices:
        raise ValueError(f"dimension {total} cannot hold three size-2 panels")
    return rng.choice(choices)


def _separators(lengths):
    first, second, _third = lengths
    return first, first + second + 1


def _bands(total, separators):
    first, second = separators
    return (
        (0, first),
        (first + 1, second),
        (second + 1, total),
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # A shared hidden profile produces recurring exact 11x11 examples while a
    # broad component retains shape diversity. Full domains remain in both.
    core = ctx.draw_choice(
        "curriculum_profile", ("canonical", "broad", "broad")
    ) == "canonical"
    height = ctx.draw_choice(
        "grid_h", _dimension_options(core=core, difficulty=difficulty)
    )
    width = ctx.draw_choice(
        "grid_w", _dimension_options(core=core, difficulty=difficulty)
    )
    profile = ctx.draw_choice("count_profile", COUNT_PROFILES)

    row_lengths = _band_lengths(height, ctx.draw_rng("row_bands"))
    col_lengths = _band_lengths(width, ctx.draw_rng("col_bands"))
    separator_rows = _separators(row_lengths)
    separator_cols = _separators(col_lengths)
    row_bands = _bands(height, separator_rows)
    col_bands = _bands(width, separator_cols)

    grid = full_grid(height, width, 0)
    for row in separator_rows:
        for col in range(width):
            grid[row][col] = 8
    for col in separator_cols:
        for row in range(height):
            grid[row][col] = 8

    panel_counts = list(_PROFILE_COUNTS[profile])
    ctx.draw_rng("panel_count_permutation").shuffle(panel_counts)
    position_rng = ctx.draw_rng("six_positions")
    for panel_index, count in enumerate(panel_counts):
        row_start, row_end = row_bands[panel_index // 3]
        col_start, col_end = col_bands[panel_index % 3]
        candidates = [
            (row, col)
            for row in range(row_start, row_end)
            for col in range(col_start, col_end)
        ]
        for row, col in position_rng.sample(candidates, count):
            grid[row][col] = 6
    return grid


def _parse_grid(grid):
    """Return structural analysis or raise a diagnostic ``ValueError``."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int for row in grid for value in row):
        raise ValueError("all cells must be integer colors")
    bad_colors = sorted({value for row in grid for value in row if value not in (0, 6, 8)})
    if bad_colors:
        raise ValueError(f"unexpected colors outside 0/6/8: {bad_colors}")

    height = len(grid)
    if not 9 <= height <= 17 or not 9 <= width <= 17:
        raise ValueError(
            f"grid dimensions must each be in [9, 17], got {height}x{width}"
        )
    separator_rows = [
        row for row in range(height) if all(value == 8 for value in grid[row])
    ]
    separator_cols = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if len(separator_rows) != 2:
        raise ValueError(
            "expected exactly 2 full-width color-8 divider rows; "
            f"got {len(separator_rows)}"
        )
    if len(separator_cols) != 2:
        raise ValueError(
            "expected exactly 2 full-height color-8 divider columns; "
            f"got {len(separator_cols)}"
        )
    separator_row_set = set(separator_rows)
    separator_col_set = set(separator_cols)
    stray_eights = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8 and row not in separator_row_set and col not in separator_col_set
    ]
    if stray_eights:
        raise ValueError(f"color-8 cells outside divider lines: {stray_eights[:4]}")

    row_bands = _bands(height, tuple(separator_rows))
    col_bands = _bands(width, tuple(separator_cols))
    row_lengths = [end - start for start, end in row_bands]
    col_lengths = [end - start for start, end in col_bands]
    if min(row_lengths + col_lengths) < 2:
        raise ValueError(
            f"every panel band must have size at least 2; got rows {row_lengths}, "
            f"columns {col_lengths}"
        )
    counts = [
        [
            sum(
                grid[row][col] == 6
                for row in range(row_start, row_end)
                for col in range(col_start, col_end)
            )
            for col_start, col_end in col_bands
        ]
        for row_start, row_end in row_bands
    ]
    return {
        "height": height,
        "width": width,
        "separator_rows": tuple(separator_rows),
        "separator_cols": tuple(separator_cols),
        "counts": counts,
    }


def _flat_counts(analysis):
    return [value for row in analysis["counts"] for value in row]


def _recognized_profile(counts):
    histogram = Counter(counts)
    for name, expected in _PROFILE_HISTOGRAMS.items():
        if histogram == expected:
            return name
    return None


def self_check(grid, *, difficulty=None, meta=None):
    """Validate a canonical example or a generated semantic profile."""
    try:
        analysis = _parse_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    counts = _flat_counts(analysis)
    profile = _recognized_profile(counts)
    canonical_signature = set(counts) == {1, 2}
    if profile is None and not canonical_signature:
        return [
            "panel-count curriculum must be a declared profile or canonical "
            f"1/2-only support; got histogram {dict(sorted(Counter(counts).items()))}"
        ]
    return []


def strict_canonical_like(grid):
    """Return diagnostics for grids outside the selected lawful manifold."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every public exact axis from returned pixels."""
    analysis = _parse_grid(grid)
    counts = _flat_counts(analysis)
    profile = _recognized_profile(counts)
    if profile is None:
        raise ValueError(
            "panel-count histogram does not identify a declared count_profile"
        )
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "count_profile": profile,
    }


def rule_mirror(grid):
    """Independent Python mirror of the pinned Racket threshold rule."""
    counts = _parse_grid(grid)["counts"]
    return [[int(value >= 2) for value in row] for row in counts]


def _exactly_two(grid):
    """Canonical-fitting rival: incorrectly treats three as negative."""
    counts = _parse_grid(grid)["counts"]
    return [[int(value == 2) for value in row] for row in counts]


def _nonempty(grid):
    """Rival: incorrectly treats a single color-6 cell as positive."""
    counts = _parse_grid(grid)["counts"]
    return [[int(value > 0) for value in row] for row in counts]


def _has_count_three(grid):
    return 3 in _flat_counts(_parse_grid(grid))


def _has_count_one(grid):
    return 1 in _flat_counts(_parse_grid(grid))


SEMANTIC_WITNESSES = {
    "count_three": _has_count_three,
    "count_one": _has_count_one,
}
SEMANTIC_RIVALS = {
    "exactly_two": _exactly_two,
    "nonempty": _nonempty,
}
WITNESS_RIVALS = {
    "count_three": ["exactly_two"],
    "count_one": ["nonempty"],
}
CANONICAL_SHORTCUTS = {"exactly_two": _exactly_two}
LESSON_COMPETITORS = {
    "exactly_two": _exactly_two,
    "nonempty": _nonempty,
}
