"""Semantic generator for ARC task 4ebdc8d865ce.

Isolated color-2 cells become color 1; every color-2 cell with an orthogonal
color-2 neighbor stays color 2.  Linked scenes transform public occupancy
masks, while generalized scenes construct bounded independent components.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "4ebdc8d865ce"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6c1ad8a5edc2"
SUMMARY = (
    "Recolor each isolated 2 to 1 and preserve every 2 having at least one "
    "orthogonal 2-neighbor."
)
EXAMPLES_NEEDED = 5

SCENE_FAMILIES = ("linked", "generalized")
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized",
        "valid": "|".join(SCENE_FAMILIES),
        "doc": "transformed public occupancy topology or novel components",
    },
}
INVARIANTS = [
    "input contains only background 0 and foreground 2",
    "every scene contains at least one isolated 2 that changes to 1",
    "every scene contains at least one multi-cell component that stays 2",
    "distinct components have no orthogonal contact",
    "generation is bounded, deterministic, and returns fresh grids",
]
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

# Public input occupancy only: (height, width, foreground coordinates).
_PUBLIC_MASKS = (
    (5, 4, ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (2, 3), (4, 1), (4, 2), (4, 3))),
    (4, 4, ((0, 0), (0, 1), (0, 2), (1, 1), (2, 3), (3, 1))),
    (3, 3, ((0, 0), (0, 1), (1, 0), (1, 2), (2, 1))),
    (3, 3, ((0, 1), (0, 2), (1, 1), (1, 2), (2, 0))),
    (5, 4, ((0, 0), (0, 1), (0, 3), (1, 1), (2, 2), (3, 0), (4, 2), (4, 3))),
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
    if not (3 <= height <= 30 and 3 <= width <= 30):
        errors.append("grid dimensions must be 3..30")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or value not in (0, 2)
        for row in grid
        for value in row
    ):
        errors.append("input cells must be integers from {0, 2}")
    return errors


def _components(grid):
    foreground = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 2
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
    cells = tuple(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 2
    )
    if not cells:
        return None
    normalized = _normalize(cells)
    for index, orientations in enumerate(_PUBLIC_ORIENTATIONS):
        if normalized in orientations:
            return f"public_{index + 1}"
    return None


def _analyze(grid):
    errors = _grid_error(grid)
    if errors:
        return {"errors": errors, "facts": None}
    components = _components(grid)
    isolated = tuple(cells[0] for cells in components if len(cells) == 1)
    groups = tuple(cells for cells in components if len(cells) >= 2)
    if not isolated:
        errors.append("input must contain at least one isolated 2")
    if not groups:
        errors.append("input must contain at least one grouped 2 component")
    profile = _canonical_profile(grid)
    return {
        "errors": errors,
        "facts": {
            "height": len(grid),
            "width": len(grid[0]),
            "components": components,
            "isolated": isolated,
            "groups": groups,
            "n_isolated": len(isolated),
            "n_groups": len(groups),
            "group_sizes": tuple(sorted(len(cells) for cells in groups)),
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
        f"generalized:{facts['n_isolated']}:{facts['group_sizes']}"
    )


def rule_mirror(grid):
    """Independent Python mirror used only by focused tests."""
    output = copy.deepcopy(grid)
    for component in _components(grid):
        if len(component) == 1:
            row, col = component[0]
            output[row][col] = 1
    return output


def _transform(cells, rotations, reflect):
    result = tuple(cells)
    if reflect:
        result = tuple((row, -col) for row, col in result)
    for _ in range(rotations):
        result = tuple((col, -row) for row, col in result)
    return _normalize(result)


def _build_linked(rng, difficulty):
    _, _, public = rng.choice(_PUBLIC_MASKS)
    cells = _transform(public, rng.randrange(4), rng.random() < 0.5)
    content_height = max(row for row, _ in cells) + 1
    content_width = max(col for _, col in cells) + 1
    if difficulty == "easy":
        extra_height, extra_width = rng.randint(0, 1), rng.randint(0, 1)
    elif difficulty == "hard":
        extra_height, extra_width = rng.randint(3, 9), rng.randint(3, 9)
    else:
        extra_height, extra_width = rng.randint(0, 4), rng.randint(0, 4)
    height = min(30, content_height + extra_height)
    width = min(30, content_width + extra_width)
    row_shift = rng.randint(0, height - content_height)
    col_shift = rng.randint(0, width - content_width)
    grid = full_grid(height, width, 0)
    for row, col in cells:
        grid[row + row_shift][col + col_shift] = 2
    return grid


def _random_walk(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(sorted(cells))
        delta = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        cells.add((row + delta[0], col + delta[1]))
    return _normalize(tuple(cells))


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


def _generalized_dimensions(ctx, difficulty):
    if difficulty == "easy":
        choices = [
            (height, width)
            for height in range(4, 8)
            for width in range(4, 8)
        ]
    elif difficulty == "hard":
        choices = [
            (height, width)
            for height in range(10, 15)
            for width in range(10, 17)
        ]
    else:
        choices = [
            (height, width)
            for height in range(6, 11)
            for width in range(6, 12)
        ]
    return ctx.draw_choice("dimensions", choices)


def _build_generalized(ctx, rng, difficulty):
    height, width = _generalized_dimensions(ctx, difficulty)
    for _attempt in range(60):
        if difficulty == "easy":
            group_sizes = [rng.randint(2, 4)]
            isolated_count = rng.randint(1, 2)
        elif difficulty == "hard":
            group_sizes = [
                rng.randint(2, 8) for _ in range(rng.randint(2, 4))
            ]
            isolated_count = rng.randint(3, 6)
        else:
            group_sizes = [
                rng.randint(2, 6) for _ in range(rng.randint(1, 3))
            ]
            isolated_count = rng.randint(2, 4)
        # Prevent generalized scenes from collapsing onto public masks.
        if len(group_sizes) == 1 and group_sizes[0] in (2, 4):
            group_sizes[0] = 3
        grid = full_grid(height, width, 0)
        failed = False
        for size in group_sizes:
            component = _random_walk(rng, size)
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
            for row, col in placed:
                grid[row][col] = 2
        if failed:
            continue
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
            grid[placed[0]][placed[1]] = 2
        if failed:
            continue
        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["scene_family"] == "generalized"
        ):
            return grid
    raise RuntimeError("could not construct generalized grouped/isolated scene")


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
        _build_linked(rng, band)
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
