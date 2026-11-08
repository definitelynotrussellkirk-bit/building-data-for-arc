"""Generator for arc_additional_puzzle_bank_volume17:H118.

The task is a two-source shortest-path Voronoi partition.  Gray(5) cells are
walls.  For every black(0) cell reachable from both seeds, compare the
4-connected BFS distance to the red(2) and green(3) seeds: paint cyan(8) when
red is nearer, yellow(4) when green is nearer, and leave equal-distance cells
black.  Seeds and walls are unchanged.

The previous generator mostly emitted open fields or one-cell walls, so a
Manhattan-distance shortcut solved almost every generated lesson.  Version
3.0.0 uses a fixed four-example teaching cadence: one open field followed by
three connected maze profiles.  Every maze draw is accepted only when walls
create an observable BFS-vs-Manhattan disagreement while both color regions
and a nontrivial tie boundary remain visible.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3c05b058b793"
VERSION = "3.0.0"
TASK_ID = "3c05b058b793"
RULE_HASH = "58404f8e7c2f"  # comment-stripped/whitespace-normalized canonical rule

SUMMARY = (
    "A black(0) grid contains exactly one red(2) seed, one green(3) seed, "
    "and optionally structured gray(5) walls. Run 4-connected shortest-path "
    "BFS through every non-wall cell from both seeds. Recolor each black cell "
    "cyan(8) when red is closer, yellow(4) when green is closer, and leave it "
    "black on an equal-distance tie. Seeds and walls remain unchanged. Normal "
    "lessons alternate an open witness with wall mazes whose detours make the "
    "BFS answer differ from a Manhattan-distance shortcut."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and the input palette is a subset of {0,2,3,5}",
    "exactly one color-2 seed and one color-3 seed, separated by at least 3 cells",
    "every non-wall cell is reachable from both seeds",
    "both nearer-seed branches and a visible equal-distance tie boundary occur",
    "when walls are present on generated draws, they form a multi-cell obstacle and alter at least one BFS-vs-Manhattan classification",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "easy 5..8 | medium 8..12 | hard 11..16 | unset 7..12",
        "valid": "5..16",
    },
    "grid_w": {
        "type": "int",
        "default": "easy 7..11 | medium 10..15 | hard 14..20 | unset 9..16",
        "valid": "7..20",
    },
}

_BAND_H = {
    "easy": (5, 8),
    "medium": (8, 12),
    "hard": (11, 16),
    None: (7, 12),
}
_BAND_W = {
    "easy": (7, 11),
    "medium": (10, 15),
    "hard": (14, 20),
    None: (9, 16),
}
_VALID_H = (5, 16)
_VALID_W = (7, 20)
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_ALLOWED = {0, 2, 3, 5}


def _validate_request(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, (lo, hi) in (("grid_h", _VALID_H), ("grid_w", _VALID_W)):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _draw_int_axis(ctx, label: str, band: tuple[int, int], valid: tuple[int, int]) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, *valid)
    return ctx.draw_int(label, *band)


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        component = {start}
        queue = [start]
        remaining.remove(start)
        while queue:
            r, c = queue.pop()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(component)
    return result


def _bfs_distances(
    height: int,
    width: int,
    walls: set[tuple[int, int]],
    start: tuple[int, int],
) -> dict[tuple[int, int], int]:
    distances = {start: 0}
    queue: deque[tuple[int, int]] = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            nr, nc = r + dr, c + dc
            point = (nr, nc)
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if point in walls or point in distances:
                continue
            distances[point] = distances[(r, c)] + 1
            queue.append(point)
    return distances


def _semantic_facts(
    height: int,
    width: int,
    walls: set[tuple[int, int]],
    seed_a: tuple[int, int],
    seed_b: tuple[int, int],
) -> dict[str, Any]:
    da = _bfs_distances(height, width, walls, seed_a)
    db = _bfs_distances(height, width, walls, seed_b)
    branch_counts: Counter[int] = Counter()
    disagreement = 0
    detour_cells = 0
    unreachable = 0
    for r in range(height):
        for c in range(width):
            point = (r, c)
            if point in walls or point == seed_a or point == seed_b:
                continue
            if point not in da or point not in db:
                unreachable += 1
                continue
            if da[point] < db[point]:
                relation = 8
            elif db[point] < da[point]:
                relation = 4
            else:
                relation = 0
            branch_counts[relation] += 1

            manhattan_a = abs(r - seed_a[0]) + abs(c - seed_a[1])
            manhattan_b = abs(r - seed_b[0]) + abs(c - seed_b[1])
            if manhattan_a < manhattan_b:
                manhattan_relation = 8
            elif manhattan_b < manhattan_a:
                manhattan_relation = 4
            else:
                manhattan_relation = 0
            disagreement += relation != manhattan_relation
            detour_cells += da[point] > manhattan_a or db[point] > manhattan_b

    wall_components = _components(walls)
    return {
        "dist_a": da,
        "dist_b": db,
        "seed_distance": da.get(seed_b),
        "count_8": branch_counts[8],
        "count_4": branch_counts[4],
        "count_tie": branch_counts[0],
        "unreachable_count": unreachable,
        "manhattan_disagreement_count": disagreement,
        "detour_cell_count": detour_cells,
        "wall_count": len(walls),
        "wall_component_sizes": tuple(sorted((len(c) for c in wall_components), reverse=True)),
    }


def _transform_walls(
    walls: Iterable[tuple[int, int]],
    height: int,
    width: int,
    transform: str,
) -> set[tuple[int, int]]:
    result = set()
    for r, c in walls:
        if transform in {"flip_v", "flip_both"}:
            r = height - 1 - r
        if transform in {"flip_h", "flip_both"}:
            c = width - 1 - c
        result.add((r, c))
    return result


def _wall_profile(height: int, width: int, profile: str) -> set[tuple[int, int]]:
    if profile == "open":
        return set()

    walls: set[tuple[int, int]] = set()
    if profile == "horizontal":
        row = max(1, min(height - 2, height // 2))
        left = max(1, width // 5)
        right = min(width - 2, width - 1 - width // 5)
        gap = max(left + 1, min(right - 1, width // 2))
        span = right - left + 1
        walls.update(
            (row, c)
            for c in range(left, right + 1)
            if span <= 3 or c != gap
        )
    elif profile == "vertical":
        column = max(1, min(width - 2, width // 2))
        top = max(1, height // 5)
        bottom = min(height - 2, height - 1 - height // 5)
        gap = max(top + 1, min(bottom - 1, height // 2))
        span = bottom - top + 1
        walls.update(
            (r, column)
            for r in range(top, bottom + 1)
            if span <= 3 or r != gap
        )
    elif profile == "parallel":
        left_column = max(1, width // 3)
        right_column = min(width - 2, (2 * width) // 3)
        top, bottom = 1, height - 2
        upper_gap = max(top, min(bottom, height // 3))
        lower_gap = max(top, min(bottom, (2 * height) // 3))
        walls.update((r, left_column) for r in range(top, bottom + 1) if r != upper_gap)
        walls.update((r, right_column) for r in range(top, bottom + 1) if r != lower_gap)
    elif profile == "cross":
        row = max(1, min(height - 2, height // 2))
        column = max(1, min(width - 2, width // 2))
        second_gap = column + 1 if column + 1 < width - 1 else column - 1
        walls.update(
            (row, c)
            for c in range(1, width - 1)
            if c not in {column, second_gap}
        )
        walls.update((r, column) for r in range(1, row))
    else:
        raise ValueError(f"unknown wall profile: {profile}")
    return walls


def _profile_for(difficulty: str | None, sample_index: int, ctx) -> str:
    slot = sample_index % 4
    if slot == 0:
        return "open"
    if slot == 1:
        return "horizontal"
    if slot == 2:
        return "vertical"
    options = {
        "easy": ("horizontal", "vertical"),
        "medium": ("parallel", "cross"),
        "hard": ("parallel", "cross"),
        None: ("parallel", "cross"),
    }[difficulty]
    return ctx.draw_choice("fourth_profile", options)


def _choose_seed_pair(
    height: int,
    width: int,
    walls: set[tuple[int, int]],
    *,
    require_wall_disagreement: bool,
    rng,
) -> tuple[tuple[int, int], tuple[int, int], dict[str, Any]]:
    cells = [(r, c) for r in range(height) for c in range(width) if (r, c) not in walls]
    rng.shuffle(cells)
    minimum_region = max(2, (len(cells) - 2) // 10)
    minimum_ties = max(1, min(height, width) // 3)
    minimum_disagreement = max(1, (height * width) // 80)

    for seed_a in cells:
        candidates = list(cells)
        rng.shuffle(candidates)
        for seed_b in candidates[: min(120, len(candidates))]:
            if seed_a == seed_b:
                continue
            if abs(seed_a[0] - seed_b[0]) + abs(seed_a[1] - seed_b[1]) < 3:
                continue
            facts = _semantic_facts(height, width, walls, seed_a, seed_b)
            seed_distance = facts["seed_distance"]
            if seed_distance is None or seed_distance % 2:
                continue
            if facts["unreachable_count"]:
                continue
            if facts["count_8"] < minimum_region or facts["count_4"] < minimum_region:
                continue
            if facts["count_tie"] < minimum_ties:
                continue
            if require_wall_disagreement and (
                facts["manhattan_disagreement_count"] < minimum_disagreement
            ):
                continue
            return seed_a, seed_b, facts
    raise RuntimeError(
        f"could not construct a semantic {height}x{width} shortest-path scene "
        f"with {len(walls)} walls"
    )


def _analyze_grid(grid: list[list[int]]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty grid"], {}
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"], {}
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid contains a non-integer or out-of-range color")
    palette = {value for row in grid for value in row if type(value) is int}
    illegal = sorted(palette - _ALLOWED)
    if illegal:
        errors.append(f"unexpected input color(s): {illegal}")

    twos = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 2]
    threes = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 3]
    walls = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 5}
    if len(twos) != 1:
        errors.append(f"expected exactly 1 color-2 seed, found {len(twos)}")
    if len(threes) != 1:
        errors.append(f"expected exactly 1 color-3 seed, found {len(threes)}")
    if len(twos) != 1 or len(threes) != 1:
        return errors, {
            "grid_h": height,
            "grid_w": width,
            "palette": tuple(sorted(palette)),
            "wall_count": len(walls),
        }

    seed_a, seed_b = twos[0], threes[0]
    manhattan_separation = abs(seed_a[0] - seed_b[0]) + abs(seed_a[1] - seed_b[1])
    if manhattan_separation < 3:
        errors.append(f"seed separation must be at least 3, found {manhattan_separation}")
    facts = _semantic_facts(height, width, walls, seed_a, seed_b)
    facts.update(
        {
            "grid_h": height,
            "grid_w": width,
            "palette": tuple(sorted(palette)),
            "seed_a": seed_a,
            "seed_b": seed_b,
            "manhattan_seed_separation": manhattan_separation,
        }
    )
    if facts["seed_distance"] is None:
        errors.append("the two seeds are disconnected by walls")
    if facts["unreachable_count"]:
        errors.append(
            f"expected every non-wall cell reachable from both seeds, found {facts['unreachable_count']} unreachable"
        )
    if facts["count_8"] == 0:
        errors.append("no black cell is closer to the color-2 seed")
    if facts["count_4"] == 0:
        errors.append("no black cell is closer to the color-3 seed")
    if facts["count_tie"] == 0:
        errors.append("no equal-distance black tie cell is visible")
    return errors, facts


def profile_signature(grid: list[list[int]]) -> tuple[Any, ...]:
    """Linked rule-relevant signature used for canonical and generated audits."""
    errors, facts = _analyze_grid(grid)
    if errors:
        raise ValueError("invalid grid for profile signature: " + "; ".join(errors))
    a, b = facts["seed_a"], facts["seed_b"]
    if a[0] == b[0]:
        seed_relation = "same_row"
    elif a[1] == b[1]:
        seed_relation = "same_column"
    else:
        seed_relation = "diagonal"
    return (
        facts["grid_h"],
        facts["grid_w"],
        seed_relation,
        facts["manhattan_seed_separation"],
        facts["seed_distance"],
        facts["wall_count"],
        facts["wall_component_sizes"],
        facts["count_8"],
        facts["count_4"],
        facts["count_tie"],
        facts["manhattan_disagreement_count"],
        facts["unreachable_count"],
    )


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    errors, facts = _analyze_grid(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    return {"grid_h": facts["grid_h"], "grid_w": facts["grid_w"]}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes that hide or weaken the shortest-path teaching grammar."""
    errors, facts = _analyze_grid(grid)
    if errors:
        return errors
    canonical = bool(isinstance(meta, dict) and meta.get("canonical"))
    if canonical:
        return []

    height, width = facts["grid_h"], facts["grid_w"]
    if not _VALID_H[0] <= height <= _VALID_H[1]:
        errors.append(f"generated height must be in {_VALID_H[0]}..{_VALID_H[1]}, found {height}")
    if not _VALID_W[0] <= width <= _VALID_W[1]:
        errors.append(f"generated width must be in {_VALID_W[0]}..{_VALID_W[1]}, found {width}")

    open_cells = height * width - facts["wall_count"] - 2
    minimum_region = max(2, open_cells // 10)
    minimum_ties = max(1, min(height, width) // 3)
    if facts["count_8"] < minimum_region:
        errors.append(
            f"color-2-nearer region too small: {facts['count_8']} < {minimum_region}"
        )
    if facts["count_4"] < minimum_region:
        errors.append(
            f"color-3-nearer region too small: {facts['count_4']} < {minimum_region}"
        )
    if facts["count_tie"] < minimum_ties:
        errors.append(
            f"tie boundary too small: {facts['count_tie']} < {minimum_ties}"
        )
    if facts["wall_count"]:
        largest_component = max(facts["wall_component_sizes"], default=0)
        if largest_component < 2:
            errors.append("wallful generated scene has only isolated one-cell walls")
        minimum_disagreement = max(1, (height * width) // 80)
        if facts["manhattan_disagreement_count"] < minimum_disagreement:
            errors.append(
                "wallful generated scene does not visibly distinguish BFS from Manhattan distance"
            )
        if facts["wall_count"] > (height * width) // 3:
            errors.append("walls occupy more than one third of the grid")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_int_axis(ctx, "grid_h", _BAND_H[difficulty], _VALID_H)
    width = _draw_int_axis(ctx, "grid_w", _BAND_W[difficulty], _VALID_W)
    profile = _profile_for(difficulty, sample_index, ctx)
    walls = _wall_profile(height, width, profile)
    transform = ctx.draw_choice(
        "wall_transform", ("identity", "flip_h", "flip_v", "flip_both")
    )
    walls = _transform_walls(walls, height, width, transform)
    seed_a, seed_b, _ = _choose_seed_pair(
        height,
        width,
        walls,
        require_wall_disagreement=bool(walls),
        rng=ctx.draw_rng("seed_pair"),
    )

    grid = full_grid(height, width, 0)
    for r, c in walls:
        grid[r][c] = 5
    grid[seed_a[0]][seed_a[1]] = 2
    grid[seed_b[0]][seed_b[1]] = 3
    return grid
