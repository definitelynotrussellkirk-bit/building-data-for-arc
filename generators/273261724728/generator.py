"""Generator for v3_rich_schema:hard_01_rotate_exemplar_by_target_color.

Rule: find the EXEMPLAR -- a 4-connected blob of non-zero cells holding
exactly one color-1 ANCHOR plus several color-3 body cells; its body
offsets (relative to the anchor) are the shape. Every TARGET marker (a
lone cell colored 2/4/6/8) encodes a rotation (2=0deg, 4=90, 6=180,
8=270); at each target, stamp the body rotated by that amount in color
3, painting only empty cells.

Combinatorial axes: grid size, the exemplar shape + anchor, and the
targets (count, positions, rotation codes).
Degenerates: no_exemplar, no_targets, anchor_outside_exemplar.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "273261724728"
VERSION = "3.0.1"  # diversity: random exemplar + N targets + size (was fixed T-shape, 2 fixed targets ~13)
TASK_ID = "273261724728"
SUMMARY = (
    "0-bg grid (size varies). One EXEMPLAR: a 4-connected blob with a "
    "single color-1 (blue) ANCHOR plus several color-3 (green) body cells. "
    "1-4 TARGET markers, each a lone cell colored from {2,4,6,8} encoding a "
    "rotation (2=0deg, 4=90, 6=180, 8=270), placed apart with their rotated "
    "stamp footprints kept empty. Rule: at each target, stamp the exemplar "
    "body rotated by the coded amount in color 3 onto empty cells. The grid "
    "size, the exemplar shape/anchor, and the targets' count/positions/codes "
    "all vary freely (was a fixed T-shape + two fixed targets, ~13 distinct)."
)

INVARIANTS = [
    "exactly one color-1 anchor in the grid; all color-3 cells lie in the exemplar blob",
    "the exemplar is a single 4-connected non-zero component with anchor + body",
    "target colors are drawn from {2,4,6,8}; each rotated stamp lands in-bounds on empty cells",
]

PALETTE_KINDS = ("default", "rot_0", "rot_90", "rot_180")
DEGENERATE_TEXTURES = ("no_exemplar", "no_targets", "anchor_outside_exemplar")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|rot_0|rot_90|rot_180"},
    "n_targets":      {"type": "int", "default": "varies", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "exemplar_plus_targets",
                       "valid": "exemplar_plus_targets"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5"},
    "exemplar_kind":  {"type": "str", "default": "random_polyomino",
                       "valid": "random_polyomino"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|rot_0|rot_90|rot_180|"
                                "no_exemplar|no_targets|anchor_outside_exemplar"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_CODES = [2, 4, 6, 8]
_ROT = {2: 0, 4: 1, 6: 2, 8: 3}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-1 anchor; ≥1 color-3 body cell; ≥1 target from {2,4,6,8}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    body3 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    targets = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (2, 4, 6, 8)]
    if not anchors and not body3 and not targets:
        return errors  # degenerate — allowed
    if len(anchors) != 1:
        errors.append(f"expected exactly 1 color-1 anchor; found {len(anchors)}")
    if not body3:
        errors.append("no color-3 exemplar body cells")
    if not targets:
        errors.append("no target cells (colors 2/4/6/8)")
    return errors


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return cells


def _rot(off, k):
    r, c = off
    for _ in range(k % 4):
        r, c = c, -r
    return (r, c)


def _place_cluster(occ, cells, h, w):
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
            return False
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) in cset:
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    for (r, c) in cells:
        occ[r][c] = True
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        hr, wr, sr, tr = (11, 13), (11, 13), (3, 4), (1, 2)
    elif difficulty == "hard":
        hr, wr, sr, tr = (16, 22), (17, 24), (4, 6), (3, 4)
    else:
        hr, wr, sr, tr = (13, 17), (14, 19), (4, 5), (2, 3)

    for _attempt in range(40):
        # exemplar shape: a connected blob; one cell is the anchor (1), rest body (3)
        blob = list(_poly(rng, rng.randint(*sr)))
        ar, ac = rng.choice(blob)
        offsets = [(r - ar, c - ac) for (r, c) in blob if (r, c) != (ar, ac)]
        if len(offsets) < 2:
            continue

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]

        # place the exemplar
        placed_ex = False
        for _t in range(40):
            er = rng.randint(0, h - 1); ec = rng.randint(0, w - 1)
            cells = [(er, ec)] + [(er + o[0], ec + o[1]) for o in offsets]
            if _place_cluster(occ, cells, h, w):
                g[er][ec] = 1
                for (r, c) in cells[1:]:
                    g[r][c] = 3
                placed_ex = True
                break
        if not placed_ex:
            continue

        # place targets: each reserves its rotated stamp footprint as empty
        placed_t = 0
        for _ in range(rng.randint(*tr)):
            v = rng.choice(_CODES)
            ro = [_rot(o, _ROT[v]) for o in offsets]
            for _t in range(40):
                tr0 = rng.randint(0, h - 1); tc0 = rng.randint(0, w - 1)
                foot = [(tr0, tc0)] + [(tr0 + o[0], tc0 + o[1]) for o in ro]
                if _place_cluster(occ, foot, h, w):
                    g[tr0][tc0] = v          # marker only; footprint stays 0
                    placed_t += 1
                    break
        if placed_t >= 1:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 12, 0)
    exemplar = [(0, 1, 3), (1, 0, 3), (1, 1, 1), (2, 1, 3)]
    if name == "no_exemplar":
        g[2][8] = 2; g[7][8] = 6
        return g
    if name == "no_targets":
        for dr, dc, v in exemplar:
            g[1 + dr][1 + dc] = v
        return g
    if name == "anchor_outside_exemplar":
        for dr, dc, v in [(0, 1, 3), (1, 0, 3), (2, 1, 3)]:
            g[1 + dr][1 + dc] = v
        g[2][8] = 4; g[7][8] = 8
        return g
    return g
