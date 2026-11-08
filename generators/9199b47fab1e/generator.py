"""Generator for ARC task 9199b47fab1e: barrier-aware distance bands.

Color 2 cells are simultaneous BFS sources.  Traversal is cardinal and may
enter only cells colored 0 or 2; every other color is an impassable wall.
Reachable cells are recolored by shortest-path distance modulo three
(0 -> 3, 1 -> 4, 2 -> 5), while walls and unreachable cells are preserved.

Ordinary instances use canonical-scale chamber geometry.  A closed outer
barrier always separates a seedless exterior from seeded interior space, so
every single example visibly distinguishes the intended barrier-aware rule
from the plausible shortcut that uses Manhattan distance through walls.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9199b47fab1e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b0749d721740"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "One to three color-2 seeds occupy canonical-scale chambers bounded by a "
    "single color from 6/7/8/9. Cardinal BFS may cross only 0/2 cells. Every "
    "reachable cell is recolored by distance mod 3 as 3/4/5; walls and "
    "unreachable chambers remain unchanged. A closed outer barrier makes wall "
    "blocking answer-changing in every ordinary example; a three-slot wall-color "
    "schedule also refutes the canonical-fitting color-8-only shortcut."
)

INVARIANTS = [
    "the grid uses background 0, one wall color in 6..9, and 1..3 color-2 seeds",
    "walls separate at least one seeded traversable component from a seedless component",
    "color-2 cells are simultaneous cardinal-BFS sources through only colors 0 and 2",
    "reachable cells become 3/4/5 according to shortest-path distance modulo three",
    "walls and unreachable cells retain their input colors",
]

SHAPE_OPTIONS = (
    "9x9",
    "9x13",
    "10x12",
    "11x11",
    "11x13",
    "12x14",
    "14x16",
    "16x18",
    "18x20",
)
_CANONICAL_SHAPES = ("9x9", "9x13", "10x12", "11x11", "11x13")
_WALL_COLORS = (6, 7, 8, 9)
_LAYOUT_PROFILES = (
    "box",
    "vertical_split",
    "horizontal_split",
    "cross",
    "inner_box",
    "vertical_gate",
    "double_split",
    "staggered",
)
SCHEDULE_PROFILES = _LAYOUT_PROFILES

# These are the only exact public controls.  Each is recoverable from the
# returned pixels by observe_overrides(), and every value is legal in every
# difficulty band.
AXES = {
    "shape": {
        "type": "str",
        "default": "canonical-weighted keyed draw",
        "valid": "|".join(SHAPE_OPTIONS),
    },
    "n_seeds": {
        "type": "int",
        "default": "keyed draw over 1..3",
        "valid": "1..3",
    },
    "wall_color": {
        "type": "color",
        "default": "canonical-weighted keyed draw",
        "valid": "6|7|8|9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the deterministic chamber-grammar profile used for this draw."""
    del seed, difficulty
    return _LAYOUT_PROFILES[int(sample_index) % len(_LAYOUT_PROFILES)]


def _shape_options(difficulty: str | None) -> tuple[str, ...]:
    """Weighted defaults with full-band override support.

    Canonical dimensions remain common in every band, while all nine declared
    shapes have nonzero default support.  Difficulty changes only the weighting,
    never the legal domain.
    """
    canonical_weight = {"easy": 8, "medium": 6, "hard": 4}.get(difficulty, 6)
    broad_weight = {"easy": 1, "medium": 2, "hard": 4}.get(difficulty, 2)
    canonical = tuple(shape for shape in _CANONICAL_SHAPES for _ in range(canonical_weight))
    broad = tuple(shape for shape in SHAPE_OPTIONS for _ in range(broad_weight))
    return canonical + broad


