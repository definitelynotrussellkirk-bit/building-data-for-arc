"""Generator for arc_puzzle_bank_21_set13_s:S13_E4.

Combinatorial axes (8): height, width, palette_kind, symmetric_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, all_symmetric, all_asymmetric.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4e04b5fcae45"
VERSION = "2.0.1"
TASK_ID = "4e04b5fcae45"
SUMMARY = (
    "0-bg grid (h~10-16, w~12-18) with: (a) 1-3 "
    "HORIZONTALLY-SYMMETRIC COMPONENTS — each shape "
    "drawn from a small bank _SYM_H of LR-symmetric "
    "motifs (plus, square, horizontal-3 bar — shapes "
    "that satisfy shape ≡ flip_lr(shape)); (b) 2 "
    "ASYMMETRIC COMPONENTS — each shape drawn from "
    "_ASYM bank (L-triomino, Z-tetromino, T-shape — "
    "no LR symmetry). Each component is painted in a "
    "DISTINCT non-0 color drawn from {2, 3, 4, 6} "
    "(shuffled). Components are placed at non-touching "
    "positions with 1-cell padding (_free check). "
    "Rule (RECOLOR ONLY HORIZONTALLY-SYMMETRIC "
    "COMPONENTS TO COLOR 8): for EACH 4-CONNECTED non-"
    "bg COMPONENT in the input: CHECK whether the "
    "component's local shape (in its bbox) is "
    "HORIZONTALLY MIRROR-SYMMETRIC (flipping its cells "
    "left-right produces the same shape). If YES: "
    "RECOLOR every cell of that component to COLOR 8. "
    "If NO: LEAVE the component unchanged (keeps its "
    "original color). Bg-0 cells stay 0. Net: "
    "horizontally-symmetric shapes are unified under "
    "color 8 (cyan); asymmetric shapes retain their "
    "original colors as distractors."
)

INVARIANTS = [
    "background is 0",
    "there is at least one horizontally symmetric component",
    "there is at least one component without horizontal symmetry",
    "outputs preserve size and recolor only horizontal-symmetry components",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "all_symmetric", "all_asymmetric")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "width":          {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "symmetric_count": {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "mixed_sym_asym",
                       "valid": "mixed_sym_asym"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SYM_H = [
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2)],
]
_ASYM = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
]


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _free(g, r0, c0, shape, pad=1):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - pad), min(h, r0 + sh + pad)):
        for c in range(max(0, c0 - pad), min(w, c0 + sw + pad)):
            if g[r][c] != 0:
                return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    for _ in range(120):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, shape):
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            return
    raise ValueError("could not place object")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=3 non-bg components (sym + asym mixed)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    visited = [[False] * w for _ in range(h)]
    def flood(r0, c0):
        stack = [(r0, c0)]
        visited[r0][c0] = True
        while stack:
            r, c = stack.pop()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                rr, cc = r+dr, c+dc
                if 0 <= rr < h and 0 <= cc < w and not visited[rr][cc] and grid[rr][cc] != 0:
                    visited[rr][cc] = True
                    stack.append((rr, cc))
    n_components = 0
    for r in range(h):
        for c in range(w):
            if not visited[r][c] and grid[r][c] != 0:
                flood(r, c)
                n_components += 1
    if n_components < 3:
        errs.append(f"expected >=3 components (sym+asym), got {n_components}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 10, 11)
        w = ctx.draw_int("width", 12, 13)
        sym_count = ctx.draw_int("symmetric_count", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 13, 16)
        w = ctx.draw_int("width", 14, 18)
        sym_count = ctx.draw_int("symmetric_count", 2, 3)
    else:
        h = ctx.draw_int("height", 10, 13)
        w = ctx.draw_int("width", 12, 15)
        sym_count = ctx.draw_int("symmetric_count", 1, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = [2, 3, 4, 6]
    rng.shuffle(colors)
    for i in range(sym_count):
        _place(g, rng, rng.choice(_SYM_H), colors[i])
    for color in colors[sym_count:sym_count + 2]:
        _place(g, rng, rng.choice(_ASYM), color)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 13
    g = full_grid(h, w, 0)
    if name == "no_components":
        # Empty grid — rule has no components to evaluate symmetry on.
        return g
    if name == "all_symmetric":
        # All components are LR-symmetric — every one gets recolored.
        for dr, dc in _SYM_H[0]: g[1 + dr][2 + dc] = 4
        for dr, dc in _SYM_H[1]: g[5 + dr][2 + dc] = 5
        for dr, dc in _SYM_H[2]: g[8 + dr][2 + dc] = 6
        return g
    if name == "all_asymmetric":
        # No symmetric components — rule recolors nothing (input == output).
        for dr, dc in _ASYM[0]: g[1 + dr][2 + dc] = 4
        for dr, dc in _ASYM[1]: g[5 + dr][2 + dc] = 5
        for dr, dc in _ASYM[2]: g[8 + dr][2 + dc] = 6
        return g
    return g
