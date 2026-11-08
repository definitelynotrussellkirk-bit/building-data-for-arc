"""Inputs for Component Center Markers (M63); labels remain canonical Racket.

Alternate simple rectangles and component-disambiguating lessons. Repeated
colors and diagonal contact distinguish components from color groups; asymmetric
elbows distinguish inclusive, floor-rounded bbox centers from centroids and
existing-cell selection. See notes.md for the deliberately bounded support.
"""
from __future__ import annotations

from collections import defaultdict

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6e068328f4ce"
TASK_ID = GENERATOR_ID
VERSION = "2.0.1"
RULE_HASH = "c3726fc6c507"
SUMMARY = (
    "Collapse each four-connected same-color component to its floor-rounded "
    "bounding-box center on zero background; repeated colors remain separate."
)
INVARIANTS = [
    "zero is the fixed background; foreground colors are integers 1..9",
    "2..5 four-connected same-color components, each containing at least two cells",
    "requested component and distinct-color counts are realized exactly",
    "generated component bboxes do not overlap; diagonal contact is allowed",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical 9..11 or broad 9..16", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "canonical 9..11 or broad 9..16", "valid": "7..16"},
    "n_blobs": {"type": "int", "default": "2 rectangles or 3..5 varied components", "valid": "2..5"},
    "n_distinct_colors": {"type": "int", "default": "2 or 2..n_blobs-1", "valid": "1..5"},
}
# Strict policy: the only legitimate joint rejection is raised with its axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("rectangles", "component_witnesses")
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, not bool")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


class IncompatibleControls(ValueError):
    incompatible_axes = ("n_blobs", "n_distinct_colors")


