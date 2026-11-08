"""Generator for arc_additional_puzzle_bank_volume16:M109.

Rule: the red candidate that is a true mirror, not a rotation, of the
blue source recolors cyan.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_candidates,
palette_size, position_bias, n_distinct_colors, chirality, texture.
Degenerates: no_mirror, all_mirrors, achiral_source.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85f0fcea28c0"
# 2.1.0: one entry in the source bank (S-thicker-5) is actually ACHIRAL — its
# reflection equals a rotation, so the "reflection" candidate fails the
# not-a-rotation test and NOTHING recolors -> output == input (identity). Choose
# the source only from genuinely chiral shapes. Adds self_check.
VERSION = "2.1.0"
TASK_ID = "85f0fcea28c0"
SUMMARY = (
    "0-bg grid (h~11-20, w~11-20) with: "
    "(a) ONE CHIRAL SOURCE in COLOR 1 — a "
    "5-6 cell shape drawn from _CHIRAL_"
    "SOURCES bank (L-5/Z-5/zigzag-5/F-"
    "shape) where the shape's REFLECTION "
    "is NOT one of its rotations (chiral "
    "property guaranteed); (b) 2-3 "
    "CANDIDATE SHAPES in COLOR 2 placed "
    "at non-touching positions, each "
    "either a REFLECTION-then-ROTATION of "
    "source (in dihedral closure but NOT "
    "in rotation closure) or a ROTATION-"
    "ONLY of source or a DECOY (shape "
    "not in source's dihedral closure). "
    "At least 1 candidate is a true "
    "MIRROR (in dihedral closure, not in "
    "rotation closure); at least 1 is "
    "not. Rule (RECOLOR TO CYAN ONLY "
    "THE COLOR-2 CANDIDATES THAT ARE "
    "TRUE MIRRORS OF SOURCE — DIHEDRALLY "
    "MATCHING BUT NOT ROTATIONALLY "
    "MATCHING): for EACH 4-connected "
    "color-2 COMPONENT: NORMALIZE its "
    "cells. CHECK (a) does the "
    "normalized set match source under "
    "SOME dihedral transform (rotation + "
    "reflection)? AND CHECK (b) does it "
    "NOT match source under rotation "
    "ALONE? If BOTH (a) AND (b): RECOLOR "
    "to COLOR 8 (cyan). Otherwise stay "
    "color 2. The color-1 source stays. "
    "Net: only the true-mirror "
    "candidates (reflections that aren't "
    "also rotations) get highlighted cyan."
)

# Rivals: 'output is input' refuted by demos with ≥1 mirror candidate
# present. 'recolor all candidates to 8' refuted by demos with a
# rotation-only candidate (stays 2). 'recolor only rotations'
# refuted by demos (it's the opposite — reflections, not rotations).
# 'recolor any candidate that matches source size' refuted by demos
# with a wrong-shape decoy (stays 2). 4 demos with combinations of
# (1 reflection + 1 rotation + 1 decoy) pin the (in dihedral closure
# AND NOT in rotation closure) rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one source shape in color 1, and it is chiral",
    "≥1 color-2 candidate that IS a reflection of source (not a rotation) — the rule recolors it to 8",
    "≥1 color-2 candidate that is NOT in the dihedral closure (a decoy or rotation-only) — stays color 2",
    "color-2 candidates are separated from each other and from the source by ≥1 bg gap",
    "no other non-bg colors in the grid (so the rule's effect on color 2 is unambiguous)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_mirror", "all_mirrors", "achiral_source")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "9..24"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "9..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_candidates":   {"type": "int", "default": "2", "valid": "2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "spread_corners",
                       "valid": "spread_corners"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "chirality":      {"type": "str", "default": "chiral_source",
                       "valid": "chiral_source"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_mirror|all_mirrors|achiral_source"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
        n_cand_min = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 20)
        w = ctx.draw_int("grid_w", 16, 20)
        n_cand_min = 3
    else:
        h = ctx.draw_int("grid_h", 13, 17)
        w = ctx.draw_int("grid_w", 13, 17)
        n_cand_min = 2
    rng = ctx.draw_rng("layout")
    # only genuinely chiral sources (reflection NOT in the rotation closure);
    # an achiral source makes every "reflection" candidate a rotation -> nothing
    # qualifies -> identity.
    chiral = [s for s in _CHIRAL_SOURCES
              if _normalize(_reflect_h(s)) not in _all_rotations(s)]

    for _attempt in range(20):
        g = full_grid(h, w, 0)
        source = rng.choice(chiral)
        # Decoy = a shape not in source's dihedral closure
        decoy = _pick_decoy(rng, source)
        # Build placement list: source + >=1 reflection + >=1 (rotation OR decoy)
        n_cand = rng.randint(n_cand_min, n_cand_min + 1)
        candidates = []
        # Always include at least one true-mirror reflection
        reflection_k = rng.randint(0, 3)
        candidates.append(("reflection", _reflect_then_rotate(source, reflection_k)))
        # Add 1..(n_cand-1) of rotation_only or decoy
        for _ in range(n_cand - 1):
            kind = rng.choice(["rotation", "decoy"])
            if kind == "rotation":
                rot_k = rng.randint(1, 3)
                candidates.append(("rotation", _rotate_cells(source, rot_k)))
            else:
                candidates.append(("decoy", decoy))
        rng.shuffle(candidates)

        placements = _place_shapes(rng, h, w, [source] + [c[1] for c in candidates])
        if placements is None:
            continue  # retry with new shapes/positions rather than a degenerate
        src_top, src_left = placements[0]
        for r, c in source:
            g[src_top + r][src_left + c] = 1
        for (kind, cells), (top, left) in zip(candidates, placements[1:]):
            for r, c in cells:
                g[top + r][left + c] = 2
        return g

    # deterministic fallback: source + one true mirror + one decoy in separate
    # quadrants (never the achiral degenerate).
    g = full_grid(h, w, 0)
    source = chiral[0]
    mirror = _reflect_then_rotate(source, 0)
    decoy = _pick_decoy(rng, source)
    for r, c in source:
        g[1 + r][1 + c] = 1
    for r, c in mirror:
        g[1 + r][(w // 2) + 1 + c] = 2
    for r, c in decoy:
        g[(h // 2) + 1 + r][1 + c] = 2
    return g


_CHIRAL_SOURCES = [
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)],            # L-5 horizontal
    [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],            # L-5 vertical
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],            # Z-5
    [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],            # zigzag-5
    [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3)],    # F-shape
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 0)],            # S-thicker-5
]


def _normalize(cells):
    if not cells:
        return frozenset()
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return frozenset((r - minr, c - minc) for r, c in cells)


def _rotate_cells(cells, k):
    cur = list(cells)
    for _ in range(k % 4):
        maxr = max(r for r, _ in cur)
        cur = [(c, maxr - r) for r, c in cur]
    return list(_normalize(cur))


def _reflect_h(cells):
    maxc = max(c for _, c in cells)
    return list(_normalize([(r, maxc - c) for r, c in cells]))


def _reflect_then_rotate(cells, k):
    return _rotate_cells(_reflect_h(cells), k)


def _all_rotations(cells):
    return {_normalize(_rotate_cells(cells, k)) for k in range(4)}


def _all_dihedral(cells):
    out = set()
    base = list(cells)
    for k in range(4):
        rot = _rotate_cells(base, k)
        out.add(_normalize(rot))
        out.add(_normalize(_reflect_h(rot)))
    return out


def _pick_decoy(rng, source):
    """A shape NOT in source's dihedral closure."""
    dih = _all_dihedral(source)
    for _ in range(40):
        cand = rng.choice(_CHIRAL_SOURCES)
        if _normalize(cand) not in dih and _normalize(_reflect_h(cand)) not in dih:
            return cand
    # Last resort: take any shape distinct from source
    for c in _CHIRAL_SOURCES:
        if _normalize(c) != _normalize(source):
            return c
    return source


