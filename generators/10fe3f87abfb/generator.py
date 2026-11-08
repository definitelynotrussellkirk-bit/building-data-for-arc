"""Generator for 10fe3f87abfb — erase 4-objects opposite the 9 over guide.

Rule: BG = 7. A straight line of 5s is the guide. A single 9 cell is
the marker, on one side of the guide. Several color-4 4-connected
objects are scattered. For each 4-object: if it lies ENTIRELY on the
opposite side from the marker, AND its cells project onto the guide
range at ≥2 distinct positions (for vertical guide: ≥2 rows in
[r0,r1]; for horizontal: ≥2 cols in [c0,c1], or any cell on the
marker's col/row), it's erased back to 7. Otherwise preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "10fe3f87abfb"
VERSION = "2.0.1"  # +self_check
TASK_ID = "10fe3f87abfb"
SUMMARY = (
    "Color-7 bg grid. ONE straight line of color-5 cells (the guide, "
    "horizontal or vertical). ONE color-9 cell (the marker) on one side "
    "of the guide. Several color-4 objects (connected 4-components) "
    "scattered. Some objects lie entirely on the marker's side of the "
    "guide (preserved). Other objects lie entirely on the opposite "
    "side; of these, ≥1 'crosses' the guide projection at ≥2 positions "
    "and gets erased. Rule erases such objects to color 7."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is color 7",
    "exactly one straight color-5 line (horizontal or vertical), length ≥3",
    "exactly one color-9 marker on ONE side of the guide",
    "≥1 color-4 object on the marker's side (preserved)",
    "≥1 color-4 object on the opposite side that crosses the guide projection at ≥2 positions (erased)",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); the object counts (n_erase/n_keep) come from the unkeyed layout
# rng and scale with difficulty, so they aren't override axes.
AXES = {
    "grid_h": {"type": "int", "default": "rng 10..13", "valid": "9..16",
               "doc": "Grid height (easy 9..11, medium 10..13, hard 12..16)."},
    "grid_w": {"type": "int", "default": "rng 12..15", "valid": "10..18",
               "doc": "Grid width (easy 10..12, medium 12..15, hard 14..18)."},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if g[r][c] != 7:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 12)
        n_erase = 1
        n_keep = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        n_erase = rng.randint(2, 3)
        n_keep = rng.randint(3, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 15)
        n_erase = rng.randint(1, 2)
        n_keep = rng.randint(2, 4)

    orientation = rng.choice(["vertical", "horizontal"])
    g = full_grid(h, w, 7)

    if orientation == "vertical":
        col = rng.randint(max(4, w // 3), w - max(4, w // 3) - 1)
        r0 = rng.randint(1, max(1, h // 3))
        r1 = rng.randint(max(r0 + 3, 2 * h // 3), h - 2)
        for r in range(r0, r1 + 1):
            g[r][col] = 5
        # Marker on one side
        marker_side = rng.choice([-1, 1])  # -1 = left, 1 = right
        marker_col = (col - rng.randint(2, 3)) if marker_side == -1 else (col + rng.randint(2, 3))
        if not (0 <= marker_col < w):
            marker_col = col - 2 if marker_side == -1 else col + 2
        marker_row = rng.randint(r0, r1)
        # Place 9 in marker side (clear of guide)
        if 0 <= marker_col < w and g[marker_row][marker_col] == 7:
            g[marker_row][marker_col] = 9
        else:
            return generate(seed + 1, sample_index, difficulty=difficulty, **overrides)
        opposite_side = -marker_side  # the side to erase
        # Place erase candidates: on opposite side, ≥2 rows overlap with [r0..r1]
        for _ in range(n_erase):
            for tries in range(60):
                obj_col = (col + rng.randint(2, 3)) if opposite_side == 1 else (col - rng.randint(2, 3))
                if not (0 <= obj_col < w - 1 and obj_col >= 1):
                    continue
                obj_r_start = rng.randint(r0, max(r0, r1 - 2))
                obj_len = rng.randint(2, 3)
                if obj_r_start + obj_len > h:
                    continue
                cells = [(obj_r_start + dr, obj_col) for dr in range(obj_len)]
                if not all(g[r][c] == 7 for r, c in cells):
                    continue
                for r, c in cells:
                    g[r][c] = 4
                break
        # Place keep candidates: on marker side OR not crossing
        for _ in range(n_keep):
            for tries in range(60):
                kind = rng.choice(["marker_side", "single_cell_opposite", "outside_guide"])
                if kind == "marker_side":
                    obj_col = marker_col + rng.choice([-1, 0, 1, 2]) if marker_side == 1 else marker_col + rng.choice([-2, -1, 0, 1])
                    obj_row = rng.randint(0, h - 1)
                    if not (0 <= obj_col < w):
                        continue
                    if (obj_col - col) * marker_side <= 0:
                        continue
                    if g[obj_row][obj_col] != 7:
                        continue
                    g[obj_row][obj_col] = 4
                    break
                elif kind == "single_cell_opposite":
                    obj_col = (col + rng.randint(2, w - col - 1)) if opposite_side == 1 and col + 2 < w else (col - rng.randint(2, col)) if col - 2 >= 0 else col
                    obj_row = rng.randint(0, h - 1)
                    if not (0 <= obj_col < w):
                        continue
                    if (obj_col - col) * opposite_side <= 0:
                        continue
                    if g[obj_row][obj_col] != 7:
                        continue
                    g[obj_row][obj_col] = 4
                    break
                else:
                    obj_col = rng.randint(0, w - 1)
                    obj_row = rng.choice([0, h - 1])
                    if obj_row >= r0 and obj_row <= r1:
                        continue
                    if g[obj_row][obj_col] != 7:
                        continue
                    g[obj_row][obj_col] = 4
                    break
    else:
        row = rng.randint(max(4, h // 3), h - max(4, h // 3) - 1)
        c0 = rng.randint(1, max(1, w // 3))
        c1 = rng.randint(max(c0 + 3, 2 * w // 3), w - 2)
        for c in range(c0, c1 + 1):
            g[row][c] = 5
        marker_side = rng.choice([-1, 1])
        marker_row = (row - rng.randint(2, 3)) if marker_side == -1 else (row + rng.randint(2, 3))
        if not (0 <= marker_row < h):
            marker_row = row - 2 if marker_side == -1 else row + 2
        marker_col = rng.randint(c0, c1)
        if 0 <= marker_row < h and g[marker_row][marker_col] == 7:
            g[marker_row][marker_col] = 9
        else:
            return generate(seed + 1, sample_index, difficulty=difficulty, **overrides)
        opposite_side = -marker_side
        for _ in range(n_erase):
            for tries in range(60):
                obj_row = (row + rng.randint(2, 3)) if opposite_side == 1 else (row - rng.randint(2, 3))
                if not (0 <= obj_row < h - 1 and obj_row >= 1):
                    continue
                obj_c_start = rng.randint(c0, max(c0, c1 - 2))
                obj_len = rng.randint(2, 3)
                if obj_c_start + obj_len > w:
                    continue
                cells = [(obj_row, obj_c_start + dc) for dc in range(obj_len)]
                if not all(g[r][c] == 7 for r, c in cells):
                    continue
                for r, c in cells:
                    g[r][c] = 4
                break
        for _ in range(n_keep):
            for tries in range(60):
                kind = rng.choice(["marker_side", "single_cell_opposite", "outside_guide"])
                if kind == "marker_side":
                    obj_row = marker_row + rng.choice([-1, 0, 1, 2]) if marker_side == 1 else marker_row + rng.choice([-2, -1, 0, 1])
                    obj_col = rng.randint(0, w - 1)
                    if not (0 <= obj_row < h):
                        continue
                    if (obj_row - row) * marker_side <= 0:
                        continue
                    if g[obj_row][obj_col] != 7:
                        continue
                    g[obj_row][obj_col] = 4
                    break
                elif kind == "single_cell_opposite":
                    obj_row = (row + rng.randint(2, h - row - 1)) if opposite_side == 1 and row + 2 < h else (row - rng.randint(2, row)) if row - 2 >= 0 else row
                    obj_col = rng.randint(0, w - 1)
                    if obj_col == marker_col:
                        continue
                    if not (0 <= obj_row < h):
                        continue
                    if (obj_row - row) * opposite_side <= 0:
                        continue
                    if g[obj_row][obj_col] != 7:
                        continue
                    g[obj_row][obj_col] = 4
                    break
                else:
                    obj_col = rng.choice([0, w - 1])
                    obj_row = rng.randint(0, h - 1)
                    if obj_col >= c0 and obj_col <= c1:
                        continue
                    if g[obj_row][obj_col] != 7:
                        continue
                    g[obj_row][obj_col] = 4
                    break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """BG=7; color-5 guide line; color-9 marker; color-4 objects present."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    # Background should be 7 (most cells)
    sevens = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 7)
    if sevens == 0:
        errors.append("no background-7 cells found (expected 7-filled grid)")
    has_guide = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    if not has_guide:
        errors.append("no color-5 guide line cells found")
    has_marker = any(grid[r][c] == 9 for r in range(h) for c in range(w))
    if not has_marker:
        errors.append("no color-9 marker cell found")
    has_objects = any(grid[r][c] == 4 for r in range(h) for c in range(w))
    if not has_objects:
        errors.append("no color-4 object cells found")
    return errors
