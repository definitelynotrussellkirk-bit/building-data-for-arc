"""Generator for arc_puzzle_bank_21_set4_d:medium_d01 — move object to marker's corner.

Rule: ONE MARKER cell with colour in {1,2,3,4} encodes a destination corner
(1=top-left, 2=top-right, 3=bottom-left, 4=bottom-right). ONE OBJECT (a
connected polyomino in a colour from {5..9}) is cropped to its bbox and
pasted into the marker-indicated corner of an otherwise-empty output grid.
The marker itself is dropped.

Combinatorial axes: grid size, marker colour (= corner branch), object shape,
object colour, object position.
Degenerates: no_marker, no_object, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bcdbe9c5f1b4"
# 2.0.0: COMPLETE REWRITE. Previous generator was a WRONG-TASK stub (placed
# 3-4 random motifs in colours 2..9 with a "vertical pack" docstring). The
# real rule is: a single marker in {1,2,3,4} picks a corner, and a single
# object (colour 5..9) is moved there. Now generates exactly that, varying
# the marker (all 4 corner branches), the object shape/colour/position.
VERSION = "2.0.1"  # add self_check
TASK_ID = "bcdbe9c5f1b4"

SUMMARY = (
    "0-bg grid with ONE marker cell (colour 1=TL/2=TR/3=BL/4=BR) and ONE "
    "connected object (colour 5..9). Rule: crop the object and paste it into "
    "the marker-indicated corner of an empty grid; the marker is dropped."
)

INVARIANTS = [
    "background is 0",
    "exactly one marker cell with colour in {1,2,3,4}",
    "exactly one connected object in a colour from {5..9}",
    "marker and object do not touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_object", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "marker":         {"type": "int", "default": "rng 1..4 (corner)", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "obj_size":       {"type": "int", "default": "rng 3..6", "valid": "2..8"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "marker_corner_plus_object",
                       "valid": "marker_corner_plus_object"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _poly(rng, size, max_dim=4):
    cells = {(0, 0)}; frontier = [(0, 0)]
    while len(cells) < size and frontier:
        r, c = rng.choice(frontier)
        opts = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
        rng.shuffle(opts)
        grown = False
        for nr, nc in opts:
            if (nr, nc) in cells:
                continue
            rs = [x for x, _ in cells] + [nr]; cs = [y for _, y in cells] + [nc]
            if max(rs) - min(rs) + 1 > max_dim or max(cs) - min(cs) + 1 > max_dim:
                continue
            cells.add((nr, nc)); frontier.append((nr, nc)); grown = True
            break
        if not grown:
            frontier.remove((r, c))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; one marker in {1,2,3,4}; one object in {5..9}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (1, 2, 3, 4)]
    objects = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in range(5, 10)]
    if not markers and not objects:
        return errs  # degenerate
    if not markers:
        return errs  # degenerate no_marker
    if not objects:
        errs.append("no object cells (colors 5-9) found")
    if len(markers) > 1:
        errs.append(f"expected exactly 1 marker cell, got {len(markers)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        obj_size = ctx.draw_int("obj_size", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 12, 16)
        obj_size = ctx.draw_int("obj_size", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 9, 13)
        obj_size = ctx.draw_int("obj_size", 3, 6)
    marker = ctx.draw_int("marker", 1, 4)
    rng = ctx.draw_rng("layout")

    for _ in range(60):
        g = full_grid(h, w, 0)
        shape = _poly(rng, obj_size)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if sh > h - 1 or sw > w - 1:
            continue
        obj_color = rng.choice([5, 6, 7, 8, 9])
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        cells = {(r0 + dr, c0 + dc) for dr, dc in shape}
        for r, c in cells:
            g[r][c] = obj_color
        # Marker: a single cell not adjacent to the object (8-neighbourhood).
        forbidden = set(cells)
        for r, c in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    forbidden.add((r + dr, c + dc))
        free = [(r, c) for r in range(h) for c in range(w)
                if (r, c) not in forbidden]
        if not free:
            continue
        mr, mc = rng.choice(free)
        g[mr][mc] = marker
        return g
    # fallback
    g = full_grid(h, w, 0)
    g[0][0] = marker
    g[h - 1][w - 1] = 5
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # object but no marker -> corner is undefined (rule reads garbage)
        for r, c in [(3, 4), (3, 5), (4, 5)]:
            g[r][c] = 7
        return g
    if name == "no_object":
        # marker but no object -> empty output
        g[0][0] = 2
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 7
        return g
    return g
