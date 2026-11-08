"""Generator for puzzle 70e6b513.

Rule: full separator row/col split repeated tiles. Output keeps
unanimous cells across the 4 tiles and writes 1 for any disagreement.

Combinatorial axes (8): tile_h, tile_w, palette_kind, palette_size,
disagreement_count, sep_color, anchor_corner, asymmetry_force.
Degenerates: no_disagreement, all_disagreement, no_separator.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c50efad27ca7"
VERSION = "1.2.0"  # add executable separator/tile-disagreement invariants for random audit
TASK_ID = "c50efad27ca7"
SUMMARY = "Tiled tiles w/ separator; rule keeps unanimous, writes 1 for disagreements."

INVARIANTS = [
    "h = 2*th+1, w = 2*tw+1 with th, tw in [3, 5]",
    "row th and col tw are full-5 separators",
    "4 tile copies with 1-3 disagreements between them",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_disagreement", "all_disagreement", "no_separator")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "tile_h":           {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "tile_w":           {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "palette_kind":     {"type": "str", "default": "rng helpful",
                         "valid": "|".join(PALETTE_KINDS)},
    "palette_size":     {"type": "int", "default": "rng 3..5", "valid": "2..7"},
    "disagreement_count":{"type": "int", "default": "rng 1..3",
                          "valid": "1..5"},
    "sep_color":        {"type": "color", "default": "5", "valid": "5"},
    "anchor_corner":    {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "asymmetry_force":  {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "texture":          {"type": "str", "default": "alias for palette_kind",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        th_lo, th_hi = 2, 3
    elif difficulty == "hard":
        th_lo, th_hi = 5, 7
    else:
        th_lo, th_hi = 3, 5
    th = int(overrides.get("tile_h",
                           ctx.draw_int("tile_h", th_lo, th_hi)))
    tw = int(overrides.get("tile_w",
                           ctx.draw_int("tile_w", th_lo, th_hi)))
    th = max(2, min(7, th))
    tw = max(2, min(7, tw))
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    palette_size = int(overrides.get("palette_size",
                                     ctx.draw_int("palette_size", 3, 5)))
    palette_size = max(2, min(7, palette_size))
    palette = _build_palette(palette_kind, palette_size, rng)
    n_dis = int(overrides.get("disagreement_count",
                              ctx.draw_int("disagreement_count", 1, 3)))
    n_dis = max(1, min(5, n_dis))
    h = th * 2 + 1
    w = tw * 2 + 1
    g = full_grid(h, w, 0)
    for c in range(w):
        g[th][c] = 5
    for r in range(h):
        g[r][tw] = 5
    base = [[rng.choice(palette) for _ in range(tw)] for _ in range(th)]
    starts = [(0, 0), (0, tw + 1), (th + 1, 0), (th + 1, tw + 1)]
    for r0, c0 in starts:
        for r in range(th):
            for c in range(tw):
                g[r0 + r][c0 + c] = base[r][c]
    # Introduce n_dis disagreements at random positions across the 4 tiles
    cells = [(r, c) for r in range(th) for c in range(tw)]
    rng.shuffle(cells)
    for i in range(min(n_dis, len(cells))):
        cr, cc = cells[i]
        # Pick a random tile to differ
        tr, tc = rng.choice(starts[1:])
        differ_color = next((p for p in palette if p != base[cr][cc]),
                            (palette[0] + 1) % 10)
        if differ_color == 5 or differ_color == 0:
            differ_color = 7
        g[tr + cr][tc + cc] = differ_color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the 2x2 tiled board has one separator cross and real disagreements."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    sep_rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    sep_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(sep_rows) != 1 or len(sep_cols) != 1:
        return [f"expected exactly one full color-5 separator row/col, found {len(sep_rows)}/{len(sep_cols)}"]
    sr, sc = sep_rows[0], sep_cols[0]
    if h != 2 * sr + 1 or w != 2 * sc + 1:
        errs.append("separator row/col do not split the grid into four equal tiles")
    if sr < 2 or sc < 2:
        errs.append("tile dimensions are too small for normal examples")
    for r in range(h):
        for c in range(w):
            if r == sr or c == sc:
                if grid[r][c] != 5:
                    errs.append("separator cross contains a non-5 cell")
            elif grid[r][c] in (0, 5):
                errs.append("tile cells should use nonzero, non-separator colors")
                break
    if errs:
        return errs
    starts = [(0, 0), (0, sc + 1), (sr + 1, 0), (sr + 1, sc + 1)]
    disagreements = 0
    unanimous = 0
    for r in range(sr):
        for c in range(sc):
            vals = [grid[r0 + r][c0 + c] for r0, c0 in starts]
            if len(set(vals)) == 1:
                unanimous += 1
            else:
                disagreements += 1
    if not (1 <= disagreements <= min(5, sr * sc)):
        errs.append(f"expected 1..{min(5, sr * sc)} local disagreements, found {disagreements}")
    if unanimous == 0:
        errs.append("all tile positions disagree; normal examples need some unanimous cells")
    return errs


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 7, 8]
    elif kind == "primary":
        pool = [2, 3, 4]
    else:
        pool = [2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [2, 3, 4, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    th = 3; tw = 3
    h = th * 2 + 1; w = tw * 2 + 1
    g = full_grid(h, w, 0)
    for c in range(w):
        g[th][c] = 5
    for r in range(h):
        g[r][tw] = 5
    base = [[rng.choice([2, 3, 4]) for _ in range(tw)] for _ in range(th)]
    starts = [(0, 0), (0, tw + 1), (th + 1, 0), (th + 1, tw + 1)]
    if name == "no_disagreement":
        for r0, c0 in starts:
            for r in range(th):
                for c in range(tw):
                    g[r0 + r][c0 + c] = base[r][c]
        return g
    if name == "all_disagreement":
        for i, (r0, c0) in enumerate(starts):
            for r in range(th):
                for c in range(tw):
                    g[r0 + r][c0 + c] = (i % 4) + 2
        return g
    if name == "no_separator":
        # No separators
        g2 = full_grid(h, w, 0)
        for r in range(h):
            for c in range(w):
                g2[r][c] = base[r % th][c % tw]
        return g2
    return g
