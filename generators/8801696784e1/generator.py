"""Generator for 15b:hard_102 — select symmetric object, rotate, scale 2x.

Rule: code at (h-1, w-1). Among shapes whose crop is both LR- and UD-
symmetric, the largest is picked. Output: that crop transformed per
code, then upscaled 2x.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_symmetric (no LR+UD-symmetric component → rule's
selector finds nothing, output undefined), all_symmetric (every
component is symmetric → tie-break decides which is "largest"),
no_code (cell (h-1, w-1) is bg → transform is identity by default).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8801696784e1"
VERSION = "3.3.0"  # strict overrides/types; preserves the canonical rule. FIX all_background_output: v3.x random symmetric polyominoes were often FULLY FILLED bboxes, so the output (crop upscaled 2x) was a single solid color -> flagged. The canonical outputs (and the 3 seed templates: frame/cross/X) all have INTERIOR background. Now require the symmetric shape to NOT fill its bbox (>=1 hole) so the cropped output always contains 0.
TASK_ID = "8801696784e1"
SUMMARY = (
    "0-bg grid (h~9-11, w~"
    "11-13) with: (a) TRANSFORM "
    "CODE at (h-1, w-1) in "
    "value {1, 2, 3} (encodes "
    "rotation 0°/90°/180° or "
    "similar); (b) ONE "
    "LR+UD-SYMMETRIC SHAPE "
    "drawn from 3 hardcoded "
    "SYMMETRIC TEMPLATES "
    "(3×3 frame, +cross, "
    "X-pattern) in a random "
    "color from {2, 4, 5, 6, "
    "7, 8, 9}; (c) ONE "
    "ASYMMETRIC SHAPE drawn "
    "from 3 hardcoded "
    "ASYM TEMPLATES (L-shape, "
    "corner-tromino, J-shape) "
    "in a distinct random "
    "color. Shapes placed "
    "non-overlapping with 1-"
    "cell padding. Output "
    "uniq_out=17 (intrinsic — "
    "3 symmetric templates × "
    "3 codes × upscale "
    "normalizes). Rule "
    "(PICK SYMMETRIC SHAPE, "
    "TRANSFORM BY CODE, "
    "UPSCALE 2x): identify "
    "the CODE at (h-1, w-1). "
    "AMONG components whose "
    "CROP is BOTH LR- AND "
    "UD-SYMMETRIC, PICK the "
    "LARGEST. APPLY the "
    "CODE's TRANSFORM "
    "(rotation/flip) to that "
    "crop. UPSCALE 2× "
    "(double dims). EMIT "
    "the result as output. "
    "Net: largest LR+UD-sym "
    "shape, transformed and "
    "2× upscaled."
)

INVARIANTS = [
    "background is 0",
    "cell (h-1, w-1) is a transform code in {1, 2, 3}",
    "exactly one component whose crop is both LR- and UD-symmetric",
    "1 other asymmetric component (smaller or non-symmetric)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_symmetric", "all_symmetric", "no_code")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "10..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "code_plus_sym_plus_asym",
                       "valid": "code_plus_sym_plus_asym"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_INT_AXES = {
    "grid_h": (8, 14),
    "grid_w": (10, 17),
    "palette_size": (2, 2),
    "n_distinct_colors": (2, 2),
}
_ENUM_AXES = {
    "palette_kind": set(PALETTE_KINDS),
    "position_bias": {"code_plus_sym_plus_asym"},
    "density": {"sparse"},
    "texture": set(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
}
_PALETTES = {
    "default": (2, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 6, 9),
    "cool": (5, 7, 8),
    "varied": (2, 4, 5, 6, 7, 8, 9),
}


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, (low, high) in _INT_AXES.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} override must be an integer in {low}..{high}")
    for name, choices in _ENUM_AXES.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not str or value not in choices:
            raise ValueError(f"{name} override must be one of {sorted(choices)}")


def _draw_int(ctx, overrides, name, low, high):
    return overrides[name] if name in overrides else ctx.draw_int(name, low, high)


_SYMMETRIC = [
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],
]
_ASYM = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(0, h - sh - 1); c0 = rng.randint(0, w - sw - 1)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def _norm(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return sorted((r - rmin, c - cmin) for r, c in cells)


def _connected(cells):
    cs = set(cells); start = next(iter(cs)); seen = {start}; stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            n = (r + dr, c + dc)
            if n in cs and n not in seen:
                seen.add(n); stack.append(n)
    return len(seen) == len(cs)


def _both_sym(cells):
    n = _norm(cells); hh = max(r for r, _ in n) + 1; ww = max(c for _, c in n) + 1
    return (n == sorted((r, ww - 1 - c) for r, c in n) and
            n == sorted((hh - 1 - r, c) for r, c in n))


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    return _norm(cells)


def _rand_both_sym(rng):
    """Random LR+UD-symmetric connected polyomino (quadrant mirrored), bbox<=6x6."""
    for _ in range(160):
        base = _rand_poly(rng, rng.randint(2, 6))
        s = set(base)
        ww = max(c for _, c in base)
        s |= {(r, ww - c) for r, c in base}
        hh = max(r for r, _ in s)
        s |= {(hh - r, c) for r, c in s}
        n = _norm(s)
        hh = max(r for r, _ in n) + 1; ww = max(c for _, c in n) + 1
        # Require an interior hole (shape must NOT fill its bbox) so the
        # cropped output keeps background 0 and is never a solid block.
        if hh <= 6 and ww <= 6 and _connected(n) and _both_sym(n) \
           and len(n) >= 3 and len(n) < hh * ww:
            return n
    return _SYMMETRIC[0]


def _rand_asym(rng):
    for _ in range(60):
        s = _rand_poly(rng, rng.randint(3, 5))
        if not _both_sym(s):
            return s
    return _ASYM[0]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = _draw_int(ctx, overrides, "grid_h", 9, 11)
        w = _draw_int(ctx, overrides, "grid_w", 11, 13)
    elif difficulty == "hard":
        h = _draw_int(ctx, overrides, "grid_h", 12, 14)
        w = _draw_int(ctx, overrides, "grid_w", 14, 17)
    else:
        h = _draw_int(ctx, overrides, "grid_h", 10, 13)
        w = _draw_int(ctx, overrides, "grid_w", 12, 16)
    rng = ctx.draw_rng("layout")
    palette_kind = overrides.get("palette_kind")
    texture = overrides.get("texture")
    if palette_kind is None and texture in HELPFUL_TEXTURES:
        palette_kind = texture
    palette = rng.sample(list(_PALETTES[palette_kind or "default"]), 2)
    # Canonical program maps bottom-right codes 1,2,3; 4..7 were out-of-task noise.
    code = rng.choice([1, 2, 3])
    for _layout_try in range(80):
        g = full_grid(h, w, 0)
        g[h - 1][w - 1] = code
        sym = _rand_both_sym(rng)
        asym = _rand_asym(rng)
        for _ in range(80):
            if len(sym) > len(asym):
                break
            sym = _rand_both_sym(rng)
            asym = _rand_asym(rng)
        if len(sym) <= len(asym):
            continue
        if _place(g, rng, sym, palette[0]) and _place(g, rng, asym, palette[1]):
            return g
    raise ValueError("could not place unique larger symmetric target and asymmetric distractor")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    g[h - 1][w - 1] = 1
    if name == "no_symmetric":
        # No LR+UD-symmetric component — rule's selector finds
        # nothing; output undefined.
        for dr, dc in _ASYM[0]: g[2 + dr][2 + dc] = 4
        for dr, dc in _ASYM[2]: g[2 + dr][7 + dc] = 6
        return g
    if name == "all_symmetric":
        # All components are LR+UD-symmetric — rule's "largest"
        # tie-break decides; selection ambiguous.
        for dr, dc in _SYMMETRIC[1]: g[2 + dr][2 + dc] = 4
        for dr, dc in _SYMMETRIC[2]: g[5 + dr][7 + dc] = 6
        return g
    if name == "no_code":
        # Cell (h-1, w-1) is bg — transform code missing; rule
        # defaults to identity transform.
        g[h - 1][w - 1] = 0
        for dr, dc in _SYMMETRIC[0]: g[2 + dr][2 + dc] = 4
        for dr, dc in _ASYM[1]: g[3 + dr][8 + dc] = 6
        return g
    return g



def _same_color_components_without_code(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) == (h - 1, w - 1) or (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if ((nr, nc) == (h - 1, w - 1) or not (0 <= nr < h and 0 <= nc < w)
                            or (nr, nc) in seen or grid[nr][nc] != color):
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)):
        return ["grid is empty or ragged"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["every ARC cell must be an exact integer in 0..9"]
    h, w = len(grid), len(grid[0])
    code = grid[h - 1][w - 1]
    if code not in {1, 2, 3}:
        errs.append(f"bottom-right transform code must be 1..3, got {code}")
    comps = _same_color_components_without_code(grid)
    sym = []
    asym = []
    for _color, cells in comps:
        if _both_sym(cells):
            sym.append(cells)
        else:
            asym.append(cells)
    if len(sym) != 1:
        errs.append(f"expected exactly one LR+UD symmetric selectable object, found {len(sym)}")
    if not asym:
        errs.append("missing asymmetric distractor object")
    if sym and asym and len(sym[0]) <= max(len(c) for c in asym):
        errs.append("symmetric target is not strictly larger than every distractor")
    return errs
