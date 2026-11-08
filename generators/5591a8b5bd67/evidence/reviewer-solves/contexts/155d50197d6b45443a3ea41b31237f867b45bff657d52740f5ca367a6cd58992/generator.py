"""Generator for Cast Rightward Rays Until the Wall (5591a8b5bd67).

Every non-gray seed casts its own color rightward through zero cells.  A ray
stops at the first gray wall or at the grid boundary.  Generated scenes use one
seed per active row so the gray-wall versus border branches remain explicit.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5591a8b5bd67"
VERSION = "3.0.0"
TASK_ID = "5591a8b5bd67"
RULE_HASH = "8ee1a275388e"
SUMMARY = (
    "On a color-0 background, each active row contains exactly one non-gray "
    "seed. The seed paints consecutive zero cells to its right with its own "
    "color, stopping at an optional gray (5) wall or at the right boundary. "
    "Seeds and walls are preserved. Consecutive sample indices deliberately "
    "cycle through mixed, all-blocked, and all-open wall profiles."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is color 0",
    "there are at least two active rows, each with exactly one non-gray seed",
    "every seed has a zero cell immediately to its right, so every ray is visible",
    "an active row has at most one gray wall; every wall is at least two cells right of its seed and leaves a zero beyond it",
    "every scene has at least one seed with background space to its left, rebutting bidirectional growth",
    "normal lessons cycle through mixed, all-blocked, and border-reaching examples",
]

SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
WALL_PROFILES = ("open", "mixed", "blocked")
_PROFILE_SCHEDULE = ("mixed", "blocked", "open")

# Every declared axis is exact and recoverable from the returned grid.  Single
# overrides accept the full declared range in every difficulty band; explicitly
# incompatible combinations (for example rays=10 with grid_h=6) reject loudly.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 6..14",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 8..18",
        "valid": "8..18",
    },
    "rays": {
        "type": "int",
        "default": "difficulty-aware rng 2..10",
        "valid": "2..10",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "rng 2..min(8,rays); exact override may request 1",
        "valid": "1..8",
    },
    "wall_profile": {
        "type": "enum",
        "default": "sample_index cycle mixed|blocked|open",
        "valid": WALL_PROFILES,
    },
}


def _band_ranges(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (6, 8), (8, 11), (2, 4)
    if difficulty == "hard":
        return (11, 14), (14, 18), (6, 10)
    return (8, 11), (11, 15), (4, 7)


def _requested_int(overrides: dict, name: str) -> int | None:
    value = overrides.get(name)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} override must be an integer") from exc


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket rule remains output authority."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    (h_lo, h_hi), (w_lo, w_hi), (ray_lo, ray_hi) = _band_ranges(difficulty)
    requested_h = _requested_int(overrides, "grid_h")
    requested_rays = _requested_int(overrides, "rays")
    requested_colors = _requested_int(overrides, "n_distinct_colors")

    if requested_rays is not None and not 2 <= requested_rays <= 10:
        raise ValueError("rays override outside declared range 2..10")
    if requested_colors is not None and not 1 <= requested_colors <= 8:
        raise ValueError("n_distinct_colors override outside declared range 1..8")
    if (
        requested_rays is not None
        and requested_colors is not None
        and requested_colors > requested_rays
    ):
        raise ValueError("n_distinct_colors cannot exceed rays")

    # A lone high ray-count override remains feasible by raising the default
    # height floor.  A contradictory explicit grid_h+rays pair rejects in the
    # rays draw below, which the override contract records as an intentional
    # combination rejection.
    if requested_h is not None:
        h = ctx.draw_int("grid_h", 6, 14)
    else:
        required_h = requested_rays or requested_colors or 0
        h = ctx.draw_int("grid_h", max(h_lo, required_h), h_hi if required_h <= h_hi else 14)

    if "grid_w" in overrides and overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", 8, 18)
    else:
        w = ctx.draw_int("grid_w", w_lo, w_hi)

    if requested_rays is not None:
        rays = ctx.draw_int("rays", 2, min(10, h))
    else:
        min_rays = max(ray_lo, requested_colors or 1)
        max_rays = min(10, h)
        default_hi = max(ray_hi, requested_colors or ray_hi)
        rays = ctx.draw_int("rays", min_rays, min(default_hi, max_rays))

    if requested_colors is not None:
        n_colors = ctx.draw_int("n_distinct_colors", 1, min(8, rays))
    else:
        n_colors = ctx.draw_int("n_distinct_colors", 2, min(8, rays))

    if overrides.get("wall_profile") is not None:
        wall_profile = ctx.draw_choice("wall_profile", WALL_PROFILES)
    else:
        scheduled = _PROFILE_SCHEDULE[int(sample_index) % len(_PROFILE_SCHEDULE)]
        wall_profile = ctx.draw_choice("wall_profile", (scheduled,))

    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    rows = rng.sample(range(h), rays)

    palette = rng.sample(list(SEED_COLORS), n_colors)
    seed_colors = list(palette)
    seed_colors.extend(rng.choice(palette) for _ in range(rays - n_colors))
    rng.shuffle(seed_colors)

    if wall_profile == "open":
        blocked_rows: set[int] = set()
    elif wall_profile == "blocked":
        blocked_rows = set(rows)
    else:
        blocked_count = rng.randint(1, rays - 1)
        blocked_rows = set(rng.sample(rows, blocked_count))

    for index, (row, color) in enumerate(zip(rows, seed_colors)):
        blocked = row in blocked_rows
        max_seed_col = w - 4 if blocked else w - 3
        min_seed_col = 1 if index == 0 else 0
        seed_col = rng.randint(min_seed_col, max_seed_col)
        grid[row][seed_col] = color
        if blocked:
            wall_col = rng.randint(seed_col + 2, w - 2)
            grid[row][wall_col] = 5

    return grid


def _analysis(grid) -> dict:
    """Recover exact semantic controls from a structurally valid scene."""
    seeds: list[tuple[int, int, int]] = []
    walls: list[tuple[int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 5:
                walls.append((r, c))
            elif value != 0:
                seeds.append((r, c, value))
    seed_rows = {r for r, _, _ in seeds}
    blocked_seed_rows = {r for r, _ in walls if r in seed_rows}
    if not walls:
        wall_profile = "open"
    elif len(blocked_seed_rows) == len(seed_rows) and len(walls) == len(seed_rows):
        wall_profile = "blocked"
    else:
        wall_profile = "mixed"
    return {
        "rays": len(seeds),
        "n_distinct_colors": len({value for _, _, value in seeds}),
        "wall_profile": wall_profile,
        "seed_rows": seed_rows,
        "walls": walls,
        "seeds": seeds,
    }


def observe_overrides(grid) -> dict[str, int | str]:
    info = _analysis(grid)
    return {
        "rays": info["rays"],
        "n_distinct_colors": info["n_distinct_colors"],
        "wall_profile": info["wall_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons while accepting all five canonical inputs."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cell values must be integer ARC colors 0..9")
        return errors

    seed_count = 0
    has_left_space_witness = False
    for r, row in enumerate(grid):
        seeds = [(c, value) for c, value in enumerate(row) if value not in (0, 5)]
        walls = [c for c, value in enumerate(row) if value == 5]
        if len(seeds) > 1:
            errors.append(f"row {r} has multiple non-gray seeds")
            continue
        if walls and not seeds:
            errors.append(f"row {r} has a gray wall but no seed")
            continue
        if len(walls) > 1:
            errors.append(f"row {r} has multiple gray walls")
        if not seeds:
            continue
        seed_count += 1
        seed_col, _ = seeds[0]
        has_left_space_witness = has_left_space_witness or seed_col > 0
        if seed_col + 1 >= width:
            errors.append(f"row {r} seed is at the right edge")
        elif row[seed_col + 1] != 0:
            errors.append(f"row {r} seed has no visible zero immediately right")
        for wall_col in walls:
            if wall_col <= seed_col + 1:
                errors.append(f"row {r} wall must be at least two cells right of seed")
            if wall_col + 1 >= width or row[wall_col + 1] != 0:
                errors.append(f"row {r} wall must leave a zero cell beyond it")

    if seed_count < 2:
        errors.append(f"expected at least two active seed rows, got {seed_count}")
    if seed_count and not has_left_space_witness:
        errors.append("expected at least one seed with background space to its left")
    return errors
