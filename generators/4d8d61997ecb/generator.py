"""Generator for arc_puzzle_bank_sixth21:H38 — stamp the rotated template at each marker.

Rule: cell (0,0) is a ROTATION CODE (1=identity, 2=rotate-cw, 3=rotate-180,
else=rotate-ccw). The LARGEST object (excluding colors {0, 9, code}) is the
template; rotate it by the code, then stamp the rotated pattern (top-left
anchored) at every color-9 MARKER cell, on a blank output of the input size.

The old docstring called this a "multi-motif gallery pack" and the generator
scattered random motifs with no rotation code and no color-9 markers, so the
rule's structure (code + template + markers) was absent. Now: a deliberate
code at (0,0), one template object (the largest), and 2-4 color-9 markers with
room for the rotated stamp.

Combinatorial axes: rotation code, the template shape/size, marker count and
positions, the template color, grid size.
Degenerates: no_code, no_template, no_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4d8d61997ecb"
VERSION = "2.0.1"  # WRONG-TASK ('gallery pack' docstring): rule reads a rotation code at (0,0), rotates the LARGEST object, and stamps it at every color-9 marker. Old gen scattered motifs (no code, no markers). Now deliberate code + one template + 2-4 color-9 markers with room for the rotated stamp.
TASK_ID = "4d8d61997ecb"
SUMMARY = (
    "0-bg grid (size varies). Cell (0,0) holds a ROTATION CODE in {1,2,3,4}. "
    "One TEMPLATE object (a random connected polyomino, 3-8 cells, the largest "
    "non-{0,9,code} object) sits in the grid, plus 2-4 color-9 MARKER cells "
    "positioned with room for the rotated stamp. Rule: rotate the template by "
    "the code (1=id, 2=cw, 3=180, else=ccw) and stamp it (top-left anchored) at "
    "every color-9 marker on a blank output. Output = the rotated template "
    "repeated at the marker positions."
)

INVARIANTS = [
    "cell (0,0) is a rotation code in {1,2,3,4}",
    "exactly one template object (the largest non-{0,9,code} object, size > 1)",
    "2-4 color-9 marker cells, each with room for the rotated stamp",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_code", "no_template", "no_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "rot_code":       {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "n_markers":      {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "code_template_markers",
                       "valid": "code_template_markers"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_code|no_template|no_markers"},
}


def _build_motif(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for (r, c) in cells]


def _free(g, top, left, oh, ow):
    h, w = len(g), len(g[0])
    for r in range(max(0, top - 1), min(h, top + oh + 1)):
        for c in range(max(0, left - 1), min(w, left + ow + 1)):
            if g[r][c] != 0:
                return False
    return 0 <= top and 0 <= left and top + oh <= h and left + ow <= w


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 9, 11); nm = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16); nm = rng.randint(3, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 10, 13); nm = rng.randint(2, 3)

    code = ctx.draw_int("rot_code", 1, 4)
    tcolor = rng.choice([c for c in (1, 2, 3, 4, 5, 6, 7, 8) if c != code])

    for _outer in range(40):
        g = full_grid(h, w, 0)
        g[0][0] = code
        template = _build_motif(rng, rng.randint(3, 8))
        th = max(r for r, _ in template) + 1
        tw = max(c for _, c in template) + 1
        # rotated stamp dims (cw/ccw swap dims)
        rh, rw = (tw, th) if code in (2, 4) else (th, tw)
        if th > h or tw > w or rh > h or rw > w:
            continue
        # place template (avoid (0,0) area)
        placed = False
        for _ in range(80):
            tr = rng.randint(0, h - th); tc = rng.randint(0, w - tw)
            if _free(g, tr, tc, th, tw):
                for dr, dc in template:
                    g[tr + dr][tc + dc] = tcolor
                placed = True
                break
        if not placed:
            continue
        # markers (color 9), each with room for the rotated stamp
        mk = 0
        for _ in range(200):
            if mk >= nm:
                break
            mrk = rng.randint(0, h - rh)
            mck = rng.randint(0, w - rw)
            if g[mrk][mck] == 0 and (mrk, mck) != (0, 0):
                g[mrk][mck] = 9
                mk += 1
        if mk >= 2:
            return g
    raise ValueError("could not realize 4d8d layout")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify rotation-code + template + markers invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    problems = []
    code = grid[0][0]
    if code not in (1, 2, 3, 4):
        problems.append(f"(0,0) rotation code should be in {{1,2,3,4}}, found {code}")
    flat = [v for row in grid for v in row]
    count9 = flat.count(9)
    if count9 < 2:
        problems.append(f"expected >=2 color-9 marker cells, found {count9}")
    template_cells = [v for v in flat if v not in (0, 9, code)]
    if not template_cells:
        problems.append("no template cells found (non-{0,9,code} cells)")
    return problems


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    g[0][0] = 2
    if name == "no_code":
        g[0][0] = 0
        g[3][3] = 7; g[3][4] = 7; g[4][3] = 7
        g[6][6] = 9
        return g
    if name == "no_template":
        g[6][6] = 9
        return g
    if name == "no_markers":
        g[3][3] = 7; g[3][4] = 7; g[4][3] = 7
        return g
    g[3][3] = 7; g[3][4] = 7; g[4][3] = 7
    g[7][7] = 9
    return g
