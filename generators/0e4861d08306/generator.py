"""Semantic generator for custom ARC task 36f9e4ca / 0e4861d08306.

The first red seed floods through its 4-connected red/blue component.  Every
reachable blue cell turns green, while azure walls and disconnected blue or
later-red components remain unchanged.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "0e4861d08306"
VERSION = "2.0.0"
TASK_ID = "0e4861d08306"
RULE_HASH = "08735d91bff4"
SUMMARY = (
    "Flood from the reading-order-first red(2) seed through 4-connected "
    "blue/red cells, recoloring reached blue(1) cells green(3). Azure(8) "
    "walls block the flood and disconnected blue cells remain unchanged."
)
INVARIANTS = [
    "black is modal and the exact input palette is {0,1,2,8}",
    "the first red seed reaches at least four blue cells by 4-connectivity",
    "at least two blue cells remain unreachable and unchanged",
    "an azure wall cell directly separates reached and unreachable walkable cells",
    "generalized scenes have a later disconnected red seed with blue support",
    "green 3 is output-only and the transformation is never identity",
]
EXAMPLES_NEEDED = 3
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng authored|generalized (3:1)",
        "valid": "authored|generalized",
        "doc": (
            "authored has the singular red seed stated by the task; generalized "
            "adds a later disconnected red seed to expose first-seed selection"
        ),
    },
}

BACKGROUND = 0
BLUE = 1
RED = 2
GREEN = 3
WALL = 8
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
_BANDS = {
    "easy": {
        "dims": (9, 13), "reached": (5, 10), "blocked": (3, 7),
        "decoys": (1, 2), "extra_walls": (0, 1),
    },
    "medium": {
        "dims": (14, 20), "reached": (10, 24), "blocked": (5, 13),
        "decoys": (1, 3), "extra_walls": (1, 2),
    },
    "hard": {
        "dims": (21, 30), "reached": (22, 52), "blocked": (8, 22),
        "decoys": (2, 5), "extra_walls": (2, 4),
    },
}
_TOPOLOGIES = ("walk", "branch", "compact")


def _copy_grid(grid):
    return [list(row) for row in grid]


def _walkable_region(grid, start):
    height, width = len(grid), len(grid[0])
    seen = {start}
    stack = [start]
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            candidate = row + dr, col + dc
            if not (
                0 <= candidate[0] < height
                and 0 <= candidate[1] < width
                and candidate not in seen
                and grid[candidate[0]][candidate[1]] in (BLUE, RED)
            ):
                continue
            seen.add(candidate)
            stack.append(candidate)
    return frozenset(seen)


def _components_for_color(grid, color):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    result = []
    while remaining:
        start = min(remaining)
        cells = {start}
        stack = [start]
        remaining.remove(start)
        while stack:
            row, col = stack.pop()
            for dr, dc in _CARDINAL:
                candidate = row + dr, col + dc
                if candidate in remaining:
                    remaining.remove(candidate)
                    cells.add(candidate)
                    stack.append(candidate)
        result.append(frozenset(cells))
    return tuple(result)


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return {"errors": ["cells must be integer ARC colors 0..9"], "facts": None}

    height = len(grid)
    if not (9 <= height <= 30 and 9 <= width <= 30):
        errors.append("dimensions must lie in 9..30")
    palette = {value for row in grid for value in row}
    if palette != {BACKGROUND, BLUE, RED, WALL}:
        errors.append(f"input palette must be exactly [0, 1, 2, 8], found {sorted(palette)}")
    counts = Counter(value for row in grid for value in row)
    if counts[BACKGROUND] <= max(
        (count for color, count in counts.items() if color != BACKGROUND), default=0
    ):
        errors.append("black must be the modal background")

    seeds = tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == RED
    )
    if len(seeds) not in (1, 2):
        errors.append(f"expected one or two red seeds, found {len(seeds)}")
    if not seeds:
        return {"errors": errors, "facts": None}
    reached = _walkable_region(grid, seeds[0])
    reached_blue = frozenset(
        position for position in reached if grid[position[0]][position[1]] == BLUE
    )
    all_blue = frozenset(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == BLUE
    )
    unreachable_blue = all_blue - reached_blue
    if len(reached_blue) < 4:
        errors.append(f"first seed must reach at least four blue cells, found {len(reached_blue)}")
    if len(unreachable_blue) < 2:
        errors.append(
            f"at least two blue negative witnesses must remain unreachable, found {len(unreachable_blue)}"
        )

    relevant_walls = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != WALL:
                continue
            for (dr1, dc1), (dr2, dc2) in (
                (((0, -1), (0, 1))), (((-1, 0), (1, 0)))
            ):
                first = row + dr1, col + dc1
                second = row + dr2, col + dc2
                if (
                    (first in reached and second in unreachable_blue)
                    or (second in reached and first in unreachable_blue)
                ):
                    relevant_walls.append((row, col))
                    break
    if not relevant_walls:
        errors.append("an azure wall must directly separate reached and unreachable cells")

    if len(seeds) == 2:
        if seeds[1] in reached:
            errors.append("the later red seed must be disconnected from the first")
        if not any(
            (seeds[1][0] + dr, seeds[1][1] + dc) in unreachable_blue
            for dr, dc in _CARDINAL
        ):
            errors.append("the later red seed must have adjacent unreachable blue support")

    output = _copy_grid(grid)
    for row, col in reached_blue:
        output[row][col] = GREEN
    if output == [list(row) for row in grid]:
        errors.append("the transformation must not be identity")

    facts = {
        "height": height,
        "width": width,
        "palette": frozenset(palette),
        "seeds": seeds,
        "seed_count": len(seeds),
        "reached": reached,
        "reached_blue": reached_blue,
        "unreachable_blue": unreachable_blue,
        "reached_blue_count": len(reached_blue),
        "unreachable_blue_count": len(unreachable_blue),
        "unreachable_components": _components_for_color(grid, BLUE),
        "wall_count": counts[WALL],
        "relevant_wall_count": len(set(relevant_walls)),
        "output": output,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return "authored" if analysis["facts"]["seed_count"] == 1 else "generalized"


def observe_overrides(grid):
    family = canonical_profile_signature(grid)
    return {} if family == "invalid" else {"scene_family": family}


def _grow_region(start, target_size, allowed, topology, rng):
    cells = {start}
    active = [start]
    last = start
    while len(cells) < target_size:
        candidates = []
        sources = [last] if topology == "walk" else list(active)
        for row, col in sources:
            for dr, dc in _CARDINAL:
                candidate = row + dr, col + dc
                if candidate not in cells and allowed(candidate):
                    candidates.append(candidate)
        if not candidates and topology == "walk":
            for row, col in active:
                for dr, dc in _CARDINAL:
                    candidate = row + dr, col + dc
                    if candidate not in cells and allowed(candidate):
                        candidates.append(candidate)
        if not candidates:
            return None
        if topology == "compact":
            scores = {
                candidate: sum(
                    (candidate[0] + dr, candidate[1] + dc) in cells
                    for dr, dc in _CARDINAL
                )
                for candidate in candidates
            }
            best = max(scores.values())
            candidates = [candidate for candidate in candidates if scores[candidate] == best]
        chosen = rng.choice(candidates)
        cells.add(chosen)
        active.append(chosen)
        last = chosen
    return frozenset(cells)


def _rect_clear(grid, top, left, height, width, *, moat=True):
    grid_height, grid_width = len(grid), len(grid[0])
    if not (0 <= top <= grid_height - height and 0 <= left <= grid_width - width):
        return False
    if not moat:
        return all(
            grid[row][col] == BACKGROUND
            for row in range(top, top + height)
            for col in range(left, left + width)
        )
    return all(
        grid[row][col] == BACKGROUND
        for row in range(max(0, top - 1), min(grid_height, top + height + 1))
        for col in range(max(0, left - 1), min(grid_width, left + width + 1))
    )


def _paint_rect(grid, top, left, height, width, color):
    for row in range(top, top + height):
        for col in range(left, left + width):
            grid[row][col] = color


def _place_blue_decoy(grid, rng):
    for _ in range(200):
        horizontal = rng.choice((False, True))
        length = rng.randint(1, 3)
        height, width = (1, length) if horizontal else (length, 1)
        top = rng.randint(0, len(grid) - height)
        left = rng.randint(0, len(grid[0]) - width)
        if _rect_clear(grid, top, left, height, width):
            _paint_rect(grid, top, left, height, width, BLUE)
            return True
    return False


def _place_wall_segment(grid, rng):
    for _ in range(200):
        horizontal = rng.choice((False, True))
        length = rng.randint(2, min(7, len(grid) - 2, len(grid[0]) - 2))
        height, width = (1, length) if horizontal else (length, 1)
        top = rng.randint(0, len(grid) - height)
        left = rng.randint(0, len(grid[0]) - width)
        if _rect_clear(grid, top, left, height, width):
            _paint_rect(grid, top, left, height, width, WALL)
            return True
    return False


def _construct_scene(rng, band, family):
    bounds = _BANDS[band]
    for _attempt in range(1_200):
        height = rng.randint(*bounds["dims"])
        width = rng.randint(*bounds["dims"])
        grid = full_grid(height, width, BACKGROUND)
        vertical = rng.choice((False, True))
        if vertical:
            wall_col = rng.randint(max(3, width // 3), min(width - 4, 2 * width // 3))
            wall_length = rng.randint(3, min(height - 4, max(4, height // 2)))
            wall_top = rng.randint(2, height - wall_length - 2)
            wall_mid = wall_top + wall_length // 2
            wall_cells = [(row, wall_col) for row in range(wall_top, wall_top + wall_length)]
            left_side = rng.choice((False, True))
            first_start = (wall_mid, wall_col - 1 if left_side else wall_col + 1)
            second_start = (wall_mid, wall_col + 1 if left_side else wall_col - 1)

            def first_allowed(position):
                row, col = position
                return (
                    1 <= row < height - 1
                    and (1 <= col < wall_col if left_side else wall_col < col < width - 1)
                    and grid[row][col] == BACKGROUND
                )

            def second_allowed(position):
                row, col = position
                return (
                    1 <= row < height - 1
                    and (wall_col < col < width - 1 if left_side else 1 <= col < wall_col)
                    and grid[row][col] == BACKGROUND
                )
        else:
            wall_row = rng.randint(max(3, height // 3), min(height - 4, 2 * height // 3))
            wall_length = rng.randint(3, min(width - 4, max(4, width // 2)))
            wall_left = rng.randint(2, width - wall_length - 2)
            wall_mid = wall_left + wall_length // 2
            wall_cells = [(wall_row, col) for col in range(wall_left, wall_left + wall_length)]
            upper_side = rng.choice((False, True))
            first_start = (wall_row - 1 if upper_side else wall_row + 1, wall_mid)
            second_start = (wall_row + 1 if upper_side else wall_row - 1, wall_mid)

            def first_allowed(position):
                row, col = position
                return (
                    (1 <= row < wall_row if upper_side else wall_row < row < height - 1)
                    and 1 <= col < width - 1
                    and grid[row][col] == BACKGROUND
                )

            def second_allowed(position):
                row, col = position
                return (
                    (wall_row < row < height - 1 if upper_side else 1 <= row < wall_row)
                    and 1 <= col < width - 1
                    and grid[row][col] == BACKGROUND
                )

        for row, col in wall_cells:
            grid[row][col] = WALL
        topology = rng.choice(_TOPOLOGIES)
        reached_target = rng.randint(*bounds["reached"])
        blocked_target = rng.randint(*bounds["blocked"])
        first_region = _grow_region(
            first_start, reached_target + 1, first_allowed, topology, rng
        )
        second_region = _grow_region(
            second_start, blocked_target, second_allowed, rng.choice(_TOPOLOGIES), rng
        )
        if first_region is None or second_region is None:
            continue
        for row, col in first_region | second_region:
            grid[row][col] = BLUE
        first_seed = min(first_region) if family == "generalized" else rng.choice(tuple(first_region))
        grid[first_seed[0]][first_seed[1]] = RED
        if family == "generalized":
            later_candidates = [position for position in second_region if position > first_seed]
            if not later_candidates:
                continue
            second_seed = max(later_candidates)
            grid[second_seed[0]][second_seed[1]] = RED

        placed = True
        for _ in range(rng.randint(*bounds["decoys"])):
            if not _place_blue_decoy(grid, rng):
                placed = False
                break
        for _ in range(rng.randint(*bounds["extra_walls"])):
            if not _place_wall_segment(grid, rng):
                placed = False
                break
        if not placed:
            continue
        analysis = _analyze(grid)
        if analysis["errors"]:
            continue
        observed = "authored" if analysis["facts"]["seed_count"] == 1 else "generalized"
        if observed == family:
            return grid
    raise RuntimeError(f"could not construct a valid {band}/{family} flood scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice(
        "scene_family", ("authored", "authored", "authored", "generalized")
    )
    band = "medium" if difficulty in (None, "default") else difficulty
    return _construct_scene(ctx.draw_rng("layout"), band, family)
