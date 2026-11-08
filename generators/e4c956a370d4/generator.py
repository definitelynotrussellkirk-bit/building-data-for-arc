"""Generator for arc_puzzle_bank_21_set16_bundle:hard_p04 — guide-shape selects stamp.

Rule: a color-2 guide shape; color-9 anchors; non-{2, 9} candidate shapes.
Find the candidate whose shape matches a dihedral variant of the guide;
stamp that candidate's crop at every anchor (using the candidate's color).

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_guide (no color-2 shape → rule has no template);
no_match (guide + candidates but none matches → selector returns
nothing); no_anchors (guide + match but no color-9 anchors → no
stamp destinations).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e4c956a370d4"
VERSION = "2.1.0"  # clean but shallow: 5-shape bank, anchors 1-2. Add 2 more distinct-class shapes (I-tetromino, P-pentomino -> never dihedral-equiv to others), widen anchors 1-4 and grids; stamp room sized to the matching candidate.
TASK_ID = "e4c956a370d4"

SUMMARY = (
    "0-bg grid (h~9-11, w~"
    "13-15) with: (a) ONE "
    "COLOR-2 (red) GUIDE "
    "SHAPE — a 3-5 cell "
    "shape chosen from a "
    "shape bank, placed "
    "at random non-"
    "touching position; "
    "(b) 1-3 COLOR-9 "
    "(maroon) ANCHOR "
    "CELLS placed at "
    "random positions "
    "with room for "
    "stamping; (c) TWO "
    "CANDIDATE SHAPES in "
    "DISTINCT non-{2, 9} "
    "colors — one shape "
    "is a DIHEDRAL "
    "VARIANT (rotation/"
    "reflection) of the "
    "GUIDE; the other is "
    "a DIFFERENT shape. "
    "Rule (FIND THE "
    "DIHEDRALLY-MATCHING "
    "CANDIDATE, STAMP IT "
    "AT EVERY 9-ANCHOR)"
    ": identify the "
    "GUIDE (color-2) and "
    "the 2 CANDIDATES "
    "(non-{0, 2, 9})). "
    "For EACH CANDIDATE, "
    "check if its "
    "normalized shape "
    "matches any "
    "rotation/reflection "
    "of the guide's "
    "normalized shape. "
    "Pick the MATCHING "
    "CANDIDATE. CROP it. "
    "Produce a FRESH "
    "BLANK output grid; "
    "STAMP the matching "
    "candidate's crop "
    "(in its color) at "
    "each 9-ANCHOR "
    "position. Guide, "
    "non-matching "
    "candidate, and 9-"
    "anchors are "
    "DISCARDED."
)

# Rivals: 'output is input' refuted. 'stamp every candidate' refuted
# by demos with only matching candidate stamped. 'preserve guide
# in output' refuted. 'preserve anchors' refuted. 'use color 8 for
# stamps' refuted by demos preserving candidate color. 'stamp at
# guide position, not anchors' refuted. 'match without dihedral
# rotation' refuted by demos where matching candidate is rotated.
# 4 demos with rotation/reflection matches pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one color-2 guide shape (3-5 cells)",
    "1-2 color-9 anchor cells",
    "exactly 2 non-{2, 9} candidate components in distinct colors",
    "exactly one candidate is dihedrally-equivalent to the guide",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_guide", "no_match", "no_anchors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..16"},
    "grid_w":            {"type": "int", "default": "rng 13..15", "valid": "11..18"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "position_bias":     {"type": "str", "default": "guide_anchors_two_candidates",
                          "valid": "guide_anchors_two_candidates"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],                         # L-tromino (3)
    [(0, 0), (1, 0), (1, 1), (2, 1)],                 # S-tetromino (4)
    [(0, 0), (0, 1), (0, 2), (1, 1)],                 # T-tetromino (4)
    [(0, 0), (0, 1), (1, 0), (1, 1)],                 # square (4)
    [(0, 0), (0, 1), (0, 2), (1, 0)],                 # J-tetromino (4)
    [(0, 0), (0, 1), (0, 2), (0, 3)],                 # I-tetromino (4, straight)
    [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],         # P-pentomino (5)
]


def _normalize(shape):
    if not shape:
        return tuple()
    r0 = min(r for r, _ in shape)
    c0 = min(c for _, c in shape)
    return tuple(sorted((r - r0, c - c0) for r, c in shape))


def _rotate_cw(shape):
    rs = [r for r, _ in shape]
    h = max(rs) + 1
    return sorted([(c, h - 1 - r) for r, c in shape])


def _dihedral_keys(shape):
    cur = _normalize(shape)
    variants = []
    for refl in (False, True):
        ss = list(cur)
        if refl:
            maxc = max(c for _, c in ss)
            ss = [(r, maxc - c) for r, c in ss]
        for _ in range(4):
            variants.append(_normalize(ss))
            ss = _rotate_cw(ss)
    return set(variants)


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
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 13, 14)
        n_anchors = ctx.draw_int("n_anchors", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 15, 18)
        n_anchors = ctx.draw_int("n_anchors", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 14, 16)
        n_anchors = ctx.draw_int("n_anchors", 2, 3)
    rng = ctx.draw_rng("layout")

    guide = rng.choice(_SHAPES)
    rotated = guide
    for _ in range(rng.randint(1, 3)):
        rotated = _rotate_cw(rotated)
    # Normalize after rotation before drawing.  Otherwise a rotated non-square
    # shape can carry leading blank columns in its bbox; the canonical rule
    # crops objects before comparing, so the generated candidate no longer
    # matches the guide's dihedral class (rule_smoke seed 15 crash).
    rotated = list(_normalize(rotated))
    guide_keys = _dihedral_keys(guide)
    other_choices = [s for s in _SHAPES if _normalize(s) not in guide_keys]
    other = rng.choice(other_choices)
    cand_colors = rng.sample([1, 3, 4, 5, 6, 7, 8], 2)
    # stamp footprint = matching candidate (rotated) bbox; anchors need this room
    rrs = [r for r, _ in rotated]; rcs = [c for _, c in rotated]
    stamp_h = max(rrs) - min(rrs) + 1
    stamp_w = max(rcs) - min(rcs) + 1

    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        sh = max(r for r, _ in guide) + 1
        sw = max(c for _, c in guide) + 1
        placed = False
        for _ in range(80):
            r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
            if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
            for dr, dc in guide:
                g[r0 + dr][c0 + dc] = 2
            placed = True; break
        if not placed: continue
        for shape, color in zip([rotated, other], cand_colors):
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed_a = False
            for _ in range(80):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                placed_a = True; break
            if not placed_a:
                ok = False; break
        if not ok:
            continue
        placed_anchors = 0
        for _ in range(n_anchors):
            placed_this = False
            for _t in range(120):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if not _free(g, r, c, r, c): continue
                if r + stamp_h > h or c + stamp_w > w: continue   # room for the stamp
                g[r][c] = 9
                placed_anchors += 1
                placed_this = True
                break
            if not placed_this:
                break
        if placed_anchors == n_anchors:
            return g
    raise ValueError("could not realize hard_p04 layout")


def _components(grid, bg=0):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] == bg:
                continue
            color = grid[sr][sc]
            q = [(sr, sc)]; seen.add((sr, sc)); cells = []
            while q:
                r, c = q.pop(); cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for guide-shape selection and anchor stamping.

    The crash caught by rule_smoke came from layouts with zero/partial anchor
    placement; the canonical rule takes `(first anchors)`. This check also
    ensures exactly one non-{2,9} candidate is dihedrally equivalent to the
    guide, preventing ambiguous selectors.
    """
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    if any(v != 0 for row in grid for v in row if v < 0 or v > 9):
        errs.append("grid contains non-ARC colors")
    comps = _components(grid, 0)
    guides = [cells for color, cells in comps if color == 2]
    anchors = [cell for color, cells in comps if color == 9 for cell in cells]
    candidates = [(color, cells) for color, cells in comps if color not in (2, 9)]
    if len(guides) != 1:
        errs.append(f"expected exactly one color-2 guide component, found {len(guides)}")
        guide_keys = set()
    else:
        guide_keys = _dihedral_keys(guides[0])
        if not (3 <= len(guides[0]) <= 5):
            errs.append(f"guide should have 3..5 cells, found {len(guides[0])}")
    if len(anchors) < 1:
        errs.append("expected at least one color-9 anchor")
    if len(candidates) != 2:
        errs.append(f"expected exactly two candidate components, found {len(candidates)}")
    matches = [(color, cells) for color, cells in candidates if _normalize(cells) in guide_keys]
    if len(matches) != 1:
        errs.append(f"expected exactly one dihedral-matching candidate, found {len(matches)}")
    if matches:
        cells = matches[0][1]
        stamp_h = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        stamp_w = max(c for _, c in cells) - min(c for _, c in cells) + 1
        h, w = len(grid), len(grid[0])
        for r, c in anchors:
            if r + stamp_h > h or c + stamp_w > w:
                errs.append("anchor lacks room for matching-candidate stamp")
                break
            for rr in range(max(0, r - 1), min(h, r + 2)):
                for cc in range(max(0, c - 1), min(w, c + 2)):
                    if (rr, cc) != (r, c) and grid[rr][cc] != 0:
                        errs.append("anchor touches another non-background object")
                        return errs
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 14
    g = full_grid(h, w, 0)
    if name == "no_guide":
        # No color-2 guide — rule has no template.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[2 + dr][8 + dc] = 5
        g[6][3] = 9
        return g
    if name == "no_match":
        # Guide is L-tromino, candidates are 2x2 squares (different class).
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[2 + dr][8 + dc] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[6 + dr][8 + dc] = 5
        g[6][3] = 9
        return g
    if name == "no_anchors":
        # Guide + matching candidate but no color-9 anchors.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 2
        for dr, dc in [(0, 1), (1, 0), (1, 1)]:
            g[2 + dr][8 + dc] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[6 + dr][8 + dc] = 5
        return g
    return g
