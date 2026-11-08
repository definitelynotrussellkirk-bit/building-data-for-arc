"""Exact input sampler for nearest-seed distance on a simple cardinal path.

Racket remains the label authority. Python predictions below are diagnostic
rivals and witness selectors, never emitted training labels. Default draws
cycle through odd contrast, even contrast and varied paths; see notes.md.
"""
from __future__ import annotations

import heapq
import math
from functools import lru_cache, partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "547c45a21db1"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "44ec512ed7bb"
SUMMARY = (
    "A simple induced four-neighbor path on background 0 has one endpoint 2 "
    "and one endpoint 3. Recolor its internal 1-cells by shortest path distance "
    "to those seeds; use 4 for equal distances. Exact lengths include both "
    "seeds. Orientations, positions, parity and seed order vary."
)
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "nonempty rectangular integer grid, using only colors 0, 1, 2, 3",
    "all active cells form one connected simple induced cardinal path",
    "exactly one seed 2 and one seed 3, at the path's two endpoints",
    "at least two internal 1-cells; total active path length at least four",
    "default six-pair windows contain two contrast draws of each parity before any rejection",
]
AXES = {
    "grid_h": {"type": "int", "default": "5..14; canonical sizes favored in every band", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "6..14; canonical sizes favored in every band", "valid": "6..14"},
    "path_len": {"type": "int", "default": "4..20; odd/even contrast and varied paths", "valid": "4..20",
                 "doc": "Exact TOTAL active cells, including the two seeds; not the number of 1-cells."},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("odd_contrast", "even_contrast", "varied")
_D4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_D8 = _D4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))
# Small constructive paths from the independent exhaustive 5x6 geometry census,
# not canonical examples. Wider end-extended snake variants are added below.
_EVEN_WALKS = {
    10: "RRRRRUULU",
    12: "RRDDLLLULUL",
    14: "LDDRDDLLLUUUU",
    16: "LDDRRDDLLLLUUUU",
    18: "LDDRRRDDLLLLLUUUU",
    20: "URURRDDLDLDLLLUUUUR",
}


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _support(grid):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value in (1, 2, 3)}


def _neighbors(point, cells):
    r, c = point
    return [(r + dr, c + dc) for dr, dc in _D4 if (r + dr, c + dc) in cells]


def self_check(grid, *, difficulty=None, meta=None):
    """Validate graph membership; malformed inputs return diagnostics, not crashes."""
    if not isinstance(grid, list) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["expected nonempty rows"]
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 1, 2, 3) for row in grid for value in row):
        return ["cells must be integer colors 0, 1, 2, 3"]
    seeds = {color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
             for color in (2, 3)}
    errors = [f"expected exactly one seed {color}" for color, points in seeds.items() if len(points) != 1]
    if sum(value == 1 for row in grid for value in row) < 2:
        errors.append("expected at least two internal 1-cells")
    cells = _support(grid)
    degrees = {point: len(_neighbors(point, cells)) for point in cells}
    ends = {point for point, degree in degrees.items() if degree == 1}
    if len(ends) != 2 or any(degree not in (1, 2) for degree in degrees.values()):
        errors.append("active cells must have two degree-1 endpoints and degree-2 interiors")
    if all(len(points) == 1 for points in seeds.values()):
        if ends != {seeds[2][0], seeds[3][0]}:
            errors.append("seeds must be the two path endpoints")
        reached = {seeds[2][0]}
        pending = [seeds[2][0]]
        while pending:
            for point in _neighbors(pending.pop(), cells):
                if point not in reached:
                    reached.add(point)
                    pending.append(point)
        if reached != cells:
            errors.append("active cells must be one connected component")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "path_len": len(_support(grid))}


def _path_order(grid):
    cells = _support(grid)
    point = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    previous = None
    path = []
    while point is not None:
        path.append(point)
        onward = [p for p in _neighbors(point, cells) if p != previous]
        if len(onward) > 1 or len(path) > len(cells):
            raise ValueError("diagnostic requires a simple path with endpoint seeds")
        previous, point = point, onward[0] if onward else None
    if len(path) != len(cells):
        raise ValueError("diagnostic requires connected active cells")
    return path


def _distances(cells, start, diagonal_cost=None):
    distances = {start: 0.0}
    pending = [(0.0, start)]
    directions = _D4 if diagonal_cost is None else _D8
    while pending:
        distance, point = heapq.heappop(pending)
        if distance > distances[point]:
            continue
        for dr, dc in directions:
            other = (point[0] + dr, point[1] + dc)
            cost = distance + (diagonal_cost if dr and dc else 1.0)
            if other in cells and cost < distances.get(other, math.inf):
                distances[other] = cost
                heapq.heappush(pending, (cost, other))
    return distances


