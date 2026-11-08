"""Generator for 2697da3f.

Rule: a single-color motif is stamped with rotations and reflection
into a larger square.

Combinatorial axes (8): motif, color, palette_kind, grid_size,
position_bias, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_motif, full_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d1559d680a5f"
VERSION = "1.3.0"  # keep random default diversity, but honor explicit motif/texture overrides
TASK_ID = "d1559d680a5f"
SUMMARY = "Single-color motif stamped with rotations and reflection into a larger square."

INVARIANTS = [
    "all nonzero cells share one color",
    "the source motif has a compact bounding box",
    "the output size is determined by the motif bounding box",
    "the rule stamps the motif, both quarter rotations, and a left-right reflection",
]

MOTIFS = {
    "l": [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
    "t": [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    "stair": [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
    "zig": [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],
}
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_motif", "full_grid", "single_cell")
HELPFUL_TEXTURES = tuple(MOTIFS.keys())

AXES = {
    "motif":          {"type": "str", "default": "rng random_connected; explicit overrides use bank",
                       "valid": "l|t|stair|zig"},
    "color":          {"type": "color", "default": "rng !0",
                       "valid": "1..9"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "warm|cool|broad|primary"},
    "grid_size":      {"type": "int", "default": "rng 6..9", "valid": "5..14"},
    "position_bias":  {"type": "str", "default": "rng",
                       "valid": "centered|rng"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for motif",
                       "valid": "l|t|stair|zig|no_motif|full_grid|single_cell"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    motif_name = (overrides.get("texture") if overrides.get("texture") in MOTIFS else None) or overrides.get("motif")
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, rng)
    color = int(overrides.get("color",
                              rng.choice(pal) if pal else
                              ctx.draw_color("color", exclude={0})))
    if difficulty == "easy":
        s_lo, s_hi = 5, 7
    elif difficulty == "hard":
        s_lo, s_hi = 9, 14
    else:
        s_lo, s_hi = 6, 9
    size = int(overrides.get("grid_size",
                             rng.randint(s_lo, s_hi)))
    size = max(5, min(14, size))
    g = full_grid(size, size, 0)
    if motif_name in MOTIFS:
        # Explicit motif/texture overrides should realize the advertised motif axis.
        cells = list(MOTIFS[motif_name])
    else:
        # Default generation remains random so output size/content stay diverse.
        k = rng.randint(3, min(7, size - 1))
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < k:
            rr, cc = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            if (rr + dr, cc + dc) not in seen:
                cells.append((rr + dr, cc + dc)); seen.add((rr + dr, cc + dc))
        rmin = min(a for a, _ in cells); cmin = min(b for _, b in cells)
        cells = [(a - rmin, b - cmin) for a, b in cells]
    bh = max(a for a, _ in cells) + 1; bw = max(b for _, b in cells) + 1
    r0 = rng.randint(0, max(0, size - bh))
    c0 = rng.randint(0, max(0, size - bw))
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = color
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    size = 7
    g = full_grid(size, size, 0)
    if name == "no_motif":
        return g
    if name == "full_grid":
        for r in range(size):
            for c in range(size):
                g[r][c] = 2
        return g
    if name == "single_cell":
        g[3][3] = 2
        return g
    return g


def _is_connected(cells):
    cells = set(cells)
    if not cells:
        return False
    todo = [next(iter(cells))]
    seen = {todo[0]}
    while todo:
        r, c = todo.pop()
        for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nb in cells and nb not in seen:
                seen.add(nb)
                todo.append(nb)
    return seen == cells


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h != w or not (5 <= h <= 14):
        msgs.append("motif source grid should be square with size 5..14")
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not cells:
        msgs.append("normal instance should contain a motif")
        return msgs
    colors = {v for _, _, v in cells}
    if len(colors) != 1:
        msgs.append("all motif cells should use one nonzero color")
    if not (3 <= len(cells) <= 7):
        msgs.append("random motif should contain 3..7 cells")
    pts = [(r, c) for r, c, _ in cells]
    if not _is_connected(pts):
        msgs.append("motif cells should be 4-connected")
    rs = [r for r, _ in pts]
    cs = [c for _, c in pts]
    bh = max(rs) - min(rs) + 1
    bw = max(cs) - min(cs) + 1
    if bh > h or bw > w:
        msgs.append("motif bbox should fit inside the source grid")
    if bh == h and bw == w:
        msgs.append("motif should not fill the whole source grid")
    return sorted(set(msgs))
