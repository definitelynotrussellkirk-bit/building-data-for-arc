"""Generator for arc_puzzle_bank_21_set13_s:S13_E5 — single holed component selector.

Rule: among the connected components, exactly one has exactly ONE enclosed 0-hole
(a 0-region strictly inside its bbox). Crop that component to its bbox and recolor
it to 8; output the crop.

Prior versions used a plain rectangular RING as the holed object, so the output
(the recolored crop) was always a full rectangular border -> only ~9 distinct
outputs (dup-outputs flag) and it did NOT match canonical, whose holed objects are
IRREGULAR polyominoes with one hole (e.g. 8880/8088/8880). This version grows an
irregular one-hole polyomino (rectangular ring + random outward bumps, verified to
have exactly one hole), giving varied crops that match the canonical distribution.

Rule-safe diversity: grid size, holed-shape dims + bumps, distractor count/shape,
colors, positions.
Degenerates: no_components, no_holed_object, multiple_holed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f3ecc20ad2d1"
VERSION = "3.0.0"  # irregular one-hole polyominoes (was plain rings -> 9 distinct outputs, off-canonical)
TASK_ID = "f3ecc20ad2d1"
SUMMARY = (
    "0-bg grid (h~11-16, w~13-18) with: (a) EXACTLY ONE HOLED component — an "
    "IRREGULAR polyomino with exactly one enclosed 0-hole (a rectangular ring "
    "grown with random outward bumps); (b) 1-4 SOLID distractor components with no "
    "holes. Each in a distinct non-0 color, non-touching (1-cell padding). Rule: "
    "find the unique component with exactly one enclosed hole, crop it to its bbox "
    "and recolor to 8. Output = that crop. (Was: plain rectangular ring -> only 9 "
    "distinct outputs and off-canonical.)"
)

INVARIANTS = [
    "background is 0",
    "exactly one component has exactly one enclosed 0-hole",
    "all distractor components have zero holes",
    "components are non-touching (1-cell padding) and distractors stay outside the holed bbox",
    "the one-hole component is cropped and recolored to 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "no_holed_object", "multiple_holed")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":           {"type": "int", "default": "11 easy / 11-14 med / 14-16 hard", "valid": "9..18"},
    "width":            {"type": "int", "default": "13 easy / 13-16 med / 16-19 hard", "valid": "10..20"},
    "distractor_count": {"type": "int", "default": "1-2 easy / 2-3 med / 3-4 hard", "valid": "1..4"},
    "ring_h":           {"type": "int", "default": "ring height 3-6", "valid": "3..7"},
    "ring_w":           {"type": "int", "default": "ring width 3-6", "valid": "3..7"},
    "bumps":            {"type": "int", "default": "outward bumps 0-6 (irregularity)", "valid": "0..10"},
    "density":          {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":          {"type": "str", "default": "alias for palette_kind",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SOLID = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
]


def _count_holes(cells):
    cells = set(cells)
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    H = max(rs) - r0 + 1; W = max(cs) - c0 + 1
    norm = {(r - r0, c - c0) for r, c in cells}
    seen = set(); holes = 0
    for r in range(H):
        for c in range(W):
            if (r, c) in norm or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); touches = False
            while stack:
                rr, cc = stack.pop()
                if rr in (0, H - 1) or cc in (0, W - 1):
                    touches = True
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in norm and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            if not touches:
                holes += 1
    return holes


def _make_holed(rng, rh, rw, bumps):
    """Rectangular ring (one hole) grown with random OUTWARD bumps; verified
    to keep exactly one enclosed hole. Returns normalized cell list."""
    interior = {(r, c) for r in range(1, rh - 1) for c in range(1, rw - 1)}
    for _attempt in range(8):
        cells = {(r, c) for r in range(rh) for c in range(rw)
                 if r in (0, rh - 1) or c in (0, rw - 1)}
        for _ in range(bumps):
            cand = []
            for (r, c) in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (r + dr, c + dc)
                    if n not in cells and n not in interior:
                        cand.append(n)
            if not cand:
                break
            cells.add(rng.choice(cand))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        mr, mc = min(rs), min(cs)
        norm = [(r - mr, c - mc) for r, c in cells]
        if _count_holes(norm) == 1:
            return norm
    # fallback: plain ring (always exactly one hole)
    return [(r, c) for r in range(rh) for c in range(rw) if r in (0, rh - 1) or c in (0, rw - 1)]


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _free(g, r0, c0, shape, forbid=None, pad=1):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    if forbid is not None:
        fr1, fc1, fr2, fc2 = forbid
        if not (r0 + sh - 1 < fr1 - 1 or r0 > fr2 + 1 or
                c0 + sw - 1 < fc1 - 1 or c0 > fc2 + 1):
            return False
    for r in range(max(0, r0 - pad), min(h, r0 + sh + pad)):
        for c in range(max(0, c0 - pad), min(w, c0 + sw + pad)):
            if g[r][c] != 0:
                return False
    return True


def _place(g, rng, shape, color, forbid=None):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    for _ in range(200):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, shape, forbid=forbid):
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            return (r0, c0, r0 + sh - 1, c0 + sw - 1)
    raise ValueError("could not place object")



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the generator contract: one one-hole component, no holed distractors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if any(v < 0 or v > 9 for row in grid for v in row):
        return ["color outside 0..9"]

    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
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
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)

    if not components:
        return ["no components"]
    hole_counts = [_count_holes(cells) for cells in components]
    one_hole = sum(1 for n in hole_counts if n == 1)
    if one_hole != 1:
        return [f"expected exactly one one-hole component, saw {one_hole}"]
    bad_distractors = [n for n in hole_counts if n not in (0, 1)]
    if bad_distractors:
        return [f"component with unsupported hole count(s): {bad_distractors}"]
    return []

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 11, 12); w = ctx.draw_int("width", 13, 14)
        distractor_count = ctx.draw_int("distractor_count", 1, 2)
        rh = ctx.draw_int("ring_h", 3, 4); rw = ctx.draw_int("ring_w", 3, 4)
        bumps = ctx.draw_int("bumps", 0, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 14, 16); w = ctx.draw_int("width", 16, 19)
        distractor_count = ctx.draw_int("distractor_count", 3, 4)
        rh = ctx.draw_int("ring_h", 3, 7); rw = ctx.draw_int("ring_w", 3, 7)
        bumps = ctx.draw_int("bumps", 2, 7)
    else:
        h = ctx.draw_int("height", 11, 14); w = ctx.draw_int("width", 13, 16)
        distractor_count = ctx.draw_int("distractor_count", 2, 3)
        rh = ctx.draw_int("ring_h", 3, 6); rw = ctx.draw_int("ring_w", 3, 6)
        bumps = ctx.draw_int("bumps", 1, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = [2, 3, 4, 6, 7, 9]
    rng.shuffle(colors)
    holed = _make_holed(rng, rh, rw, bumps)
    forbid = _place(g, rng, holed, colors[0])          # the single varied holed shape
    for color in colors[1:1 + distractor_count]:
        _place(g, rng, rng.choice(_SOLID), color, forbid=forbid)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_components":
        return g
    if name == "no_holed_object":
        for r, c in [(2, 2), (2, 3), (3, 2), (3, 3)]: g[r][c] = 4
        for r, c in [(7, 8), (7, 9), (8, 8)]: g[r][c] = 6
        return g
    if name == "multiple_holed":
        ring = [(r, c) for r in range(3) for c in range(3) if r in (0, 2) or c in (0, 2)]
        for dr, dc in ring: g[1 + dr][1 + dc] = 4
        for dr, dc in ring: g[7 + dr][9 + dc] = 6
        return g
    return g
