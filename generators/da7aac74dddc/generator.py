"""Generator for arc_additional_puzzles_21_set10_bundle:H66 — rotational equivalence matrix.

Rule: every non-zero connected component (color-separated) is cropped
to a binary bounding box; components are ordered by top-left position.
Output is N×N: 1 on diagonal, 2 if two shapes are equal up to rotation,
3 otherwise.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "da7aac74dddc"
VERSION = "2.0.1"  # add executable self_check for isolated rotation-class components  # distinct 4 + shape-locked-out: n PINNED at 3 (always 3x3 matrix) + fixed shape bank. Output is the n x n rotation-equivalence matrix. Now vary object count 2-5 + random rotation-class shapes (distinct sizes) -> output sizes + matrix patterns vary. Raise -> graceful fallback.
TASK_ID = "da7aac74dddc"

SUMMARY = "N (2-5) isolated components from random rotation-classes; output N×N rotation-equivalence matrix (1 diag, 2 if rotation-equal, 3 else)."

INVARIANTS = [
    "background is 0",
    "2-5 isolated connected components in colors {1..9}",
    "components are 4-connected and color-separated",
    "shape classes have distinct cell counts so they are rotation-inequivalent",
]

AXES = {
    "grid_h":   {"type": "int", "default": "rng 10..14", "valid": "8..16"},
    "grid_w":   {"type": "int", "default": "rng 13..16", "valid": "10..18"},
    "n_objs":   {"type": "int", "default": "rng 3..5", "valid": "2..5"},
    "n_classes":{"type": "int", "default": "rng 1..min(n,4)", "valid": "1..4"},
}


_SHAPES = [
    [(0, 0), (1, 0), (1, 1)],                  # L tromino
    [(0, 0), (0, 1), (1, 0)],                  # mirror L tromino
    [(0, 0), (0, 1), (0, 2), (1, 1)],          # T tetromino
    [(0, 0), (1, 0), (1, 1), (2, 1)],          # S tetromino
    [(0, 0), (0, 1), (1, 0), (1, 1)],          # 2x2 square
    [(0, 0), (0, 1), (0, 2)],                  # I tromino
]


def _rotate_cw(shape):
    rs = [r for r, _ in shape]
    h = max(rs) + 1
    return sorted([(c, h - 1 - r) for r, c in shape])


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    # output is the n x n rotation-equivalence matrix; n was PINNED at 3 (always 3x3,
    # shape-locked) and shapes came from a fixed bank -> distinct 4. Vary object count
    # and use random rotation-class shapes (distinct sizes -> rotation-inequivalent).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n_objs", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 15, 18)
        n = ctx.draw_int("n_objs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n_objs", 3, 5)
    rng = ctx.draw_rng("layout")
    n_classes = ctx.draw_int("n_classes", 1, min(n, 4))
    for outer in range(40):
        g = full_grid(h, w, 0)
        sizes = rng.sample(range(2, 6), n_classes)   # distinct sizes -> rotation-inequivalent classes
        bases = [_poly(rng, k) for k in sizes]
        assign = list(range(n_classes)) + [rng.randint(0, n_classes - 1)
                                           for _ in range(n - n_classes)]
        rng.shuffle(assign)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        for cls, color in zip(assign, colors):
            shape = bases[cls]
            for _ in range(rng.randint(0, 3)):       # random rotation within the class
                shape = _rotate_cw(shape)
            shape = sorted(shape)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                rmin = min(r for r, _ in shape); cmin = min(c for _, c in shape)
                for dr, dc in shape:
                    g[r0 + dr - rmin][c0 + dc - cmin] = color
                placed = True; break
            if not placed: ok = False; break
        if ok:
            return g
    return g   # graceful fallback (last attempt); never raise



def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        errs.append("ragged grid")
        return errs
    comps = _components(grid)
    if not (2 <= len(comps) <= 5):
        errs.append(f"expected 2-5 components, got {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("component colors are not unique")
    occupied = {(r, c) for _, cells in comps for r, c in cells}
    for color, cells in comps:
        if not (2 <= len(cells) <= 5):
            errs.append(f"component color {color} size {len(cells)} outside 2..5")
        # The placer promises a one-cell moat around each component; catch future
        # fallback or placement regressions that merge/touch objects.
        for r, c in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nb = (r + dr, c + dc)
                    if nb in occupied and nb not in cells:
                        errs.append(f"component color {color} touches another component")
                        return errs
    return errs
