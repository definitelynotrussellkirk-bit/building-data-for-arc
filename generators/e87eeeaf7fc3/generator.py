"""Generator for bank task 4e772fa039b8:H57 / e87eeeaf7fc3.

Gray cells are walls.  The remaining cells form one sparse graph containing
red start 2, green checkpoint 3, and yellow goal 4.  The rule paints the
ordered BFS paths 2 -> 3 and 3 -> 4 cyan 8, clears unused traversable cells,
and preserves the walls.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e87eeeaf7fc3"
VERSION = "3.0.0"
TASK_ID = "e87eeeaf7fc3"
RULE_HASH = "3c811e3e98bd"

SUMMARY = (
    "Construct a sparse connected graph inside gray walls, with either a "
    "tree topology or genuine alternate-route loops. Place red start 2, "
    "green checkpoint 3, and leaf goal 4 so both BFS segments are nontrivial "
    "and several traversable cells remain off the ordered route."
)

INVARIANTS = [
    "the border and every blocked cell are gray 5",
    "all non-wall cells form one sparse 4-connected graph",
    "there is exactly one marker of each color 2, 3, and 4",
    "the ordered BFS paths 2->3 and 3->4 meet only at marker 3",
    "at least four traversable cells remain outside the painted path",
    "tree scenes have cycle rank 0; looped scenes have cycle rank 1..4",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 9..20",
        "valid": "9..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 9..20",
        "valid": "9..20",
    },
    "graph_kind": {
        "type": "str",
        "default": "rng tree|looped",
        "valid": "tree|looped",
    },
}

_VALID_H = (9, 20)
_VALID_W = (9, 20)
_GRAPH_KINDS = ("tree", "looped")
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PROFILE_PRIOR = 0.10

# A profile links every answer-bearing public feature used here:
#   h, w, open cells, cycle rank, degree histogram,
#   path lengths 2->3 and 3->4, and marker degrees (2, 3, 4).
# Layout and orientation are deliberately nuisance variables.
_PROFILE_SPECS = (
    (12, 12, 19, 0, ((1, 4), (2, 13), (3, 2)), 9, 6, (2, 2, 1)),
    (11, 11, 17, 2, ((1, 4), (2, 7), (3, 6)), 8, 5, (1, 3, 1)),
    (
        11,
        11,
        16,
        3,
        ((1, 2), (2, 9), (3, 4), (4, 1)),
        8,
        5,
        (1, 3, 1),
    ),
    (
        13,
        13,
        19,
        2,
        ((1, 3), (2, 12), (3, 3), (4, 1)),
        7,
        9,
        (2, 2, 1),
    ),
    (13, 13, 21, 1, ((1, 3), (2, 15), (3, 3)), 7, 11, (1, 2, 1)),
)

# Synthetic search results, not public layouts.  They make profile generation
# total even if a particular keyed random search exhausts its retry budget.
_PROFILE_FALLBACKS = (
    (
        (
            (1, 7),
            (1, 10),
            (2, 7),
            (2, 8),
            (2, 10),
            (3, 8),
            (3, 9),
            (3, 10),
            (4, 10),
            (5, 8),
            (5, 9),
            (5, 10),
            (6, 8),
            (6, 10),
            (7, 8),
            (7, 10),
            (8, 8),
            (9, 8),
            (10, 8),
        ),
        ((2, 7), (5, 8), (10, 8)),
    ),
    (
        (
            (6, 3),
            (6, 4),
            (7, 1),
            (7, 2),
            (7, 3),
            (7, 4),
            (8, 2),
            (8, 4),
            (8, 6),
            (9, 1),
            (9, 2),
            (9, 3),
            (9, 4),
            (9, 5),
            (9, 6),
            (9, 7),
            (9, 8),
        ),
        ((9, 8), (7, 3), (9, 1)),
    ),
    (
        (
            (4, 2),
            (4, 3),
            (4, 4),
            (4, 6),
            (5, 1),
            (5, 2),
            (5, 4),
            (5, 5),
            (5, 6),
            (6, 1),
            (6, 2),
            (6, 3),
            (6, 4),
            (7, 1),
            (7, 2),
            (7, 4),
        ),
        ((4, 6), (5, 2), (7, 4)),
    ),
    (
        (
            (1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (2, 2),
            (2, 5),
            (3, 2),
            (3, 5),
            (4, 1),
            (4, 2),
            (4, 3),
            (4, 4),
            (4, 5),
            (5, 1),
            (5, 2),
            (6, 2),
            (6, 3),
            (7, 2),
        ),
        ((3, 2), (2, 5), (6, 3)),
    ),
    (
        (
            (1, 3),
            (1, 4),
            (1, 5),
            (1, 6),
            (2, 3),
            (3, 1),
            (3, 2),
            (3, 3),
            (3, 4),
            (3, 5),
            (3, 6),
            (4, 1),
            (4, 4),
            (5, 1),
            (5, 2),
            (5, 4),
            (5, 5),
            (5, 6),
            (6, 2),
            (6, 3),
            (6, 4),
        ),
        ((5, 6), (5, 2), (1, 6)),
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    kind = overrides.get("graph_kind")
    if kind is not None and type(kind) is not str:
        raise ValueError("graph_kind must be a string")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _interior_neighbors(cell, h, w):
    r, c = cell
    return tuple(
        (r + dr, c + dc)
        for dr, dc in _CARDINALS
        if 1 <= r + dr < h - 1 and 1 <= c + dc < w - 1
    )


def _graph_neighbors(cell, cells):
    r, c = cell
    return tuple(
        (r + dr, c + dc)
        for dr, dc in _CARDINALS
        if (r + dr, c + dc) in cells
    )


def _degree_map(cells):
    return {
        cell: len(_graph_neighbors(cell, cells))
        for cell in cells
    }


def _degree_histogram(cells):
    return tuple(sorted(Counter(_degree_map(cells).values()).items()))


def _cycle_rank(cells):
    edges = sum(_degree_map(cells).values()) // 2
    return edges - len(cells) + 1


def _is_connected(cells):
    if not cells:
        return False
    start = min(cells)
    seen = {start}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for neighbor in _graph_neighbors(cell, cells):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == cells


def _shortest_path(cells, start, goal):
    """Match Racket cardinal-deltas BFS order: up, down, left, right."""
    if start not in cells or goal not in cells:
        return ()
    parent = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        r, c = cell
        for dr, dc in _CARDINALS:
            neighbor = (r + dr, c + dc)
            if neighbor in cells and neighbor not in parent:
                parent[neighbor] = cell
                queue.append(neighbor)
    if goal not in parent:
        return ()
    reverse_path = []
    cell = goal
    while cell is not None:
        reverse_path.append(cell)
        cell = parent[cell]
    return tuple(reversed(reverse_path))


def _paths_from(cells, start):
    parent = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        r, c = cell
        for dr, dc in _CARDINALS:
            neighbor = (r + dr, c + dc)
            if neighbor in cells and neighbor not in parent:
                parent[neighbor] = cell
                queue.append(neighbor)

    paths = {}
    for goal in cells:
        reverse_path = []
        cell = goal
        while cell is not None:
            reverse_path.append(cell)
            cell = parent[cell]
        paths[goal] = tuple(reversed(reverse_path))
    return paths


def _marker_positions(grid):
    positions = {2: [], 3: [], 4: []}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in positions:
                positions[value].append((r, c))
    return positions


def _analyze_scene(grid):
    coerced = _coerce_grid(grid)
    h = len(coerced)
    w = len(coerced[0]) if coerced else 0
    cells = {
        (r, c)
        for r, row in enumerate(coerced)
        for c, value in enumerate(row)
        if value != 5
    }
    positions = _marker_positions(coerced)
    markers = {
        color: values[0]
        for color, values in positions.items()
        if len(values) == 1
    }
    degrees = _degree_map(cells) if cells else {}
    path_23 = (
        _shortest_path(cells, markers[2], markers[3])
        if 2 in markers and 3 in markers
        else ()
    )
    path_34 = (
        _shortest_path(cells, markers[3], markers[4])
        if 3 in markers and 4 in markers
        else ()
    )
    route = set(path_23) | set(path_34)
    return {
        "grid": coerced,
        "h": h,
        "w": w,
        "cells": cells,
        "positions": positions,
        "markers": markers,
        "degrees": degrees,
        "degree_histogram": (
            tuple(sorted(Counter(degrees.values()).items()))
            if degrees
            else ()
        ),
        "cycle_rank": _cycle_rank(cells) if cells else -1,
        "path_23": path_23,
        "path_34": path_34,
        "route": route,
        "off_path": cells - route,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    h = len(coerced)
    w = width
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append("grid height must be in 9..20")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append("grid width must be in 9..20")
    if any(
        type(value) is not int or value not in {0, 2, 3, 4, 5}
        for row in coerced
        for value in row
    ):
        errors.append("input values must be integer colors 0, 2, 3, 4, or 5")
        return errors
    if any(value != 5 for value in coerced[0] + coerced[-1]):
        errors.append("top and bottom borders must be gray walls")
    if any(row[0] != 5 or row[-1] != 5 for row in coerced):
        errors.append("left and right borders must be gray walls")

    scene = _analyze_scene(coerced)
    n_open = len(scene["cells"])
    max_open = min(48, max(18, (22 * h * w + 99) // 100))
    if not 14 <= n_open <= max_open:
        errors.append(
            f"traversable-cell count must be sparse (14..{max_open})"
        )
    for color in (2, 3, 4):
        if len(scene["positions"][color]) != 1:
            errors.append(f"scene must contain exactly one marker color {color}")
    if scene["cells"] and not _is_connected(scene["cells"]):
        errors.append("all non-wall cells must form one connected component")
    if not 0 <= scene["cycle_rank"] <= 4:
        errors.append("graph cycle rank must be in 0..4")

    degree_counts = Counter(scene["degrees"].values())
    if degree_counts[1] < 2:
        errors.append("graph must contain at least two leaves")
    if sum(
        count for degree, count in degree_counts.items() if degree >= 3
    ) < 2:
        errors.append("graph must contain at least two junction cells")

    if len(scene["markers"]) == 3 and _is_connected(scene["cells"]):
        start = scene["markers"][2]
        checkpoint = scene["markers"][3]
        goal = scene["markers"][4]
        if scene["degrees"].get(start) not in (1, 2):
            errors.append("start marker must have graph degree 1 or 2")
        if scene["degrees"].get(checkpoint) not in (2, 3):
            errors.append("checkpoint marker must have graph degree 2 or 3")
        if scene["degrees"].get(goal) != 1:
            errors.append("goal marker must sit on a graph leaf")
        if len(scene["path_23"]) < 4 or len(scene["path_34"]) < 4:
            errors.append("both ordered BFS path segments must be nontrivial")
        if (
            set(scene["path_23"]) & set(scene["path_34"])
            != {checkpoint}
        ):
            errors.append(
                "the two ordered BFS segments must meet only at checkpoint"
            )
        max_off_path = max(8, n_open // 2)
        if not 4 <= len(scene["off_path"]) <= max_off_path:
            errors.append(
                "scene must leave a controlled set of off-path cells"
            )
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "graph_kind": (
            "tree" if scene["cycle_rank"] == 0 else "looped"
        ),
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    output = full_grid(scene["h"], scene["w"], 5)
    for r, c in scene["cells"]:
        output[r][c] = 0
    for r, c in scene["route"]:
        output[r][c] = 8
    return output


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    marker_degrees = tuple(
        scene["degrees"][scene["markers"][color]]
        for color in (2, 3, 4)
    )
    return (
        scene["h"],
        scene["w"],
        len(scene["cells"]),
        scene["cycle_rank"],
        scene["degree_histogram"],
        len(scene["path_23"]),
        len(scene["path_34"]),
        len(scene["route"]),
        len(scene["off_path"]),
        marker_degrees,
    )


def _profile_signature(spec):
    h, w, n_open, rank, histogram, path_23, path_34, degrees = spec
    route_length = path_23 + path_34 - 1
    return (
        h,
        w,
        n_open,
        rank,
        histogram,
        path_23,
        path_34,
        route_length,
        n_open - route_length,
        degrees,
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_signature(spec) for spec in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    return (
        canonical_profile_signature(grid)
        in _CANONICAL_PROFILE_SIGNATURES
    )


def _grow_graph(h, w, n_open, cycle_rank, rng):
    """Grow an induced tree, then add degree-two cells for exact cycles."""
    start = (rng.randrange(1, h - 1), rng.randrange(1, w - 1))
    cells = {start}
    neighbor_counts = Counter(_interior_neighbors(start, h, w))

    for _ in range(n_open - cycle_rank - 1):
        candidates = sorted(
            cell
            for cell, count in neighbor_counts.items()
            if count == 1
        )
        if not candidates:
            return None
        cell = rng.choice(candidates)
        cells.add(cell)
        neighbor_counts.pop(cell, None)
        for neighbor in _interior_neighbors(cell, h, w):
            if neighbor not in cells:
                neighbor_counts[neighbor] += 1

    for _ in range(cycle_rank):
        candidates = sorted(
            cell
            for cell, count in neighbor_counts.items()
            if count == 2
        )
        if not candidates:
            return None
        cell = rng.choice(candidates)
        cells.add(cell)
        neighbor_counts.pop(cell, None)
        for neighbor in _interior_neighbors(cell, h, w):
            if neighbor not in cells:
                neighbor_counts[neighbor] += 1

    if len(cells) != n_open or _cycle_rank(cells) != cycle_rank:
        return None
    return cells


def _path_tables(cells, sources):
    return {
        source: _paths_from(cells, source)
        for source in sources
    }


def _select_markers(
    cells,
    rng,
    *,
    exact_path_lengths=None,
    exact_marker_degrees=None,
):
    degrees = _degree_map(cells)
    if exact_marker_degrees is None:
        starts = [
            cell for cell in sorted(cells) if degrees[cell] in (1, 2)
        ]
        checkpoints = [
            cell for cell in sorted(cells) if degrees[cell] in (2, 3)
        ]
        goals = [
            cell for cell in sorted(cells) if degrees[cell] == 1
        ]
    else:
        starts = [
            cell
            for cell in sorted(cells)
            if degrees[cell] == exact_marker_degrees[0]
        ]
        checkpoints = [
            cell
            for cell in sorted(cells)
            if degrees[cell] == exact_marker_degrees[1]
        ]
        goals = [
            cell
            for cell in sorted(cells)
            if degrees[cell] == exact_marker_degrees[2]
        ]

    paths = _path_tables(cells, set(starts) | set(checkpoints))
    chosen = None
    n_candidates = 0
    for start in starts:
        for checkpoint in checkpoints:
            if checkpoint == start:
                continue
            path_23 = paths[start][checkpoint]
            if len(path_23) < 4:
                continue
            if (
                exact_path_lengths is not None
                and len(path_23) != exact_path_lengths[0]
            ):
                continue
            path_23_cells = set(path_23)
            for goal in goals:
                if goal in (start, checkpoint):
                    continue
                path_34 = paths[checkpoint][goal]
                if len(path_34) < 4:
                    continue
                if (
                    exact_path_lengths is not None
                    and len(path_34) != exact_path_lengths[1]
                ):
                    continue
                if path_23_cells & set(path_34) != {checkpoint}:
                    continue
                off_path = (
                    len(cells) - len(path_23) - len(path_34) + 1
                )
                if exact_path_lengths is None:
                    if not 4 <= off_path <= max(8, len(cells) // 2):
                        continue
                elif off_path != (
                    len(cells)
                    - exact_path_lengths[0]
                    - exact_path_lengths[1]
                    + 1
                ):
                    continue
                n_candidates += 1
                if rng.randrange(n_candidates) == 0:
                    chosen = (start, checkpoint, goal)
    return chosen


def _paint_scene(h, w, cells, markers):
    grid = full_grid(h, w, 5)
    for r, c in cells:
        grid[r][c] = 0
    for color, cell in zip((2, 3, 4), markers):
        grid[cell[0]][cell[1]] = color
    return grid


def _draw_profile(profile_index, rng):
    spec = _PROFILE_SPECS[profile_index]
    h, w, n_open, rank, histogram, path_23, path_34, degrees = spec
    for _ in range(5_000):
        cells = _grow_graph(h, w, n_open, rank, rng)
        if cells is None or _degree_histogram(cells) != histogram:
            continue
        markers = _select_markers(
            cells,
            rng,
            exact_path_lengths=(path_23, path_34),
            exact_marker_degrees=degrees,
        )
        if markers is not None:
            return _paint_scene(h, w, cells, markers)

    fallback_cells, fallback_markers = _PROFILE_FALLBACKS[profile_index]
    grid = _paint_scene(
        h,
        w,
        set(fallback_cells),
        fallback_markers,
    )
    if canonical_profile_signature(grid) != _profile_signature(spec):
        raise AssertionError("invalid synthetic profile fallback")
    return grid


def _draw_general(h, w, graph_kind, rng):
    min_open = max(14, round(h * w * 0.10))
    max_open = max(min_open, min(48, round(h * w * 0.16)))
    for _ in range(2_000):
        n_open = rng.randint(min_open, max_open)
        if graph_kind == "tree":
            rank = 0
        else:
            rank = rng.randint(1, min(4, max(1, n_open // 8)))
        cells = _grow_graph(h, w, n_open, rank, rng)
        if cells is None:
            continue
        degree_counts = Counter(_degree_map(cells).values())
        if degree_counts[1] < 2:
            continue
        if sum(
            count
            for degree, count in degree_counts.items()
            if degree >= 3
        ) < 2:
            continue
        markers = _select_markers(cells, rng)
        if markers is not None:
            return _paint_scene(h, w, cells, markers)
    raise AssertionError(
        f"could not construct lawful {graph_kind} graph in {h}x{w}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )
    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )

    if profile_index is not None:
        spec = _PROFILE_SPECS[profile_index]
        h, w, _n_open, rank = spec[:4]
        graph_kind = "tree" if rank == 0 else "looped"
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.draw_choice("graph_kind", (graph_kind,))
        grid = _draw_profile(
            profile_index,
            ctx.draw_rng("layout"),
        )
    else:
        if overrides.get("grid_h") is not None:
            h = ctx.draw_int("grid_h", *_VALID_H)
        else:
            h = ctx.draw_int(
                "grid_h",
                *{
                    "easy": (9, 12),
                    "medium": (11, 16),
                    "hard": (15, 20),
                }[band],
            )
        if overrides.get("grid_w") is not None:
            w = ctx.draw_int("grid_w", *_VALID_W)
        else:
            w = ctx.draw_int(
                "grid_w",
                *{
                    "easy": (9, 13),
                    "medium": (11, 17),
                    "hard": (15, 20),
                }[band],
            )
        graph_kind = ctx.draw_choice("graph_kind", _GRAPH_KINDS)
        grid = _draw_general(
            h,
            w,
            graph_kind,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
