"""Generator for 15b:m101 — stamp prototype at all anchors.

Rule: a small non-9 prototype blob + several 9-anchor cells. Output:
empty grid + prototype stamped at each anchor (anchor = top-left of stamp).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_prototype, no_anchors, anchor_oob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.selfcheck import components, bbox

GENERATOR_ID = "70c1f7fc5056"
VERSION = "2.0.2"  # require anchor cell itself to be empty, not just future stamp cells
TASK_ID = "70c1f7fc5056"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with: (a) ONE small "
    "PROTOTYPE BLOB of 2-4 cells in some non-{0, 9} "
    "color, placed at a random position (this is "
    "the SHAPE to be stamped); (b) 1-2 color-9 "
    "(maroon) ANCHOR single cells placed at "
    "positions that have room for the full prototype "
    "stamp to fit in-bounds without overlapping "
    "existing cells. Rule: extract the prototype's "
    "shape cells (the non-9, non-0 connected blob). "
    "Build an EMPTY OUTPUT GRID of the same dims. "
    "For each color-9 ANCHOR, STAMP the prototype's "
    "shape ANCHORED at the anchor's position (with "
    "anchor as the stamp's top-left), painted in "
    "the prototype's original color. Original "
    "prototype + anchors are DISCARDED from output. "
    "Net: anchors become stamp positions; output "
    "is the prototype replicated at each anchor."
)

INVARIANTS = [
    "background is 0",
    "exactly one non-9 prototype blob of size 2-4",
    "1-2 9-anchor single cells, each with room for prototype stamp",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_prototype", "no_anchors", "anchor_oob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "prototype_plus_9_anchors",
                       "valid": "prototype_plus_9_anchors"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
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
    color = rng.choice([2, 3, 4, 5, 6, 7, 8])
    for r, c in template:
        g[r][c] = color
    used |= template
    n_anchors = rng.randint(1, 2)
    for _ in range(n_anchors):
        for _ in range(40):
            ar = rng.randint(0, h - tpl_h)
            ac = rng.randint(0, w - tpl_w)
            stamp = {(ar + (r - rs[0]), ac + (c - cs[0])) for r, c in template}
            if g[ar][ac] != 0 or any(g[rr][cc] != 0 for rr, cc in stamp):
                continue
            g[ar][ac] = 9
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_prototype":
        # 9-anchors but no prototype blob — rule has no shape to stamp.
        g[2][3] = 9; g[6][7] = 9
        return g
    if name == "no_anchors":
        # Prototype but no 9-anchors — rule has no stamp positions.
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 5
        return g
    if name == "anchor_oob":
        # Prototype + anchor placed near corner so the stamp would
        # extend past the grid — rule's full-stamp region is undefined.
        for r, c in [(0, 0), (0, 1), (1, 0)]: g[r][c] = 5
        g[h - 1][w - 1] = 9
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    issues: list[str] = []
    h = len(grid); w = len(grid[0]) if h else 0
    if h < 7 or w < 8:
        issues.append("grid unexpectedly small")
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    if not (1 <= len(anchors) <= 2):
        issues.append(f"expected 1-2 anchors, got {len(anchors)}")
    comps = [comp for comp in components(grid, colors={1,2,3,4,5,6,7,8}, same_color=True)]
    if len(comps) != 1:
        issues.append(f"expected exactly one non-9 prototype component, got {len(comps)}")
        return issues
    comp = comps[0]
    if not (2 <= len(comp["cells"]) <= 4):
        issues.append("prototype size must be 2-4")
    r1, c1, r2, c2 = comp["bbox"]
    th, tw = r2 - r1 + 1, c2 - c1 + 1
    for ar, ac in anchors:
        if ar + th > h or ac + tw > w:
            issues.append("anchor lacks room for full prototype stamp")
    return issues
