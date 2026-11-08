"""Semantic generator for ARC task 86e4139d27c1 (source e9614598).

Read blue (1) cells in row-major order, take the first two, floor the
coordinate-wise midpoint, and paint that midpoint plus its four cardinal
neighbours green (3).  Writes outside the canvas are clipped; every other
cell is preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "86e4139d27c1"
TASK_ID = "86e4139d27c1"
VERSION = "3.0.0"
RULE_HASH = "23ba8d9ddb01"
SUMMARY = "Paint a clipped green plus at the floored midpoint of the first two row-major blue cells."
INVARIANTS = [
    "blue (1) cells are read in row-major order and the first two determine the midpoint",
    "midpoint coordinates use floor independently, including odd endpoint deltas",
    "the midpoint and four cardinal neighbours are painted green (3)",
    "out-of-bounds plus arms are clipped and in-bounds writes may overwrite blue endpoints",
    "all cells outside the in-bounds plus footprint are preserved",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "axis_even",
    "diagonal_even",
    "odd_floor",
    "first_two_of_three",
    "endpoint_overwrite",
    "clipped_plus",
    "decor_preserved",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "official-family and seven midpoint/order/clipping/preservation contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_CARDINAL_PLUS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
_DECOR_COLORS = (2, 4, 5, 6, 7, 8, 9)


def _blank(height, width, endpoints):
    grid = [[0] * width for _ in range(height)]
    for row, col in endpoints:
        grid[row][col] = 1
    return grid


_PUBLIC_INPUTS = {
    "public_1": _blank(10, 10, ((0, 3), (8, 3))),
    "public_2": _blank(10, 10, ((4, 1), (4, 7))),
    "public_3": _blank(10, 6, ((0, 3), (6, 3))),
    "public_4": _blank(12, 12, ((3, 1), (3, 11))),
}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 3 <= len(grid) <= 30:
        return ["input must contain three through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 3 <= len(grid[0]) <= 30:
        return ["input must contain three through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _blue_cells(grid):
    return tuple(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    )


def _midpoint_and_footprint(blues):
    (row_a, col_a), (row_b, col_b) = blues[:2]
    midpoint = ((row_a + row_b) // 2, (col_a + col_b) // 2)
    footprint = tuple((midpoint[0] + dr, midpoint[1] + dc) for dr, dc in _CARDINAL_PLUS)
    return midpoint, footprint


def rule_mirror(grid):
    """Exact Python mirror of the executable Racket rule's broad domain."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    blues = _blue_cells(grid)
    if len(blues) < 2:
        raise ValueError("the rule requires at least two blue cells")
    _, footprint = _midpoint_and_footprint(blues)
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row, col in footprint:
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = 3
    return output


def _public_family_key(grid):
    if _valid_grid(grid):
        return None
    blues = _blue_cells(grid)
    if len(blues) != 2 or any(value == 3 for row in grid for value in row):
        return None
    midpoint, footprint = _midpoint_and_footprint(blues)
    height, width = len(grid), len(grid[0])
    if not all(0 <= row < height and 0 <= col < width for row, col in footprint):
        return None
    del midpoint
    row_delta = abs(blues[1][0] - blues[0][0])
    col_delta = abs(blues[1][1] - blues[0][1])
    return row_delta, col_delta


_PUBLIC_FAMILIES = {_public_family_key(grid): profile for profile, grid in _PUBLIC_INPUTS.items()}


def canonical_profile_signature(grid):
    try:
        signature = tuple(tuple(row) for row in grid)
    except TypeError:
        return None
    return _PUBLIC_SIGNATURES.get(signature)


def canonical_family_signature(grid):
    return _PUBLIC_FAMILIES.get(_public_family_key(grid))


