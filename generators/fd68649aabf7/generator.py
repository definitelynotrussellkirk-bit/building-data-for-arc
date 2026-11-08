"""Nearest top marker recolors monochrome orthogonal components.

Input generation only; labels remain the pinned canonical Racket rule. Ordinary
draws alternate a randomized canonical-size population with two joint teaching
witnesses. The witness separates bbox center, left ties and four-connectivity
from eight plausible rules that fit all the canonical pairs.
"""
from __future__ import annotations

from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fd68649aabf7"
TASK_ID = GENERATOR_ID
VERSION = "2.2.0"
RULE_HASH = "f4e553d13f24"
SUMMARY = (
    "Distinct colored top-row markers recolor each monochrome four-connected "
    "body below an empty row 1. Choose the marker nearest the body's horizontal "
    "bounding-box center; exact ties choose the smaller column. Markers and "
    "background remain unchanged. Body colors are disjoint from marker colors."
)
INVARIANTS = [
    "integer colors 0..9; zero background; empty row 1",
    "2..6 distinct-color markers at distinct columns of row 0",
    "1..10 monochrome four-connected bodies in rows 2 onward",
    "body colors are disjoint from marker colors; diagonal same-color contacts are lawful",
    "every requested grid dimension, marker count and body count is realized exactly",
]
AXES = {
    "grid_h": {"type": "int", "default": "7..20; canonical slot favors 9", "valid": "7..20"},
    "grid_w": {"type": "int", "default": "9..24; canonical slot favors 12..14", "valid": "9..24"},
    "n_markers": {"type": "int", "default": "2..6; canonical slot favors 3", "valid": "2..6"},
    "n_blobs": {"type": "int", "default": "2..10; canonical slot favors 3", "valid": "1..10"},
}
# All joint combinations are constructive, including 7x9 / 6 markers / 10 bodies.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical", "joint_a", "joint_b")
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_axis(ctx, name, low, high, preferred):
    # Explicit controls use the full domain in every difficulty. Preferences
    # change the ordinary draw distribution, never the meaning of an override.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_choice(name, preferred)


def _neighbors(cells):
    return {(r + dr, c + dc) for r, c in cells for dr, dc in _DIRS}


def _joint_motif(rng, h, w):
    """Two orthogonal bodies, diagonally touching, with opposite assignments."""
    left = rng.randrange(w - 2)
    top = rng.randint(2, h - 5)
    right_body = {(top, left + 1), (top, left + 2)}
    left_body = {
        (top + 1, left), (top + 2, left), (top + 2, left + 1),
        (top + 2, left + 2), (top + 3, left + 2), (top + 4, left + 2),
    }
    # Middle-column additions preserve a strictly right-biased centroid while
    # the bounding-box center stays at the exact left-resolved marker tie.
    for row in (top + 3, top + 4):
        if rng.randrange(2):
            left_body.add((row, left + 1))
    if top > 2 and rng.randrange(2):
        right_body.add((top - 1, left + 2))
        if rng.randrange(2):
            right_body.add((top - 1, left + 1))
    return left, [right_body, left_body]


def _fill_bodies(rng, h, w, bodies, count):
    """Reserve all remaining components before growing any of them.

    A checkerboard supplies nonadjacent seeds. Growth may stop short of its
    optional shape size, but no requested component is ever dropped. Reserving
    rows 0/1 as unavailable coordinates (not occupied cells) permits row 2.
    """
    used = set().union(*bodies) if bodies else set()
    forbidden = used | _neighbors(used)
    needed = count - len(bodies)
    available = [(r, c) for r in range(2, h) for c in range(w)
                 if (r, c) not in forbidden]
    pools = [[p for p in available if (p[0] + p[1]) % 2 == parity] for parity in (0, 1)]
    feasible = [pool for pool in pools if len(pool) >= needed]
    if not feasible:
        raise RuntimeError("constructive body capacity invariant failed")
    seeds = rng.sample(rng.choice(feasible), needed)
    used.update(seeds)
    for seed in seeds:
        cells = {seed}
        target = rng.randint(2, 6)
        while len(cells) < target:
            other = used - cells
            candidates = sorted(p for p in _neighbors(cells)
                                if 2 <= p[0] < h and 0 <= p[1] < w
                                and p not in used
                                and not (_neighbors({p}) & other))
            if not candidates:
                break
            point = rng.choice(candidates)
            cells.add(point)
            used.add(point)
        bodies.append(cells)
    return bodies


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = sample_index % LESSON_SCHEDULE_PERIOD == 0
    if difficulty == "easy":
        heights, widths, markers, counts = range(7, 11), range(9, 15), (2, 3), (2, 3)
    elif difficulty == "hard":
        heights, widths, markers, counts = range(13, 21), range(15, 25), (4, 5, 6), range(5, 11)
    else:
        heights, widths, markers, counts = range(9, 15), range(12, 20), (3, 4), range(3, 7)
    h = _draw_axis(ctx, "grid_h", 7, 20, (9,) if core else heights)
    w = _draw_axis(ctx, "grid_w", 9, 24, (12, 13, 14) if core else widths)
    n_markers = _draw_axis(ctx, "n_markers", 2, 6, (3,) if core else markers)
    n_blobs = _draw_axis(ctx, "n_blobs", 1, 10, (3,) if core else counts)
    rng = ctx.draw_rng("geometry")
    palette_rng = ctx.draw_rng("palette")
    joint = not core and n_blobs >= 2
    bodies = []
    if joint:
        left, bodies = _joint_motif(rng, h, w)
        outer = [c for c in range(w) if c not in (left, left + 1, left + 2)]
        marker_cols = sorted([left, left + 2] + rng.sample(outer, n_markers - 2))
    else:
        marker_cols = sorted(rng.sample(range(w), n_markers))
    _fill_bodies(rng, h, w, bodies, n_blobs)
    marker_palette = palette_rng.sample(range(1, 10), n_markers)
    remaining = [c for c in range(1, 10) if c not in marker_palette]
    max_body_colors = min(len(remaining), n_blobs - int(joint))
    n_body_colors = min(3, max_body_colors) if core else palette_rng.randint(1, max_body_colors)
    body_palette = palette_rng.sample(remaining, n_body_colors)
    if joint:
        colors = [body_palette[0], body_palette[0]]
        colors += [body_palette[(i + 1) % n_body_colors] for i in range(n_blobs - 2)]
    else:
        colors = [body_palette[i % n_body_colors] for i in range(n_blobs)]
    grid = full_grid(h, w, 0)
    for col, color in zip(marker_cols, marker_palette):
        grid[0][col] = color
    for cells, color in zip(bodies, colors):
        for row, col in cells:
            grid[row][col] = color
    return grid


