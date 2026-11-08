"""Generator for arc_puzzle_bank_21_set15:S15_M3.

Rule: take the color-2 template (normalized to top-left), apply transform
op 3 ((r,c)->(c, h-1-r), a 90 rotation), and stamp it in color 8 at the
first color-1 marker on a blank grid.

This generator draws a random color-2 template and a color-1 marker placed
so the rotated stamp fits in bounds.

Combinatorial axes: grid size, the template shape, and the marker position.
Degenerates: no_template, no_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "9a1157936e2b"
VERSION = "2.0.1"  # diversity: random template + marker, rotate-stamp (was fixed ~24)
TASK_ID = "9a1157936e2b"
SUMMARY = (
    "0-bg grid (size varies). A color-2 template shape and a color-1 marker. "
    "Rule: rotate the template (op 3 = (r,c)->(c,h-1-r)) and stamp it in "
    "color 8 at the marker, on a blank grid. The grid size, template shape "
    "and marker position vary freely (was a fixed setup, ~24 distinct)."
)

INVARIANTS = [
    "one color-2 template and one color-1 marker",
    "the rotated template fits in bounds anchored at the marker",
    "the output is the rotated template in color 8 at the marker",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_marker", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "template_size":  {"type": "int", "default": "varies", "valid": "3..7"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "template_plus_marker",
                       "valid": "template_plus_marker"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_template|no_marker|full_grid"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _op3(cells):
    nr = _norm(cells); h = max(r for r, c in nr) + 1
    return _norm([(c, h - 1 - r) for r, c in nr])


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 color-2 connected component (template); exactly 1 color-1 cell (marker)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    # Count color-2 components
    seen = set()
    comps2 = 0
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) in seen or grid[r0][c0] != 2:
                continue
            stack = [(r0, c0)]; seen.add((r0, c0))
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 2:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps2 += 1
    cells1 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    errs = []
    if comps2 < 1:
        errs.append(f"expected >=1 color-2 template component; found {comps2}")
    if cells1 != 1:
        errs.append(f"expected exactly 1 color-1 marker cell; found {cells1}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, ts = (12, 14), (12, 16), (3, 4)
    elif difficulty == "hard":
        hr, wr, ts = (16, 22), (18, 24), (5, 7)
    else:
        hr, wr, ts = (13, 18), (14, 20), (3, 6)

    for _attempt in range(40):
        base = _poly(rng, rng.randint(*ts))
        bh = max(r for r, c in base) + 1; bw = max(c for r, c in base) + 1
        stamped = _op3(base)
        th = max(r for r, c in stamped) + 1; tw = max(c for r, c in stamped) + 1

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        if bh + 1 > h or bw + 1 > w:
            continue
        bt = rng.randint(0, h - bh); bl = rng.randint(0, w - bw)
        if not _reserve(occ, bt, bl, bh, bw, h, w):
            continue
        paint_at(g, bt, bl, base, 2)
        # marker so the rotated stamp footprint fits and is free
        for _t in range(50):
            mr = rng.randint(0, h - th); mc = rng.randint(0, w - tw)
            foot = [(mr + r, mc + c) for r, c in stamped]
            if any(occ[r][c] for r, c in foot):
                continue
            if any(0 <= mr + dr < h and 0 <= mc + dc < w and occ[mr + dr][mc + dc]
                   for dr, dc in _CARD):
                continue
            g[mr][mc] = 1
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    base = [(0, 0), (1, 0), (1, 1)]
    paint_at(g, 1, 1, base, 2)
    if name == "no_template":
        g2 = full_grid(12, 14, 0); g2[6][6] = 1
        return g2
    if name == "no_marker":
        return g
    if name == "full_grid":
        return full_grid(12, 14, 2)
    g[6][8] = 1
    return g
