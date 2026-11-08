"""Input sampler for top-row seeds that paint down-right diagonal rays.

The canonical demonstrations use a different color for every seed, so they are
also compatible with the shortcut "paint only the first seed of each color".
This sampler deliberately places repeated-color seeds in two of every three
consecutive draws, while retaining a canonical-profile distinct-color draw.
The unchanged Racket program remains the label authority.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5d13a2fe59fc"
TASK_ID = GENERATOR_ID
RULE_HASH = "ba0a11187d3c"
VERSION = "2.0.0"

SUMMARY = (
    "Place 2..5 colored seeds in the top row of a 5..10 by 7..12 grid. "
    "Each seed paints its own down-right diagonal ray; scheduled repeated-color "
    "seeds refute the canonical-only first-seed-per-color shortcut."
)

INVARIANTS = [
    "background is 0 and every nonzero input cell is a top-row seed",
    "there are 2..5 seeds in distinct columns",
    "colors are integers 1..9; repeated seed colors are lawful",
    "every three consecutive draws contain at least two repeated-color witnesses",
    "each seed paints a down-right ray independently, even when another seed has the same color",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical/broad 5..10", "valid": "5..10"},
    "grid_w": {"type": "int", "default": "scheduled canonical/broad 7..12", "valid": "7..12"},
    "seeds": {"type": "int", "default": "scheduled 2..5", "valid": "2..5"},
    "color_pattern": {
        "type": "str",
        "default": "two repeat profiles then one distinct canonical profile",
        "valid": "distinct|repeat",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("repeat_left", "repeat_right", "canonical_distinct")

_INT_BOUNDS = {
    "grid_h": (5, 10),
    "grid_w": (7, 12),
    "seeds": (2, 5),
}
_COLOR_PATTERNS = ("distinct", "repeat")
_CANONICAL_ANCHORS = {
    "easy": ((5, 7, 2), (6, 8, 3)),
    "medium": ((6, 8, 3), (7, 9, 2)),
    "hard": ((7, 9, 2), (8, 10, 3)),
    None: ((5, 7, 2), (6, 8, 3), (7, 9, 2), (8, 10, 3)),
}
_BROAD_CHOICES = {
    "easy": {
        "grid_h": (5, 5, 6),
        "grid_w": (7, 8, 8),
        "seeds": (2, 3, 3),
    },
    "medium": {
        "grid_h": (6, 7, 8),
        "grid_w": (8, 9, 10),
        "seeds": (3, 3, 4),
    },
    "hard": {
        "grid_h": (8, 9, 10),
        "grid_w": (10, 11, 12),
        "seeds": (3, 4, 5),
    },
    None: {
        "grid_h": tuple(range(5, 11)),
        "grid_w": tuple(range(7, 13)),
        "seeds": tuple(range(2, 6)),
    },
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic three-slot curriculum profile."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_BOUNDS:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer (not bool)")
            lo, hi = _INT_BOUNDS[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name} must be in {lo}..{hi}")
        elif name == "color_pattern":
            if type(value) is not str:
                raise TypeError("color_pattern must be a string")
            if value not in _COLOR_PATTERNS:
                raise ValueError(f"color_pattern must be one of {_COLOR_PATTERNS}")


def _draw_scheduled_int(ctx, label, scheduled):
    lo, hi = _INT_BOUNDS[label]
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    # A singleton keyed draw records the realized axis without pretending that
    # the schedule itself was random. Exact overrides still use the full domain.
    return ctx.draw_choice(label, (scheduled,))


def _draw_scheduled_choice(ctx, label, scheduled, options):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_defaults(ctx, profile):
    band = ctx.difficulty if ctx.difficulty in ("easy", "medium", "hard") else None
    if profile == "canonical_distinct":
        anchors = _CANONICAL_ANCHORS[band]
        return ctx.draw_rng("canonical_anchor").choice(anchors)
    choices = _BROAD_CHOICES[band]
    return tuple(ctx.draw_rng(f"scheduled_{name}").choice(choices[name]) for name in ("grid_h", "grid_w", "seeds"))


def _seed_columns(width, count, profile, rng):
    if profile == "repeat_left":
        columns = [0] + rng.sample(range(1, width), count - 1)
    elif profile == "repeat_right":
        columns = [width - 1] + rng.sample(range(width - 1), count - 1)
    else:
        columns = rng.sample(range(width), count)
    return sorted(columns)


def _seed_colors(count, pattern, rng):
    if pattern == "distinct":
        return rng.sample(range(1, 10), count)
    unique = rng.sample(range(1, 10), count - 1)
    duplicate = unique[0]
    # The caller assigns the first and last entries to the extreme selected
    # columns, making the repeated-color counterexample visually separated.
    return [duplicate, *unique[1:], duplicate]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_seeds = _scheduled_defaults(ctx, profile)
    height = _draw_scheduled_int(ctx, "grid_h", default_h)
    width = _draw_scheduled_int(ctx, "grid_w", default_w)
    seed_count = _draw_scheduled_int(ctx, "seeds", default_seeds)
    default_pattern = "distinct" if profile == "canonical_distinct" else "repeat"
    color_pattern = _draw_scheduled_choice(ctx, "color_pattern", default_pattern, _COLOR_PATTERNS)

    grid = full_grid(height, width, 0)
    columns = _seed_columns(width, seed_count, profile, ctx.draw_rng("seed_columns"))
    colors = _seed_colors(seed_count, color_pattern, ctx.draw_rng("seed_colors"))
    for column, color in zip(columns, colors):
        grid[0][column] = color
    return grid


def _validation_errors(grid):
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) for row in grid) or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors = []
    height = len(grid)
    if not 5 <= height <= 10:
        errors.append(f"grid height must be 5..10, got {height}")
    if not 7 <= width <= 12:
        errors.append(f"grid width must be 7..12, got {width}")

    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({row_index},{col_index})")
                return errors
            if row_index > 0 and value != 0:
                errors.append(f"nonzero cell below top row at ({row_index},{col_index})")
                return errors

    seeds = [value for value in grid[0] if value != 0]
    if not 2 <= len(seeds) <= 5:
        errors.append(f"top row must contain 2..5 seeds, got {len(seeds)}")
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete intended input domain used by this generator."""
    return _validation_errors(grid)


