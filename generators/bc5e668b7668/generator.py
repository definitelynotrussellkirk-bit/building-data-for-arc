"""Input generator for task bc5e668b7668: stable upward column packing.

The selected Racket authority packs each column's nonzero values into rows
0..k-1 while preserving their original top-to-bottom order.  This module emits
only inputs; outputs remain authority-derived.

The canonical examples leave one especially strong ambiguity: every canonical
column has at least two nonzero values, so a wrong rule that ignores singleton
columns fits every demonstration.  The four-slot schedule therefore includes a
singleton counterexample, plus an A-B-A order witness that rules out sorting the
values while packing them.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bc5e668b7668"
TASK_ID = GENERATOR_ID
RULE_HASH = "bd83e3df4565"
VERSION = "3.0.0"
SUMMARY = (
    "A 5..9 by 5..9 color grid uses background 0 and all foreground colors "
    "1..9. Every column contains one to three nonzero values. The rule packs "
    "each column's nonzero values upward into rows 0,1,... while preserving "
    "their original top-to-bottom order. A deterministic four-example teaching "
    "schedule includes dense canonical-scale scenes, a below-top singleton that "
    "must move, and an A-B-A column whose order must remain A-B-A."
)

INVARIANTS = [
    "background is 0 and every color 1..9 appears",
    "every column is active and contains one to three nonzero values",
    "at least one column contains two or three values",
    "at least one nonzero value moves when each column is packed upward",
    "top-to-bottom order within every column is semantically significant",
]

TEXTURES = ("canonical_dense", "singleton_witness", "interleaved_order")
HELPFUL_TEXTURES = TEXTURES
AXES = {
    "grid_h": {
        "type": "int",
        "default": "one of the canonical shape profiles",
        "valid": "5..9",
    },
    "grid_w": {
        "type": "int",
        "default": "one of the canonical shape profiles",
        "valid": "5..9",
    },
    "texture": {
        "type": "str",
        "default": "four-slot teaching schedule",
        "valid": "|".join(TEXTURES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# All default dimensions are literal canonical profiles.  Explicit overrides
# deliberately generalize the same grammar to 5..9 in either dimension.
_CANONICAL_SHAPES = ((5, 5), (6, 6), (6, 7), (7, 5))
_CANONICAL_PROFILES = {(h, w, 10) for h, w in _CANONICAL_SHAPES}

# Four consecutive samples expose all semantically important branches.  The
# repeated dense slot brackets the two counterexamples and makes a four-demo
# lesson independent of its starting residue.
SCHEDULE_PROFILES = (
    "canonical_dense",
    "singleton_witness",
    "interleaved_order",
    "canonical_dense",
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic curriculum branch for this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard', "
            f"not {difficulty!r}"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name in ("grid_h", "grid_w"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not 5 <= value <= 9:
            raise ValueError(f"{name} override {value} outside [5, 9]")

    if "texture" in overrides and overrides["texture"] is not None:
        value = overrides["texture"]
        if type(value) is not str:
            raise TypeError(
                f"texture must be a string, not {type(value).__name__}"
            )
        if value not in TEXTURES:
            raise ValueError(
                f"texture override {value!r} not in {list(TEXTURES)!r}"
            )


def _draw_exact_axis(ctx, name, default, domain):
    """Record a deterministic default while retaining the full override domain."""
    options = tuple(domain) if name in ctx.overrides else (default,)
    return ctx.draw_choice(name, options)


def _default_shape(ctx):
    # Shape is independent of the semantic schedule.  Difficulty selects
    # disjoint easy/hard canonical ranges so the public knob is observable,
    # while every default remains an exact canonical (height,width) profile.
    choices = {
        "easy": _CANONICAL_SHAPES[:2],
        "medium": _CANONICAL_SHAPES[1:3],
        "hard": _CANONICAL_SHAPES[2:],
    }.get(ctx.difficulty, _CANONICAL_SHAPES)
    return ctx.draw_rng("canonical_shape").choice(choices)


def _column_counts(width, texture, rng):
    counts = [2 + rng.randrange(2) for _ in range(width)]
    witness_column = rng.randrange(width)
    if texture == "singleton_witness":
        counts[witness_column] = 1
    elif texture == "interleaved_order":
        counts[witness_column] = 3
    return counts, witness_column


def _fill_sequences(counts, texture, witness_column, rng):
    """Assign all colors 1..9 while making texture recoverable from pixels."""
    sequences = [[None] * count for count in counts]
    slots = [
        (column, offset)
        for column, count in enumerate(counts)
        for offset in range(count)
    ]

    if texture == "interleaved_order":
        a, b = rng.sample(range(1, 10), 2)
        sequences[witness_column] = [a, b, a]
        free = [slot for slot in slots if slot[0] != witness_column]
        rng.shuffle(free)
        required = [color for color in range(1, 10) if color not in (a, b)]
        rng.shuffle(required)
        values = required + [b]
        values.extend(rng.choice(range(1, 10)) for _ in range(len(free) - len(values)))
        rng.shuffle(values)
        for (column, offset), value in zip(free, values):
            sequences[column][offset] = value
    else:
        rng.shuffle(slots)
        colors = list(range(1, 10))
        rng.shuffle(colors)
        values = colors + [
            rng.choice(range(1, 10)) for _ in range(len(slots) - len(colors))
        ]
        rng.shuffle(values)
        for (column, offset), value in zip(slots, values):
            sequences[column][offset] = value

    # Only interleaved_order may expose A-B-A as its identifying signature.
    if texture == "canonical_dense":
        for sequence in sequences:
            if len(sequence) == 3 and sequence[0] == sequence[2]:
                sequence[2] = 1 + (sequence[0] % 9)

    assert all(all(type(v) is int for v in sequence) for sequence in sequences)
    assert set(v for sequence in sequences for v in sequence) == set(range(1, 10))
    return sequences


def _rows_for_column(height, count, rng, *, force_below_top=False):
    if force_below_top:
        rows = sorted(rng.sample(range(1, height), count))
    else:
        rows = sorted(rng.sample(range(height), count))
    if rows == list(range(count)):
        # Refuse identity demonstrations: move the final item into a later gap.
        rows[-1] = next(r for r in range(height - 1, count - 1, -1) if r not in rows[:-1])
        rows.sort()
    return rows


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

    default_h, default_w = _default_shape(ctx)
    h = _draw_exact_axis(ctx, "grid_h", default_h, range(5, 10))
    w = _draw_exact_axis(ctx, "grid_w", default_w, range(5, 10))
    scheduled = schedule_profile(seed, sample_index, difficulty=difficulty)
    texture = _draw_exact_axis(ctx, "texture", scheduled, TEXTURES)

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    counts, witness_column = _column_counts(w, texture, layout_rng)
    sequences = _fill_sequences(counts, texture, witness_column, color_rng)

    grid = full_grid(h, w, 0)
    for column, sequence in enumerate(sequences):
        rows = _rows_for_column(
            h,
            len(sequence),
            layout_rng,
            force_below_top=(
                texture == "singleton_witness" and column == witness_column
            ),
        )
        for row, value in zip(rows, sequence):
            grid[row][column] = value
    return grid


def _column_values(grid, column):
    return [row[column] for row in grid if row[column] != 0]


def _pack_up(grid):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for column in range(w):
        for row, value in enumerate(_column_values(grid, column)):
            out[row][column] = value
    return out


def observe_overrides(grid):
    """Recover every exact axis from returned pixels, never RNG bookkeeping."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    values = [_column_values(grid, column) for column in range(width)]
    if any(len(sequence) == 1 for sequence in values):
        texture = "singleton_witness"
    elif any(
        len(sequence) == 3
        and sequence[0] == sequence[2]
        and sequence[0] != sequence[1]
        for sequence in values
    ):
        texture = "interleaved_order"
    else:
        texture = "canonical_dense"
    return {"grid_h": len(grid), "grid_w": width, "texture": texture}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors = []
    h, w = len(grid), width
    if not (5 <= h <= 9 and 5 <= w <= 9):
        errors.append(f"grid shape {(h, w)} outside the supported 5..9 range")

    cells = [value for row in grid for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in cells):
        errors.append("grid values must be integer colors 0..9 (booleans are invalid)")
        return errors
    palette = set(cells)
    if palette != set(range(10)):
        errors.append(
            f"expected the canonical full palette 0..9, got {sorted(palette)}"
        )

    counts = []
    for column in range(w):
        count = len(_column_values(grid, column))
        counts.append(count)
        if not 1 <= count <= 3:
            errors.append(
                f"column {column} has {count} nonzero values; expected 1..3"
            )
    if counts and max(counts) < 2:
        errors.append("at least one column must contain multiple ordered values")
    if not errors and _pack_up(grid) == [list(row) for row in grid]:
        errors.append("input is already top-packed, so the rule would be identity")
    return errors


