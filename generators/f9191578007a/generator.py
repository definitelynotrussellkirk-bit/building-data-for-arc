"""Generator for arc_puzzle_bank_21_set20_bundle:medium_p06 — sort components and gallery-top pack.

Rule: collect all 4-connected components. Sort by (cell_count ASC,
then bbox height ASC, then bbox width ASC, then color ASC). Crop
each to its bbox. Pack the crops left-to-right top-aligned with 1-
cell 0-gaps between. Output height = max bbox height, width = sum
bbox widths + (n-1) gaps.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f9191578007a"
VERSION = "1.3.0"  # bigger grids + more objects (up to 7) + larger blobs on the existing distinct-signature design
TASK_ID = "f9191578007a"

SUMMARY = (
    "Several 4-connected colored components on a 0-bg grid with "
    "distinct (size, height, width) signatures. Rule sorts by "
    "(cell_count ASC, bbox height ASC, bbox width ASC, color ASC), "
    "crops each to its tight bbox, then horizontally packs them "
    "top-aligned with 1-cell 0-gaps. Output height = max bbox "
    "height, width = sum widths + (n-1) gaps."
)

# Rivals: 'output is input' refuted by any demo (output is small).
# 'pack bottom-aligned' refuted by any demo (top-aligned is visible).
# 'sort by color first' refuted by demos where size matters more.
# 'no gap between' refuted by any multi-component demo. 3 demos
# with ≥3 components of distinct (size, h, w) cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥3 4-connected non-bg components",
    "components have STRICTLY distinct (size, height, width) tuples",
    "components don't 4-touch each other",
]

AXES = {
    "grid_h":     {"type": "int", "default": "8-11 easy / 11-16 med / 15-22 hard", "valid": "8..24"},
    "grid_w":     {"type": "int", "default": "11-14 easy / 14-19 med / 18-26 hard", "valid": "10..28"},
    "n_objects":  {"type": "int", "default": "3-4 easy / 3-5 med / 4-7 hard", "valid": "2..7"},
}


def _grow_blob(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    minr, minc = min(rs), min(cs)
    return [(r - minr, c - minc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(8, 11); w = rng.randint(11, 14)
        n_objects = rng.randint(3, 4); smax = 7
    elif difficulty == "hard":
        h = rng.randint(15, 22); w = rng.randint(18, 26)
        n_objects = rng.randint(4, 7); smax = 9
    else:
        h = rng.randint(11, 16); w = rng.randint(14, 19)
        n_objects = rng.randint(3, 5); smax = 8

    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_objects)
    placed_boxes = []
    # Generate shapes with strictly distinct (size, h, w) signatures.
    used_signatures: set = set()
    placed_count = 0
    attempts = 0
    while placed_count < n_objects and attempts < 600:
        attempts += 1
        size = rng.randint(2, smax)
        shape = _grow_blob(rng, size)
        ph = max(r for r, _ in shape) + 1
        pw = max(c for _, c in shape) + 1
        sig = (size, ph, pw)
        if sig in used_signatures:
            continue
        if ph > h or pw > w:
            continue
        # Try to place.
        ok = False
        for _attempt in range(80):
            r0 = rng.randint(0, h - ph)
            c0 = rng.randint(0, w - pw)
            collide = False
            for (pr1, pc1, pr2, pc2) in placed_boxes:
                if (r0 - 1 <= pr2 and pr1 <= r0 + ph and
                    c0 - 1 <= pc2 and pc1 <= c0 + pw):
                    collide = True; break
            if collide:
                continue
            color = palette[placed_count]
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            placed_boxes.append((r0, c0, r0 + ph - 1, c0 + pw - 1))
            used_signatures.add(sig)
            placed_count += 1
            ok = True
            break
        if not ok:
            continue
    return g
