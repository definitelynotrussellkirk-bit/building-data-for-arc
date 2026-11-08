"""Generator for arc_additional_puzzles_21_set17_bundle:M117 — pick object by cmd at (0,0).

Rule: cell (0,0) holds a command; the rest of the grid has objects.
Pick one object per command:
  1: smallest size; 2: largest size; 3: widest bbox; 4: tallest bbox
Output is the bbox crop of the chosen object.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_command (cell (0,0) is bg → rule has no command);
no_objects (command set but no objects → selector has no
candidates); tied_dimensions (two objects share size, height, and
width → selector ambiguous for some commands).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "feeea4ae7af8"
VERSION = "3.1.0"  # add executable command/object selector invariants
TASK_ID = "feeea4ae7af8"
SUMMARY = (
    "0-bg grid (size varies). Cell (0, 0) holds a COMMAND "
    "in {1, 2, 3, 4}. Rest of grid has 2-4 4-connected random "
    "polyomino objects in distinct colors, with PAIRWISE-DISTINCT "
    "size, bbox-width, and bbox-height (so every command is "
    "unambiguous). Rule: clear (0, 0) "
    "to 0. Compute objects of the cleared grid. Pick one "
    "object per command — 1: smallest size, 2: largest size, "
    "3: widest bbox, 4: tallest bbox; tiebreakers go to "
    "top-most then left-most then smallest color. Output = "
    "bbox crop of the chosen object (paint its cells in its "
    "color over an empty grid sized to the bbox)."
)

INVARIANTS = [
    "background is 0",
    "(0,0) holds a command in {1, 2, 3, 4}",
    "2-4 4-connected non-bg objects with PAIRWISE-DISTINCT size, bbox_w, and bbox_h",
    "objects don't touch each other or (0,0)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_command", "no_objects", "tied_dimensions")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "9-11 easy / 10-13 med / 12-14 hard", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "11-14 easy / 12-16 med / 14-18 hard", "valid": "10..18"},
    "n_objects":         {"type": "int", "default": "2 easy / 3 med / 4 hard", "valid": "2..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "= n_objects", "valid": "2..4"},
    "position_bias":     {"type": "str", "default": "cmd_at_origin_with_scattered_objects",
                          "valid": "cmd_at_origin_with_scattered_objects"},
    "n_distinct_colors": {"type": "int", "default": "= n_objects", "valid": "2..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

def _rand_poly(rng, size):
    """Random 4-connected polyomino of `size` cells, normalized to origin."""
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    cells = [(0, 0)]
    guard = 0
    while len(cells) < size and guard < 200:
        guard += 1
        gr, gc = rng.choice(cells)
        for dr, dc in rng.sample(dirs, 4):
            p = (gr + dr, gc + dc)
            if p not in cells:
                cells.append(p)
                break
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]



def _components_excluding_command(grid):
    h, w = len(grid), len(grid[0])
    seen = {(0, 0)}
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for command-at-origin object selection."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    cmd = grid[0][0]
    if cmd not in (1, 2, 3, 4):
        errs.append(f"command cell must be in {{1,2,3,4}}, got {cmd}")
    comps = _components_excluding_command(grid)
    if not (2 <= len(comps) <= 4):
        errs.append(f"expected 2..4 selectable objects, got {len(comps)}")
    sizes, widths, heights, colors = [], [], [], []
    boxes = []
    for color, cells in comps:
        colors.append(color)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        sizes.append(len(cells)); heights.append(r1 - r0 + 1); widths.append(c1 - c0 + 1)
        boxes.append((r0, c0, r1, c1))
    for name, vals in (("size", sizes), ("bbox width", widths), ("bbox height", heights)):
        if len(vals) != len(set(vals)):
            errs.append(f"objects must have pairwise-distinct {name}s, got {vals}")
    if len(colors) != len(set(colors)):
        errs.append("objects should have distinct colors")
    for i, a in enumerate(boxes):
        ar0, ac0, ar1, ac1 = a
        for b in boxes[i + 1:]:
            br0, bc0, br1, bc1 = b
            if not (ar1 + 1 < br0 or br1 + 1 < ar0 or ac1 + 1 < bc0 or bc1 + 1 < ac0):
                errs.append("object bounding boxes must be separated by at least one background row/col")
    return errs

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 14)
        n_obj, smax = 2, 6
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 18)
        n_obj, smax = 4, 9
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
        n_obj, smax = 3, 8
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cmd = rng.choice([1, 2, 3, 4])
    g[0][0] = cmd

    # Random polyomino objects with PAIRWISE-DISTINCT size AND width AND height,
    # so EVERY command (smallest/largest size, widest, tallest) is unambiguous
    # (the old fixed 6-shape bank both capped output diversity and let two shapes
    # share a size). Each must fit the grid interior (rows/cols >= 1).
    shapes = []
    sizes, widths, heights = set(), set(), set()
    attempts = 0
    while len(shapes) < n_obj and attempts < 600:
        attempts += 1
        sz = rng.randint(2, smax)
        cells = _rand_poly(rng, sz)
        sh = max(r for r, _ in cells) + 1
        sw = max(c for _, c in cells) + 1
        if sh > h - 1 or sw > w - 1:
            continue
        if sz in sizes or sw in widths or sh in heights:
            continue
        shapes.append((cells, sh, sw)); sizes.add(sz); widths.add(sw); heights.add(sh)
    palette = list(random_palette(rng, max(2, len(shapes))))

    placed = [(0, 0, 0, 0)]

    def try_scatter(cells, sh, sw, color):
        for _ in range(120):
            r0 = rng.randint(1, h - sh)
            c0 = rng.randint(1, w - sw)
            bb_pad = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
            if any(bbox_overlaps(bb_pad, p) for p in placed):
                continue
            paint_at(g, r0, c0, cells, color)
            placed.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
            return True
        return False

    if not all(try_scatter(c, sh, sw, col)
               for (c, sh, sw), col in zip(shapes, palette)):
        # row-pack fallback: lay objects left-to-right on row 1 (guaranteed by sizing).
        for r in range(h):
            for c in range(w):
                if (r, c) != (0, 0):
                    g[r][c] = 0
        left = 1
        for (cells, sh, sw), col in zip(shapes, palette):
            if left + sw > w:
                break
            paint_at(g, 1, left, cells, col)
            left += sw + 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_command":
        # Cell (0,0) is bg — rule has no command.
        for r in range(2):
            for c in range(2):
                g[3 + r][3 + c] = 4
        for r in range(2):
            for c in range(3):
                g[6 + r][8 + c] = 5
        return g
    if name == "no_objects":
        # Command set but no objects.
        g[0][0] = 1
        return g
    if name == "tied_dimensions":
        # Two objects with same size, h, w — selector ambiguous.
        g[0][0] = 1
        for r in range(2):
            for c in range(2):
                g[3 + r][3 + c] = 4
        for r in range(2):
            for c in range(2):
                g[6 + r][8 + c] = 5
        return g
    return g
