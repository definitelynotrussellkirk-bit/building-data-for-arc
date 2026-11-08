"""Generator for 9b:m63 — crop unique 180-symmetric component.

Rule: of the connected components (4-conn, single color), exactly one
has 180° rotational symmetry. Output is that component cropped.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_symmetric (no 180°-symmetric component → rule's
selector finds nothing), all_symmetric (every component is
180°-symmetric → "the unique" is ambiguous, tie-break decides),
single_component (only one component, trivially the choice → no
candidate contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3e18c05a8b57"
VERSION = "3.1.0"  # ensure symmetric+distractor placements all succeed; add self_check
TASK_ID = "3e18c05a8b57"
SUMMARY = (
    "0-bg grid (h ∈ 8-11, w ∈ 10-13) "
    "with: (a) ONE 180°-SYMMETRIC "
    "COMPONENT — drawn from _180_SYM "
    "bank (4 four-connected variants: "
    "2×2 square, plus, H/7-cell, "
    "S-tetromino), painted in "
    "palette[0] at a random "
    "non-overlapping position via "
    "_free_box (1-cell padding); "
    "(b) 1-2 ASYMMETRIC COMPONENTS — "
    "drawn from _ASYM bank (5 "
    "variants: L-tromino, S-tromino, "
    "P-tetromino, L-tetromino, S-tet), "
    "each in a DISTINCT non-symmetric "
    "color drawn from palette[1:]. "
    "All colors distinct, drawn from "
    "{1,2,3,4,6,7,8,9}. Rule (FIND "
    "THE UNIQUE 180°-SYMMETRIC "
    "COMPONENT, CROP TO ITS BBOX, "
    "OUTPUT): EXTRACT every "
    "4-connected non-bg COMPONENT "
    "(single-color). For EACH "
    "component: COMPUTE its "
    "NORMALIZED BINARY SHAPE; CHECK "
    "if shape == its 180° ROTATION. "
    "SELECT the unique component "
    "where shape is 180°-symmetric. "
    "CROP it to its bounding box. "
    "OUTPUT the cropped grid "
    "(preserving the component's "
    "color, 0 elsewhere in bbox). "
    "Net: the symmetric shape is "
    "extracted; asymmetric "
    "distractors discarded. Flagged "
    "intrinsic-low (uniq_out=28): "
    "small bank × few colors "
    "bounds outputs."
)

INVARIANTS = [
    "background is 0",
    "2-3 isolated 4-connected components in distinct colors",
    "exactly one's normalized binary shape equals its 180° rotation",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_symmetric", "all_symmetric", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":            {"type": "int", "default": "rng 10..13", "valid": "9..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "position_bias":     {"type": "str", "default": "one_symmetric_plus_asyms",
                          "valid": "one_symmetric_plus_asyms"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_symmetric|all_symmetric|single_component"},
}


# Every shape here must be BOTH 180°-symmetric AND 4-connected: the rule
# extracts 4-connected components, so a symmetric-but-4-disconnected shape
# (e.g. the 5-cell X = centre + 4 diagonal corners, or two separate
# L-trominoes) splits into several asymmetric pieces -> 0 symmetric
# components found -> rule returns #f (non-grid). Those two are removed.
_180_SYM = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],                                   # 2x2 square
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],                           # plus
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)],           # H / 7-cell
    [(0, 0), (1, 0), (1, 1), (2, 1)],                                   # S-tetromino
]
_ASYM = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
]


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    start = next(iter(cells)); seen = {start}; stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARD:
            n = (r + dr, c + dc)
            if n in cells and n not in seen:
                seen.add(n); stack.append(n)
    return len(seen) == len(cells)


def _is_sym180(cells):
    cs = set(cells)
    h = max(r for r, _ in cells) + 1; w = max(c for _, c in cells) + 1
    return all((h - 1 - r, w - 1 - c) in cs for (r, c) in cells)


def _rand_sym180(rng):
    """A random 4-connected polyomino that is 180-degree rotationally symmetric
    about its bbox centre (cell (r,c) in shape iff its mirror is too)."""
    for _ in range(100):
        h = rng.randint(2, 5); w = rng.randint(2, 5)
        cells = set(); decided = set()
        for r in range(h):
            for c in range(w):
                pk = frozenset({(r, c), (h - 1 - r, w - 1 - c)})
                if pk in decided:
                    continue
                decided.add(pk)
                if rng.random() < 0.55:
                    cells |= pk
        if not cells:
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        if not (min(rs) == 0 and max(rs) == h - 1 and min(cs) == 0 and max(cs) == w - 1):
            continue
        # Avoid large solid rectangles.  They are technically 180-symmetric, but
        # their crop is a single-color slab, which hides the intended
        # "select-by-shape-symmetry" rule and trips the generic all-solid-output
        # detector.  Small 2x2 squares remain canonical and harmless.
        if len(cells) == h * w and h * w >= 9:
            continue
        if _connected(cells):
            return sorted(cells)
    return [(0, 0), (0, 1), (1, 0), (1, 1)]


def _rand_asym(rng):
    """A random 4-connected polyomino that is NOT 180-degree symmetric."""
    for _ in range(100):
        cells = [(0, 0)]; seen = {(0, 0)}
        n = rng.randint(3, 5)
        while len(cells) < n:
            r, c = rng.choice(cells)
            dr, dc = rng.choice(_CARD)
            if (r + dr, c + dc) not in seen:
                cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
        rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
        norm = [(r - rmin, c - cmin) for r, c in cells]
        if not _is_sym180(norm):
            return norm
    return [(0, 0), (1, 0), (1, 1)]


def _free_box(g, r1, c1, r2, c2):
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
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if not _free_box(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        n_lo, n_hi = 1, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        n_lo, n_hi = 2, 2
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n_lo, n_hi = 1, 2
    rng = ctx.draw_rng("layout")
    n_asym = rng.randint(n_lo, n_hi)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 1 + n_asym)
    for _attempt in range(80):
        g = full_grid(h, w, 0)
        # the ONE 180-symmetric component (the output) + asymmetric distractors,
        # all RANDOM now (was a 4-shape bank -> distinct=32).
        if not _place(g, rng, _rand_sym180(rng), palette[0]):
            continue
        ok = True
        for color in palette[1:]:
            if not _place(g, rng, _rand_asym(rng), color):
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place unique symmetric component plus distractors")


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_symmetric":
        # No 180°-symmetric component — rule's selector finds nothing.
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[2 + dr][2 + dc] = 4
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][6 + dc] = 6
        return g
    if name == "all_symmetric":
        # Every component is 180°-symmetric — "the unique" is ambiguous.
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[1 + dr][1 + dc] = 4   # 2x2 (sym)
        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]:
            g[5 + dr][5 + dc] = 6   # plus (sym)
        return g
    if name == "single_component":
        # Only one component — no contrast.
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[3 + dr][4 + dc] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    from puzzle_generators.helpers.selfcheck import components
    errors = []
    comps = components(grid)
    min_components = {"easy": 2, "hard": 3}.get(difficulty, 2)
    if len(comps) < min_components:
        errors.append(f"expected at least {min_components} components, found {len(comps)}")
    syms = [comp for comp in comps if _is_sym180(comp["norm"])]
    if len(syms) != 1:
        errors.append(f"expected exactly one 180-symmetric component, found {len(syms)}")
    elif len(syms[0]["norm"]) >= 9:
        rs = [r for r, _ in syms[0]["norm"]]
        cs = [c for _, c in syms[0]["norm"]]
        area = (max(rs) + 1) * (max(cs) + 1)
        if len(syms[0]["norm"]) == area:
            errors.append("symmetric component is a large solid rectangle; rule signal is hidden")
    if len({comp["color"] for comp in comps}) != len(comps):
        errors.append("component colors are not distinct")
    return errors
