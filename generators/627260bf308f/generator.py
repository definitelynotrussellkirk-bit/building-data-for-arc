"""Inputs for palette-rank recoloring; canonical Racket remains label authority.

Even indices are compact counterexamples to seven canonical-fitting shortcuts.
Odd indices broaden shapes, counts, sizes, positions, dimensions and palettes.
All four advertised axes are exact and independently observable. The misleading
v2 palette/count aliases and texture controls were removed, not silently accepted.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "627260bf308f"
TASK_ID = "627260bf308f"
RULE_HASH = "088353dcd64f"
VERSION = "3.0.0"
SUMMARY = "Read the row-0 palette left-to-right; color size-ranked 4-connected color-8 components."
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "row 0 contains 2..5 distinct nonzero palette colors, excluding placeholder 8",
    "row 1 is blank; all body cells are 0 or 8",
    "exactly one palette entry per 4-connected body component; component sizes are distinct",
    "diagonal contacts are allowed and do not merge 4-connected components",
    "placement is all-or-nothing with a constructive fallback; no component is silently omitted",
]
AXES = {
    "grid_h": {"type": "int", "default": "8/9 in witness draws; 8..24 otherwise", "valid": "8..24"},
    "grid_w": {"type": "int", "default": "10/11 in witness draws; 10..24 otherwise", "valid": "10..24"},
    "n_components": {"type": "int", "default": "3 in witness draws; 2..5 otherwise", "valid": "2..5"},
    "palette_order": {"type": "str", "default": "unsorted in witness draws; either otherwise", "valid": "sorted|unsorted"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("witness", "broad")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    return "witness" if sample_index % 2 == 0 else "broad"


def _axis(ctx, name, domain, preferred):
    # Defaults are a curriculum choice, not a narrower legal override domain.
    choices = domain if ctx.overrides.get(name) is not None else preferred
    return ctx.draw_choice(name, choices)


def _grow(rng, size, height, width):
    """Grow an exact-size connected shape within a finite rectangle."""
    if not 1 <= size <= height * width:
        raise ValueError("shape size exceeds its constructive rectangle")
    cells = {(rng.randrange(height), rng.randrange(width))}
    frontier = set()
    while len(cells) < size:
        for r, c in cells:
            frontier.update((r + dr, c + dc) for dr, dc in _CARDINAL
                            if 0 <= r + dr < height and 0 <= c + dc < width)
        frontier.difference_update(cells)
        cells.add(rng.choice(sorted(frontier)))
    top, left = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _fits(grid, cells, top, left):
    h, w = len(grid), len(grid[0])
    for dr, dc in cells:
        r, c = top + dr, left + dc
        if not (2 <= r < h and 0 <= c < w) or grid[r][c] != 0:
            return False
        if any(0 <= r + rr < h and 0 <= c + cc < w and grid[r + rr][c + cc] != 0
               for rr, cc in _CARDINAL):
            return False
    return True


def _stamp(grid, cells, top, left):
    for r, c in cells:
        grid[top + r][left + c] = 8


def _witness_plan(rng, n):
    # A size-4 square ABOVE a size-3 L: equal bbox/height/width, opposite size
    # order. They touch diagonally, but never cardinally. Reflect left/right.
    omitted = rng.choice(((0, 1), (1, 0), (1, 1)))
    ell = [(r + 2, c + 2) for r in range(2) for c in range(2) if (r, c) != omitted]
    group = [(0, 0), (0, 1), (1, 0), (1, 1)] + ell
    if rng.randrange(2):
        group = [(r, 3 - c) for r, c in group]
    plan = [(tuple(group), 2, 0)]
    # The 8x10 minimum canvas fits ALL supported counts. For n=3 the sizes
    # 1,3,4 also refute treating absolute pixel counts as palette indices.
    for size, pos in zip((1, 5, 6)[:n - 2], ((7, 0), (2, 6), (5, 6))):
        plan.append((_grow(rng, size, 2, 3), *pos))
    return plan


def _broad_plan(rng, h, w, n):
    # Six disjoint constructive rectangles. After subtracting blank gutters,
    # the minimum canvas gives heights (2,3), widths (2,3,3). Random free
    # placement below normally discards these region positions, not the shapes.
    body = h - 2
    heights = ((body - 1) // 2, body - 1 - (body - 1) // 2)
    base, rem = divmod(w - 2, 3)
    widths = [base + (j >= 3 - rem) for j in range(3)]
    boxes, top = [], 2
    for ph in heights:
        left = 0
        for pw in widths:
            boxes.append((top, left, ph, pw))
            left += pw + 1
        top += ph + 1
    chosen = rng.sample(boxes, n)
    rng.shuffle(chosen)  # randomize equal-capacity ordering
    chosen.sort(key=lambda b: b[2] * b[3])
    capacities = [min(14, ph * pw) for _, _, ph, pw in chosen]
    plan, previous = [], 0
    for i, (top, left, ph, pw) in enumerate(chosen):
        # Reserve enough distinct sizes for every remaining rectangle. This is
        # constructive even for n=5 at 8x10; no truncated growth or retry loss.
        upper = min(capacities[j] - (j - i) for j in range(i, n))
        size = rng.randint(previous + 1, upper)
        cells = _grow(rng, size, ph, pw)
        sh, sw = max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
        plan.append((cells, top + rng.randrange(ph - sh + 1), left + rng.randrange(pw - sw + 1)))
        previous = size
    return plan


def _layout(rng, h, w, fallback):
    for _ in range(5):
        grid = full_grid(h, w, 0)
        # Largest bounding rectangles first reduces needless placement retries.
        items = sorted(fallback, key=lambda item: -len(item[0]))
        for cells, _, _ in items:
            sh, sw = max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
            for _ in range(40):
                top, left = rng.randint(2, h - sh), rng.randint(0, w - sw)
                if _fits(grid, cells, top, left):
                    _stamp(grid, cells, top, left)
                    break
            else:
                break
        else:
            return grid
    grid = full_grid(h, w, 0)
    for cells, top, left in fallback:
        if not _fits(grid, cells, top, left):
            raise RuntimeError("constructive layout invariant failed; refusing an incomplete grid")
        _stamp(grid, cells, top, left)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or removed override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    for name in ("grid_h", "grid_w", "n_components"):
        if overrides.get(name) is not None and type(overrides[name]) is not int:
            raise ValueError(f"{name} must be an integer, not {type(overrides[name]).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    witness = schedule_profile(seed, sample_index, difficulty) == "witness"
    anchor_h, anchor_w = ctx.draw_rng("canonical_profile").choice(((8, 10), (9, 11)))
    h = _axis(ctx, "grid_h", tuple(range(8, 25)), (anchor_h,) if witness else tuple(range(8, 25)))
    w = _axis(ctx, "grid_w", tuple(range(10, 25)), (anchor_w,) if witness else tuple(range(10, 25)))
    favored = (2, 3) if difficulty == "easy" else ((4, 5) if difficulty == "hard" else ())
    n = _axis(ctx, "n_components", (2, 3, 4, 5), (3,) if witness else (2, 3, 4, 5) + favored)
    order = _axis(ctx, "palette_order", ("sorted", "unsorted"), ("unsorted",) if witness else ("sorted", "unsorted"))
    rng = ctx.draw_rng("layout")
    fallback = _witness_plan(rng, n) if witness else _broad_plan(rng, h, w, n)
    grid = _layout(rng, h, w, fallback)
    palette_rng = ctx.draw_rng("palette")
    palette = sorted(palette_rng.sample(_COLORS, n))
    if order == "unsorted":
        palette_rng.shuffle(palette)
        if palette == sorted(palette):
            palette[0], palette[1] = palette[1], palette[0]
    columns = sorted(ctx.draw_rng("header_columns").sample(range(w), n))
    for column, color in zip(columns, palette):
        grid[0][column] = color
    errors = self_check(grid)
    if errors:
        raise RuntimeError("input construction failed: " + "; ".join(errors))
    return grid


def _components(grid, diagonals=False):
    unseen = {(r, c) for r in range(1, len(grid)) for c, v in enumerate(grid[r]) if v == 8}
    neighbors = _CARDINAL + (((-1, -1), (-1, 1), (1, -1), (1, 1)) if diagonals else ())
    groups = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack, group = [start], {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in neighbors:
                cell = r + dr, c + dc
                if cell in unseen:
                    unseen.remove(cell); group.add(cell); stack.append(cell)
        groups.append(group)
    return groups


def _box(group):
    return (min(r for r, _ in group), min(c for _, c in group),
            max(r for r, _ in group), max(c for _, c in group))


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9 (not booleans)"]
    errors = []
    palette = [v for v in grid[0] if v]
    if not 2 <= len(palette) <= 5 or len(set(palette)) != len(palette) or 8 in palette:
        errors.append("expected 2..5 distinct nonzero palette entries excluding 8")
    if len(grid) < 3 or any(grid[1]):
        errors.append("row 1 must be a blank separator above the body")
    if any(v not in (0, 8) for row in grid[1:] for v in row):
        errors.append("body may contain only background 0 and placeholder 8")
    groups = _components(grid)
    if len(groups) != len(palette):
        errors.append(f"palette/component cardinality mismatch: {len(palette)} versus {len(groups)}")
    if len({len(g) for g in groups}) != len(groups):
        errors.append("body component sizes must be distinct; tie semantics are outside this sampler")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    palette = [v for v in grid[0] if v]
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_components": len(_components(grid)),
            "palette_order": "sorted" if palette == sorted(palette) else "unsorted"}


# Pure rival predictors below are diagnostic contracts, NEVER label authority
# and NEVER used by generate(). The shared tools compare them with Racket.
def _rank_key(group, mode):
    r0, c0, r1, c1 = _box(group)
    measure = {"size": len(group), "row_major": 0,
               "bbox_area": (r1-r0+1)*(c1-c0+1),
               "height": r1-r0+1, "width": c1-c0+1}[mode]
    return measure, (r0, c0, r1, c1)


def _rival(grid, mode):
    palette = [v for v in grid[0] if v]
    groups = _components(grid, diagonals=(mode == "diagonal_merge"))
    order = mode if mode in ("row_major", "bbox_area", "height", "width") else "size"
    groups.sort(key=lambda group: _rank_key(group, order))
    if mode == "numeric_palette":
        palette.sort()
    out = [list(row) for row in grid]
    for index, group in enumerate(groups):
        color_index = min(len(group)-1, len(palette)-1) if mode == "absolute_size" else index
        if color_index < len(palette):
            for r, c in group:
                out[r][c] = palette[color_index]
    return out


def _row_major(grid): return _rival(grid, "row_major")
def _bbox_area(grid): return _rival(grid, "bbox_area")
def _height_rank(grid): return _rival(grid, "height")
def _width_rank(grid): return _rival(grid, "width")
def _numeric_palette(grid): return _rival(grid, "numeric_palette")
def _absolute_size(grid): return _rival(grid, "absolute_size")
def _diagonal_merge(grid): return _rival(grid, "diagonal_merge")


def _order_differs(grid, mode):
    groups = _components(grid)
    return sorted(groups, key=lambda x: _rank_key(x, "size")) != sorted(groups, key=lambda x: _rank_key(x, mode))


def _spatial_witness(grid): return _order_differs(grid, "row_major")
def _area_witness(grid): return _order_differs(grid, "bbox_area")
def _height_witness(grid): return _order_differs(grid, "height")
def _width_witness(grid): return _order_differs(grid, "width")
def _palette_witness(grid):
    palette = [v for v in grid[0] if v]
    return palette != sorted(palette)
def _absolute_witness(grid):
    sizes = sorted(len(group) for group in _components(grid))
    return any(min(size-1, len(sizes)-1) != rank for rank, size in enumerate(sizes))
def _diagonal_witness(grid): return len(_components(grid)) != len(_components(grid, diagonals=True))


SEMANTIC_RIVALS = {
    "row_major": _row_major, "bbox_area": _bbox_area,
    "height_rank": _height_rank, "width_rank": _width_rank,
    "numeric_palette": _numeric_palette, "absolute_size": _absolute_size,
    "diagonal_merge": _diagonal_merge,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "spatial_inversion": _spatial_witness, "area_inversion": _area_witness,
    "height_inversion": _height_witness, "width_inversion": _width_witness,
    "nonmonotone_palette": _palette_witness, "absolute_count_trap": _absolute_witness,
    "diagonal_contact": _diagonal_witness,
}
WITNESS_RIVALS = {
    "spatial_inversion": ["row_major"], "area_inversion": ["bbox_area"],
    "height_inversion": ["height_rank"], "width_inversion": ["width_rank"],
    "nonmonotone_palette": ["numeric_palette"], "absolute_count_trap": ["absolute_size"],
    "diagonal_contact": ["diagonal_merge"],
}
