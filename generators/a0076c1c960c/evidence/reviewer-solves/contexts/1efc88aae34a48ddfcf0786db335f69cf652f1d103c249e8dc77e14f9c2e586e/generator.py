"""Input sampler for ``Bridge Only, Not the Endpoints`` (S18_E4).

The selected Racket authority takes every nonzero marker in each row, closes the
horizontal span, removes the original marker cells, and paints only the inserted
bridge cells color 8.  This module generates inputs only; ``_bridge_output`` is a
small independent-facing Python mirror used by focused tests and semantic rivals.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a0076c1c960c"
TASK_ID = GENERATOR_ID
RULE_HASH = "2205cb4e988b"
VERSION = "3.0.0"
SUMMARY = (
    "Canonical-size zero-background grids contain two to four active rows. "
    "Each active row has exactly two nonzero endpoint markers; the authoritative "
    "output drops those markers and paints only zero cells strictly between the "
    "row's leftmost and rightmost marker with color 8. Ordinary lessons mix the "
    "canonical color-2 palette with same-color and mixed-color endpoints, and "
    "include lawful adjacent pairs whose bridge is empty."
)

EXPECTED_OUTPUT_CODOMAIN = (0, 8)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

_SHAPES = ("8x10", "8x11", "9x9")
_SHAPE_DIMS = {"8x10": (8, 10), "8x11": (8, 11), "9x9": (9, 9)}
_PALETTE_MODES = ("canonical", "same_color", "mixed_color")
_ADJACENT_MODES = ("absent", "present")
_MARKER_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_NONCANONICAL_SAME_COLORS = (1, 3, 4, 5, 6, 7, 9)

# In every four consecutive default draws, two are mixed-color counterexamples.
# This makes both production lessons and every single-pair query rotation retain
# at least one demonstration that refutes the same-color-pairs shortcut.
_PALETTE_SCHEDULE = (
    "mixed_color",
    "canonical",
    "mixed_color",
    "same_color",
    "mixed_color",
    "canonical",
)
_ADJACENT_SCHEDULE = ("present", "absent", "present", "absent", "present", "present")

INVARIANTS = [
    "shape is one of the three canonical input profiles: 8x10, 8x11, or 9x9",
    "two to four rows contain exactly two nonzero markers each",
    "at most one active row is adjacent; every grid has at least one nonempty bridge",
    "non-adjacent endpoint distance is 2..6 and is exact under the span override",
    "input markers never use output color 8; authoritative outputs use only 0 and 8",
]

AXES = {
    "shape": {
        "type": "str",
        "default": "six-step canonical-profile schedule",
        "valid": "8x10|8x11|9x9",
    },
    "active_rows": {
        "type": "int",
        "default": "difficulty-aware schedule",
        "valid": "2..4",
    },
    "span": {
        "type": "int",
        "default": "difficulty-aware 2..6 schedule",
        "valid": "2..6",
    },
    "adjacent_mode": {
        "type": "str",
        "default": "scheduled absent/present",
        "valid": "absent|present",
    },
    "palette_mode": {
        "type": "str",
        "default": "mixed/canonical/mixed/same/mixed/canonical",
        "valid": "canonical|same_color|mixed_color",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _validate_generate_args(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name, value in overrides.items():
        if value is None:
            continue
        if name in ("active_rows", "span"):
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer (not bool)")
            lo, hi = (2, 4) if name == "active_rows" else (2, 6)
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        elif name == "shape":
            if type(value) is not str or value not in _SHAPES:
                raise ValueError(f"shape must be one of {_SHAPES}")
        elif name == "adjacent_mode":
            if type(value) is not str or value not in _ADJACENT_MODES:
                raise ValueError(f"adjacent_mode must be one of {_ADJACENT_MODES}")
        elif name == "palette_mode":
            if type(value) is not str or value not in _PALETTE_MODES:
                raise ValueError(f"palette_mode must be one of {_PALETTE_MODES}")


def _draw_choice(ctx, overrides, name, legal, default):
    options = legal if overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, options)


def _draw_int(ctx, overrides, name, lo, hi, default):
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _default_active_rows(sample_index, difficulty):
    band = difficulty or "medium"
    schedules = {
        "easy": (2, 3, 2, 3, 2, 3),
        "medium": (3, 2, 4, 3, 2, 4),
        "hard": (4, 3, 4, 3, 4, 3),
    }
    return schedules[band][sample_index % 6]


def _default_span(sample_index, difficulty):
    band = difficulty or "medium"
    schedules = {
        "easy": (2, 3, 2, 4, 3, 2),
        "medium": (3, 2, 4, 5, 6, 3),
        "hard": (5, 6, 4, 6, 5, 4),
    }
    return schedules[band][sample_index % 6]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a lawful input with exact, pixel-observable override controls."""
    _validate_generate_args(seed, sample_index, difficulty, overrides)
    clean = {name: value for name, value in overrides.items() if value is not None}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=clean,
    )

    shape_default = _SHAPES[(sample_index + {None: 1, "easy": 0, "medium": 1, "hard": 2}[difficulty]) % 3]
    shape = _draw_choice(ctx, clean, "shape", _SHAPES, shape_default)
    active_count = _draw_int(
        ctx,
        clean,
        "active_rows",
        2,
        4,
        _default_active_rows(sample_index, difficulty),
    )
    span = _draw_int(ctx, clean, "span", 2, 6, _default_span(sample_index, difficulty))
    adjacent_mode = _draw_choice(
        ctx,
        clean,
        "adjacent_mode",
        _ADJACENT_MODES,
        _ADJACENT_SCHEDULE[sample_index % 6],
    )
    palette_mode = _draw_choice(
        ctx,
        clean,
        "palette_mode",
        _PALETTE_MODES,
        _PALETTE_SCHEDULE[sample_index % 6],
    )

    height, width = _SHAPE_DIMS[shape]
    grid = full_grid(height, width, 0)
    layout_rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}")
    color_rng = ctx.draw_rng("marker_colors")
    rows = layout_rng.sample(range(height), active_count)
    adjacent_row = rows[0] if adjacent_mode == "present" else None

    if palette_mode == "canonical":
        color_pairs = [(2, 2)] * active_count
    elif palette_mode == "same_color":
        color = color_rng.choice(_NONCANONICAL_SAME_COLORS)
        color_pairs = [(color, color)] * active_count
    else:
        left, right = color_rng.sample(_MARKER_COLORS, 2)
        color_pairs = []
        for index in range(active_count):
            color_pairs.append((left, right) if index % 2 == 0 else (right, left))

    for index, row in enumerate(rows):
        row_span = 1 if row == adjacent_row else span
        left_col = layout_rng.randint(0, width - row_span - 1)
        right_col = left_col + row_span
        left_color, right_color = color_pairs[index]
        grid[row][left_col] = left_color
        grid[row][right_col] = right_color

    return grid


