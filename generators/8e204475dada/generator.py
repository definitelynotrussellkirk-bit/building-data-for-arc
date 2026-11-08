"""Generator for arc_puzzle_bank_21_set5_s:S5_H2 — row-pair recolor map.

Rule: row 0 gives source colors and row 1 gives target colors at the same
columns. For rows 2..end, every non-zero cell whose color appears in row 0 is
recolored to the paired row-1 color; zeros stay zero and unmapped colors are
preserved.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, identity_pairs, unmapped_body_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8e204475dada"
VERSION = "1.2.0"
TASK_ID = "8e204475dada"

SUMMARY = "Top two rows encode 3-4 source→target color pairs; body motifs use the source colors so the rule recolors them by column-wise lookup."

INVARIANTS = [
    "background is 0",
    "row 0/row 1 contain 3-4 aligned non-zero source→target color pairs",
    "non-pair cells in the first two rows are 0",
    "body contains at least one motif for every source color and no unmapped colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "identity_pairs", "unmapped_body_only")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "map_rows_plus_spaced_source_motifs",
                       "valid": "map_rows_plus_spaced_source_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n = ctx.draw_int("n_pairs", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        n = ctx.draw_int("n_pairs", 4, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n_pairs", 3, 4)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        sources = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        targets = rng.sample([c for c in range(1, 10) if c not in sources], n)
        cols = sorted(rng.sample(range(w), n))
        for col, src, tgt in zip(cols, sources, targets):
            g[0][col] = src
            g[1][col] = tgt

        ok = True
        for color in sources:
            cells = _build_motif(rng, rng.randint(3, 5))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(2, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize row-pair recolor layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # body exists but the top mapping rows are blank.
        for (r, c) in [(4, 3), (4, 4), (5, 3), (6, 3)]: g[r][c] = 4
        return g
    if name == "identity_pairs":
        # source maps to itself, so recoloring is hidden.
        g[0][1] = 4; g[1][1] = 4
        for (r, c) in [(4, 3), (4, 4), (5, 3), (6, 3)]: g[r][c] = 4
        return g
    if name == "unmapped_body_only":
        # map rows exist, but the body contains only colors not named by row 0.
        g[0][1] = 4; g[1][1] = 7
        for (r, c) in [(4, 3), (4, 4), (5, 3), (6, 3)]: g[r][c] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if len(grid) < 3:
        return ["grid must have mapping rows plus a body"]
    h, w = len(grid), len(grid[0])
    pairs = [(grid[0][c], grid[1][c]) for c in range(w) if grid[0][c] != 0]
    if not (3 <= len(pairs) <= 4):
        msgs.append("expected 3-4 nonzero source->target mapping pairs")
    if any(src == tgt or tgt == 0 for src, tgt in pairs):
        msgs.append("mapping pairs must be nonzero and non-identity")
    source_cols = {c for c in range(w) if grid[0][c] != 0}
    if any(grid[1][c] != 0 for c in range(w) if c not in source_cols):
        msgs.append("row 1 has target colors without a row-0 source")
    sources = {src for src, _ in pairs}
    body_vals = {v for row in grid[2:] for v in row if v != 0}
    if not sources or not sources <= body_vals:
        msgs.append("body must exercise every source color")
    if body_vals - sources:
        msgs.append("body contains unmapped nonzero colors")
    return msgs
