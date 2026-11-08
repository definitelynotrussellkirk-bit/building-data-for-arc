"""Generator for arc_additional_puzzle_bank_volume21:M143.

Rule: compute the bbox of the red(2) cells and the bbox of the green(3)
cells, intersect them, and output a fresh grid with COLOR 8 painted over
that intersection rectangle (blank if the bboxes don't overlap).

Combinatorial axes: grid size, the intersection rectangle, the red/green
blob extents, and the decoy.
Degenerates: no_overlap, no_red, no_green.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.selfcheck import bbox, components_cells as components

GENERATOR_ID = "c4070aab5660"
VERSION = "2.0.0"  # diversity: random intersection rect + blob extents + decoy + grid (was fixed ~12)
TASK_ID = "c4070aab5660"
SUMMARY = (
    "0-bg grid (size varies). ONE color-2 (red) BLOB and ONE color-3 "
    "(green) BLOB, built as rectangles minus their shared corner so their "
    "BBOXES overlap but their cells do not, plus a color-6 (magenta) "
    "decoy. Rule: intersect the red bbox with the green bbox and output a "
    "fresh grid with COLOR 8 (cyan) over that intersection rectangle. The "
    "grid size, the intersection rectangle, the blob extents and the "
    "decoy all vary freely (was a fixed 2-blob layout, ~12 distinct)."
)

INVARIANTS = [
    "exactly one red(2) blob and one green(3) blob, cells disjoint",
    "their bboxes overlap in a non-empty intersection rectangle",
    "decoration is non-{2,3} cells outside both blobs",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_overlap", "no_red", "no_green")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "overlap_kind":   {"type": "str", "default": "varies", "valid": "varies"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "two_blobs_overlapping",
                       "valid": "two_blobs_overlapping"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "blobs", "valid": "blobs"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_overlap|no_red|no_green"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, ir, er = (8, 11), (10, 13), (1, 2), (1, 2)
    elif difficulty == "hard":
        hr, wr, ir, er = (11, 16), (13, 18), (2, 4), (2, 4)
    else:
        hr, wr, ir, er = (9, 14), (11, 15), (1, 3), (1, 3)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        ih = rng.randint(*ir); iw = rng.randint(*ir)        # intersection size
        eat = rng.randint(*er); eal = rng.randint(*er)      # red extends up/left
        ebb = rng.randint(*er); ebr = rng.randint(*er)      # green extends down/right
        # total A∪B extent (relative): rows [-eat, ih-1+ebb], cols [-eal, iw-1+ebr]
        toth = eat + ih + ebb; totw = eal + iw + ebr
        if toth > h or totw > w:
            continue
        top = rng.randint(0, h - toth); left = rng.randint(0, w - totw)
        # I (intersection) origin in grid
        ir0 = top + eat; ic0 = left + eal
        ir1 = ir0 + ih - 1; ic1 = ic0 + iw - 1
        # A = [ir0-eat, ir1] x [ic0-eal, ic1]; B = [ir0, ir1+ebb] x [ic0, ic1+ebr]
        Aset = {(r, c) for r in range(ir0 - eat, ir1 + 1) for c in range(ic0 - eal, ic1 + 1)}
        Bset = {(r, c) for r in range(ir0, ir1 + ebb + 1) for c in range(ic0, ic1 + ebr + 1)}
        Iset = {(r, c) for r in range(ir0, ir1 + 1) for c in range(ic0, ic1 + 1)}

        g = full_grid(h, w, 0)
        occ = set()
        for (r, c) in Aset - Iset:
            g[r][c] = 2; occ.add((r, c))
        for (r, c) in Bset - Iset:
            g[r][c] = 3; occ.add((r, c))

        # decoy: a few color-6 cells outside A∪B
        AB = Aset | Bset
        for _ in range(rng.randint(1, 3)):
            for _t in range(20):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if (r, c) not in AB and (r, c) not in occ:
                    g[r][c] = 6; occ.add((r, c))
                    break
        return g

    raise ValueError("could not place red/green bbox-intersection instance")


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_overlap":
        paint_at(g, 1, 1, [(0, 0), (1, 0), (0, 1)], 2)
        paint_at(g, 5, 8, [(0, 0), (1, 0), (0, 1)], 3)
        return g
    if name == "no_red":
        paint_at(g, 5, 4, [(0, 0), (0, 1), (1, 0)], 3)
        return g
    if name == "no_green":
        paint_at(g, 3, 3, [(0, 0), (1, 0), (0, 1)], 2)
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    reds = components(grid, colors={2})
    greens = components(grid, colors={3})
    if len(reds) != 1:
        msgs.append(f"expected one red component, found {len(reds)}")
    if len(greens) != 1:
        msgs.append(f"expected one green component, found {len(greens)}")
    if len(reds) == 1 and len(greens) == 1:
        rb = bbox(reds[0]); gb = bbox(greens[0])
        ir1, ic1 = max(rb[0], gb[0]), max(rb[1], gb[1])
        ir2, ic2 = min(rb[2], gb[2]), min(rb[3], gb[3])
        if ir1 > ir2 or ic1 > ic2:
            msgs.append("red/green bounding boxes do not overlap")
        red_cells = set(reds[0]); green_cells = set(greens[0])
        if red_cells & green_cells:
            msgs.append("red and green cells overlap")
    return msgs
