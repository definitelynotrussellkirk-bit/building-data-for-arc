"""Curriculum-safe generator for “keep only the first-found color”.

The selected rule scans the input in row-major order, takes the first nonzero
color as the key, and erases every other color.  Generated labels remain owned
by the canonical Racket authority; the Python transforms below are executable
review rivals and test mirrors only.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "341758fa9de1"
TASK_ID = GENERATOR_ID
RULE_HASH = "6e591d69c073"
VERSION = "2.1.0"

SUMMARY = (
    "Three to five sparse colors share a grid. The row-major first nonzero "
    "color is the key and survives; all distractor colors are erased. Exact "
    "canonical-size anchors and a twelve-slot schedule vary selector position, "
    "numeric rank, and frequency rank so those cues cannot replace scanning."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

INVARIANTS = [
    "background is literal ARC color 0",
    "there are 3..5 nonzero colors and every color occurs at least twice",
    "the row-major first nonzero key occurs in more than one location",
    "default scenes vary the selector position and put a later distractor in its row",
    "default schedules cross key numeric rank with least/middle/most frequency",
]

PALETTE_KINDS = ("cool", "warm", "varied")
KEY_FREQUENCIES = ("least", "middle", "most")
NUMERIC_RANKS = ("low", "middle", "high")
_NUMERIC_SCHEDULE = ("low", "middle", "high", "middle")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-weighted full domain",
        "valid": "5..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-weighted full domain",
        "valid": "5..18",
    },
    "n_colors": {
        "type": "int",
        "default": "canonical anchor or keyed choice",
        "valid": "3..5",
    },
    "palette_kind": {
        "type": "enum",
        "default": "keyed choice",
        "valid": ["cool", "warm", "varied"],
    },
    "key_frequency": {
        "type": "enum",
        "default": "period-3 semantic schedule",
        "valid": ["least", "middle", "most"],
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# The exact set of used colors makes both palette_kind and n_colors observable
# from pixels.  The selected key deliberately cycles through low, middle, and
# high numeric ranks so palette-order shortcuts are counterexampled.
_PALETTES = {
    "cool": {
        3: (1, 2, 3),
        4: (1, 2, 3, 4),
        5: (1, 2, 3, 4, 5),
    },
    "warm": {
        3: (7, 8, 9),
        4: (6, 7, 8, 9),
        5: (5, 6, 7, 8, 9),
    },
    "varied": {
        3: (1, 5, 9),
        4: (1, 4, 6, 9),
        5: (1, 3, 5, 7, 9),
    },
}
_PALETTE_LOOKUP = {
    frozenset(colors): kind
    for kind, by_count in _PALETTES.items()
    for colors in by_count.values()
}

_CANONICAL_SCHEDULE = (
    (5, 6, 3),
    (5, 5, 3),
    (5, 6, 4),
    None,
)
_CANONICAL_PROFILES = {
    (5, 6, 4),  # h, w, palette size including background
    (5, 5, 4),
    (5, 6, 5),
}
_DIFFICULTY_DIMENSIONS = {
    None: tuple(range(5, 19)),
    "easy": (5, 5, 5, 6, 6, 7, 8, 9),
    "medium": (7, 8, 9, 10, 11, 12, 13, 14),
    "hard": (10, 11, 12, 13, 14, 15, 16, 17, 18),
}
SCHEDULE_PROFILES = tuple(
    f"{KEY_FREQUENCIES[index % 3]}|{_NUMERIC_SCHEDULE[index % 4]}|position-{index % 4}"
    for index in range(12)
)


def _frequency_schedule(sample_index):
    return KEY_FREQUENCIES[sample_index % len(KEY_FREQUENCIES)]


def _numeric_schedule(sample_index):
    return _NUMERIC_SCHEDULE[sample_index % len(_NUMERIC_SCHEDULE)]


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the full period-12 frequency/numeric/position curriculum slot."""
    del seed
    if difficulty not in _DIFFICULTY_DIMENSIONS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not 5 <= value <= 18:
            raise ValueError(f"{name}={value} outside [5, 18]")

    value = overrides.get("n_colors")
    if value is not None:
        if type(value) is not int:
            raise TypeError(
                f"n_colors must be an integer, not {type(value).__name__}"
            )
        if not 3 <= value <= 5:
            raise ValueError(f"n_colors={value} outside [3, 5]")

    value = overrides.get("palette_kind")
    if value is not None:
        if type(value) is not str:
            raise TypeError(
                f"palette_kind must be a string, not {type(value).__name__}"
            )
        if value not in PALETTE_KINDS:
            raise ValueError(f"palette_kind must be one of {PALETTE_KINDS}")

    value = overrides.get("key_frequency")
    if value is not None:
        if type(value) is not str:
            raise TypeError(
                f"key_frequency must be a string, not {type(value).__name__}"
            )
        if value not in KEY_FREQUENCIES:
            raise ValueError(f"key_frequency must be one of {KEY_FREQUENCIES}")