def _draw(ctx, name, lo, hi, defaults):
    """Record keyed provenance on both default and exact override paths."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, defaults)


def _controls(ctx, overrides, core, difficulty):
    anchor_h, anchor_w = ctx.draw_rng("canonical_profile").choice(
        ((9, 9), (9, 11), (10, 10), (11, 11))
    )
    favored = (9, 10, 11) if difficulty == "easy" else (
        (13, 14, 15, 16) if difficulty == "hard" else (10, 11, 12)
    )
    broad_sizes = tuple(range(9, 17)) + favored
    h = _draw(ctx, "grid_h", 7, 16, (anchor_h,) if core else broad_sizes)
    w = _draw(ctx, "grid_w", 7, 16, (anchor_w,) if core else broad_sizes)
    requested_colors = overrides.get("n_distinct_colors")
    minimum = max(2, requested_colors or 2)
    favored_counts = (3, 3, 4, 5) if difficulty == "easy" else (
        (3, 4, 5, 5) if difficulty == "hard" else (3, 4, 4, 5)
    )
    defaults = (max(2, minimum),) if core else tuple(
        n for n in favored_counts if n >= minimum
    )
    count = _draw(ctx, "n_blobs", 2, 5, defaults)
    if requested_colors is not None and requested_colors > count:
        raise IncompatibleControls("n_distinct_colors cannot exceed n_blobs")
    default_colors = (min(2, count),) if core else tuple(range(2, count)) or (1,)
    colors = _draw(ctx, "n_distinct_colors", 1, 5, default_colors)
    return h, w, count, colors


def _extra_shape(rng, max_h, max_w):
    """A connected rectangle, frame, bar or elbow fitting a reserved slot."""
    h = rng.randint(1, max_h)
    w = rng.randint(2 if h == 1 else 1, max_w)
    style = rng.choice(("rectangle", "frame", "elbow"))
    return {(r, c) for r in range(h) for c in range(w)
            if style == "rectangle" or r == 0 or c == 0
            or (style == "frame" and (r == h-1 or c == w-1))}


def _layout(ctx, h, w, count, n_colors, core):
    rng = ctx.draw_rng("layout")
    transpose = rng.choice((False, True))
    inner_h, inner_w = (w, h) if transpose else (h, w)
    # Two diagonal slots plus three mutually separated spare slots fit even
    # the 7x7, five-component boundary. No rejection loop can drop a component.
    if core:
        a, b = min(3, (inner_h-2)//2), min(3, inner_w//2)
        first = {(r, c) for r in range(a) for c in range(b)}
        second = set(first)
    else:
        # Default broad grids admit a>=3 and even b>=4. This keeps the empty
        # midpoint and rounding/centroid witnesses while varying their scale.
        a = rng.randint(3 if inner_h >= 9 else 2, (inner_h-3)//2)
        widths = tuple(range(4, inner_w//2+1, 2))
        b = rng.choice(widths) if widths else inner_w//2
        first = {(0, c) for c in range(b)} | {(r, b-1) for r in range(a)}
        second = {(0, c) for c in range(b)} | {(r, 0) for r in range(a)}
    components = [first, {(r+a, c+b) for r, c in second}]
    slots = [(a+1, 0, a-1, b-1), (0, b+1, a-1, b-1),
             (2*a+1, 0, inner_h-2*a-1, 2*b)]
    rng.shuffle(slots)
    for r0, c0, max_h, max_w in slots[:count-2]:
        components.append({(r+r0, c+c0) for r, c in _extra_shape(rng, max_h, max_w)})
    palette = ctx.draw_rng("palette").sample(list(range(1, 10)), n_colors)
    if n_colors < count:
        assigned = [palette[0], palette[0]] + palette[1:]
    else:
        assigned = list(palette)
    while len(assigned) < count:
        assigned.append(rng.choice(palette))
    used_h = 1 + max(r for obj in components for r, _ in obj)
    used_w = 1 + max(c for obj in components for _, c in obj)
    dr, dc = rng.randint(0, inner_h-used_h), rng.randint(0, inner_w-used_w)
    flip_r, flip_c = rng.choice((False, True)), rng.choice((False, True))
    grid = full_grid(h, w, 0)
    for color, cells in zip(assigned, components):
        for r, c in cells:
            r, c = r+dr, c+dc
            if flip_r:
                r = inner_h-1-r
            if flip_c:
                c = inner_w-1-c
            if transpose:
                r, c = c, r
            grid[r][c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unsupported override axes: {sorted(unknown)}; supported: {sorted(AXES)}")
    limits = {"grid_h": (7, 16), "grid_w": (7, 16), "n_blobs": (2, 5),
              "n_distinct_colors": (1, 5)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = limits[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in [{lo}, {hi}]")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = schedule_profile(seed, sample_index, difficulty) == "rectangles"
    return _layout(ctx, *_controls(ctx, overrides, core, difficulty), core)


def _components(grid, diagonal=False):
    h, w = len(grid), len(grid[0])
    seen, components = set(), []
    steps = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if diagonal:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells, stack = [], [(r, c)]
            seen.add((r, c))
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in steps:
                    point = x+dx, y+dy
                    if (0 <= point[0] < h and 0 <= point[1] < w
                            and point not in seen and grid[point[0]][point[1]] == color):
                        seen.add(point)
                        stack.append(point)
            components.append((color, cells))
    return components


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["ARC grids must have at most 30 rows and columns"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer ARC colors 0..9"]
    components = _components(grid)
    errors = []
    if not 2 <= len(components) <= 5:
        errors.append(f"expected 2..5 same-color components, found {len(components)}")
    if any(len(cells) < 2 for _, cells in components):
        errors.append("each component must contain at least two cells")
    return errors


def strict_canonical_like(grid):
    """Task-domain validation; exact canonical shape support is checked separately."""
    return self_check(grid)


def observe_overrides(grid):
    components = _components(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blobs": len(components),
            "n_distinct_colors": len({color for color, _ in components})}


def _diagnostic_markers(grid, mode="bbox"):
    """Diagnostic mirror/rivals only; NEVER used to supply generated labels."""
    components = _components(grid, diagonal=mode == "eight_connected")
    if mode == "per_color":
        merged = defaultdict(list)
        for color, cells in components:
            merged[color].extend(cells)
        components = list(merged.items())
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in components:
        rs, cs = zip(*cells)
        r, c = (min(rs)+max(rs))//2, (min(cs)+max(cs))//2
        if mode == "ceil_midpoint":
            r, c = (min(rs)+max(rs)+1)//2, (min(cs)+max(cs)+1)//2
        elif mode == "floor_centroid":
            r, c = sum(rs)//len(rs), sum(cs)//len(cs)
        elif mode == "rounded_centroid":
            r, c = round(sum(rs)/len(rs)), round(sum(cs)/len(cs))
        if mode != "existing_cells_only" or (r, c) in cells:
            out[r][c] = color
    return out


def _per_color(grid):
    return _diagnostic_markers(grid, "per_color")


def _eight_connected(grid):
    return _diagnostic_markers(grid, "eight_connected")


def _ceil_midpoint(grid):
    return _diagnostic_markers(grid, "ceil_midpoint")


def _floor_centroid(grid):
    return _diagnostic_markers(grid, "floor_centroid")


def _rounded_centroid(grid):
    return _diagnostic_markers(grid, "rounded_centroid")


def _existing_cells_only(grid):
    return _diagnostic_markers(grid, "existing_cells_only")


def _has_repeated_colors(grid):
    components = _components(grid)
    return len(components) > len({color for color, _ in components})


def _has_diagonal_separation(grid):
    return len(_components(grid)) > len(_components(grid, diagonal=True))


def _has_midpoint_witness(grid):
    expected = _diagnostic_markers(grid)
    return all(rival(grid) != expected for rival in
               (_ceil_midpoint, _floor_centroid, _rounded_centroid, _existing_cells_only))


SEMANTIC_RIVALS = {
    "per_color": _per_color, "eight_connected": _eight_connected,
    "ceil_midpoint": _ceil_midpoint, "floor_centroid": _floor_centroid,
    "rounded_centroid": _rounded_centroid, "existing_cells_only": _existing_cells_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "repeated_colors": _has_repeated_colors,
    "diagonal_separation": _has_diagonal_separation,
    "midpoint_disambiguation": _has_midpoint_witness,
}
WITNESS_RIVALS = {
    "repeated_colors": ["per_color"],
    "diagonal_separation": ["eight_connected"],
    "midpoint_disambiguation": ["ceil_midpoint", "floor_centroid", "rounded_centroid", "existing_cells_only"],
}
