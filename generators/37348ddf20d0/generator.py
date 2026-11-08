"""Generator for task 37348ddf20d0: wall-aware two-color Voronoi fill.

Gray (5) cells are impassable walls.  Every black (0) cell is recolored by the
strictly nearer red (2) or green (3) seed under 4-neighbor shortest-path
distance.  Finite ties and components with no seed of either color remain 0.
Seed and wall cells are preserved.

The five-profile schedule is a lesson, not merely a morphology sampler:

* ``open_voronoi`` exercises nearest-of-multiple-seeds behavior;
* ``wall_detour`` makes wall-aware distance disagree with Manhattan distance;
* ``tie_rooms`` guarantees a finite red/green tie that must remain black;
* ``seedless_rooms`` guarantees a fully seedless chamber that remains black;
* ``mixed_rooms`` mirrors the canonical complete-wall partitions.

Five consecutive examples cover every profile, so every normal lesson can
falsify the named shortcut solvers declared at the bottom of this module.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "37348ddf20d0"
VERSION = "3.0.0"
TASK_ID = "37348ddf20d0"
RULE_HASH = "6d8410c29906"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Bordered red/green seed fields with open, detour, finite-tie, seedless-"
    "chamber, and complete-partition profiles. Open cells use wall-aware BFS "
    "distance; ties and seedless chambers remain black."
)

INVARIANTS = [
    "the grid is 11..13 by 11..13 and uses only colors 0, 2, 3, and 5",
    "the outer border is entirely color-5 wall",
    "there is at least one red seed and at least one green seed",
    "ordinary lessons cycle through five recoverable wall textures",
    "open cells use multi-source wall-aware distance; finite ties and seedless chambers stay 0",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile canonical schedule",
        "valid": "11..13",
        "doc": "Exact grid height; the full domain is accepted in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile canonical schedule",
        "valid": "11..13",
        "doc": "Exact grid width; the full domain is accepted in every difficulty band.",
    },
    "n_red": {
        "type": "int",
        "default": "scheduled 1..4",
        "valid": "1..4",
        "doc": "Exact number of red (2) seeds in the returned grid.",
    },
    "n_green": {
        "type": "int",
        "default": "scheduled 1..4",
        "valid": "1..4",
        "doc": "Exact number of green (3) seeds in the returned grid.",
    },
    "texture": {
        "type": "enum",
        "default": "five-profile semantic schedule",
        "valid": "open_voronoi|wall_detour|tie_rooms|seedless_rooms|mixed_rooms",
        "doc": "Exact recoverable wall topology / semantic lesson profile.",
    },
}

SCHEDULE_PROFILES = (
    "open_voronoi",
    "wall_detour",
    "tie_rooms",
    "seedless_rooms",
    "mixed_rooms",
)

# Every Cartesian product of the declared exact domains is deliberately valid.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_ALLOWED_COLORS = {0, 2, 3, 5}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the semantic profile for one draw.

    Within one lesson ``seed`` is fixed and sample indexes are consecutive, so
    every sliding window of five examples visits every profile exactly once.
    """
    del difficulty
    index = (int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)
    return SCHEDULE_PROFILES[index]


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))


def _draw_exact_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_exact_choice(ctx, label: str, scheduled: str, choices: tuple[str, ...]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, choices)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_axes(profile: str, difficulty: str | None) -> tuple[int, int, int, int]:
    dimensions = {
        "open_voronoi": (12, 11),
        "wall_detour": (11, 12),
        "tie_rooms": (13, 11),
        "seedless_rooms": (11, 13),
        "mixed_rooms": (12, 12),
    }
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    counts = {
        "easy": {
            "open_voronoi": (2, 2),
            "wall_detour": (2, 2),
            "tie_rooms": (2, 2),
            "seedless_rooms": (2, 2),
            "mixed_rooms": (2, 1),
        },
        "medium": {
            "open_voronoi": (3, 3),
            "wall_detour": (2, 2),
            "tie_rooms": (2, 2),
            "seedless_rooms": (2, 2),
            "mixed_rooms": (3, 2),
        },
        "hard": {
            "open_voronoi": (4, 4),
            "wall_detour": (3, 3),
            "tie_rooms": (3, 3),
            "seedless_rooms": (4, 4),
            "mixed_rooms": (4, 3),
        },
    }
    height, width = dimensions[profile]
    n_red, n_green = counts[band][profile]
    return height, width, n_red, n_green


