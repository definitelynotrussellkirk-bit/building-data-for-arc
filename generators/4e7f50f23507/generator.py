"""Semantic generator for ARC task 4e7f50f23507 (bank H82).

Gray 5 cells are walls. From the unique red 2 and green 3 seeds, compute
four-connected shortest-path distance through non-wall cells. Paint a blank
cell cyan 8 exactly when it is reachable from both seeds at equal distance.
The curriculum contains all five complete official mazes plus explicit
same-row, same-column, diagonal, detour, fragmented, long, singleton, and
disconnected-pocket contrasts.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "4e7f50f23507"
TASK_ID = "4e7f50f23507"
VERSION = "3.0.0"
RULE_HASH = "c06350648cb4"
EXAMPLES_NEEDED = 4
SUMMARY = "Paint each blank cell whose wall-constrained distance to the red and green seeds is equal."
INVARIANTS = [
    "gray 5 cells are impassable walls and zero cells are traversable blanks",
    "there is exactly one red 2 seed and one green 3 seed",
    "a cyan 8 is added only to a blank reachable from both seeds at equal shortest-path distance",
    "unequally distant, singly reachable, unreachable, wall, and seed cells are preserved",
    "every generated lesson has at least one observable equidistant blank",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "single_tie",
    "fragmented_ties",
    "long_connected_tie",
    "wall_detour",
    "same_row_tie",
    "same_column_tie",
    "diagonal_tie",
    "disconnected_pockets",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five complete official mazes plus eight equal-distance contrasts",
        "valid": "public_1|public_2|public_3|public_4|public_5|single_tie|fragmented_ties|long_connected_tie|wall_detour|same_row_tie|same_column_tie|diagonal_tie|disconnected_pockets",
    }
}

_PUBLIC_ROWS = {
    "public_1": (
        '555555555555555',
        '500000000000005',
        '500000000000005',
        '500000555000005',
        '500000555000005',
        '500200555003005',
        '500000555000005',
        '500000555000005',
        '500000000000005',
        '500000000000005',
        '555555555555555',
    ),
    "public_2": (
        '55555555555555',
        '50000000000005',
        '50000000000005',
        '50020000000005',
        '50000000000005',
        '50000000000005',
        '50005500550005',
        '50000000000005',
        '50000000003005',
        '50000000000005',
        '50000000000005',
        '55555555555555',
    ),
    "public_3": (
        '5555555555555',
        '5000000000005',
        '5000000000005',
        '5002000000005',
        '5000005000005',
        '5000005000005',
        '5000000000005',
        '5000005000005',
        '5000005000005',
        '5000000003005',
        '5000000000005',
        '5000000000005',
        '5555555555555',
    ),
    "public_4": (
        '5555555555555555',
        '5000000000000005',
        '5002000000000005',
        '5000000000000005',
        '5000055555500005',
        '5000000000000005',
        '5000055555500005',
        '5000000000003005',
        '5000000000000005',
        '5555555555555555',
    ),
    "public_5": (
        '5555555555555',
        '5000000000005',
        '5000500050005',
        '5000500050005',
        '5000500050005',
        '5020000000305',
        '5000500050005',
        '5000500050005',
        '5000500050005',
        '5000000000005',
        '5555555555555',
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


def _distances(grid, start):
    height, width = len(grid), len(grid[0])
    distances = {start: 0}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in _neighbors(current, height, width):
            if grid[neighbor[0]][neighbor[1]] == 5 or neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return distances


def _component_sizes(cells):
    remaining = set(cells)
    sizes = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        size = 0
        while stack:
            current = stack.pop()
            size += 1
            row, col = current
            for neighbor in (
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        sizes.append(size)
    return tuple(sorted(sizes, reverse=True))


def _facts(grid):
    seeds_2 = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    seeds_3 = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    ]
    if len(seeds_2) != 1 or len(seeds_3) != 1:
        return {"seed_2": seeds_2, "seed_3": seeds_3, "connected": False}
    seed_2, seed_3 = seeds_2[0], seeds_3[0]
    distance_2 = _distances(grid, seed_2)
    distance_3 = _distances(grid, seed_3)
    common = set(distance_2) & set(distance_3)
    equal = tuple(sorted(
        cell for cell in common
        if grid[cell[0]][cell[1]] == 0
        and distance_2[cell] == distance_3[cell]
    ))
    all_open = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 5
    }
    output = [list(row) for row in grid]
    for row, col in equal:
        output[row][col] = 8
    connected = seed_3 in distance_2
    reachable = set(distance_2)
    endpoint_set = {seed_2, seed_3}
    dead_ends = sum(
        cell not in endpoint_set
        and sum(neighbor in reachable for neighbor in _neighbors(cell, len(grid), len(grid[0]))) == 1
        for cell in reachable
    )
    return {
        "seed_2": seed_2,
        "seed_3": seed_3,
        "connected": connected,
        "distance_2": distance_2,
        "distance_3": distance_3,
        "shortest_distance": distance_2.get(seed_3),
        "manhattan": abs(seed_2[0] - seed_3[0]) + abs(seed_2[1] - seed_3[1]),
        "equal": equal,
        "equal_count": len(equal),
        "equal_components": _component_sizes(equal),
        "equal_distance_histogram": tuple(sorted(Counter(distance_2[cell] for cell in equal).items())),
        "mutual_distance_pairs": tuple(sorted(Counter(
            (distance_2[cell], distance_3[cell])
            for cell in common if grid[cell[0]][cell[1]] == 0
        ).items())),
        "reachable_open": len(reachable),
        "unreachable_open": len(all_open - reachable),
        "dead_ends": dead_ends,
        "output": output,
    }


def rule_mirror(grid):
    """Broad, input-pure mirror of the executable two-source BFS rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _facts(grid)
    if not isinstance(facts.get("seed_2"), tuple) or not isinstance(facts.get("seed_3"), tuple):
        raise ValueError("input must contain exactly one red 2 and one green 3 seed")
    return [row[:] for row in facts["output"]]


