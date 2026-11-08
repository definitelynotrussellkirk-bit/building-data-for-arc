"""Generator for arc_puzzle_bank_21_set6_s:S6_M5 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "83f1b2ab7741"
VERSION = "2.0.1"
TASK_ID = "83f1b2ab7741"

SUMMARY = (
    "0-bg grid (h~10-13, w~12-16) containing: "
    "(a) EXACTLY ONE PAIR of COLOR-6 (magenta) "
    "MOTIFS where the second is a HORIZONTAL "
    "MIRROR of the first (asymmetric base shape "
    "such that mirror differs from original); "
    "(b) 0-2 additional COLOR-6 distractor "
    "motifs that are NEITHER the base nor its "
    "mirror (different normalized shape); (c) "
    "1-3 distractor MOTIFS in OTHER non-{0, 6} "
    "colors (2-4 cells each) placed at "
    "scattered positions. All motifs are "
    "non-touching (1-cell padding). Rule: among "
    "all color-6 components, find the UNIQUE "
    "PAIR (A, B) where normalize(B) = "
    "h_mirror(normalize(A)). RECOLOR both A "
    "and B to COLOR 2 (red). ERASE everything "
    "else (set all other cells, including other "
    "color-6 distractors and other-colored "
    "motifs, to 0). Net: only the unique "
    "horizontally-mirrored magenta pair "
    "survives, repainted red."
)

# Rivals: 'paint all color-6 components' refuted by ≥1 demo with ≥3
# color-6 motifs where only the mirror pair survives. 'paint matching
# shapes regardless of orientation' refuted by ≥1 demo where same
# shape exists but not mirrored. 'paint with original color' refuted
# by any demo (output is 2). 'preserve distractor colors' refuted by
# any demo (distractors erased).
# 4 demos with varied mirror pairs cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "3-4 connected motifs in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..17"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..20"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 color-6 components present (a matched pair + possibly more)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    sixes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6]
    if not sixes:
        return []  # no_motifs / all_same_color degenerate — allowed
    # count color-6 4-connected components
    visited = set()
    n_six_comps = 0
    for r0, c0 in sixes:
        if (r0, c0) not in visited:
            n_six_comps += 1
            queue = [(r0, c0)]
            visited.add((r0, c0))
            while queue:
                r, c = queue.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (nr, nc) not in visited and 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 6:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
    errs = []
    if n_six_comps < 2:
        errs.append(f"expected ≥2 color-6 components; found {n_six_comps}")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _normalize(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return sorted((r - r0, c - c0) for r, c in cells)


def _hmirror(cells):
    cs = [c for _, c in cells]
    cmax = max(cs)
    return sorted((r, cmax - c) for r, c in cells)


def _is_h_symmetric(cells):
    """A motif equal to its own horizontal mirror — would be its own pair."""
    return _normalize(cells) == _normalize(_hmirror(cells))


def _place_motif(g, cells, r0, c0, color):
    for r, c in cells:
        g[r0 + r][c0 + c] = color


def _can_place(g, cells, r0, c0):
    h, w = len(g), len(g[0])
    for r, c in cells:
        rr, cc = r0 + r, c0 + c
        if not (0 <= rr < h and 0 <= cc < w) or g[rr][cc] != 0:
            return False
    # 1-cell padding so motifs don't merge into one component.
    for r, c in cells:
        rr, cc = r0 + r, c0 + c
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if (0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0 and
                        (nr - r0, nc - c0) not in set(cells)):
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 11, 13)
        n_extras = ctx.draw_int("n_extras", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 17)
        w = ctx.draw_int("grid_w", 15, 20)
        n_extras = ctx.draw_int("n_extras", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
        n_extras = ctx.draw_int("n_extras", 2, 3)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        # 1. Build the matched color-6 pair (asymmetric motif + its mirror).
        for _ in range(20):
            motif = _build_motif(rng, rng.randint(3, 5))
            motif_n = _normalize(motif)
            if not _is_h_symmetric(motif_n):
                break
        else:
            continue
        mirror = _normalize(_hmirror(motif_n))
        mh = max(r for r, _ in motif_n) + 1
        mw = max(c for _, c in motif_n) + 1
        # Place both somewhere in the grid, non-overlapping.
        for _ in range(80):
            r1 = rng.randint(0, h - mh); c1 = rng.randint(0, w - mw)
            r2 = rng.randint(0, h - mh); c2 = rng.randint(0, w - mw)
            if _can_place(g, motif_n, r1, c1):
                _place_motif(g, motif_n, r1, c1, 6)
                if _can_place(g, mirror, r2, c2):
                    _place_motif(g, mirror, r2, c2, 6)
                    break
                # Roll back motif if mirror won't fit.
                for r, c in motif_n: g[r1 + r][c1 + c] = 0
        else:
            continue
        # 2. Add color-6 distractor motifs that are NOT mirror-paired
        # (their normalized form differs from any earlier motif's mirror).
        n_color6_extras = rng.randint(0, max(0, n_extras - 1))
        color6_sigs = [motif_n, mirror]   # every accepted color-6 normalized signature
        for _ in range(n_color6_extras):
            for _ in range(20):
                extra = _build_motif(rng, rng.randint(3, 5))
                ext_n = _normalize(extra)
                if _is_h_symmetric(ext_n):
                    continue
                # Must NOT equal OR mirror ANY already-accepted color-6 motif — else two
                # distractors form a SECOND mirror pair (3/120 instances did). (repo-audit fix:
                # old code only checked against the main pair, not against each other.)
                if any(ext_n == sig or ext_n == _normalize(_hmirror(sig)) for sig in color6_sigs):
                    continue
                eh = max(r for r, _ in ext_n) + 1
                ew = max(c for _, c in ext_n) + 1
                placed = False
                for _ in range(40):
                    r0 = rng.randint(0, h - eh); c0 = rng.randint(0, w - ew)
                    if _can_place(g, ext_n, r0, c0):
                        _place_motif(g, ext_n, r0, c0, 6)
                        placed = True; break
                if placed:
                    color6_sigs.append(ext_n)   # track it so later extras can't mirror it
                    break
        # 3. Add distractor motifs in other colors.
        n_other = rng.randint(1, n_extras)
        other_colors = rng.sample([1, 2, 3, 4, 5, 7, 8, 9], n_other)
        for color in other_colors:
            extra = _normalize(_build_motif(rng, rng.randint(2, 4)))
            eh = max(r for r, _ in extra) + 1
            ew = max(c for _, c in extra) + 1
            for _ in range(60):
                r0 = rng.randint(0, h - eh); c0 = rng.randint(0, w - ew)
                if _can_place(g, extra, r0, c0):
                    _place_motif(g, extra, r0, c0, color)
                    break
        return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
