"""Generator for c8b7cc0f.

Rule: bbox of 1-cells = frame. Pick first non-{0,1} color C. Count
C-cells strictly inside. Output: 3x3 with first `count` cells = C.

Combinatorial axes (8): grid_h/w, frame_h, frame_w, n_inside, n_outside,
position_bias, palette_kind, anchor_corner.
Degenerates: no_frame, no_inside, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "667f94d9830a"
VERSION = "1.3.0"  # FIX all_background_output: the output is a 3x3 bar-chart of the interior count; n_inside==9 -> count 9 -> a SOLID 3x3 (flagged). The canonical train counts are 1-8 (partial fills). Cap the interior count at 8 so the output is always a partial bar (never solid, and never blank since count>=1). + self_check.
TASK_ID = "667f94d9830a"
SUMMARY = "Random h x w grid with one 1-rectangle frame containing 1-9 cells of one non-{0,1} color inside (output: 3x3 count-encoding)."

INVARIANTS = [
    "exactly one rectangular 1-frame (>=5 wide, >=5 tall)",
    "1-9 cells of a single non-{0,1} color C strictly inside the frame interior",
    "0-3 stray C-cells outside the frame (don't affect count)",
]

POSITION_BIASES = ("centered", "corner", "near_edge", "scattered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "no_inside", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "frame_h":        {"type": "int", "default": "rng 5..h-2", "valid": "5..h-2"},
    "frame_w":        {"type": "int", "default": "rng 5..w-2", "valid": "5..w-2"},
    "n_inside":       {"type": "int", "default": "rng 1..9", "valid": "1..9"},
    "n_outside":      {"type": "int", "default": "rng 0..2", "valid": "0..3"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # Cap counts at 8: count==9 fills the whole 3x3 output (a solid block).
    if difficulty == "easy":
        h_lo, h_hi = 7, 9
        ni_lo, ni_hi = 1, 4
    elif difficulty == "hard":
        h_lo, h_hi = 11, 14
        ni_lo, ni_hi = 5, 8
    else:
        h_lo, h_hi = 8, 11
        ni_lo, ni_hi = 1, 8
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, rng)
    # output diversity = (count) x (color); maximise the color axis over all
    # non-{0,1} colors rather than the restricted palette pool.
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    fh = int(overrides.get("frame_h",
                           rng.randint(5, max(5, h - 2))))
    fw = int(overrides.get("frame_w",
                           rng.randint(5, max(5, w - 2))))
    fh = max(5, min(fh, h - 2))
    fw = max(5, min(fw, w - 2))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    fr, fc = _pick_pos(bias, h, w, fh, fw, rng)
    draw_frame(g, fr, fc, fr + fh - 1, fc + fw - 1, 1)
    interior = [(r, c) for r in range(fr + 1, fr + fh - 1)
                for c in range(fc + 1, fc + fw - 1)]
    n_inside = int(overrides.get("n_inside",
                                 rng.randint(ni_lo, ni_hi)))
    # count in [1, 8]: 0 -> blank output, 9 -> solid output (both degenerate).
    n_inside = max(1, min(min(8, len(interior)), n_inside))
    chosen = rng.sample(interior, n_inside)
    for r, c in chosen:
        g[r][c] = color
    n_outside = int(overrides.get("n_outside",
                                  ctx.draw_int("n_outside", 0, 2)))
    n_outside = max(0, min(3, n_outside))
    placed = 0
    attempts = 0
    while placed < n_outside and attempts < 30:
        attempts += 1
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if g[r][c] == 0:
            in_interior = (fr < r < fr + fh - 1) and (fc < c < fc + fw - 1)
            on_frame = (r == fr or r == fr + fh - 1 or c == fc or c == fc + fw - 1) and (
                fr <= r <= fr + fh - 1 and fc <= c <= fc + fw - 1)
            if not in_interior and not on_frame:
                g[r][c] = color
                placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """One rectangular 1-frame, and 1..8 cells of a single non-{0,1} color C
    strictly inside it (the rule's count) -> the 3x3 bar output is a partial
    fill (never blank, never solid). Returns violations (empty == pass)."""
    h, w = len(grid), len(grid[0])
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    msgs = []
    if not ones:
        msgs.append("no 1-frame")
        return msgs
    r1 = min(r for r, _ in ones); r2 = max(r for r, _ in ones)
    c1 = min(c for _, c in ones); c2 = max(c for _, c in ones)
    color = next((grid[r][c] for r in range(h) for c in range(w)
                  if grid[r][c] not in (0, 1)), None)
    if color is None:
        msgs.append("no interior color C")
        return msgs
    count = sum(1 for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)
                if grid[r][c] == color)
    if not (1 <= count <= 8):
        msgs.append(f"interior count {count} not in 1..8 (blank/solid output)")
    return msgs


def _pick_pos(bias, h, w, fh, fw, rng):
    max_r = max(0, h - fh - 1)
    max_c = max(0, w - fw - 1)
    if bias == "centered":
        fr = max(0, (h - fh) // 2)
        fc = max(0, (w - fw) // 2)
    elif bias == "corner":
        fr = rng.choice([0, max_r])
        fc = rng.choice([0, max_c])
    elif bias == "near_edge":
        if rng.random() < 0.5:
            fr = rng.choice([0, max_r])
            fc = rng.randint(0, max_c)
        else:
            fr = rng.randint(0, max_r)
            fc = rng.choice([0, max_c])
    else:
        fr = rng.randint(0, max_r)
        fc = rng.randint(0, max_c)
    return fr, fc


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [5, 7, 8]
    elif kind == "primary":
        pool = [2, 3, 4]
    else:
        pool = [2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c not in (0, 1)]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_frame":
        for _ in range(4):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            g[r][c] = 1
        return g
    if name == "no_inside":
        draw_frame(g, 1, 1, 6, 7, 1)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        return g
    return g
