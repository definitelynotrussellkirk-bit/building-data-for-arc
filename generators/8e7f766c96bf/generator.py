"""Input sampler for E161: fill only complete blue 4x4 hollow frames red.

Racket remains the label authority. Sparse scenes alternate with contrast scenes
containing 3x3, 4x5 and 5x4 distractors. Three demonstrations retain a contrast
witness even after any single-query rotation of four consecutive samples.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "8e7f766c96bf"
TASK_ID = GENERATOR_ID
RULE_HASH = "bb4f82892380"
VERSION = "2.0.0"
SUMMARY = "Fill only blue hollow frames whose outer height and width both equal four."
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0; all foreground cells are blue 1",
    "each 4-connected component is a complete hollow rectangle with empty interior",
    "at least one component has outer dimensions 4x4",
    "all requested targets and contrast distractors fit without truncation or overlap",
]
AXES = {
    "grid_h": {"type": "int", "default": "9..22, canonical sizes favored", "valid": "9..22"},
    "grid_w": {"type": "int", "default": "12..22, canonical sizes favored", "valid": "12..22"},
    "n_squares": {"type": "int", "default": "1..3, difficulty weighted", "valid": "1..3"},
    "texture": {"type": "str", "default": "alternating sparse/contrast", "valid": "sparse|contrast"},
}
# Unsupported joint shelf layouts raise ValueError with the requested axes.
# This declares sampler support, not impossibility under all geometric packings.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("sparse", "contrast")
_CANONICAL_SIZES = ((9, 13), (11, 14), (12, 15), (12, 12), (10, 15))
_INT_LIMITS = {"grid_h": (9, 22), "grid_w": (12, 22), "n_squares": (1, 3)}


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 2]


def _shapes(n_squares, texture, large):
    targets = ((4, 4),) * n_squares
    if texture == "contrast":
        return targets + ((3, 3), (4, 5), (5, 4))
    return targets + (((5, 5),) if large else ())


@lru_cache(maxsize=256)
def _packing_table(shapes, width):
    """Minimum shelf height for every object subset, with one-cell gaps.

    Dynamic programming considers every row subset. Its result is a feasibility
    certificate; generation never relies on capped random placement retries.
    Only immutable geometry is cached, never random draws or returned grids.
    """
    size = 1 << len(shapes)
    row_heights = [0] * size
    row_widths = [0] * size
    minimum = [10**6] * size
    minimum[0] = 0
    for mask in range(1, size):
        dimensions = [shape for i, shape in enumerate(shapes) if mask & (1 << i)]
        row_heights[mask] = max(h for h, _ in dimensions)
        row_widths[mask] = sum(w for _, w in dimensions) + len(dimensions) - 1
        anchor = mask & -mask
        row = mask
        while row:
            rest = mask ^ row
            if row & anchor and row_widths[row] <= width:
                cost = row_heights[row] + (1 + minimum[rest] if rest else 0)
                minimum[mask] = min(minimum[mask], cost)
            row = (row - 1) & mask
    return tuple(minimum), tuple(row_heights), tuple(row_widths)


def _available_sizes(shapes, overrides):
    heights = [overrides["grid_h"]] if overrides.get("grid_h") is not None else range(9, 23)
    widths = [overrides["grid_w"]] if overrides.get("grid_w") is not None else range(12, 23)
    result = []
    for w in widths:
        needed = _packing_table(shapes, w)[0][-1]
        result.extend((h, w) for h in heights if h >= needed)
    return result


def _spacings(rng, spare, count):
    gaps = [0] * count
    for _ in range(spare):
        gaps[rng.randrange(count)] += 1
    return gaps


def _place(grid, shapes, rng):
    h, w = len(grid), len(grid[0])
    minimum, row_heights, row_widths = _packing_table(shapes, w)
    mask, budget = (1 << len(shapes)) - 1, h
    shelves = []
    while mask:
        choices = []
        anchor = mask & -mask
        row = mask
        while row:
            rest = mask ^ row
            needed = row_heights[row] + (1 + minimum[rest] if rest else 0)
            if row & anchor and row_widths[row] <= w and needed <= budget:
                choices.append(row)
            row = (row - 1) & mask
        if not choices:
            raise RuntimeError("constructive packing certificate was not realized")
        chosen = rng.choice(choices)
        shelves.append([shape for i, shape in enumerate(shapes) if chosen & (1 << i)])
        mask ^= chosen
        budget -= row_heights[chosen] + (1 if mask else 0)
    rng.shuffle(shelves)
    used_h = sum(max(sh for sh, _ in row) for row in shelves) + len(shelves) - 1
    vertical = _spacings(rng, h - used_h, len(shelves) + 1)
    r = vertical[0]
    for j, row in enumerate(shelves):
        rng.shuffle(row)
        shelf_h = max(sh for sh, _ in row)
        used_w = sum(sw for _, sw in row) + len(row) - 1
        horizontal = _spacings(rng, w - used_w, len(row) + 1)
        c = horizontal[0]
        for k, (sh, sw) in enumerate(row):
            top = r + rng.randint(0, shelf_h - sh)
            draw_rect_outline(grid, top, c, sh, sw, 1)
            c += sw + 1 + horizontal[k + 1]
        r += shelf_h + 1 + vertical[j + 1]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, (lo, hi) in _INT_LIMITS.items():
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be a Python integer in [{lo}, {hi}]")
    if overrides.get("texture") is not None and overrides["texture"] not in SCHEDULE_PROFILES:
        raise ValueError("texture must be sparse or contrast")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    # Overrides receive the full legal domain; an ordinary lesson uses the
    # declared deterministic schedule. Both choices are recorded through GenCtx.
    texture_options = SCHEDULE_PROFILES if overrides.get("texture") is not None else (
        schedule_profile(seed, sample_index, difficulty),)
    texture = ctx.draw_choice("texture", texture_options)
    requested = overrides.get("n_squares")
    counts = [requested] if requested is not None else range(1, 4)
    configurations = {}
    for large in ((False, True) if texture == "sparse" else (False,)):
        sizes_by_count = {n: _available_sizes(_shapes(n, texture, large), overrides) for n in counts}
        feasible = {n: sizes for n, sizes in sizes_by_count.items() if sizes}
        if feasible:
            configurations[large] = feasible
    if not configurations:
        error = ValueError("requested dimensions/count has no supported separated shelf layout")
        error.incompatible_axes = tuple(name for name, value in overrides.items() if value is not None)
        raise error
    # An optional shape cannot invalidate an otherwise feasible exact request.
    large = ctx.draw_choice("large_distractor", tuple(configurations)) if texture == "sparse" else False
    candidates = configurations[large]
    favored = (1, 1, 1) if difficulty == "easy" else ((2, 3, 3) if difficulty == "hard" else ())
    n = ctx.draw_choice("n_squares", list(candidates) + [v for v in favored if v in candidates])
    sizes = candidates[n]
    heights = sorted({h for h, _ in sizes})
    # Shape/palette anchors remain freshly sampled scenes, never copied examples.
    anchor_h = [h for h, w in _CANONICAL_SIZES if (h, w) in sizes]
    h = ctx.draw_choice("grid_h", heights + anchor_h * 12)
    widths = sorted({w for hh, w in sizes if hh == h})
    anchor_w = [w for hh, w in _CANONICAL_SIZES if hh == h and w in widths]
    w = ctx.draw_choice("grid_w", widths + anchor_w * 20)
    grid = full_grid(h, w, 0)
    _place(grid, _shapes(n, texture, large), ctx.draw_rng("placement"))
    return grid


def _components(grid):
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    components = []
    while pending:
        start = min(pending)
        pending.remove(start)
        cells, queue = {start}, [start]
        while queue:
            r, c = queue.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in pending:
                    pending.remove(point)
                    cells.add(point)
                    queue.append(point)
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        components.append((r0, c0, r1 - r0 + 1, c1 - c0 + 1, cells))
    return components


def _is_frame(component):
    r, c, h, w, cells = component
    if h < 3 or w < 3:
        return False
    border = {(rr, cc) for rr in range(r, r + h) for cc in range(c, c + w)
              if rr in (r, r + h - 1) or cc in (c, c + w - 1)}
    return cells == border


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid dimensions must not exceed 30"]
    if any(type(value) is not int or value not in (0, 1) for row in grid for value in row):
        return ["input cells must be Python integer colors 0 or 1"]
    components = _components(grid)
    errors = []
    if not any(obj[2] == obj[3] == 4 and _is_frame(obj) for obj in components):
        errors.append("expected at least one complete blue 4x4 hollow frame")
    for obj in components:
        r, c, h, w, _ = obj
        if not _is_frame(obj):
            errors.append(f"component at ({r}, {c}) is not a complete hollow rectangle")
        elif any(grid[rr][cc] != 0 for rr in range(r + 1, r + h - 1) for cc in range(c + 1, c + w - 1)):
            errors.append(f"frame at ({r}, {c}) has a nonempty interior")
    return errors


def strict_canonical_like(grid):
    """Structural task domain; exact dimensions are measured by the profile gate."""
    return self_check(grid)


def observe_overrides(grid):
    sizes = [(h, w) for _, _, h, w, _ in _components(grid)]
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_squares": sizes.count((4, 4)),
            "texture": "contrast" if all(shape in sizes for shape in ((3, 3), (4, 5), (5, 4))) else "sparse"}


def _rival_fill(grid, choose):
    """Candidate-rule predictions for diagnostics; never used to generate labels."""
    out = [list(row) for row in grid]
    frames = [obj for obj in _components(grid) if _is_frame(obj)]
    for obj in frames:
        r, c, h, w, _ = obj
        if choose(h, w, frames):
            for rr in range(r + 1, r + h - 1):
                for cc in range(c + 1, c + w - 1):
                    out[rr][cc] = 2
    return out


def _smallest_frame(grid):
    return _rival_fill(grid, lambda h, w, frames: h * w == min(o[2] * o[3] for o in frames))


def _height_four(grid):
    return _rival_fill(grid, lambda h, w, frames: h == 4)


def _width_four(grid):
    return _rival_fill(grid, lambda h, w, frames: w == 4)


def _small_squares(grid):
    return _rival_fill(grid, lambda h, w, frames: h == w and h <= 4)


def _all_frames(grid):
    return _rival_fill(grid, lambda h, w, frames: True)


def _has_size(grid, shape):
    return any((obj[2], obj[3]) == shape and _is_frame(obj) for obj in _components(grid))


SEMANTIC_WITNESSES = {
    "smaller_frame": lambda g: _has_size(g, (3, 3)),
    "height_only_decoy": lambda g: _has_size(g, (4, 5)),
    "width_only_decoy": lambda g: _has_size(g, (5, 4)),
    "large_frame": lambda g: _has_size(g, (5, 5)),
}
CANONICAL_SHORTCUTS = {
    "smallest_frame": _smallest_frame,
    "height_four": _height_four,
    "width_four": _width_four,
    "small_squares": _small_squares,
}
SEMANTIC_RIVALS = {**CANONICAL_SHORTCUTS, "all_frames": _all_frames}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
WITNESS_RIVALS = {
    "smaller_frame": ["smallest_frame", "small_squares"],
    "height_only_decoy": ["height_four"],
    "width_only_decoy": ["width_four"],
    "large_frame": ["all_frames"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival guard on labeled pairs, not a uniqueness proof."""
    return [f"{name} fits every demonstration but disagrees on the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