def _prediction(grid, mode):
    """Pure hypothesis implementation for finite rival checks, not label authority."""
    path = _path_order(grid)
    if mode in ("even_raster_seed_order", "odd_raster_seed_order"):
        selected_parity = 0 if mode.startswith("even_") else 1
        mode = "raster_seed_order" if len(path) % 2 == selected_parity else "cardinal"
    cells = set(path)
    seed2, seed3 = path[0], path[-1]
    if mode.startswith("turn_"):
        penalty = {"turn_penalty_half": 0.5, "turn_discount_half": -0.5, "turn_penalty_one": 1.0}[mode]
        turns = [i for i in range(1, len(path) - 1)
                 if (path[i][0] - path[i-1][0], path[i][1] - path[i-1][1]) !=
                    (path[i+1][0] - path[i][0], path[i+1][1] - path[i][1])]
        d2 = {p: i + penalty * sum(t < i for t in turns) for i, p in enumerate(path)}
        d3 = {p: len(path) - 1 - i + penalty * sum(t > i for t in turns) for i, p in enumerate(path)}
    elif mode in ("manhattan", "euclidean_squared", "chebyshev"):
        def metric(a, b):
            dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
            return dr + dc if mode == "manhattan" else max(dr, dc) if mode == "chebyshev" else dr*dr + dc*dc
        d2, d3 = ({p: metric(p, seed) for p in path} for seed in (seed2, seed3))
    else:
        if mode == "raster_seed_order":
            seed2, seed3 = sorted((seed2, seed3))
        diagonal_cost = {"bfs8": 1.0, "diagonal_euclidean": math.sqrt(2)}.get(mode)
        d2 = _distances(cells, seed2, diagonal_cost)
        d3 = _distances(cells, seed3, diagonal_cost)
    output = [list(row) for row in grid]
    for r, c in path[1:-1]:
        delta = d2[(r, c)] - d3[(r, c)]
        output[r][c] = 2 if delta < -1e-9 else 3 if delta > 1e-9 else 4
    return output


def _paint(path, height, width, reverse_seed_order=False):
    grid = full_grid(height, width, 0)
    for r, c in path:
        grid[r][c] = 1
    first, last = path[0], path[-1]
    if reverse_seed_order:
        first, last = max(first, last), min(first, last)
    grid[first[0]][first[1]] = 2
    grid[last[0]][last[1]] = 3
    return grid


def _all_base_rivals_refuted(grid):
    intended = _prediction(grid, "cardinal")
    return all(rival(grid) != intended for rival in _BASE_COMPETITORS.values())


def _odd_contrast(grid):
    return len(_support(grid)) % 2 == 1 and _all_base_rivals_refuted(grid)


def _even_contrast(grid):
    return len(_support(grid)) % 2 == 0 and _all_base_rivals_refuted(grid)


def _normalize(path):
    top = min(r for r, _ in path)
    left = min(c for _, c in path)
    return tuple((r - top, c - left) for r, c in path)


def _snake(height, width):
    path = []
    for index, row in enumerate(range(0, height, 2)):
        if path:
            path.append((row - 1, path[-1][1]))
        columns = range(width) if index % 2 == 0 else range(width - 1, -1, -1)
        path.extend((row, column) for column in columns)
    return path


@lru_cache(maxsize=10)
def _contrast_templates(length):
    """Immutable geometry cache; no cached draws, outputs, or seed-dependent state."""
    candidates = set()
    base_length = length if length % 2 else length - 1
    for width in range(2, 15):
        route = _snake(14, width)
        for start in range(len(route) - base_length + 1):
            path = _normalize(route[start:start + base_length])
            if length % 2:
                candidates.add(path)
            else:
                cells = set(path)
                for oriented in (path, path[::-1]):
                    r, c = oriented[-1]
                    for dr, dc in _D4:
                        point = (r + dr, c + dc)
                        if point not in cells and len(_neighbors(point, cells)) == 1:
                            candidates.add(_normalize((*oriented, point)))
    if length in _EVEN_WALKS:
        path = [(0, 0)]
        deltas = {"R": (0, 1), "L": (0, -1), "D": (1, 0), "U": (-1, 0)}
        for direction in _EVEN_WALKS[length]:
            dr, dc = deltas[direction]
            path.append((path[-1][0] + dr, path[-1][1] + dc))
        candidates.add(_normalize(path))
    candidates.update(tuple((c, r) for r, c in p) for p in tuple(candidates))
    accepted = []
    for path in sorted(candidates):
        height = max(r for r, _ in path) + 1
        width = max(c for _, c in path) + 1
        if height <= 14 and width <= 14 and _all_base_rivals_refuted(_paint(path, height, width, reverse_seed_order=True)):
            accepted.append(path)
    return tuple(accepted)


def _walk(rng, height, width, length):
    for _ in range(12):
        path = [(rng.randrange(height), rng.randrange(width))]
        cells = set(path)
        while len(path) < length:
            r, c = path[-1]
            choices = [(r + dr, c + dc) for dr, dc in _D4
                       if 0 <= r + dr < height and 0 <= c + dc < width
                       and (r + dr, c + dc) not in cells
                       and len(_neighbors((r + dr, c + dc), cells)) == 1]
            if not choices:
                break
            point = rng.choice(choices)
            path.append(point)
            cells.add(point)
        if len(path) == length:
            return _normalize(path)
    # Constructive fallback has capacity >=20 on the minimum 5x6 canvas.
    route = _snake(height, width)
    start = rng.randrange(len(route) - length + 1)
    return _normalize(route[start:start + length])


