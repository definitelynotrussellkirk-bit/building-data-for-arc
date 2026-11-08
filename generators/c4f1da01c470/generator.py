"""Generator for 3d588dc9.

Rule: a zero LOLLIPOP (a solid rectangular body + a thin stem pointing
toward a color-5 object) loses its stem (cleared to bg 7), and the body
edge FACING the color-5 object is painted color 6.

Combinatorial axes: grid size, orientation (which side the 5 is on),
body size, stem length, and positions.
Degenerates: no_stem, no_target, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "c4f1da01c470"
RULE_HASH = "9d9d84c57766"  # canonical rule this generator was written against
VERSION = "2.1.0"  # add executable lollipop/target self_check
TASK_ID = "c4f1da01c470"
SUMMARY = (
    "Color-7 (orange) background grid (size varies). A zero LOLLIPOP — a "
    "solid 3-4 cell rectangular body plus a thin 1-2 cell STEM at its "
    "facing-edge midpoint — points toward a color-5 (gray) object on one "
    "side. Rule: clear the stem (to 7) and paint the body edge facing the "
    "color-5 object with COLOR 6 (magenta). The grid size, orientation, "
    "body size, stem length and positions all vary freely (was a fixed "
    "13x13 with fixed positions, ~12 distinct)."
)

INVARIANTS = [
    "background is color 7; one zero lollipop (solid body + thin stem)",
    "a color-5 object aligned with the body on the stem's side",
    "the body's facing edge gets color 6 and the stem is cleared",
]

ORIENTATIONS = ("right", "left", "down", "up")
BODY_SIZES = ("3x3", "3x4", "4x3")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_stem", "no_target", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..18"},
    "orientation":    {"type": "str", "default": "rng helpful",
                       "valid": "right|left|down|up"},
    "body_size":      {"type": "str", "default": "varies", "valid": "3x3|3x4|4x3|4x4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for orientation",
                       "valid": "right|left|down|up|no_stem|no_target|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = overrides.get("orientation")
    if orientation not in ORIENTATIONS:
        orientation = rng.choice(ORIENTATIONS)

    if difficulty == "easy":
        gr, sr = (11, 13), (1, 2)
    elif difficulty == "hard":
        gr, sr = (13, 18), (1, 3)
    else:
        gr, sr = (12, 16), (1, 2)

    for _attempt in range(40):
        h = rng.randint(*gr); w = rng.randint(*gr)
        bh = rng.randint(3, 4); bw = rng.randint(3, 4)
        stem = rng.randint(*sr)
        g5 = rng.randint(2, 3)        # size of the gray target block
        g = full_grid(h, w, 7)

        if orientation in ("right", "left"):
            if h - 1 - bh < 1:
                continue
            r0 = rng.randint(1, h - 1 - bh)
            need = bw + stem + g5 + 2   # body + stem + gray + margins along the row
            if orientation == "right":
                if w - need < 1:
                    continue
                c0 = rng.randint(1, w - need)
                draw_rect(g, r0, c0, bh, bw, 0)
                mid = r0 + bh // 2
                for c in range(c0 + bw, c0 + bw + stem):
                    g[mid][c] = 0
                draw_rect(g, r0, c0 + bw + stem, bh, g5, 5)
            else:  # left
                lo = g5 + stem + 1; hi = w - bw - 1
                if lo > hi:
                    continue
                c0 = rng.randint(lo, hi)
                draw_rect(g, r0, c0, bh, bw, 0)
                mid = r0 + bh // 2
                for c in range(c0 - stem, c0):
                    g[mid][c] = 0
                draw_rect(g, r0, c0 - stem - g5, bh, g5, 5)
        else:
            if w - 1 - bw < 1:
                continue
            c0 = rng.randint(1, w - 1 - bw)
            need = bh + stem + g5 + 2
            if orientation == "down":
                if h - need < 1:
                    continue
                r0 = rng.randint(1, h - need)
                draw_rect(g, r0, c0, bh, bw, 0)
                mid = c0 + bw // 2
                for r in range(r0 + bh, r0 + bh + stem):
                    g[r][mid] = 0
                draw_rect(g, r0 + bh + stem, c0, g5, bw, 5)
            else:  # up
                lo = g5 + stem + 1; hi = h - bh - 1
                if lo > hi:
                    continue
                r0 = rng.randint(lo, hi)
                draw_rect(g, r0, c0, bh, bw, 0)
                mid = c0 + bw // 2
                for r in range(r0 - stem, r0):
                    g[r][mid] = 0
                draw_rect(g, r0 - stem - g5, c0, g5, bw, 5)
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 7)
    if name == "no_stem":
        draw_rect(g, 4, 2, 3, 3, 0)
        draw_rect(g, 4, 10, 3, 2, 5)
        return g
    if name == "no_target":
        draw_rect(g, 4, 2, 3, 3, 0)
        for c in range(5, 7):
            g[5][c] = 0
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 5
        return g
    return g


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = [(r, c)]; seen.add((r, c)); cells = []
            for rr, cc in q:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    colors = {v for row in grid for v in row}
    if not colors.issubset({0, 5, 7}):
        errs.append(f"unexpected colors for lollipop task: {sorted(colors - {0, 5, 7})}")
    zeros = _components(grid, 0)
    targets = _components(grid, 5)
    if len(zeros) != 1:
        errs.append(f"expected one connected zero lollipop, found {len(zeros)}")
    if len(targets) != 1:
        errs.append(f"expected one connected color-5 target, found {len(targets)}")
    if zeros:
        rs = [r for r, _ in zeros[0]]; cs = [c for _, c in zeros[0]]
        if max(rs) - min(rs) + 1 < 3 or max(cs) - min(cs) + 1 < 3:
            errs.append("zero lollipop bbox too small to contain body plus stem")
    if targets and len(targets[0]) < 4:
        errs.append("color-5 target is too small")
    return errs
