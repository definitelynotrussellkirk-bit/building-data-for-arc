"""Generator for arc_additional_puzzles_21_set5:M30 — wrap motif crop in frame color.

Rule: cell (0,0) supplies the new frame color around the cropped nonzero
motif.

Combinatorial axes (8): grid_h, grid_w, palette_kind, frame_color,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame_color, no_motif, motif_touches_command.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e96f42608654"
VERSION = "2.0.0"  # was a FIXED 3x2 motif -> output ALWAYS 5x4 (shape-locked-out). Output dims = motif bbox + 2, so vary the motif bbox (H,W incl non-square, with internal zeros) -> varied output dims; vary color count
TASK_ID = "e96f42608654"
SUMMARY = (
    "0-bg grid; cell (0,0) holds a FRAME color; elsewhere a single patterned "
    "motif block (random H x W bbox spanning all four sides, with internal "
    "zeros, in 2-4 colors). Rule: crop the bbox of all nonzero cells except "
    "(0,0) and wrap it in a 1-cell frame of (0,0)'s color. Output dims = "
    "(H+2) x (W+2); motif bbox, colors, position and grid size all vary."
)

INVARIANTS = [
    "the frame color is stored only at (0,0)",
    "exactly one motif block, offset away from (0,0)",
    "the motif spans its full H x W bbox (cells touch all four sides)",
    "motif colors exclude 0 and the frame color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame_color", "no_motif", "motif_touches_command")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "derived", "valid": "6..20"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "6..20"},
    "motif_h":        {"type": "int", "default": "rng 3..8 by diff", "valid": "2..10"},
    "motif_w":        {"type": "int", "default": "rng 3..8 by diff", "valid": "2..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "frame_color":    {"type": "color", "default": "rng nonzero", "valid": "1..9"},
    "n_colors":       {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _motif(rng, H, W, palette):
    """A connected patterned block spanning the full H x W bbox.

    The previous density-sampled mask often split into multiple disconnected
    islands, violating the generator's "exactly one motif block" invariant.
    Build a connected cross/backbone first, then add adjacent cells at random.
    """
    cells = set()
    pivot_r = rng.randint(0, H - 1)
    pivot_c = rng.randint(0, W - 1)
    for r in range(H):
        cells.add((r, pivot_c))
    for c in range(W):
        cells.add((pivot_r, c))

    target_density = rng.uniform(0.45, 0.7)
    target = max(len(cells), int(round(H * W * target_density)))
    frontier = [(r, c) for r in range(H) for c in range(W) if (r, c) not in cells]
    rng.shuffle(frontier)
    changed = True
    while len(cells) < target and changed:
        changed = False
        for r, c in list(frontier):
            if len(cells) >= target:
                break
            if any((r + dr, c + dc) in cells for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                if rng.random() < 0.55:
                    cells.add((r, c))
                    frontier.remove((r, c))
                    changed = True
    cell = [[0] * W for _ in range(H)]
    for r, c in cells:
        cell[r][c] = rng.choice(palette)
    return cell


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        mh_lo, mh_hi = 3, 4
    elif difficulty == "hard":
        mh_lo, mh_hi = 4, 8
    else:
        mh_lo, mh_hi = 3, 6
    H = int(overrides.get("motif_h", ctx.draw_int("motif_h", mh_lo, mh_hi)))
    W = int(overrides.get("motif_w", ctx.draw_int("motif_w", mh_lo, mh_hi)))
    H = max(2, min(10, H)); W = max(2, min(10, W))
    n_colors = int(overrides.get("n_colors", ctx.draw_int("n_colors", 2, 4)))
    frame = ctx.draw_color("frame_color", exclude=[0])
    palette = list(ctx.draw_distinct_colors("colors", n=max(2, n_colors),
                                            exclude=[0, frame]))
    rng = ctx.draw_rng("layout")
    # grid sized around the motif with random margins (input shape varies too)
    pad_top = ctx.draw_int("pad_top", 2, 4)
    pad_bot = ctx.draw_int("pad_bot", 1, 3)
    pad_left = ctx.draw_int("pad_left", 2, 4)
    pad_right = ctx.draw_int("pad_right", 1, 3)
    h = pad_top + H + pad_bot
    w = pad_left + W + pad_right
    g = full_grid(h, w, 0)
    g[0][0] = frame
    top = rng.randint(2, h - H - 1) if h - H - 1 >= 2 else 2
    left = rng.randint(2, w - W - 1) if w - W - 1 >= 2 else 2
    block = _motif(rng, H, W, palette)
    for dr in range(H):
        for dc in range(W):
            if block[dr][dc] != 0:
                g[top + dr][left + dc] = block[dr][dc]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_frame_color":
        # (0,0) is 0 → no frame color provided, rule has no wrapper color
        g[3][3] = 4; g[3][4] = 6; g[4][4] = 6; g[5][3] = 7
        return g
    if name == "no_motif":
        # frame color present but no motif → rule has nothing to wrap
        g[0][0] = 4
        return g
    if name == "motif_touches_command":
        # motif extends to (0,0) → command cell is also part of motif, wrapping logic ambiguous
        g[0][0] = 4
        g[0][1] = 6; g[1][0] = 6; g[1][1] = 7
        return g
    return g



def _motif_components(grid, frame):
    h, w = len(grid), len(grid[0])
    cells = {(r, c) for r in range(h) for c in range(w)
             if grid[r][c] != 0 and (r, c) != (0, 0)}
    seen = set()
    comps = []
    for cell in sorted(cells):
        if cell in seen:
            continue
        stack = [cell]
        seen.add(cell)
        comp = []
        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cells and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    msgs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    frame = grid[0][0]
    if frame == 0:
        msgs.append("command frame color at (0,0) is zero")
    frame_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == frame]
    if frame != 0 and frame_cells != [(0, 0)]:
        msgs.append("frame color appears outside the command cell")
    motif = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0 and (r, c) != (0, 0)]
    if not motif:
        return msgs + ["no motif cells"]
    comps = _motif_components(grid, frame)
    if len(comps) != 1:
        msgs.append(f"motif is split into {len(comps)} connected components")
    rs = [r for r, _ in motif]
    cs = [c for _, c in motif]
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    if r1 < 2 or c1 < 2:
        msgs.append("motif touches or nearly touches the command cell")
    if not any(grid[r1][c] != 0 for c in range(c1, c2 + 1)):
        msgs.append("motif bbox top side is empty")
    if not any(grid[r2][c] != 0 for c in range(c1, c2 + 1)):
        msgs.append("motif bbox bottom side is empty")
    if not any(grid[r][c1] != 0 for r in range(r1, r2 + 1)):
        msgs.append("motif bbox left side is empty")
    if not any(grid[r][c2] != 0 for r in range(r1, r2 + 1)):
        msgs.append("motif bbox right side is empty")
    if any(grid[r][c] == frame for r, c in motif):
        msgs.append("motif uses the frame color")
    return msgs