def _validate_override_types(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    if "shape" in overrides and overrides["shape"] is not None:
        if type(overrides["shape"]) is not str:
            raise TypeError("shape override must be a string")
        if overrides["shape"] not in SHAPE_OPTIONS:
            raise ValueError(f"shape override must be one of {SHAPE_OPTIONS}")
    if "n_seeds" in overrides and overrides["n_seeds"] is not None:
        if type(overrides["n_seeds"]) is not int:
            raise TypeError("n_seeds override must be an integer (not bool)")
        if overrides["n_seeds"] not in (1, 2, 3):
            raise ValueError("n_seeds override must be in 1..3")
    if "wall_color" in overrides and overrides["wall_color"] is not None:
        if type(overrides["wall_color"]) is not int:
            raise TypeError("wall_color override must be an integer ARC color (not bool)")
        if overrides["wall_color"] not in _WALL_COLORS:
            raise ValueError("wall_color override must be one of 6, 7, 8, 9")


def _parse_shape(shape: str) -> tuple[int, int]:
    h_text, w_text = shape.split("x", 1)
    return int(h_text), int(w_text)


def _draw_wall_color(ctx, sample_index: int) -> int:
    """Three-slot curriculum: 8, non-8, non-8.

    Every three consecutive demonstrations therefore contains a counterexample
    to the canonical-fitting shortcut that hard-codes color 8 as the only wall.
    The override branch still exposes the complete declared domain.
    """
    if ctx.overrides.get("wall_color") is not None:
        return ctx.draw_choice("wall_color", _WALL_COLORS)
    cycle = (6, 7, 9)
    block = int(sample_index) // 3
    phase = int(sample_index) % 3
    if phase == 0:
        scheduled = 8
    elif phase == 1:
        scheduled = cycle[block % len(cycle)]
    else:
        scheduled = cycle[(block + 1) % len(cycle)]
    return ctx.draw_choice("wall_color", (scheduled,))


def _paint_frame(grid: list[list[int]], top: int, left: int, bottom: int, right: int, color: int) -> None:
    for c in range(left, right + 1):
        grid[top][c] = color
        grid[bottom][c] = color
    for r in range(top + 1, bottom):
        grid[r][left] = color
        grid[r][right] = color


def _interior_column(width: int, rng) -> int:
    return rng.choice(list(range(3, width - 3)))


def _interior_row(height: int, rng) -> int:
    return rng.choice(list(range(3, height - 3)))


def _draw_chambers(
    height: int,
    width: int,
    wall_color: int,
    profile: str,
    rng,
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    # Canonical signature: a one-cell zero moat surrounds a closed wall frame.
    _paint_frame(grid, 1, 1, height - 2, width - 2, wall_color)

    if profile == "box":
        return grid

    if profile == "vertical_split":
        column = _interior_column(width, rng)
        for row in range(1, height - 1):
            grid[row][column] = wall_color
        return grid

    if profile == "horizontal_split":
        row = _interior_row(height, rng)
        for column in range(1, width - 1):
            grid[row][column] = wall_color
        return grid

    if profile == "cross":
        row = _interior_row(height, rng)
        column = _interior_column(width, rng)
        for c in range(1, width - 1):
            grid[row][c] = wall_color
        for r in range(1, height - 1):
            grid[r][column] = wall_color
        return grid

    if profile == "inner_box":
        # Leave at least one open cell between the nested frame and outer frame.
        top = rng.randint(3, max(3, height // 2 - 1))
        left = rng.randint(3, max(3, width // 2 - 1))
        bottom = rng.randint(max(top + 2, height // 2 + 1), height - 4)
        right = rng.randint(max(left + 2, width // 2 + 1), width - 4)
        _paint_frame(grid, top, left, bottom, right, wall_color)
        return grid

    if profile == "vertical_gate":
        column = _interior_column(width, rng)
        gap = _interior_row(height, rng)
        for row in range(1, height - 1):
            if row != gap:
                grid[row][column] = wall_color
        return grid

    if profile == "double_split":
        available = list(range(3, width - 3))
        left = available[len(available) // 3]
        right = available[(2 * len(available)) // 3]
        if left == right:
            right = min(width - 4, left + 2)
        if right - left < 2:
            left, right = 3, width - 4
        for column in (left, right):
            for row in range(1, height - 1):
                grid[row][column] = wall_color
        return grid

    if profile == "staggered":
        available = list(range(3, width - 3))
        first = available[len(available) // 3]
        second = available[(2 * len(available)) // 3]
        if first == second:
            second = min(width - 4, first + 2)
        upper_end = max(3, height // 2)
        lower_start = min(height - 4, height // 2)
        for row in range(1, upper_end + 1):
            grid[row][first] = wall_color
        for row in range(lower_start, height - 1):
            grid[row][second] = wall_color
        return grid

    raise ValueError(f"unknown layout profile {profile!r}")


def _open_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] not in (0, 2) or (row, column) in seen:
                continue
            component: list[tuple[int, int]] = []
            queue = deque([(row, column)])
            seen.add((row, column))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] in (0, 2)
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)
    return components


def _place_seeds(grid: list[list[int]], n_seeds: int, rng) -> None:
    height, width = len(grid), len(grid[0])
    interior_components = [
        component
        for component in _open_components(grid)
        if not any(r in (0, height - 1) or c in (0, width - 1) for r, c in component)
        and len(component) >= 4
    ]
    if not interior_components:
        raise ValueError("chamber grammar produced no seedable interior component")

    rng.shuffle(interior_components)
    chosen: list[tuple[int, int]] = []
    for index in range(n_seeds):
        component = interior_components[index % len(interior_components)]
        # Prefer cells not immediately touching a wall; fall back for narrow
        # canonical chambers.  Also keep sources separated when space permits.
        preferred = [
            (r, c)
            for r, c in component
            if all(
                0 <= r + dr < height
                and 0 <= c + dc < width
                and grid[r + dr][c + dc] in (0, 2)
                for dr, dc in _CARDINAL
            )
            and all(abs(r - pr) + abs(c - pc) >= 2 for pr, pc in chosen)
        ]
        candidates = preferred or [
            point
            for point in component
            if point not in chosen
            and all(abs(point[0] - pr) + abs(point[1] - pc) >= 2 for pr, pc in chosen)
        ]
        candidates = candidates or [point for point in component if point not in chosen]
        if not candidates:
            raise ValueError("chamber grammar cannot place requested distinct seeds")
        point = rng.choice(candidates)
        chosen.append(point)
        grid[point[0]][point[1]] = 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic authority-compatible input grid."""
    _validate_override_types(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    shape = ctx.draw_choice("shape", _shape_options(difficulty))
    n_seeds = ctx.draw_choice("n_seeds", (1, 1, 1, 2, 2, 3))
    wall_color = _draw_wall_color(ctx, sample_index)
    height, width = _parse_shape(shape)
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("chamber_geometry")
    grid = _draw_chambers(height, width, wall_color, profile, rng)
    _place_seeds(grid, n_seeds, rng)
    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal chamber grammar violation: {errors}")
    return grid


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact public axis from returned pixels."""
    wall_colors = sorted({value for row in grid for value in row if value not in (0, 2)})
    if len(wall_colors) != 1:
        raise ValueError(f"expected one wall color, found {wall_colors}")
    return {
        "shape": f"{len(grid)}x{len(grid[0])}",
        "n_seeds": sum(value == 2 for row in grid for value in row),
        "wall_color": wall_colors[0],
    }


def _wall_components(grid: list[list[int]], wall_color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] != wall_color or (row, column) in seen:
                continue
            component: list[tuple[int, int]] = []
            queue = deque([(row, column)])
            seen.add((row, column))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == wall_color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(component)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical chamber manifold without mutating ``grid``."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty 2D list"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid rows must be rectangular and non-empty"]
    height = len(grid)

    errors: list[str] = []
    shape = f"{height}x{width}"
    if shape not in SHAPE_OPTIONS:
        errors.append(f"shape {shape} is outside the canonical-scale domain")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an integer ARC color: {value!r}")
    if errors:
        return errors

    seeds = sum(value == 2 for row in grid for value in row)
    if not 1 <= seeds <= 3:
        errors.append(f"expected 1..3 color-2 seeds, found {seeds}")

    wall_colors = sorted({value for row in grid for value in row if value not in (0, 2)})
    if len(wall_colors) != 1:
        errors.append(f"expected exactly one wall color, found {wall_colors}")
        return errors
    wall_color = wall_colors[0]
    if wall_color not in _WALL_COLORS:
        errors.append(f"wall color must be one of {_WALL_COLORS}, found {wall_color}")
        return errors

    wall_components = _wall_components(grid, wall_color)
    wall_cells = sum(len(component) for component in wall_components)
    if wall_cells < 8:
        errors.append(f"wall support is too small to define a chamber: {wall_cells} cells")
    if not wall_components or max(map(len, wall_components)) < 8:
        errors.append("no substantial connected wall barrier")

    components = _open_components(grid)
    if len(components) < 2:
        errors.append("walls do not separate traversable space into multiple components")
    seeded_sizes: list[int] = []
    seedless_sizes: list[int] = []
    for component in components:
        if any(grid[r][c] == 2 for r, c in component):
            seeded_sizes.append(len(component))
        else:
            seedless_sizes.append(len(component))
    if not seeded_sizes:
        errors.append("no traversable component contains a color-2 source")
    elif sum(seeded_sizes) < 4:
        errors.append("seeded reachable support is too small to expose distance bands")
    if not seedless_sizes:
        errors.append("no unreachable traversable component demonstrates wall blocking")
    elif max(seedless_sizes) < 4:
        errors.append("unreachable component is too small to be a meaningful wall-blocking witness")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Input-pure Python mirror for tests and adversarial semantic probes."""
    if not grid or not grid[0]:
        raise ValueError("expected a non-empty grid")
    height, width = len(grid), len(grid[0])
    distances: dict[tuple[int, int], int] = {}
    queue: deque[tuple[int, int]] = deque()
    for row in range(height):
        if len(grid[row]) != width:
            raise ValueError("ragged grid")
        for column in range(width):
            if grid[row][column] == 2:
                distances[(row, column)] = 0
                queue.append((row, column))
    while queue:
        row, column = queue.popleft()
        for dr, dc in _CARDINAL:
            nr, nc = row + dr, column + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and (nr, nc) not in distances
                and grid[nr][nc] in (0, 2)
            ):
                distances[(nr, nc)] = distances[(row, column)] + 1
                queue.append((nr, nc))
    output = deepcopy(grid)
    colors = (3, 4, 5)
    for (row, column), distance in distances.items():
        output[row][column] = colors[distance % 3]
    return output


def nearest_seed_manhattan_ignoring_walls(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: preserve walls but let distance pass through them."""
    seeds = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    output = deepcopy(grid)
    if not seeds:
        return output
    colors = (3, 4, 5)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 2):
                distance = min(abs(r - sr) + abs(c - sc) for sr, sc in seeds)
                output[r][c] = colors[distance % 3]
    return output


def color_8_only_barrier(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: only color 8 blocks propagation.

    All other pixels are treated as traversable background and recolored.  This
    exactly matches every public pair because their sole barrier color is 8, but
    it fails generated examples whose wall color is 6, 7, or 9.
    """
    if not grid or not grid[0]:
        raise ValueError("expected a non-empty grid")
    height, width = len(grid), len(grid[0])
    distances: dict[tuple[int, int], int] = {}
    queue: deque[tuple[int, int]] = deque()
    for row in range(height):
        if len(grid[row]) != width:
            raise ValueError("ragged grid")
        for column in range(width):
            if grid[row][column] == 2:
                distances[(row, column)] = 0
                queue.append((row, column))
    while queue:
        row, column = queue.popleft()
        for dr, dc in _CARDINAL:
            nr, nc = row + dr, column + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and (nr, nc) not in distances
                and grid[nr][nc] != 8
            ):
                distances[(nr, nc)] = distances[(row, column)] + 1
                queue.append((nr, nc))
    output = deepcopy(grid)
    colors = (3, 4, 5)
    for (row, column), distance in distances.items():
        output[row][column] = colors[distance % 3]
    return output


def _wall_blocks_propagation(grid: list[list[int]]) -> bool:
    components = _open_components(grid)
    return (
        any(any(grid[r][c] == 2 for r, c in component) for component in components)
        and any(not any(grid[r][c] == 2 for r, c in component) for component in components)
        and nearest_seed_manhattan_ignoring_walls(grid) != rule_mirror(grid)
    )


def _non_8_wall_color(grid: list[list[int]]) -> bool:
    wall_colors = {value for row in grid for value in row if value not in (0, 2)}
    return (
        len(wall_colors) == 1
        and next(iter(wall_colors)) != 8
        and color_8_only_barrier(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "wall_blocks_propagation": _wall_blocks_propagation,
    "non_8_wall_color": _non_8_wall_color,
}
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "nearest_seed_manhattan_ignoring_walls": nearest_seed_manhattan_ignoring_walls,
    "color_8_only_barrier": color_8_only_barrier,
}
WITNESS_RIVALS = {
    "wall_blocks_propagation": ["nearest_seed_manhattan_ignoring_walls"],
    "non_8_wall_color": ["color_8_only_barrier"],
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "color_8_only_barrier": color_8_only_barrier,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a declared rival alive."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:  # diagnostic contract; never hide malformed lessons
            reasons.append(f"pair {index} input is invalid: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with barrier-aware BFS")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