def _rotate(grid):
    return tuple(tuple(row) for row in zip(*grid[::-1]))


def _reflect(grid):
    return tuple(tuple(reversed(row)) for row in grid)


def _transforms(grid):
    current = tuple(map(tuple, grid))
    variants = set()
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(variants))


def _swap_endpoints(grid):
    return tuple(tuple(3 if value == 2 else 2 if value == 3 else value for value in row) for row in grid)


_PUBLIC_TRANSFORMS = {
    profile: tuple(sorted({
        variant
        for transformed in _transforms(grid)
        for variant in (transformed, _swap_endpoints(transformed))
    }))
    for profile, grid in _PUBLIC_INPUTS.items()
}
_PUBLIC_CORE_LOOKUP = {}
for _profile, _cores in _PUBLIC_TRANSFORMS.items():
    for _core in _cores:
        _shape = (len(_core), len(_core[0]))
        _PUBLIC_CORE_LOOKUP.setdefault(_shape, {})[_core] = _profile


def _public_family(grid):
    """Find one complete official maze, optionally sealed inside wall padding."""
    height, width = len(grid), len(grid[0])
    matches = set()
    for (core_height, core_width), lookup in _PUBLIC_CORE_LOOKUP.items():
        if core_height > height or core_width > width:
            continue
        for top in range(height - core_height + 1):
            for left in range(width - core_width + 1):
                core = tuple(
                    tuple(grid[row][left:left + core_width])
                    for row in range(top, top + core_height)
                )
                profile = lookup.get(core)
                if profile is not None:
                    matches.add(profile)
    return next(iter(matches)) if len(matches) == 1 else None


