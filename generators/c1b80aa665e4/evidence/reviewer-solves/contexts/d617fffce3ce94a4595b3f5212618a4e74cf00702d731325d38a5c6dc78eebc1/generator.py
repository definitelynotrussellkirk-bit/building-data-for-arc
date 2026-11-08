"""Semantic generator for ARC task c1b80aa665e4.

Orthogonally isolated foreground cells turn color 9; every cell belonging to a
multi-cell component remains unchanged.  Linked scenes preserve transformed
public occupancy masks, while generalized scenes vary component count/shape.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c1b80aa665e4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "54c7b30bb7f3"
SUMMARY = (
    "Recolor every nonzero cell with no orthogonally adjacent nonzero "
    "neighbor to 9; preserve all multi-cell foreground components."
)
EXAMPLES_NEEDED = 3

SCENE_FAMILIES = ("linked", "generalized")
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized",
        "valid": "|".join(SCENE_FAMILIES),
        "doc": "transformed public occupancy topology or a novel component mix",
    },
}
INVARIANTS = [
    "background is zero and input contains no output color 9",
    "every scene has at least two orthogonally isolated foreground cells",
    "every scene has at least one multi-cell orthogonal component",
    "isolated cells change to 9 and clustered cells remain unchanged",
    "all returned grids are rectangular ARC grids with fresh row objects",
]
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
COLORS = tuple(range(1, 9))

# Public input occupancy only: (height, width, foreground coordinates).
_PUBLIC_MASKS = (
    (5, 7, ((1, 1), (1, 4), (3, 2), (3, 3), (4, 6))),
    (5, 7, ((0, 0), (2, 3), (2, 4), (4, 6))),
    (7, 8, ((1, 1), (2, 6), (4, 2), (4, 3), (6, 3))),
)


def _grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be nonempty sequences"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return ["grid must be rectangular"]
    height, width = len(grid), next(iter(widths))
    errors = []
    if not (4 <= height <= 30 and 5 <= width <= 30):
        errors.append("grid dimensions must be height 4..30 and width 5..30")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be ARC integers 0..9")
    return errors


def _components(grid):
    height, width = len(grid), len(grid[0])
    foreground = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    result = []
    while foreground:
        start = min(foreground)
        foreground.remove(start)
        component = [start]
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in foreground:
                    foreground.remove(neighbor)
                    component.append(neighbor)
                    stack.append(neighbor)
        result.append(tuple(sorted(component)))
    return tuple(sorted(result, key=lambda cells: cells[0]))


def _normalize(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _orientations(cells):
    current = tuple(cells)
    result = set()
    for _ in range(4):
        result.add(_normalize(current))
        result.add(_normalize(tuple((row, -col) for row, col in current)))
        current = tuple((col, -row) for row, col in current)
    return result


_PUBLIC_ORIENTATIONS = tuple(
    _orientations(cells) for _, _, cells in _PUBLIC_MASKS
)


def _canonical_profile(grid):
    foreground = tuple(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != 0
    )
    if not foreground:
        return None
    normalized = _normalize(foreground)
    for index, orientations in enumerate(_PUBLIC_ORIENTATIONS):
        if normalized in orientations:
            return f"public_{index + 1}"
    return None


def _analyze(grid):
    errors = _grid_error(grid)
    if errors:
        return {"errors": errors, "facts": None}
    flat = [value for row in grid for value in row]
    if 9 in flat:
        errors.append("input must not contain output color 9")
    components = _components(grid)
    isolated = tuple(cells[0] for cells in components if len(cells) == 1)
    clusters = tuple(cells for cells in components if len(cells) >= 2)
    if len(isolated) < 2:
        errors.append("input must contain at least two isolated cells")
    if not clusters:
        errors.append("input must contain at least one multi-cell component")
    profile = _canonical_profile(grid)
    return {
        "errors": errors,
        "facts": {
            "height": len(grid),
            "width": len(grid[0]),
            "components": components,
            "isolated": isolated,
            "clusters": clusters,
            "n_isolated": len(isolated),
            "n_clusters": len(clusters),
            "cluster_sizes": tuple(sorted(len(cells) for cells in clusters)),
            "colors": tuple(sorted(set(flat) - {0})),
            "canonical_profile": profile,
            "scene_family": "linked" if profile else "generalized",
        },
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["scene_family"]}


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    facts = analysis["facts"]
    return facts["canonical_profile"] or (
        f"generalized:{facts['n_isolated']}:{facts['cluster_sizes']}"
    )


def rule_mirror(grid):
    """Independent Python mirror used only by focused tests."""
    output = copy.deepcopy(grid)
    for component in _components(grid):
        if len(component) == 1:
            row, col = component[0]
            output[row][col] = 9
    return output


def _transform(cells, orientation):
    result = tuple(cells)
    rotations, reflect = orientation
    if reflect:
        result = tuple((row, -col) for row, col in result)
    for _ in range(rotations):
        result = tuple((col, -row) for row, col in result)
    return _normalize(result)


def _paint_components(grid, cells, colors):
    cell_set = set(cells)
    components = []
    while cell_set:
        start = min(cell_set)
        cell_set.remove(start)
        component = [start]
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in cell_set:
                    cell_set.remove(neighbor)
                    component.append(neighbor)
                    stack.append(neighbor)
        components.append(component)
    for index, component in enumerate(components):
        color = colors[index % len(colors)]
        for row, col in component:
            grid[row][col] = color


def _build_linked(ctx, rng, difficulty):
    _, _, public = rng.choice(_PUBLIC_MASKS)
    cells = _transform(
        public,
        (rng.randrange(4), rng.random() < 0.5),
    )
    content_height = max(row for row, _ in cells) + 1
    content_width = max(col for _, col in cells) + 1
    if difficulty == "easy":
        extra_height, extra_width = rng.randint(0, 2), rng.randint(0, 2)
    elif difficulty == "hard":
        extra_height, extra_width = rng.randint(4, 10), rng.randint(4, 10)
    else:
        extra_height, extra_width = rng.randint(0, 5), rng.randint(0, 5)
    height = max(4, min(30, content_height + extra_height))
    width = max(5, min(30, content_width + extra_width))
    row_shift = rng.randint(0, height - content_height)
    col_shift = rng.randint(0, width - content_width)
    placed = tuple(
        (row + row_shift, col + col_shift) for row, col in cells
    )
    component_count = len(
        _components(
            [
                [
                    1 if (row, col) in set(cells) else 0
                    for col in range(content_width)
                ]
                for row in range(content_height)
            ]
        )
    )
    palette_count = rng.randint(1, component_count)
    palette = list(ctx.draw_distinct_colors(
        "linked_colors",
        n=palette_count,
        exclude={0, 9},
    ))
    grid = full_grid(height, width, 0)
    _paint_components(grid, placed, palette)
    return grid


def _free_with_cardinal_margin(grid, cells):
    height, width = len(grid), len(grid[0])
    candidate = set(cells)
    if any(
        not (0 <= row < height and 0 <= col < width)
        for row, col in candidate
    ):
        return False
    forbidden = set(candidate)
    for row, col in candidate:
        forbidden.update(
            ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
        )
    return all(
        not (0 <= row < height and 0 <= col < width)
        or grid[row][col] == 0
        for row, col in forbidden
    )


def _random_walk(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(sorted(cells))
        delta = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        cells.add((row + delta[0], col + delta[1]))
    return _normalize(tuple(cells))


def _generalized_dimensions(ctx, difficulty):
    if difficulty == "easy":
        choices = [
            (height, width)
            for height in range(5, 9)
            for width in range(6, 11)
        ]
    elif difficulty == "hard":
        choices = [
            (height, width)
            for height in range(11, 17)
            for width in range(13, 21)
        ]
    else:
        choices = [
            (height, width)
            for height in range(7, 13)
            for width in range(8, 16)
        ]
    return ctx.draw_choice("dimensions", choices)


def _build_generalized(ctx, rng, difficulty):
    height, width = _generalized_dimensions(ctx, difficulty)
    for attempt in range(60):
        grid = full_grid(height, width, 0)
        if difficulty == "easy":
            isolated_count = rng.randint(2, 3)
            cluster_sizes = [rng.randint(3, 4)]
        elif difficulty == "hard":
            isolated_count = rng.randint(4, 7)
            cluster_sizes = [
                rng.randint(2, 6) for _ in range(rng.randint(2, 4))
            ]
        else:
            isolated_count = rng.randint(3, 5)
            cluster_sizes = [
                rng.randint(2, 5) for _ in range(rng.randint(1, 3))
            ]
            if len(cluster_sizes) == 1 and cluster_sizes[0] == 2:
                cluster_sizes[0] = 3
        components = [_random_walk(rng, size) for size in cluster_sizes]
        placed_components = []
        failed = False
        for component in components:
            component_height = max(row for row, _ in component) + 1
            component_width = max(col for _, col in component) + 1
            placed = None
            for _ in range(100):
                row0 = rng.randint(0, height - component_height)
                col0 = rng.randint(0, width - component_width)
                candidate = tuple(
                    (row + row0, col + col0) for row, col in component
                )
                if _free_with_cardinal_margin(grid, candidate):
                    placed = candidate
                    break
            if placed is None:
                failed = True
                break
            placed_components.append(placed)
            for row, col in placed:
                grid[row][col] = 1
        if failed:
            continue
        isolated = []
        for _ in range(isolated_count):
            placed = None
            for _ in range(120):
                candidate = ((rng.randrange(height), rng.randrange(width)),)
                if _free_with_cardinal_margin(grid, candidate):
                    placed = candidate[0]
                    break
            if placed is None:
                failed = True
                break
            isolated.append((placed,))
            grid[placed[0]][placed[1]] = 1
        if failed:
            continue
        all_components = placed_components + isolated
        palette_count = rng.randint(1, min(len(all_components), 8))
        palette = list(ctx.draw_distinct_colors(
            f"generalized_colors_{attempt}",
            n=palette_count,
            exclude={0, 9},
        ))
        rng.shuffle(palette)
        grid = full_grid(height, width, 0)
        for index, component in enumerate(all_components):
            color = palette[index % len(palette)]
            for row, col in component:
                grid[row][col] = color
        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["scene_family"] == "generalized"
        ):
            return grid
    raise RuntimeError("could not construct generalized isolated-cell scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
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
    family = ctx.draw_choice("scene_family", SCENE_FAMILIES)
    rng = ctx.draw_rng("scene")
    band = "medium" if difficulty in (None, "default") else difficulty
    grid = (
        _build_linked(ctx, rng, band)
        if family == "linked"
        else _build_generalized(ctx, rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["scene_family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {family}, observed "
                    f"{analysis['facts']['scene_family']}"
                ]
            )
        )
    return grid
