"""Generator for arc_additional_puzzle_bank_volume20:M140 — crop nearest object to red marker.

Rule: among the non-red objects, take the one with the smallest minimum
Manhattan distance to the red(2) marker cell, and output it cropped to its bbox.

The old generator placed a FIXED near object (one L-tromino) and two FIXED far
objects at fixed positions — only the colors varied, so the output was always
the same shape (distinct=6). Now: a RANDOM nearest object (varied shape/size)
placed close to a random marker, plus 1-2 random distractors placed strictly
farther away, so the output shape and dims vary.

Combinatorial axes: the nearest object's shape/size (-> output dims), its
color, the marker position, the distractors, grid size.
Degenerates: no_objects, tie_distance, single_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4fe33a81bf48"
VERSION = "3.0.1"  # distinct=6: rule crops the non-red object NEAREST the red(2) marker. Old gen used a fixed near object + fixed far objects (only colours varied). Now random nearest object (varied shape) near a random marker + farther distractors -> output shape/dims vary.
TASK_ID = "4fe33a81bf48"
SUMMARY = (
    "0-bg grid (size varies) with: a single RED(2) MARKER cell; a NEAREST "
    "object (a random connected polyomino, 3-7 cells, distinct color) placed "
    "close to the marker; and 1-2 DISTRACTOR objects placed strictly farther "
    "from the marker (so the nearest is unique). Rule: among non-red objects, "
    "pick the one with the smallest minimum Manhattan distance to the marker "
    "and output it cropped to its bbox. Output shape/dims = the nearest object."
)

INVARIANTS = [
    "exactly one red(2) marker cell",
    "the nearest non-red object is uniquely closest to the marker",
    "objects are separated distinct components in distinct colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "tie_distance", "single_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..18"},
    "n_distractors":  {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "near_and_far", "valid": "near_and_far"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, n):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for (r, c) in cells]


def _free(g, top, left, cells):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        rr, cc = top + dr, left + dc
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = rr + ddr, cc + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def _mindist(cells, top, left, marker):
    return min(abs(top + dr - marker[0]) + abs(left + dc - marker[1]) for dr, dc in cells)


def _place(g, rng, cells, color, marker, want_near, near_d):
    """Place `cells` such that its min distance to marker is < near_d (near) or
    > near_d (far). Returns the achieved min distance, or None."""
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    best = None
    for _ in range(200):
        top = rng.randint(0, h - sh)
        left = rng.randint(0, w - sw)
        if not _free(g, top, left, cells):
            continue
        d = _mindist(cells, top, left, marker)
        if (want_near and d <= near_d) or (not want_near and d > near_d):
            for dr, dc in cells:
                g[top + dr][left + dc] = color
            return d
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one red(2) marker; >=1 non-red object."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    red_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(red_cells) != 1:
        errs.append(f"expected exactly 1 red(2) marker cell, found {len(red_cells)}")
    has_nonred = any(grid[r][c] not in (0, 2) for r in range(h) for c in range(w))
    if not has_nonred:
        errs.append("no non-red object cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 9, 11); nd = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 13, 18); nd = 2
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 10, 14); nd = rng.randint(1, 2)

    for _outer in range(40):
        g = full_grid(h, w, 0)
        marker = (rng.randint(2, h - 3), rng.randint(2, w - 3))
        g[marker[0]][marker[1]] = 2
        colors = rng.sample([1, 3, 4, 5, 6, 7, 8, 9], 1 + nd)
        near_d = 3
        d_near = _place(g, rng, _rand_poly(rng, rng.randint(3, 7)), colors[0], marker, True, near_d)
        if d_near is None:
            continue
        ok = True
        for col in colors[1:]:
            # distractor must be strictly farther than the nearest object
            if _place(g, rng, _rand_poly(rng, rng.randint(3, 7)), col, marker, False, d_near + 1) is None:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not realize 4fe33 layout")


def _draw_from_degenerate(name, rng):
    rng = rng or __import__("random").Random(0)
    g = full_grid(11, 11, 0)
    g[5][5] = 2
    if name == "no_objects":
        return g
    if name == "single_object":
        for r, c in [(5, 1), (5, 2), (6, 1)]:
            g[r][c] = 4
        return g
    if name == "tie_distance":
        for r, c in [(5, 1), (5, 2)]:
            g[r][c] = 4
        for r, c in [(5, 8), (5, 9)]:
            g[r][c] = 6
        return g
    return g
