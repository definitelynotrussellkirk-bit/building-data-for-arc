"""Generator for 28f91ad53b1b: wall-aware Voronoi from colored seeds.

Color 5 is an impassable wall. Every other nonzero cell is a one-cell seed.
For every non-wall cell, measure 4-neighbor shortest-path distance through
non-wall cells to every reachable seed. The closest seed color wins; a finite
distance tie is resolved by the numerically smaller color. A component with no
seed stays 0, and walls stay 5.

The five-profile schedule is deliberately semantic:

* ``open_voronoi`` anchors the canonical framed-chamber morphology and repeats
  the finite-tie lesson without internal walls;
* ``wall_detour`` makes shortest-path distance disagree with Manhattan distance;
* ``tie_order`` reverses color order versus row-major seed order at a finite tie;
* ``seedless_rooms`` contains an enclosed component with no seed and a second
  wall-detour witness in a seeded component;
* ``mixed_rooms`` gives three or more isolated seed colors independent regions.

Five consecutive examples visit all profiles. Every six-pair lesson (five
demonstrations plus one query) contains two independent counterexamples for the
row-major-tie and component-Manhattan shortcuts, so any query rotation remains
identified by the other five pairs.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "28f91ad53b1b"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "443a7da44ab8"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Canonical-style zero outer border and gray inner chamber frame, with 2..5 "
    "distinct one-cell color seeds. Open, wall-detour, finite-tie, seedless-room, "
    "and mixed-room profiles teach wall-aware nearest-seed fill; ties choose the "
    "smaller color and components without seeds stay zero."
)

INVARIANTS = [
    "the outer border is 0 and the one-cell inset chamber frame is color 5",
    "there are 2..5 one-cell seeds with distinct colors other than 0 and 5",
    "every generated seed touches the connected wall network, matching canonical object morphology",
    "non-wall cells use per-seed 4-neighbor shortest-path distance through non-walls",
    "finite ties choose the smaller color; seedless components remain 0",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile canonical schedule",
        "valid": "8..10",
        "doc": "Exact height; the full canonical envelope is valid in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile canonical schedule",
        "valid": "10..12",
        "doc": "Exact width; the full canonical envelope is valid in every band.",
    },
    "n_seeds": {
        "type": "int",
        "default": "scheduled 2..5",
        "valid": "2..5",
        "doc": "Exact number of distinct-color seed cells.",
    },
    "texture": {
        "type": "enum",
        "default": "five-profile semantic schedule",
        "valid": "open_voronoi|wall_detour|tie_order|seedless_rooms|mixed_rooms",
        "doc": "Exact recoverable wall topology and semantic lesson profile.",
    },
}

SCHEDULE_PROFILES = (
    "open_voronoi",
    "wall_detour",
    "tie_order",
    "seedless_rooms",
    "mixed_rooms",
)

# Every Cartesian product of the exact domains above is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_EXTRA_COLORS = (1, 3, 4, 6, 7, 8, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    """Recoverable five-cycle used by ordinary lessons."""
    del difficulty
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for name in ("grid_h", "grid_w", "n_seeds"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    value = overrides.get("texture")
    if value is not None and type(value) is not str:
        raise ValueError(f"texture must be a string, not {type(value).__name__}")


def _draw_exact_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_exact_choice(ctx, label: str, scheduled: str, choices: tuple[str, ...]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, choices)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_axes(profile: str, difficulty: str | None) -> tuple[int, int, int]:
    dimensions = {
        "open_voronoi": (9, 11),
        "wall_detour": (10, 12),
        "tie_order": (8, 10),
        "seedless_rooms": (9, 11),
        "mixed_rooms": (10, 12),
    }
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    counts = {
        "easy": {
            "open_voronoi": 2,
            "wall_detour": 2,
            "tie_order": 2,
            "seedless_rooms": 3,
            "mixed_rooms": 3,
        },
        "medium": {
            "open_voronoi": 2,
            "wall_detour": 2,
            "tie_order": 2,
            "seedless_rooms": 4,
            "mixed_rooms": 3,
        },
        "hard": {
            "open_voronoi": 2,
            "wall_detour": 2,
            "tie_order": 2,
            "seedless_rooms": 5,
            "mixed_rooms": 4,
        },
    }
    height, width = dimensions[profile]
    return height, width, counts[band][profile]


def _framed_grid(height: int, width: int) -> list[list[int]]:
    """Canonical morphology: zero outer border, gray one-cell inset frame."""
    grid = full_grid(height, width, 0)
    for col in range(1, width - 1):
        grid[1][col] = 5
        grid[height - 2][col] = 5
    for row in range(1, height - 1):
        grid[row][1] = 5
        grid[row][width - 2] = 5
    return grid


def _chamber_cells(height: int, width: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(2, height - 2)
        for col in range(2, width - 2)
    ]


def _dedupe(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    return list(dict.fromkeys(cells))


def _place(grid, cells: Iterable[tuple[int, int]], colors: Iterable[int]) -> None:
    cells = list(cells)
    colors = list(colors)
    if len(cells) != len(colors):
        raise AssertionError("seed plan length mismatch")
    if len(set(cells)) != len(cells):
        raise AssertionError("seed plan contains duplicate cells")
    for (row, col), color in zip(cells, colors):
        if grid[row][col] != 0:
            raise AssertionError("seed plan overlaps a wall or another seed")
        grid[row][col] = color


def _sample_seed_colors(ctx, count: int) -> list[int]:
    """Anchor canonical colors 2 and {3,4}, then add distinct broader colors."""
    secondary = ctx.draw_choice("canonical_secondary_color", (3, 4, 6, 7, 8, 9))
    remaining = [color for color in _EXTRA_COLORS if color != secondary]
    extras = ctx.draw_rng("extra_seed_colors").sample(remaining, count - 2)
    return [2, secondary, *extras]


def _perimeter_cells(height: int, width: int) -> list[tuple[int, int]]:
    return _dedupe(
        [(2, col) for col in range(2, width - 2)]
        + [(height - 3, col) for col in range(2, width - 2)]
        + [(row, 2) for row in range(3, height - 3)]
        + [(row, width - 3) for row in range(3, height - 3)]
    )


def _build_open_voronoi(height, width, colors, rng):
    grid = _framed_grid(height, width)
    # Preserve an open canonical chamber while guaranteeing a finite tie whose
    # smaller color is row-major later. This backs up tie_order when any one of
    # the six materialized pairs is rotated into the query slot.
    left = rng.choice(list(range(2, width - 4)))
    earlier = (2, left)
    later = (2, left + 2)
    extras = [(height - 3, col) for col in range(2, width - 2)]
    rng.shuffle(extras)
    _place(
        grid,
        [earlier, later, *extras[: len(colors) - 2]],
        [colors[1], colors[0], *colors[2:]],
    )
    return grid


def _detour_wall_col(width: int, rng) -> int:
    choices = list(range(4, width - 4))
    if not choices:
        raise ValueError(f"width {width} cannot hold the detour profile")
    return rng.choice(choices)


def _build_wall_detour(height, width, colors, rng):
    grid = _framed_grid(height, width)
    wall_col = _detour_wall_col(width, rng)
    gap_at_bottom = bool(rng.getrandbits(1))
    if gap_at_bottom:
        # Attach to the top frame, leaving exactly one bottom gap.
        for row in range(2, height - 3):
            grid[row][wall_col] = 5
        witness_row = 2
        left_seed = (height - 3, rng.choice(list(range(2, wall_col - 1)) or [2]))
        right_seed = (2, wall_col + 1)
    else:
        # Vertical reflection: attach to the bottom frame and leave a top gap.
        for row in range(3, height - 2):
            grid[row][wall_col] = 5
        witness_row = height - 3
        left_seed = (2, rng.choice(list(range(2, wall_col - 1)) or [2]))
        right_seed = (height - 3, wall_col + 1)

    # Extras stay on the right perimeter. At
    # q=(witness_row, wall_col-1), every one remains farther by wall-aware
    # distance than left_seed, while right_seed is closer in raw Manhattan.
    right_perimeter = _dedupe(
        [(2, col) for col in range(wall_col + 1, width - 2)]
        + [(row, width - 3) for row in range(3, height - 3)]
        + [(height - 3, col) for col in range(wall_col + 1, width - 2)]
    )
    right_perimeter = [
        cell
        for cell in right_perimeter
        if grid[cell[0]][cell[1]] == 0 and cell != right_seed
    ]
    rng.shuffle(right_perimeter)
    _place(
        grid,
        [left_seed, right_seed, *right_perimeter[: len(colors) - 2]],
        colors,
    )
    return grid


def _build_tie_order(height, width, colors, rng):
    grid = _framed_grid(height, width)
    split = rng.choice(list(range(3, height - 3)))
    for col in range(1, width - 1):
        grid[split][col] = 5

    seed_row = rng.choice((2, split - 1))
    pairs = [
        (left, right)
        for left in range(2, width - 4)
        for right in range(left + 2, width - 2)
        if (right - left) % 2 == 0
    ]
    left, right = rng.choice(pairs)
    # Earlier row-major seed deliberately has the larger color. At the midpoint,
    # the canonical rule chooses color 2 while the canonical-fitting shortcut
    # chooses the earlier larger color.
    secondary = colors[1]
    extra_colors = colors[2:]
    bottom = [
        (row, col)
        for row in range(split + 1, height - 2)
        for col in range(2, width - 2)
        if row in {split + 1, height - 3} or col in {2, width - 3}
    ]
    rng.shuffle(bottom)
    _place(
        grid,
        [(seed_row, left), (seed_row, right), *bottom[: len(extra_colors)]],
        [secondary, 2, *extra_colors],
    )
    return grid


def _seedless_walls(width: int, rng) -> tuple[int, int]:
    if width >= 11:
        # Leave a three-column seeded room on the left. It can hold a partial
        # detour wall while the columns between the full walls remain seedless.
        return 5, width - 4
    pairs = [
        (left, right)
        for left in range(3, width - 4)
        for right in range(left + 3, width - 3)
        if left - 1 >= 2 and width - right - 2 >= 1
    ]
    if not pairs:
        # The 10-column boundary has one canonical constructive pair.
        return 3, width - 4
    return rng.choice(pairs)


def _build_seedless_rooms(height, width, colors, rng):
    grid = _framed_grid(height, width)
    left_wall, right_wall = _seedless_walls(width, rng)
    for row in range(1, height - 1):
        grid[row][left_wall] = 5
        grid[row][right_wall] = 5

    left_cells = [(row, 2) for row in range(2, height - 2)]
    right_cells = [(row, width - 3) for row in range(2, height - 2)]

    if left_wall >= 5 and len(colors) >= 3:
        # Attach a partial wall to one horizontal frame and leave a one-cell gap
        # at the other. The first and third seeds occupy opposite corridors:
        # component-restricted Manhattan distance prefers the third seed near
        # the closed end, while wall-aware BFS reaches the first seed directly.
        detour_col = left_wall - 2
        gap_at_bottom = bool(rng.getrandbits(1))
        if gap_at_bottom:
            for row in range(2, height - 3):
                grid[row][detour_col] = 5
            first = (height - 3, 2)
            third = (2, left_wall - 1)
        else:
            for row in range(3, height - 2):
                grid[row][detour_col] = 5
            first = (2, 2)
            third = (height - 3, left_wall - 1)
        second = rng.choice(right_cells)
        # Keep all later colors in the separate right component. Extra seeds in
        # either left corridor can erase the intended two-seed distance reversal.
        candidates = [cell for cell in right_cells if cell != second]
        rng.shuffle(candidates)
        _place(
            grid,
            [first, second, third, *candidates[: len(colors) - 3]],
            colors,
        )
    else:
        first = rng.choice(left_cells)
        second = rng.choice(right_cells)
        extras = [cell for cell in left_cells + right_cells if cell not in {first, second}]
        rng.shuffle(extras)
        _place(grid, [first, second, *extras[: len(colors) - 2]], colors)
    return grid


def _mixed_splits(height: int, width: int, rng) -> tuple[int, int]:
    rows = list(range(4, height - 3)) or [height - 4]
    cols = list(range(4, width - 4)) or [width // 2]
    return rng.choice(rows), rng.choice(cols)


def _build_mixed_rooms(height, width, colors, rng):
    grid = _framed_grid(height, width)
    split_row, split_col = _mixed_splits(height, width, rng)
    for col in range(1, width - 1):
        grid[split_row][col] = 5
    for row in range(1, height - 1):
        grid[row][split_col] = 5

    rooms = [
        [(row, col) for row in range(2, split_row) for col in range(2, split_col)],
        [(row, col) for row in range(2, split_row) for col in range(split_col + 1, width - 2)],
        [(row, col) for row in range(split_row + 1, height - 2) for col in range(2, split_col)],
        [
            (row, col)
            for row in range(split_row + 1, height - 2)
            for col in range(split_col + 1, width - 2)
        ],
    ]
    mandatory = []
    for room in rooms:
        # Every room touches the cross/frame wall network; pick a boundary cell.
        candidates = [
            cell
            for cell in room
            if any(grid[cell[0] + dr][cell[1] + dc] == 5 for dr, dc in _DIR4)
        ]
        mandatory.append(rng.choice(candidates or room))
    all_touching = [
        cell
        for cell in _chamber_cells(height, width)
        if grid[cell[0]][cell[1]] == 0
        and any(grid[cell[0] + dr][cell[1] + dc] == 5 for dr, dc in _DIR4)
    ]
    chosen = mandatory[: min(len(colors), 4)]
    extras = [cell for cell in all_touching if cell not in chosen]
    rng.shuffle(extras)
    chosen.extend(extras[: len(colors) - len(chosen)])
    _place(grid, chosen, colors)
    return grid


_BUILDERS = {
    "open_voronoi": _build_open_voronoi,
    "wall_detour": _build_wall_detour,
    "tie_order": _build_tie_order,
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
    profile = _draw_exact_choice(ctx, "texture", scheduled_profile, SCHEDULE_PROFILES)
    scheduled_h, scheduled_w, scheduled_n = _scheduled_axes(profile, difficulty)
    height = _draw_exact_int(ctx, "grid_h", scheduled_h, 8, 10)
    width = _draw_exact_int(ctx, "grid_w", scheduled_w, 10, 12)
    n_seeds = _draw_exact_int(ctx, "n_seeds", scheduled_n, 2, 5)
    colors = _sample_seed_colors(ctx, n_seeds)
    grid = _BUILDERS[profile](height, width, colors, ctx.draw_rng("layout"))
    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise AssertionError("constructive generator emitted invalid grid: " + "; ".join(findings))
    return grid


def _shape_error(grid) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list"
    if not all(isinstance(row, list) and row for row in grid):
        return "every row must be a nonempty list"
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return "ragged grid"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer ARC colors 0..9"
    return None


def _nonzero_component_count(grid) -> int:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    count = 0
    while unseen:
        count += 1
        queue = [unseen.pop()]
        for row, col in queue:
            for dr, dc in _DIR4:
                point = (row + dr, col + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
    return count


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical-style input grammar emitted by this generator."""
    del difficulty, meta
    error = _shape_error(grid)
    if error:
        return [error]
    height, width = len(grid), len(grid[0])
    findings: list[str] = []
    if not (8 <= height <= 10):
        findings.append(f"height {height} outside 8..10")
    if not (10 <= width <= 12):
        findings.append(f"width {width} outside 10..12")
    if findings:
        return findings

    outer = (
        all(value == 0 for value in grid[0])
        and all(value == 0 for value in grid[-1])
        and all(row[0] == 0 and row[-1] == 0 for row in grid)
    )
    if not outer:
        findings.append("outer border must be all 0")

    inner = (
        all(grid[1][col] == 5 and grid[height - 2][col] == 5 for col in range(1, width - 1))
        and all(grid[row][1] == 5 and grid[row][width - 2] == 5 for row in range(1, height - 1))
    )
    if not inner:
        findings.append("one-cell inset chamber frame must be all 5")

    seeds = [
        value
        for row in grid
        for value in row
        if value not in (0, 5)
    ]
    if not (2 <= len(seeds) <= 5):
        findings.append(f"expected 2..5 seed cells, found {len(seeds)}")
    if len(set(seeds)) != len(seeds):
        findings.append("seed colors must be distinct one-cell markers")
    if not any(
        grid[row][col] == 0
        for row in range(2, height - 2)
        for col in range(2, width - 2)
    ):
        findings.append("chamber must contain at least one open cell")
    if _nonzero_component_count(grid) != 1:
        findings.append("wall frame and all seeds must form one nonzero component")
    return findings


