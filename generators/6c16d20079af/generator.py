"""Generator for 5b:hard_35 — fill holed component with key color.

Rule: a single key cell (value 8 or 9) names the fill color. Output is
the first (in scan order) component with at least one bbox-interior bg
cell, cropped, with its holes filled by the key color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_solid,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_holed, no_solid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6c16d20079af"
VERSION = "2.1.0"  # distinct=24/dup17%: output is the holed component with its hole filled; holed/solid shapes came from fixed 2-entry/3-entry banks. Use random hollow rectangles (varied dims) as the holed shape + random polyomino distractors -> filled output varies widely.
TASK_ID = "6c16d20079af"
SUMMARY = (
    "0-bg grid (h~9-13, w~11-15) with: (a) ONE HOLED "
    "COMPONENT — picked from a small bank of HOLED shapes "
    "(a 3×3 ring with one center hole, or a 3×4 ring with "
    "two center holes), placed in the TOP HALF (rows "
    "0..h/2-sh), painted in a non-key non-bg color C0 "
    "from {1,2,3,4,6,7}; (b) 1-2 SOLID NON-HOLED "
    "COMPONENTS — picked from a small bank of L/2×2 "
    "shapes (3-4 cells each), placed in the BOTTOM HALF "
    "(rows h/2..h-ssh), each in a DISTINCT non-{0, "
    "key} color; (c) ONE ISOLATED KEY CELL with value "
    "8 or 9, placed at a random bg position with NO non-bg "
    "neighbors in any of its 8 surrounding cells. Components "
    "are placed with 1-cell 8-conn padding (no touches). "
    "Rule (FILL THE HOLED COMPONENT WITH THE KEY COLOR, "
    "CROP IT, OUTPUT): scan components in reading order "
    "(top-to-bottom, left-to-right by bbox). FIND the "
    "FIRST component that contains at least one bbox-"
    "interior bg cell (a 'hole'). LOOK UP the KEY COLOR — "
    "the unique isolated cell with value in {8,9}. FILL "
    "every bbox-interior bg cell of that holed component "
    "with the KEY COLOR. CROP the result to the holed "
    "component's bbox. OUTPUT that crop (other components "
    "and the key cell are discarded). Net: a small "
    "rectangular output showing the holed shape with its "
    "holes plugged by the key color. Flagged intrinsic-low "
    "uniq_out (~21): output crops to a small fixed-shape "
    "set × 2 key-color values × a few non-key colors, "
    "limiting structural diversity."
)

INVARIANTS = [
    "background is 0",
    "exactly one isolated key cell with value in {8, 9}",
    "the first scan-order component has at least one hole (bbox-interior bg)",
    "1-2 other components are solid (no holes)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_holed", "no_solid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "10..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_solid":        {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "holed_top_solid_bottom",
                       "valid": "holed_top_solid_bottom"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_HOLED = [
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3),
     (2, 0), (2, 1), (2, 2), (2, 3)],
]
_SOLID = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
]


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


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
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 13, 17)
    else:
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 15)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_solid = rng.randint(1, 2)
    palette = rng.sample([1, 2, 3, 4, 6, 7], 1 + n_solid)
    # holed shape = a random hollow rectangle (its interior is the hole the rule fills)
    fh = rng.randint(3, max(3, h // 2 - 1))
    fw = rng.randint(3, max(3, min(6, w - 1)))
    holed = [(r, c) for r in range(fh) for c in range(fw)
             if r == 0 or r == fh - 1 or c == 0 or c == fw - 1]
    sh = fh
    sw = fw
    for _ in range(40):
        r0 = rng.randint(0, h // 2 - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in holed: g[r0 + dr][c0 + dc] = palette[0]
        break
    for color in palette[1:]:
        s = _rand_poly(rng, rng.randint(2, 5))
        ssh = max(r for r, _ in s) + 1
        ssw = max(c for _, c in s) + 1
        for _ in range(40):
            r0 = rng.randint(h // 2, h - ssh); c0 = rng.randint(0, w - ssw)
            if not _free(g, r0, c0, r0 + ssh - 1, c0 + ssw - 1): continue
            for dr, dc in s: g[r0 + dr][c0 + dc] = color
            break
    key = rng.choice([8, 9])
    for _ in range(60):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0: continue
        bad = False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    bad = True; break
            if bad: break
        if bad: continue
        g[r][c] = key; break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_key":
        # Components but no key — rule has no fill color for holes.
        for dr, dc in _HOLED[0]: g[1 + dr][1 + dc] = 4
        for dr, dc in _SOLID[0]: g[6 + dr][6 + dc] = 5
        return g
    if name == "no_holed":
        # All components are solid — rule has no holed component to fill.
        g[0][8] = 8
        for dr, dc in _SOLID[0]: g[1 + dr][1 + dc] = 4
        for dr, dc in _SOLID[1]: g[6 + dr][6 + dc] = 5
        return g
    if name == "no_solid":
        # Only a holed component, no solids — rule selects holed (no contrast).
        g[0][8] = 8
        for dr, dc in _HOLED[0]: g[1 + dr][1 + dc] = 4
        return g
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or grid[r][c] in (8, 9) or (r, c) in seen:
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
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            out.append((color, cells, (min(rs), min(cs), max(rs), max(cs))))
    return sorted(out, key=lambda x: (x[2][0], x[2][1]))


def _has_bbox_hole(grid, cells, bbox):
    r1, c1, r2, c2 = bbox
    s = set(cells)
    return any((r, c) not in s and grid[r][c] == 0
               for r in range(r1 + 1, r2) for c in range(c1 + 1, c2))


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    keys = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (8, 9)]
    if len(keys) != 1:
        errs.append(f"expected exactly one key cell in {{8,9}}, got {len(keys)}")
    else:
        kr, kc = keys[0]
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = kr + dr, kc + dc
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 0:
                    errs.append("key cell is not isolated")
                    break
            if errs and errs[-1] == "key cell is not isolated":
                break
    comps = _components(grid)
    if len(comps) < 2:
        errs.append(f"expected holed component plus solid distractor, got {len(comps)} components")
    holes = [idx for idx, (_color, cells, bbox) in enumerate(comps)
             if _has_bbox_hole(grid, cells, bbox)]
    if not holes:
        errs.append("no holed component")
    elif holes[0] != 0:
        errs.append(f"first scan-order component is not holed; hole indices={holes}")
    return errs
