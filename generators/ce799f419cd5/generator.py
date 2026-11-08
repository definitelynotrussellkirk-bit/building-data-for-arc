"""Generator for arc_puzzle_bank_thirteenth21:M88 — motif panels; the collage is stamped at the dividers.

Rule (verified from the canonical Racket — NOT the 'find matching pair' task this generator was built
for): small motifs sit in panels separated by full-height color-9 (maroon) divider columns. The rule
crops the joint bounding box of ALL motif cells, removes the color-9 dividers (-> background), and stamps
that whole motif-collage crop at each former divider-column position. It does NOT identify or emit a
matching motif pair.

⚠ MISMATCH FLAGGED: the generator guarantees exactly one same-shape+same-color motif pair, but the
canonical rule ignores the pair entirely (it stamps the whole collage). This looks like a bad canonical
conversion of M88 — the executable rule and the intended 'find-pair' task disagree. Needs a review of
whether the canonical program_solution for this task is correct before trusting these demos.

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ce799f419cd5"
VERSION = "2.2.0"  # guarantee exactly one same-shape+same-color motif pair; add self_check
TASK_ID = "ce799f419cd5"

SUMMARY = (
    "0-bg grid: n_panels (4-6) of 4-WIDE x h-HEIGHT (panel_h 4..5), separated by FULL-HEIGHT COLOR-9 "
    "(maroon) DIVIDER COLUMNS, each panel holding a SMALL MOTIF (1-3 cells) in a color from {2..7}. "
    "Rule (VERIFIED from the canonical Racket): crop the joint bounding box of ALL motif cells, remove "
    "the color-9 dividers (-> 0), and STAMP that motif-collage crop at each former divider-column "
    "position. It does NOT identify or emit a matching motif pair — see the docstring MISMATCH flag "
    "(the canonical rule and the generator's 'find-pair' design disagree; likely a bad conversion)."
)

INVARIANTS = [
    "background is 0",
    "panels separated by full-height color-9 divider columns (1 col wide)",
    "each panel has a small motif (1-3 cells) in a non-{0,9} color at a random in-panel position",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "n_panels":       {"type": "int", "default": "rng 4..6", "valid": "4..7"},
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


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells

def _normalize(cells):
    min_r = min(r for r, _ in cells); min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _place_motif(grid, panel_index, panel_w, cells, color, rng):
    h = len(grid)
    c0 = panel_index * (panel_w + 1)
    norm = _normalize(cells)
    sh = max(r for r, _ in norm) + 1
    sw = max(c for _, c in norm) + 1
    top = rng.randint(0, h - sh)
    left = rng.randint(0, panel_w - sw)
    for r, c in norm:
        grid[top + r][c0 + left + c] = color


def _panel_motifs(grid):
    h = len(grid); w = len(grid[0]) if h else 0
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    starts = [0] + [c + 1 for c in divs]
    ends = divs + [w]
    motifs = []
    for start, end in zip(starts, ends):
        cells = []
        colors = set()
        for r in range(h):
            for c in range(start, end):
                v = grid[r][c]
                if v not in (0, 9):
                    cells.append((r, c - start)); colors.add(v)
        if not cells or len(colors) != 1:
            motifs.append(None)
        else:
            motifs.append((next(iter(colors)), _normalize(cells)))
    return divs, motifs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        panel_h = ctx.draw_int("panel_h", 4, 4)
        n = ctx.draw_int("n_panels", 4, 5)
    elif difficulty == "hard":
        panel_h = ctx.draw_int("panel_h", 5, 5)
        n = ctx.draw_int("n_panels", 6, 7)
    else:
        panel_h = ctx.draw_int("panel_h", 4, 5)
        n = ctx.draw_int("n_panels", 5, 6)
    rng = ctx.draw_rng("layout")

    panel_w = 4
    # W = n*(panel_w+1) - 1 must fit the 30-col canvas (hard n=7 -> 34 -> clipped/corrupt).
    n = max(4, min(n, 6))   # 4-6 panels fit the 30-col canvas (round2 fix)
    h = panel_h
    w = panel_w * n + (n - 1)
    g = full_grid(h, w, 0)
    for k in range(1, n):
        c = panel_w * k + (k - 1)
        for r in range(h):
            g[r][c] = 9
    # Choose exactly ONE panel pair sharing the same (normalized shape, color); every other
    # panel's (color, shape) key is forced unique -> exactly one pair, no missing/extra pair.
    # (reviewer round2 2.2.0: was independently sampling each panel -> most had NO pair.)
    colors = [1, 2, 3, 4, 5, 6, 7, 8]
    rng.shuffle(colors)
    pair_a, pair_b = sorted(rng.sample(range(n), 2))
    shared_shape = _normalize(_build_motif(rng, rng.randint(1, 3)))
    shared_color = colors[0]
    used_keys = {(shared_color, shared_shape)}
    for k in range(n):
        if k in (pair_a, pair_b):
            cells, color = shared_shape, shared_color
        else:
            for _ in range(100):
                cells = _normalize(_build_motif(rng, rng.randint(1, 3)))
                color = colors[(k + rng.randint(1, len(colors) - 1)) % len(colors)]
                if (color, cells) not in used_keys:
                    used_keys.add((color, cells)); break
            else:
                color = colors[(k + 1) % len(colors)]; cells = ((0, 0),)
                if (color, cells) in used_keys:
                    color = colors[(k + 2) % len(colors)]
                used_keys.add((color, cells))
        _place_motif(g, k, panel_w, cells, color, rng)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify panel gallery geometry: 4-wide panels, full 9 dividers, non-empty motifs."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    panel_w = 4
    if (w + 1) % (panel_w + 1) != 0:
        return [f"width {w} is not n*4+(n-1) panel geometry"]
    n = (w + 1) // (panel_w + 1)
    if n < 4:
        errs.append(f"expected at least 4 panels, got {n}")
    for k in range(1, n):
        dc = panel_w * k + (k - 1)
        if any(grid[r][dc] != 9 for r in range(h)):
            errs.append(f"divider column {dc} is not full color-9")
            break
    for k in range(n):
        c0 = k * (panel_w + 1)
        cells = [(r, c) for r in range(h) for c in range(c0, c0 + panel_w)
                 if grid[r][c] not in (0, 9)]
        if not cells:
            errs.append(f"panel {k} has no motif cells")
        if len(cells) > 4:
            errs.append(f"panel {k} motif too large: {len(cells)} cells")
    bad = [v for row in grid for v in row if v not in range(10)]
    if bad:
        errs.append(f"cell values outside 0..9: {bad[:3]}")
    return errs


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