def _place_shapes(rng, h, w, shape_list):
    """Place each shape such that bboxes don't touch (≥1 bg gap)."""
    placements = []
    placed = []  # (top, left, bbox_h, bbox_w)
    for shape in shape_list:
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        found = None
        for _ in range(200):
            top = rng.randint(0, h - sh)
            left = rng.randint(0, w - sw)
            collides = False
            for pt, pl, psh, psw in placed:
                if (top - (pt + psh) < 2 and pt - (top + sh) < 2 and
                    left - (pl + psw) < 2 and pl - (left + sw) < 2):
                    collides = True
                    break
            if collides:
                continue
            found = (top, left, sh, sw)
            break
        if found is None:
            return None
        placements.append((found[0], found[1]))
        placed.append(found)
    return placements


def _color_components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or seen[sr][sc]:
                continue
            stack = [(sr, sc)]; seen[sr][sc] = True; cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == color:
                        seen[nr][nc] = True; stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one chiral color-1 source, and >=1 color-2 candidate that is a
    true mirror (dihedral match, not rotation match) so the rule recolors
    something to cyan -> output != input."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    src_comps = _color_components(grid, 1)
    errors = []
    if len(src_comps) != 1:
        errors.append(f"expected exactly one color-1 source, found {len(src_comps)}")
        return errors
    source = src_comps[0]
    if _normalize(_reflect_h(source)) in _all_rotations(source):
        errors.append("source is achiral — mirror == rotation, criterion vacuous")
    dih = _all_dihedral(source); rots = _all_rotations(source)
    cand_comps = _color_components(grid, 2)
    n_qual = sum(1 for cells in cand_comps
                 if _normalize(cells) in dih and _normalize(cells) not in rots)
    if n_qual < 1:
        errors.append("no color-2 candidate is a true mirror — the rule recolors "
                      "nothing (output == input, identity)")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 13, 13
    g = full_grid(h, w, 0)
    source = [(1, 1), (1, 2), (1, 3), (1, 4), (2, 1)]
    rotation_only = [(1, w - 5), (1, w - 4), (1, w - 3), (1, w - 2), (2, w - 2)]
    mirror = [(1, w - 4), (2, w - 4), (3, w - 4), (4, w - 5), (4, w - 4)]
    distractor = [(h - 4, 2), (h - 4, 3), (h - 3, 2), (h - 3, 3), (h - 2, 3)]
    for r, c in source:
        g[r][c] = 1
    if name == "no_mirror":
        # both red candidates are rotations / non-matches → no winner to recolor
        for r, c in rotation_only:
            g[r][c] = 2
        for r, c in distractor:
            g[r][c] = 2
        return g
    if name == "all_mirrors":
        # both red candidates are mirrors → tie, target ambiguous
        for r, c in mirror:
            g[r][c] = 2
        mirror2 = [(h - 4, w - 5), (h - 4, w - 4), (h - 3, w - 5), (h - 2, w - 5), (h - 2, w - 4)]
        for r, c in mirror2:
            g[r][c] = 2
        return g
    if name == "achiral_source":
        # source has mirror symmetry → mirror = rotation, recolor criterion vacuous
        achiral = [(1, 1), (1, 2), (1, 3), (2, 2), (3, 1), (3, 2), (3, 3)]
        g2 = full_grid(h, w, 0)
        for r, c in achiral:
            g2[r][c] = 1
        for r, c in mirror:
            g2[r][c] = 2
        for r, c in distractor:
            g2[r][c] = 2
        return g2
    return g