def strict_canonical_like(grid):
    return self_check(grid)


def _seed_positions(grid) -> list[tuple[int, int, int]]:
    return [
        (value, row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]


def _distance_map(grid, start: tuple[int, int]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    infinity = height * width + 1
    distance = [[infinity] * width for _ in range(height)]
    row, col = start
    distance[row][col] = 0
    queue = deque([(row, col)])
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


def _seed_maps(grid):
    return [
        (color, row, col, _distance_map(grid, (row, col)))
        for color, row, col in _seed_positions(grid)
    ]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket authority."""
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    height, width = len(grid), len(grid[0])
    infinity = height * width + 1
    maps = _seed_maps(grid)
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5:
                output[row][col] = 5
                continue
            candidates = [
                (distance[row][col], color)
                for color, _, _, distance in maps
                if distance[row][col] < infinity
            ]
            output[row][col] = min(candidates)[1] if candidates else 0
    return output


def _full_chamber_rows(grid) -> list[int]:
    height, width = len(grid), len(grid[0])
    return [
        row
        for row in range(2, height - 2)
        if all(grid[row][col] == 5 for col in range(1, width - 1))
    ]


def _full_chamber_cols(grid) -> list[int]:
    height, width = len(grid), len(grid[0])
    return [
        col
        for col in range(2, width - 2)
        if all(grid[row][col] == 5 for row in range(1, height - 1))
    ]


def _observe_texture(grid) -> str:
    height, width = len(grid), len(grid[0])
    full_rows = _full_chamber_rows(grid)
    full_cols = _full_chamber_cols(grid)
    explained = {
        (row, col)
        for row in full_rows
        for col in range(2, width - 2)
    } | {
        (row, col)
        for col in full_cols
        for row in range(2, height - 2)
    }
    internal_walls = {
        (row, col)
        for row in range(2, height - 2)
        for col in range(2, width - 2)
        if grid[row][col] == 5
    }
    signature = (len(full_rows), len(full_cols), bool(internal_walls - explained))
    textures = {
        (0, 0, False): "open_voronoi",
        (0, 0, True): "wall_detour",
        (1, 0, False): "tie_order",
        (0, 2, False): "seedless_rooms",
        (0, 2, True): "seedless_rooms",
        (1, 1, False): "mixed_rooms",
    }
    if signature not in textures:
        raise ValueError(
            "wall topology is not a declared texture: "
            f"full_rows={full_rows}, full_cols={full_cols}, "
            f"extra={len(internal_walls - explained)}"
        )
    return textures[signature]


def observe_overrides(grid) -> dict[str, int | str]:
    findings = self_check(grid)
    if findings:
        raise ValueError("grid is outside task grammar: " + "; ".join(findings))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_seeds": len(_seed_positions(grid)),
        "texture": _observe_texture(grid),
    }


# ---------------------------------------------------------------------------
# Semantic witnesses and plausible wrong-rule competitors
# ---------------------------------------------------------------------------


def _rival_row_major_tie_break(grid):
    maps = _seed_maps(grid)  # row-major seed order from _seed_positions
    height, width = len(grid), len(grid[0])
    infinity = height * width + 1
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5:
                output[row][col] = 5
                continue
            best_distance = min((dist[row][col] for _, _, _, dist in maps), default=infinity)
            winner = next(
                (color for color, _, _, dist in maps if dist[row][col] == best_distance),
                0,
            )
            output[row][col] = winner if best_distance < infinity else 0
    return output


def _nonwall_components(grid) -> tuple[list[set[tuple[int, int]]], dict[tuple[int, int], int]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 5
    }
    components = []
    owner = {}
    while unseen:
        start = unseen.pop()
        component = {start}
        queue = [start]
        for row, col in queue:
            for dr, dc in _DIR4:
                point = (row + dr, col + dc)
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        index = len(components)
        for point in component:
            owner[point] = index
        components.append(component)
    return components, owner


def _rival_component_manhattan(grid):
    components, owner = _nonwall_components(grid)
    del components
    seeds = _seed_positions(grid)
    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 5:
                continue
            candidates = [
                (abs(row - sr) + abs(col - sc), color)
                for color, sr, sc in seeds
                if owner[(row, col)] == owner[(sr, sc)]
            ]
            output[row][col] = min(candidates)[1] if candidates else 0
    return output


def _rival_global_manhattan(grid):
    seeds = _seed_positions(grid)
    output = [row[:] for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 5:
                continue
            candidates = [
                (abs(row - sr) + abs(col - sc), color)
                for color, sr, sc in seeds
            ]
            output[row][col] = min(candidates)[1] if candidates else 0
    return output


def _rival_first_two_seeds_only(grid):
    seeds = _seed_positions(grid)[:2]
    height, width = len(grid), len(grid[0])
    infinity = height * width + 1
    maps = [
        (color, _distance_map(grid, (row, col)))
        for color, row, col in seeds
    ]
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5:
                continue
            candidates = [
                (distance[row][col], color)
                for color, distance in maps
                if distance[row][col] < infinity
            ]
            output[row][col] = min(candidates)[1] if candidates else 0
    return output


def _has_wall_aware_distance(grid) -> bool:
    return rule_mirror(grid) != _rival_component_manhattan(grid)


def _has_smaller_color_tie(grid) -> bool:
    canonical = rule_mirror(grid)
    rival = _rival_row_major_tie_break(grid)
    if canonical == rival:
        return False
    maps = _seed_maps(grid)
    infinity = len(grid) * len(grid[0]) + 1
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            finite = [
                (dist[row][col], color, index)
                for index, (color, _, _, dist) in enumerate(maps)
                if dist[row][col] < infinity
            ]
            if not finite:
                continue
            best = min(distance for distance, _, _ in finite)
            tied = [(color, index) for distance, color, index in finite if distance == best]
            if len(tied) >= 2:
                smaller = min(color for color, _ in tied)
                earlier = min(tied, key=lambda item: item[1])[0]
                if smaller != earlier and canonical[row][col] == smaller and rival[row][col] == earlier:
                    return True
    return False


def _has_seedless_component(grid) -> bool:
    components, _ = _nonwall_components(grid)
    height, width = len(grid), len(grid[0])
    for component in components:
        values = {grid[row][col] for row, col in component}
        touches_outer = any(
            row in {0, height - 1} or col in {0, width - 1}
            for row, col in component
        )
        if not touches_outer and 0 in values and not any(value not in (0, 5) for value in values):
            return True
    return False


def _has_all_seed_colors_compete(grid) -> bool:
    return len(_seed_positions(grid)) >= 3 and rule_mirror(grid) != _rival_first_two_seeds_only(grid)


SEMANTIC_WITNESSES = {
    "wall_aware_distance": _has_wall_aware_distance,
    "smaller_color_wins_finite_ties": _has_smaller_color_tie,
    "seedless_components_stay_zero": _has_seedless_component,
    "all_seed_colors_compete": _has_all_seed_colors_compete,
}

SEMANTIC_RIVALS = {
    "component_manhattan": _rival_component_manhattan,
    "row_major_tie_break": _rival_row_major_tie_break,
    "global_manhattan": _rival_global_manhattan,
    "first_two_seeds_only": _rival_first_two_seeds_only,
}

WITNESS_RIVALS = {
    "wall_aware_distance": ["component_manhattan"],
    "smaller_color_wins_finite_ties": ["row_major_tie_break"],
    "seedless_components_stay_zero": ["global_manhattan"],
    "all_seed_colors_compete": ["first_two_seeds_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# This rival fits all three canonical pairs, including the held-out labelled
# pair, because the smaller-colored seed is also row-major earlier every time.
CANONICAL_SHORTCUTS = {
    "row_major_tie_break": _rival_row_major_tie_break,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a labelled lesson where a declared rival survives the demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with wall-aware Voronoi")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with wall-aware Voronoi")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output")
            for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