def _bordered_grid(height: int, width: int) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][0] = 5
        grid[row][width - 1] = 5
    for col in range(width):
        grid[0][col] = 5
        grid[height - 1][col] = 5
    return grid


def _dedupe(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    return list(dict.fromkeys(cells))


def _place_seed_plan(
    grid: list[list[int]],
    *,
    n_red: int,
    n_green: int,
    mandatory_red: Iterable[tuple[int, int]],
    mandatory_green: Iterable[tuple[int, int]],
    red_pool: Iterable[tuple[int, int]],
    green_pool: Iterable[tuple[int, int]],
    rng,
) -> None:
    """Place exact seed counts while protecting both colors' mandatory cells."""
    plans = {
        2: (n_red, _dedupe(mandatory_red), _dedupe(red_pool)),
        3: (n_green, _dedupe(mandatory_green), _dedupe(green_pool)),
    }

    # Reserve and paint all mandatory positions before either color draws extras.
    used: dict[int, int] = {2: 0, 3: 0}
    reserved: set[tuple[int, int]] = set()
    for color in (2, 3):
        count, mandatory, _ = plans[color]
        for row, col in mandatory[:count]:
            if (row, col) in reserved or grid[row][col] != 0:
                raise AssertionError("mandatory seed positions overlap a wall or another seed")
            reserved.add((row, col))
            grid[row][col] = color
            used[color] += 1

    for color in (2, 3):
        count, _, pool = plans[color]
        candidates = [cell for cell in pool if grid[cell[0]][cell[1]] == 0]
        rng.shuffle(candidates)
        need = count - used[color]
        if len(candidates) < need:
            raise ValueError(
                f"texture cannot place {count} color-{color} seeds; only "
                f"{used[color] + len(candidates)} cells available"
            )
        for row, col in candidates[:need]:
            grid[row][col] = color


def _all_interior(height: int, width: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]


def _build_open_voronoi(height, width, n_red, n_green, rng):
    grid = _bordered_grid(height, width)
    top = rng.randint(1, max(1, height // 3))
    bottom = rng.randint(max(top + 2, 2 * height // 3), height - 2)
    left = rng.randint(1, max(1, width // 3))
    right = rng.randint(max(left + 2, 2 * width // 3), width - 2)

    mandatory_red = [(top, left), (bottom, right)]
    mandatory_green = [(top, right), (bottom, left)]
    all_cells = _all_interior(height, width)
    red_preferred = [
        cell for cell in all_cells if cell[0] >= height // 2 and cell[1] >= width // 2
    ]
    green_preferred = [
        cell for cell in all_cells if cell[0] >= height // 2 and cell[1] < width // 2
    ]
    _place_seed_plan(
        grid,
        n_red=n_red,
        n_green=n_green,
        mandatory_red=mandatory_red,
        mandatory_green=mandatory_green,
        red_pool=red_preferred + all_cells,
        green_pool=green_preferred + all_cells,
        rng=rng,
    )
    return grid


def _build_wall_detour(height, width, n_red, n_green, rng):
    grid = _bordered_grid(height, width)
    wall_col = rng.randint(4, width - 5)
    for row in range(1, height - 2):
        grid[row][wall_col] = 5

    left_cells = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, wall_col)
        if grid[row][col] == 0
    ]
    right_cells = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(wall_col + 1, width - 1)
        if grid[row][col] == 0
    ]
    seed_row_hi = min(4, height - 3)
    mandatory_red = [(rng.randint(1, seed_row_hi), 1)]
    mandatory_green = [(rng.randint(1, seed_row_hi), wall_col + 1)]
    _place_seed_plan(
        grid,
        n_red=n_red,
        n_green=n_green,
        mandatory_red=mandatory_red,
        mandatory_green=mandatory_green,
        red_pool=sorted(left_cells, key=lambda cell: (-cell[0], cell[1])),
        green_pool=right_cells,
        rng=rng,
    )
    return grid


def _build_tie_rooms(height, width, n_red, n_green, rng):
    grid = _bordered_grid(height, width)
    split = rng.randint(4, height - 5)
    for col in range(width):
        grid[split][col] = 5

    seed_row = rng.randint(1, split - 1)
    left = rng.randint(1, max(1, width // 3))
    right = width - 2 - rng.randint(0, 1)
    if (right - left) % 2:
        right -= 1
    if right <= left:
        right = left + 2
    mandatory_red = [(seed_row, left)]
    mandatory_green = [(seed_row, right)]
    bottom_cells = [
        (row, col)
        for row in range(split + 1, height - 1)
        for col in range(1, width - 1)
    ]
    _place_seed_plan(
        grid,
        n_red=n_red,
        n_green=n_green,
        mandatory_red=mandatory_red,
        mandatory_green=mandatory_green,
        red_pool=bottom_cells,
        green_pool=reversed(bottom_cells),
        rng=rng,
    )
    return grid


def _vertical_partition_pair(width: int, rng) -> tuple[int, int]:
    pairs = [
        (left, right)
        for left in range(3, width - 4)
        for right in range(left + 3, width - 2)
        if width - right - 1 >= 2
    ]
    if not pairs:
        raise ValueError(f"width {width} cannot hold three nonempty chambers")
    return rng.choice(pairs)


def _build_seedless_rooms(height, width, n_red, n_green, rng):
    grid = _bordered_grid(height, width)
    left_wall, right_wall = _vertical_partition_pair(width, rng)
    for row in range(height):
        grid[row][left_wall] = 5
        grid[row][right_wall] = 5

    outer_cells = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if col < left_wall or col > right_wall
    ]
    left_cells = [cell for cell in outer_cells if cell[1] < left_wall]
    right_cells = [cell for cell in outer_cells if cell[1] > right_wall]
    mandatory_red = [rng.choice(left_cells)]
    mandatory_green = [rng.choice(right_cells)]
    _place_seed_plan(
        grid,
        n_red=n_red,
        n_green=n_green,
        mandatory_red=mandatory_red,
        mandatory_green=mandatory_green,
        red_pool=left_cells + right_cells,
        green_pool=right_cells + left_cells,
        rng=rng,
    )
    return grid


def _build_mixed_rooms(height, width, n_red, n_green, rng):
    grid = _bordered_grid(height, width)
    split_row = rng.randint(4, height - 5)
    split_col = rng.randint(4, width - 5)
    for col in range(width):
        grid[split_row][col] = 5
    for row in range(height):
        grid[row][split_col] = 5

    top_left = [
        (row, col)
        for row in range(1, split_row)
        for col in range(1, split_col)
    ]
    all_open = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 0
    ]
    pair = rng.sample(top_left, 2)
    _place_seed_plan(
        grid,
        n_red=n_red,
        n_green=n_green,
        mandatory_red=[pair[0]],
        mandatory_green=[pair[1]],
        red_pool=all_open,
        green_pool=reversed(all_open),
        rng=rng,
    )
    return grid


_BUILDERS = {
    "open_voronoi": _build_open_voronoi,
    "wall_detour": _build_wall_detour,
    "tie_rooms": _build_tie_rooms,
    "seedless_rooms": _build_seedless_rooms,
    "mixed_rooms": _build_mixed_rooms,
}


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
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w, scheduled_red, scheduled_green = _scheduled_axes(
        scheduled_profile, difficulty
    )
    height = _draw_exact_int(ctx, "grid_h", scheduled_h, 11, 13)
    width = _draw_exact_int(ctx, "grid_w", scheduled_w, 11, 13)
    n_red = _draw_exact_int(ctx, "n_red", scheduled_red, 1, 4)
    n_green = _draw_exact_int(ctx, "n_green", scheduled_green, 1, 4)
    texture = _draw_exact_choice(
        ctx, "texture", scheduled_profile, SCHEDULE_PROFILES
    )
    rng = ctx.draw_rng("layout")
    grid = _BUILDERS[texture](height, width, n_red, n_green, rng)

    # Constructors are deliberately total over the AXES Cartesian product.
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_red": n_red,
        "n_green": n_green,
        "texture": texture,
    }
    if observed != expected:
        raise AssertionError(f"constructor observability mismatch: {observed} != {expected}")
    findings = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if findings:
        raise AssertionError("constructor violated self_check: " + "; ".join(findings))
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and rule mirror
# ---------------------------------------------------------------------------


def _shape_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list of rows"
    if not all(isinstance(row, list) for row in grid):
        return "every row must be a list"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be a nonempty rectangle"
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or value not in _ALLOWED_COLORS:
                return "grid values must be colors 0, 2, 3, or 5"
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    error = _shape_error(grid)
    if error:
        return [error]
    height, width = len(grid), len(grid[0])
    findings: list[str] = []
    if not 11 <= height <= 13:
        findings.append(f"grid height must be in 11..13, got {height}")
    if not 11 <= width <= 13:
        findings.append(f"grid width must be in 11..13, got {width}")
    if any(grid[0][col] != 5 or grid[height - 1][col] != 5 for col in range(width)):
        findings.append("top and bottom borders must be color-5 walls")
    if any(grid[row][0] != 5 or grid[row][width - 1] != 5 for row in range(height)):
        findings.append("left and right borders must be color-5 walls")
    n_red = sum(value == 2 for row in grid for value in row)
    n_green = sum(value == 3 for row in grid for value in row)
    if not 1 <= n_red <= 4:
        findings.append(f"expected 1..4 red seeds, got {n_red}")
    if not 1 <= n_green <= 4:
        findings.append(f"expected 1..4 green seeds, got {n_green}")
    if not any(value == 0 for row in grid for value in row):
        findings.append("expected at least one open black cell")
    return findings


def strict_canonical_like(grid) -> list[str]:
    """Every lawful generated or authoritative input lies on this task manifold."""
    return self_check(grid)


def _distance_map_from_sources(
    grid: list[list[int]], sources: Iterable[tuple[int, int]]
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    infinity = height * width + 1
    distance = [[infinity] * width for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()
    for row, col in sources:
        if grid[row][col] == 5 or distance[row][col] == 0:
            continue
        distance[row][col] = 0
        queue.append((row, col))
    while queue:
        row, col = queue.popleft()
        for dr, dc in _DIR4:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 5
                and distance[nr][nc] == infinity
            ):
                distance[nr][nc] = distance[row][col] + 1
                queue.append((nr, nc))
    return distance


def _seed_positions(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def _distance_maps(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    return (
        _distance_map_from_sources(grid, _seed_positions(grid, 2)),
        _distance_map_from_sources(grid, _seed_positions(grid, 3)),
    )


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected canonical Racket rule."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    red, green = _distance_maps(grid)
    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 0:
                continue
            if red[row][col] < green[row][col]:
                output[row][col] = 2
            elif green[row][col] < red[row][col]:
                output[row][col] = 3
    return output


def _full_wall_rows(grid) -> list[int]:
    height, width = len(grid), len(grid[0])
    return [
        row
        for row in range(1, height - 1)
        if all(grid[row][col] == 5 for col in range(width))
    ]


def _full_wall_cols(grid) -> list[int]:
    height, width = len(grid), len(grid[0])
    return [
        col
        for col in range(1, width - 1)
        if all(grid[row][col] == 5 for row in range(height))
    ]


def _observe_texture(grid) -> str:
    height, width = len(grid), len(grid[0])
    full_rows = _full_wall_rows(grid)
    full_cols = _full_wall_cols(grid)
    explained = {
        (row, col)
        for row in full_rows
        for col in range(1, width - 1)
    } | {
        (row, col)
        for col in full_cols
        for row in range(1, height - 1)
    }
    interior_walls = {
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 5
    }
    extras = interior_walls - explained
    signature = (len(full_rows), len(full_cols), bool(extras))
    textures = {
        (0, 0, False): "open_voronoi",
        (0, 0, True): "wall_detour",
        (1, 0, False): "tie_rooms",
        (0, 2, False): "seedless_rooms",
        (1, 1, False): "mixed_rooms",
    }
    if signature not in textures:
        raise ValueError(
            "wall pattern is not one of the five declared textures: "
            f"full_rows={full_rows}, full_cols={full_cols}, extra={len(extras)}"
        )
    return textures[signature]


def observe_overrides(grid) -> dict[str, int | str]:
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_red": sum(value == 2 for row in grid for value in row),
        "n_green": sum(value == 3 for row in grid for value in row),
        "texture": _observe_texture(grid),
    }


# ---------------------------------------------------------------------------
# Semantic witnesses and named wrong-rule competitors
# ---------------------------------------------------------------------------


def _rival_ignore_walls_manhattan(grid):
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    red_seeds = _seed_positions(grid, 2)
    green_seeds = _seed_positions(grid, 3)
    infinity = len(grid) * len(grid[0]) + 1
    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 0:
                continue
            d_red = min(
                (abs(row - rr) + abs(col - cc) for rr, cc in red_seeds),
                default=infinity,
            )
            d_green = min(
                (abs(row - rr) + abs(col - cc) for rr, cc in green_seeds),
                default=infinity,
            )
            if d_red < d_green:
                output[row][col] = 2
            elif d_green < d_red:
                output[row][col] = 3
    return output


def _rival_break_ties_toward_red(grid):
    red, green = _distance_maps(grid)
    infinity = len(grid) * len(grid[0]) + 1
    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 0:
                continue
            if red[row][col] <= green[row][col] and red[row][col] < infinity:
                output[row][col] = 2
            elif green[row][col] < red[row][col]:
                output[row][col] = 3
    return output


def _rival_first_seed_each_color(grid):
    red_seeds = _seed_positions(grid, 2)
    green_seeds = _seed_positions(grid, 3)
    red = _distance_map_from_sources(grid, red_seeds[:1])
    green = _distance_map_from_sources(grid, green_seeds[:1])
    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 0:
                continue
            if red[row][col] < green[row][col]:
                output[row][col] = 2
            elif green[row][col] < red[row][col]:
                output[row][col] = 3
    return output


def _nonwall_components(grid) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 5
    }
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = next(iter(unseen))
        component = {start}
        queue = [start]
        unseen.remove(start)
        for row, col in queue:
            for dr, dc in _DIR4:
                neighbor = (row + dr, col + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _has_wall_aware_detour(grid) -> bool:
    return rule_mirror(grid) != _rival_ignore_walls_manhattan(grid)


def _has_finite_tie(grid) -> bool:
    red, green = _distance_maps(grid)
    infinity = len(grid) * len(grid[0]) + 1
    return any(
        grid[row][col] == 0
        and red[row][col] == green[row][col]
        and red[row][col] < infinity
        for row in range(len(grid))
        for col in range(len(grid[0]))
    )


def _has_seedless_chamber(grid) -> bool:
    for component in _nonwall_components(grid):
        colors = {grid[row][col] for row, col in component}
        if 0 in colors and 2 not in colors and 3 not in colors:
            return True
    return False


def _has_multiple_seed_effect(grid) -> bool:
    if max(len(_seed_positions(grid, 2)), len(_seed_positions(grid, 3))) < 2:
        return False
    return rule_mirror(grid) != _rival_first_seed_each_color(grid)


SEMANTIC_WITNESSES = {
    "wall_aware_detour": _has_wall_aware_detour,
    "finite_ties_remain_black": _has_finite_tie,
    "seedless_chamber_remains_black": _has_seedless_chamber,
    "nearest_of_multiple_same_color": _has_multiple_seed_effect,
}

SEMANTIC_RIVALS = {
    "ignore_walls_manhattan": _rival_ignore_walls_manhattan,
    "break_ties_toward_red": _rival_break_ties_toward_red,
    "first_seed_each_color": _rival_first_seed_each_color,
}

WITNESS_RIVALS = {
    "wall_aware_detour": ["ignore_walls_manhattan"],
    "finite_ties_remain_black": ["break_ties_toward_red"],
    "seedless_chamber_remains_black": ["ignore_walls_manhattan"],
    "nearest_of_multiple_same_color": ["first_seed_each_color"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named wrong rule survives every demonstration."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with wall-aware BFS")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with wall-aware BFS")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
