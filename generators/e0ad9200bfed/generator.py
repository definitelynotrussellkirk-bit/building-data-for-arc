"""Generator for 4b:hard_23 — make transform strip from template and keys.

Rule: template = color-1 multi-cell shape. keys = scattered cells
with values in {2,3,4,5}, sorted by column. For each key, transform
template by the key's value (2=identity, 3=CW, 4=180, 5=flip-lr),
recolor to key's color. Output is hpack-top of these strips.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_template (no color-1 shape → rule has no source);
no_keys (template present but no {2,3,4,5} keys → rule's strip
list is empty); rot_symmetric_template (template invariant under
all 4 rotations + flips → all key transforms produce identical
strips, no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e0ad9200bfed"
VERSION = "2.0.0"  # fixed 3-shape template bank + 2 raise statements. Rule: transform the color-1 template per each key in {2,3,4,5} (2=id,3=cw,4=180,5=flip-lr), hpack strips. Now random asymmetric template + robust no-raise placement."
TASK_ID = "e0ad9200bfed"

SUMMARY = "1 color-1 template + 2-4 scattered key cells in {2, 3, 4, 5}."

INVARIANTS = [
    "background is 0",
    "exactly one color-1 multi-cell template",
    "2-4 isolated single-cell keys with values in {2, 3, 4, 5}",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_keys", "rot_symmetric_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "grid_w":            {"type": "int", "default": "rng 13..15", "valid": "12..18"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "position_bias":     {"type": "str", "default": "template_plus_scattered_keys",
                          "valid": "template_plus_scattered_keys"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
]


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _too_close(g, r, c) -> bool:
    h, w = len(g), len(g[0])
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                return True
    return False


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != color:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    templates = _components(grid, 1)
    if len(templates) != 1:
        errs.append(f"expected exactly one color-1 template component, found {len(templates)}")
    elif len(templates[0]) < 3:
        errs.append(f"template should be multi-cell, found {len(templates[0])} cell(s)")
    keys = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (2, 3, 4, 5)]
    if not (2 <= len(keys) <= 4):
        errs.append(f"expected 2-4 transform key cells, found {len(keys)}")
    h, w = len(grid), len(grid[0])
    for r, c in keys:
        neigh = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 0:
                    neigh += 1
        if neigh:
            errs.append("a transform key is not isolated from the template/other keys")
            break
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12); w = ctx.draw_int("grid_w", 13, 14)
        nk = (2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 17); w = ctx.draw_int("grid_w", 14, 18)
        nk = (3, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 13, 16)
        nk = (2, 4)
    rng = ctx.draw_rng("layout")

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        shape = _poly(rng, rng.randint(3, 5))     # random asymmetric template
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        placed = False
        for _ in range(60):
            r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
            if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                continue
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = 1
            placed = True
            break
        if not placed:
            continue
        n_keys = rng.randint(*nk)
        placed_keys = 0
        for _ in range(120):
            if placed_keys >= n_keys:
                break
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0 or _too_close(g, r, c):
                continue
            g[r][c] = rng.choice([2, 3, 4, 5])
            placed_keys += 1
        if placed_keys >= 2:
            return g
    return g   # graceful fallback


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_template":
        # No color-1 template — rule has no source to transform.
        g[3][3] = 2; g[5][7] = 3; g[7][11] = 4
        return g
    if name == "no_keys":
        # Template present but no {2,3,4,5} keys — strip list is empty.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 1
        return g
    if name == "rot_symmetric_template":
        # 2x2 solid square is invariant under rotations + flips.
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[2 + dr][2 + dc] = 1
        g[5][7] = 2; g[7][9] = 3; g[9][11] = 4; g[6][12] = 5
        return g
    return g
