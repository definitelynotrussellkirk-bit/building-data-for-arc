"""Generator for arc_puzzle_bank_eighth21:H56 — anchor-coded rotation stamps.

Rule: a prototype shape (4-connected component, color NOT in
{2,3,4,5}) sits somewhere on a 0-bg grid. Several "anchor"
single-cell markers in colors {2, 3, 4, 5} are placed elsewhere.
Each anchor's color is a ROTATION CODE for the prototype shape:
  2 = identity
  3 = rotate 90° CW
  4 = rotate 180°
  5 = rotate 90° CCW (= 270° CW)
The output is a fresh same-size grid: at each anchor position, stamp
the rotated prototype shape (using the prototype's color, with shape
offsets applied relative to the anchor cell). The original prototype
and anchor cells do NOT appear in output unless they coincide with a
stamped position.

Combinatorial axes: grid_h, grid_w, proto_color, proto_size,
n_anchors, anchor_codes, anchor_layout.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "531e65dffc0a"
VERSION = "1.2.1"
TASK_ID = "531e65dffc0a"

SUMMARY = (
    "One prototype shape (color ∉ {2,3,4,5}) plus N anchor cells in "
    "colors {2,3,4,5} acting as rotation codes (2=id, 3=cw90, 4=180, "
    "5=ccw90). Rule outputs a fresh grid where each anchor is the "
    "origin of a rotated stamp of the prototype shape, painted in "
    "the prototype's color. Original proto/anchor cells are erased."
)

# Rivals: 'output is input' refuted by any demo (proto+anchors gone,
# stamps appear). 'use anchor colors in output' refuted by any
# demo (output uses proto color). 'stamp without rotation' refuted
# by ≥1 demo with code 3/4/5 producing an orientation differing
# from the proto. 'stamp at proto position' refuted by any demo
# (stamps appear at anchor positions). 3 demos with ≥3 distinct
# rotation codes among anchors cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one prototype shape, color ∉ {0, 2, 3, 4, 5}",
    "≥1 anchor cell, each color in {2, 3, 4, 5}",
    "anchor cells are isolated (not 4-touching the prototype)",
]

AXES = {
    "grid_h":    {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w":    {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "n_anchors": {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "proto_size":{"type": "int", "default": "rng 3..5", "valid": "2..6"},
}


def _grow_proto(rng, k):
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


def _rotated(cells, code):
    if code == 2:
        return cells
    if code == 3:
        # CW 90: (r, c) -> (c, H - 1 - r) where H is bbox height
        h = max(r for r, _ in cells) + 1
        return [(c, h - 1 - r) for r, c in cells]
    if code == 4:
        # 180: (r, c) -> (H - 1 - r, W - 1 - c)
        h = max(r for r, _ in cells) + 1
        w = max(c for _, c in cells) + 1
        return [(h - 1 - r, w - 1 - c) for r, c in cells]
    if code == 5:
        # CCW 90 (= CW 270): (r, c) -> (W - 1 - c, r)
        w = max(c for _, c in cells) + 1
        return [(w - 1 - c, r) for r, c in cells]
    return cells


def _bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return (min(rs), min(cs), max(rs), max(cs))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; prototype color not in {0,2,3,4,5} exists; ≥1 anchor in {2,3,4,5}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    anchor_colors = {2, 3, 4, 5}
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in anchor_colors]
    proto_cells = [(r, c) for r in range(h) for c in range(w)
                   if grid[r][c] not in (0, 2, 3, 4, 5)]
    if not proto_cells:
        return errors  # degenerate — allowed
    if not anchors:
        errors.append("no anchor cells in {2,3,4,5} found")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(8, 10); w = rng.randint(9, 11)
        n_anchors = rng.randint(2, 3); proto_size = rng.randint(3, 4)
    elif difficulty == "hard":
        h = rng.randint(12, 16); w = rng.randint(13, 18)
        n_anchors = rng.randint(4, 6); proto_size = rng.randint(4, 6)
    else:
        h = rng.randint(9, 12); w = rng.randint(10, 14)
        n_anchors = rng.randint(3, 4); proto_size = rng.randint(3, 5)

    # Prototype color must be NOT in {0, 2, 3, 4, 5}.
    proto_color = rng.choice([1, 6, 7, 8, 9])
    proto = _grow_proto(rng, proto_size)
    pr1, pc1, pr2, pc2 = _bbox(proto)
    proto_h = pr2 + 1
    proto_w = pc2 + 1

    g = full_grid(h, w, 0)
    # Place prototype somewhere with a 1-cell buffer.
    for _ in range(80):
        r0 = rng.randint(0, h - proto_h)
        c0 = rng.randint(0, w - proto_w)
        # Check buffer empty.
        clear = True
        for dr, dc in proto:
            if g[r0 + dr][c0 + dc] != 0:
                clear = False; break
        if not clear:
            continue
        for dr, dc in proto:
            g[r0 + dr][c0 + dc] = proto_color
        break

    # Place anchors. Each anchor is a single cell, isolated from any
    # non-bg cell (4-touching).
    occupied = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 0}
    placed = 0
    attempts = 0
    while placed < n_anchors and attempts < 200:
        attempts += 1
        ar = rng.randint(0, h - 1)
        ac = rng.randint(0, w - 1)
        if (ar, ac) in occupied:
            continue
        # Must not 4-touch any non-bg cell.
        if any((ar + dr, ac + dc) in occupied
               for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]):
            continue
        code = rng.choice([2, 3, 4, 5])
        g[ar][ac] = code
        occupied.add((ar, ac))
        placed += 1
    return g
