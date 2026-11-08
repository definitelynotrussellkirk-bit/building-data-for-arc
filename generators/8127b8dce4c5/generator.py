"""Generator for puzzle 27a28665.

Rule: 3x3 input. Count non-zero corner cells.
- 0 corners non-zero → output 6
- 4 corners non-zero → output 2
- has 2x2 sub-block all non-zero → output 3
- otherwise → output 1

Combinatorial axes (8): n_cells, color, corner_pattern, has_2x2,
center_filled, anchor_corner, asymmetry_force, palette_kind.
Degenerates: empty_grid, full_grid, single_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8127b8dce4c5"
# 3.1.0: defect-lint low_output_diversity + drift — the draws ignored the
# difficulty band, so easy/medium/hard emitted IDENTICAL grids (18 samples = 6
# distinct); density was far below the canonical 5-6-cells-of-9 (modal was 0,
# canonical modal is the color). Band now enters the rng salt; classes padded
# with class-safe extra cells to canonical density; EXPECTED_OUTPUT_CODOMAIN
# declared under the name the gates read. (3.0.0: uniform class targeting.)
VERSION = "3.1.0"
EXPECTED_OUTPUT_CODOMAIN = 4  # {1,2,3,6} — intrinsic 4-label classifier
TASK_ID = "8127b8dce4c5"
SUMMARY = (
    "Exactly 3×3 grid with some non-zero cells in a single "
    "color (1-9). Corner cells (0,0),(0,2),(2,0),(2,2) and "
    "edge/center vary in pattern. Rule: count NON-ZERO "
    "corner cells (0..4). Check if any 2×2 sub-block is all "
    "non-zero. Output: a 1×1 grid with: 6 if 0 corners non-"
    "zero; 2 if 4 corners non-zero; 3 if a 2×2 fully filled "
    "block exists; else 1."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "h = w = 3",
    "1+ non-zero cells (so rule has input)",
    "all non-zero cells share one color",
]

CORNER_PATTERNS = ("zero_corners", "all_corners", "two_corners",
                   "diagonal_corners", "anti_diag_corners")
PALETTE_KINDS = ("warm", "cool", "broad")
DEGENERATE_TEXTURES = ("empty_grid", "full_grid", "single_corner")
HELPFUL_TEXTURES = CORNER_PATTERNS

AXES = {
    "n_cells":        {"type": "int", "default": "rng 2..7", "valid": "1..9"},
    "color":          {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "corner_pattern": {"type": "str", "default": "rng helpful",
                       "valid": "|".join(CORNER_PATTERNS)},
    "has_2x2":        {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "center_filled":  {"type": "bool", "default": "rng",
                       "valid": "true|false"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for corner_pattern",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    # Include the band in the salt: this generator has no size knobs, so without
    # it every band produced the SAME grid for a given (seed, index).
    rng = ctx.draw_rng(f"layout:{difficulty or 'default'}")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    color = int(overrides.get("color", rng.randint(1, 9)))
    if color == 0:
        color = 1
    # Target each output CLASS uniformly so all 4 (6,2,3,1) appear.
    target = overrides.get("target_class") or rng.choice(["c6", "c2", "c3", "c1"])
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    edges_center = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
    g = full_grid(3, 3, 0)

    def _has_2x2():
        return any(all(g[r + dr][c + dc] != 0 for dr in (0, 1) for dc in (0, 1))
                   for r in (0, 1) for c in (0, 1))

    # Canonical demos are DENSE (5-6 of 9 cells colored, modal = the color,
    # zeros scattered) — each class targets >=5 cells where its label allows.
    if target == "c6":
        # zero corners (plus shape: all edges + center) -> class 6; the four
        # zero corners stay isolated like the canonical checker-style demos
        for r, c in edges_center:
            g[r][c] = color
        if rng.random() < 0.3:
            g[1][1] = 0   # hollow plus variant — still class 6, zeros still scattered
    elif target == "c2":
        # all 4 corners + center (X pattern) -> class 2; zeros = isolated edges
        for r, c in corners:
            g[r][c] = color
        g[1][1] = color
        if rng.random() < 0.4:
            r, c = rng.choice([(0, 1), (1, 0), (1, 2), (2, 1)])
            g[r][c] = color
    elif target == "c3":
        # a full 2x2 block (one corner -> corners=1) -> class 3; pad with 1-2
        # extra corners (corners stays <= 3, so the class holds)
        br = rng.randint(0, 1); bc = rng.randint(0, 1)
        for dr in range(2):
            for dc in range(2):
                g[br + dr][bc + dc] = color
        free_corners = [(r, c) for r, c in corners if g[r][c] == 0]
        for r, c in rng.sample(free_corners, min(rng.randint(1, 2), len(free_corners))):
            g[r][c] = color
    else:  # c1: 2-3 corners + center (partial X), no 2x2 -> class 1;
        # zeros stay scattered as isolated edges (canonical checker style)
        for r, c in rng.sample(corners, rng.randint(2, 3)):
            g[r][c] = color
        g[1][1] = color  # center is safe (cannot complete a 2x2 alone)
        if rng.random() < 0.4:
            pads = list(edges_center)
            rng.shuffle(pads)
            for r, c in pads[:1]:
                if g[r][c] == 0:
                    g[r][c] = color
                    if _has_2x2():
                        g[r][c] = 0   # would flip the class — revert
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """The rule maps a 3x3 input to ONE of only four class labels {1,2,3,6}, so the
    output cardinality is intrinsically <= 4 (a scalar classifier, not low-diversity).
    This guards the INPUT: 3x3, >=1 non-zero cell, all non-zero cells one color."""
    errs = []
    if len(grid) != 3 or any(len(row) != 3 for row in grid):
        errs.append("input is not 3x3")
        return errs
    nz = {v for row in grid for v in row if v != 0}
    if not nz:
        errs.append("no non-zero cells — rule has no input")
    if len(nz) > 1:
        errs.append(f"non-zero cells use multiple colors: {sorted(nz)}")
    return errs


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    return pool


def _apply_corner_pattern(g, pattern, color, rng):
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    if pattern == "zero_corners":
        # Fill non-corners only
        non_corners = [(r, c) for r in range(3) for c in range(3)
                       if (r, c) not in corners]
        rng.shuffle(non_corners)
        for r, c in non_corners[:rng.randint(1, 3)]:
            g[r][c] = color
    elif pattern == "all_corners":
        for r, c in corners:
            g[r][c] = color
    elif pattern == "two_corners":
        for r, c in rng.sample(corners, 2):
            g[r][c] = color
        # Optional: a few non-corner cells
        non_corners = [(r, c) for r in range(3) for c in range(3)
                       if (r, c) not in corners]
        rng.shuffle(non_corners)
        for r, c in non_corners[:rng.randint(0, 2)]:
            g[r][c] = color
    elif pattern == "diagonal_corners":
        for r, c in [(0, 0), (2, 2)]:
            g[r][c] = color
    elif pattern == "anti_diag_corners":
        for r, c in [(0, 2), (2, 0)]:
            g[r][c] = color
    else:
        n = rng.randint(2, 6)
        cells = [(r, c) for r in range(3) for c in range(3)]
        rng.shuffle(cells)
        for r, c in cells[:n]:
            g[r][c] = color


def _draw_from_degenerate(name, rng):
    g = full_grid(3, 3, 0)
    if name == "empty_grid":
        return g
    if name == "full_grid":
        c = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for r in range(3):
            for cc in range(3):
                g[r][cc] = c
        return g
    if name == "single_corner":
        g[0][0] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        return g
    return g
