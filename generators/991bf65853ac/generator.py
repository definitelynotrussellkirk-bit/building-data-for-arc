"""Generator for 15b:m105 — fill the hole of the holed object.

Rule: of the connected components, exactly one has at least one bg
cell inside its bbox. Output is that component cropped, with its
hole(s) filled in its color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components (no objects → rule has nothing to crop);
all_solid (no component has a hole → rule's "exactly one holed"
precondition fails); all_holed (every component has at least one
hole → selector's "exactly one" precondition fails).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "991bf65853ac"
VERSION = "2.0.1"  # distinct 24 / out_sh=3: holed shape came from a 3-shape bank, so output (= holed component cropped + holes filled) had only 3 bboxes. Use a RANDOM holed polyomino (arbitrary outer shape enclosing >=1 bg hole) so output shape/content vary.
TASK_ID = "991bf65853ac"
SUMMARY = "2-3 components; exactly one is a random holed polyomino (arbitrary outer shape enclosing >=1 bg cell). Rule crops that component and fills its holes -> output shape and content vary."

INVARIANTS = [
    "background is 0",
    "2-3 isolated 4-connected components, distinct colors",
    "exactly one component has at least one bg cell inside its bbox (a hole)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "all_solid", "all_holed")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 11..14", "valid": "10..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":     {"type": "str", "default": "holed_plus_solid_components",
                          "valid": "holed_plus_solid_components"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_HOLED = [
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],     # 3x3 ring
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 3),       # 3x4 ring
     (3, 0), (3, 1), (3, 2), (3, 3)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3),                       # holed L
     (2, 0), (2, 1), (2, 2), (2, 3)],
]
_SOLID = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 0)],
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
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _hole_count(cells):
    """Number of enclosed bg regions (bg cells in the crop not reachable
    from the crop border) — matches the rule's hole detector."""
    cs = set(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    bg = {(r, c) for r in range(h) for c in range(w) if (r, c) not in cs}
    outside = set()
    stack = [(r, c) for (r, c) in bg if r in (0, h - 1) or c in (0, w - 1)]
    outside.update(stack)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            n = (r + dr, c + dc)
            if n in bg and n not in outside:
                outside.add(n); stack.append(n)
    enclosed = bg - outside
    regions = 0; vis = set()
    for cell in enclosed:
        if cell in vis: continue
        regions += 1; vis.add(cell); stack = [cell]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                n = (r + dr, c + dc)
                if n in enclosed and n not in vis:
                    vis.add(n); stack.append(n)
    return regions


def _rand_holed(rng):
    """Random connected polyomino enclosing >=1 bg hole, bbox <= 6x6."""
    for _ in range(200):
        cand = _rand_poly(rng, rng.randint(9, 16))
        if max(r for r, _ in cand) <= 5 and max(c for _, c in cand) <= 5 \
           and _hole_count(cand) >= 1:
            return cand
    return _HOLED[0]


def _rand_solid(rng):
    """Small compact blob with no enclosed hole (a non-target distractor)."""
    for _ in range(40):
        cand = _rand_poly(rng, rng.randint(3, 6))
        if _hole_count(cand) == 0:
            return cand
    return _SOLID[0]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 non-bg component has a bg cell enclosed in its bbox (the holed object)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    seen = set()
    holed = 0
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) in seen or grid[r0][c0] == 0:
                continue
            stack = [(r0, c0)]; seen.add((r0, c0)); cells = [(r0, c0)]
            while stack:
                r, c = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 0:
                        seen.add((nr, nc)); stack.append((nr, nc)); cells.append((nr, nc))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
            bbox_bg = any(grid[r][c] == 0 for r in range(r1, r2 + 1) for c in range(c1, c2 + 1))
            if bbox_bg:
                holed += 1
    if holed < 1:
        return [f"expected >=1 holed component (bbox contains bg); found {holed}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_solid = rng.randint(1, 2)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 1 + n_solid)
    # Exactly one holed component (the rule's target) + solid distractors.
    _place(g, rng, _rand_holed(rng), palette[0])
    for color in palette[1:]:
        _place(g, rng, _rand_solid(rng), color)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_components":
        return g
    if name == "all_solid":
        # No component has a hole — rule's selector finds nothing.
        for r in range(2):
            for c in range(2):
                g[1 + r][1 + c] = 1
        for r in range(3):
            for c in range(3):
                g[5 + r][5 + c] = 2
        return g
    if name == "all_holed":
        # Two holed components — selector's "exactly one" fails.
        for dr, dc in _HOLED[0]:
            g[1 + dr][1 + dc] = 1
        for dr, dc in _HOLED[0]:
            if 1 + dr < h and 7 + dc < w:
                g[1 + dr][7 + dc] = 2
        return g
    return g