def _components(grid, *, diagonal=False):
    marker_colors = set(grid[0]) - {0}
    directions = _DIRS + (((1, 1), (1, -1), (-1, 1), (-1, -1)) if diagonal else ())
    seen = set()
    components = []
    for row in range(2, len(grid)):
        for col, color in enumerate(grid[row]):
            if color == 0 or color in marker_colors or (row, col) in seen:
                continue
            cells = [(row, col)]
            seen.add((row, col))
            for r, c in cells:
                for dr, dc in directions:
                    point = (r + dr, c + dc)
                    rr, cc = point
                    if (2 <= rr < len(grid) and 0 <= cc < len(grid[0])
                            and point not in seen and grid[rr][cc] == color):
                        seen.add(point)
                        cells.append(point)
            components.append(cells)
    return components


def observe_overrides(grid):
    """Measure exact controls from pixels, independently of draw bookkeeping."""
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_markers": sum(v != 0 for v in grid[0]),
            "n_blobs": len(_components(grid))}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty and rectangular"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    if not 7 <= len(grid) <= 20 or not 9 <= width <= 24:
        return ["sampler domain is 7..20 rows and 9..24 columns"]
    markers = [v for v in grid[0] if v]
    errors = []
    if not 2 <= len(markers) <= 6:
        errors.append("expected 2..6 top-row markers")
    if len(set(markers)) != len(markers):
        errors.append("marker colors must be distinct")
    if any(grid[1]):
        errors.append("row 1 must be empty")
    if any(v in markers for row in grid[2:] for v in row):
        errors.append("body colors must be disjoint from marker colors")
    if not 1 <= len(_components(grid)) <= 10:
        errors.append("expected 1..10 monochrome four-connected bodies")
    return errors


def strict_canonical_like(grid):
    """Lawful selected input manifold, including every labelled canonical pair."""
    return self_check(grid)


def _nearest(markers, numerator, denominator, *, right_tie=False):
    return min(markers, key=lambda col: (abs(col * denominator - numerator),
                                        -col if right_tie else col))


def _assignment(grid, mode):
    """Geometric predictions for rival diagnostics; never the label authority."""
    markers = [c for c, color in enumerate(grid[0]) if color]
    assignment = {}
    for index, cells in enumerate(_components(grid, diagonal=mode == "eight_connected")):
        low = min(c for _, c in cells)
        high = max(c for _, c in cells)
        numerator, denominator = low + high, 2
        if mode == "centroid":
            numerator, denominator = sum(c for _, c in cells), len(cells)
        elif mode == "left_edge":
            numerator, denominator = low, 1
        elif mode == "right_edge":
            numerator, denominator = high, 1
        elif mode == "floor_bbox":
            numerator, denominator = (low + high) // 2, 1
        column = (markers[min(index, len(markers) - 1)] if mode == "rank" else
                  _nearest(markers, numerator, denominator, right_tie=mode == "right_tie"))
        for row, col in cells:
            target = _nearest(markers, col, 1) if mode == "pixel" else column
            assignment[row, col] = grid[0][target]
    return assignment


def _rival(grid, *, mode):
    output = [list(row) for row in grid]
    for (row, col), color in _assignment(grid, mode).items():
        output[row][col] = color
    return output


def _witness(grid, *, mode):
    return _assignment(grid, "bbox") != _assignment(grid, mode)


_RIVAL_NAMES = ("centroid", "left_edge", "right_edge", "floor_bbox",
                "right_tie", "pixel", "rank", "eight_connected")
SEMANTIC_RIVALS = {name: partial(_rival, mode=name) for name in _RIVAL_NAMES}
SEMANTIC_WITNESSES = {name: partial(_witness, mode=name) for name in _RIVAL_NAMES}
WITNESS_RIVALS = {name: [name] for name in _RIVAL_NAMES}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
