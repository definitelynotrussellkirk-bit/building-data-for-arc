"""Lawful inputs for the cropped onion-depth-map ARC rule.

The unchanged Racket authority ignores foreground color, finds each 4-connected
binary component, repeatedly peels cardinal boundary layers, labels each cell by
its peel depth, and crops the combined map to the foreground bounding box.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bd8613daf5b1"
TASK_ID = GENERATOR_ID
RULE_HASH = "94cb476392e1"
VERSION = "3.0.0"
SUMMARY = (
    "A zero-background grid contains one or two thick 4-connected binary "
    "components grown around guaranteed 3x3 cores. Foreground colors are "
    "semantically ignored; scheduled striped multicolor components explicitly "
    "teach that adjacent colors belong to one shape. The rule peels cardinal "
    "boundary layers, writes each cell's onion depth, and crops the combined "
    "map to the foreground bbox."
)

INVARIANTS = [
    "background is 0 and every foreground cell uses a color in 1..8",
    "there are one or two 4-connected binary components with a one-cell canvas margin",
    "every component contains a solid 3x3 core, so its depth reaches at least 2",
    "foreground color boundaries do not split a binary component for onion peeling",
    "the output is the tight crop of the components' cardinal onion-depth map",
]

DIFFICULTIES = (None, "easy", "medium", "hard")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 9/11 schedule plus weighted full-domain draws",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 9/11 schedule plus weighted full-domain draws",
        "valid": "9..20",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

# The two monochrome teaching residues are bound to the two public
# canvas/palette profiles. The four witness residues draw broadly.
_CANONICAL_PROFILE_DIMS = {
    "monochrome_core": (9, 9),
    "monochrome_pair": (11, 11),
}

# Witness, ordinary, witness, witness, ordinary, witness. Thus every three
# consecutive demonstrations contain a multicolor counterexample; every four
# consecutive examples retain one under any single query rotation.
SCHEDULE_PROFILES = (
    "multicolor_core_a",
    "monochrome_core",
    "multicolor_core_b",
    "multicolor_core_c",
    "monochrome_pair",
    "multicolor_core_d",
)

_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_MULTICOLOR_PROFILES = {
    "multicolor_core_a",
    "multicolor_core_b",
    "multicolor_core_c",
    "multicolor_core_d",
}
_PROFILE_SIZE_RANGES = {
    "multicolor_core_a": (13, 28),
    "monochrome_core": (25, 45),
    "multicolor_core_b": (17, 35),
    "multicolor_core_c": (24, 45),
    "multicolor_core_d": (15, 40),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic teaching profile used at ``sample_index``."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty, overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of easy|medium|hard|None, got {difficulty!r}"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, lo, hi in (("grid_h", 9, 18), ("grid_w", 9, 20)):
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _weighted_dimension(ctx, axis_name, draw_label, lo, hi, difficulty):
    values = list(range(lo, hi + 1))
    if axis_name == "grid_h":
        favored = {
            None: range(9, 19),
            "easy": range(9, 13),
            "medium": range(11, 16),
            "hard": range(14, 19),
        }[difficulty]
    else:
        favored = {
            None: range(9, 21),
            "easy": range(9, 14),
            "medium": range(12, 17),
            "hard": range(16, 21),
        }[difficulty]
    choices = values + [value for value in favored for _ in range(4)]
    return ctx.draw_rng(draw_label).choice(choices)


def _effective_axes(seed, sample_index, difficulty, overrides):
    """Resolve defaults, then record both exact controls in the final GenCtx."""
    effective = dict(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled = _CANONICAL_PROFILE_DIMS.get(profile)
    if scheduled is not None:
        effective.setdefault("grid_h", scheduled[0])
        effective.setdefault("grid_w", scheduled[1])
    elif "grid_h" not in effective or "grid_w" not in effective:
        planner = gen_ctx(
            seed=seed,
            sample_index=sample_index,
            version=VERSION,
            task_id=TASK_ID,
            difficulty=difficulty,
            overrides={},
        )
        if "grid_h" not in effective:
            effective["grid_h"] = _weighted_dimension(
                planner, "grid_h", "planned_grid_h", 9, 18, difficulty
            )
        if "grid_w" not in effective:
            effective["grid_w"] = _weighted_dimension(
                planner, "grid_w", "planned_grid_w", 9, 20, difficulty
            )
    return effective


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def _random_thick_shape(rng, min_size, max_size):
    """Grow a varied connected mask around a guaranteed solid 3x3 core."""
    box_h = rng.randint(5, 7)
    box_w = rng.randint(5, 7)
    core_r = rng.randint(0, box_h - 3)
    core_c = rng.randint(0, box_w - 3)
    cells = {
        (r, c)
        for r in range(core_r, core_r + 3)
        for c in range(core_c, core_c + 3)
    }
    target = rng.randint(max(9, min_size), min(max_size, box_h * box_w))
    frontier = {
        (r + dr, c + dc)
        for r, c in cells
        for dr, dc in _CARDINAL
        if 0 <= r + dr < box_h
        and 0 <= c + dc < box_w
        and (r + dr, c + dc) not in cells
    }
    while len(cells) < target:
        choice = rng.choice(sorted(frontier))
        frontier.remove(choice)
        cells.add(choice)
        r, c = choice
        for dr, dc in _CARDINAL:
            candidate = (r + dr, c + dc)
            if (
                0 <= candidate[0] < box_h
                and 0 <= candidate[1] < box_w
                and candidate not in cells
            ):
                frontier.add(candidate)
    normalized = _normalize(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    core_center = (core_r + 1 - r0, core_c + 1 - c0)
    return normalized, core_center


def _paired_shape(rng):
    """Two independently thick components in a 7x7 local box."""
    variant = rng.randrange(3)
    if variant == 0:
        first = {(r, c) for r in range(3) for c in range(3)}
        second = {(r, c) for r in range(4, 7) for c in range(4, 7)}
    elif variant == 1:
        first = {(r, c) for r in range(4) for c in range(3)}
        second = {(r, c) for r in range(4, 7) for c in range(3, 7)}
    else:
        first = {(r, c) for r in range(3) for c in range(4)}
        second = {(r, c) for r in range(3, 7) for c in range(4, 7)}
    return first | second, None


def _shape_for_profile(profile, rng):
    if profile == "monochrome_pair":
        return _paired_shape(rng)
    min_size, max_size = _PROFILE_SIZE_RANGES[profile]
    return _random_thick_shape(rng, min_size, max_size)


def _normalize_with_point(cells, point):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    normalized = {(r - r0, c - c0) for r, c in cells}
    if point is None:
        return normalized, None
    return normalized, (point[0] - r0, point[1] - c0)


def _transform(cells, point, transform):
    result = set(cells)
    current = point
    if transform >= 4:
        width = max(c for _, c in result)
        result = {(r, width - c) for r, c in result}
        if current is not None:
            current = (current[0], width - current[1])
        result, current = _normalize_with_point(result, current)
    for _ in range(transform % 4):
        height = max(r for r, _ in result)
        result = {(c, height - r) for r, c in result}
        if current is not None:
            current = (current[1], height - current[0])
        result, current = _normalize_with_point(result, current)
    return _normalize_with_point(result, current)


def _connected_partition(cells, first_seed, second_seed, rng):
    """Partition one connected mask into exactly two connected color regions."""
    owners = {first_seed: 0, second_seed: 1}
    queue = [first_seed, second_seed]
    cursor = 0
    while cursor < len(queue):
        cell = queue[cursor]
        cursor += 1
        neighbors = [
            (cell[0] + dr, cell[1] + dc)
            for dr, dc in _CARDINAL
            if (cell[0] + dr, cell[1] + dc) in cells
            and (cell[0] + dr, cell[1] + dc) not in owners
        ]
        rng.shuffle(neighbors)
        for neighbor in neighbors:
            owners[neighbor] = owners[cell]
            queue.append(neighbor)
    if set(owners) != set(cells):
        raise RuntimeError("two-source color partition did not cover the shape")
    return owners


def _color_cells(cells, multicolor, colors, core_center, rng):
    if not multicolor:
        return {cell: colors[0] for cell in cells}
    directions = [
        (dr, dc)
        for dr, dc in _CARDINAL
        if (core_center[0] + dr, core_center[1] + dc) in cells
    ]
    dr, dc = rng.choice(directions)
    second_seed = (core_center[0] + dr, core_center[1] + dc)
    owners = _connected_partition(cells, core_center, second_seed, rng)
    colored = {cell: colors[owner] for cell, owner in owners.items()}
    if len(set(colored.values())) != 2:
        raise RuntimeError("multicolor profile failed to realize two colors")
    return colored


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    effective = _effective_axes(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 9, 18)
    w = ctx.draw_int("grid_w", 9, 20)
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("shape_layout")
    cells, core_center = _shape_for_profile(profile, rng)
    cells, core_center = _transform(cells, core_center, rng.randrange(8))
    colors = ctx.draw_distinct_colors("object_colors", n=2, exclude={0, 9})
    colored = _color_cells(
        cells,
        profile in _MULTICOLOR_PROFILES,
        colors,
        core_center,
        rng,
    )
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    if sh > h - 2 or sw > w - 2:
        raise ValueError(
            f"profile {profile} ({sh}x{sw}) cannot fit requested {h}x{w} with margin"
        )
    r0 = rng.randint(1, h - sh - 1)
    c0 = rng.randint(1, w - sw - 1)
    grid = full_grid(h, w, 0)
    for (r, c), color in colored.items():
        grid[r0 + r][c0 + c] = color
    return grid


def _foreground(value):
    return value not in (0, 9)


def _components(grid, *, split_by_color=False):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or not _foreground(grid[sr][sc]):
                continue
            color = grid[sr][sc]
            todo = [(sr, sc)]
            seen.add((sr, sc))
            component = set()
            while todo:
                r, c = todo.pop()
                component.add((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    value = grid[nr][nc]
                    if not _foreground(value):
                        continue
                    if split_by_color and value != color:
                        continue
                    seen.add((nr, nc))
                    todo.append((nr, nc))
            result.append(component)
    return result


def _has_interior(component):
    return any(
        all((r + dr, c + dc) in component for dr, dc in _CARDINAL)
        for r, c in component
    )


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 8 for row in grid for value in row):
        return ["cells must be integer colors 0..8 (9 is excluded by the rule mask)"]

    height = len(grid)
    errors = []
    if not 9 <= height <= 18:
        errors.append(f"grid height {height} outside 9..18")
    if not 9 <= width <= 20:
        errors.append(f"grid width {width} outside 9..20")
    values = {value for row in grid for value in row}
    if 0 not in values:
        errors.append("background color 0 must be present")
    if not (values - {0}):
        errors.append("at least one foreground cell is required")
        return errors

    components = _components(grid)
    if not 1 <= len(components) <= 2:
        errors.append(f"expected one or two binary components, found {len(components)}")
    for index, component in enumerate(components):
        if any(r in (0, height - 1) or c in (0, width - 1) for r, c in component):
            errors.append(f"component {index} must have a one-cell canvas margin")
        if not _has_interior(component):
            errors.append(f"component {index} has no interior cell (depth never exceeds 1)")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _onion_depth(grid, *, split_by_color=False):
    height, width = len(grid), len(grid[0])
    output = [[0] * width for _ in range(height)]
    for component in _components(grid, split_by_color=split_by_color):
        remaining = set(component)
        depth = 1
        while remaining:
            boundary = {
                (r, c)
                for r, c in remaining
                if any((r + dr, c + dc) not in remaining for dr, dc in _CARDINAL)
            }
            for r, c in boundary:
                output[r][c] = depth
            remaining.difference_update(boundary)
            depth += 1
    occupied = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if output[r][c] != 0
    ]
    if not occupied:
        return [[0]]
    r0 = min(r for r, _ in occupied)
    r1 = max(r for r, _ in occupied)
    c0 = min(c for _, c in occupied)
    c1 = max(c for _, c in occupied)
    return [row[c0:c1 + 1] for row in output[r0:r1 + 1]]


def rule_mirror(grid):
    """Diagnostic Python mirror; the selected Racket source remains authority."""
    return _onion_depth(deepcopy(grid), split_by_color=False)


def _peel_each_color_separately(grid):
    """Wrong canonical-fitting rival: treat adjacent colors as separate shapes."""
    return _onion_depth(deepcopy(grid), split_by_color=True)


def _multicolor_connected_shape(grid):
    try:
        for component in _components(grid):
            if len({grid[r][c] for r, c in component}) > 1:
                return True
    except Exception:
        return False
    return False


SEMANTIC_WITNESSES = {"multicolor_connected_shape": _multicolor_connected_shape}
SEMANTIC_RIVALS = {"peel_each_color_separately": _peel_each_color_separately}
WITNESS_RIVALS = {
    "multicolor_connected_shape": ["peel_each_color_separately"]
}
CANONICAL_SHORTCUTS = {
    "peel_each_color_separately": _peel_each_color_separately
}
LESSON_COMPETITORS = {
    "peel_each_color_separately": _peel_each_color_separately
}


def lesson_identifiable(demos, query):
    """Return any declared wrong rule that survives every demonstration."""
    problems = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(deepcopy(pair["input"])) == pair["output"] for pair in demos
            )
        except Exception as exc:
            problems.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            problems.append(f"{name} fits every demonstration")
    return problems
