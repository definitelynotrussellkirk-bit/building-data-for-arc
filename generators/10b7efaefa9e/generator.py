"""Generator for ARC task ae58858e.

Rule: for each non-bg 4-connected object: if size ≥4, recolor all its
cells to 6 (magenta); else keep.

Combinatorial axes: grid_h/w, fg_color, n_large/n_small, large_kind,
small_kind, placement. Degenerates: only_large, only_small,
touching_objects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "10b7efaefa9e"
VERSION = "1.2.0"  # bounds-guard large cells (line_h/v force len-4 past the small hard bbox)
TASK_ID = "10b7efaefa9e"
SUMMARY = "Separated objects of varied sizes; objects with ≥4 cells become 6."

INVARIANTS = [
    "background is zero",
    "foreground objects are 4-disconnected",
    "≥1 object size <4 (kept) and ≥1 object size ≥4 (recolored)",
]

LARGE_KINDS = ("rect", "L_shape", "cross", "blob", "line_h", "line_v")
SMALL_KINDS = ("single", "pair_h", "pair_v", "triple_L", "triple_line")
PLACEMENTS = ("random", "corners", "row", "column")
DEGENERATE_TEXTURES = ("only_large", "only_small", "touching_objects")
HELPFUL_TEXTURES = LARGE_KINDS

AXES = {
    "grid_h":          {"type": "int", "default": "rng 7..16", "valid": "5..22"},
    "grid_w":          {"type": "int", "default": "rng 7..16", "valid": "5..22"},
    "fg_color":        {"type": "color", "default": "rng (≠0,6)", "valid": "1..9 (≠6)"},
    "n_large_objects": {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_small_objects": {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "large_kind":      {"type": "str", "default": "rng helpful",
                        "valid": "rect|L_shape|cross|blob|line_h|line_v"},
    "small_kind":      {"type": "str", "default": "rng helpful",
                        "valid": "single|pair_h|pair_v|triple_L|triple_line"},
    "placement":       {"type": "str", "default": "rng random|corners|row|column",
                        "valid": "random|corners|row|column"},
    "texture":         {"type": "str", "default": "alias for large_kind",
                        "valid": "rect|L_shape|cross|blob|line_h|line_v|only_large|only_small|touching_objects"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, l_lo, l_hi, s_lo, s_hi = 7, 9, 1, 1, 1, 3
    elif difficulty == "hard":
        h_lo, h_hi, l_lo, l_hi, s_lo, s_hi = 13, 16, 2, 3, 4, 5
    else:
        h_lo, h_hi, l_lo, l_hi, s_lo, s_hi = 7, 16, 1, 3, 2, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, ctx, rng)
    fg = int(overrides.get("fg_color", ctx.draw_color("fg_color", exclude={0, 6})))
    n_large = int(overrides.get("n_large_objects",
                                ctx.draw_int("n_large_objects", l_lo, l_hi)))
    n_small = int(overrides.get("n_small_objects",
                                ctx.draw_int("n_small_objects", s_lo, s_hi)))
    large_kind = (overrides.get("texture") or overrides.get("large_kind")
                  or ctx.draw_choice("large_kind", list(LARGE_KINDS)))
    small_kind = overrides.get("small_kind",
                               ctx.draw_choice("small_kind", list(SMALL_KINDS)))

    for _layout_attempt in range(80):
        g = full_grid(h, w, 0)
        occupied: set[tuple[int, int]] = set()
        for _ in range(n_large):
            for _try in range(40):
                sh = rng.randint(2, max(2, h // 4))
                sw = rng.randint(2, max(2, w // 4))
                rr = rng.randint(0, h - sh - 1); rc = rng.randint(0, w - sw - 1)
                if not _check_clear(g, rr, rc, sh, sw):
                    continue
                cells = _large_cells(large_kind, sh, sw)
                if len(cells) < 4:
                    cells.append((sh - 1, sw - 1)); cells.append((0, sw - 1))
                    cells = list(set(cells))
                # line_h/line_v force a length of max(4, sw/sh), which can exceed the
                # sh×sw bbox that rr/rc were sized for; retry on overflow.
                if any(not (0 <= rr + dr < h and 0 <= rc + dc < w) for dr, dc in cells):
                    continue
                for dr, dc in cells:
                    g[rr + dr][rc + dc] = fg
                    occupied.add((rr + dr, rc + dc))
                break
        for _ in range(n_small):
            for _try in range(40):
                cells = _small_cells(small_kind, rng)
                rr = rng.randint(1, max(1, h - 4))
                rc = rng.randint(1, max(1, w - 4))
                actual = [(rr + dr, rc + dc) for dr, dc in cells]
                buffer = set()
                for (r, c) in actual:
                    for ddr in (-1, 0, 1):
                        for ddc in (-1, 0, 1):
                            buffer.add((r + ddr, c + ddc))
                if any(p in occupied for p in buffer):
                    continue
                for (r, c) in actual:
                    if 0 <= r < h and 0 <= c < w:
                        g[r][c] = fg
                        occupied.add((r, c))
                break
        sizes = _component_sizes(g)
        # The old implementation accepted partial placements and used a
        # disconnected checkerboard "blob", so normal boards often had no
        # size>=4 object at all.  Retry until both branches of the rule are
        # visible in the input.
        if any(s >= 4 for s in sizes) and any(s < 4 for s in sizes):
            return g
    # Deterministic safety fallback: keep the sample valid rather than silently
    # emitting a branch-missing board on unusually congested RNG paths.
    g = full_grid(h, w, 0)
    for r in range(1, min(3, h)):
        for c in range(1, min(3, w)):
            g[r][c] = fg
    if h >= 6 and w >= 6:
        g[h - 2][w - 2] = fg
        if w >= 7:
            g[h - 2][w - 3] = fg
    return g

def _check_clear(g, rr, rc, sh, sw):
    for r in range(max(0, rr - 1), min(len(g), rr + sh + 1)):
        for c in range(max(0, rc - 1), min(len(g[0]), rc + sw + 1)):
            if g[r][c] != 0:
                return False
    return True


def _large_cells(kind, sh, sw):
    if kind == "rect":
        return [(dr, dc) for dr in range(sh) for dc in range(sw)]
    if kind == "L_shape":
        out = [(dr, 0) for dr in range(sh)]
        out += [(sh - 1, dc) for dc in range(1, sw)]
        return out
    if kind == "cross":
        mr, mc = sh // 2, sw // 2
        out = [(mr, dc) for dc in range(sw)]
        out += [(dr, mc) for dr in range(sh) if dr != mr]
        return list(set(out))
    if kind == "blob":
        # Connected sparse blob.  The old checkerboard body split into several
        # 4-connected one-cell/two-cell objects, so a "large" object could be
        # seen by the rule as only small components.
        out = [(0, dc) for dc in range(sw)]
        out += [(dr, 0) for dr in range(1, sh)]
        out += [(dr, dc) for dr in range(1, sh) for dc in range(1, sw)
                if (dr + dc) % 3 == 0]
        return list(set(out))
    if kind == "line_h":
        return [(0, dc) for dc in range(max(4, sw))]
    if kind == "line_v":
        return [(dr, 0) for dr in range(max(4, sh))]
    return [(dr, dc) for dr in range(sh) for dc in range(sw)]


def _small_cells(kind, rng):
    if kind == "single":
        return [(0, 0)]
    if kind == "pair_h":
        return [(0, 0), (0, 1)]
    if kind == "pair_v":
        return [(0, 0), (1, 0)]
    if kind == "triple_L":
        return [(0, 0), (1, 0), (1, 1)]
    if kind == "triple_line":
        return [(0, 0), (0, 1), (0, 2)]
    return [(0, 0)]



def _component_sizes(g):
    h, w = len(g), len(g[0])
    seen = set()
    sizes = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            color = g[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            count = 0
            while stack:
                rr, cc = stack.pop()
                count += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and g[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            sizes.append(count)
    return sizes


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    vals = {v for row in grid for v in row if v != 0}
    if not vals:
        msgs.append("expected at least one foreground object")
    if 6 in vals:
        msgs.append("normal inputs should not already contain recolor target color 6")
    sizes = _component_sizes(grid)
    if not any(s >= 4 for s in sizes):
        msgs.append(f"expected at least one size>=4 object; component sizes={sizes}")
    if not any(0 < s < 4 for s in sizes):
        msgs.append(f"expected at least one size<4 object; component sizes={sizes}")
    return msgs

def _draw_from_degenerate(name, h, w, ctx, rng):
    fg = ctx.draw_color("fg_color", exclude={0, 6})
    g = full_grid(h, w, 0)
    if name == "only_large":
        for i, (rr, rc) in enumerate([(1, 1), (1, w - 5), (h - 5, 1)]):
            for r in range(rr, rr + 3):
                for c in range(rc, rc + 3):
                    g[r][c] = fg
        return g
    if name == "only_small":
        cells = [(r, c) for r in range(1, h - 1, 3) for c in range(1, w - 1, 3)]
        rng.shuffle(cells)
        for r, c in cells[:6]:
            g[r][c] = fg
        return g
    if name == "touching_objects":
        for r in range(1, 4):
            for c in range(1, 4):
                if rng.random() < 0.6:
                    g[r][c] = fg
        return g
    return g