def strict_canonical_like(grid):
    """Semantic-gate domain hook; repeated colors are intentionally lawful."""
    return _validation_errors(grid)


def observe_overrides(grid):
    errors = _validation_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    colors = [value for value in grid[0] if value]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "seeds": len(colors),
        "color_pattern": "repeat" if len(set(colors)) < len(colors) else "distinct",
    }


def rule_mirror(grid):
    """Pure diagnostic mirror of the canonical rule; Racket remains authority."""
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for start_col, color in enumerate(grid[0]):
        if color == 0:
            continue
        row, col = 0, start_col
        while row < height and col < width:
            output[row][col] = color
            row += 1
            col += 1
    return output


def _first_seed_per_color(grid):
    """Wrong rule: ignore every seed after the first occurrence of its color."""
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    seen = set()
    for start_col, color in enumerate(grid[0]):
        if color == 0 or color in seen:
            continue
        seen.add(color)
        row, col = 0, start_col
        while row < height and col < width:
            output[row][col] = color
            row += 1
            col += 1
    return output


def _has_repeated_color_seeds(grid):
    if _validation_errors(grid):
        return False
    colors = [value for value in grid[0] if value]
    return len(colors) > len(set(colors))


SEMANTIC_WITNESSES = {"repeated_color_seeds": _has_repeated_color_seeds}
SEMANTIC_RIVALS = {"first_seed_per_color": _first_seed_per_color}
WITNESS_RIVALS = {"repeated_color_seeds": ("first_seed_per_color",)}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report a named rival that fits every demo but changes the query answer."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = _validation_errors(pair["input"])
        if errors:
            reasons.append(f"demo {index} invalid: {errors[0]}")
    query_errors = _validation_errors(query["input"])
    if query_errors:
        reasons.append(f"query invalid: {query_errors[0]}")
    if reasons:
        return reasons

    canonical_query = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        survives_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives_demos and rival(query["input"]) != canonical_query:
            reasons.append(f"named rival {name} fits every demonstration but changes the query")
    return reasons
