"""Generator for 93b4f4b3.

Rule: shape patterns on the right fill matching holes in a frame on the
left.

Combinatorial axes (8): grid_h/w, frame_color, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_holes, no_shapes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "98e5564fbf8a"
VERSION = "3.0.1"  # in_sh=out_sh=1: fully fixed 12x12 + fixed left width + 2 fixed holes/shapes -> output (= left panel) always 12x6. Rule matches each left hole to a right shape by normalized pattern and fills it with that color; output = left panel cropped. Vary grid h, left width fw, hole count (2-3) and random distinct matched shapes -> output dims (h x fw) and content vary.
TASK_ID = "98e5564fbf8a"
SUMMARY = (
    "Two-panel grid: LEFT panel (cols 0..fw-1) is mostly filled with "
    "frame color (5 or 8) with 2-3 'hole' regions (small 0-shapes "
    "punched out). RIGHT panel (cols fw+1..w-1) has 2-3 small shapes "
    "in distinct non-frame colors, separated by zero rows. Each hole "
    "shape (normalized) matches exactly one right shape. Rule: detect "
    "hole sections in left frame. For each hole, find right shape "
    "with matching normalized pattern. Fill the hole with that "
    "shape's color. Output is left panel only (cropped)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "left panel is filled with frame color (5 or 8) except for hole regions",
    "right panel has shapes in distinct non-frame colors",
    "each hole's shape matches exactly one right shape (normalized pattern)",
    "zero-column separates panels",
]

FRAME_KINDS = ("F5", "F8")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_holes", "no_shapes", "full_grid")
HELPFUL_TEXTURES = FRAME_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "12", "valid": "12"},
    "grid_w":         {"type": "int", "default": "12", "valid": "12"},
    "frame_color":    {"type": "choice", "default": "rng helpful",
                       "valid": "5|8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for frame_color",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint(g, cells, color):
    for r, c in cells:
        g[r][c] = color


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return tuple(sorted((r - rmin, c - cmin) for r, c in cells))


def _distinct_shapes(rng, k, max_h, max_w):
    """k distinct normalized polyominoes fitting within max_h x max_w."""
    shapes = []; seen = set()
    for _ in range(400):
        if len(shapes) >= k:
            break
        s = _rand_poly(rng, rng.randint(2, 5))
        if max(r for r, _ in s) + 1 > max_h or max(c for _, c in s) + 1 > max_w:
            continue
        if s in seen:
            continue
        seen.add(s); shapes.append(s)
    return shapes


def _bands(rng, h, heights):
    """Top positions for blocks of given heights, >=1 separating row between
    them and clear of grid edges, slack distributed randomly. None if no fit."""
    k = len(heights)
    used = sum(heights) + (k - 1)
    if used > h:
        return None
    slack = h - used
    gaps = [0] * (k + 1)
    for _ in range(slack):
        gaps[rng.randint(0, k)] += 1
    tops = []; r = gaps[0]
    for i, hh in enumerate(heights):
        tops.append(r); r += hh + 1 + gaps[i + 1]
    return tops


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: a full all-zero column (separator) exists in the interior."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    interior_zero_cols = [c for c in range(1, w - 1) if all(grid[r][c] == 0 for r in range(h))]
    if not interior_zero_cols:
        return ["no interior all-zero separator column found"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    tx = overrides.get("texture")
    if tx in FRAME_KINDS:
        frame_color = int(tx[1])
    else:
        frame_color = ctx.draw_choice("frame_color", [5, 8])
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11); fw = ctx.draw_int("left_w", 4, 5); k = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16); fw = ctx.draw_int("left_w", 5, 7)
        k = ctx.draw_int("n_holes", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 11, 14); fw = ctx.draw_int("left_w", 4, 6)
        k = ctx.draw_int("n_holes", 2, 3)
    rw = ctx.draw_int("right_w", 4, 6)
    w = fw + 1 + rw
    # k distinct hole shapes fitting both panels; retry the whole layout until
    # the row bands fit on each side.
    for _ in range(40):
        shapes = _distinct_shapes(rng, k, min(3, h // 3), min(fw - 1, rw - 1))
        if len(shapes) < k:
            continue
        heights = [max(r for r, _ in s) + 1 for s in shapes]
        left_tops = _bands(rng, h, heights)
        order = list(range(k)); rng.shuffle(order)
        right_heights = [heights[i] for i in order]
        right_tops = _bands(rng, h, right_heights)
        if left_tops is None or right_tops is None:
            continue
        colors = rng.sample([c for c in range(1, 10) if c not in (0, frame_color)], k)
        g = full_grid(h, w, 0)
        for r in range(h):
            for c in range(fw):
                g[r][c] = frame_color
        # left: punch each hole (0-cells) into the frame
        for s, top in zip(shapes, left_tops):
            sw = max(c for _, c in s) + 1
            c0 = rng.randint(0, fw - sw)
            _paint(g, [(top + dr, c0 + dc) for dr, dc in s], 0)
        # right: place the same shapes (shuffled order) in distinct colors
        for slot, top in zip(order, right_tops):
            s = shapes[slot]; sw = max(c for _, c in s) + 1
            c0 = rng.randint(0, rw - sw)
            _paint(g, [(top + dr, fw + 1 + c0 + dc) for dr, dc in s], colors[slot])
        return g
    raise ValueError("could not realize two-panel hole-fill layout")



def _norm_cells(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _components_where(h, w, pred):
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if not pred(r, c) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and pred(nr, nc):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for two-panel hole-to-shape matching inputs."""
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    sep = None
    frame_color = None
    for c in range(1, w - 1):
        if not all(grid[r][c] == 0 for r in range(h)):
            continue
        left_nonzero = {grid[r][cc] for r in range(h) for cc in range(c) if grid[r][cc] != 0}
        if len(left_nonzero) != 1:
            continue
        fc = next(iter(left_nonzero))
        if fc not in (5, 8):
            continue
        right_nonzero = {grid[r][cc] for r in range(h) for cc in range(c + 1, w) if grid[r][cc] != 0}
        if right_nonzero and fc not in right_nonzero:
            sep, frame_color = c, fc
            break
    if sep is None:
        return ["could not find a zero separator with a single-color frame on the left"]
    holes = _components_where(h, sep, lambda r, c: grid[r][c] == 0)
    shapes = _components_where(h, w - sep - 1, lambda r, c: grid[r][sep + 1 + c] not in (0, frame_color))
    if not (2 <= len(holes) <= 3):
        errs.append(f"expected 2-3 left hole components, found {len(holes)}")
    if len(shapes) != len(holes):
        errs.append(f"right shape count {len(shapes)} does not match hole count {len(holes)}")
    shape_colors = [grid[r][sep + 1 + c] for comp in shapes for r, c in comp]
    comp_colors = [{grid[r][sep + 1 + c] for r, c in comp} for comp in shapes]
    if any(len(colors) != 1 for colors in comp_colors):
        errs.append("each right shape component should be a single color")
    if len({next(iter(colors)) for colors in comp_colors if colors}) != len(comp_colors):
        errs.append("right shape colors should be distinct")
    hole_patterns = sorted(_norm_cells(comp) for comp in holes)
    shape_patterns = sorted(_norm_cells(comp) for comp in shapes)
    if hole_patterns != shape_patterns:
        errs.append("normalized left hole patterns do not exactly match right shape patterns")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_holes":
        for r in range(12):
            for c in range(5):
                g[r][c] = 5
        return g
    if name == "no_shapes":
        for r in range(12):
            for c in range(5):
                g[r][c] = 5
        for r, c in [(2, 1), (2, 2), (3, 1), (7, 2), (8, 1), (8, 2)]:
            g[r][c] = 0
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 5
        return g
    return g
