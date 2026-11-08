"""Input sampler for "Seed paints its whole column".

The unchanged Racket authority scans each column from top to bottom.  Empty
columns remain zero; every active column is filled with the color of its first
(topmost) nonzero seed.  Lower seeds are overwritten and therefore provide the
critical evidence that "exactly one seed" and "bottommost seed wins" are only
shortcuts that happen to fit all four canonical pairs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4842b1ca59e2"
TASK_ID = GENERATOR_ID
RULE_HASH = "977235c720d6"
VERSION = "3.0.0"
SUMMARY = (
    "Two to four active columns contain colored seeds.  At least one column "
    "contains a stack of two or three seeds with a different lower color.  "
    "The first nonzero seed in each column paints that entire column; empty "
    "columns remain zero."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and grids are 4..8 rows by 5..9 columns",
    "2..4 active columns have distinct topmost colors",
    "ordinary draws have 1..2 stacked columns of a common depth 2..3",
    "lower stack colors reuse another active top color and differ from the controlling top seed",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "one of the four canonical height/width/palette profiles",
        "valid": "4..8",
    },
    "grid_w": {
        "type": "int",
        "default": "one of the four canonical height/width/palette profiles",
        "valid": "5..9",
    },
    "active_columns": {
        "type": "int",
        "default": "2 or 3 from the selected canonical palette profile",
        "valid": "2..4",
    },
    "stacked_columns": {
        "type": "int",
        "default": "1 on easy; 1..2 otherwise",
        "valid": "1..2",
    },
    "stack_depth": {
        "type": "int",
        "default": "2 on easy; 2..3 otherwise",
        "valid": "2..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# (height, width, active nonzero colors).  Including background, these exactly
# match the public profiles (4,5,3), (4,6,3), (5,6,3), and (5,6,4).
_CANONICAL_PROFILES = (
    (4, 5, 2),
    (4, 6, 2),
    (5, 6, 2),
    (5, 6, 3),
)
_BANDS = {None, "easy", "medium", "hard"}
_BOUNDS = {
    "grid_h": (4, 8),
    "grid_w": (5, 9),
    "active_columns": (2, 4),
    "stacked_columns": (1, 2),
    "stack_depth": (2, 3),
}


def _validate_call(difficulty, overrides):
    if difficulty not in _BANDS:
        raise ValueError(f"unknown difficulty {difficulty!r}; expected easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None or type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool/None)")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")


def _axis(ctx, name, anchor):
    """Record an anchored default while retaining the full exact override domain."""
    lo, hi = _BOUNDS[name]
    if name in ctx.overrides:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (anchor,))


def _profile(ctx, difficulty):
    if difficulty == "easy":
        choices = (0, 0, 1, 2)
    elif difficulty == "hard":
        choices = (1, 2, 3, 3)
    else:
        choices = (0, 1, 2, 3)
    return _CANONICAL_PROFILES[ctx.draw_rng("canonical_profile").choice(choices)]


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

    profile_h, profile_w, profile_active = _profile(ctx, difficulty)
    h = _axis(ctx, "grid_h", profile_h)
    w = _axis(ctx, "grid_w", profile_w)
    active_count = _axis(ctx, "active_columns", profile_active)

    default_stacked = 1 if difficulty == "easy" else 1 + (sample_index % 2)
    stacked_count = _axis(ctx, "stacked_columns", default_stacked)
    default_depth = 2 if difficulty == "easy" else 2 + (sample_index % 2)
    stack_depth = _axis(ctx, "stack_depth", default_depth)

    # The declared domains make every joint override constructive.
    if stacked_count > active_count:
        raise ValueError("stacked_columns cannot exceed active_columns")
    if stack_depth > h - 1:
        raise ValueError("stack_depth requires at least one row above its bottom extent")

    columns = sorted(ctx.draw_rng("active_column_positions").sample(range(w), active_count))
    colors = ctx.draw_rng("top_seed_colors").sample(range(1, 10), active_count)
    stacked = set(ctx.draw_rng("stacked_column_choice").sample(columns, stacked_count))
    color_by_column = dict(zip(columns, colors))
    index_by_column = {column: index for index, column in enumerate(columns)}

    grid = full_grid(h, w, 0)
    row_rng = ctx.draw_rng("seed_rows")
    for column in columns:
        color = color_by_column[column]
        if column in stacked:
            # Start below row 0 so the scene also rejects a top-row-only cue.
            top = row_rng.randint(1, h - stack_depth)
            for offset in range(stack_depth):
                row = top + offset
                if offset == 0:
                    grid[row][column] = color
                else:
                    other = colors[(index_by_column[column] + 1) % active_count]
                    grid[row][column] = other
        else:
            grid[row_rng.randrange(h)][column] = color
    return grid


def _grid_shape_and_cells(grid):
    if not isinstance(grid, list) or not grid:
        return None, None, ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return None, None, ["grid must have a nonempty first row"]
    width = len(grid[0])
    problems = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != width:
            problems.append(f"row {row_index} has invalid width")
            continue
        for column, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                problems.append(f"cell ({row_index},{column}) is not an ARC color 0..9")
    return len(grid), width, problems


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept public single-seed scenes and the reviewed multi-seed extension."""
    h, w, problems = _grid_shape_and_cells(grid)
    if h is None or problems:
        return problems
    if not 4 <= h <= 8:
        problems.append(f"height {h} outside 4..8")
    if not 5 <= w <= 9:
        problems.append(f"width {w} outside 5..9")
    if problems:
        return problems

    active = []
    top_colors = []
    all_colors = set()
    for column in range(w):
        seeds = [(row, grid[row][column]) for row in range(h) if grid[row][column] != 0]
        if not seeds:
            continue
        active.append((column, seeds))
        top_colors.append(seeds[0][1])
        all_colors.update(value for _, value in seeds)
        if not 1 <= len(seeds) <= 3:
            problems.append(f"column {column} has {len(seeds)} seeds, expected 1..3")

    if not 2 <= len(active) <= 4:
        problems.append(f"found {len(active)} active columns, expected 2..4")
    if len(top_colors) != len(set(top_colors)):
        problems.append("topmost seed colors must be distinct across active columns")
    if all_colors and not all_colors.issubset(set(top_colors)):
        problems.append("lower seeds must reuse an active column's topmost color")
    return problems


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    problems = self_check(grid)
    if problems:
        raise ValueError(f"cannot observe invalid grid: {problems}")
    h, w = len(grid), len(grid[0])
    counts = [sum(grid[row][column] != 0 for row in range(h)) for column in range(w)]
    active = [count for count in counts if count]
    stacked = [count for count in active if count > 1]
    if not stacked:
        raise ValueError("generated exact-axis scene has no stacked column")
    if len(set(stacked)) != 1:
        raise ValueError(f"stacked columns have inconsistent depths: {stacked}")
    return {
        "grid_h": h,
        "grid_w": w,
        "active_columns": len(active),
        "stacked_columns": len(stacked),
        "stack_depth": stacked[0],
    }


