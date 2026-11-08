"""Generator for 17b:m117 — select rotation match and recolor.

Rule: target color at (0, w-1). The largest color-1 shape is the
reference. Among other shapes, find one rotation-equivalent to the
reference. Output: that shape cropped, recolored to target.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_target (cell (0, w-1) is bg → rule has no recolor
target); no_reference (no color-1 shape → rule has no reference);
no_match (reference but no rotation-equivalent candidate → rule's
selector returns nothing).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e73c86cb45ad"
VERSION = "2.1.0"  # base shapes were 4 FIXED small polyominoes -> output bbox locked (out_shapes 3, dup-outputs 41%). Now random base + rotated match + non-rotation-equivalent distractor(s)
TASK_ID = "e73c86cb45ad"
SUMMARY = "Target color at (0, w-1) + color-1 ref + 2-3 other shapes (one rotation-match)."

INVARIANTS = [
    "background is 0",
    "cell (0, w-1) is the target color",
    "exactly one color-1 reference shape",
    "2-3 other shapes; exactly one is rotation-equivalent to the reference",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_target", "no_reference", "no_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "grid_w":            {"type": "int", "default": "rng 12..14", "valid": "11..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "position_bias":     {"type": "str", "default": "target_corner_plus_ref_and_candidates",
                          "valid": "target_corner_plus_ref_and_candidates"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


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
    for _ in range(200):
        r0 = rng.randint(1, h - sh); c0 = rng.randint(0, w - sw - 1)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def _rotate_cw(shape):
    rs = [r for r, _ in shape]
    h = max(rs) + 1
    return sorted([(c, h - 1 - r) for r, c in shape])


def _norm(shape):
    mr = min(r for r, _ in shape); mc = min(c for _, c in shape)
    return tuple(sorted((r - mr, c - mc) for r, c in shape))


def _rot_class(shape):
    s = set(); cur = list(shape)
    for _ in range(4):
        s.add(_norm(cur)); cur = _rotate_cw(cur)
    return s


def _poly(rng, k):
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
    rng = ctx.draw_rng("layout")
    # One distractor plus the guaranteed rotation-match gives the required
    # 2 non-reference shapes.  A second default distractor made crowded
    # boards fail closed on valid seeds.
    n_other = 2 if difficulty == "hard" else 1
    for _attempt in range(160):
        g = full_grid(h, w, 0)
        target_color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
        g[0][w - 1] = target_color
        base = _poly(rng, rng.randint(4, 6 if difficulty == "easy" else 7))
        base_class = _rot_class(base)
        rotated = base
        for _ in range(rng.randint(1, 3)):
            rotated = _rotate_cw(rotated)
        rotated = sorted(rotated)
        if not _place(g, rng, base, 1):
            continue
        used = {target_color, 1}
        oc = rng.choice([c for c in range(2, 10) if c not in used]); used.add(oc)
        if not _place(g, rng, rotated, oc):
            continue
        # non-matching distractor(s): rotation class != base's.  Keep the
        # default/easy distractor compact and retry the whole scene if crowded.
        ok = True
        for _ in range(n_other):
            other = None
            for _t in range(50):
                cand = _poly(rng, rng.randint(3, 5))
                if _norm(cand) not in base_class:
                    other = cand
                    break
            if other is None:
                ok = False
                break
            oc2 = rng.choice([c for c in range(2, 10) if c not in used]); used.add(oc2)
            if not _place(g, rng, other, oc2):
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place reference, rotation-match, and distractor shapes")


def _components_by_color(grid):
    h = len(grid); w = len(grid[0]) if h else 0
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            q = [(r, c)]; seen.add((r, c)); cells = []
            while q:
                rr, cc = q.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify target corner, one color-1 reference, exactly one rotation-equivalent candidate."""
    errs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    target = grid[0][w - 1]
    if target == 0:
        errs.append("target color at top-right must be nonzero")
    comps = [(color, cells) for color, cells in _components_by_color(grid)
             if not (len(cells) == 1 and cells[0] == (0, w - 1))]
    refs = [cells for color, cells in comps if color == 1]
    if len(refs) != 1:
        errs.append(f"expected exactly one color-1 reference component, got {len(refs)}")
        return errs
    ref_class = _rot_class(refs[0])
    matches = []
    distractors = []
    for color, cells in comps:
        if color == 1:
            continue
        if _norm(cells) in ref_class:
            matches.append(color)
        else:
            distractors.append(color)
    if len(matches) != 1:
        errs.append(f"expected exactly one rotation-equivalent candidate, got {len(matches)}")
    if len(distractors) < 1:
        errs.append("expected at least one non-matching distractor")
    if target in {1, *matches, *distractors}:
        errs.append("target corner color must be distinct from shape colors")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 12, 13
    g = full_grid(h, w, 0)
    if name == "no_target":
        # Cell (0, w-1) is bg — rule has no recolor target.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 1
        for dr, dc in [(0, 1), (1, 0), (1, 1)]:
            g[7 + dr][7 + dc] = 4
        return g
    if name == "no_reference":
        # Target + candidates but no color-1 reference.
        g[0][w - 1] = 6
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[7 + dr][7 + dc] = 5
        return g
    if name == "no_match":
        # Reference is L-tromino but candidates are 2x2 squares (different class).
        g[0][w - 1] = 6
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 1
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[7 + dr][3 + dc] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[7 + dr][8 + dc] = 5
        return g
    return g
