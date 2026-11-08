"""Generator for a1c55d0f7af9 — slide objects away from nearest 9 anchor.

Rule: bg = 7. Multiple color-9 anchor cells. Other objects in non-{7, 9}
colors. For each object: find the nearest 9 cell (Manhattan). Compute
dominant offset direction (1 of 4 cardinals). Slide the object in that
direction until it hits the grid edge. Anchors and bg preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a1c55d0f7af9"
VERSION = "2.0.2"
TASK_ID = "a1c55d0f7af9"
SUMMARY = (
    "Grid with bg = color 7. Contains: (a) 1-3 ANCHOR cells (color 9); "
    "(b) 2-5 OBJECTS, each a small connected blob (2-4 cells) in some "
    "non-{7, 9} color. Anchors and objects are separated (≥1-cell "
    "buffer). Rule: for each object O, find the nearest color-9 anchor "
    "cell (Manhattan). Compute dominant direction (whichever axis has "
    "larger offset; ties go to row). Slide O entirely until its bounding "
    "box touches the grid edge in that direction. Anchors stay put; bg "
    "preserved."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is color 7",
    "1-3 color-9 anchor cells",
    "2-5 objects in distinct non-{7, 9} colors, each 2-4 cells",
    "each object has a strictly nearest anchor (no tie)",
    "the dominant axis offset is unambiguous (abs(dr) != abs(dc))",
    "objects placed with buffer so sliding doesn't collide",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard. (n_anchors
# is a constant 1 in the easy band, so it's only keyed in medium/hard.)
AXES = {
    "grid_h":    {"type": "int", "default": "rng 11..13", "valid": "9..18",
                  "doc": "Grid height (easy 9..11, medium 11..13, hard 14..18)."},
    "grid_w":    {"type": "int", "default": "rng 11..13", "valid": "9..18",
                  "doc": "Grid width (easy 9..11, medium 11..13, hard 14..18)."},
    "n_anchors": {"type": "int", "default": "rng 1..2", "valid": "1..3",
                  "doc": "Color-9 anchor cells (easy 1, medium 1..2, hard 2..3)."},
    "n_objects": {"type": "int", "default": "rng 2..4", "valid": "2..5",
                  "doc": "Sliding objects (easy 2..3, medium 2..4, hard 3..5)."},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the slide-away demos."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs: list[str] = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    non_bg = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 7]
    if not non_bg:
        return ["grid contains only background"]
    nines = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if not nines:
        errs.append("no color-9 anchor cells found")
    colors = sorted({v for _, _, v in non_bg if v not in (9,)})
    if len(colors) < 2:
        errs.append(f"expected at least two sliding object colors, found {colors}")
    for color in colors:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if not (2 <= len(cells) <= 4):
            errs.append(f"object color {color} has {len(cells)} cells, expected 2..4")
            continue
        br = sum(r for r, _ in cells) // len(cells)
        bc = sum(c for _, c in cells) // len(cells)
        dists = sorted((abs(br - ar) + abs(bc - ac), ar, ac) for ar, ac in nines)
        if len(dists) >= 2 and dists[0][0] == dists[1][0]:
            errs.append(f"object color {color} has tied nearest anchors")
            continue
        if not dists:
            continue
        _, ar, ac = dists[0]
        dr_off = br - ar
        dc_off = bc - ac
        if abs(dr_off) == abs(dc_off):
            errs.append(f"object color {color} has ambiguous dominant direction")
            continue
        maxr = max(r for r, _ in cells); minr = min(r for r, _ in cells)
        maxc = max(c for _, c in cells); minc = min(c for _, c in cells)
        if abs(dr_off) > abs(dc_off):
            slide = (h - 1 - maxr) if dr_off > 0 else minr
            direction = "down" if dr_off > 0 else "up"
        else:
            slide = (w - 1 - maxc) if dc_off > 0 else minc
            direction = "right" if dc_off > 0 else "left"
        if slide <= 0:
            errs.append(f"object color {color} already touches {direction} edge; demo would be identity for it")
    return errs


def _free(g, cells, h, w):
    cell_set = set(cells)
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        if g[r][c] != 7:
            return False
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    if g[nr][nc] != 7 and (nr, nc) not in cell_set:
                        return False
    return True


def _build_blob(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        n_anchors = 1
        n_objects = ctx.draw_int("n_objects", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 14, 18)
        n_anchors = ctx.draw_int("n_anchors", 2, 3)
        n_objects = ctx.draw_int("n_objects", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
        n_anchors = ctx.draw_int("n_anchors", 1, 2)
        n_objects = ctx.draw_int("n_objects", 2, 4)
    g = full_grid(h, w, 7)
    anchor_positions = []
    for _ in range(n_anchors * 8):
        if len(anchor_positions) >= n_anchors:
            break
        r = rng.randint(2, h - 3); c = rng.randint(2, w - 3)
        if g[r][c] != 7:
            continue
        too_close = False
        for ar, ac in anchor_positions:
            if abs(r - ar) + abs(c - ac) < 3:
                too_close = True; break
        if too_close:
            continue
        g[r][c] = 9
        anchor_positions.append((r, c))
    obj_colors = [c for c in [1, 2, 3, 4, 5, 6, 8] if c != 7 and c != 9]
    rng.shuffle(obj_colors)
    placed = 0
    for color in obj_colors[:n_objects]:
        for _ in range(60):
            blob = _build_blob(rng, rng.randint(2, 4))
            sh = max(r for r, _ in blob) + 1
            sw = max(c for _, c in blob) + 1
            r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
            cells_abs = [(r0 + dr, c0 + dc) for dr, dc in blob]
            if not _free(g, cells_abs, h, w):
                continue
            # Pick the nearest anchor, ensure dr != dc (no ambiguity)
            br = sum(r for r, _ in cells_abs) // len(cells_abs)
            bc = sum(c for _, c in cells_abs) // len(cells_abs)
            dists = sorted((abs(br - ar) + abs(bc - ac), ar, ac)
                           for ar, ac in anchor_positions)
            if len(dists) >= 2 and dists[0][0] == dists[1][0]:
                continue  # no strictly nearest anchor
            _, best_ar, best_ac = dists[0]
            dr_off = br - best_ar
            dc_off = bc - best_ac
            if abs(dr_off) == abs(dc_off):
                continue  # ambiguous direction
            maxr = max(r for r, _ in cells_abs); minr = min(r for r, _ in cells_abs)
            maxc = max(c for _, c in cells_abs); minc = min(c for _, c in cells_abs)
            if abs(dr_off) > abs(dc_off):
                slide = (h - 1 - maxr) if dr_off > 0 else minr
            else:
                slide = (w - 1 - maxc) if dc_off > 0 else minc
            if slide <= 0:
                continue  # already at target edge; would not demonstrate movement
            for r, c in cells_abs:
                g[r][c] = color
            placed += 1
            break
    if placed < 2:
        # INVARIANT guard: the rule needs ≥2 objects to be a meaningful demo.
        # In practice placement always succeeds at these sizes, but under
        # override extremes it could under-populate — reject so the runner
        # resamples rather than emitting a malformed (sub-invariant) grid.
        raise ValueError("could not place ≥2 objects")
    return g
