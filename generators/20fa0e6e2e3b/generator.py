"""Generator for arc_additional_puzzle_bank_volume18:E122.

Rule: crop the smallest non-zero connected object to its bbox.

Combinatorial axes (8): grid_h/w, palette_kind, num_objects, smallest_size,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: tied_smallest, only_one_component, all_same_size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "20fa0e6e2e3b"
VERSION = "3.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has non-zero cells (objects for crop-smallest rule)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        errs.append("no non-zero cells (expected objects to crop-smallest from)")
    return errs
TASK_ID = "20fa0e6e2e3b"
SUMMARY = (
    "0-bg grid (h, w~8-13) "
    "with HARDCODED LAYOUT: "
    "(a) COLOR-7 SOLID "
    "2×3 RECT at (0..1, "
    "0..2) (6 cells, "
    "largest); (b) COLOR-8 "
    "SOLID 3×3 RECT at "
    "(h-3..h-1, w-3..w-1) "
    "(9 cells); (c) COLOR-"
    "2 L-SHAPE at random "
    "interior position "
    "(r, c) with cells "
    "(r, c), (r+1, c), "
    "(r+1, c+1) — 3 cells, "
    "always smallest. "
    "Hardcoded shapes + 7 "
    "and 8 fixed positions; "
    "only the L-shape "
    "position varies. "
    "Output uniq_out=1 — "
    "always emits the same "
    "L-shape 2×2 bbox in "
    "COLOR-2 (intrinsic — "
    "fixed smallest shape). "
    "Rule (CROP SMALLEST "
    "CONNECTED OBJECT TO "
    "BBOX): identify all "
    "NON-BG connected "
    "components. FIND the "
    "SMALLEST by cell count. "
    "CROP it to its BBOX. "
    "EMIT the cropped "
    "subgrid. Net: smallest "
    "object's bbox crop is "
    "the output."
)

INVARIANTS = [
    "background is 0",
    "one object is uniquely smallest by component size",
    "larger objects are separated from the target",
    "the target shape can have internal background in its bounding box",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("tied_smallest", "only_one_component", "all_same_size")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|rainbow"},
    "num_objects":    {"type": "int", "default": "3", "valid": "3"},
    "smallest_size":  {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|rainbow|tied_smallest|only_one_component|all_same_size"},
}


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_NONBG = [1, 2, 3, 4, 5, 6, 7, 8, 9]


def _poly(rng, n):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _place(g, cells, color, rng, occ):
    h, w = len(g), len(g[0])
    bh = max(r for r, _ in cells) + 1
    bw = max(c for _, c in cells) + 1
    if bh > h or bw > w:
        return False
    for _ in range(150):
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        ac = [(r0 + r, c0 + c) for r, c in cells]
        if any((r + dr, c + dc) in occ
               for r, c in ac for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            continue
        for r, c in ac:
            g[r][c] = color
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    occ.add((r + dr, c + dc))
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13); w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 13); w = ctx.draw_int("grid_w", 8, 13)
    rng = ctx.draw_rng("placement")

    # The SMALLEST object (the answer) is a varied polyomino; two strictly
    # larger objects ensure it is uniquely smallest. Its varied form+colour
    # drive the cropped-output diversity.
    ssize = rng.randint(2, 4)
    small = _poly(rng, ssize)
    big1 = _poly(rng, ssize + rng.randint(2, 3))
    big2 = _poly(rng, ssize + rng.randint(4, 5))
    cs, c1, c2 = rng.sample(_NONBG, 3)
    g = full_grid(h, w, 0)
    occ = set()
    _place(g, small, cs, rng, occ)
    _place(g, big1, c1, rng, occ)
    _place(g, big2, c2, rng, occ)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "tied_smallest":
        # two objects tied at smallest size — pick is ambiguous
        g[2][2] = 2; g[2][3] = 2
        g[5][6] = 4; g[5][7] = 4
        draw_rect(g, h - 3, 0, 3, 3, 7)
        return g
    if name == "only_one_component":
        # single object — trivially smallest
        g[3][3] = 2; g[3][4] = 2; g[4][3] = 2
        return g
    if name == "all_same_size":
        # 3 objects same size — no unique smallest
        g[1][1] = 2; g[1][2] = 2; g[2][1] = 2
        g[1][6] = 4; g[1][7] = 4; g[2][6] = 4
        g[7][1] = 7; g[7][2] = 7; g[8][1] = 7
        return g
    return g