def _general_profile(facts):
    if not facts.get("connected") or not facts.get("equal"):
        return None
    seed_2, seed_3 = facts["seed_2"], facts["seed_3"]
    if facts["unreachable_open"] >= 1:
        return "disconnected_pockets"
    if len(facts["equal_components"]) >= 2:
        return "fragmented_ties"
    if facts["equal_count"] == 1:
        return "single_tie"
    if facts["equal_count"] >= 8:
        return "long_connected_tie"
    if facts["shortest_distance"] > facts["manhattan"]:
        return "wall_detour"
    if seed_2[0] == seed_3[0]:
        return "same_row_tie"
    if seed_2[1] == seed_3[1]:
        return "same_column_tie"
    return "diagonal_tie"


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if not 9 <= height <= 22 or not 9 <= width <= 22 or not 99 <= height * width <= 400:
        errors.append("calibrated mazes require 9..22 axes and area 99..400")
    palette = {value for row in grid for value in row}
    if palette != {0, 2, 3, 5}:
        errors.append("calibrated mazes require exactly blank 0, seeds 2/3, and wall 5")
    if any(value != 5 for value in grid[0] + grid[-1]):
        errors.append("top and bottom borders must be solid walls")
    if any(row[0] != 5 or row[-1] != 5 for row in grid):
        errors.append("left and right borders must be solid walls")
    wall_count = sum(value == 5 for row in grid for value in row)
    wall_fraction = wall_count / (height * width)
    if not 0.28 <= wall_fraction <= 0.72:
        errors.append("calibrated wall fraction must stay within 0.28..0.72")
    facts = _facts(grid)
    if not facts.get("connected"):
        errors.append("the unique red and green seeds must be connected")
    else:
        if not 4 <= facts["manhattan"] <= 14:
            errors.append("calibrated seed Manhattan distance must be four through fourteen")
        if not 4 <= facts["shortest_distance"] <= 20:
            errors.append("calibrated wall-constrained seed distance must be four through twenty")
        if not 1 <= facts["equal_count"] <= 24:
            errors.append("calibrated lessons require one through twenty-four equidistant blanks")
    public_profile = _public_family(grid)
    profile = public_profile or _general_profile(facts)
    if profile not in SCENE_PROFILES:
        errors.append("maze relationships do not match a declared equal-distance profile")
    details = dict(facts)
    details.update({
        "height": height,
        "width": width,
        "wall_count": wall_count,
        "wall_fraction": wall_fraction,
        "scene_profile": profile,
        "public_profile": public_profile,
    })
    return {
        "errors": errors,
        "scene_profile": profile,
        "facts": details,
        "output": facts.get("output"),
    }


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


class _CodeRng:
    """Tiny deterministic mixer for public nuisance bits; no global RNG use."""

    def __init__(self, seed):
        self.state = seed & ((1 << 64) - 1)

    def next(self):
        self.state = (
            6_364_136_223_846_793_005 * self.state + 1_442_695_040_888_963_407
        ) & ((1 << 64) - 1)
        return self.state


