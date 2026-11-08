"""Generator for 543a7ed5 -- halo and interior-fill around color-6 shapes.

Rule: background is 8. For each 4-connected component containing a color-6
cell, paint the 1-cell ring of background cells around the component's bbox
to 3 (a green halo), and paint the background cells INSIDE the bbox to 4.
The color-6 cells themselves are kept.

This generator scatters color-6 shapes (some solid, some hollow, so interior
4-fills appear) on an 8 background with enough separation that each shape's
halo fits.

Combinatorial axes: grid size, the number/shape of color-6 components and
their positions.
Degenerates: no_shapes, solid_only, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f75403bbef0c"
VERSION = "2.2.0"  # bigger frames + concave U/C shapes (richer 4-fills) + more shapes (was <=5x5 frames, solid/hollow only)
TASK_ID = "f75403bbef0c"
SUMMARY = (
    "8-bg grid (size varies) with several color-6 shapes (some hollow). Rule: "
    "around each shape's bbox paint a 1-cell background halo of 3, and fill "
    "the background cells inside the bbox with 4; the shape stays color 6. "
    "The grid size, shape count/forms and positions vary freely (was a fixed "
    "setup, ~27 distinct)."
)

INVARIANTS = [
    "background is 8; shapes are connected color-6 components",
    "each component's bbox gets a 1-cell halo of 3 and interior bg -> 4",
    "shapes are separated so their halos fit and stay distinct",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shapes", "solid_only", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..26"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..26"},
    "n_shapes":       {"type": "int", "default": "varies", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_shapes|solid_only|full_grid"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _hollow_rect(rng):
    h = rng.randint(3, 9); w = rng.randint(3, 9)
    return [(r, c) for r in range(h) for c in range(w)
            if r in (0, h - 1) or c in (0, w - 1)]


def _u_shape(rng):
    """Rectangular frame missing one side -> a big open notch (large 4-fill)."""
    h = rng.randint(3, 8); w = rng.randint(3, 8)
    cells = [(r, c) for r in range(h) for c in range(w)
             if r in (0, h - 1) or c in (0, w - 1)]
    side = rng.choice(["top", "bottom", "left", "right"])
    drop = {"top": lambda r, c: r == 0 and 0 < c < w - 1,
            "bottom": lambda r, c: r == h - 1 and 0 < c < w - 1,
            "left": lambda r, c: c == 0 and 0 < r < h - 1,
            "right": lambda r, c: c == w - 1 and 0 < r < h - 1}[side]
    return [(r, c) for (r, c) in cells if not drop(r, c)]


def _solid_rect(rng):
    h = rng.randint(2, 7); w = rng.randint(2, 7)
    return [(r, c) for r in range(h) for c in range(w)]


def _reserve(occ, top, left, sh, sw, h, w, margin=2):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w:
                occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, nr = (12, 15), (12, 16), (1, 2)
    elif difficulty == "hard":
        hr, wr, nr = (20, 26), (20, 26), (3, 5)
    else:
        hr, wr, nr = (15, 20), (15, 21), (2, 4)

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 8)
        occ = [[False] * w for _ in range(h)]
        placed = 0
        target = rng.randint(*nr)
        for _i in range(target * 4):
            if placed >= target:
                break
            kind = rng.choice(["hollow", "hollow", "u", "u", "poly", "solid"])
            if kind == "hollow":
                shape = _hollow_rect(rng)              # ring -> interior 4-fill
            elif kind == "u":
                shape = _u_shape(rng)                  # open notch -> big 4-fill
            elif kind == "solid":
                shape = _solid_rect(rng)               # solid -> halo only
            else:
                shape = _poly(rng, rng.randint(4, 14))  # blob (varied)
            sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
            # keep a 1-cell margin from the border so the halo is fully in bounds
            if sh + 2 >= h or sw + 2 >= w:
                continue
            top = rng.randint(1, h - sh - 1); left = rng.randint(1, w - sw - 1)
            if not _reserve(occ, top, left, sh, sw, h, w):
                continue
            for (r, c) in shape:
                g[top + r][left + c] = 6
            placed += 1
        if placed == target:
            return g

    return _fallback_layout(difficulty, target)


def _fallback_layout(difficulty, target):
    """Deterministic separated-ring fallback used only after random packing fails."""
    if difficulty == "easy":
        h, w = 15, 16
        anchors = [(3, 3), (3, 10)]
    elif difficulty == "hard":
        h, w = 26, 26
        anchors = [(2, 2), (2, 11), (2, 20), (14, 5), (14, 16)]
    else:
        h, w = 20, 21
        anchors = [(2, 2), (2, 12), (12, 2), (12, 12)]
    ring = [(r, c) for r in range(3) for c in range(3)
            if r in (0, 2) or c in (0, 2)]
    g = full_grid(h, w, 8)
    for top, left in anchors[:target]:
        for dr, dc in ring:
            g[top + dr][left + dc] = 6
    return g


def _components_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                y, x = stack.pop()
                comp.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and (ny, nx) not in seen and grid[ny][nx] == color:
                        seen.add((ny, nx))
                        stack.append((ny, nx))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    vals = {v for row in grid for v in row}
    if not vals <= {6, 8}:
        errors.append(f"input must contain only background 8 and shape color 6, found {sorted(vals)}")
    comps = _components_color(grid, 6)
    lo = 1 if difficulty == "easy" else 3 if difficulty == "hard" else 2
    hi = 2 if difficulty == "easy" else 5 if difficulty == "hard" else 4
    if not (lo <= len(comps) <= hi):
        errors.append(f"expected {lo}..{hi} separated shapes, found {len(comps)}")
    boxes = []
    for comp in comps:
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        if r0 < 1 or c0 < 1 or r1 > h - 2 or c1 > w - 2:
            errors.append(f"shape bbox {(r0, c0, r1, c1)} leaves no room for 1-cell halo")
        boxes.append((r0 - 1, c0 - 1, r1 + 1, c1 + 1))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]):
                errors.append(f"shape halos overlap: {a} vs {b}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    if name == "no_shapes":
        return full_grid(h, w, 8)
    if name == "full_grid":
        return full_grid(h, w, 6)
    g = full_grid(h, w, 8)
    if name == "solid_only":
        for (r, c) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
            g[r][c] = 6
        return g
    for (r, c) in _hollow_rect(rng):
        g[3 + r][3 + c] = 6
    return g
