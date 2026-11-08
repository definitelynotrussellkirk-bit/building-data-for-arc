"""Generator for arc_additional_puzzle_bank_volume17:M115 — recolor 2nd largest color-2 blob.

Rule: collect all color-2 4-connected components. Sort by (cell count
DESC, top-left ASC). Recolor the SECOND blob's cells to color 8.
Largest blob and any 3rd+ blobs stay 2.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components, components_have_clearance

GENERATOR_ID = "d292e3214bb1"
VERSION = "1.2.0"
TASK_ID = "d292e3214bb1"
SUMMARY = (
    "≥3 4-connected color-2 (red) blobs of strictly distinct sizes, "
    "plus optional non-2 decoration cells. Rule sorts the 2-blobs "
    "by (cell count DESC, then top-left ASC) and recolors the second "
    "blob's cells to color 8. Other blobs (largest, 3rd+) stay 2."
)

# Rivals: 'output is input' refuted by demos (2nd blob recolors).
# 'recolor largest' refuted by demos (largest stays 2). 'recolor
# smallest' refuted by demos (smallest stays 2). 'recolor all 2s'
# refuted by demos (only 2nd changes). 3 demos with ≥3 distinct-
# size blobs cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥3 color-2 4-connected components with strictly distinct sizes",
    "components don't 4-touch each other",
    "optional non-{0,2,8} decoration cells",
]

AXES = {
    "grid_h":     {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w":     {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "n_blobs":    {"type": "int", "default": "rng 3..4", "valid": "3..6"},
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
        h = rng.randint(8, 10); w = rng.randint(10, 12)
        n_blobs = 3; size_pool = [2, 3, 4, 5]
    elif difficulty == "hard":
        h = rng.randint(13, 17); w = rng.randint(15, 20)
        n_blobs = rng.randint(4, 6); size_pool = list(range(2, 9))
    else:
        h = rng.randint(10, 12); w = rng.randint(12, 14)
        n_blobs = rng.randint(3, 4); size_pool = list(range(2, 7))

    g = full_grid(h, w, 0)
    sizes = rng.sample(size_pool, n_blobs)
    placed_boxes = []
    for size in sizes:
        shape = _grow_blob(rng, size)
        ph = max(r for r, _ in shape) + 1
        pw = max(c for _, c in shape) + 1
        if ph > h or pw > w:
            continue
        for _attempt in range(120):
            r0 = rng.randint(0, h - ph)
            c0 = rng.randint(0, w - pw)
            collide = False
            for (pr1, pc1, pr2, pc2) in placed_boxes:
                if (r0 - 1 <= pr2 and pr1 <= r0 + ph and
                    c0 - 1 <= pc2 and pc1 <= c0 + pw):
                    collide = True; break
            if collide:
                continue
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = 2
            placed_boxes.append((r0, c0, r0 + ph - 1, c0 + pw - 1))
            break
    # Optional decoration in a non-{2, 8} color
    if rng.random() < 0.6:
        for _ in range(20):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] == 0:
                g[r][c] = rng.choice([1, 3, 4, 5, 6, 7, 9])
                break
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for recoloring the second-largest red blob."""
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid is empty or not rectangular"]
    comps2 = components(grid, colors={2})
    sizes = [len(c["cells"]) for c in comps2]
    if len(comps2) < 3:
        errs.append(f"expected at least 3 color-2 components, got {len(comps2)}")
    if len(set(sizes)) != len(sizes):
        errs.append(f"color-2 component sizes are not strictly distinct: {sizes}")
    if not components_have_clearance(grid, comps2, diagonal=False):
        errs.append("color-2 blobs should not 4-touch each other")
    bad_decor = sorted({v for row in grid for v in row if v not in (0, 2) and not (1 <= v <= 9)})
    if bad_decor:
        errs.append(f"invalid decoration colors: {bad_decor}")
    if any(v == 8 for row in grid for v in row):
        errs.append("input should not already contain output color 8")
    return errs