def _general_profile(facts):
    if facts["blue_count"] == 3:
        return "first_two_of_three"
    if facts["clipped_count"]:
        return "clipped_plus"
    if facts["endpoint_overlap_count"]:
        return "endpoint_overwrite"
    if facts["decor_count"] >= 6:
        return "decor_preserved"
    if facts["row_delta"] % 2 or facts["col_delta"] % 2:
        return "odd_floor"
    if facts["row_delta"] and facts["col_delta"]:
        return "diagonal_even"
    return "axis_even"


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    height, width = len(grid), len(grid[0])
    blues = _blue_cells(grid)
    if len(blues) < 2:
        errors.append("at least two blue cells are required")
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    if len(blues) > 3:
        errors.append("calibrated lessons permit at most three blue cells")
    if any(value == 3 for row in grid for value in row):
        errors.append("green is reserved for rule output")
    midpoint, footprint = _midpoint_and_footprint(blues)
    in_bounds = tuple((row, col) for row, col in footprint if 0 <= row < height and 0 <= col < width)
    endpoint_overlap = frozenset(blues[:2]) & frozenset(in_bounds)
    decor = tuple(
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 1)
    )
    facts = {
        "height": height,
        "width": width,
        "blues": blues,
        "blue_count": len(blues),
        "first_blue": blues[0],
        "second_blue": blues[1],
        "midpoint": midpoint,
        "footprint": footprint,
        "in_bounds_footprint": in_bounds,
        "clipped_count": len(footprint) - len(in_bounds),
        "endpoint_overlap": endpoint_overlap,
        "endpoint_overlap_count": len(endpoint_overlap),
        "row_delta": abs(blues[1][0] - blues[0][0]),
        "col_delta": abs(blues[1][1] - blues[0][1]),
        "decor": decor,
        "decor_count": len(decor),
        "preserved_decor_count": sum((row, col) not in in_bounds for row, col, _ in decor),
    }
    profile = canonical_profile_signature(grid)
    if profile is None:
        profile = canonical_family_signature(grid)
    if profile is None:
        profile = _general_profile(facts)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared midpoint lesson profile")
    output = None if errors else rule_mirror(grid)
    if output is not None:
        changed = {
            (row, col)
            for row in range(height)
            for col in range(width)
            if output[row][col] != grid[row][col]
        }
        if not changed <= set(in_bounds):
            errors.append("the rule may change only the in-bounds plus footprint")
        if any(output[row][col] != 3 for row, col in in_bounds):
            errors.append("every in-bounds plus cell must be green")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _limits(difficulty):
    if difficulty == "easy":
        return 6, 10
    if difficulty == "medium":
        return 10, 16
    if difficulty == "hard":
        return 16, 24
    return 8, 18


def _axis_pair(height, width, rng):
    if rng.choice((False, True)):
        row = rng.randint(1, height - 2)
        centre = rng.randint(2, width - 3)
        half = rng.randint(2, min(centre, width - 1 - centre))
        return (row, centre - half), (row, centre + half)
    col = rng.randint(1, width - 2)
    centre = rng.randint(2, height - 3)
    half = rng.randint(2, min(centre, height - 1 - centre))
    return (centre - half, col), (centre + half, col)


def _diagonal_pair(height, width, rng):
    centre_row = rng.randint(1, height - 2)
    centre_col = rng.randint(1, width - 2)
    row_half = rng.randint(1, min(centre_row, height - 1 - centre_row))
    col_half = rng.randint(1, min(centre_col, width - 1 - centre_col))
    row_sign = rng.choice((-1, 1))
    col_sign = rng.choice((-1, 1))
    first = (centre_row - row_sign * row_half, centre_col - col_sign * col_half)
    second = (centre_row + row_sign * row_half, centre_col + col_sign * col_half)
    return tuple(sorted((first, second)))


def _odd_pair(height, width, rng):
    cells = [(row, col) for row in range(height) for col in range(width)]
    for _ in range(200):
        first, second = sorted(rng.sample(cells, 2))
        midpoint, footprint = _midpoint_and_footprint((first, second))
        if not (1 <= midpoint[0] < height - 1 and 1 <= midpoint[1] < width - 1):
            continue
        if first in footprint or second in footprint:
            continue
        if abs(second[0] - first[0]) % 2 or abs(second[1] - first[1]) % 2:
            return first, second
    raise AssertionError("could not construct odd-delta endpoint pair")


def _three_blue_cells(height, width, rng):
    cells = [(row, col) for row in range(height) for col in range(width)]
    for _ in range(200):
        first, second, third = sorted(rng.sample(cells, 3))
        midpoint, footprint = _midpoint_and_footprint((first, second))
        if third in footprint:
            continue
        if midpoint == first or midpoint == second:
            continue
        return first, second, third
    raise AssertionError("could not construct ordered three-blue scene")


def _clipped_pair(height, width, rng):
    if rng.choice((False, True)):
        row = rng.choice((0, height - 1))
        centre = rng.randint(2, width - 3)
        half = rng.randint(2, min(centre, width - 1 - centre))
        return (row, centre - half), (row, centre + half)
    col = rng.choice((0, width - 1))
    centre = rng.randint(2, height - 3)
    half = rng.randint(2, min(centre, height - 1 - centre))
    return (centre - half, col), (centre + half, col)


