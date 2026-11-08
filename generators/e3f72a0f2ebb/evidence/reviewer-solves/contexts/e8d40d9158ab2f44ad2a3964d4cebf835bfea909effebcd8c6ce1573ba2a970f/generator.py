"""Inputs for replacing each connected object by its tight bounding-box frame.

The selected Racket rule is the label authority. Normal draws mix changing and
unchanged components, including disconnected objects sharing a color. Placement
reserves the complete output rectangles, not just occupied input pixels.
"""
from __future__ import annotations

from collections import defaultdict

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "e3f72a0f2ebb"
TASK_ID = GENERATOR_ID
RULE_HASH = "8d3a7f6a327b"
VERSION = "4.0.0"
SUMMARY = (
    "Replace every 4-connected, same-color nonzero object by the frame of its "
    "tight bounding box on a fresh zero grid. Draw 2..4 separated objects with "
    "1..4 distinct colors, varied positions and shapes, including fixed points. "
    "Disconnected objects may share a color; their frames stay separate."
)
INVARIANTS = [
    "normal draws contain exactly 2..4 same-color 4-connected components",
    "complete component bounding boxes are separated by at least one blank row or column",
    "all colors 1..9 are interchangeable; zero is the fixed background",
    "singletons, lines and complete frames are lawful unchanged components",
    "every default draw requires both adding frame pixels and erasing interior pixels",
]
AXES = {
    "grid_h": {"type": "int", "default": "7..18; even phases favor 8", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "8..18; even phases favor 10..12", "valid": "8..18"},
    "n_blobs": {"type": "int", "default": "2..4; adapts to an exact color count", "valid": "2..4"},
    "n_distinct_colors": {"type": "int", "default": "1..n_blobs; odd phases repeat a color", "valid": "1..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_blobs": 2, "n_distinct_colors": [3, 4]},
    {"n_blobs": 3, "n_distinct_colors": 4},
]
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("cross", "branch_with_fixed_point", "notched_solid", "path_with_fixed_point")
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    """The semantic roles repeat; geometry, positions and colors remain random."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _weighted_int(ctx, name, lo, hi, favored):
    # Keep the complete control domain available in every band. Repeated options
    # affect default probabilities only; explicit overrides retain exact values.
    return ctx.draw_choice(name, list(range(lo, hi + 1)) + list(favored) * 40)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override keys: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not bool/float/string")
        lo, hi = map(int, AXES[name]["valid"].split(".."))
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    n, k = overrides.get("n_blobs"), overrides.get("n_distinct_colors")
    if n is not None and k is not None and k > n:
        raise ValueError("n_distinct_colors cannot exceed n_blobs")


def _regions(h, w, n, rng):
    """Construct disjoint capacity, even for the smallest full joint override."""
    if n == 2 and rng.choice((False, True)):
        if rng.choice((False, True)):
            cut = rng.randint(3, h - 4)
            regions = [(0, 0, cut, w), (cut + 1, 0, h - cut - 1, w)]
        else:
            cut = rng.randint(3, w - 4)
            regions = [(0, 0, h, cut), (0, cut + 1, h, w - cut - 1)]
    else:
        rr, cc = rng.randint(3, h - 4), rng.randint(3, w - 4)
        regions = [
            (0, 0, rr, cc), (0, cc + 1, rr, w - cc - 1),
            (rr + 1, 0, h - rr - 1, cc),
            (rr + 1, cc + 1, h - rr - 1, w - cc - 1),
        ]
    rng.shuffle(regions)
    return regions[:n]


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _bbox_outline(cells):
    r1, c1, r2, c2 = _bbox(cells)
    return {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)}


def _informative_shape(h, w, phase, rng):
    """Connected spanning shapes with both an interior pixel and missing border."""
    ir, ic = rng.randint(1, h - 2), rng.randint(1, w - 2)
    if phase == 0:
        cells = {(ir, c) for c in range(w)} | {(r, ic) for r in range(h)}
    elif phase == 1:
        cells = {(0, c) for c in range(w)} | {(r, ic) for r in range(h)}
    elif phase == 2:
        cells = {(r, c) for r in range(h) for c in range(w)} - {(0, 0)}
    else:
        cells = {(0, 0)}
        r, c = 0, 0
        for tr, tc in ((ir, ic), (h - 1, w - 1)):
            while (r, c) != (tr, tc):
                steps = ([(1, 0)] if r < tr else []) + ([(0, 1)] if c < tc else [])
                dr, dc = rng.choice(steps)
                r, c = r + dr, c + dc
                cells.add((r, c))
    if rng.choice((False, True)):
        cells = {(h - 1 - r, c) for r, c in cells}
    if rng.choice((False, True)):
        cells = {(r, w - 1 - c) for r, c in cells}
    return cells


def _fixed_shape(region_h, region_w, rng):
    kind = rng.choice(("singleton", "row", "column", "frame"))
    if kind == "singleton":
        return {(0, 0)}
    if kind == "row":
        return {(0, c) for c in range(rng.randint(2, region_w))}
    if kind == "column":
        return {(r, 0) for r in range(rng.randint(2, region_h))}
    h, w = rng.randint(2, region_h), rng.randint(2, region_w)
    return _bbox_outline(((0, 0), (h - 1, w - 1)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    core = phase % 2 == 0
    favored_h = [8] if core else list({"easy": range(7, 11), "hard": range(12, 19)}.get(difficulty, range(8, 15)))
    favored_w = [10, 11, 12] if core else list({"easy": range(8, 13), "hard": range(12, 19)}.get(difficulty, range(9, 16)))
    h = _weighted_int(ctx, "grid_h", 7, 18, favored_h)
    w = _weighted_int(ctx, "grid_w", 8, 18, favored_w)
    requested_colors = overrides.get("n_distinct_colors") or 1
    min_blobs = max(2, requested_colors) if overrides.get("n_blobs") is None else 2
    favored_n = [2, 3] if core or difficulty != "hard" else [3, 4]
    n = _weighted_int(ctx, "n_blobs", min_blobs, 4, [v for v in favored_n if v >= min_blobs])
    if overrides.get("n_distinct_colors") is not None:
        color_choices = list(range(1, n + 1))
    else:
        color_choices = [n] if core else list(range(1, n))
    k = ctx.draw_choice("n_distinct_colors", color_choices)
    rng = ctx.draw_rng("layout")
    palette = rng.sample(range(1, 10), k)
    colors = palette + [rng.choice(palette) for _ in range(n - k)]
    rng.shuffle(colors)
    regions = _regions(h, w, n, rng)
    g = full_grid(h, w, 0)
    cap = {"easy": 4, "hard": 8}.get(difficulty, 6)
    for i, (r0, c0, rh, rw) in enumerate(regions):
        shape_rng = ctx.draw_rng(f"shape_{i}")
        if (i == 1 and phase % 2 == 1) or (i > 1 and shape_rng.randrange(3) == 0):
            cells = _fixed_shape(rh, rw, shape_rng)
        else:
            sh, sw = shape_rng.randint(3, min(rh, cap)), shape_rng.randint(3, min(rw, cap))
            cells = _informative_shape(sh, sw, phase if i == 0 else shape_rng.randrange(4), shape_rng)
        _, _, r2, c2 = _bbox(cells)
        rr, cc = r0 + rng.randint(0, rh - r2 - 1), c0 + rng.randint(0, rw - c2 - 1)
        paint_at(g, rr, cc, sorted(cells), colors[i])
    return g


def _components(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen, comps = set(), []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color, stack, cells = grid[r][c], [(r, c)], []
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30 or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["expected dimensions at most 30 and integer colors 0..9"]
    comps = _components(grid)
    if not 1 <= len(comps) <= 4:
        return ["expected 1..4 connected objects in this sampler's domain"]
    boxes = [_bbox(cells) for _, cells in comps]
    for i, (r1, c1, r2, c2) in enumerate(boxes):
        for s1, t1, s2, t2 in boxes[i + 1:]:
            if not (r2 < s1 or s2 < r1 or c2 < t1 or t2 < c1):
                return ["component bounding boxes overlap; output frames may interfere"]
    return []


def strict_canonical_like(grid):
    """Lawful noninterfering component-frame instances, including fixed points."""
    return self_check(grid)


def observe_overrides(grid):
    comps = _components(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blobs": len(comps),
            "n_distinct_colors": len({color for color, _ in comps})}


def _render_rival(grid, *, merge_colors=False, filled=False, preserve=False, drop_fixed=False):
    """Pure rival predictions for authoring checks; never used as labels."""
    comps = _components(grid)
    if merge_colors:
        grouped = defaultdict(list)
        for color, cells in comps:
            grouped[color].extend(cells)
        comps = sorted(grouped.items())
    out = [list(row) for row in grid] if preserve else full_grid(len(grid), len(grid[0]), 0)
    for color, cells in comps:
        boundary = _bbox_outline(cells)
        if drop_fixed and set(cells) == boundary:
            continue
        if filled:
            r1, c1, r2, c2 = _bbox(cells)
            boundary = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        for r, c in boundary:
            out[r][c] = color
    return out


def _color_box(grid):
    return _render_rival(grid, merge_colors=True)


def _solid_boxes(grid):
    return _render_rival(grid, filled=True)


def _add_frames(grid):
    return _render_rival(grid, preserve=True)


def _drop_fixed_points(grid):
    return _render_rival(grid, drop_fixed=True)


def _identity(grid):
    return [list(row) for row in grid]


def _repeated_color(grid):
    colors = [color for color, _ in _components(grid)]
    return len(colors) != len(set(colors))


def _interior_occupied(grid):
    return any(set(cells) - _bbox_outline(cells) for _, cells in _components(grid))


def _missing_border(grid):
    return any(_bbox_outline(cells) - set(cells) for _, cells in _components(grid))


def _has_fixed_point(grid):
    return any(set(cells) == _bbox_outline(cells) for _, cells in _components(grid))


SEMANTIC_WITNESSES = {
    "separate_same_color_objects": _repeated_color,
    "erase_interior": _interior_occupied,
    "complete_border": _missing_border,
    "retain_fixed_points": _has_fixed_point,
}
SEMANTIC_RIVALS = {
    "color_box": _color_box, "solid_boxes": _solid_boxes,
    "add_frames": _add_frames, "drop_fixed_points": _drop_fixed_points,
    "identity": _identity,
}
WITNESS_RIVALS = {
    "separate_same_color_objects": ["color_box"],
    "erase_interior": ["add_frames", "solid_boxes"],
    "complete_border": ["identity"],
    "retain_fixed_points": ["drop_fixed_points"],
}
CANONICAL_SHORTCUTS = {"color_box": _color_box}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
