"""Generator for ARC task 12eac192.

Rule: `(rule! (lambda (g) (paint-objects-by g (objects g 0) (lambda (obj) (if (>= (obj-size obj) 3) #f 3)))))`.
For each non-bg 4-connected object: if size ≥ 3 → keep; if size < 3
(i.e., 1 or 2 cells) → recolor to 3.

Combinatorial axes:
  * grid_h / grid_w        — outer canvas size
  * fg_color               — color of large objects (≠ 0, ≠ 3)
  * n_large_objects        — number of size-≥3 objects
  * n_small_objects        — number of size-1 or size-2 objects (rule
                             will recolor these)
  * large_kind             — shape of large objects: rect / L / cross /
                             blob / line
  * small_kind             — shape of small objects: single / pair_h /
                             pair_v / pair_diag
  * placement              — random / corners / row / column
  * caller-opt-in degenerates: only_large (rule no-op),
                               only_small (output all 3),
                               touching_objects
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b1118feaedd5"
# 2.1.0: when every small-object placement collided, the grid held only size>=3
# objects -> the recolor-small-to-3 rule changed nothing -> output == input
# (identity). Now retry until >=1 small AND >=1 large object are placed, with a
# guaranteed fallback. Adds self_check.
VERSION = "2.1.0"
TASK_ID = "b1118feaedd5"
SUMMARY = (
    "0-bg grid (h, w~7-16) with: (a) 1-3 LARGE "
    "OBJECTS (size ≥ 3 cells) in some non-{0, 3} "
    "fg_color, shaped as rect / L / cross / "
    "random_blob / line_h / line_v; (b) 2-5 "
    "SMALL OBJECTS (size 1 or 2 cells) in the "
    "SAME fg_color — singletons or pairs "
    "(pair_h / pair_v / pair_diag). Large and "
    "small objects are 4-conn isolated with "
    "1-cell padding. Rule: for EVERY 4-CONN "
    "OBJECT, compute its CELL COUNT. If size < "
    "3 (singletons or pairs), RECOLOR every "
    "cell of that object to COLOR 3 (green). "
    "If size ≥ 3 (large), KEEP fg_color "
    "unchanged. Net: small objects turn green; "
    "large objects stay."
)

INVARIANTS = [
    "background is zero",
    "foreground objects are 4-disconnected",
    "≥1 small object (size 1 or 2) so rule has visible effect",
    "≥1 large object (size ≥3) so rule preserves something",
]

LARGE_KINDS = ("rect", "L_shape", "cross", "random_blob", "line_h", "line_v")
SMALL_KINDS = ("single", "pair_h", "pair_v", "pair_diag")
PLACEMENTS = ("random", "corners", "row", "column")
DEGENERATE_TEXTURES = ("only_large", "only_small", "touching_objects")
HELPFUL_TEXTURES = LARGE_KINDS

AXES = {
    "grid_h":          {"type": "int", "default": "rng 7..16", "valid": "5..22"},
    "grid_w":          {"type": "int", "default": "rng 7..16", "valid": "5..22"},
    "fg_color":        {"type": "color", "default": "rng (≠0,3)", "valid": "1..9 (≠3)"},
    "n_large_objects": {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_small_objects": {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "large_kind":      {"type": "str", "default": "rng helpful",
                        "valid": "|".join(LARGE_KINDS)},
    "small_kind":      {"type": "str", "default": "rng helpful",
                        "valid": "|".join(SMALL_KINDS)},
    "placement":       {"type": "str", "default": "rng random|corners|row|column",
                        "valid": "|".join(PLACEMENTS)},
    "texture":         {"type": "str", "default": "alias for large_kind",
                        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
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
    fg = int(overrides.get("fg_color", ctx.draw_color("fg_color", exclude={0, 3})))
    n_large = int(overrides.get("n_large_objects",
                                ctx.draw_int("n_large_objects", l_lo, l_hi)))
    n_small = int(overrides.get("n_small_objects",
                                ctx.draw_int("n_small_objects", s_lo, s_hi)))
    large_kind = (overrides.get("texture")
                  or overrides.get("large_kind")
                  or ctx.draw_choice("large_kind", list(LARGE_KINDS)))
    small_kind = overrides.get("small_kind",
                               ctx.draw_choice("small_kind", list(SMALL_KINDS)))

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        occupied: set[tuple[int, int]] = set()
        n_placed_large = 0
        for _ in range(n_large):
            for _try in range(20):
                sh = rng.randint(2, max(2, h // 4))
                sw = rng.randint(2, max(2, w // 4))
                rr = rng.randint(0, h - sh - 1)
                rc = rng.randint(0, w - sw - 1)
                if not _check_clear(g, rr, rc, sh, sw):
                    continue
                cells = _large_cells(large_kind, sh, sw)
                if len(cells) < 3:
                    cells.append((sh - 1, sw - 1))
                    cells.append((0, sw - 1))
                    cells = list(set(cells))
                for dr, dc in cells:
                    g[rr + dr][rc + dc] = fg
                    occupied.add((rr + dr, rc + dc))
                n_placed_large += 1
                break

        n_placed_small = 0
        for _ in range(n_small):
            for _try in range(20):
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
                n_placed_small += 1
                break

        # need >=1 small (rule has visible effect) AND >=1 large (rule preserves)
        if n_placed_small >= 1 and n_placed_large >= 1:
            return g

    # deterministic fallback: one 1x3 large bar + one singleton, well separated
    g = full_grid(h, w, 0)
    for dc in range(3):
        g[1][1 + dc] = fg
    g[h - 2][w - 2] = fg
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least one object of size <3 (recolored to 3 by the rule) and at least
    one of size >=3 (kept) — so the rule visibly changes the grid without erasing
    everything."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    sizes = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or seen[sr][sc]:
                continue
            col = grid[sr][sc]; stack = [(sr, sc)]; seen[sr][sc] = True; cnt = 0
            while stack:
                r, c = stack.pop(); cnt += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == col):
                        seen[nr][nc] = True; stack.append((nr, nc))
            sizes.append(cnt)
    errors = []
    if not any(s < 3 for s in sizes):
        errors.append("no small object (size<3) — recolor rule has no effect "
                      "(output == input)")
    if not any(s >= 3 for s in sizes):
        errors.append("no large object (size>=3) preserved")
    return errors


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
    if kind == "random_blob":
        # the (dr+dc)%2 checkerboard is 4-DISCONNECTED (each cell a separate
        # singleton -> no real large object). Use a connected rect-with-a-notch.
        return [(dr, dc) for dr in range(sh) for dc in range(sw)
                if not (dr == 0 and dc == sw - 1)]
    if kind == "line_h":
        return [(0, dc) for dc in range(max(3, sw))]
    if kind == "line_v":
        return [(dr, 0) for dr in range(max(3, sh))]
    return [(0, 0), (1, 0), (0, 1)]


def _small_cells(kind, rng):
    if kind == "single":
        return [(0, 0)]
    if kind == "pair_h":
        return [(0, 0), (0, 1)]
    if kind == "pair_v":
        return [(0, 0), (1, 0)]
    if kind == "pair_diag":
        return [(0, 0), (1, 1)]
    return [(0, 0)]


def _draw_from_degenerate(name, h, w, ctx, rng):
    fg = ctx.draw_color("fg_color", exclude={0, 3})
    g = full_grid(h, w, 0)
    if name == "only_large":
        # Several large rects only, no small objects.
        for i, (rr, rc) in enumerate([(1, 1), (1, w - 5), (h - 5, 1)]):
            for r in range(rr, rr + 3):
                for c in range(rc, rc + 3):
                    g[r][c] = fg
        return g
    if name == "only_small":
        # Many size-1 or size-2 objects.
        cells = [(r, c) for r in range(1, h - 1, 3) for c in range(1, w - 1, 3)]
        rng.shuffle(cells)
        for r, c in cells[:8]:
            g[r][c] = fg
        return g
    if name == "touching_objects":
        # Two clusters that visually look small-ish but 4-conn merges them
        # into a large object.
        for r in range(1, 4):
            for c in range(1, 4):
                if rng.random() < 0.6:
                    g[r][c] = fg
        return g
    return g
