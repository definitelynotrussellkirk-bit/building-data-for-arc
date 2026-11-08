"""Generator for v1_e_m_h_keys:M1 — recolor smallest object to 8.

Rule: find all 4-connected non-bg objects. Pick the one with the
fewest cells (ties broken by lex order of bbox tuple). Recolor that
object to 8. Everything else passes through unchanged.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "40f42915c6c4"
VERSION = "1.2.1"
TASK_ID = "40f42915c6c4"
SUMMARY = (
    "Several 4-connected non-bg colored objects of distinct sizes "
    "(no two share the same cell count). Rule recolors the smallest "
    "object to color 8, leaving every other cell unchanged."
)

# Rivals: 'output is input' refuted by any demo (smallest recolors).
# 'recolor by color, not size' refuted by demos where the smallest
# obj has a distinct color and demos where multiple use the same
# original color. 'recolor lines only' refuted by demos where the
# smallest object is not a line. 'recolor largest' refuted by ≥1
# demo. 3 demos with ≥3 objects of strictly distinct sizes cover.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 4-connected non-bg objects with STRICTLY distinct cell counts",
    "object colors are non-bg and non-8 in the input",
    "objects don't touch each other (1-cell buffer)",
]

AXES = {
    "grid_h": {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "n_objects": {"type": "int", "default": "rng 2..4", "valid": "2..6"},
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


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the executable invariant: >=2 objects, no input 8, strictly distinct sizes."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs: list[str] = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    comps = _components(grid)
    if any(color == 8 for color, _ in comps):
        errs.append("color-8 present in input (reserved for smallest-object recolor)")
    if len(comps) < 2:
        errs.append(f"expected >=2 non-bg objects, got {len(comps)}")
    sizes = [len(cells) for _color, cells in comps]
    if len(set(sizes)) != len(sizes):
        errs.append(f"object sizes must be strictly distinct, got {sorted(sizes)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(6, 8); w = rng.randint(8, 10)
        n_objects = rng.randint(2, 3)
        size_pool = [2, 3, 4, 5]
    elif difficulty == "hard":
        h = rng.randint(10, 14); w = rng.randint(12, 16)
        n_objects = rng.randint(4, 6)
        size_pool = list(range(2, 10))
    else:
        h = rng.randint(7, 10); w = rng.randint(9, 12)
        n_objects = rng.randint(3, 4)
        size_pool = list(range(2, 8))

    # Strictly distinct sizes: sample n_objects distinct ints.
    n_objects = min(n_objects, len(size_pool))
    sizes = rng.sample(size_pool, n_objects)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n_objects)  # exclude 8

    g = full_grid(h, w, 0)
    placed_boxes = []  # (r1, c1, r2, c2) inclusive bbox
    for size, color in zip(sizes, palette):
        blob = _grow_blob(rng, size)
        ph = max(r for r, _ in blob) + 1
        pw = max(c for _, c in blob) + 1
        for attempt in range(100):
            r0 = rng.randint(0, h - ph)
            c0 = rng.randint(0, w - pw)
            # 1-cell buffer collision check.
            collide = False
            for (pr1, pc1, pr2, pc2) in placed_boxes:
                if (r0 - 1 <= pr2 and pr1 <= r0 + ph and
                    c0 - 1 <= pc2 and pc1 <= c0 + pw):
                    collide = True; break
            if collide:
                continue
            for dr, dc in blob:
                g[r0 + dr][c0 + dc] = color
            placed_boxes.append((r0, c0, r0 + ph - 1, c0 + pw - 1))
            break
    return g