def _embed_public(profile, variant_index, band_index):
    """Embed an exact sealed official maze and injectively code nuisance pockets."""
    code = 1 + variant_index + band_index * 1_000_003
    cores = _PUBLIC_TRANSFORMS[profile]
    core = cores[(code // 17) % len(cores)]
    core_height, core_width = len(core), len(core[0])
    height, width = core_height + 4, core_width + 4
    grid = [[5] * width for _ in range(height)]
    for row in range(core_height):
        grid[row + 2][2:2 + core_width] = core[row]
    exterior = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if not (2 <= row < 2 + core_height and 2 <= col < 2 + core_width)
    ]
    mixer = _CodeRng(73_993 + PUBLIC_PROFILES.index(profile) * 10_007)
    for index, (row, col) in enumerate(exterior):
        mask_bit = (mixer.next() >> 63) & 1
        code_bit = (code >> index) & 1
        grid[row][col] = 0 if mask_bit ^ code_bit else 5
    return grid


_PROFILE_WALL_RANGES = {
    "single_tie": (0.12, 0.34),
    "fragmented_ties": (0.16, 0.38),
    "long_connected_tie": (0.05, 0.22),
    "wall_detour": (0.20, 0.42),
    "same_row_tie": (0.04, 0.20),
    "same_column_tie": (0.04, 0.20),
    "diagonal_tie": (0.06, 0.28),
    "disconnected_pockets": (0.28, 0.50),
}
_CALIBRATED_SHAPES = tuple(sorted({
    (len(grid), len(grid[0]))
    for grid in _PUBLIC_INPUTS.values()
} | {
    (len(grid[0]), len(grid))
    for grid in _PUBLIC_INPUTS.values()
}))


def _pair_orientation_ok(profile, first, second):
    if profile == "same_row_tie":
        return first[0] == second[0]
    if profile == "same_column_tie":
        return first[1] == second[1]
    if profile == "diagonal_tie":
        return first[0] != second[0] and first[1] != second[1]
    return True


def _random_maze(profile, rng):
    low, high = _PROFILE_WALL_RANGES[profile]
    for _ in range(8000):
        height, width = rng.choice(_CALIBRATED_SHAPES)
        wall_probability = rng.uniform(low, high)
        grid = [[5] * width for _ in range(height)]
        open_cells = []
        for row in range(1, height - 1):
            for col in range(1, width - 1):
                if rng.random() >= wall_probability:
                    grid[row][col] = 0
                    open_cells.append((row, col))
        if len(open_cells) < 28:
            continue
        candidates = [tuple(rng.sample(open_cells, 2)) for _ in range(36)]
        for seed_2, seed_3 in candidates:
            manhattan = abs(seed_2[0] - seed_3[0]) + abs(seed_2[1] - seed_3[1])
            if not 4 <= manhattan <= 12 or manhattan % 2:
                continue
            if not _pair_orientation_ok(profile, seed_2, seed_3):
                continue
            grid[seed_2[0]][seed_2[1]] = 2
            grid[seed_3[0]][seed_3[1]] = 3
            analysis = _analysis(grid)
            if not analysis["errors"] and analysis["scene_profile"] == profile:
                return grid
            grid[seed_2[0]][seed_2[1]] = 0
            grid[seed_3[0]][seed_3[1]] = 0
    raise AssertionError(f"could not construct equal-distance lesson {profile!r}")


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
    lesson_index, phase = divmod(sample_index, EXAMPLES_NEEDED)
    schedule_key = seed + lesson_index + 17 * band_index
    explicit = overrides.get("scene_profile") is not None
    if explicit:
        profile = ctx.draw_choice("scene_profile", list(SCENE_PROFILES))
    else:
        if phase == 0:
            # Every four-pair lesson begins with the decisive counterexample:
            # walls make graph distance differ from Manhattan distance.
            scheduled = "wall_detour"
        elif phase == 1:
            scheduled = ("same_row_tie", "same_column_tie", "diagonal_tie")[
                schedule_key % 3
            ]
        elif phase == 2:
            scheduled = (
                "single_tie", "fragmented_ties", "long_connected_tie",
                "disconnected_pockets",
            )[schedule_key % 4]
        else:
            scheduled = PUBLIC_PROFILES[schedule_key % len(PUBLIC_PROFILES)]
        profile = ctx.draw_choice("scene_profile", [scheduled])
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and explicit:
        grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
    elif profile in PUBLIC_PROFILES:
        # Phase three anchors each lesson to official morphology. One quarter
        # of lessons use an exact official grid (strict empirical manifold);
        # the rest preserve an exact sealed official core while varying only
        # disconnected nuisance pockets.
        if lesson_index % 4 == 0:
            grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
        else:
            variant_index = seed * 1_000_003 + lesson_index
            grid = _embed_public(profile, variant_index, band_index)
    else:
        grid = _random_maze(profile, ctx.draw_rng(f"maze:{band_index}"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid equal-distance lesson: " + "; ".join(errors))
    return grid
