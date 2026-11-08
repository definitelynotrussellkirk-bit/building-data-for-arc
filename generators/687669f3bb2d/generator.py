"""Generator for 3b:hard_16 — scale the unique vertically symmetric component.

Rule: among color-3 components, pick the first whose normalized cells
form a vertically (LR-mirror) symmetric shape. Output is that shape
2x-upscaled, painted color 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_vsym (no symmetric component → rule selects nothing),
all_vsym (every component is symmetric → first-match makes selection
order-sensitive), single_component (only one shape → no contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "687669f3bb2d"
VERSION = "3.2.0"  # avoid solid-target outputs + FIX crash: _rand_vsym seeded two disconnected mirror cells, so objects g 0 (4-conn) split the green blob -> no single vsym component -> rule's (first (filter...)) crashed. Now grow from a self-mirroring centre column (odd width) so the shape is 4-connected AND LR-symmetric.
TASK_ID = "687669f3bb2d"

SUMMARY = (
    "0-bg grid (h~11-13, w~13-15) with multiple ISOLATED "
    "color-3 (green) connected components. EXACTLY ONE is "
    "VERTICALLY (LR-mirror) SYMMETRIC — its normalized cells "
    "are invariant under flip-lr. The other 1-2 components are "
    "ASYMMETRIC under that mirror. Components are buffered by "
    "≥1 bg cell on all sides. Rule: scan color-3 objects in "
    "scan order. Pick the FIRST one whose normalized cells are "
    "LR-mirror symmetric. Compute its scaled offsets at factor "
    "2 (each cell becomes a 2×2 block). Output is a small grid "
    "sized to fit the scaled cells, painted color 8 (cyan)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "1 color-3 component is vertically (LR) mirror-symmetric",
    "1-2 other color-3 components are NOT vertically symmetric",
    "all components are isolated (no 4-connectivity bridging)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_vsym", "all_vsym", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "grid_w":         {"type": "int", "default": "rng 13..15", "valid": "12..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "one_vsym_with_asym_distractors",
                       "valid": "one_vsym_with_asym_distractors"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_VSYM = [
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],          # plus
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)],   # H
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],          # T
    [(0, 1), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],  # U
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)],  # n
    [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],          # X
    [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 2)],  # T-wide
    [(0, 1), (0, 2), (0, 3), (1, 0), (1, 4), (2, 1), (2, 2), (2, 3)],  # diamond-ring
    [(0, 2), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],  # triangle
    [(0, 1), (0, 2), (0, 3), (1, 2), (2, 0), (2, 4)],  # Y
    [(0, 2), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],  # T-tall
]
_ASYM = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 1), (1, 0), (1, 1), (2, 0)],
    [(0, 0), (1, 0), (1, 1), (1, 2)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place_or_raise(g, rng, shape, color, label):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(60):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return
    raise ValueError(f"could not place {label}")


def _norm(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return sorted((r - r0, c - c0) for r, c in cells)


def _is_vsym(cells):
    """True if the normalized cell set is invariant under LR mirror."""
    n = _norm(cells)
    maxc = max(c for _, c in n)
    return n == sorted((r, maxc - c) for r, c in n)


def _bbox_area(cells):
    n = _norm(cells)
    return (max(r for r, _ in n) + 1) * (max(c for _, c in n) + 1)


def _rand_vsym(rng, maxh, maxw, target):
    """Random LR-mirror-symmetric, 4-CONNECTED polyomino.  Reject solid
    rectangles: their 2x upscaled output is a featureless all-8 block, which
    hides the selected-shape rule and trips the generic solid-output detector."""
    odd = [w for w in range(3, max(3, maxw) + 1) if w % 2 == 1]
    for _shape_try in range(120):
        W = rng.choice(odd)
        center = W // 2
        mir = lambda c: W - 1 - c
        r0 = rng.randint(0, maxh - 1)
        S = {(r0, center)}
        for _ in range(600):
            if len(S) >= target:
                break
            br, bc = rng.choice(list(S))
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = br + dr, bc + dc
            if 0 <= nr < maxh and 0 <= nc < W:
                S.add((nr, nc)); S.add((nr, mir(nc)))
        n = _norm(S)
        if len(n) < _bbox_area(n):
            return n
    return _VSYM[0]


def _rand_asym(rng, maxh, maxw, target):
    """Random connected polyomino that is NOT LR-symmetric."""
    for _ in range(60):
        cells = [(0, 0)]; seen = {(0, 0)}
        for _ in range(400):
            if len(cells) >= target:
                break
            br, bc = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = br + dr, bc + dc
            if (nr, nc) not in seen and 0 <= nr < maxh and 0 <= nc < maxw:
                cells.append((nr, nc)); seen.add((nr, nc))
        n = _norm(cells)
        if not _is_vsym(n):
            return n
    return [(0, 0), (0, 1), (1, 0)]  # fallback L-tromino (asymmetric)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 13, 13)
        n_asym = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 15, 18)
        n_asym = 2
    else:
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 15)
        n_asym = None
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # EXACTLY ONE LR-symmetric color-3 component (the rule's target),
    # built fresh each instance so the scaled output shape varies widely.
    vsym = _rand_vsym(rng, maxh=rng.randint(4, 6), maxw=rng.randint(4, 7),
                      target=rng.randint(7, 16))
    _place_or_raise(g, rng, vsym, 3, "v-symmetric")
    if n_asym is None:
        n_asym = rng.randint(1, 2)
    for _ in range(n_asym):
        asym = _rand_asym(rng, maxh=rng.randint(2, 4), maxw=rng.randint(2, 4),
                          target=rng.randint(3, 5))
        _place_or_raise(g, rng, asym, 3, "asymmetric")
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Exactly one 4-connected color-3 component must be LR-symmetric (the rule
    selects the first such; zero would crash it). Returns violation list."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sr in range(h):
        for sc in range(w):
            if seen[sr][sc] or grid[sr][sc] != 3:
                continue
            stack = [(sr, sc)]; seen[sr][sc] = True; cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == 3):
                        seen[nr][nc] = True; stack.append((nr, nc))
            comps.append(cells)
    vsym_comps = [cells for cells in comps if _is_vsym(cells)]
    n_vsym = len(vsym_comps)
    out = []
    if n_vsym != 1:
        out.append(f"need exactly one LR-symmetric color-3 component, got {n_vsym}")
    elif len(vsym_comps[0]) == _bbox_area(vsym_comps[0]):
        out.append("selected LR-symmetric component must not be a solid rectangle")
    if len(comps) < 2:
        out.append(f"need a distractor: got {len(comps)} color-3 component(s)")
    return out


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_vsym":
        # Only asymmetric components — rule's "first vsym" selector
        # finds nothing; output undefined.
        for shape, base in [(_ASYM[0], (1, 1)), (_ASYM[1], (5, 8)), (_ASYM[2], (8, 2))]:
            for dr, dc in shape:
                g[base[0] + dr][base[1] + dc] = 3
        return g
    if name == "all_vsym":
        # Every component is symmetric — rule's "first-match" makes
        # selection depend on scan order, not a property of the input.
        for shape, base in [(_VSYM[0], (1, 1)), (_VSYM[1], (5, 7)), (_VSYM[2], (8, 2))]:
            for dr, dc in shape:
                g[base[0] + dr][base[1] + dc] = 3
        return g
    if name == "single_component":
        # Only one component — selector is trivial; no asymmetric
        # distractors so the rule has no contrast to demonstrate.
        for dr, dc in _VSYM[0]:
            g[2 + dr][5 + dc] = 3
        return g
    return g
