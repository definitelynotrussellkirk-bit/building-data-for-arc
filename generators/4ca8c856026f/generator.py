"""Generator for 4ca8c856026f — copy a room's color-3 pattern into the color-2 room.

Rule (verified from canonical Racket): walls are colors {1,7,9}; the non-wall
cells form ROOMS (4-connected regions). The SOURCE room is the one containing
color 3 but not color 2; the TARGET room is the one containing color 2. The
output keeps only the walls and paints the source room's color-3 pattern
(relative to the source room's top-left) into the target room (relative to the
target's top-left), in color 8.

The previous body was the generic "6 panels, find the matching pair" template,
which never built walls or rooms, so the rule's `(first (filter ...))` for the
source/target rooms returned #f and crashed (rule_smoke 8/12). This 2.2.0
rewrite CONSTRUCTS valid inputs: a wall splits the grid into two rooms, one gets
a small color-3 pattern (the source), the other a color-2 marker (the target);
an optional color-7 door sits in the wall.

Axes: grid size, wall position, 3-pattern, marker, door.
Degenerates: single_cell_pattern, no_door, big_pattern.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4ca8c856026f"
VERSION = "2.2.1"  # REWRITE: room copy (was find-pair template; crashed the rule 8/12 on missing source/target rooms)
TASK_ID = "4ca8c856026f"

SUMMARY = (
    "A color-1 wall splits the grid into two rooms; the source room holds a "
    "small color-3 pattern, the target room a color-2 marker. Rule: copy the "
    "source's 3-pattern into the target room as color 8, keeping the walls. "
    "Grid size, wall, pattern, marker and an optional color-7 door vary."
)

INVARIANTS = [
    "walls are color 1 (plus an optional color-7 door); they split the grid into two rooms",
    "exactly one room has color 3 and no color 2 (source); the other has color 2 (target)",
    "the source 3-pattern fits inside its room",
]

DEGENERATE_TEXTURES = ("single_cell_pattern", "no_door", "big_pattern")
HELPFUL_TEXTURES = ("vertical", "doored", "swapped")

AXES = {
    "grid_h":       {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "grid_w":       {"type": "int", "default": "rng 10..13", "valid": "10..16"},
    "pattern_size": {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "door":         {"type": "int", "default": "rng 0..1", "valid": "0|1"},
    "texture":      {"type": "str", "default": "rng helpful",
                     "valid": "vertical|doored|swapped|single_cell_pattern|no_door|big_pattern"},
}


def _walk(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}; tries = 0
    while len(cells) < k and tries < 50:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nc = (r + dr, c + dc)
        if nc not in seen:
            cells.append(nc); seen.add(nc)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _build(rng, h, w, k, door):
    g = full_grid(h, w, 0)
    wc = max(3, min(w - 4, rng.randint(w // 2 - 1, w // 2 + 1)))   # >=3 cols each side
    for r in range(h):
        g[r][wc] = 1
    if door:
        g[rng.randint(0, h - 1)][wc] = 7

    shape = _walk(rng, k)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    left_is_source = (rng.randint(0, 1) == 0)
    src_lo, src_hi = (0, wc - 1) if left_is_source else (wc + 1, w - 1)
    tgt_lo, tgt_hi = (wc + 1, w - 1) if left_is_source else (0, wc - 1)

    sr = rng.randint(0, max(0, h - sh))
    sc = rng.randint(src_lo, max(src_lo, src_hi - sw + 1))
    for (dr, dc) in shape:
        if 0 <= sr + dr < h and src_lo <= sc + dc <= src_hi:
            g[sr + dr][sc + dc] = 3
    g[rng.randint(0, h - 1)][rng.randint(tgt_lo, tgt_hi)] = 2
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        sz_lo, sz_hi, k_lo, k_hi = 8, 10, 2, 3
    elif difficulty == "hard":
        sz_lo, sz_hi, k_lo, k_hi = 12, 16, 4, 6
    else:
        sz_lo, sz_hi, k_lo, k_hi = 10, 13, 3, 4

    h = ctx.draw_int("grid_h", sz_lo, sz_hi)
    w = ctx.draw_int("grid_w", max(sz_lo, 10), sz_hi)
    k = ctx.draw_int("pattern_size", k_lo, k_hi)
    door = (ctx.draw_int("door", 0, 1) == 1)
    return _build(rng, h, w, k, door)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify room-copy source/target invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    flat = [v for row in grid for v in row]
    if 1 not in flat and 7 not in flat:
        problems.append("no wall cells (color 1 or 7) found")
    if flat.count(2) != 1:
        problems.append(f"expected exactly 1 color-2 target marker, found {flat.count(2)}")
    if flat.count(3) < 1:
        problems.append("no color-3 source pattern cells found")
    return problems


def _draw_from_degenerate(name, rng):
    if name == "single_cell_pattern":
        return _build(rng, 10, 12, 1, door=True)
    if name == "no_door":
        return _build(rng, 11, 13, 3, door=False)
    return _build(rng, 14, 16, 6, door=True)   # big_pattern
