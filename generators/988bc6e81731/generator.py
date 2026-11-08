"""Generator for 17b:m119 — scale the only horizontally symmetric object.

Rule: of the connected components, exactly one's normalized binary
shape is left-right (horizontal) mirror symmetric. Output is that
shape scaled 2x in its color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_symmetric (no LR-symmetric component → rule's
selector finds nothing), all_symmetric (every component is LR-symmetric
→ "exactly one" precondition fails), single_motif (only one component
→ trivially the symmetric one, no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "988bc6e81731"
VERSION = "2.1.0"  # FIX all_background_output (7/18 seeds): the random LR-symmetric target often FILLED its bbox -> the 2x-upscaled crop was a single solid color. Require the symmetric target to NOT fill its bbox (>=1 interior hole) so the output keeps background 0. + self_check.
TASK_ID = "988bc6e81731"
SUMMARY = "Several connected components; exactly one is left-right (horizontal-mirror) symmetric in its bbox crop. Rule outputs that component's crop scaled 2x in its own color. The symmetric target is a random mirror-symmetric polyomino; distractors are verified non-symmetric."

# Rivals: 'pick the largest' refuted by ≥2 demos where the symmetric
# one isn't the largest. 'pick the first' refuted by ≥1 demo where
# top-left isn't the symmetric one. 'recolor to a fixed output color'
# refuted by any demo (output uses the picked color). 'no scaling'
# refuted by any demo (output is 2× crop). 3 demos with varied
# component sets cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-3 isolated 4-connected components, distinct colors",
    "exactly one's bbox-normalized binary shape is LR-mirror symmetric",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_symmetric", "all_symmetric", "single_motif")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "10..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "one_sym_plus_distractors",
                       "valid": "one_sym_plus_distractors"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_LR_SYM = [
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 3)],
]
_ASYM = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
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
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    return cells


def _normalize(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return sorted((r - rmin, c - cmin) for r, c in cells)


def _is_lr_sym(cells):
    n = _normalize(cells)
    wmax = max(c for _, c in n)
    return n == sorted((r, wmax - c) for r, c in n)


def _connected(cells):
    cs = set(cells); start = next(iter(cs)); seen = {start}; stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            n = (r + dr, c + dc)
            if n in cs and n not in seen:
                seen.add(n); stack.append(n)
    return len(seen) == len(cs)


def _rand_lr_sym(rng):
    """Random LR-mirror-symmetric connected polyomino (built by unioning a
    random poly with its left-right mirror), bbox <= 6x6."""
    for _ in range(120):
        base = _rand_poly(rng, rng.randint(2, 7))
        wmax = max(c for _, c in base)
        u = set(base) | {(r, wmax - c) for r, c in base}
        n = _normalize(u)
        hh = max(r for r, _ in n) + 1; ww = max(c for _, c in n) + 1
        # Require an interior hole (shape must NOT fill its bbox) so the
        # 2x-upscaled crop keeps background 0 and is never a solid block.
        if hh <= 6 and ww <= 6 and _connected(n) and len(n) < hh * ww:
            return n
    return _LR_SYM[0]


def _rand_asym(rng):
    """Random connected polyomino whose crop is NOT LR-symmetric."""
    for _ in range(60):
        s = _normalize(_rand_poly(rng, rng.randint(3, 6)))
        if not _is_lr_sym(s):
            return s
    return _ASYM[0]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n_asym = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 16, 20)
        n_asym = rng.randint(3, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 13, 16)
        n_asym = rng.randint(1, 3)
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 1 + n_asym)
    _place(g, rng, _rand_lr_sym(rng), palette[0])
    for color in palette[1:]:
        _place(g, rng, _rand_asym(rng), color)
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]; stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen \
                            and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Exactly one 4-connected component's bbox-crop is LR-mirror symmetric,
    and that crop is not a solid block (keeps background in the output).
    Returns a list of violation strings (empty == pass)."""
    msgs = []
    comps = _components(grid)
    if len(comps) < 2:
        msgs.append(f"need >=2 components, got {len(comps)}")
        return msgs
    syms = [cells for _col, cells in comps if _is_lr_sym(cells)]
    if len(syms) != 1:
        msgs.append(f"expected exactly one LR-symmetric component, got {len(syms)}")
    else:
        n = _normalize(syms[0])
        hh = max(r for r, _ in n) + 1; ww = max(c for _, c in n) + 1
        if len(n) >= hh * ww:
            msgs.append("symmetric target fills its bbox (solid output)")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 11, 13
    g = full_grid(h, w, 0)
    if name == "no_symmetric":
        # No LR-symmetric component — rule's selector finds nothing.
        for dr, dc in _ASYM[0]: g[1 + dr][1 + dc] = 4
        for dr, dc in _ASYM[2]: g[5 + dr][7 + dc] = 6
        return g
    if name == "all_symmetric":
        # Every component is LR-symmetric → "exactly one" precondition
        # fails; rule's selector is ambiguous.
        for dr, dc in _LR_SYM[1]: g[1 + dr][1 + dc] = 4
        for dr, dc in _LR_SYM[2]: g[6 + dr][8 + dc] = 6
        return g
    if name == "single_motif":
        # Only one component — trivially the "the only" symmetric;
        # no contrast across candidates.
        for dr, dc in _LR_SYM[0]: g[3 + dr][5 + dc] = 7
        return g
    return g
