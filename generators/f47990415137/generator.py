"""Inputs for component-wise bbox-aspect recoloring; Racket supplies all labels.

Default inputs refute global color grouping and filling an object's bounding box.
The four exact controls describe returned pixels. See notes.md for migration
from the v2 ignored palette/texture controls and for this sampler's domain limits.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f47990415137"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5cf35af61edf"
SUMMARY = (
    "Recolor each monochrome 4-component by its bounding-box aspect: tall->2, "
    "wide->3, square->4. Varied connected shapes, repeated colors across aspects, "
    "8..20 canvases, 3..6 objects; all bands retain canonical-scale support."
)
INVARIANTS = [
    "8..20 rectangular integer-color grid with zero background and 3..6 objects",
    "objects are monochrome 4-connected and mutually 8-separated",
    "at least one tall, wide, and square bounding box in every returned input",
    "default inputs repeat a color across tall/wide objects and include a nonrectangle",
    "explicit object and foreground-palette counts are exact; no dropped-object fallback",
]
AXES = {
    "grid_h": {"type": "int", "default": "8..20; core mixture favors 10", "valid": "8..20"},
    "grid_w": {"type": "int", "default": "8..20; core mixture favors 12", "valid": "8..20"},
    "n_blobs": {"type": "int", "default": "3..6; core mixture favors 4", "valid": "3..6"},
    "n_distinct_colors": {"type": "int", "default": "1..n_blobs-1; core favors 3", "valid": "1..6"},
}
# A repeated color is a DEFAULT teaching choice, not a validator restriction.
# Explicit all-distinct palettes remain useful controls and include canonical data.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("n_blobs", "n_distinct_colors")]
MIN_STRICT_FRAC = 1.0
_FOUR = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if (r, c) != (0, 0))


class IncompatibleControls(ValueError):
    incompatible_axes = ("n_blobs", "n_distinct_colors")


def _components(grid):
    seen = set()
    groups = []
    h, w = len(grid), len(grid[0])
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if not color or (sr, sc) in seen:
                continue
            queue = [(sr, sc)]
            seen.add((sr, sc))
            for r, c in queue:
                for dr, dc in _FOUR:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            groups.append((color, queue))
    return groups


def _bbox(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def _orientation(cells):
    r0, c0, r1, c1 = _bbox(cells)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    return "tall" if h > w else "wide" if w > h else "square"


def _shape(rng, orient, max_h, max_w, *, nonrectangle=False):
    sizes = [(h, w) for h in range(1, min(6, max_h) + 1)
             for w in range(1, min(6, max_w) + 1)
             if ("tall" if h > w else "wide" if w > h else "square") == orient
             and (not nonrectangle or min(h, w) >= 2)]
    h, w = rng.choice(sizes)
    whole = {(r, c) for r in range(h) for c in range(w)}
    if min(h, w) == 1 or (not nonrectangle and rng.randrange(3) == 0):
        cells = whole
    else:
        # Start from an L spanning the box, then grow through adjacent cells.
        # Connectivity and bbox dimensions hold constructively at every step.
        cells = {(r, 0) for r in range(h)} | {(0, c) for c in range(w)}
        limit = h * w - (1 if nonrectangle else 0)
        target = rng.randint(len(cells), limit)
        while len(cells) < target:
            frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in _FOUR}
                              & (whole - cells))
            cells.add(rng.choice(frontier))
    # Both flips preserve class while avoiding a privileged filled corner.
    if rng.randrange(2):
        cells = {(h - 1 - r, c) for r, c in cells}
    if rng.randrange(2):
        cells = {(r, w - 1 - c) for r, c in cells}
    return cells


def _place_shape(rng, h, w, used, shape):
    sh, sw = max(r for r, c in shape) + 1, max(c for r, c in shape) + 1
    for _ in range(48):
        r0, c0 = rng.randint(0, h - sh), rng.randint(0, w - sw)
        cells = {(r + r0, c + c0) for r, c in shape}
        if cells & used:
            continue
        if any((r + dr, c + dc) in used for r, c in cells for dr, dc in _EIGHT):
            continue
        return cells
    return None


def _slot_intervals(length, count, rng):
    """Partition into positive bands with one empty separator; each band >=2."""
    sizes = [2] * count
    for _ in range(length - (count - 1) - 2 * count):
        sizes[rng.randrange(count)] += 1
    result = []
    start = 0
    for size in sizes:
        result.append((start, size))
        start += size + 1
    return result


def _constructive_layout(rng, h, w, plan):
    """Exact-count crowded-grid fallback; never silently falls back to 3 blobs."""
    nr, nc = (2, 2) if len(plan) <= 4 else rng.choice(((2, 3), (3, 2)))
    rows = _slot_intervals(h, nr, rng)
    cols = _slot_intervals(w, nc, rng)
    slots = [(r, c, rh, cw) for r, rh in rows for c, cw in cols]
    rng.shuffle(slots)
    placed = []
    for (orient, color, nonrect), (r0, c0, rh, cw) in zip(plan, slots):
        shape = _shape(rng, orient, rh, cw, nonrectangle=nonrect)
        sh, sw = max(r for r, c in shape) + 1, max(c for r, c in shape) + 1
        r0 += rng.randint(0, rh - sh)
        c0 += rng.randint(0, cw - sw)
        placed.append((color, {(r + r0, c + c0) for r, c in shape}))
    return placed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or removed override axes: {sorted(unknown)}")
    bounds = {"grid_h": (8, 20), "grid_w": (8, 20), "n_blobs": (3, 6),
              "n_distinct_colors": (1, 6)}
    for name, value in overrides.items():
        if value is not None and (type(value) is not int or not bounds[name][0] <= value <= bounds[name][1]):
            raise ValueError(f"{name} must be an integer in {bounds[name]}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = ctx.draw_choice("profile", ("core", "core", "core", "broad", "broad")) == "core"
    h = ctx.draw_choice("grid_h", list(range(8, 21)) + ([10] * 200 if core else []))
    w = ctx.draw_choice("grid_w", list(range(8, 21)) + ([12] * 200 if core else []))
    requested_colors = overrides.get("n_distinct_colors")
    min_n = max(3, requested_colors or 1) if overrides.get("n_blobs") is None else 3
    favored_n = 4 if core or difficulty != "hard" else 6
    n_options = list(range(min_n, 7))
    n = ctx.draw_choice("n_blobs", n_options + ([favored_n] * 12 if favored_n in n_options else []))
    color_options = list(range(1, 7)) if requested_colors is not None else list(range(1, n))
    if requested_colors is None and 3 in color_options:
        color_options += [3] * (200 if core else 4)
    k = ctx.draw_choice("n_distinct_colors", color_options)
    if k > n:
        raise IncompatibleControls("n_distinct_colors cannot exceed n_blobs")
    rng = ctx.draw_rng("layout")
    palette = rng.sample(range(1, 10), k)
    orientations = ["tall", "wide", "square"] + rng.choices(("tall", "wide", "square"), k=n-3)
    if k < n:
        # The same input color must map to both 2 and 3: global-color rules fail.
        colors = [palette[0], palette[0]] + palette[1:]
        colors += [rng.choice(palette) for _ in range(n - len(colors))]
    else:
        colors = palette[:]
    plan = [(orient, color, i == 2) for i, (orient, color) in enumerate(zip(orientations, colors))]
    rng.shuffle(plan)
    placed = None
    for _ in range(10):
        used = set()
        trial = []
        for orient, color, nonrect in plan:
            shape = _shape(rng, orient, h, w, nonrectangle=nonrect)
            cells = _place_shape(rng, h, w, used, shape)
            if cells is None:
                break
            used.update(cells)
            trial.append((color, cells))
        if len(trial) == n:
            placed = trial
            break
    if placed is None:
        placed = _constructive_layout(rng, h, w, plan)
    grid = full_grid(h, w, 0)
    for color, cells in placed:
        for r, c in cells:
            grid[r][c] = color
    return grid


def observe_overrides(grid):
    groups = _components(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blobs": len(groups),
            "n_distinct_colors": len({color for color, cells in groups})}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        return ["grid must be a nonempty list of nonempty rows"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["colors must be integers 0..9 (not bool)"]
    if not (8 <= h <= 20 and 8 <= w <= 20):
        return ["grid dimensions must be within 8..20"]
    groups = _components(grid)
    errors = []
    if not 3 <= len(groups) <= 6:
        errors.append(f"expected 3..6 components, got {len(groups)}")
    missing = {"tall", "wide", "square"} - {_orientation(cells) for _, cells in groups}
    if missing:
        errors.append(f"missing aspect classes: {sorted(missing)}")
    owner = {cell: i for i, (_, cells) in enumerate(groups) for cell in cells}
    if any(owner.get((r + dr, c + dc), i) != i
           for (r, c), i in owner.items() for dr, dc in _EIGHT):
        errors.append("distinct objects must be 8-separated")
    return errors


def strict_canonical_like(grid):
    """Task-domain validity, not exact canonical rectangle shape or palette."""
    return self_check(grid)


def _group_by_color(grid):
    """RIVAL: incorrectly merge disconnected objects sharing an input color."""
    merged = {}
    for color, cells in _components(grid):
        merged.setdefault(color, []).extend(cells)
    out = full_grid(len(grid), len(grid[0]), 0)
    for cells in merged.values():
        value = {"tall": 2, "wide": 3, "square": 4}[_orientation(cells)]
        for r, c in cells:
            out[r][c] = value
    return out


def _fill_bounding_boxes(grid):
    """RIVAL: classify correctly but paint background inside each bounding box."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for _, cells in _components(grid):
        r0, c0, r1, c1 = _bbox(cells)
        value = {"tall": 2, "wide": 3, "square": 4}[_orientation(cells)]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = value
    return out


def _color_spans_aspects(grid):
    aspects = {}
    for color, cells in _components(grid):
        aspects.setdefault(color, set()).add(_orientation(cells))
    return any(len(values) > 1 for values in aspects.values())


def _nonrectangle(grid):
    for _, cells in _components(grid):
        r0, c0, r1, c1 = _bbox(cells)
        if len(cells) < (r1 - r0 + 1) * (c1 - c0 + 1):
            return True
    return False


SEMANTIC_WITNESSES = {"color_spans_aspects": _color_spans_aspects, "nonrectangle": _nonrectangle}
SEMANTIC_RIVALS = {"group_by_color": _group_by_color, "fill_bounding_boxes": _fill_bounding_boxes}
WITNESS_RIVALS = {"color_spans_aspects": ["group_by_color"], "nonrectangle": ["fill_bounding_boxes"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
