"""Generator for arc_puzzle_bank_ninth21:M60 — hollow vs solid recolor.

Rule: each non-bg component is checked. If its cells fully fill its
bbox (solid, no hole-cells inside the bbox interior), recolor to 4.
Otherwise (hollow — at least one bbox interior cell is bg), recolor
to 8.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect, draw_rect_outline
from puzzle_generators.helpers.selfcheck import components as _components

GENERATOR_ID = "9e7fcd5605d8"
VERSION = "1.3.0"
TASK_ID = "9e7fcd5605d8"
SUMMARY = (
    "0-bg grid with several non-bg components (typically all in the "
    "same color, e.g. all 2s, though the rule is color-agnostic). "
    "Each component is either SOLID (cells exactly fill its bbox) or "
    "HOLLOW (≥1 bbox-interior cell is bg). Rule: extract every "
    "non-bg connected component; for each, check if its cells "
    "completely fill its bbox. If solid, recolor to 4. If hollow, "
    "recolor to 8. Output is a fresh grid with each component "
    "appearing in its original cells with the new color."
)

# Rivals: 'output is input' refuted by demos (colors change).
# 'recolor everything to 4' refuted by demos with hollow components
# getting 8. 'recolor everything to 8' refuted by demos with solid
# components getting 4. 'use color 5 for solid' refuted by demos
# showing 4. 'flip the mapping (hollow→4, solid→8)' refuted by demos.
# 'distinguish by size, not hole-ness' refuted by demos with same-size
# solid and hollow getting different colors. 4 demos with multiple "
# components of each type pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "≥1 SOLID component (cells fill its bbox completely)",
    "≥1 HOLLOW component (≥1 bbox-interior cell is bg)",
    "components are separated by ≥1 bg cell (4-conn separation)",
    "all components in the same input color (typically) — the rule's recolor still applies",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blobs", "only_hollow", "only_solid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "9..18"},
    "n_hollow":       {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "n_solid":        {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..3"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        n_hollow_lo, n_hollow_hi = 1, 1
        n_solid_lo, n_solid_hi = 1, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        n_hollow_lo, n_hollow_hi = 2, 3
        n_solid_lo, n_solid_hi = 2, 3
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 15)
        n_hollow_lo, n_hollow_hi = 1, 2
        n_solid_lo, n_solid_hi = 1, 2
    rng = ctx.draw_rng("layout")
    # Use a single input color, but do not use the output label colors 4 or 8:
    # those hide one branch's recoloring (solid->4 or hollow->8).
    color = rng.choice([1, 2, 3, 5, 6, 7, 9])
    n_hollow = rng.randint(n_hollow_lo, n_hollow_hi)
    n_solid = rng.randint(n_solid_lo, n_solid_hi)
    for _attempt in range(80):
        g = full_grid(h, w, 0)
        placed = []
        def _place(r0, c0, bh, bw, hollow):
            if r0 < 0 or c0 < 0 or r0 + bh > h or c0 + bw > w:
                return False
            for (pr, pc, pbh, pbw) in placed:
                if (r0 - (pr + pbh) < 2 and pr - (r0 + bh) < 2 and
                    c0 - (pc + pbw) < 2 and pc - (c0 + pbw) < 2):
                    return False
            if hollow:
                draw_rect_outline(g, r0, c0, bh, bw, color)
            else:
                draw_rect(g, r0, c0, bh, bw, color)
            placed.append((r0, c0, bh, bw))
            return True
        # Place hollow components (≥3×3 so interior exists)
        for _ in range(n_hollow):
            for _ in range(60):
                bh = rng.randint(3, 5); bw = rng.randint(3, 5)
                r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
                if _place(r0, c0, bh, bw, hollow=True):
                    break
        # Place solid components
        for _ in range(n_solid):
            for _ in range(60):
                bh = rng.randint(1, 3); bw = rng.randint(1, 3)
                r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
                if _place(r0, c0, bh, bw, hollow=False):
                    break
        if _solid_hollow_counts(g) == (n_solid, n_hollow):
            return g
    raise ValueError("could not realize solid+hollow recolor layout")


def _solid_hollow_counts(grid):
    solid = hollow = 0
    for comp in _components(grid):
        r1, c1, r2, c2 = comp["bbox"]
        area = (r2 - r1 + 1) * (c2 - c1 + 1)
        if area == len(comp["cells"]):
            solid += 1
        else:
            hollow += 1
    return solid, hollow


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        return g
    if name == "only_hollow":
        for c in range(2, 6): g[2][c] = 4; g[5][c] = 4
        for r in range(2, 6): g[r][2] = 4; g[r][5] = 4
        return g
    if name == "only_solid":
        for r in range(2, 4):
            for c in range(2, 4): g[r][c] = 4
        for r in range(6, 8):
            for c in range(8, 10): g[r][c] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    vals = {v for row in grid for v in row if v != 0}
    if vals & {4, 8}:
        msgs.append("input color must not already be output label 4 or 8")
    if len(vals) != 1:
        msgs.append("default components should use one shared input color")
    solid, hollow = _solid_hollow_counts(grid)
    if solid < 1:
        msgs.append("expected at least one solid component")
    if hollow < 1:
        msgs.append("expected at least one hollow component")
    return msgs