def _varied_path(rng, height, width, length):
    kind = rng.choice(("walk", "walk", "snake", "straight", "l"))
    if kind == "straight" and length <= max(height, width):
        if length <= width and (length > height or rng.randrange(2)):
            return tuple((0, c) for c in range(length))
        return tuple((r, 0) for r in range(length))
    if kind == "l":
        shapes = []
        for transposed in (False, True):
            h, w = (width, height) if transposed else (height, width)
            for arm in range(2, min(w, length - 2) + 1):
                tail = length - arm
                if 2 <= tail < h:
                    points = [(0, c) for c in range(arm)] + [(r, arm - 1) for r in range(1, tail + 1)]
                    shapes.append(tuple((c, r) for r, c in points) if transposed else tuple(points))
        if shapes:
            return rng.choice(shapes)
    if kind == "snake":
        widths = [w for w in range(2, width + 1) if len(_snake(height, w)) >= length]
        route = _snake(height, rng.choice(widths))
        start = rng.randrange(len(route) - length + 1)
        return _normalize(route[start:start + length])
    return _walk(rng, height, width, length)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    contrast = profile != "varied"
    core = ctx.draw_choice("profile", ("canonical", "broad")) == "canonical"
    anchor_h, anchor_w = ctx.draw_choice("canonical_shape", ((5, 7), (7, 7), (8, 9)))
    height = ctx.draw_choice("grid_h", list(range(5, 15)) + ([anchor_h] * 60 if core else []))
    width = ctx.draw_choice("grid_w", list(range(6, 15)) + ([anchor_w] * 60 if core else []))
    # Exact overrides take priority over the teaching schedule. In their absence
    # every contrast draw refutes all base rivals and its parity-conditioned
    # seed-order rival; free draws retain complete 4..20 support.
    if overrides.get("path_len") is not None:
        length = ctx.draw_int("path_len", 4, 20)
    elif profile == "odd_contrast":
        favored = 7 if difficulty == "easy" else 13 if difficulty == "hard" else 9
        length = ctx.draw_choice("path_len", [7, 9, 11, 13] + [favored] * 3)
    elif profile == "even_contrast":
        favored = 10 if difficulty == "easy" else 18 if difficulty == "hard" else 14
        length = ctx.draw_choice("path_len", [10, 12, 14, 16, 18, 20] + [favored] * 3)
    else:
        favored = list(range(4, 10)) if difficulty == "easy" else list(range(13, 21)) if difficulty == "hard" else list(range(7, 16))
        length = ctx.draw_choice("path_len", list(range(4, 21)) + favored)
    rng = ctx.draw_rng("geometry")
    contrast_paths = []
    if contrast and length in (7, 9, 11, 13, 10, 12, 14, 16, 18, 20):
        contrast_paths = [p for p in _contrast_templates(length)
                          if max(r for r, _ in p) < height and max(c for _, c in p) < width]
    if contrast_paths:
        path = rng.choice(contrast_paths)
    else:
        path = _varied_path(rng, height, width, length)
    # Fit-preserving reflections and translations; transpose is already present
    # in the contrast bank and varied construction. Seed order is independent
    # for varied paths, deliberately reversed in contrast paths.
    ph = max(r for r, _ in path) + 1
    pw = max(c for _, c in path) + 1
    flip_r, flip_c = rng.randrange(2), rng.randrange(2)
    dr, dc = rng.randrange(height - ph + 1), rng.randrange(width - pw + 1)
    path = [(dr + (ph - 1 - r if flip_r else r), dc + (pw - 1 - c if flip_c else c)) for r, c in path]
    if not contrast_paths and rng.randrange(2):
        path.reverse()
    return _paint(path, height, width, reverse_seed_order=bool(contrast_paths))


_BASE_COMPETITORS = {name: partial(_prediction, mode=name) for name in (
    "bfs8", "diagonal_euclidean", "raster_seed_order", "turn_penalty_half",
    "turn_discount_half", "turn_penalty_one", "manhattan", "euclidean_squared", "chebyshev",
)}
LESSON_COMPETITORS = dict(_BASE_COMPETITORS)
LESSON_COMPETITORS.update({name: partial(_prediction, mode=name) for name in (
    "even_raster_seed_order", "odd_raster_seed_order",
)})
CANONICAL_SHORTCUTS = {name: LESSON_COMPETITORS[name] for name in (
    "bfs8", "diagonal_euclidean", "raster_seed_order", "turn_penalty_half", "turn_discount_half",
    "even_raster_seed_order", "odd_raster_seed_order",
)}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
SEMANTIC_WITNESSES = {"odd_metric_contrast": _odd_contrast, "even_metric_contrast": _even_contrast}
WITNESS_RIVALS = {
    "odd_metric_contrast": [*_BASE_COMPETITORS, "odd_raster_seed_order"],
    "even_metric_contrast": [*_BASE_COMPETITORS, "even_raster_seed_order"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; no claim of universal rule identifiability."""
    return [f"{name} fits demonstrations but changes query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
