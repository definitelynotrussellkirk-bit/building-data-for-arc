"""Generator for arc_puzzle_bank_fifth_21_bundle:easy_35_hollow_solid_rectangles.

Rule: solid rectangles of color 6 are hollowed by erasing their interiors.

Combinatorial axes: grid_h, grid_w, n_rects, texture
(plain|notched|thin_rect|color_decoy).
Degenerates: no_rects, hollow_rects, wrong_color_rects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "05a9779042f4"
VERSION = "3.3.0"
TASK_ID = "05a9779042f4"
SUMMARY = (
    "0-bg grid with 1-3 solid color-6 rectangles (3-6 x 3-6) that get "
    "their interiors erased to 0 (borders stay 6), alongside near-miss "
    "decoys the rule skips: notched 6-shapes (size != bbox area), thin "
    "2-row/2-col solid 6 rects (empty interior, unchanged), and solid "
    "rects in other colors. (Was: 3-4 x 3-5 rects only, solidity check "
    "never refuted, plus a fixed green marker at (h-1,0) every board.)"
)

# Rivals: 'hollow every 6-object' refuted by notched 6-shapes that
# stay. 'hollow every rectangle' refuted by other-color rects. 'thin
# rects vanish' refuted by 2xk rects with empty interiors staying
# whole. 3 demos incl. >=1 decoy board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=1 solid color-6 rectangle with nonempty interior (so output != input)",
    "notched decoys keep their object 4-connected",
    "decoy rects in other colors never use color 6",
]

DEGENERATE_TEXTURES = ("no_rects", "hollow_rects", "wrong_color_rects")
HELPFUL_TEXTURES = ("plain", "notched", "thin_rect", "color_decoy")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":  {"type": "int", "default": "rng 9..16", "valid": "6..18"},
    "n_rects": {"type": "int", "default": "rng 1..3", "valid": "1..4",
                "doc": "Solid 6-rects that get hollowed."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|notched|thin_rect|color_decoy|"
                         "no_rects|hollow_rects|wrong_color_rects",
                "doc": "notched: a 6-shape with a bite (stays); thin_rect: "
                       "2-row/2-col solid 6 rect (empty interior, stays); "
                       "color_decoy: solid non-6 rect (stays)."},
}


def _rect_fits(bb, occupied):
    return not any(not (bb[2] + 1 < ob[0] or ob[2] + 1 < bb[0]
                        or bb[3] + 1 < ob[1] or ob[3] + 1 < bb[1])
                   for ob in occupied)


def _place_rect(g, occupied, rng, rh, rw, color):
    h, w = len(g), len(g[0])
    if rh > h or rw > w:
        return None
    for _try in range(80):
        rr = rng.randint(0, h - rh)
        rc = rng.randint(0, w - rw)
        bb = (rr, rc, rr + rh - 1, rc + rw - 1)
        if not _rect_fits(bb, occupied):
            continue
        draw_rect(g, rr, rc, rh, rw, color)
        occupied.append(bb)
        return bb
    return None


def _place_rect_at(g, occupied, rr, rc, rh, rw, color):
    h, w = len(g), len(g[0])
    if rr < 0 or rc < 0 or rr + rh > h or rc + rw > w:
        return None
    bb = (rr, rc, rr + rh - 1, rc + rw - 1)
    if not _rect_fits(bb, occupied):
        return None
    draw_rect(g, rr, rc, rh, rw, color)
    occupied.append(bb)
    return bb


def _place_rect_anywhere(g, occupied, rng, rh, rw, color):
    """Exhaustive fallback for required teaching branches.

    The old branch-specific decoys were attempted after random large
    hollowable rectangles, so small boards often skipped the promised
    notched/thin/color-decoy branch.  This helper scans all placements
    (in a seeded shuffled order) before giving up.
    """
    h, w = len(g), len(g[0])
    if rh > h or rw > w:
        return None
    starts = [(rr, rc) for rr in range(h - rh + 1) for rc in range(w - rw + 1)]
    rng.shuffle(starts)
    for rr, rc in starts:
        bb = (rr, rc, rr + rh - 1, rc + rw - 1)
        if not _rect_fits(bb, occupied):
            continue
        draw_rect(g, rr, rc, rh, rw, color)
        occupied.append(bb)
        return bb
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "notched", "thin_rect", "color_decoy"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        n_rects = ctx.draw_int("n_rects", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 13, 16)
        n_rects = ctx.draw_int("n_rects", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 14)
        w = ctx.draw_int("grid_w", 9, 16)
        n_rects = ctx.draw_int("n_rects", 1, 3)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    occupied: list[tuple[int, int, int, int]] = []

    placed = 0
    if texture in ("notched", "thin_rect", "color_decoy"):
        # Reserve room for the requested counterexample branch with a fixed
        # two-corner layout.  Randomly placing the first 3x3 rectangle could
        # land in the middle of a small board and leave no legal second slot.
        if _place_rect_at(g, occupied, 0, 0, 3, 3, 6):
            placed += 1
        if texture == "notched":
            # 6-shape with a corner bite: size != bbox area, rule skips it.
            bb = _place_rect_at(g, occupied, h - 3, w - 3, 3, 3, 6)
            if bb:
                corner = rng.choice(((bb[0], bb[1]), (bb[0], bb[3]),
                                     (bb[2], bb[1]), (bb[2], bb[3])))
                g[corner[0]][corner[1]] = 0
        elif texture == "thin_rect":
            # 2-wide solid rect: interior range is empty, erase is a no-op.
            if rng.random() < 0.5:
                _place_rect_at(g, occupied, h - 2, w - 3, 2, 3, 6)
            else:
                _place_rect_at(g, occupied, h - 3, w - 2, 3, 2, 6)
        elif texture == "color_decoy":
            _place_rect_at(g, occupied, h - 3, w - 3, 3, 3,
                           rng.choice([1, 2, 3, 4, 5, 7, 8, 9]))

    for _ in range(max(0, n_rects - placed)):
        if _place_rect(g, occupied, rng,
                       rng.randint(3, min(6, h)), rng.randint(3, min(6, w)), 6):
            placed += 1
    if placed == 0:  # invariant: at least one hollowable rect
        if _place_rect_anywhere(g, occupied, rng, 3, 3, 6):
            placed += 1
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_rects          — scattered non-6 dots: identity.
    hollow_rects      — already-hollow 6 ring: size != area, identity.
    wrong_color_rects — solid rects in non-6 colors: identity.
    """
    rng = ctx.draw_rng("degenerate_placement")
    h = ctx.draw_int("grid_h", 8, 12)
    w = ctx.draw_int("grid_w", 9, 14)
    g = full_grid(h, w, 0)
    occupied: list[tuple[int, int, int, int]] = []
    if name == "no_rects":
        for color in rng.sample([1, 2, 3, 4, 5, 7, 8, 9], rng.randint(2, 4)):
            g[rng.randrange(h)][rng.randrange(w)] = color
        return g
    if name == "hollow_rects":
        for _ in range(rng.randint(1, 2)):
            bb = _place_rect(g, occupied, rng,
                             rng.randint(3, 5), rng.randint(3, 5), 6)
            if bb:
                for r in range(bb[0] + 1, bb[2]):
                    for c in range(bb[1] + 1, bb[3]):
                        g[r][c] = 0
        return g
    # wrong_color_rects
    for color in rng.sample([1, 2, 3, 4, 5, 7, 8, 9], rng.randint(1, 3)):
        _place_rect(g, occupied, rng, rng.randint(3, 4), rng.randint(3, 5), color)
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
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


def _bbox(cells):
    rs = [r for r, _c in cells]
    cs = [c for _r, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _is_solid_rect(cells):
    r0, c0, r1, c1 = _bbox(cells)
    return len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1)


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        msgs.append("ragged grid")
    hollowable = 0
    for color, cells in _components(grid):
        if color != 6 or not _is_solid_rect(cells):
            continue
        r0, c0, r1, c1 = _bbox(cells)
        if r1 - r0 + 1 >= 3 and c1 - c0 + 1 >= 3:
            hollowable += 1
    if hollowable < 1:
        msgs.append("no solid color-6 rectangle with nonempty interior")
    return msgs