def _draw_int_axis(ctx, name, lo, hi, default):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if isinstance(default, tuple):
        return ctx.draw_choice(name, default)
    return ctx.draw_choice(name, (default,))


def _draw_choice_axis(ctx, name, options, default=None):
    if ctx.overrides.get(name) is not None or default is None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _key_color(colors, profile):
    index = {
        "low": 0,
        "middle": len(colors) // 2,
        "high": len(colors) - 1,
    }[profile]
    return colors[index]


def _frequency_counts(colors, key, profile, rng):
    """Assign unique counts 2..N+1 with the key at the requested rank."""
    values = list(range(2, 2 + len(colors)))
    key_index = {
        "least": 0,
        "middle": len(values) // 2,
        "most": len(values) - 1,
    }[profile]
    key_count = values.pop(key_index)
    rng.shuffle(values)
    counts = {key: key_count}
    for color, count in zip((c for c in colors if c != key), values):
        counts[color] = count
    return counts


def _selector_position(h, w, occupied_cells, position_slot, rng):
    """Choose a varied row-major selector while leaving enough suffix cells."""
    last_for_capacity = h * w - occupied_cells
    last_before_final_row = (h - 1) * w - 2
    last_allowed = min(last_for_capacity, last_before_final_row)
    candidates = [
        flat
        for flat in range(1, last_allowed + 1)
        if flat % w != w - 1
    ]
    if not candidates or candidates[0] != 1:
        raise RuntimeError("grid too small for selector-position schedule")
    if position_slot == 0:
        flat = 1
    else:
        nonfixed = candidates[1:]
        if len(nonfixed) < 3:
            raise RuntimeError("grid too small for varied selector positions")
        start = (position_slot - 1) * len(nonfixed) // 3
        stop = position_slot * len(nonfixed) // 3
        bucket = nonfixed[start:stop]
        if not bucket:
            raise RuntimeError("empty selector-position schedule bucket")
        flat = bucket[rng.randrange(len(bucket))]
    return divmod(flat, w)


