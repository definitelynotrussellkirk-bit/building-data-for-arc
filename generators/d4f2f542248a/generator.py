"""Semantic generator for ARC task d4f2f542248a (bank H85).

Walls are gray 5, the red 2 cell is the start, and the green 3 cell is
the goal.  Paint a blank cell cyan 8 exactly when every shortest walk from
start to goal through non-wall cells passes through it.  The curriculum
contains the five complete official shortest-path structures plus explicit
unique-route, branching, bottleneck, dead-end, and disconnected-pocket
contrasts.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "d4f2f542248a"
TASK_ID = "d4f2f542248a"
VERSION = "2.0.0"
RULE_HASH = "de5e86ab7e23"
SUMMARY = "Mark each blank cell that lies on every shortest non-wall path from the red start to the green goal."
INVARIANTS = [
    "gray 5 cells are impassable walls and zero cells are traversable blanks",
    "there is exactly one red 2 start and one green 3 goal",
    "the outer border is entirely wall and the endpoints are connected",
    "a cyan 8 is added only to a blank cell on every shortest start-goal path",
    "blank cells on only some shortest paths, longer paths, dead ends, and disconnected pockets stay unchanged",
    "all input cells outside unavoidable shortest-path blanks are preserved",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "unique_route",
    "many_paths_few_gates",
    "few_paths_long_spine",
    "many_paths_shared_spine",
    "dead_end_contrast",
    "disconnected_pockets",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
_PUBLIC_VARIANTS_PER_BAND = 509
_PUBLIC_POOL_SIZE = 4 * _PUBLIC_VARIANTS_PER_BAND
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five complete official families plus six shortest-path contrasts",
        "valid": "public_1|public_2|public_3|public_4|public_5|unique_route|many_paths_few_gates|few_paths_long_spine|many_paths_shared_spine|dead_end_contrast|disconnected_pockets",
    }
}

_PUBLIC_ROWS = {
    "public_1": (
        "555555555555", "500002050005", "500000055005", "500000005505",
        "505000000005", "553050500005", "500005000005", "500505500005",
        "555555555555",
    ),
    "public_2": (
        "555555555555", "500000555055", "500550500005", "500500005035",
        "505050555005", "525500000555", "555050005005", "555000055005",
        "500000050555", "500000000005", "555555555555",
    ),
    "public_3": (
        "55555555555", "50055050005", "50000500505", "50000005035",
        "50505000055", "50005050505", "50005000005", "50005000055",
        "50000000005", "52000000505", "55005500505", "55555555555",
    ),
    "public_4": (
        "55555555555", "50500300055", "50055550505", "55000050005",
        "50020005055", "50050050055", "50000000505", "50050500005",
        "50500505005", "55555555555",
    ),
    "public_5": (
        "55555555555555", "50000050050005", "55550000005505", "50500550055055",
        "50000200005005", "55000000050005", "50500000003005", "55005000550055",
        "50000005005005", "55000505050005", "50050500000005", "55555555555555",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _neighbors(cell, height, width):
    row, col = cell
    return tuple(
        (next_row, next_col)
        for next_row, next_col in (
            (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)
        )
        if 0 <= next_row < height and 0 <= next_col < width
    )


def _distance_counts(grid, start):
    height, width = len(grid), len(grid[0])
    distances, counts = {start: 0}, {start: 1}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in _neighbors(current, height, width):
            if grid[neighbor[0]][neighbor[1]] == 5:
                continue
            next_distance = distances[current] + 1
            if neighbor not in distances:
                distances[neighbor] = next_distance
                counts[neighbor] = counts[current]
                queue.append(neighbor)
            elif distances[neighbor] == next_distance:
                counts[neighbor] += counts[current]
    return distances, counts


def _path_facts(grid):
    starts = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    goals = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    ]
    if len(starts) != 1 or len(goals) != 1:
        return {"start": starts, "goal": goals, "connected": False}
    start, goal = starts[0], goals[0]
    from_start, start_counts = _distance_counts(grid, start)
    from_goal, goal_counts = _distance_counts(grid, goal)
    if goal not in from_start:
        return {
            "start": start, "goal": goal, "connected": False,
            "from_start": from_start, "from_goal": from_goal,
        }
    shortest_distance = from_start[goal]
    total_paths = start_counts[goal]
    shortest_nodes = tuple(sorted(
        cell for cell in from_start
        if cell in from_goal
        and from_start[cell] + from_goal[cell] == shortest_distance
    ))
    unavoidable = tuple(sorted(
        cell for cell in shortest_nodes
        if grid[cell[0]][cell[1]] == 0
        and start_counts[cell] * goal_counts[cell] == total_paths
    ))
    reachable = frozenset(from_start)
    all_open = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 5
    }
    endpoint_set = {start, goal}
    dead_ends = sum(
        cell not in endpoint_set
        and sum(neighbor in reachable for neighbor in _neighbors(cell, len(grid), len(grid[0]))) == 1
        for cell in reachable
    )
    layer_flow = []
    for distance in range(shortest_distance + 1):
        layer_flow.append(tuple(sorted(
            (start_counts[cell], goal_counts[cell])
            for cell in shortest_nodes if from_start[cell] == distance
        )))
    return {
        "start": start,
        "goal": goal,
        "connected": True,
        "shortest_distance": shortest_distance,
        "total_paths": total_paths,
        "shortest_nodes": shortest_nodes,
        "shortest_blank_count": sum(grid[row][col] == 0 for row, col in shortest_nodes),
        "unavoidable": unavoidable,
        "unavoidable_layers": tuple(from_start[cell] for cell in unavoidable),
        "layer_flow": tuple(layer_flow),
        "reachable_open": len(reachable),
        "unreachable_open": len(all_open - reachable),
        "dead_ends": dead_ends,
        "manhattan": abs(start[0] - goal[0]) + abs(start[1] - goal[1]),
    }


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical shortest-path count rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _path_facts(grid)
    if not facts.get("connected"):
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    for row, col in facts["unavoidable"]:
        output[row][col] = 8
    return output


def _rotate(grid):
    return tuple(
        tuple(grid[len(grid) - 1 - row][col] for row in range(len(grid)))
        for col in range(len(grid[0]))
    )


def _d4_grids(grid):
    variants, current = set(), tuple(map(tuple, grid))
    for _ in range(4):
        variants.add(current)
        variants.add(tuple(tuple(reversed(row)) for row in current))
        current = _rotate(current)
    return tuple(sorted(variants))


def _swap_endpoints(grid):
    return tuple(
        tuple(3 if value == 2 else 2 if value == 3 else value for value in row)
        for row in grid
    )


def _shortest_signature(grid, facts=None):
    facts = facts or _path_facts(grid)
    if not facts.get("connected"):
        return None
    return (
        len(grid), len(grid[0]),
        facts["shortest_distance"], facts["manhattan"], facts["total_paths"],
        facts["shortest_blank_count"], facts["unavoidable_layers"], facts["layer_flow"],
    )


_PUBLIC_TRANSFORMS = {
    profile: tuple(sorted({
        variant
        for transformed in _d4_grids(grid)
        for variant in (transformed, _swap_endpoints(transformed))
    }))
    for profile, grid in _PUBLIC_INPUTS.items()
}
_PUBLIC_FAMILY_SIGNATURES = {
    _shortest_signature(transformed): profile
    for profile, transforms in _PUBLIC_TRANSFORMS.items()
    for transformed in transforms
}


class _PoolRng:
    """Small deterministic PRNG used only to enumerate a frozen variant pool."""

    def __init__(self, seed):
        self.state = seed & ((1 << 64) - 1)

    def _next(self):
        self.state = (
            6_364_136_223_846_793_005 * self.state + 1_442_695_040_888_963_407
        ) & ((1 << 64) - 1)
        return self.state

    def randint(self, low, high):
        return low + self._next() % (high - low + 1)

    def choice(self, values):
        return values[self._next() % len(values)]

    def shuffle(self, values):
        for index in range(len(values) - 1, 0, -1):
            swap_index = self._next() % (index + 1)
            values[index], values[swap_index] = values[swap_index], values[index]


def _public_family(grid, facts=None):
    try:
        return _PUBLIC_FAMILY_SIGNATURES.get(_shortest_signature(grid, facts))
    except (TypeError, IndexError):
        return None


def _general_profile(facts):
    if not facts.get("connected"):
        return None
    paths = facts["total_paths"]
    unavoidable = len(facts["unavoidable"])
    if paths == 1 and 4 <= unavoidable <= 18:
        return "unique_route"
    if paths >= 8 and 2 <= unavoidable <= 4:
        return "many_paths_few_gates"
    if 2 <= paths <= 7 and 8 <= unavoidable <= 18:
        return "few_paths_long_spine"
    if paths >= 8 and 5 <= unavoidable <= 18:
        return "many_paths_shared_spine"
    if 2 <= paths <= 7 and 2 <= unavoidable <= 7:
        if facts["unreachable_open"] >= 1:
            return "disconnected_pockets"
        if facts["dead_ends"] >= 3:
            return "dead_end_contrast"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if not 9 <= height <= 14 or not 9 <= width <= 14 or not 99 <= height * width <= 168:
        errors.append("calibrated mazes must use official-scale 9..14 axes and area 99..168")
    palette = {value for row in grid for value in row}
    if palette != {0, 2, 3, 5}:
        errors.append("calibrated mazes require exactly blank 0, start 2, goal 3, and wall 5")
    if any(value != 5 for value in grid[0] + grid[-1]):
        errors.append("top and bottom borders must be solid walls")
    if any(row[0] != 5 or row[-1] != 5 for row in grid):
        errors.append("left and right borders must be solid walls")
    wall_fraction = sum(value == 5 for row in grid for value in row) / (height * width)
    if not 0.40 <= wall_fraction <= 0.62:
        errors.append("calibrated wall fraction must stay within 0.40..0.62")
    facts = _path_facts(grid)
    if not facts.get("connected"):
        errors.append("the unique red start and green goal must be connected")
        output = [list(row) for row in grid]
    else:
        output = [list(row) for row in grid]
        for row, col in facts["unavoidable"]:
            output[row][col] = 8
        if not 5 <= facts["shortest_distance"] <= 24:
            errors.append("calibrated shortest-path distance must be five through twenty-four")
        if not 2 <= len(facts["unavoidable"]) <= 18:
            errors.append("calibrated lessons require two through eighteen unavoidable blank cells")
    profile = _public_family(grid, facts) or _general_profile(facts)
    if profile not in SCENE_PROFILES:
        errors.append("maze relationships do not match a declared shortest-path profile")
    details = dict(facts)
    details.update({
        "height": height,
        "width": width,
        "wall_fraction": wall_fraction,
        "wall_count": sum(value == 5 for row in grid for value in row),
        "scene_profile": profile,
        "changed": sum(
            before != after
            for before_row, after_row in zip(grid, output)
            for before, after in zip(before_row, after_row)
        ),
    })
    return {"errors": errors, "scene_profile": profile, "facts": details, "output": output}


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


@lru_cache(maxsize=None)
def _public_variant_pool(profile):
    """Build a prime-sized pool with the complete public path DAG fixed."""
    transforms = _PUBLIC_TRANSFORMS[profile]
    variants = set(transforms)
    rng = _PoolRng(91_337 + PUBLIC_PROFILES.index(profile) * 10_007)
    attempts = 0
    while len(variants) < _PUBLIC_POOL_SIZE and attempts < 160_000:
        attempts += 1
        grid = [list(row) for row in rng.choice(transforms)]
        candidates = [
            (row, col)
            for row in range(1, len(grid) - 1)
            for col in range(1, len(grid[0]) - 1)
            if grid[row][col] in (0, 5)
        ]
        rng.shuffle(candidates)
        for row, col in candidates[: rng.randint(1, min(12, len(candidates)))]:
            grid[row][col] = 5 if grid[row][col] == 0 else 0
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            variants.add(tuple(map(tuple, grid)))
    if len(variants) < _PUBLIC_POOL_SIZE:
        raise AssertionError(
            f"could not build public variant pool {profile!r}: "
            f"{len(variants)}/{_PUBLIC_POOL_SIZE}"
        )
    return tuple(sorted(variants))


def _mutate_public(profile, variant_index, band_index):
    pool = _public_variant_pool(profile)
    pool_index = (
        band_index * _PUBLIC_VARIANTS_PER_BAND
        + variant_index % _PUBLIC_VARIANTS_PER_BAND
    )
    variant = pool[pool_index]
    return [list(row) for row in variant]


_PROFILE_WALL_RANGES = {
    "unique_route": (0.37, 0.52),
    "many_paths_few_gates": (0.18, 0.34),
    "few_paths_long_spine": (0.28, 0.45),
    "many_paths_shared_spine": (0.18, 0.35),
    "dead_end_contrast": (0.23, 0.42),
    "disconnected_pockets": (0.27, 0.50),
}
_CALIBRATED_SHAPES = tuple(sorted({
    (len(grid), len(grid[0]))
    for grid in _PUBLIC_INPUTS.values()
} | {
    (len(grid[0]), len(grid))
    for grid in _PUBLIC_INPUTS.values()
}))


def _random_maze(profile, rng):
    low, high = _PROFILE_WALL_RANGES[profile]
    for _ in range(5000):
        height, width = rng.choice(_CALIBRATED_SHAPES)
        wall_probability = rng.uniform(low, high)
        grid = [[5] * width for _ in range(height)]
        open_cells = []
        for row in range(1, height - 1):
            for col in range(1, width - 1):
                if rng.random() >= wall_probability:
                    grid[row][col] = 0
                    open_cells.append((row, col))
        if len(open_cells) < 12:
            continue
        endpoint_pairs = [
            tuple(rng.sample(open_cells, 2)) for _ in range(24)
        ]
        pair = next((
            candidate for candidate in endpoint_pairs
            if abs(candidate[0][0] - candidate[1][0])
            + abs(candidate[0][1] - candidate[1][1]) >= 5
        ), None)
        if pair is None:
            continue
        start, goal = pair
        grid[start[0]][start[1]] = 2
        grid[goal[0]][goal[1]] = 3
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct shortest-path lesson {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
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
    band_index = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    schedule_index = seed + 37 * sample_index + 5500 * band_index
    explicit = overrides.get("scene_profile") is not None
    if explicit:
        profile = ctx.draw_choice("scene_profile", list(SCENE_PROFILES))
    else:
        profile = ctx.draw_choice(
            "scene_profile", [SCENE_PROFILES[schedule_index % len(SCENE_PROFILES)]]
        )
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and explicit:
        grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
    elif profile in PUBLIC_PROFILES:
        grid = _mutate_public(
            profile, schedule_index // len(SCENE_PROFILES), band_index
        )
    else:
        grid = _random_maze(profile, ctx.draw_rng("maze"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid shortest-path lesson: " + "; ".join(errors))
    return grid
