"""Generator for arc_puzzle_bank_21_set8:hard_h18.

Places colored source objects on the left and gray transformed slot
silhouettes on the right. The rule recolors each slot by its matching
source object under a dihedral transform.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3ede374cd992"
VERSION = "1.1.1"
TASK_ID = "3ede374cd992"

SUMMARY = "Colored source shapes match gray slot silhouettes under transforms."

INVARIANTS = [
    "background is 0",
    "slot silhouettes use gray 8",
    "each slot matches exactly one colored source under rotation/reflection",
]

AXES = {
    "grid_h": {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "rng 13..16", "valid": "12..18"},
    "n_pairs": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
}

SHAPES = [
    [(0, 0), (1, 0), (2, 0)],
    [(0, 0), (1, 0), (1, 1), (1, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=1 color-8 slot silhouette and >=1 non-{0,8} colored source cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    gray_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    colored_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)]
    if not gray_cells:
        errs.append("no color-8 slot silhouette cells found")
    if not colored_cells:
        errs.append("no non-{0,8} colored source cells found")
    return errs


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _dims(cells):
    return (
        max(r for r, _ in cells) + 1,
        max(c for _, c in cells) + 1,
    )


def _transform(cells, turn, flip):
    cells = _normalize(cells)
    h, w = _dims(cells)
    if flip:
        cells = [(r, w - 1 - c) for r, c in cells]
    for _ in range(turn % 4):
        h, w = _dims(cells)
        cells = [(c, h - 1 - r) for r, c in cells]
    return _normalize(cells)


def _paint(g, cells, top, left, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _free(g, cells, top, left):
    h, w = len(g), len(g[0])
    for r, c in cells:
        rr, cc = top + r, left + c
        if rr < 0 or cc < 0 or rr >= h or cc >= w or g[rr][cc] != 0:
            return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    n_pairs = ctx.draw_int("n_pairs", 2, 3)
    h = ctx.draw_int("grid_h", max(9, n_pairs * 4), max(10, n_pairs * 4 + 1))
    w = ctx.draw_int("grid_w", 13, 16)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    shapes = SHAPES[:]
    rng.shuffle(shapes)
    colors = rng.sample([2, 3, 4, 5, 6, 7, 9], n_pairs)
    left_limit = max(5, w // 2 - 1)
    right_start = w // 2 + 1

    for idx, (shape, color) in enumerate(zip(shapes[:n_pairs], colors)):
        source = _normalize(shape)
        slot = _transform(shape, rng.randint(0, 3), rng.choice([True, False]))
        source_h, source_w = _dims(source)
        slot_h, slot_w = _dims(slot)
        band_top = 1 + idx * 4

        source_top = band_top + rng.randint(0, max(0, 3 - source_h))
        source_left = rng.randint(1, max(1, left_limit - source_w))
        slot_top = band_top + rng.randint(0, max(0, 3 - slot_h))
        slot_left = rng.randint(right_start, max(right_start, w - slot_w - 1))

        if not _free(g, source, source_top, source_left):
            raise ValueError("source placement collided")
        if not _free(g, slot, slot_top, slot_left):
            raise ValueError("slot placement collided")
        _paint(g, source, source_top, source_left, color)
        _paint(g, slot, slot_top, slot_left, 8)

    return g
