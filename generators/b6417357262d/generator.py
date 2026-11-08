"""Generator for 5b:hard_31 — boolean template combine by key.

Rule: a key cell has value 4 (OR), 6 (AND), or 8 (XOR). Two shapes
(color 2 and color 3) get cell-wise combined per key into color 7.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_key (no isolated key cell → rule's op-selector returns
nothing), identical_shapes (cells_a == cells_b → AND==OR==both, XOR
empty; ops collapse), unequal_bboxes (color-2 and color-3 shapes have
different bbox dims → rule's "equal-bbox" precondition fails).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b6417357262d"
VERSION = "2.1.1"
TASK_ID = "b6417357262d"
SUMMARY = (
    "0-bg grid (h = 2*sh + 4, w = 2*sw + 4 with sh, sw ~3-4) "
    "with: (a) ONE isolated KEY CELL in {4 (OR), 6 (AND), "
    "8 (XOR)} placed alone with 8-neighbor buffer; (b) ONE "
    "color-2 (red) shape A at (1, 1) with sh × sw bbox; "
    "(c) ONE color-3 (green) shape B at (sh+3, sw+3) with "
    "matching sh × sw bbox. A and B are connected within "
    "the sh × sw bbox but have DIFFERENT cell patterns. "
    "Rule: detect op key, A, B. Compute per-cell boolean "
    "combine of A and B (both normalized to bbox), with "
    "op = OR (key==4), AND (key==6), or XOR (key==8). "
    "Output: the combined pattern painted in color 7 "
    "(orange) at A's position. Other cells = 0."
)

INVARIANTS = [
    "background is 0",
    "exactly one isolated key cell with value in {4, 6, 8}",
    "one color-2 shape and one color-3 shape with equal bbox dims",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "identical_shapes", "unequal_bboxes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "shape_h":           {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "shape_w":           {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "key_plus_two_shapes",
                          "valid": "key_plus_two_shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the key + equal-bbox boolean-shape setup.

    The useful regime has exactly one isolated key in {4,6,8}, one color-2
    shape, one color-3 shape, matching bboxes, different normalized patterns,
    and a nonempty/nonfull boolean result. The last guard catches the solid
    color-7 output degeneracy that makes an OR demo teach only "make a block".
    """
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []

    errs: list[str] = []
    keys = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
            if grid[r][c] in (4, 6, 8)]
    if len(keys) != 1:
        errs.append(f"expected exactly one key cell in {{4,6,8}}, found {len(keys)}")
    elif any(
        0 <= keys[0][0] + dr < h and 0 <= keys[0][1] + dc < w
        and not (dr == 0 and dc == 0)
        and grid[keys[0][0] + dr][keys[0][1] + dc] != 0
        for dr in (-1, 0, 1) for dc in (-1, 0, 1)
    ):
        errs.append("key cell is not 8-neighbor isolated")

    def cells_of(color: int) -> set[tuple[int, int]]:
        return {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}

    def norm(cells: set[tuple[int, int]]) -> tuple[set[tuple[int, int]], int, int]:
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        r1 = max(r for r, _ in cells)
        c1 = max(c for _, c in cells)
        return ({(r - r0, c - c0) for r, c in cells}, r1 - r0 + 1, c1 - c0 + 1)

    cells_a = cells_of(2)
    cells_b = cells_of(3)
    if not cells_a:
        errs.append("color-2 shape missing")
    if not cells_b:
        errs.append("color-3 shape missing")
    if cells_a and cells_b:
        a, ah, aw = norm(cells_a)
        b, bh, bw = norm(cells_b)
        if (ah, aw) != (bh, bw):
            errs.append(f"shape bbox mismatch: A={ah}x{aw}, B={bh}x{bw}")
        elif a == b:
            errs.append("shape patterns are identical")
        elif keys:
            op = keys[0][2]
            if op == 4:
                combined = a | b
            elif op == 6:
                combined = a & b
            else:
                combined = a ^ b
            area = ah * aw
            if not combined:
                errs.append("boolean result is empty")
            if len(combined) == area:
                errs.append("boolean result fills the entire bbox")
    return errs


def _poly(rng, sh, sw, k):
    """Random connected polyomino that touches all sides of the sh x sw bbox."""
    variants = [
        {(r, 0) for r in range(sh)} | {(sh - 1, c) for c in range(sw)},
        {(r, sw - 1) for r in range(sh)} | {(sh - 1, c) for c in range(sw)},
        {(r, 0) for r in range(sh)} | {(0, c) for c in range(sw)},
        {(r, sw - 1) for r in range(sh)} | {(0, c) for c in range(sw)},
    ]
    cells = set(rng.choice(variants))
    k = max(k, len(cells))
    k = min(k, sh * sw - 1)
    tries = 0
    while len(cells) < k and tries < 500:
        tries += 1
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < sh and 0 <= nc < sw:
            cells.add((nr, nc))
    return cells

def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        sh = ctx.draw_int("shape_h", 2, 3)
        sw = ctx.draw_int("shape_w", 2, 3)
    elif difficulty == "hard":
        sh = ctx.draw_int("shape_h", 4, 6)
        sw = ctx.draw_int("shape_w", 4, 6)
    else:
        sh = ctx.draw_int("shape_h", 3, 5)
        sw = ctx.draw_int("shape_w", 3, 5)
    rng = ctx.draw_rng("layout")
    h = sh * 2 + 4; w = sw * 2 + 4
    for _ in range(40):
        g = full_grid(h, w, 0)
        op = rng.choice([4, 6, 8])
        for _ in range(40):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            bad = False
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                        bad = True; break
                if bad: break
            if bad: continue
            g[r][c] = op; break
        max_cells = max(2, sh * sw - 1)
        min_cells = min(max_cells, max(sh + sw - 1, sh * sw // 3))
        ka = rng.randint(min_cells, max_cells)
        kb = rng.randint(min_cells, max_cells)
        cells_a = _poly(rng, sh, sw, ka)
        cells_b = _poly(rng, sh, sw, kb)
        if cells_a == cells_b:
            continue
        if op == 4:
            combined = cells_a | cells_b
        elif op == 6:
            combined = cells_a & cells_b
        else:
            combined = cells_a ^ cells_b
        if not combined or len(combined) == sh * sw:
            continue
        ar, ac = 1, 1
        br, bc = sh + 3, sw + 3
        if not _free(g, ar, ac, ar + sh - 1, ac + sw - 1) or not _free(g, br, bc, br + sh - 1, bc + sw - 1):
            continue
        for dr, dc in cells_a: g[ar + dr][ac + dc] = 2
        for dr, dc in cells_b: g[br + dr][bc + dc] = 3
        return g
    return g


def _draw_from_degenerate(name, rng):
    sh, sw = 3, 3
    h = sh * 2 + 4
    w = sw * 2 + 4
    g = full_grid(h, w, 0)
    if name == "no_key":
        # No isolated key cell — rule's op-selector returns nothing.
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)]: g[1 + dr][1 + dc] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]: g[sh + 3 + dr][sw + 3 + dc] = 3
        return g
    if name == "identical_shapes":
        # cells_a == cells_b — all ops collapse.
        cells = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)]
        g[8][1] = 4
        for dr, dc in cells: g[1 + dr][1 + dc] = 2
        for dr, dc in cells: g[sh + 3 + dr][sw + 3 + dc] = 3
        return g
    if name == "unequal_bboxes":
        # A is 3x3, B is 2x2 — equal-bbox precondition fails.
        g[8][1] = 6
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)]: g[1 + dr][1 + dc] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]: g[sh + 3 + dr][sw + 3 + dc] = 3
        return g
    return g
