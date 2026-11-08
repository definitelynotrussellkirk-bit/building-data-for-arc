"""Generator for arc_additional_puzzles_21_set18_bundle:H126 — transform and palette by example.

Rule: 3 isolated multicolor components sorted by (r1, c1). A and A' show a
dihedral transform plus a per-cell color mapping. B is the query: output is
transform(B) recolored via the inferred map.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: identity_transform (t=0 → A == A', no transform to infer);
no_recolor (cmap is identity → no palette shift to infer);
no_query (only A and A', no B → nothing to apply rule to).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3bad71db5197"
VERSION = "1.2.2"  # require full-D4-unique visible geometry without rare construction failure
TASK_ID = "3bad71db5197"

SUMMARY = "3 isolated multicolor components: A, transform(A) recolored, and an independent B."

INVARIANTS = [
    "background is 0",
    "exactly 3 isolated non-bg multicolor components sorted by (r1, c1)",
    "first two are related by one full-D4-unique transform plus a one-to-one color permutation",
    "third component is independent",
    "B uses colors that are present in A's palette (so the inferred map covers them)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("identity_transform", "no_recolor", "no_query")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 10..12", "valid": "9..14"},
    "grid_w":            {"type": "int", "default": "rng 13..16", "valid": "11..18"},
    "transform":         {"type": "int", "default": "rng 1..5", "valid": "0..5"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..6", "valid": "4..8"},
    "position_bias":     {"type": "str", "default": "three_motifs_sorted",
                          "valid": "three_motifs_sorted"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "4..8"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _xform_grid(g, t):
    if t == 0: return [row[:] for row in g]
    if t == 1:
        h, w = len(g), len(g[0])
        return [[g[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if t == 2: return [row[::-1] for row in g[::-1]]
    if t == 3:
        h, w = len(g), len(g[0])
        return [[g[r][c] for r in range(h)] for c in range(w)]
    if t == 4: return [row[::-1] for row in g]
    return g[::-1]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k, palette):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sr0, sc0 = -min(rs), -min(cs)
    sh = max(rs) - min(rs) + 1
    sw = max(cs) - min(cs) + 1
    grid = [[0] * sw for _ in range(sh)]
    for i, (r, c) in enumerate(cells):
        grid[sr0 + r][sc0 + c] = palette[i % len(palette)]
    return grid


def _recolor(grid, cmap):
    h, w = len(grid), len(grid[0])
    return [[cmap.get(grid[r][c], grid[r][c]) for c in range(w)] for r in range(h)]


def _support(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not cells:
        return ()
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _xform_support(grid, t):
    return _support(_xform_grid([[1 if v else 0 for v in row] for row in grid], t))


def _matching_geom_codes(a, ap):
    # Check uniqueness against the full dihedral group, not just the subset used
    # to draw defaults.  Otherwise a demo can visually fit two transforms (for
    # example rot270 and mirror), hiding the rule even though the sampled code is
    # one of the supported defaults.
    from puzzle_generators.helpers.selfcheck import d4_transform
    source = _support([[1 if v else 0 for v in row] for row in a])
    target = _support([[1 if v else 0 for v in row] for row in ap])
    return [code for code in range(8) if d4_transform(source, code) == target]


def _paint(g, top, left, motif):
    sh, sw = len(motif), len(motif[0])
    for r in range(sh):
        for c in range(sw):
            if motif[r][c] != 0:
                g[top + r][left + c] = motif[r][c]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 13, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 15, 16)
    else:
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 13, 16)
    t = ctx.draw_int("transform", 1, 5)
    rng = ctx.draw_rng("layout")

    for outer in range(160):
        n_colors = rng.randint(2, 3)
        a_palette = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n_colors)
        b_palette = rng.sample([c for c in [2, 3, 4, 5, 6, 7, 8, 9] if c not in a_palette], n_colors)
        cmap = dict(zip(a_palette, b_palette))

        a = _build_motif(rng, rng.randint(3, 5), a_palette)
        ap_geom = _xform_grid(a, t)
        # A->A' must demonstrate a single visible geometry transform; recolor alone
        # is not enough because it hides the transform branch from the learner.
        if len(_matching_geom_codes(a, ap_geom)) != 1 or _xform_support(a, t) == _support(a):
            continue
        ap = _recolor(ap_geom, cmap)
        if a == ap:
            continue
        b = _build_motif(rng, rng.randint(3, 5), a_palette)
        if _xform_support(b, t) == _support(b):
            continue

        g = full_grid(h, w, 0)
        positions = []
        ok = True
        for motif in (a, ap, b):
            sh, sw = len(motif), len(motif[0])
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                if positions and (r0, c0) <= positions[-1]: continue
                _paint(g, r0, c0, motif)
                positions.append((r0, c0))
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place transform+palette analogy in 160 attempts")


def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = full_grid(h, w, 0)
    if name == "identity_transform":
        # A == A' (t=0) — no transform inferable.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 3
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][6 + dc] = 3
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[6 + dr][3 + dc] = 4
        return g
    if name == "no_recolor":
        # Transform present but cmap is identity — no palette shift.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 3
        for dr, dc in [(0, 0), (0, 1), (0, 1 if False else 1)]:
            pass
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[1 + dr][6 + dc] = 3
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[6 + dr][3 + dc] = 4
        return g
    if name == "no_query":
        # Only A and A' — no B.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[1 + dr][1 + dc] = 3
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[1 + dr][7 + dc] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    from puzzle_generators.helpers.selfcheck import components_cells as components, normalize, d4_transform
    comps = components(grid)
    if len(comps) != 3:
        return [f"expected exactly 3 separated components, found {len(comps)}"]
    color_sets = [{grid[r][c] for r, c in cells} for cells in comps]
    candidates = []
    for ai, a_cells in enumerate(comps):
        for api, ap_cells in enumerate(comps):
            if ai == api or not color_sets[ai].isdisjoint(color_sets[api]):
                continue
            a_shape = normalize(a_cells)
            ap_shape = normalize(ap_cells)
            codes = [code for code in range(8) if d4_transform(a_shape, code) == ap_shape]
            if len(codes) == 1 and codes[0] != 0:
                qi = ({0, 1, 2} - {ai, api}).pop()
                if color_sets[qi] <= color_sets[ai]:
                    candidates.append((ai, api, codes[0]))
    msgs = []
    if not candidates:
        msgs.append("no visible non-identity A->A' geometry witness")
        return msgs
    if not any(d4_transform(normalize(comps[({0, 1, 2} - {ai, api}).pop()]), code)
               != normalize(comps[({0, 1, 2} - {ai, api}).pop()])
               for ai, api, code in candidates):
        msgs.append("query component is unchanged by every plausible inferred transform")
    return msgs
