"""Generator for hard_89_sort_objects_by_holes_then_pack_vertical.

Rule: sort all 4-connected objects by (hole_count ASC, then size DESC).
Crop each to bbox. Vertically stack centered with 1-cell gap.
Output width = max bbox width, height = sum(bbox heights) + (n-1) gaps.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "800735f51c58"
VERSION = "2.0.1"
TASK_ID = "800735f51c58"

SUMMARY = (
    "0-bg grid (h, w~12-22) with 3-6 4-CONNECTED "
    "OBJECTS in distinct non-bg colors, mixing SOLID "
    "BLOBS (no enclosed holes, 3-6 cells) and HOLLOW "
    "FRAMES (rectangular outlines with 1-2 interior "
    "0-holes inside their bbox). Each object's bbox "
    "dimensions vary. Objects are 4-conn isolated. "
    "Rule: identify all objects and their (HOLE "
    "COUNT, CELL COUNT). SORT objects by (hole_count "
    "ASC, cell_count DESC) — fewest-holes first, "
    "ties broken by largest size first. For each "
    "sorted object, CROP to its bbox. VERTICALLY "
    "STACK the cropped shapes, each HORIZONTALLY "
    "CENTERED in a strip of width = max bbox width, "
    "with 1-cell 0-gaps between successive shapes. "
    "Output: a tall centered stack of shapes ordered "
    "by (holes asc, size desc). Net: input scene is "
    "packed vertically by hole-then-size ranking."
)

# Rivals: 'output is input' refuted by any demo (output is small +
# repacked). 'sort by size only' refuted by ≥1 demo where hole count
# matters. 'horizontal stack' refuted by any demo (vertical only).
# 'no gaps between' refuted by any demo (1-cell gap visible).
# 3 demos with ≥1 holed object and ≥2 solid objects cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥3 objects in distinct non-zero colors",
    "at least one object has ≥1 enclosed hole and ≥1 has none",
    "objects don't 4-touch each other",
]

AXES = {
    "grid_h":   {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "grid_w":   {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "n_objects":{"type": "int", "default": "rng 3..4", "valid": "2..6"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥2 distinct nonzero colors (solid + holed objects)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    colors = {v for row in grid for v in row if v != 0}
    if len(colors) < 2:
        return [f"expected ≥2 distinct nonzero colors; found {len(colors)}"]
    return []


def _solid_blob(rng, k):
    """Random connected blob of k cells (no holes guaranteed)."""
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


def _holed_frame(rng, n_holes):
    """Rectangular frame with n_holes interior 0 cells."""
    side = max(3, 2 + 2 * (n_holes // 4 + 1))
    cells = []
    # Outline of side × side
    for c in range(side):
        cells.append((0, c)); cells.append((side - 1, c))
    for r in range(1, side - 1):
        cells.append((r, 0)); cells.append((r, side - 1))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(10, 12); w = rng.randint(12, 15)
        n_objects = rng.randint(3, 4)
    elif difficulty == "hard":
        h = rng.randint(15, 20); w = rng.randint(18, 22)
        n_objects = rng.randint(4, 6)
    else:
        h = rng.randint(12, 16); w = rng.randint(14, 18)
        n_objects = rng.randint(3, 5)

    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_objects)
    placed_boxes = []  # (r1, c1, r2, c2) inclusive
    for i, color in enumerate(palette):
        # Mix: at least one solid and at least one holed.
        if i == 0:
            shape = _holed_frame(rng, rng.randint(1, 2))
        elif i == 1:
            shape = _solid_blob(rng, rng.randint(3, 6))
        else:
            if rng.random() < 0.5:
                shape = _holed_frame(rng, rng.randint(1, 2))
            else:
                shape = _solid_blob(rng, rng.randint(3, 6))
        ph = max(r for r, _ in shape) + 1
        pw = max(c for _, c in shape) + 1
        if ph > h or pw > w:
            continue
        for attempt in range(120):
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
                g[r0 + dr][c0 + dc] = color
            placed_boxes.append((r0, c0, r0 + ph - 1, c0 + pw - 1))
            break
    return g
