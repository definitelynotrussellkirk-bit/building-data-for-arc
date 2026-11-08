"""Generator for 12b:m83 — select the LR-symmetric blob, crop + recolor.

Canonical rule: the TOP-LEFT cell (0,0) is a COLOR KEY. Zero it out, find
every object, keep the one whose cropped binary mask is LR-symmetric (== its
flip-lr), take the smallest such, crop it to its bbox, and recolor every cell
to the KEY color. Output = the symmetric blob, in the key color.

The old generator never set the (0,0) key (so the key was ~always 0 -> blank
outputs, distinct=3) and drew the symmetric blob from only 2 fixed shapes.
Now: place the key pixel, a RANDOM LR-symmetric target blob (the unique
symmetric object), and asymmetric distractors. Output = the symmetric shape
recolored to the key -> output shape AND color both vary widely.

Combinatorial axes: grid size, key color, the symmetric blob shape/size,
distractor count/shapes/colors, positions.
Degenerates: no_distractors, big_symmetric, many_distractors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a09c683cd25"
VERSION = "3.1.0"  # distinct=3 (catastrophic): rule reads (0,0) as a COLOR KEY, picks the unique LR-symmetric object, crops + recolors to the key. Old gen never set the key (-> ~0 -> blank crops) and used 2 fixed sym shapes. Now place the key + a RANDOM LR-symmetric target + asymmetric distractors -> output shape AND color vary.
TASK_ID = "5a09c683cd25"
SUMMARY = (
    "0-bg grid (size varies). Cell (0,0) holds a COLOR KEY. The grid contains "
    "ONE LR-SYMMETRIC target blob (a random connected LR-symmetric polyomino, "
    "3-14 cells, its own color) and 1-3 LR-ASYMMETRIC distractor blobs (each a "
    "random asymmetric polyomino in a distinct color). All blobs are placed "
    "non-touching (8-connectivity gap) so they are separate components, and "
    "none sits at (0,0). Rule (SELECT LR-SYMMETRIC BLOB, CROP + RECOLOR TO "
    "KEY): read the key color at (0,0); zero it; among all objects keep those "
    "whose cropped binary mask equals its flip-lr; take the smallest; crop to "
    "bbox; recolor every cell to the KEY color. Output = the symmetric blob's "
    "shape painted in the key color. Distractors (asymmetric) are never "
    "candidates, so the symmetric target is always the one selected."
)

INVARIANTS = [
    "cell (0,0) is the non-background color key",
    "exactly one LR-symmetric multi-cell object (the target)",
    "every other object is LR-asymmetric (>= 2 cells, never a stray pixel)",
    "blobs do not 8-touch, so each is its own connected component",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_distractors", "big_symmetric", "many_distractors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "8..15"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..5"},
    "distractor_count": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "key_plus_sym_plus_asym",
                       "valid": "key_plus_sym_plus_asym"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _norm(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for (r, c) in cells]


def _is_lr_sym(cells):
    s = set(cells)
    W = max(c for _, c in cells) + 1
    return all((r, W - 1 - c) in s for (r, c) in cells)


def _has_background_in_bbox(cells):
    """Canonical outputs are cropped shapes with visible background, not filled
    rectangles.  A solid rectangle still passes the Racket rule but hides the
    shape-selection/cropping lesson and was flagged by the generic linter."""
    H = max(r for r, _ in cells) + 1
    W = max(c for _, c in cells) + 1
    return len(set(cells)) < H * W


def _rand_lr_sym(rng):
    """Random connected LR-symmetric polyomino: grow a connected blob in the
    left half (cols 0..cw, seeded on the center column), then mirror across
    column cw. Sharing the self-mirrored center column keeps it connected."""
    for _ in range(80):
        cw = rng.randint(1, 3)
        H = rng.randint(2, 5)
        cells = {(rng.randint(0, H - 1), cw)}
        target = rng.randint(3, 8)
        guard = 0
        while len(cells) < target and guard < 300:
            guard += 1
            r, c = rng.choice(tuple(cells))
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc <= cw:
                cells.add((nr, nc))
        full = set()
        for (r, c) in cells:
            full.add((r, c))
            full.add((r, 2 * cw - c))
        norm = _norm(full)
        if _is_lr_sym(norm) and _has_background_in_bbox(norm):
            return norm
    # Connected LR-symmetric fallback with an internal background cell after crop.
    return [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)]


def _rand_asym(rng):
    """Random connected asymmetric (not LR-symmetric) polyomino, >= 3 cells."""
    for _ in range(60):
        H = rng.randint(2, 4)
        Wd = rng.randint(2, 4)
        cells = {(rng.randint(0, H - 1), rng.randint(0, Wd - 1))}
        target = rng.randint(3, 6)
        guard = 0
        while len(cells) < target and guard < 200:
            guard += 1
            r, c = rng.choice(tuple(cells))
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < Wd:
                cells.add((nr, nc))
        norm = _norm(cells)
        if len(norm) >= 3 and not _is_lr_sym(norm):
            return norm
    return [(0, 0), (1, 0), (1, 1)]  # L-tromino, asymmetric


def _free(g, r0, c0, cells):
    h, w = len(g), len(g[0])
    for (r, c) in cells:
        rr, cc = r0 + r, c0 + c
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    if sh > h or sw > w:
        return False
    for _ in range(120):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, cells):
            for (r, c) in cells:
                g[r0 + r][c0 + c] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        ndist = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 13, 16)
        ndist = ctx.draw_int("distractor_count", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 13)
        ndist = ctx.draw_int("distractor_count", 1, 2)

    pal = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2 + ndist)
    key, sym_color = pal[0], pal[1]
    dist_colors = pal[2:]

    g = full_grid(h, w, 0)
    g[0][0] = key
    # place the symmetric target first (on a near-empty grid it always fits).
    _place(g, rng, _rand_lr_sym(rng), sym_color)
    for dc in dist_colors:
        _place(g, rng, _rand_asym(rng), dc)
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) == (0, 0) or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color and (nr, nc) != (0, 0)):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, comp))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the color-key + unique LR-symmetric crop target invariants."""
    errs = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid is not a non-empty rectangular list"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    if grid[0][0] == 0:
        errs.append("top-left key color is background")
    comps = _components(grid)
    if not comps:
        errs.append("no non-key objects")
        return errs
    sym = []
    for color, comp in comps:
        norm = _norm(comp)
        if len(norm) < 3:
            errs.append("object has fewer than 3 cells")
        if _is_lr_sym(norm):
            sym.append((color, norm))
    if len(sym) != 1:
        errs.append(f"expected exactly one LR-symmetric object, found {len(sym)}")
    elif not _has_background_in_bbox(sym[0][1]):
        errs.append("LR-symmetric target crops to a solid rectangle")
    return errs


def _draw_from_degenerate(name, rng):
    rng = rng or __import__("random").Random(0)
    g = full_grid(11, 13, 0)
    g[0][0] = 8
    _place(g, rng, _rand_lr_sym(rng), 4)
    if name == "no_distractors":
        return g
    if name == "big_symmetric":
        # an extra-large symmetric target dominates the grid
        for r, c in [(3, 5), (3, 6), (3, 7), (4, 6), (5, 6), (5, 5), (5, 7)]:
            g[r][c] = 4
        return g
    if name == "many_distractors":
        for dc in (2, 3, 6):
            _place(g, rng, _rand_asym(rng), dc)
        return g
    return g
