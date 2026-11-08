"""Semantic generator for ARC task ad4e2cd6e3bc.

Color 5 is a wall.  Starting from the first red (2) cell, traverse the
4-connected region containing only black (0) or red cells and recolor its
black cells cyan (8).  Preserve the seed, walls, and unreachable chambers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "ad4e2cd6e3bc"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "f76966dac45b"
SUMMARY = "Flood reachable black cells cyan from the red seed without crossing gray walls."
INVARIANTS = [
    "color 5 forms an outer wall border and optional interior barriers",
    "exactly one color-2 seed lies in a nontrivial passable chamber",
    "nonzero-pocket profiles include a multi-cell unreachable chamber",
    "some lessons place the seed outside the largest passable component",
    "flood traversal is 4-connected through colors 0 and 2",
    "unreachable color-0 chambers remain unchanged",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_test_1")
GENERAL_PROFILES = (
    "all_reachable",
    "one_pocket",
    "two_pockets",
    "three_pockets",
    "four_pockets",
    "five_pockets",
    "six_pockets",
    "seven_pockets",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and zero-through-seven unreachable chambers",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_train_1": "555555555/520000055/505550055/500050055/505050055/500000055/555555555",
    "public_train_2": "55555555/50020055/50555055/50005055/55505055/50000055/55555555",
    "public_test_1": "5555555555/5200000055/5055550055/5000050055/5050050055/5000000055/5555555555",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_POCKET_PROFILES = {count: profile for count, profile in enumerate(GENERAL_PROFILES)}
_PROFILE_POCKETS = {profile: count for count, profile in _POCKET_PROFILES.items()}
_DEFAULT_PROFILES = (
    [name for name in PUBLIC_PROFILES for _ in range(3)]
    + ["all_reachable"] * 20
    + ["one_pocket"] * 10
    + ["two_pockets"] * 6
    + ["three_pockets"] * 3
    + list(GENERAL_PROFILES[4:])
)


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _passable_components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] in (0, 2)}
    components = []
    while unseen:
        todo = [next(iter(unseen))]
        cells = set()
        while todo:
            cell = todo.pop()
            if cell not in unseen:
                continue
            unseen.remove(cell)
            cells.add(cell)
            row, col = cell
            todo.extend(
                neighbor
                for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                if neighbor in unseen
            )
        components.append(cells)
    return components


def _seed_region(grid):
    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if not seeds:
        raise ValueError("grid has no color-2 seed")
    seed = seeds[0]
    return seed, next(component for component in _passable_components(grid) if seed in component)


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    _, region = _seed_region(grid)
    output = [list(row) for row in grid]
    for row, col in region:
        if grid[row][col] == 0:
            output[row][col] = 8
    return output


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    unexpected = sorted({value for row in grid for value in row} - {0, 2, 5})
    if unexpected:
        errors.append(f"unexpected colors: {unexpected}")
    border_ok = (
        all(value == 5 for value in grid[0])
        and all(value == 5 for value in grid[-1])
        and all(row[0] == 5 and row[-1] == 5 for row in grid)
    )
    if not border_ok:
        errors.append("outer border must be entirely color 5")
    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(seeds) != 1:
        errors.append(f"expected exactly one color-2 seed, found {len(seeds)}")
    components = _passable_components(grid)
    seed_region = next((component for component in components if seeds and seeds[0] in component), set())
    reachable_zeros = {(r, c) for r, c in seed_region if grid[r][c] == 0}
    if not reachable_zeros:
        errors.append("seed must reach at least one black cell")
    unreachable = [component for component in components if component is not seed_region]
    pocket_count = len(unreachable)
    if pocket_count > 7:
        errors.append(f"at most seven unreachable chambers are calibrated, found {pocket_count}")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public or _POCKET_PROFILES.get(pocket_count)
    if profile not in SCENE_PROFILES:
        errors.append("topology does not match a declared scene profile")
    output = None
    if seeds and seed_region:
        output = [list(row) for row in grid]
        for row, col in reachable_zeros:
            output[row][col] = 8
    result.update(
        {
            "seed": seeds[0] if seeds else None,
            "seed_region": seed_region,
            "reachable_zeros": reachable_zeros,
            "unreachable_components": tuple(unreachable),
            "unreachable_zeros": set().union(*unreachable) if unreachable else set(),
            "pocket_count": pocket_count,
            "wall_count": sum(value == 5 for row in grid for value in row),
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _base_dimensions(rng, band, pocket_count):
    ranges = {"easy": ((7, 9), (8, 12)), "medium": ((7, 11), (8, 14)), "hard": ((9, 14), (10, 18))}
    (h_low, h_high), (w_low, w_high) = ranges[band]
    height = rng.randint(h_low, h_high)
    # One extra interior column guarantees that a nonzero-pocket scene can
    # contain a chamber wider than one cell while retaining an open corridor.
    minimum_width = 2 * pocket_count + (5 if pocket_count else 4)
    width = max(rng.randint(w_low, w_high), minimum_width)
    return min(height, 30), min(width, 30)


def _pocket_widths(rng, pocket_count, width):
    if not pocket_count:
        return []
    widths = [1] * pocket_count
    extra_capacity = width - (2 * pocket_count + 4)
    extra_cells = rng.randint(1, min(2 * pocket_count, extra_capacity))
    order = list(range(pocket_count))
    rng.shuffle(order)
    while extra_cells:
        choices = [index for index in order if widths[index] < 3]
        if not choices:
            break
        widths[rng.choice(choices)] += 1
        extra_cells -= 1
    return widths


def _ordered_components(grid):
    return sorted(_passable_components(grid), key=lambda cells: (-len(cells), min(cells)))


def _build_scene(rng, pocket_count, band):
    for _attempt in range(80):
        height, width = _base_dimensions(rng, band, pocket_count)
        grid = [[5 if r in (0, height - 1) or c in (0, width - 1) else 0 for c in range(width)] for r in range(height)]
        pocket_row = rng.randint(3, height - 4)
        pocket_widths = _pocket_widths(rng, pocket_count, width)
        for row in range(1, pocket_row):
            for col in range(1, width - 1):
                grid[row][col] = 5
        cursor = 2
        for pocket_width in pocket_widths:
            left_wall = cursor - 1
            right_wall = cursor + pocket_width
            grid[pocket_row][left_wall] = 5
            grid[pocket_row][right_wall] = 5
            for bottom_col in range(left_wall, right_wall + 1):
                grid[pocket_row + 1][bottom_col] = 5
            cursor = right_wall + 1
        components = _passable_components(grid)
        if len(components) != pocket_count + 1:
            continue
        # Add short boundary-attached dead ends only below the chamber row so
        # the guaranteed multi-cell chamber cannot be accidentally collapsed.
        for _ in range({"easy": 1, "medium": 3, "hard": 5}[band]):
            row = rng.randint(pocket_row + 2, height - 2)
            length = rng.randint(1, min(5, width - 3))
            changed = [(row, col) for col in range(1, length + 1) if grid[row][col] == 0]
            for rr, cc in changed:
                grid[rr][cc] = 5
            if len(_passable_components(grid)) != pocket_count + 1:
                for rr, cc in changed:
                    grid[rr][cc] = 0
        components = _ordered_components(grid)
        largest = components[0]
        smaller_seed_regions = [component for component in components[1:] if len(component) >= 2]
        use_smaller_seed = smaller_seed_regions and rng.randrange(3) == 0
        seed_region = rng.choice(smaller_seed_regions) if use_smaller_seed else largest
        seed_candidates = sorted(seed_region)
        rng.shuffle(seed_candidates)
        seed = seed_candidates[0]
        grid[seed[0]][seed[1]] = 2
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["pocket_count"] == pocket_count:
            return grid
    raise RuntimeError(f"could not construct {pocket_count}-pocket {band} scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = requested or ctx.draw_choice("scene_profile", _DEFAULT_PROFILES)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _build_scene(ctx.draw_rng("layout"), _PROFILE_POCKETS[profile], band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Return task-domain findings for the semantic gate."""
    return self_check(grid)


def _largest_component_rival(grid):
    """Shortcut that ignores the red seed and floods the largest component."""
    target = _ordered_components(grid)[0]
    output = [list(row) for row in grid]
    for row, col in target:
        if grid[row][col] == 0:
            output[row][col] = 8
    return output


def _local_neighbor_rival(grid):
    """Shortcut that paints any black cell touching another passable cell."""
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            if any(
                0 <= rr < height
                and 0 <= cc < width
                and grid[rr][cc] in (0, 2)
                for rr, cc in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                )
            ):
                output[row][col] = 8
    return output


SEMANTIC_RIVALS = {
    "largest_component": _largest_component_rival,
    "local_neighbor": _local_neighbor_rival,
}
SEMANTIC_WITNESSES = {
    name: (lambda grid, rival=rival: rule_mirror(grid) != rival(grid))
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}
