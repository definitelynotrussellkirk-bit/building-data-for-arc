"""Generator for arc_puzzle_bank_eighth21:M53 — keep only blobs with a hole.

Rule: keep blobs whose bbox interior has at least one 0-cell that is
fully enclosed by the blob; drop the rest.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: all_solid (no holed objects → rule erases everything,
output empty), all_holed (every object is holed → rule keeps
everything, no contrast), no_objects (grid is all bg → rule's
selector finds nothing).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8bc82608e55f"
VERSION = "2.0.1"
TASK_ID = "8bc82608e55f"
SUMMARY = (
    "0-bg grid (h ∈ 9-11, w ∈ 11-13) "
    "with: (a) ONE HOLLOW "
    "RECTANGULAR FRAME of size fh × "
    "fw (fh, fw ∈ 3-4) drawn at a "
    "random non-overlapping interior "
    "position in palette[0] color; "
    "(b) 1-2 SOLID 2×2 BLOBS in "
    "palette[1:] colors (distinct "
    "from frame color), placed at "
    "random non-touching positions "
    "(no 4-adjacency with other "
    "blobs or the frame). Palette "
    "drawn from {1..9}\\{0}. Rule "
    "(KEEP BLOBS WHOSE BBOX "
    "INTERIOR HAS AT LEAST ONE "
    "0-CELL FULLY ENCLOSED BY THE "
    "BLOB (HOLEY OBJECTS); DROP "
    "BLOBS WITH NO HOLES (SOLID "
    "OBJECTS)): EXTRACT every 4-"
    "connected non-bg COMPONENT. "
    "For EACH: COMPUTE its bbox; "
    "CHECK if any 0-cell inside "
    "the bbox is fully enclosed "
    "by the component's cells. "
    "IF YES (holey): KEEP. IF "
    "NO (solid): ERASE every cell "
    "of the blob to 0. Net: "
    "hollow frames survive; solid "
    "blobs vanish."
)

INVARIANTS = [
    "background is 0",
    "≥1 closed rect-frame ≥3×3 (kept)",
    "≥1 solid blob (≥1×1 with no interior 0)",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_solid", "all_holed", "no_objects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 11..13", "valid": "9..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "frame_plus_solid_blobs",
                          "valid": "frame_plus_solid_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all values in 0-9; grid shape consistent."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if not (0 <= v <= 9):
                errs.append(f"cell ({r},{c}) value {v} out of 0-9 range")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 13, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    for _ in range(40):
        fh = rng.randint(3, 4); fw = rng.randint(3, 4)
        r1 = rng.randint(0, h - fh)
        c1 = rng.randint(0, w - fw)
        r2 = r1 + fh - 1; c2 = c1 + fw - 1
        if _free(g, r1, c1, r2, c2):
            for c in range(c1, c2 + 1):
                g[r1][c] = palette[0]; g[r2][c] = palette[0]
            for r in range(r1, r2 + 1):
                g[r][c1] = palette[0]; g[r][c2] = palette[0]
            break
    used = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 0}
    for color in palette[1:]:
        for _ in range(40):
            r1 = rng.randint(0, h - 2)
            c1 = rng.randint(0, w - 2)
            cells = {(r1, c1), (r1, c1 + 1), (r1 + 1, c1), (r1 + 1, c1 + 1)}
            if cells & used:
                continue
            ok = True
            for r, c in cells:
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells and g[nr][nc] != 0:
                        ok = False; break
                if not ok: break
            if not ok: continue
            for r, c in cells:
                g[r][c] = color
            used |= cells
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "all_solid":
        for r, c in [(1, 1), (1, 2), (2, 1), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 6), (6, 7)]: g[r][c] = 6
        for r, c in [(8, 2), (8, 3)]: g[r][c] = 8
        return g
    if name == "all_holed":
        for c in range(1, 4): g[1][c] = 4; g[3][c] = 4
        g[2][1] = 4; g[2][3] = 4
        for c in range(6, 9): g[6][c] = 6; g[8][c] = 6
        g[7][6] = 6; g[7][8] = 6
        return g
    if name == "no_objects":
        return g
    return g