def _add_decor(grid, rng, minimum, maximum, forbidden):
    candidates = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 0 and (row, col) not in forbidden
    ]
    rng.shuffle(candidates)
    count = min(len(candidates), rng.randint(minimum, maximum))
    for row, col in candidates[:count]:
        grid[row][col] = rng.choice(_DECOR_COLORS)


def _general_scene_once(profile, difficulty, rng):
    low, high = _limits(difficulty)
    height, width = rng.randint(low, high), rng.randint(low, high)
    if profile == "axis_even":
        endpoints = _axis_pair(height, width, rng)
    elif profile == "diagonal_even":
        endpoints = _diagonal_pair(height, width, rng)
    elif profile == "odd_floor":
        endpoints = _odd_pair(height, width, rng)
    elif profile == "first_two_of_three":
        endpoints = _three_blue_cells(height, width, rng)
    elif profile == "endpoint_overwrite":
        midpoint = (rng.randint(1, height - 2), rng.randint(1, width - 2))
        if rng.choice((False, True)):
            endpoints = ((midpoint[0], midpoint[1] - 1), (midpoint[0], midpoint[1] + 1))
        else:
            endpoints = ((midpoint[0] - 1, midpoint[1]), (midpoint[0] + 1, midpoint[1]))
    elif profile == "clipped_plus":
        endpoints = _clipped_pair(height, width, rng)
    elif profile == "decor_preserved":
        endpoints = rng.choice((_axis_pair, _diagonal_pair))(height, width, rng)
    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    grid = _blank(height, width, endpoints)
    _, footprint = _midpoint_and_footprint(_blue_cells(grid))
    forbidden = set(endpoints) | set(footprint)
    if profile == "decor_preserved":
        _add_decor(grid, rng, 6, min(30, max(6, height * width // 5)), forbidden)
    else:
        _add_decor(grid, rng, 0, 5, forbidden)
    return grid


def _general_scene(profile, difficulty, rng):
    for _ in range(120):
        try:
            grid = _general_scene_once(profile, difficulty, rng)
        except (AssertionError, ValueError):
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct midpoint lesson profile {profile!r}")


def _delta_variants(row_delta, col_delta):
    return tuple(
        sorted(
            {
                (row_sign * row_delta, col_sign * col_delta)
                for row_sign in (-1, 1)
                for col_sign in (-1, 1)
            }
        )
    )


def _public_nuisance(profile, rng, difficulty=None):
    source = _PUBLIC_INPUTS[profile]
    source_blues = _blue_cells(source)
    row_delta = abs(source_blues[1][0] - source_blues[0][0])
    col_delta = abs(source_blues[1][1] - source_blues[0][1])
    low, high = _limits(difficulty)
    minimum_height = max(low, row_delta + 1)
    minimum_width = max(low, col_delta + 1)
    height = rng.randint(minimum_height, max(high, minimum_height))
    width = rng.randint(minimum_width, max(high, minimum_width))
    candidates = []
    for dr, dc in _delta_variants(row_delta, col_delta):
        for row in range(height):
            for col in range(width):
                other = row + dr, col + dc
                if not (0 <= other[0] < height and 0 <= other[1] < width):
                    continue
                endpoints = tuple(sorted(((row, col), other)))
                midpoint, footprint = _midpoint_and_footprint(endpoints)
                if all(0 <= rr < height and 0 <= cc < width for rr, cc in footprint):
                    candidates.append((endpoints, midpoint, footprint))
    if not candidates:
        raise AssertionError(f"no public-family placements for {profile!r}")
    endpoints, _, footprint = rng.choice(candidates)
    grid = _blank(height, width, endpoints)
    forbidden = set(endpoints) | set(footprint)
    _add_decor(grid, rng, 1, min(30, max(1, height * width // 4)), forbidden)
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"invalid public-family nuisance for {profile!r}")
    return grid


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
    public_prior = PUBLIC_PROFILES * 2
    general_prior = (
        ("axis_even",) * 6
        + ("diagonal_even",) * 6
        + ("odd_floor",) * 6
        + ("first_two_of_three",) * 4
        + ("endpoint_overwrite",) * 4
        + ("clipped_plus",) * 4
        + ("decor_preserved",) * 6
    )
    profile = ctx.draw_choice("scene_profile", public_prior + general_prior)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        if overrides.get("scene_profile") is not None:
            return [row[:] for row in _PUBLIC_INPUTS[profile]]
        grid = _public_nuisance(profile, ctx.draw_rng("public_nuisance"), difficulty)
    else:
        grid = _general_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid midpoint lesson: " + "; ".join(errors))
    return grid
