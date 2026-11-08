"""Generator for a8d7556c — color largest inscribed rectangles inside zero holes.

Rule: nonzero background surrounds 4-connected zero components.
For each zero component of size ≥ 4, find the largest all-zero
axis-aligned rectangle (max area) entirely inside the component.
Paint every cell of every such best-area rectangle with color 2.
Other zero cells and the background remain unchanged.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "c45291fac031"
VERSION = "2.0.1"
TASK_ID = "c45291fac031"
SUMMARY = (
    "A noisy non-zero background (one color, scattered with random 0s) "
    "plus a few rectangular all-0 holes punched in. Rule paints the "
    "MAXIMUM-AREA all-zero rectangle inscribed inside each 4-connected "
    "zero component (size ≥ 4) with color 2; ties (multiple equal "
    "max-area rects in one component) all get painted. Background and "
    "small/non-rectangular zero regions stay."
)

# Rivals: 'output is input' refuted by any demo (≥1 rectangle paints).
# 'paint ALL zero cells with 2' refuted by ≥1 demo with leftover 0s.
# 'paint with bg color' refuted by any demo (always 2). 'paint only
# the bbox of the component' refuted by ≥1 demo where the bbox >
# the inscribed rect (irregular zero region). 3 demos with ≥2 holes
# of different shapes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is a non-zero noise color (typically 5)",
    "≥ 2 distinct rectangular all-0 holes are present",
    "each hole component has ≥ 4 cells (so it can hold a 2x2 rect)",
]

AXES = {
    "grid_h":     {"type": "int", "default": "rng 12..16", "valid": "10..22"},
    "grid_w":     {"type": "int", "default": "rng 14..18", "valid": "12..24"},
    "bg_color":   {"type": "color", "default": "rng 4|5|8", "valid": "1..9"},
    "n_holes":    {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "noise_rate": {"type": "float", "default": "rng 0.25..0.45", "valid": "0..0.5"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(10, 13); w = rng.randint(12, 16)
        n_holes = rng.randint(1, 2); noise_rate = rng.uniform(0.2, 0.35)
    elif difficulty == "hard":
        h = rng.randint(16, 22); w = rng.randint(18, 24)
        n_holes = rng.randint(4, 6); noise_rate = rng.uniform(0.35, 0.5)
    else:
        h = rng.randint(13, 17); w = rng.randint(14, 19)
        n_holes = rng.randint(2, 4); noise_rate = rng.uniform(0.25, 0.45)

    bg = rng.choice([4, 5, 8])
    g = full_grid(h, w, bg)
    # Add bg-noise: random 0-cells scattered in the bg.
    for r in range(h):
        for c in range(w):
            if rng.random() < noise_rate:
                g[r][c] = 0

    # Punch in n_holes rectangular all-zero holes with 1-cell buffer.
    placed_boxes = []
    for _ in range(n_holes):
        for attempt in range(60):
            rh = rng.randint(2, max(2, h // 4))
            rw = rng.randint(3, max(3, w // 4))
            r0 = rng.randint(1, h - rh - 1)
            c0 = rng.randint(1, w - rw - 1)
            # Buffer check: keep a 1-cell separation from prior holes,
            # but allow holes to merge with bg-noise zeros (that's
            # the point — the inscribed rect is what survives).
            collide = False
            for (pr, pc, prh, prw) in placed_boxes:
                if (r0 - 1 <= pr + prh and pr - 1 <= r0 + rh and
                    c0 - 1 <= pc + prw and pc - 1 <= c0 + rw):
                    collide = True; break
            if collide:
                continue
            draw_rect(g, r0, c0, rh, rw, 0)
            placed_boxes.append((r0, c0, rh, rw))
            break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Nonzero background present; >=1 zero region (hole) with >=4 cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    nonzero = sum(grid[r][c] != 0 for r in range(h) for c in range(w))
    zeros = h * w - nonzero
    if nonzero == 0:
        errors.append("grid is all background (no nonzero cells)")
    if zeros < 4:
        errors.append(f"expected >=4 zero cells (holes), found {zeros}")
    return errors
