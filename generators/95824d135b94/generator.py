"""Generator for arc_puzzle_bank_seventeenth21:H119 — 6 panels separated by 9-cols, find pair.

Rule: 6 panels separated by full color-9 columns; each has a small motif.

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "95824d135b94"
# 3.0.0: all_background fix + correct construction. The canonical rule is NOT a
# "find matching pair" rule -- it splits into EXACTLY 5 SQUARE panels, infers
# transform f1 (panel0->panel1) and f2 (panel2->panel3), and outputs
# f2(f1(panel4)). The old generator made n in {4..7} random-motif panels, so
# panel4 was often empty (-> all-0 output) and panel0/1, panel2/3 had no
# transform relation. Now: 5 square panels, panel1=transform(panel0),
# panel3=transform(panel2), panel4 a non-empty motif -> output is always the
# (non-empty) transformed panel4.
VERSION = "3.0.0"
TASK_ID = "95824d135b94"

SUMMARY = (
    "Horizontal panel "
    "layout (panel_h ∈ "
    "[4, 5], 5-6 PANELS "
    "each of width 4) "
    "separated by FULL-"
    "HEIGHT COLOR-9 "
    "(maroon) DIVIDER "
    "COLUMNS between "
    "panels. Total width = "
    "4*n_panels + (n_panels"
    " - 1). Each panel "
    "contains a SMALL "
    "MOTIF (1-3 cells, "
    "connected blob) in a "
    "color from {2..7}. "
    "Panels may share "
    "motifs by chance. "
    "Rule (FIND THE "
    "MATCHING PANEL PAIR "
    "AND ISOLATE / MARK): "
    "scan all panels and "
    "find which TWO PANELS "
    "share the SAME MOTIF "
    "SHAPE (up to color/"
    "translation matching, "
    "per puzzle convention)"
    ". Mark or extract the "
    "MATCHING PAIR — e.g., "
    "isolate those two "
    "panel crops side by "
    "side, or paint a "
    "marker on them. Net: "
    "among n panels, "
    "identify the two "
    "whose motifs match."
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
    "n_panels":       {"type": "int", "default": "rng 5..6", "valid": "4..7"},
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


# panel transforms — must mirror the canonical rule's s17-transform exactly
# (panels are square pw x pw so every kind preserves the panel shape).
_KINDS = ("id", "rot90", "rot180", "rot270", "flip_h", "flip_v",
          "transpose", "anti_transpose")


def _apply(p, kind):
    n = len(p)
    if kind == "id":
        return [row[:] for row in p]
    if kind == "rot90":                  # rotate-cw
        return [[p[n - 1 - c][r] for c in range(n)] for r in range(n)]
    if kind == "rot180":
        return [[p[n - 1 - r][n - 1 - c] for c in range(n)] for r in range(n)]
    if kind == "rot270":                 # rotate-ccw
        return [[p[c][n - 1 - r] for c in range(n)] for r in range(n)]
    if kind == "flip_h":                 # flip-lr
        return [[p[r][n - 1 - c] for c in range(n)] for r in range(n)]
    if kind == "flip_v":                 # flip-ud
        return [[p[n - 1 - r][c] for c in range(n)] for r in range(n)]
    if kind == "transpose":
        return [[p[c][r] for c in range(n)] for r in range(n)]
    # anti_transpose
    return [[p[n - 1 - c][n - 1 - r] for c in range(n)] for r in range(n)]


def _rand_panel(rng, pw, min_size=1):
    """A pw x pw panel (0-bg) carrying one connected motif in a non-{0,9} colour."""
    hi = max(min_size, min(pw + 1, pw * pw // 2 + 1))
    for _ in range(20):
        cells = _build_motif(rng, rng.randint(min_size, hi))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        if sh <= pw and sw <= pw:
            break
    else:
        cells = [(0, 0)]; rs = cs = [0]; sh = sw = 1
    p = [[0] * pw for _ in range(pw)]
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    top = rng.randint(0, pw - sh); left = rng.randint(0, pw - sw)
    for r, c in cells:
        p[top + r - min(rs)][left + c - min(cs)] = color
    return p


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        pw = ctx.draw_int("panel_h", 3, 4)
    elif difficulty == "hard":
        pw = ctx.draw_int("panel_h", 4, 5)
    else:
        pw = ctx.draw_int("panel_h", 3, 5)
    rng = ctx.draw_rng("layout")

    n = 5                                 # the rule hard-codes a 5-panel split
    h = pw
    w = pw * n + (n - 1)
    g = full_grid(h, w, 0)
    for k in range(1, n):                 # full-height colour-9 dividers
        c = pw * k + (k - 1)
        for r in range(h):
            g[r][c] = 9

    p0 = _rand_panel(rng, pw); p1 = _apply(p0, rng.choice(_KINDS))
    p2 = _rand_panel(rng, pw); p3 = _apply(p2, rng.choice(_KINDS))
    # panel4 drives the output; a >=2-cell motif gives richer, more varied
    # (non-trivially-symmetric) transformed outputs
    p4 = _rand_panel(rng, pw, min_size=2)
    panels = [p0, p1, p2, p3, p4]
    for k, p in enumerate(panels):
        c0 = k * (pw + 1)
        for r in range(pw):
            for c in range(pw):
                if p[r][c]:
                    g[r][c0 + c] = p[r][c]
    return g


def _infer_kind(a, b):
    return next((k for k in _KINDS if _apply(a, k) == b), None)


def self_check(grid, *, difficulty=None, meta=None):
    """5 square panels separated by colour-9 dividers; panel1 is a transform of
    panel0 and panel3 a transform of panel2 (so the rule's f1/f2 inference does
    not hit first-of-empty), and panel4 is non-empty (so f2(f1(panel4)) is a
    non-degenerate output, not all-0)."""
    h, w = len(grid), len(grid[0])
    pw = h
    if w != pw * 5 + 4:
        return [f"grid {h}x{w} is not 5 square {pw}-panels with 4 dividers"]
    panels = []
    for k in range(5):
        c0 = k * (pw + 1)
        panels.append([[grid[r][c0 + c] for c in range(pw)] for r in range(pw)])
    if not any(v not in (0,) for row in panels[4] for v in row):
        return ["panel 4 is empty -> output is all-0 (degenerate)"]
    if _infer_kind(panels[0], panels[1]) is None:
        return ["panel1 is not a transform of panel0 -> rule f1 inference fails"]
    if _infer_kind(panels[2], panels[3]) is None:
        return ["panel3 is not a transform of panel2 -> rule f2 inference fails"]
    return []


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
