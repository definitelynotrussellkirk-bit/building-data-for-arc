"""Generator for 7d419a02.

Rule: a color-6 block has a bbox. Each color-8 cell stays 8 if it is on the
bbox row-band or col-band (aligned with the 6 block); otherwise it stays 8
or becomes 4 depending on how many all-0 separator rows/cols lie between it
and the bbox (a diamond-support condition).

This generator draws a color-6 block plus scattered color-8 cells (some
aligned with the block, some diagonal), letting the all-0 lines act as
separators.

Combinatorial axes: grid size, the 6-block size/position, and the 8
positions.
Degenerates: no_six, no_eight, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b58ebf4ada2f"
VERSION = "2.0.1"  # diversity: random 6-block + scattered 8s diamond projection (was fixed ~26)
TASK_ID = "b58ebf4ada2f"
SUMMARY = (
    "0-bg grid (size varies). A color-6 block and scattered color-8 cells. "
    "Rule: each 8 stays 8 if aligned with the 6 block's bbox row/col band; "
    "otherwise it stays 8 or becomes 4 by a diamond-support condition on the "
    "all-0 separator rows/cols between it and the block. The grid size, "
    "6-block and 8 positions vary freely (was a fixed setup, ~26 distinct)."
)

INVARIANTS = [
    "one color-6 block plus scattered color-8 cells",
    "8s on the block's row/col band stay 8; diagonal 8s recolor by separators",
    "the output keeps non-8 cells unchanged",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_six", "no_eight", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "six_size":       {"type": "int", "default": "varies", "valid": "2..4"},
    "n_eights":       {"type": "int", "default": "varies", "valid": "4..12"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "block_plus_eights",
                       "valid": "block_plus_eights"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_six|no_eight|full_grid"},
}


def _apply(g):
    """Faithful reimplementation of the rule (also the verifier)."""
    h = len(g); w = len(g[0])
    sixes = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 6]
    sr1 = min(r for r, c in sixes); sr2 = max(r for r, c in sixes)
    sc1 = min(c for r, c in sixes); sc2 = max(c for r, c in sixes)
    sep_rows = [r for r in range(1, h - 1) if all(g[r][c] == 0 for c in range(w))]
    sep_cols = [c for c in range(1, w - 1) if all(g[r][c] == 0 for r in range(h))]
    has_rsep = bool(sep_rows); has_csep = bool(sep_cols)

    def cseps(pos, bmin, bmax, seps):
        lo = min(pos, bmin); hi = max(pos, bmax)
        return sum(1 for s in seps if lo < s < hi)

    out = [row[:] for row in g]
    for r in range(h):
        for c in range(w):
            if g[r][c] != 8:
                continue
            d_pr = max(0, sr1 - r, r - sr2); d_pc = max(0, sc1 - c, c - sc2)
            if d_pr == 0 or d_pc == 0:
                out[r][c] = 8
                continue
            d_rb = cseps(r, sr1, sr2, sep_rows) if has_rsep else 0
            d_cb = cseps(c, sc1, sc2, sep_cols) if has_csep else 0
            if has_rsep and has_csep:
                stay = (d_pc <= 2 * max(0, d_rb - 1)) and (d_pr <= 2 * max(0, d_cb - 1))
            elif has_rsep:
                stay = d_pc <= 2 * max(0, d_rb - 1)
            elif has_csep:
                stay = d_pr <= 2 * max(0, d_cb - 1)
            else:
                stay = False
            out[r][c] = 8 if stay else 4
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, sz, nr = (12, 14), (12, 16), (2, 3), (4, 7)
    elif difficulty == "hard":
        hr, wr, sz, nr = (16, 22), (18, 24), (3, 4), (8, 12)
    else:
        hr, wr, sz, nr = (13, 18), (14, 20), (2, 4), (5, 10)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        bh = rng.randint(*sz); bw = rng.randint(*sz)
        bt = rng.randint(2, h - bh - 2); bl = rng.randint(2, w - bw - 2)
        g = full_grid(h, w, 0)
        for r in range(bt, bt + bh):
            for c in range(bl, bl + bw):
                g[r][c] = 6
        block = {(r, c) for r in range(bt, bt + bh) for c in range(bl, bl + bw)}

        cnt = 0
        # Explicitly exercise the "aligned with the 6-block row/col band"
        # branch.  Purely random 8 placement often produced only diagonal
        # examples, so the output-changing branch had coverage but the
        # preserve-aligned-8 branch was hidden.
        aligned = []
        for r in range(bt, bt + bh):
            for c in list(range(0, bl)) + list(range(bl + bw, w)):
                aligned.append((r, c))
        for c in range(bl, bl + bw):
            for r in list(range(0, bt)) + list(range(bt + bh, h)):
                aligned.append((r, c))
        rng.shuffle(aligned)
        for r, c in aligned:
            if g[r][c] == 0:
                g[r][c] = 8
                cnt += 1
                break
        for _ in range(rng.randint(*nr)):
            for _t in range(20):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if (r, c) not in block and g[r][c] == 0:
                    g[r][c] = 8; cnt += 1; break
        if cnt < 2:
            continue
        if _apply(g) != g:           # ensure some 8 -> 4 (non-trivial)
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    for r in range(5, 7):
        for c in range(6, 8):
            g[r][c] = 6
    g[5][2] = 8; g[1][2] = 8
    if name == "no_six":
        g2 = full_grid(12, 14, 0); g2[5][2] = 8
        return g2
    if name == "no_eight":
        g[5][2] = 0; g[1][2] = 0
        return g
    if name == "full_grid":
        return full_grid(12, 14, 6)
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    sixes = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 6]
    eights = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    if not sixes:
        msgs.append("expected a color-6 block")
        return msgs
    if len(eights) < 2:
        msgs.append("expected at least two color-8 probe cells")
    sr1 = min(r for r, _ in sixes); sr2 = max(r for r, _ in sixes)
    sc1 = min(c for _, c in sixes); sc2 = max(c for _, c in sixes)
    if not any(sr1 <= r <= sr2 or sc1 <= c <= sc2 for r, c in eights):
        msgs.append("no color-8 cell exercises the aligned-row/column preserve branch")
    try:
        out = _apply(grid)
    except Exception as e:
        msgs.append(f"local rule application failed: {type(e).__name__}")
    else:
        changed = sum(1 for r, c in eights if out[r][c] == 4)
        if changed < 1:
            msgs.append("no color-8 cell changes to 4; diamond separator branch is hidden")
    return msgs
