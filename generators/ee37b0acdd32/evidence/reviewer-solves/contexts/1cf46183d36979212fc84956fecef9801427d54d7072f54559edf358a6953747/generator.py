"""Generator for ARC task ee37b0acdd32 — keep the marker-to-marker object path.

The input is a zero-background contact graph of monochrome components.  Blue(1)
and red(2) are singleton endpoint markers.  The component-contact graph is a
tree with one to two real dead-end branches, so the blue-to-red route is unique.
The rule erases every component off that route and paints every route cell 8.

Three scheduled lesson profiles deliberately defeat shortcuts that happened to
fit the canonical examples: retaining every connected object, retaining only
large objects plus endpoints, and selecting globally by route colors.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ee37b0acdd32"
TASK_ID = "ee37b0acdd32"
VERSION = "4.0.0"
RULE_HASH = "5db437049d2b"

SUMMARY = (
    "A zero-background tree of touching monochrome components has singleton "
    "blue(1) and red(2) endpoints, a unique 4..6-object route between them, "
    "and 1..2 attached dead-end branches. Paint every cell of the unique "
    "blue-to-red component path color 8 and erase all off-path components."
)

INVARIANTS = [
    "background is 0 and every nonzero object is a monochrome 4-component",
    "there is exactly one singleton blue(1) component and one singleton red(2) component",
    "the component-contact graph is one tree",
    "the unique blue-to-red path contains 4..6 components",
    "one or two off-path components are degree-one leaves attached to the route",
    "at least one non-endpoint route component has multiple cells",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 8|10|10", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "scheduled 10|11|13", "valid": "10..16"},
    "path_len": {"type": "int", "default": "scheduled 4|5|6", "valid": "4..6"},
    "branch_count": {"type": "int", "default": "scheduled 1|2|2", "valid": "1..2"},
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SCHEDULE_PROFILES = ("straight", "elbow", "zigzag")
_PROFILE_DEFAULTS = {
    "straight": (8, 10, 4, 1),
    "elbow": (10, 11, 5, 2),
    "zigzag": (10, 13, 6, 2),
}
_AXIS_BOUNDS = {
    "grid_h": (8, 14),
    "grid_w": (10, 16),
    "path_len": (4, 6),
    "branch_count": (1, 2),
}
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))

Cell = tuple[int, int]
Grid = list[list[int]]

_PATH_TEMPLATES: dict[str, dict[int, list[Cell]]] = {
    "straight": {
        4: [(1, 0), (1, 1), (1, 2), (1, 3)],
        5: [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4)],
        # Compact induced route so every legal axis combination fits 8x10.
        6: [(0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 3)],
    },
    "elbow": {
        4: [(0, 0), (0, 1), (1, 1), (2, 1)],
        5: [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
        6: [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3)],
    },
    "zigzag": {
        4: [(0, 0), (0, 1), (1, 1), (1, 2)],
        5: [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],
        6: [(0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 3)],
    },
}


def _neighbors(cell: Cell) -> Iterable[Cell]:
    r, c = cell
    for dr, dc in _NEIGHBORS:
        yield r + dr, c + dc


def _extract_components(grid: Grid) -> tuple[list[set[Cell]], list[int]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[set[Cell]] = []
    colors: list[int] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            component = {(r, c)}
            seen.add((r, c))
            stack = [(r, c)]
            while stack:
                cell = stack.pop()
                for nr, nc in _neighbors(cell):
                    if not (0 <= nr < h and 0 <= nc < w):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    component.add((nr, nc))
                    stack.append((nr, nc))
            components.append(component)
            colors.append(color)
    return components, colors


def _shortest_path_data(
    adjacency: list[set[int]], start: int, goal: int
) -> tuple[list[int], int]:
    distance = {start: 0}
    parent: dict[int, int | None] = {start: None}
    ways = {start: 1}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for nxt in sorted(adjacency[current]):
            candidate = distance[current] + 1
            if nxt not in distance:
                distance[nxt] = candidate
                parent[nxt] = current
                ways[nxt] = ways[current]
                queue.append(nxt)
            elif distance[nxt] == candidate:
                ways[nxt] = min(2, ways[nxt] + ways[current])
    if goal not in distance:
        return [], 0
    path: list[int] = []
    current: int | None = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path, ways[goal]


def _analyze(grid) -> dict[str, object]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if not 8 <= h <= 14:
        errors.append(f"grid height {h} outside 8..14")
    if not 10 <= w <= 16:
        errors.append(f"grid width {w} outside 10..16")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid color {value!r}")
    if errors:
        return {"errors": errors}

    components, colors = _extract_components(grid)
    if not components:
        return {"errors": ["expected nonzero components"]}
    cell_to_component = {
        cell: index for index, component in enumerate(components) for cell in component
    }
    adjacency = [set() for _ in components]
    for cell, first in cell_to_component.items():
        for nxt in _neighbors(cell):
            second = cell_to_component.get(nxt)
            if second is None or second == first:
                continue
            adjacency[first].add(second)
            adjacency[second].add(first)

    blue = [index for index, color in enumerate(colors) if color == 1]
    red = [index for index, color in enumerate(colors) if color == 2]
    if len(blue) != 1:
        errors.append(f"expected exactly one blue component, got {len(blue)}")
    if len(red) != 1:
        errors.append(f"expected exactly one red component, got {len(red)}")

    edge_count = sum(map(len, adjacency)) // 2
    connected: set[int] = set()
    if components:
        stack = [0]
        connected.add(0)
        while stack:
            current = stack.pop()
            for nxt in adjacency[current]:
                if nxt not in connected:
                    connected.add(nxt)
                    stack.append(nxt)
    graph_is_tree = len(connected) == len(components) and edge_count == len(components) - 1
    if len(connected) != len(components):
        errors.append("all nonzero components must belong to one contact graph")
    if not graph_is_tree:
        errors.append("component-contact graph must be a tree")

    path: list[int] = []
    path_count = 0
    if len(blue) == len(red) == 1:
        path, path_count = _shortest_path_data(adjacency, blue[0], red[0])
        if not path:
            errors.append("blue and red components are disconnected")
        if path_count != 1:
            errors.append(
                "expected one unique shortest blue-to-red path, found "
                + ("multiple" if path_count > 1 else "none")
            )
        if path and not 4 <= len(path) <= 6:
            errors.append(f"blue-to-red path has {len(path)} components, expected 4..6")
        if len(components[blue[0]]) != 1 or len(components[red[0]]) != 1:
            errors.append("blue and red endpoint components must be single cells")
        if path and not any(len(components[index]) > 1 for index in path[1:-1]):
            errors.append("route needs a multi-cell non-endpoint component")

    path_set = set(path)
    off_path = [index for index in range(len(components)) if index not in path_set]
    if path and not 1 <= len(off_path) <= 2:
        errors.append(f"expected 1..2 off-path branches, got {len(off_path)}")
    degrees = [len(neighbors) for neighbors in adjacency]
    for index in off_path:
        if degrees[index] != 1:
            errors.append(f"off-path component {index} must be a degree-one leaf")
        elif next(iter(adjacency[index])) not in path_set:
            errors.append(f"off-path component {index} must attach directly to the route")

    output = full_grid(h, w, 0)
    for index in path:
        for r, c in components[index]:
            output[r][c] = 8
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "components": components,
        "colors": colors,
        "adjacency": adjacency,
        "degrees": degrees,
        "graph_is_tree": graph_is_tree,
        "edge_count": edge_count,
        "blue_index": blue[0] if len(blue) == 1 else None,
        "red_index": red[0] if len(red) == 1 else None,
        "path_indices": path,
        "path_len": len(path),
        "shortest_path_count": path_count,
        "off_path_indices": off_path,
        "branch_count": len(off_path),
        "output": output,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if not errors and isinstance(meta, dict):
        requested = meta.get("overrides")
        if isinstance(requested, dict):
            observed = {
                "grid_h": analysis["grid_h"],
                "grid_w": analysis["grid_w"],
                "path_len": analysis["path_len"],
                "branch_count": analysis["branch_count"],
            }
            for axis, value in requested.items():
                if axis in AXES and value is not None and observed.get(axis) != value:
                    errors.append(
                        f"override {axis!r} requested {value!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": int(analysis["grid_h"]),
        "grid_w": int(analysis["grid_w"]),
        "path_len": int(analysis["path_len"]),
        "branch_count": int(analysis["branch_count"]),
    }


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    path = set(analysis["path_indices"])
    branches = analysis["off_path_indices"]
    path_colors = {analysis["colors"][index] for index in path}
    repeated_off_path = any(analysis["colors"][index] in path_colors for index in branches)
    return {
        **observe_overrides(grid),
        "graph_is_tree": analysis["graph_is_tree"],
        "dead_end_branch": bool(branches),
        "singleton_path_component": any(
            len(analysis["components"][index]) == 1
            for index in analysis["path_indices"][1:-1]
        ),
        "multicell_branch": any(
            len(analysis["components"][index]) > 1 for index in branches
        ),
        "repeated_path_color_off_path": repeated_off_path,
    }


def _validate_generate_args(difficulty, overrides: dict[str, object]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    for axis, value in overrides.items():
        if value is None:
            continue
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"override {axis!r} must be an integer, got {value!r}")
        lo, hi = _AXIS_BOUNDS[axis]
        if not lo <= value <= hi:
            raise ValueError(f"override {axis!r}={value} outside {lo}..{hi}")


def _draw_axis(ctx, overrides, axis: str, default: int) -> int:
    lo, hi = _AXIS_BOUNDS[axis]
    if axis in overrides and overrides[axis] is not None:
        return ctx.draw_int(axis, lo, hi)
    return ctx.draw_int(axis, default, default)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return SCHEDULE_PROFILES[(sample_index + offset) % len(SCHEDULE_PROFILES)]


def _turn_index(path: list[Cell]) -> int | None:
    for index in range(1, len(path) - 1):
        before = (path[index][0] - path[index - 1][0], path[index][1] - path[index - 1][1])
        after = (path[index + 1][0] - path[index][0], path[index + 1][1] - path[index][1])
        if before != after:
            return index
    return None


def _branch_options(
    path: list[Cell], branch_count: int, forbidden_parents: set[int]
) -> list[list[tuple[Cell, int]]]:
    path_set = set(path)
    min_r = min(r for r, _ in path) - 1
    max_r = max(r for r, _ in path) + 1
    min_c = min(c for _, c in path) - 1
    max_c = max(c for _, c in path) + 1
    candidates: list[tuple[Cell, int]] = []
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if (r, c) in path_set:
                continue
            adjacent = [
                index
                for index, cell in enumerate(path)
                if abs(cell[0] - r) + abs(cell[1] - c) == 1
            ]
            if len(adjacent) != 1:
                continue
            parent = adjacent[0]
            if parent in forbidden_parents or not 0 < parent < len(path) - 1:
                continue
            candidates.append(((r, c), parent))
    options = []
    for selection in combinations(candidates, branch_count):
        cells = [item[0] for item in selection]
        if any(
            abs(first[0] - second[0]) + abs(first[1] - second[1]) == 1
            for first, second in combinations(cells, 2)
        ):
            continue
        options.append(list(selection))
    return options


def _full_shape(cell: Cell) -> set[Cell]:
    r, c = cell
    return {(2 * r + dr, 2 * c + dc) for dr in (0, 1) for dc in (0, 1)}


def _side_shape(cell: Cell, toward: Cell, *, bar: bool, rng) -> set[Cell]:
    r, c = cell
    dr, dc = toward[0] - r, toward[1] - c
    if (dr, dc) == (-1, 0):
        choices = [(2 * r, 2 * c), (2 * r, 2 * c + 1)]
    elif (dr, dc) == (1, 0):
        choices = [(2 * r + 1, 2 * c), (2 * r + 1, 2 * c + 1)]
    elif (dr, dc) == (0, -1):
        choices = [(2 * r, 2 * c), (2 * r + 1, 2 * c)]
    elif (dr, dc) == (0, 1):
        choices = [(2 * r, 2 * c + 1), (2 * r + 1, 2 * c + 1)]
    else:
        raise AssertionError("component neighbors must be cardinal")
    return set(choices if bar else [rng.choice(choices)])


def _turn_singleton(path: list[Cell], index: int) -> set[Cell]:
    r, c = path[index]
    directions = {
        (path[index - 1][0] - r, path[index - 1][1] - c),
        (path[index + 1][0] - r, path[index + 1][1] - c),
    }
    row = 0 if (-1, 0) in directions else 1
    col = 0 if (0, -1) in directions else 1
    return {(2 * r + row, 2 * c + col)}


def _transform_points(points: set[Cell], transform: int) -> set[Cell]:
    def one(r: int, c: int) -> Cell:
        if transform == 0:
            return r, c
        if transform == 1:
            return c, -r
        if transform == 2:
            return -r, -c
        if transform == 3:
            return -c, r
        if transform == 4:
            return r, -c
        if transform == 5:
            return -c, -r
        if transform == 6:
            return -r, c
        return c, r

    transformed = {one(r, c) for r, c in points}
    min_r = min(r for r, _ in transformed)
    min_c = min(c for _, c in transformed)
    return {(r - min_r, c - min_c) for r, c in transformed}


def _transform_components(
    components: list[set[Cell]], transform: int
) -> list[set[Cell]]:
    all_points = set().union(*components)
    raw: list[set[Cell]] = []

    def one(r: int, c: int) -> Cell:
        if transform == 0:
            return r, c
        if transform == 1:
            return c, -r
        if transform == 2:
            return -r, -c
        if transform == 3:
            return -c, r
        if transform == 4:
            return r, -c
        if transform == 5:
            return -c, -r
        if transform == 6:
            return -r, c
        return c, r

    transformed_all = {one(r, c) for r, c in all_points}
    min_r = min(r for r, _ in transformed_all)
    min_c = min(c for _, c in transformed_all)
    for component in components:
        raw.append({(one(r, c)[0] - min_r, one(r, c)[1] - min_c) for r, c in component})
    return raw


def _build_scene(
    h: int, w: int, path_len: int, branch_count: int, profile: str, rng
) -> Grid:
    path = list(_PATH_TEMPLATES[profile][path_len])
    singleton_turn = _turn_index(path) if profile == "elbow" and path_len >= 5 else None
    forbidden = {singleton_turn} if singleton_turn is not None else set()
    options = _branch_options(path, branch_count, forbidden)
    if not options and singleton_turn is not None:
        singleton_turn = None
        options = _branch_options(path, branch_count, set())
    if not options:
        raise AssertionError(
            f"no branch placement for profile={profile} path_len={path_len} branches={branch_count}"
        )
    branches = rng.choice(options)

    component_shapes: list[set[Cell]] = []
    for index, cell in enumerate(path):
        if index == 0:
            component_shapes.append(_side_shape(cell, path[1], bar=False, rng=rng))
        elif index == len(path) - 1:
            component_shapes.append(_side_shape(cell, path[-2], bar=False, rng=rng))
        elif index == singleton_turn:
            component_shapes.append(_turn_singleton(path, index))
        else:
            component_shapes.append(_full_shape(cell))

    for branch_index, (cell, parent_index) in enumerate(branches):
        multi = profile == "zigzag" and branch_index == 0
        component_shapes.append(
            _side_shape(cell, path[parent_index], bar=multi, rng=rng)
        )

    # Reserve color 8 for the transformation result so every generated pair
    # visibly introduces the output label instead of occasionally reusing it.
    palette = [3, 4, 5, 6, 7, 9]
    rng.shuffle(palette)
    path_colors = [1] + palette[: path_len - 2] + [2]
    cursor = path_len - 2
    branch_colors: list[int] = []
    for branch_index, (_cell, parent_index) in enumerate(branches):
        repeat = profile in ("elbow", "zigzag") and branch_count >= 2 and branch_index == branch_count - 1
        if repeat:
            eligible = [
                index
                for index in range(1, path_len - 1)
                if index != parent_index
            ]
            branch_colors.append(path_colors[rng.choice(eligible)])
        else:
            branch_colors.append(palette[cursor])
            cursor += 1
    colors = path_colors + branch_colors

    fitting: list[list[set[Cell]]] = []
    for transform in range(8):
        transformed = _transform_components(component_shapes, transform)
        max_r = max(r for component in transformed for r, _ in component) + 1
        max_c = max(c for component in transformed for _, c in component) + 1
        if max_r <= h and max_c <= w:
            fitting.append(transformed)
    if not fitting:
        raise AssertionError(f"constructed scene does not fit requested {h}x{w}")
    components = rng.choice(fitting)
    scene_h = max(r for component in components for r, _ in component) + 1
    scene_w = max(c for component in components for _, c in component) + 1
    offset_r = rng.randint(0, h - scene_h)
    offset_c = rng.randint(0, w - scene_w)
    grid = full_grid(h, w, 0)
    for component, color in zip(components, colors):
        for r, c in component:
            if grid[r + offset_r][c + offset_c] != 0:
                raise AssertionError("component painter overlap")
            grid[r + offset_r][c + offset_c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generate_args(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_path_len, default_branches = _PROFILE_DEFAULTS[profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_axis(ctx, overrides, "grid_h", default_h)
    w = _draw_axis(ctx, overrides, "grid_w", default_w)
    path_len = _draw_axis(ctx, overrides, "path_len", default_path_len)
    branch_count = _draw_axis(ctx, overrides, "branch_count", default_branches)
    grid = _build_scene(h, w, path_len, branch_count, profile, ctx.draw_rng("layout"))
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generated invalid component-path lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, value in ctx.recorded_draws().items():
        if axis in AXES and observed.get(axis) != value:
            raise AssertionError(
                f"axis {axis!r} requested {value!r}, observed {observed.get(axis)!r}"
            )
    return grid


def rule_mirror(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def _paint_all_nonzero(grid: Grid) -> Grid:
    return [[8 if value != 0 else 0 for value in row] for row in grid]


def _keep_multicell_and_endpoints(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [row[:] for row in grid]
    out = full_grid(len(grid), len(grid[0]), 0)
    for index, component in enumerate(analysis["components"]):
        if analysis["colors"][index] in (1, 2) or len(component) > 1:
            for r, c in component:
                out[r][c] = 8
    return out


def _global_color_union(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [row[:] for row in grid]
    path_colors = {analysis["colors"][index] for index in analysis["path_indices"]}
    out = full_grid(len(grid), len(grid[0]), 0)
    for index, component in enumerate(analysis["components"]):
        if analysis["colors"][index] in path_colors:
            for r, c in component:
                out[r][c] = 8
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "paint_all_nonzero": _paint_all_nonzero,
    "keep_multicell_and_endpoints": _keep_multicell_and_endpoints,
    "global_color_union": _global_color_union,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "keep_multicell_and_endpoints": _keep_multicell_and_endpoints,
    "global_color_union": _global_color_union,
}


def _witness(grid, key: str) -> bool:
    observables = semantic_observables(grid)
    return not observables.get("errors") and bool(observables.get(key))


SEMANTIC_WITNESSES = {
    "dead_end_branch": lambda grid: _witness(grid, "dead_end_branch"),
    "singleton_path_component": lambda grid: _witness(grid, "singleton_path_component"),
    "multicell_branch": lambda grid: _witness(grid, "multicell_branch"),
    "repeated_path_color_off_path": lambda grid: _witness(grid, "repeated_path_color_off_path"),
}
WITNESS_RIVALS = {
    "dead_end_branch": ["paint_all_nonzero"],
    "singleton_path_component": ["keep_multicell_and_endpoints"],
    "multicell_branch": ["keep_multicell_and_endpoints"],
    "repeated_path_color_off_path": ["global_color_union"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is unlawful: " + "; ".join(query_errors)]
    query_truth = rule_mirror(query_input)
    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} is unlawful: {'; '.join(errors)}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the component-path rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query"
                )
    return reasons
