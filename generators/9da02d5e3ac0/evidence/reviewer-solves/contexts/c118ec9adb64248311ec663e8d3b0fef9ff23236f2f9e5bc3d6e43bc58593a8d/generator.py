"""Generator for ARC task 9da02d5e3ac0.

The selected rule treats every row independently.  A color-5 cell is replaced
by the first value in its row that is not 5; other cells are preserved.  If a
row is entirely color 5, it is unchanged.

The sampler deliberately includes preserved zero texture, multiple separated
5-runs, later distractor values, variable-depth interior row keys, zero-valued
keys, and rows with different keys.  Those cases distinguish the selected rule
from shortcuts that were indistinguishable in the imported all-5-plus-one-color
sampler, including a fixed-column repair shortcut found during final review.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9da02d5e3ac0"
VERSION = "3.1.0"
TASK_ID = "9da02d5e3ac0"
RULE_HASH = "aab70f56593c"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SUMMARY = (
    "Rows contain color-5 cells plus ordinary 0/background and 2-4 signal "
    "colors.  In each row, every 5 is replaced by that row's first non-5 "
    "value; later zeros and colored distractors stay unchanged, and an "
    "all-5 row stays all 5.  Lessons include variable-depth interior keys, "
    "zero-valued keys, separated 5-runs, and different keys across rows so "
    "fixed-column, first/last/nearest, first-nonzero, global-color, and "
    "whole-row shortcuts fail."
)

INVARIANTS = [
    "rectangular 8..14 by 8..16 ARC-color grid",
    "input contains colors 0 and 5 plus 2..4 nonzero non-5 signal colors",
    "every signal color is the first non-5 value of at least one row",
    "at least two rows contain a 5 and a non-5 replacement key",
]

AXES = {
    "grid_h": {"type": "int", "default": "weighted 8..14", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "weighted 8..16", "valid": "8..16"},
    "n_key_colors": {
        "type": "int",
        "default": "weighted 2..4",
        "valid": "2..4",
    },
}

_SIGNAL_COLORS = tuple(color for color in range(1, 10) if color != 5)


def _validate_overrides(overrides) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (8, 14),
        "grid_w": (8, 16),
        "n_key_colors": (2, 4),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _weighted_int(ctx, name: str, lo: int, hi: int, *, anchors=(), favored=()) -> int:
    """Draw across the full override domain while retaining canonical anchors."""
    options = list(range(lo, hi + 1))
    options.extend(favored)
    for anchor in anchors:
        options.extend([anchor] * 10)
    return ctx.draw_choice(name, options)


def _band_layout(width: int, rng) -> list[tuple[int, int]]:
    """Return two or three separated, canonical-like vertical 5-bands."""
    n_bands = 2 if width <= 10 else rng.choice((2, 2, 3))
    widths = [2] * n_bands
    gaps = [1] * (n_bands - 1)

    # Columns 0/1 carry row keys and preserved texture.  Distribute every
    # remaining column among band widths, internal gaps, and a trailing gap.
    remaining = width - 2 - sum(widths) - sum(gaps)
    trailing = 0
    while remaining > 0:
        choices = [("width", index) for index in range(n_bands)]
        choices.extend(("gap", index) for index in range(len(gaps)))
        choices.append(("trailing", 0))
        kind, index = rng.choice(choices)
        if kind == "width":
            widths[index] += 1
        elif kind == "gap":
            gaps[index] += 1
        else:
            trailing += 1
        remaining -= 1

    bands = []
    column = 2
    for index, band_width in enumerate(widths):
        bands.append((column, column + band_width))
        column += band_width
        if index < len(gaps):
            column += gaps[index]
    assert column + trailing == width
    return bands


def _structured_grid(
    height: int,
    width: int,
    colors: tuple[int, ...],
    rng,
) -> list[list[int]]:
    """Build connected block morphology while retaining semantic witnesses."""
    grid = full_grid(height, width, 0)
    bands = _band_layout(width, rng)

    # Each band reaches the final bridge row, so the color-5 geometry consists
    # of large connected blocks rather than per-row pepper noise.  Later bands
    # may start lower to vary the silhouette without fragmenting it.
    for band_index, (left, right) in enumerate(bands):
        top = 0 if band_index == 0 else rng.randint(0, min(2, height - 5))
        for row in range(top, height - 1):
            for column in range(left, right):
                grid[row][column] = 5
    grid[-1] = [5] * width

    # Group row keys into vertical runs, as in the canonical examples.  Every
    # selected signal color is used as a genuine first-non-5 key.
    active_rows = list(range(1, height - 1))
    row_keys = {}
    for offset, row in enumerate(active_rows):
        color_index = min(
            len(colors) - 1,
            offset * len(colors) // len(active_rows),
        )
        row_keys[row] = colors[color_index]
        grid[row][0] = colors[color_index]

    # One interior row begins with a variable-length run of 5s before its key.
    # The depth varies with the sampled band width, so the earlier repair's
    # fixed "column 1 if leading 5, else column 0" shortcut cannot survive.
    interior_row = rng.choice(list(range(2, height - 2)))
    first_left, first_right = bands[0]
    key_column = rng.randrange(max(2, first_left), first_right)
    for column in range(key_column):
        grid[interior_row][column] = 5
    grid[interior_row][key_column] = row_keys[interior_row]

    # Row 0 keeps zero as its first non-5 key while carrying a later signal.
    # This distinguishes the selected first-non-5 rule from first-nonzero.
    grid[0][0] = 0
    grid[0][1] = colors[0]
    return grid

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

    if difficulty == "easy":
        favored_h, favored_w, favored_colors = (8, 9, 10), (8, 9, 10), (2,)
    elif difficulty == "hard":
        favored_h, favored_w, favored_colors = (12, 13, 14), (13, 14, 15, 16), (3, 4)
    else:
        favored_h = favored_w = favored_colors = ()

    # Every band retains frequent exact canonical profiles: 12x12 with a
    # four- or five-color input alphabet (2 or 3 signal colors plus 0 and 5).
    height = _weighted_int(ctx, "grid_h", 8, 14, anchors=(12,), favored=favored_h)
    width = _weighted_int(ctx, "grid_w", 8, 16, anchors=(12,), favored=favored_w)
    n_colors = _weighted_int(
        ctx,
        "n_key_colors",
        2,
        4,
        anchors=(2, 3),
        favored=favored_colors,
    )
    colors = ctx.draw_distinct_colors("key_colors", n=n_colors, exclude={0, 5})
    row_rng = ctx.draw_rng("row_contents")
    return _structured_grid(height, width, tuple(colors), row_rng)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the sampler's lawful manifold without raising."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have a nonempty first row"]

    height = len(grid)
    width = len(grid[0])
    problems: list[str] = []
    if not 8 <= height <= 14:
        problems.append(f"height {height} outside 8..14")
    if not 8 <= width <= 16:
        problems.append(f"width {width} outside 8..16")

    rectangular = True
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            problems.append(f"row {row_index} has invalid width")
            rectangular = False
            continue
        for column, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                problems.append(
                    f"cell ({row_index},{column}) is not an integer ARC color 0..9"
                )
    if not rectangular:
        return problems

    values = {value for row in grid for value in row}
    if 0 not in values:
        problems.append("grid needs preserved color-0 texture")
    if 5 not in values:
        problems.append("grid needs at least one color-5 target")

    signals = values - {0, 5}
    if not 2 <= len(signals) <= 4:
        problems.append(f"found {len(signals)} signal colors, expected 2..4")

    keyed_rows = 0
    keys_seen = set()
    textured_active = False
    for row in grid:
        first_non5 = next((value for value in row if value != 5), None)
        if 5 in row and first_non5 is not None:
            keyed_rows += 1
        if first_non5 in signals:
            keys_seen.add(first_non5)
            if 5 in row and 0 in row:
                textured_active = True

    if keyed_rows < 2:
        problems.append(f"only {keyed_rows} keyed row(s), expected at least 2")
    missing_keys = signals - keys_seen
    if missing_keys:
        problems.append(
            f"signal colors never used as first non-5 row keys: {sorted(missing_keys)}"
        )
    if not textured_active:
        problems.append("need an active signal-key row containing preserved zeros")
    return problems


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    problems = self_check(grid)
    if problems:
        raise ValueError(f"cannot observe invalid grid: {problems}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_key_colors": len(
            {value for row in grid for value in row if value not in (0, 5)}
        ),
    }


# ---------------------------------------------------------------------------
# Executable rival rules used only for semantic auditing and lesson checks.
# ---------------------------------------------------------------------------


def _replace_fives(grid, key_for_row):
    output = []
    for row in grid:
        key = key_for_row(row)
        output.append([
            key if value == 5 and key is not None and key != 5 else value
            for value in row
        ])
    return output


def _first_column(grid):
    return _replace_fives(grid, lambda row: row[0] if row else None)


def _fixed_key_position(grid):
    return _replace_fives(
        grid,
        lambda row: (
            row[1]
            if row and row[0] == 5 and len(row) > 1
            else (row[0] if row else None)
        ),
    )


def _first_nonzero(grid):
    return _replace_fives(
        grid,
        lambda row: next((value for value in row if value not in (0, 5)), None),
    )


def _last_non5(grid):
    return _replace_fives(
        grid,
        lambda row: next((value for value in reversed(row) if value != 5), None),
    )


def _global_first_signal(grid):
    key = next(
        (value for row in grid for value in row if value not in (0, 5)),
        None,
    )
    return _replace_fives(grid, lambda row: key)


def _nearest_non5(grid):
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        candidates = [column for column, value in enumerate(row) if value != 5]
        if not candidates:
            continue
        for column, value in enumerate(row):
            if value != 5:
                continue
            nearest = min(candidates, key=lambda other: (abs(other - column), other))
            output[row_index][column] = row[nearest]
    return output


def _fill_entire_row(grid):
    output = []
    for row in grid:
        key = next((value for value in row if value != 5), None)
        output.append([key] * len(row) if key is not None else list(row))
    return output


def _first_non5(row):
    return next((value for value in row if value != 5), None)


def _has_interior_key(grid):
    return any(row and row[0] == 5 and _first_non5(row) is not None for row in grid)


def _has_deep_interior_key(grid):
    for row in grid:
        key_index = next(
            (index for index, value in enumerate(row) if value != 5),
            None,
        )
        if key_index is not None and key_index >= 2:
            return True
    return False


def _has_zero_key_with_signal(grid):
    return any(
        _first_non5(row) == 0
        and 5 in row
        and any(value not in (0, 5) for value in row)
        for row in grid
    )


def _has_multiple_signal_row_keys(grid):
    keys = {
        _first_non5(row)
        for row in grid
        if 5 in row and _first_non5(row) not in (None, 0, 5)
    }
    return len(keys) >= 2


def _has_later_different_non5(grid):
    for row in grid:
        key = _first_non5(row)
        if key is None or 5 not in row:
            continue
        first_index = next(index for index, value in enumerate(row) if value != 5)
        if any(value != 5 and value != key for value in row[first_index + 1 :]):
            return True
    return False


def _has_preserved_non5_texture(grid):
    return any(
        5 in row and len({value for value in row if value != 5}) >= 2
        for row in grid
    )


SEMANTIC_WITNESSES = {
    "interior_key": _has_interior_key,
    "deep_interior_key": _has_deep_interior_key,
    "zero_is_a_key": _has_zero_key_with_signal,
    "row_specific_keys": _has_multiple_signal_row_keys,
    "later_non5_distractor": _has_later_different_non5,
    "preserved_non5_texture": _has_preserved_non5_texture,
}

SEMANTIC_RIVALS = {
    "first_column": _first_column,
    "fixed_key_position": _fixed_key_position,
    "first_nonzero": _first_nonzero,
    "last_non5": _last_non5,
    "global_first_signal": _global_first_signal,
    "nearest_non5": _nearest_non5,
    "fill_entire_row": _fill_entire_row,
}

WITNESS_RIVALS = {
    "interior_key": ["first_column"],
    "deep_interior_key": ["fixed_key_position"],
    "zero_is_a_key": ["first_nonzero"],
    "row_specific_keys": ["global_first_signal"],
    "later_non5_distractor": ["last_non5", "nearest_non5"],
    "preserved_non5_texture": ["fill_entire_row"],
}

# Both shortcuts reproduce every imported canonical pair, so only generated
# counterexamples can distinguish them from the selected rule.
CANONICAL_SHORTCUTS = {
    "first_column": _first_column,
    "fixed_key_position": _fixed_key_position,
    "first_nonzero": _first_nonzero,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(
                    f"declared rival {name!r} fits every demonstration but changes the query"
                )
    return reasons