def _grid_errors(grid):
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a nonempty list"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (not bool)"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the sampler manifold while accepting all canonical inputs."""
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if (height, width) not in set(_SHAPE_DIMS.values()):
        errors.append(f"shape {height}x{width} is outside the canonical profile set")

    active = []
    for row_index, row in enumerate(grid):
        markers = [(column, value) for column, value in enumerate(row) if value != 0]
        if not markers:
            continue
        active.append((row_index, markers))
        if len(markers) != 2:
            errors.append(f"row {row_index} has {len(markers)} markers; expected exactly 2")
            continue
        if any(value == 8 for _column, value in markers):
            errors.append(f"row {row_index} uses reserved output color 8 as an input marker")
        span = markers[1][0] - markers[0][0]
        if not 1 <= span <= 6:
            errors.append(f"row {row_index} endpoint distance {span} outside [1, 6]")

    if not 2 <= len(active) <= 4:
        errors.append(f"active row count {len(active)} outside [2, 4]")

    complete_spans = [markers[1][0] - markers[0][0]
                      for _row, markers in active if len(markers) == 2]
    adjacent_count = sum(span == 1 for span in complete_spans)
    if adjacent_count > 1:
        errors.append(f"found {adjacent_count} adjacent rows; sampler permits at most 1")
    if complete_spans and all(span == 1 for span in complete_spans):
        errors.append("every active row is adjacent; at least one nonempty bridge is required")
    return errors


def strict_canonical_like(grid):
    """Return reasons when an input lies outside this reviewed task manifold."""
    return self_check(grid)


def _active_rows(grid):
    return [(r, [(c, value) for c, value in enumerate(row) if value != 0])
            for r, row in enumerate(grid) if any(value != 0 for value in row)]


def observe_overrides(grid):
    """Recover every exact advertised control solely from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))

    height, width = len(grid), len(grid[0])
    rows = _active_rows(grid)
    distances = [markers[1][0] - markers[0][0] for _r, markers in rows]
    nonadjacent = {distance for distance in distances if distance > 1}
    if len(nonadjacent) != 1:
        raise ValueError(f"generated grid does not encode one exact span: {sorted(nonadjacent)}")

    values = [value for _r, markers in rows for _c, value in markers]
    if set(values) == {2}:
        palette_mode = "canonical"
    elif all(markers[0][1] == markers[1][1] for _r, markers in rows):
        palette_mode = "same_color"
    elif all(markers[0][1] != markers[1][1] for _r, markers in rows):
        palette_mode = "mixed_color"
    else:
        raise ValueError("generated grid mixes incompatible palette modes")

    return {
        "shape": f"{height}x{width}",
        "active_rows": len(rows),
        "span": next(iter(nonadjacent)),
        "adjacent_mode": "present" if 1 in distances else "absent",
        "palette_mode": palette_mode,
    }


