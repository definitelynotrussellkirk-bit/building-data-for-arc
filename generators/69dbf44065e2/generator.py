"""Generator for S10_M6 / 69dbf44065e2 — blocked downward smears.

Every colored seed (any nonzero color except wall color 5) paints its color
straight downward through original background cells.  It stops at the first
non-background cell or at the lower edge.  Color 5 is a passive blocker.

The repaired generator exposes only four literal, observable axes.  Ordinary
three-example windows rotate through a wall blocker, a colored-seed blocker,
and an open long streak so the lesson refutes one-step and blocker-ignoring
shortcuts.  Exact overrides remain valid in every difficulty band, including
substantive 30x30 inputs.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "69dbf44065e2"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "b6021aa25bf4"
SUMMARY = (
    "Sparse colored seeds smear downward through background until the first "
    "non-background blocker or the lower edge; color 5 is a passive wall."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCENE_PROFILES = ("wall_block", "seed_block", "open_long")
SCHEDULE_PROFILES = SCENE_PROFILES
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "grid is a literal rectangular ARC grid between 5x5 and 30x30",
    "2..8 non-wall colored seed cells and 0..4 color-5 wall cells",
    "at least one colored seed has original background immediately below it",
    "only original background is painted; every original non-background cell is preserved",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty/profile keyed", "valid": "5..30"},
    "grid_w": {"type": "int", "default": "difficulty/profile keyed", "valid": "5..30"},
    "n_color": {"type": "int", "default": "difficulty/profile keyed", "valid": "2..8"},
    "n_walls": {"type": "int", "default": "difficulty/profile keyed", "valid": "0..4"},
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_COLOR_VALUES = (1, 2, 3, 4, 6, 7, 8, 9)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _grid_errors(grid: Any) -> list[str]:
    if type(grid) not in (list, tuple) or not grid:
        return ["grid must be a nonempty row sequence"]
    if type(grid[0]) not in (list, tuple) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        errors.append("grid dimensions must be in 1..30")
    for index, row in enumerate(grid):
        if type(row) not in (list, tuple) or len(row) != width:
            errors.append(f"row {index} must have width {width}")
            continue
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            errors.append("cells must be literal ARC integers 0..9; bool is forbidden")
    return errors


def _seed_cells(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]


def rule_mirror(grid):
    """Pure-Python mirror of the selected canonical Racket program."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    source = [list(row) for row in grid]
    out = deepcopy(source)
    height = len(source)
    for row, col, value in _seed_cells(source):
        rr = row + 1
        while rr < height and source[rr][col] == 0:
            out[rr][col] = value
            rr += 1
    return out