def rule_mirror(grid):
    """Independent pure mirror of the unchanged authority for tests/probes."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for column in range(w):
        color = next((grid[row][column] for row in range(h) if grid[row][column] != 0), 0)
        for row in range(h):
            out[row][column] = color
    return out


def _single_seed_columns_only(grid):
    """Canonical-fitting shortcut: ignore every column with multiple seeds."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for column in range(w):
        seeds = [grid[row][column] for row in range(h) if grid[row][column] != 0]
        if len(seeds) == 1:
            for row in range(h):
                out[row][column] = seeds[0]
    return out


def _bottommost_seed(grid):
    """Canonical-fitting shortcut: let the last rather than first seed win."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for column in range(w):
        seeds = [grid[row][column] for row in range(h) if grid[row][column] != 0]
        if seeds:
            for row in range(h):
                out[row][column] = seeds[-1]
    return out


def _has_stacked_column(grid):
    return any(sum(row[column] != 0 for row in grid) >= 2 for column in range(len(grid[0])))


def _top_and_bottom_differ(grid):
    for column in range(len(grid[0])):
        seeds = [row[column] for row in grid if row[column] != 0]
        if len(seeds) >= 2 and seeds[0] != seeds[-1]:
            return True
    return False


SEMANTIC_WITNESSES = {
    "stacked_column": _has_stacked_column,
    "top_bottom_color_conflict": _top_and_bottom_differ,
}
SEMANTIC_RIVALS = {
    "single_seed_columns_only": _single_seed_columns_only,
    "bottommost_seed": _bottommost_seed,
}
WITNESS_RIVALS = {
    "stacked_column": ["single_seed_columns_only"],
    "top_bottom_color_conflict": ["bottommost_seed"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"declared rival {name!r} fits every demonstration")
    return reasons