def _bridge_output(grid):
    """Mirror the selected rule: row closure minus every original marker."""
    output = [[0 for _value in row] for row in grid]
    for row_index, row in enumerate(grid):
        columns = [column for column, value in enumerate(row) if value != 0]
        if not columns:
            continue
        for column in range(min(columns), max(columns) + 1):
            if grid[row_index][column] == 0:
                output[row_index][column] = 8
    return output


def _same_color_pairs_only(grid):
    """Plausible rival: bridge only rows whose two endpoints share a color."""
    output = [[0 for _value in row] for row in grid]
    for row_index, row in enumerate(grid):
        markers = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(markers) != 2 or markers[0][1] != markers[1][1]:
            continue
        for column in range(markers[0][0] + 1, markers[1][0]):
            output[row_index][column] = 8
    return output


def _has_mixed_endpoint_colors(grid):
    for _row, markers in _active_rows(grid):
        if (len(markers) == 2 and markers[0][1] != markers[1][1]
                and markers[1][0] - markers[0][0] > 1):
            return True
    return False


SEMANTIC_WITNESSES = {"mixed_endpoint_colors": _has_mixed_endpoint_colors}
SEMANTIC_RIVALS = {"same_color_pairs_only": _same_color_pairs_only}
WITNESS_RIVALS = {"mixed_endpoint_colors": ["same_color_pairs_only"]}
CANONICAL_SHORTCUTS = {"same_color_pairs_only": _same_color_pairs_only}
LESSON_COMPETITORS = {"same_color_pairs_only": _same_color_pairs_only}


def lesson_identifiable(demos, query):
    """Report any declared competitor that demos fail to refute on this query."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if fits_demos and competitor(query["input"]) != query["output"]:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deliberate palette curriculum profile for census reporting."""
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return _PALETTE_SCHEDULE[sample_index % 6]


SCHEDULE_PROFILES = _PALETTE_MODES
