"""Generator for arc_additional_puzzle_bank_volume10:M65.

Rule: the smallest green object is rotated by the control color and
stamped at the maroon anchor.

Combinatorial axes (8): grid_h/w, palette_kind, control_color, num_greens,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: tied_smallest, no_control, no_anchor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "02346c46fc4d"
VERSION = "2.2.0"  # 2.2.0: add executable smallest-green/control-anchor self-check.
TASK_ID = "02346c46fc4d"
SUMMARY = (
    "0-bg grid with one control cell (2=identity 4=cw90 5=180 "
    "6=ccw90), one maroon(9) anchor, the SMALLEST green(3) object "
    "(3-4 cells, rotation-asymmetric) and 1-2 larger green "
    "distractors. Rule: rotate the smallest green per the control and "
    "stamp it in CYAN(8) with its normalized origin at the anchor — "
    "ONTO the input (everything else, distractors included, stays)."
)

# Rivals: 'stamp in green' refuted (stamp is cyan-8). 'distractors
# vanish' refuted (input preserved). 'rotate the LARGEST green'
# refuted by size selection. 'anchor is decoration' refuted by stamp
# position tracking it. 'stamps never clip' refuted by edge-anchor
# demos. 4 demos covering >=3 control values.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one control cell valued 2/4/5/6 and one maroon-9 anchor",
    "the smallest green is uniquely smallest and rotation-asymmetric",
    "greens always exist (a greenless board crashes the rule)",
    "default anchors keep the stamp in-bounds; edge_anchor boards clip",
]

DEGENERATE_TEXTURES = ("tied_smallest",)
HELPFUL_TEXTURES = ("plain", "edge_anchor", "two_distractors")

AXES = {
    "grid_h":        {"type": "int", "default": "rng 10..14", "valid": "7..24"},
    "grid_w":        {"type": "int", "default": "rng 10..14", "valid": "7..24"},
    "control_color": {"type": "int", "default": "rng", "valid": "2|4|5|6",
                      "doc": "Rotation selector."},
    "small_size":    {"type": "int", "default": "rng 3..4", "valid": "3..4",
                      "doc": "Cells in the smallest green."},
    "texture":       {"type": "str", "default": "rng helpful",
                      "valid": "plain|edge_anchor|two_distractors|tied_smallest",
                      "doc": "edge_anchor clips the stamp at the border."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "plain", "edge_anchor", "two_distractors"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 10, 14)
    small_size = ctx.draw_int("small_size", 3, 4)
    rng = ctx.draw_rng("placement")
    small_shapes_3 = [
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 1)],
    ]
    small_shapes_4 = [
        [(0, 0), (1, 0), (2, 0), (2, 1)],         # L-tetromino
        [(0, 0), (0, 1), (0, 2), (1, 0)],         # asymmetric 4-cell corner
        [(0, 1), (1, 0), (1, 1), (2, 1)],         # T-ish (rot-asym? T 90s differ)
    ]
    large_shapes = [
        [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 0), (0, 1), (0, 2), (0, 3), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)],
    ]
    n_distractors = 2 if texture == "two_distractors" else 1

    def place(shape, color):
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for _ in range(60):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
            if any(g[r][c] != 0 for r, c in cells):
                continue
            # 1-cell halo vs other greens so components never merge
            if any(g[rr][cc] == 3
                   for r, c in cells
                   for rr in range(max(0, r - 1), min(h, r + 2))
                   for cc in range(max(0, c - 1), min(w, c + 2))
                   if (rr, cc) not in cells):
                continue
            for r, c in cells:
                g[r][c] = color
            return True
        return False

    for _outer in range(40):
        g = full_grid(h, w, 0)
        small = rng.choice(small_shapes_3 if small_size == 3 else small_shapes_4)
        sh = max(r for r, _ in small) + 1
        sw = max(c for _, c in small) + 1
        cr = rng.randint(0, h - 1)
        cc = rng.randint(0, w - 1)
        g[cr][cc] = int(overrides.get("control_color", rng.choice([2, 4, 5, 6])))
        # anchor: stamp footprint is at most max(sh, sw) per side after
        # rotation; default keeps it in-bounds, edge_anchor forces a clip
        side = max(sh, sw)
        for _ in range(40):
            if texture == "edge_anchor":
                ar = rng.choice([h - 1, h - 2])
                ac = rng.randint(0, w - 1)
            else:
                ar = rng.randint(0, h - side)
                ac = rng.randint(0, w - side)
            if g[ar][ac] == 0:
                g[ar][ac] = 9
                break
        if not place(small, 3):
            continue
        ok = True
        for _ in range(n_distractors):
            big = rng.choice(large_shapes)
            if len(big) <= len(small):
                big = large_shapes[0]
            if not place(big, 3):
                ok = False
                break
        if ok:
            return g
    # last-resort: minimal valid board (greens MUST exist — the rule
    # crashes on a greenless grid)
    g = full_grid(h, w, 0)
    g[0][0] = 2
    g[h - 3][w - 3] = 9
    for r, c in ((2, 1), (2, 2), (3, 1)):
        g[r][c] = 3
    for r, c in ((5, 5), (5, 6), (6, 5), (6, 6), (6, 7)):
        g[r][c] = 3
    return g


def _draw_from_degenerate(name, ctx):
    """tied_smallest — two greens tied at min size; the sort's
    topmost-leftmost tie-break silently decides. rng-varied.
    (no_control / no_anchor are NOT offered — both CRASH the rule at
    (fst #f) / (first '()).)"""
    h = ctx.draw_int("grid_h", 10, 13)
    w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("degenerate_placement")
    g = full_grid(h, w, 0)
    g[rng.randint(0, 1)][rng.randint(0, w - 1)] = rng.choice([2, 4, 5, 6])
    g[rng.randint(h - 3, h - 1)][rng.randint(0, w - 3)] = 9
    shape = [(0, 0), (0, 1), (1, 0)]
    for c0 in (1, w - 4):
        r0 = rng.randint(2, h - 4)
        if all(g[r0 + dr][c0 + dc] == 0 for dr, dc in shape):
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = 3
    return g


def self_check(grid, *, difficulty=None, meta=None):
    from puzzle_generators.helpers.selfcheck import components, d4_transform
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    controls = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (2, 4, 5, 6)]
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    greens = components(grid, colors={3}, same_color=True)
    if len(controls) != 1:
        errs.append("need exactly one rotation control in {2,4,5,6}")
    if len(anchors) != 1:
        errs.append("need exactly one color-9 anchor")
    if len(greens) < 2:
        errs.append("need smallest green plus at least one green distractor")
    sizes = [len(g["cells"]) for g in greens]
    if sizes and sizes.count(min(sizes)) != 1:
        errs.append("smallest green object must be unique")
    if greens:
        small = min(greens, key=lambda comp: len(comp["cells"]))
        norm = small["norm"]
        if len({d4_transform(norm, code) for code in (0, 1, 2, 3)}) < 4:
            errs.append("smallest green should be rotation-asymmetric")
    return errs
