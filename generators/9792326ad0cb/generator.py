"""Generator for arc_puzzle_bank_21_set5_s:S5_M6 — template stamp at anchors.

Rule: largest 3-blob = template. Each 4-cell is an anchor. Output:
empty grid + template (in 8) stamped at each anchor.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_anchors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_anchors, anchor_overlaps_template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "9792326ad0cb"
VERSION = "2.0.1"
TASK_ID = "9792326ad0cb"
SUMMARY = (
    "0-bg grid (h~9-11, w~"
    "10-13) with: (a) ONE "
    "3-BLOB TEMPLATE — a "
    "connected blob of "
    "COLOR 3 (size 2-4) "
    "grown randomly and "
    "placed at a non-"
    "touching position; "
    "(b) 1-3 COLOR-4 "
    "SINGLETON ANCHORS — "
    "single 4-cells at "
    "positions where the "
    "TEMPLATE'S BBOX would "
    "fit without going "
    "out of bounds or "
    "overlapping the "
    "template. Rule "
    "(STAMP TEMPLATE (IN "
    "COLOR 8) AT EACH "
    "4-ANCHOR ON A FRESH "
    "GRID): identify the "
    "TEMPLATE (largest "
    "COLOR-3 connected "
    "component) and its "
    "NORMALIZED SHAPE "
    "(cells with min "
    "row/col offsets = 0)"
    ". PRODUCE a NEW "
    "BLANK h × w GRID. "
    "For EACH ANCHOR "
    "(COLOR-4 cell) at "
    "(ar, ac): STAMP the "
    "template's shape "
    "with the anchor as "
    "top-left corner, "
    "painting each "
    "stamped cell with "
    "COLOR 8 (cyan). The "
    "original template "
    "and anchors are "
    "discarded. Net: a "
    "fresh canvas with "
    "cyan copies of the "
    "template at each "
    "anchor's location."
)

INVARIANTS = [
    "background is 0",
    "exactly one 3-blob (template) of size 2-4",
    "1-3 single 4-cells that have room for the stamp without OOB",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_anchors", "anchor_overlaps_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_anchors":      {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "3blob_template_with_4anchors",
                       "valid": "3blob_template_with_4anchors"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 color-3 connected component; ≥1 color-4 cell (anchor)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    # Count color-3 components
    seen = set()
    comps3 = 0
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) in seen or grid[r0][c0] != 3:
                continue
            stack = [(r0, c0)]; seen.add((r0, c0))
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 3:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps3 += 1
    has_four = any(grid[r][c] == 4 for r in range(h) for c in range(w))
    errs = []
    if comps3 != 1:
        errs.append(f"expected exactly 1 color-3 component; found {comps3}")
    if not has_four:
        errs.append("no color-4 anchor cells")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    template = grow_blob(rng, h, w, used, rng.randint(2, 4), max_attempts=80)
    if template is None:
        return g
    rs = sorted(r for r, _ in template)
    cs = sorted(c for _, c in template)
    tpl_h = rs[-1] - rs[0] + 1
    tpl_w = cs[-1] - cs[0] + 1
    for r, c in template:
        g[r][c] = 3
    used |= template
    for _ in range(rng.randint(1, 3)):
        for _ in range(40):
            ar = rng.randint(0, h - tpl_h)
            ac = rng.randint(0, w - tpl_w)
            stamped = {(ar + (r - rs[0]), ac + (c - cs[0])) for r, c in template}
            if any(g[r][c] != 0 for r, c in stamped):
                continue
            g[ar][ac] = 4
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_template":
        # 4-anchors but no 3-blob → no shape to stamp
        g[3][3] = 4; g[6][7] = 4
        return g
    if name == "no_anchors":
        # 3-template but no 4-anchors → nothing to stamp at
        for r, c in [(2, 2), (2, 3), (3, 3)]: g[r][c] = 3
        return g
    if name == "anchor_overlaps_template":
        # 4-anchor inside template footprint → ambiguous stamp position
        for r, c in [(2, 2), (2, 3), (3, 3)]: g[r][c] = 3
        g[3][2] = 4  # inside the template's bbox
        return g
    return g
