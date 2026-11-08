"""Generator for arc_puzzle_bank_21_set24_s:S24_H6 — panel onion-depth rotation match.

Rule: split into panels at full-height color-9 divider columns. Panel 0 is the PROTO.
For each later panel, compute its onion-layer depth-map (peel boundary layers inward),
crop to content, and mark it 8 if that depth-map equals the proto's under any of the 4
rotations, else 0. Output is a 1x(n-1) strip of those marks. (The stale "each has a small
motif" header was the copy-paste panel-family template; the SUMMARY below is authoritative.)

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8dba37abe8ef"
VERSION = "2.0.1"
TASK_ID = "8dba37abe8ef"

SUMMARY = "n panels separated by full color-9 columns; panel 0 holds a proto motif. Each later panel is either a rotation of the proto (matches) or a different-size motif (doesn't). Rule outputs a 1x(n-1) row with 8 where panel k's onion-depth-map matches panel 0's under rotation. Panel count, proto shape, match pattern and colors vary."

INVARIANTS = [
    "background is 0",
    "panels separated by full-height color-9 divider columns (1 col wide)",
    "panel 0 holds the proto motif; each later panel is a rotation of it or a different-size motif",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "n_panels":       {"type": "int", "default": "rng 5..6", "valid": "3..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "motif_size":     {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "horizontal_panels_9divs",
                       "valid": "horizontal_panels_9divs"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_dividers|empty_panels|single_panel"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid has >=1 color-9 divider column separating panels."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_dividers", "empty_panels", "single_panel"):
        return errs
    has_9_col = any(
        all(grid[r][c] == 9 for r in range(h))
        for c in range(w)
    )
    if not has_9_col:
        errs.append("no full-height color-9 divider column found")
    return errs


def _norm(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return sorted((r - rmin, c - cmin) for r, c in cells)


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    return _norm(cells)


def _rot_cw(cells):
    maxr = max(r for r, _ in cells)
    return _norm([(c, maxr - r) for r, c in cells])


def _rotk(cells, k):
    out = list(cells)
    for _ in range(k % 4):
        out = _rot_cw(out)
    return out


def _fits(cells, ph, pw):
    return max(r for r, _ in cells) + 1 <= ph and max(c for _, c in cells) + 1 <= pw


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        panel_h = ctx.draw_int("panel_h", 4, 4); n = ctx.draw_int("n_panels", 3, 4)
    elif difficulty == "hard":
        panel_h = ctx.draw_int("panel_h", 5, 5); n = ctx.draw_int("n_panels", 5, 6)
    else:
        panel_h = ctx.draw_int("panel_h", 4, 5); n = ctx.draw_int("n_panels", 4, 6)
    rng = ctx.draw_rng("layout")
    panel_w = 4
    n = min(n, 6)
    h = panel_h
    w = panel_w * n + (n - 1)
    for _outer in range(40):
        g = full_grid(h, w, 0)
        for k in range(1, n):
            c = panel_w * k + (k - 1)
            for r in range(h):
                g[r][c] = 9
        # proto motif (fits the panel and all its rotations fit)
        proto = None
        for _ in range(40):
            cand = _build_motif(rng, rng.randint(2, 5))
            if _fits(cand, h, panel_w) and all(_fits(_rotk(cand, k), h, panel_w) for k in range(4)):
                proto = cand; break
        if proto is None:
            continue
        sp = len(proto)
        ok = True
        for k in range(n):
            c0 = k * (panel_w + 1)
            if k == 0:
                shape = proto
            elif rng.random() < 0.5:                # MATCH: a rotation of proto
                shape = _rotk(proto, rng.randint(0, 3))
            else:                                    # NO MATCH: different-size motif
                shape = None
                for _ in range(40):
                    cand = _build_motif(rng, rng.choice([s for s in range(1, 6) if s != sp]))
                    if _fits(cand, h, panel_w):
                        shape = cand; break
                if shape is None:
                    ok = False; break
            shape = _norm(shape)
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
            top = rng.randint(0, h - sh); left = rng.randint(0, panel_w - sw)
            for r, c in shape:
                g[top + r][c0 + left + c] = color
        if ok:
            return g
    raise ValueError("could not realize panel-match layout")


def _draw_from_degenerate(name, rng):
    panel_h, n, panel_w = 4, 5, 4
    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        for k in range(n):
            c0 = k * panel_w
            g[1][c0 + 1] = [4, 6, 7, 4, 6][k]
        return g
    if name == "empty_panels":
        for k in range(1, n):
            c = panel_w * k + (k - 1)
            for r in range(h): g[r][c] = 9
        return g
    if name == "single_panel":
        g[1][1] = 4
        return g
    return g
