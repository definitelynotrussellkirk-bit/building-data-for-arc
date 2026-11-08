"""Generator for arc_puzzle_bank_21_set5_s:S5_E1 — legend-color crop.

The top-left legend color selects the same-color object to crop.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_target_match (no body object uses the legend color →
rule's selector finds nothing, output undefined), multiple_matches
(multiple body objects use the legend color → "the object" is
ambiguous, tie-break decides), no_distractors (only one object plus
legend → no distractor contrast, rule looks like "crop everything").
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "77d32a44a58c"
VERSION = "2.1.0"  # distinct=35/dup24%: output is the legend-color object's crop; target object came from a 4-shape bank (4-5 cells) -> few shapes. Use a RANDOM connected polyomino (3-9 cells) for the target -> its crop varies widely incl non-square.
TASK_ID = "77d32a44a58c"

SUMMARY = (
    "0-bg grid (h~8-12, w~"
    "8-13) with: (a) CELL "
    "(0, 0) is the TARGET "
    "COLOR LEGEND in some "
    "color from {1..9}; (b) "
    "ONE NON-LEGEND OBJECT "
    "in the TARGET COLOR — "
    "drawn from a 4-shape "
    "bank (4-5 cell shapes), "
    "placed at an interior "
    "position with 1-cell "
    "padding; (c) 1-4 "
    "DISTRACTOR OBJECTS in "
    "DISTINCT non-target "
    "colors at scattered "
    "positions. Output "
    "uniq_out=23 (intrinsic "
    "— 4 shape banks × ~9 "
    "colors normalizes). "
    "Rule (CROP LEGEND-"
    "COLOR OBJECT): READ "
    "TARGET COLOR T = "
    "g[0][0]. Identify the "
    "BODY OBJECT in color T "
    "(excluding the (0, 0) "
    "legend cell itself). "
    "CROP that object to "
    "its BBOX. EMIT the "
    "cropped subgrid. Net: "
    "(0, 0) color points to "
    "the matching body "
    "object; output is its "
    "tight crop."
)

INVARIANTS = [
    "background is 0",
    "cell (0,0) contains the target color",
    "exactly one non-legend object has that target color",
    "distractor objects use other colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_target_match", "multiple_matches", "no_distractors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..17"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "6..18"},
    "target_shape":   {"type": "choice", "default": "rng 0..3", "valid": "0..3"},
    "distractor_count": {"type": "int", "default": "rng 1..2", "valid": "0..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "legend_plus_target_plus_distractors",
                       "valid": "legend_plus_target_plus_distractors"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 1), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)],
]

_DISTRACTORS = [
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
]


def _place(g, rng, cells, color, occupied, *, padding=1):
    h = len(g)
    w = len(g[0])
    max_r = max(r for r, _ in cells)
    max_c = max(c for _, c in cells)
    for _ in range(300):
        r0 = rng.randint(1, h - max_r - 1)
        c0 = rng.randint(1, w - max_c - 1)
        placed = [(r0 + r, c0 + c) for r, c in cells]
        if any(g[r][c] != 0 for r, c in placed):
            continue
        if any(abs(r - rr) <= padding and abs(c - cc) <= padding
               for r, c in placed for rr, cc in occupied):
            continue
        for r, c in placed:
            g[r][c] = color
        occupied.update(placed)
        return
    raise ValueError("could not place object")


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        distractor_count = ctx.draw_int("distractor_count", 1, 1); tk_lo, tk_hi = 3, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 17)
        w = ctx.draw_int("grid_w", 13, 18)
        distractor_count = ctx.draw_int("distractor_count", 2, 4); tk_lo, tk_hi = 5, 9
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 15)
        distractor_count = ctx.draw_int("distractor_count", 1, 2); tk_lo, tk_hi = 3, 8
    rng = ctx.draw_rng("layout")
    shape = _rand_poly(rng, rng.randint(tk_lo, tk_hi))
    g = full_grid(h, w, 0)
    target = ctx.draw_color("target_color", exclude={0})
    g[0][0] = target
    occupied = {(0, 0)}
    _place(g, rng, shape, target, occupied)
    colors = [c for c in range(1, 10) if c != target]
    for idx in range(distractor_count):
        _place(g, rng, rng.choice(_DISTRACTORS), colors[idx % len(colors)], occupied)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    g[0][0] = 5
    if name == "no_target_match":
        # Legend says color 5 but no body object is color 5;
        # rule's selector finds nothing.
        for dr, dc in _DISTRACTORS[1]:
            g[3 + dr][3 + dc] = 2
        for dr, dc in _DISTRACTORS[2]:
            g[5 + dr][6 + dc] = 4
        return g
    if name == "multiple_matches":
        # Multiple body objects share the legend color 5; "the
        # object" is ambiguous, tie-break decides.
        for dr, dc in _SHAPES[0]:
            g[2 + dr][2 + dc] = 5
        for dr, dc in _SHAPES[2]:
            g[2 + dr][6 + dc] = 5
        return g
    if name == "no_distractors":
        # Only one object plus legend — no distractor contrast;
        # rule looks like "crop everything".
        for dr, dc in _SHAPES[1]:
            g[3 + dr][3 + dc] = 5
        return g
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
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
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    target = grid[0][0]
    if target == 0:
        errs.append("legend cell (0,0) is background")
    target_body = []
    distractors = 0
    for color, cells in _components(grid):
        if color == target:
            body_cells = [p for p in cells if p != (0, 0)]
            if body_cells:
                target_body.append(body_cells)
        else:
            distractors += 1
    if len(target_body) != 1:
        errs.append(f"expected exactly one non-legend target-color object, got {len(target_body)}")
    if distractors < 1:
        errs.append("missing non-target distractor object")
    return errs