def strict_canonical_like(grid):
    """Accept exact canonical profiles within the task's validated grammar."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
    if profile not in _CANONICAL_PROFILES:
        return [
            f"profile {profile} is lawful but outside canonical profiles "
            f"{sorted(_CANONICAL_PROFILES)}"
        ]
    return []


def _ignore_singletons(grid):
    """Plausible wrong rule: pack only columns containing at least two values."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for column in range(w):
        values = _column_values(grid, column)
        if len(values) == 1:
            for row in range(h):
                out[row][column] = grid[row][column]
        else:
            for row, value in enumerate(values):
                out[row][column] = value
    return out


def _sort_values(grid):
    """Wrong rule: sort colors numerically before placing them at the top."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for column in range(w):
        for row, value in enumerate(sorted(_column_values(grid, column))):
            out[row][column] = value
    return out


def _has_moving_singleton(grid):
    for column in range(len(grid[0])):
        rows = [row for row in range(len(grid)) if grid[row][column] != 0]
        if len(rows) == 1 and rows[0] != 0:
            return True
    return False


def _has_stable_nonmonotonic_order(grid):
    return any(
        (values := _column_values(grid, column)) != sorted(values)
        for column in range(len(grid[0]))
    )


SEMANTIC_WITNESSES = {
    "singleton_column": _has_moving_singleton,
    "stable_nonmonotonic_order": _has_stable_nonmonotonic_order,
}
SEMANTIC_RIVALS = {
    "ignore_singletons": _ignore_singletons,
    "sort_values": _sort_values,
}
WITNESS_RIVALS = {
    "singleton_column": ["ignore_singletons"],
    "stable_nonmonotonic_order": ["sort_values"],
}
CANONICAL_SHORTCUTS = {"ignore_singletons": _ignore_singletons}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
