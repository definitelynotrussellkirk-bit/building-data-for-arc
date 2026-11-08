"""Generator for arc_puzzle_bank_21_set4:S4_H3 (task 033fb9bdf479).

THE RULE (what a solver must learn to see):
  k = the number of magenta(6) cells anywhere on the grid. Among the
  green(3) objects, find those with exactly k enclosed holes; recolor
  the first (bbox order) to orange(7). No match -> grid unchanged.

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - k = 0 reachable: NO markers at all -> the SOLID (0-hole) green
    object is the target (previously k was always 1-2)
  - markers scattered anywhere (were always in row 0)
  - frame sizes vary: 1-hole rings 3x3..4x6, 2-hole double-rings of
    varied width, solid blobs 2x2..3x4 (was one fixed shape each)
  - no_target boards: no green object has k holes -> identity

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - no_target  marker count matches nothing: unchanged output
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "033fb9bdf479"
VERSION = "3.0.1"
TASK_ID = "033fb9bdf479"

SUMMARY = (
    "0-bg grid with k magenta(6) markers scattered anywhere (k=0-2) "
    "and 3 green objects of 0/1/2 enclosed holes in varied sizes; "
    "rule recolors the green object with exactly k holes to orange. "
    "k=0 selects the solid object; no-match boards stay unchanged."
)

# Rivals: 'markers must be in row 0' refuted by scattered markers.
# 'pick the biggest/smallest green' refuted by hole-count selection.
# 'k=0 means nothing happens' refuted by k=0 boards recoloring the
# solid object. 'always one fixed frame shape' refuted by size
# variety. 4 demos spanning k=0,1,2.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly k magenta cells (k = 0..2), anywhere on the grid",
    "exactly 3 green objects with 0, 1, and 2 enclosed holes",
    "exactly one green object has k holes (helpful path)",
    "objects bbox-separated with 1-cell buffers",
]

DEGENERATE_TEXTURES = ("no_target",)
HELPFUL_TEXTURES = ("plain",)

AXES = {
    "height":     {"type": "int", "default": "rng 10..13", "valid": "9..14"},
    "width":      {"type": "int", "default": "rng 15..17", "valid": "13..18"},
    "hole_count": {"type": "int", "default": "rng 0..2", "valid": "0..2",
                   "doc": "Marker count = target hole count (0 = solid wins)."},
    "texture":    {"type": "str", "default": "plain", "valid": "plain|no_target",
                   "doc": "no_target removes the matching object (identity)."},
}


def _ring_cells(rh, rw):
    """Hollow rectangle outline: exactly 1 enclosed hole."""
    return [(r, c) for r in range(rh) for c in range(rw)
            if r in (0, rh - 1) or c in (0, rw - 1)]


def _double_ring_cells(rh, half_w):
    """Two rings sharing a wall: exactly 2 enclosed holes."""
    cells = set(_ring_cells(rh, half_w))
    for r, c in _ring_cells(rh, half_w):
        cells.add((r, c + half_w - 1))
    return sorted(cells)


def _solid_cells(rng):
    sh = rng.randint(2, 3)
    sw = rng.randint(2, 4)
    return [(r, c) for r in range(sh) for c in range(sw)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    h = ctx.draw_int("height", 10, 13)
    w = ctx.draw_int("width", 15, 17)
    hole_count = int(overrides.get("hole_count", ctx.draw_int("hole_count", 0, 2)))
    rng = ctx.draw_rng("layout")

    for _outer in range(60):
        g = full_grid(h, w, 0)
        # varied frame shapes (was: one fixed shape per hole count)
        ring_h = rng.randint(3, 4)
        ring_w = rng.randint(3, 6)
        dbl_h = rng.randint(3, 4)
        dbl_half = rng.randint(3, 4)
        shapes = [
            (1, _ring_cells(ring_h, ring_w)),
            (2, _double_ring_cells(dbl_h, dbl_half)),
            (0, _solid_cells(rng)),
        ]
        if texture == "no_target":
            # remove the object whose hole count equals k: no match
            shapes = [(holes, cells) for holes, cells in shapes
                      if holes != hole_count]
        rng.shuffle(shapes)

        used = set()
        ok = True
        for _holes, cells in shapes:
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            placed = False
            for _try in range(80):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                if any((r0 + dr, c0 + dc) in used
                       for dr in range(-1, sh + 1)
                       for dc in range(-1, sw + 1)):
                    continue
                for r, c in cells:
                    g[r0 + r][c0 + c] = 3
                for dr in range(sh):
                    for dc in range(sw):
                        used.add((r0 + dr, c0 + dc))
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            continue

        # markers anywhere on free cells (were always in row 0)
        placed_markers = 0
        for _try in range(80):
            if placed_markers >= hole_count:
                break
            r, c = rng.randrange(h), rng.randrange(w)
            if g[r][c] == 0 and all(
                    g[rr][cc] != 3
                    for rr in range(max(0, r - 1), min(h, r + 2))
                    for cc in range(max(0, c - 1), min(w, c + 2))):
                g[r][c] = 6
                placed_markers += 1
        if placed_markers == hole_count:
            return g
    raise ValueError("could not realize hole-count board")


def _selfcheck_holes(comp) -> int:
    cells = set(comp["cells"])
    r1, c1, r2, c2 = comp["bbox"]
    # Flood background in a padded bbox and count interior zero regions not connected to the outside.
    zeros = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1) if (r, c) not in cells}
    seen: set[tuple[int, int]] = set()
    holes = 0
    for start in list(zeros):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        touches_edge = False
        while stack:
            r, c = stack.pop()
            if r in (r1, r2) or c in (c1, c2):
                touches_edge = True
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                nb = (r + dr, c + dc)
                if nb in zeros and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        if not touches_edge:
            holes += 1
    return holes


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    issues: list[str] = []
    markers = sum(1 for row in grid for v in row if v == 6)
    if markers not in (0, 1, 2):
        issues.append(f"marker count must be 0..2, got {markers}")
    greens = components(grid, colors={3}, same_color=True)
    if len(greens) != 3:
        issues.append(f"expected 3 green objects, got {len(greens)}")
        return issues
    holes = sorted(_selfcheck_holes(comp) for comp in greens)
    if holes != [0, 1, 2]:
        issues.append(f"expected one 0-hole, one 1-hole, one 2-hole object, got {holes}")
    if holes.count(markers) != 1:
        issues.append("marker count should select exactly one green object")
    return issues
