"""Generator for arc_puzzle_bank_21_set7:hard_g17 -- ray-cast precedence overlay.

Rule (canonical): row 0 is a LEGEND (colour precedence order). The field (rows
1+) has color-5 BLOCKERS and EMITTER cells on its border (non-{0,5} colours on
the field's top/bottom rows and left/right columns). Each emitter shoots a ray
INWARD in its colour until it hits a blocker or the edge. Where rays overlap, the
colour with higher legend precedence wins. Output = blockers + emitters + rays.

(Previous generator was the WRONG task: it scattered random motifs with no
legend/emitter/blocker structure, so the rule found no emitters and produced a
blank output for many seeds. This builds the real field-border-emitter layout.)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "311ebe067559"
RULE_HASH = "e1a8e7766b84"  # canonical rule this generator was written against
VERSION = "3.0.1"  # WRONG-TASK fix: rule is a ray-cast precedence overlay (row0 legend, field-border emitters shoot rays inward, 5-blockers, precedence overlap). Gen scattered random motifs -> no emitters -> blank output for many seeds. Now builds the real legend+emitter+blocker layout.
TASK_ID = "311ebe067559"

SUMMARY = (
    "Row 0 is a color LEGEND (precedence order). The field (rows 1+) has EMITTER "
    "cells on its border (non-{0,5} colors on the field's top/bottom rows and "
    "left/right columns) and color-5 BLOCKERS inside. Rule: each emitter shoots a "
    "ray inward in its color until it hits a blocker or the edge; where rays "
    "overlap, the higher-precedence color (per the legend) wins. Output = blockers "
    "+ emitters + rays."
)

INVARIANTS = [
    "row 0 is a non-zero color legend (precedence)",
    "field-border cells (non-{0,5}) are emitters that cast inward rays",
    "color-5 cells are blockers; >=1 emitter so the output is non-empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Row 0 is a non-zero legend (precedence); body (rows 1+) has ≥1 emitter on border."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Row 0: legend (at least one non-zero cell)
    legend = [grid[0][c] for c in range(w) if grid[0][c] != 0]
    if not legend:
        errs.append("row 0 has no legend colors")
    if h < 2:
        errs.append("grid too short (need rows 1+ for field)")
        return errs
    # Body border emitters: non-{0,5} cells on border of rows 1..h-1
    body_h = h - 1
    emitters = []
    for c in range(w):
        if grid[1][c] not in (0, 5):
            emitters.append((1, c))
        if body_h > 1 and grid[h-1][c] not in (0, 5):
            emitters.append((h-1, c))
    for r in range(1, h):
        if grid[r][0] not in (0, 5):
            emitters.append((r, 0))
        if grid[r][w-1] not in (0, 5):
            emitters.append((r, w-1))
    if not emitters:
        errs.append("no emitter cells on body border (non-{0,5} on rows 1+/col 0/col w-1)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # row 0 = legend (precedence); field (rows 1+) has border EMITTERS that shoot
    # rays inward, stopped by color-5 blockers, overlaps resolved by precedence.
    if difficulty == "easy":
        fh = rng.randint(5, 7); fw = rng.randint(6, 8); n_emit = rng.randint(2, 4); n_block = rng.randint(0, 2)
    elif difficulty == "hard":
        fh = rng.randint(8, 12); fw = rng.randint(9, 14); n_emit = rng.randint(5, 9); n_block = rng.randint(2, 5)
    else:
        fh = rng.randint(6, 9); fw = rng.randint(7, 11); n_emit = rng.randint(3, 6); n_block = rng.randint(1, 3)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], rng.randint(3, 5))   # emitter colours (exclude 5)
    fw = max(fw, len(palette))
    H, W = fh + 1, fw
    g = full_grid(H, W, 0)
    legend = palette[:]; rng.shuffle(legend)
    for i, col in enumerate(legend):
        g[0][i] = col                                  # precedence legend in row 0
    # emitter slots on the field border (grid coords): field rows are grid 1..H-1
    border = ([(1, c) for c in range(fw)] + [(H - 1, c) for c in range(fw)] +
              [(r, 0) for r in range(2, H - 1)] + [(r, fw - 1) for r in range(2, H - 1)])
    rng.shuffle(border)
    placed = 0
    for (r, c) in border:
        if placed >= n_emit:
            break
        if g[r][c] == 0:
            g[r][c] = rng.choice(palette); placed += 1
    # color-5 blockers inside the field interior
    interior = [(r, c) for r in range(2, H - 1) for c in range(1, fw - 1)]
    rng.shuffle(interior)
    for (r, c) in interior[:n_block]:
        if g[r][c] == 0:
            g[r][c] = 5
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