def observe_overrides(grid) -> dict[str, int]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_color": len(_seed_cells(grid)),
        "n_walls": sum(value == 5 for row in grid for value in row),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task grammar and require an actually exercised smear."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if height < 5 or width < 5:
        errors.append("generator grammar requires dimensions at least 5x5")
    seeds = _seed_cells(grid)
    walls = sum(value == 5 for row in grid for value in row)
    if not 2 <= len(seeds) <= 8:
        errors.append(f"expected 2..8 colored seeds, got {len(seeds)}")
    if not 0 <= walls <= 4:
        errors.append(f"expected 0..4 color-5 walls, got {walls}")
    if seeds and not any(row + 1 < height and grid[row + 1][col] == 0 for row, col, _ in seeds):
        errors.append("at least one colored seed must have background directly below")
    if not errors and rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("canonical rule must change the generated input")
    requested = ((meta or {}).get("overrides") or {})
    if requested:
        observed = observe_overrides(grid)
        for key, value in requested.items():
            if key in AXES and observed.get(key) != value:
                errors.append(f"override {key} drifted from {value!r} to {observed.get(key)!r}")
    if difficulty not in _VALID_DIFFICULTIES:
        errors.append(f"unsupported difficulty {difficulty!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the sparse seed/wall manifold used by all canonical pairs."""
    return self_check(grid)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    if type(sample_index) is not int or isinstance(sample_index, bool):
        raise TypeError("sample_index must be an integer (not bool)")
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _draw_axis(ctx, label: str, full_low: int, full_high: int, default_low: int, default_high: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, full_low, full_high)
    return ctx.draw_int_strict(label, default_low, default_high)


def _defaults(difficulty, profile):
    if difficulty == "easy":
        dims = (6, 9)
        colors = (2, 4)
        walls = (0, 2)
    elif difficulty == "medium":
        dims = (7, 13)
        colors = (3, 6)
        walls = (0, 3)
    elif difficulty == "hard":
        dims = (14, 30)
        colors = (5, 8)
        walls = (1, 4)
    else:
        dims = (6, 12)
        colors = (2, 6)
        walls = (0, 3)
    wall_low, wall_high = walls
    if profile == "wall_block":
        wall_low = max(1, wall_low)
    return dims, colors, (wall_low, wall_high)


def _place_scene(height: int, width: int, n_color: int, n_walls: int, profile: str, layout_rng, color_rng):
    grid = full_grid(height, width, 0)
    center = width // 2
    left = max(0, center - max(2, width // 4))
    right = min(width - 1, center + max(2, width // 4))
    if left == center:
        left = max(0, center - 1)
    if right == center:
        right = min(width - 1, center + 1)

    seeds: list[tuple[int, int]]
    walls: list[tuple[int, int]] = []
    if profile == "seed_block":
        blocker_row = min(height - 2, max(2, height // 2))
        seeds = [(0, center), (blocker_row, center)]
        guaranteed = (blocker_row, center)
    elif profile == "open_long":
        seeds = [(0, left), (1, right)]
        guaranteed = seeds[0]
    else:
        seeds = [(0, center), (1, left)]
        guaranteed = seeds[0]
        if n_walls:
            walls.append((height - 2, center))

    used = set(seeds) | set(walls)
    reserve = {(guaranteed[0] + 1, guaranteed[1])}
    # Preserve the intended wall/seed relationship and one guaranteed changed cell.
    protected_columns = set()
    if profile == "wall_block" and walls:
        protected_columns.add(center)
    if profile == "seed_block":
        protected_columns.add(center)

    seed_candidates = [
        (row, col)
        for row in range(0, height - 1)
        for col in range(width)
        if (row, col) not in used and (row, col) not in reserve
        and not (col in protected_columns and row > 0)
    ]
    layout_rng.shuffle(seed_candidates)
    while len(seeds) < n_color:
        if not seed_candidates:
            raise ValueError("scene has insufficient legal seed positions")
        pos = seed_candidates.pop()
        seeds.append(pos)
        used.add(pos)

    wall_candidates = [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if (row, col) not in used and (row, col) not in reserve
        and not (profile == "seed_block" and col == center)
    ]
    layout_rng.shuffle(wall_candidates)
    while len(walls) < n_walls:
        if not wall_candidates:
            raise ValueError("scene has insufficient legal wall positions")
        pos = wall_candidates.pop()
        walls.append(pos)
        used.add(pos)

    colors = list(_COLOR_VALUES)
    color_rng.shuffle(colors)
    for (row, col), value in zip(seeds, colors[: len(seeds)]):
        grid[row][col] = value
    for row, col in walls:
        grid[row][col] = 5
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or isinstance(seed, bool) or seed < 0:
        raise TypeError("seed must be a nonnegative integer (not bool)")
    if type(sample_index) is not int or isinstance(sample_index, bool) or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unsupported difficulty {difficulty!r}; expected easy, medium, hard or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    profile = schedule_profile(seed, sample_index, difficulty)
    dims, colors, walls = _defaults(difficulty, profile)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_axis(ctx, "grid_h", 5, 30, dims[0], dims[1])
    width = _draw_axis(ctx, "grid_w", 5, 30, dims[0], dims[1])
    n_color = _draw_axis(ctx, "n_color", 2, 8, colors[0], colors[1])
    n_walls = _draw_axis(ctx, "n_walls", 0, 4, walls[0], walls[1])

    grid = _place_scene(
        height,
        width,
        n_color,
        n_walls,
        profile,
        ctx.draw_rng("layout"),
        ctx.draw_rng("colors"),
    )
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError("generated invalid smear scene: " + "; ".join(errors))
    return grid


# --- Semantic rivals and witnesses -----------------------------------------

def _resume_after_blockers(grid):
    """Wrong rule: each earlier seed resumes in every later background cell."""
    source = [list(row) for row in grid]
    out = deepcopy(source)
    for row, col, value in _seed_cells(source):
        for rr in range(row + 1, len(source)):
            if source[rr][col] == 0 and out[rr][col] == 0:
                out[rr][col] = value
    return out


def _one_step_only(grid):
    source = [list(row) for row in grid]
    out = deepcopy(source)
    for row, col, value in _seed_cells(source):
        if row + 1 < len(source) and source[row + 1][col] == 0:
            out[row + 1][col] = value
    return out


def _smear_walls_too(grid):
    source = [list(row) for row in grid]
    out = rule_mirror(source)
    for row, values in enumerate(source):
        for col, value in enumerate(values):
            if value != 5:
                continue
            rr = row + 1
            while rr < len(source) and source[rr][col] == 0:
                out[rr][col] = 5
                rr += 1
    return out


def _first_blocker(grid, row, col):
    rr = row + 1
    zeros = 0
    while rr < len(grid) and grid[rr][col] == 0:
        zeros += 1
        rr += 1
    return (grid[rr][col] if rr < len(grid) else None), zeros, rr


def _wall_stops_streak(grid) -> bool:
    return any(_first_blocker(grid, r, c)[0] == 5 and _first_blocker(grid, r, c)[1] > 0
               and _first_blocker(grid, r, c)[2] + 1 < len(grid)
               for r, c, _ in _seed_cells(grid))


def _colored_seed_stops_streak(grid) -> bool:
    return any((blocker not in (None, 0, 5)) and zeros > 0 and end + 1 < len(grid)
               for r, c, _ in _seed_cells(grid)
               for blocker, zeros, end in [_first_blocker(grid, r, c)])


def _long_extension(grid) -> bool:
    return any(_first_blocker(grid, r, c)[1] >= 2 for r, c, _ in _seed_cells(grid))


SEMANTIC_RIVALS = {
    "resume_after_blockers": _resume_after_blockers,
    "one_step_only": _one_step_only,
    "smear_walls_too": _smear_walls_too,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "wall_stops_streak": _wall_stops_streak,
    "colored_seed_stops_streak": _colored_seed_stops_streak,
    "long_extension": _long_extension,
}
WITNESS_RIVALS = {
    "wall_stops_streak": ("resume_after_blockers",),
    "colored_seed_stops_streak": ("resume_after_blockers",),
    "long_extension": ("one_step_only",),
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute the bounded plausible wrong rules."""
    if type(demos) is not list or not demos:
        return ["lesson needs at least one labeled demonstration"]
    if not isinstance(query, dict) or not {"input", "output"} <= set(query):
        return ["query must be a labeled pair"]
    reasons: list[str] = []
    try:
        if rule_mirror(query["input"]) != query["output"]:
            reasons.append("query label differs from the canonical smear rule")
        for index, pair in enumerate(demos):
            if rule_mirror(pair["input"]) != pair["output"]:
                reasons.append(f"demonstration {index} label differs from the canonical rule")
        for name, rival in LESSON_COMPETITORS.items():
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            if fits and rival(query["input"]) != query["output"]:
                reasons.append(f"competitor {name} fits every demonstration but changes the query")
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"malformed lesson: {exc}")
    return reasons