def _place_scene(h, w, colors, key, counts, position_slot, rng):
    """Place exact counts with varied selector and explicit semantic witnesses."""
    grid = full_grid(h, w, 0)
    distractors = [color for color in colors if color != key]
    rng.shuffle(distractors)
    boundary_color = distractors[0]

    first = _selector_position(h, w, sum(counts.values()), position_slot, rng)
    first_flat = first[0] * w + first[1]
    second_key = (h - 1, w - 2)
    first_row_decoy = (first[0], w - 1)
    last_decoy = (h - 1, w - 1)
    reserved = {
        first: key,
        second_key: key,
        first_row_decoy: boundary_color,
        last_decoy: boundary_color,
    }
    if len(reserved) != 4:
        raise RuntimeError("selector witnesses collided")
    for (row, col), color in reserved.items():
        grid[row][col] = color

    remaining = dict(counts)
    remaining[key] -= 2
    remaining[boundary_color] -= 2
    if any(value < 0 for value in remaining.values()):
        raise RuntimeError("frequency profile cannot satisfy semantic witnesses")

    free = [
        (row, col)
        for row in range(h)
        for col in range(w)
        if row * w + col > first_flat and (row, col) not in reserved
    ]

    # Keep the row-major selector as a one-cell key component. Earlier cells
    # remain background by construction; only right/down neighbors can be
    # placed later in row-major order.
    forbidden_for_key = {
        cell
        for cell in ((first[0], first[1] + 1), (first[0] + 1, first[1]))
        if 0 <= cell[0] < h and 0 <= cell[1] < w
    }
    key_candidates = [cell for cell in free if cell not in forbidden_for_key]
    rng.shuffle(key_candidates)
    chosen_key = key_candidates[: remaining[key]]
    if len(chosen_key) != remaining[key]:
        raise RuntimeError("grid too small for requested key count")
    for row, col in chosen_key:
        grid[row][col] = key
    chosen_key_set = set(chosen_key)
    free = [cell for cell in free if cell not in chosen_key_set]

    fill = []
    for color in distractors:
        fill.extend([color] * remaining[color])
    rng.shuffle(fill)
    rng.shuffle(free)
    if len(fill) > len(free):
        raise RuntimeError("grid too small for requested color counts")
    for (row, col), color in zip(free, fill):
        grid[row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTY_DIMENSIONS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(seed) is not int or type(sample_index) is not int:
        raise TypeError("seed and sample_index must be integers (not bool)")
    _validate_overrides(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor = _CANONICAL_SCHEDULE[sample_index % len(_CANONICAL_SCHEDULE)]
    if anchor is None:
        default_h = _DIFFICULTY_DIMENSIONS[difficulty]
        default_w = _DIFFICULTY_DIMENSIONS[difficulty]
        default_n = (3, 4, 5)
    else:
        default_h, default_w, default_n = anchor

    h = _draw_int_axis(ctx, "grid_h", 5, 18, default_h)
    w = _draw_int_axis(ctx, "grid_w", 5, 18, default_w)
    n_colors = _draw_int_axis(ctx, "n_colors", 3, 5, default_n)
    palette_kind = _draw_choice_axis(ctx, "palette_kind", PALETTE_KINDS)
    key_frequency = _draw_choice_axis(
        ctx,
        "key_frequency",
        KEY_FREQUENCIES,
        _frequency_schedule(sample_index),
    )
    key_numeric_rank = _numeric_schedule(sample_index)

    colors = _PALETTES[palette_kind][n_colors]
    key = _key_color(colors, key_numeric_rank)
    counts = _frequency_counts(
        colors, key, key_frequency, ctx.draw_rng("frequency_assignment")
    )
    grid = _place_scene(
        h,
        w,
        colors,
        key,
        counts,
        sample_index % 4,
        ctx.draw_rng("layout"),
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("generated invalid scene: " + "; ".join(errors))
    return grid


def _shape_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "expected a nonempty rectangular grid"
    return None


def _first_nonzero(grid):
    for row in grid:
        for value in row:
            if value != 0:
                return value
    return None


def _counts(grid):
    return Counter(value for row in grid for value in row if value != 0)


def self_check(grid, *, difficulty=None, meta=None):
    """Accept the public task manifold while rejecting vacuous/impostor scenes."""
    del meta
    errors = []
    if difficulty not in _DIFFICULTY_DIMENSIONS:
        errors.append("difficulty must be None, 'easy', 'medium', or 'hard'")
    shape = _shape_error(grid)
    if shape:
        return [shape, *errors]

    h, w = len(grid), len(grid[0])
    if not (5 <= h <= 18 and 5 <= w <= 18):
        errors.append("grid dimensions must each be in [5, 18]")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be literal ARC color integers 0..9")
        return errors

    counts = _counts(grid)
    if not 3 <= len(counts) <= 5:
        errors.append("expected 3..5 distinct nonzero colors")
        return errors
    too_small = sorted(color for color, count in counts.items() if count < 2)
    if too_small:
        errors.append(f"every nonzero color must occur at least twice: {too_small}")
    key = _first_nonzero(grid)
    if key is None or counts.get(key, 0) < 2:
        errors.append("row-major first nonzero key must occur at least twice")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is outside the public canonical profiles"]
    return []


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    colors = frozenset(_counts(grid))
    palette_kind = _PALETTE_LOOKUP.get(colors)
    if palette_kind is None:
        raise ValueError(f"used color set {sorted(colors)} is not a declared palette")

    counts = _counts(grid)
    if len(set(counts.values())) != len(counts):
        raise ValueError("generated exact-control scenes require unique color counts")
    key = _first_nonzero(grid)
    ordered = sorted(counts.values())
    rank = ordered.index(counts[key])
    if rank == 0:
        key_frequency = "least"
    elif rank == len(ordered) - 1:
        key_frequency = "most"
    else:
        key_frequency = "middle"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_colors": len(colors),
        "palette_kind": palette_kind,
        "key_frequency": key_frequency,
    }


def _keep_color(grid, color):
    if color in (None, 0):
        return full_grid(len(grid), len(grid[0]), 0)
    return [[value if value == color else 0 for value in row] for row in grid]


def rule_mirror(grid):
    """Review/test mirror only; production labels remain Racket-derived."""
    key = _first_nonzero(grid)
    if key is None:
        return [list(row) for row in grid]
    return _keep_color(grid, key)


def _rival_most_frequent(grid):
    counts = _counts(grid)
    if not counts:
        return [list(row) for row in grid]
    color = max(counts, key=lambda value: (counts[value], -value))
    return _keep_color(grid, color)


def _rival_least_frequent(grid):
    counts = _counts(grid)
    if not counts:
        return [list(row) for row in grid]
    color = min(counts, key=lambda value: (counts[value], value))
    return _keep_color(grid, color)


def _rival_middle_frequency(grid):
    counts = _counts(grid)
    if not counts:
        return [list(row) for row in grid]
    ordered = sorted(counts, key=lambda value: (counts[value], value))
    return _keep_color(grid, ordered[len(ordered) // 2])


def _rival_lowest_color(grid):
    counts = _counts(grid)
    return _keep_color(grid, min(counts) if counts else None)


def _rival_middle_numeric_color(grid):
    counts = _counts(grid)
    ordered = sorted(counts)
    return _keep_color(grid, ordered[len(ordered) // 2] if ordered else None)


def _rival_highest_color(grid):
    counts = _counts(grid)
    return _keep_color(grid, max(counts) if counts else None)


def _rival_fixed_position_0_1(grid):
    color = grid[0][1] if grid and len(grid[0]) > 1 else None
    return _keep_color(grid, color)


def _rival_top_left_color(grid):
    return _keep_color(grid, grid[0][0])


def _rival_rightmost_first_row_color(grid):
    for row in grid:
        for value in reversed(row):
            if value != 0:
                return _keep_color(grid, value)
    return [list(row) for row in grid]


def _rival_last_nonzero_color(grid):
    color = next(
        (value for row in reversed(grid) for value in reversed(row) if value != 0),
        None,
    )
    return _keep_color(grid, color)


def _rival_first_cell_only(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 0:
                output[row_index][col_index] = value
                return output
    return output


def _rival_identity(grid):
    return [list(row) for row in grid]


def _frequency_profile(grid):
    try:
        return observe_overrides(grid)["key_frequency"]
    except (TypeError, ValueError):
        return None


def _numeric_profile(grid):
    counts = _counts(grid)
    key = _first_nonzero(grid)
    if not counts or key is None:
        return None
    ordered = sorted(counts)
    rank = ordered.index(key)
    if rank == 0:
        return "low"
    if rank == len(ordered) - 1:
        return "high"
    return "middle"


def _first_nonzero_position(grid):
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value != 0:
                return row_index, col_index
    return None


def _witness_top_left_background(grid):
    return bool(grid and grid[0] and grid[0][0] == 0 and _first_nonzero(grid))


def _witness_first_row_decoy(grid):
    for row in grid:
        nonzero = [value for value in row if value != 0]
        if nonzero:
            return len(nonzero) >= 2 and nonzero[0] != nonzero[-1]
    return False


def _witness_key_not_most(grid):
    counts = _counts(grid)
    key = _first_nonzero(grid)
    return bool(counts and key is not None and counts[key] < max(counts.values()))


def _witness_key_least(grid):
    return _frequency_profile(grid) == "least"


def _witness_key_middle(grid):
    return _frequency_profile(grid) == "middle"


def _witness_key_most(grid):
    return _frequency_profile(grid) == "most"


def _witness_selector_not_second_cell(grid):
    position = _first_nonzero_position(grid)
    return position is not None and position != (0, 1)


def _witness_numeric_low(grid):
    return _numeric_profile(grid) == "low"


def _witness_numeric_middle(grid):
    return _numeric_profile(grid) == "middle"


def _witness_numeric_high(grid):
    return _numeric_profile(grid) == "high"


SEMANTIC_RIVALS = {
    "most_frequent": _rival_most_frequent,
    "least_frequent": _rival_least_frequent,
    "middle_frequency": _rival_middle_frequency,
    "lowest_color": _rival_lowest_color,
    "middle_numeric_color": _rival_middle_numeric_color,
    "highest_color": _rival_highest_color,
    "fixed_position_0_1": _rival_fixed_position_0_1,
    "top_left_color": _rival_top_left_color,
    "rightmost_first_row_color": _rival_rightmost_first_row_color,
    "last_nonzero_color": _rival_last_nonzero_color,
    "first_cell_only": _rival_first_cell_only,
    "identity": _rival_identity,
}
CANONICAL_SHORTCUTS = {
    "most_frequent": _rival_most_frequent,
    "top_left_color": _rival_top_left_color,
    "rightmost_first_row_color": _rival_rightmost_first_row_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "top_left_background": _witness_top_left_background,
    "first_row_decoy": _witness_first_row_decoy,
    "key_not_most": _witness_key_not_most,
    "key_least_profile": _witness_key_least,
    "key_middle_profile": _witness_key_middle,
    "key_most_profile": _witness_key_most,
    "selector_not_second_cell": _witness_selector_not_second_cell,
    "key_numeric_low": _witness_numeric_low,
    "key_numeric_middle": _witness_numeric_middle,
    "key_numeric_high": _witness_numeric_high,
}
WITNESS_RIVALS = {
    "top_left_background": ["top_left_color"],
    "first_row_decoy": ["rightmost_first_row_color"],
    "key_not_most": ["most_frequent"],
    "key_least_profile": ["most_frequent"],
    "key_middle_profile": ["most_frequent"],
    "key_most_profile": ["top_left_color"],
    "selector_not_second_cell": ["fixed_position_0_1"],
    "key_numeric_low": ["middle_numeric_color", "highest_color"],
    "key_numeric_middle": ["lowest_color", "highest_color"],
    "key_numeric_high": ["lowest_color", "middle_numeric_color"],
}


def lesson_identifiable(demos, query):
    """Reject only a rival that fits every demo but changes the held-out label."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes query")
    return reasons
