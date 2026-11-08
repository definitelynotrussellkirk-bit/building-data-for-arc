"""Generator for 966f31e63b08.

Rule: the color-2 cells define a small template shape.  The rule scans all
positions where that template's cells currently sit on background 0; when the
template is odd x odd with a missing center, the center cell must be color 5.
It greedily paints every non-overlapping valid footprint with color 2.

The canonical task is a dense 0/5 field with a small 2-template embedded in it,
not a sparse marker-only canvas.  This generator therefore builds noisy 5-fields,
carves several valid empty footprints, and keeps a few template variants so the
examples show both the 5-centered and ordinary empty-footprint cases.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "966f31e63b08"
VERSION = "2.1.0"
TASK_ID = "966f31e63b08"
SUMMARY = (
    "Dense 0/5 field containing a small color-2 template. Several empty "
    "footprints of that template are carved into the field; odd center-hole "
    "templates also keep a color-5 center marker. Rule: greedily stamp the "
    "template into every non-overlapping valid footprint."
)

INVARIANTS = [
    "the color-2 cells form one small bbox-spanning template",
    "the grid has a dense field of color-5 distractor/marker cells",
    "at least two non-overlapping template footprints are valid rule candidates",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_template", "no_markers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "10..15"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..15"},
    "template_kind":  {"type": "str", "default": "rng", "valid": "l|zig|block|frame|cross"},
    "n_footprints":   {"type": "int", "default": "varies", "valid": "2..9"},
    "five_density":   {"type": "float", "default": "rng", "valid": "0.34..0.56"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "dense_field_with_carved_footprints",
                       "valid": "dense_field_with_carved_footprints"},
    "texture":        {"type": "str", "default": "default",
                       "valid": "default|no_template|no_markers|full_grid"},
}

# Bbox-spanning templates.  Odd x odd shapes with a missing center exercise the
# rule's color-5-center guard; even/non-hole shapes exercise the plain empty
# footprint path visible in several canonical train examples.
BASE_SHAPES = [
    [(0, 0), (1, 0), (1, 1), (2, 0)],                         # 3x2 L
    [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],                 # 2x3 cap
    [(0, 0), (0, 1), (1, 0), (1, 1)],                         # 2x2 block
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],
    [(0, 1), (1, 0), (1, 2), (2, 1)],                         # 3x3 cross-hole
]
HARD_EXTRA_SHAPES = [
    [(0, c) for c in range(5)] + [(4, c) for c in range(5)] + [(r, 0) for r in range(1, 4)] + [(r, 4) for r in range(1, 4)],
    [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],
]


def _dims(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _center_required(cells):
    sh, sw = _dims(cells)
    cr, cc = sh // 2, sw // 2
    return sh % 2 == 1 and sw % 2 == 1 and (cr, cc) not in set(cells)


def _box_cells(r0, c0, sh, sw):
    return {(r0 + r, c0 + c) for r in range(sh) for c in range(sw)}


def _footprint(cells, r0, c0):
    return {(r0 + r, c0 + c) for r, c in cells}


def _pick_shape(rng, difficulty):
    pool = BASE_SHAPES + (HARD_EXTRA_SHAPES if difficulty == "hard" else [])
    return list(rng.choice(pool))


def _ranges_for(difficulty, rng):
    if difficulty == "easy":
        return rng.randint(10, 11), rng.randint(10, 11), rng.randint(2, 4), rng.uniform(0.34, 0.44)
    if difficulty == "hard":
        return rng.randint(12, 15), rng.randint(12, 15), rng.randint(5, 9), rng.uniform(0.46, 0.56)
    return rng.randint(10, 13), rng.randint(10, 13), rng.randint(3, 7), rng.uniform(0.40, 0.52)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    for _attempt in range(80):
        h, w, want, density = _ranges_for(difficulty, rng)
        shape = _pick_shape(rng, difficulty)
        sh, sw = _dims(shape)
        if h <= sh + 1 or w <= sw + 1:
            continue

        g = full_grid(h, w, 0)
        for r in range(h):
            for c in range(w):
                if rng.random() < density:
                    g[r][c] = 5

        reserved: set[tuple[int, int]] = set()
        # Place the live template and clear its bbox so the 2-shape is legible.
        tr = rng.randint(0, h - sh)
        tc = rng.randint(0, w - sw)
        reserved |= _box_cells(tr, tc, sh, sw)
        for r, c in reserved:
            g[r][c] = 0
        for r, c in shape:
            g[tr + r][tc + c] = 2

        positions = [(r0, c0) for r0 in range(0, h - sh + 1)
                     for c0 in range(0, w - sw + 1)]
        rng.shuffle(positions)
        placed = 0
        center_req = _center_required(shape)
        cr, cc = sh // 2, sw // 2
        for r0, c0 in positions:
            box = _box_cells(r0, c0, sh, sw)
            if box & reserved:
                continue
            for rr, cc2 in _footprint(shape, r0, c0):
                g[rr][cc2] = 0
            if center_req:
                g[r0 + cr][c0 + cc] = 5
            reserved |= box
            placed += 1
            if placed >= want:
                break
        if placed >= 2:
            return g

    raise RuntimeError("could not place enough rule-visible template footprints")


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    for r in range(10):
        for c in range(10):
            if rng.random() < 0.45:
                g[r][c] = 5
    frame = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]
    for (r, c) in frame:
        g[1 + r][1 + c] = 2
    if name == "no_template":
        return [[5 if v == 2 else v for v in row] for row in g]
    if name == "no_markers":
        return [[0 if v == 5 else v for v in row] for row in g]
    if name == "full_grid":
        return full_grid(10, 10, 2)
    return g


def _candidate_count(grid, shape):
    h, w = len(grid), len(grid[0])
    sh, sw = _dims(shape)
    cr, cc = sh // 2, sw // 2
    center_req = _center_required(shape)
    count = 0
    occupied: set[tuple[int, int]] = set()
    for r0 in range(0, h - sh + 1):
        for c0 in range(0, w - sw + 1):
            cells = _footprint(shape, r0, c0)
            if center_req and grid[r0 + cr][c0 + cc] != 5:
                continue
            if not all(grid[r][c] == 0 for r, c in cells):
                continue
            if cells & occupied:
                continue
            occupied |= cells
            count += 1
    return count


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    bad = sorted({v for row in grid for v in row} - {0, 2, 5})
    if bad:
        errs.append(f"unexpected colors: {bad}")
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not twos:
        errs.append("no color-2 template cell found")
        return errs
    minr = min(r for r, _ in twos); minc = min(c for _, c in twos)
    maxr = max(r for r, _ in twos); maxc = max(c for _, c in twos)
    shape = [(r - minr, c - minc) for r, c in twos]
    sh, sw = maxr - minr + 1, maxc - minc + 1
    if not ({0, sh - 1} <= {r for r, _ in shape} and {0, sw - 1} <= {c for _, c in shape}):
        errs.append("template must span its bounding box")
    five_count = sum(v == 5 for row in grid for v in row)
    if five_count < max(8, (h * w) // 8):
        errs.append("color-5 field is too sparse for the canonical motif")
    candidates = _candidate_count(grid, shape)
    if candidates < 2:
        errs.append(f"need at least two rule-visible template footprints, found {candidates}")
    return errs
