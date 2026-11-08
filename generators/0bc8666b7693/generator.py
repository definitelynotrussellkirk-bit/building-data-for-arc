"""Generator for 7d18a6fb — legend quadrant shape lookup.

Rule: the color-1 object with an exactly 7x7 bbox is the legend; the
colors at its inner offsets (+1,+1),(+1,+5),(+5,+1),(+5,+5) name the
four quadrants. Output 7x7 with a zero cross: each 3x3 quadrant holds
that color's outside-the-legend shape, normalized to its bbox min and
sampled over the TOP-LEFT 3x3 WINDOW (bigger shapes truncate). No
7x7 legend or a named color with no outside cells CRASHES — never
generated.

Combinatorial axes: grid_h/w, legend position/style, shapes, texture
(plain|big_shape|dup_color|decoy_one).
Degenerates: none survivable (documented).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0bc8666b7693"
VERSION = "3.0.2"  # strengthen executable legend/name-shape invariants
TASK_ID = "0bc8666b7693"
SUMMARY = (
    "7x7 legend names 4 quadrant colors; each quadrant copies the "
    "matching outside shape (normalized, top-left 3x3 window). "
    "Legend position free, legend body solid-1 like the original "
    "task (was: hollow outline at a fixed corner with shapes at 4 "
    "fixed origins). big_shape boards use a 4x4 shape that TRUNCATES "
    "to its top-left window; dup_color boards repeat a color in two "
    "corners (same shape twice); decoy_one boards add a small "
    "1-object that is NOT 7x7 (skipped by the legend search)."
)

# Rivals: 'first 1-object is the legend' refuted by decoy_one.
# 'shapes copied whole' refuted by big_shape truncation. 'corner
# colors distinct' refuted by dup_color. 3-4 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly one 1-object with a 7x7 bbox",
    "every named corner color has >=1 cell outside the legend box",
    "shape colors exclude 0 and 1",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ("plain", "big_shape", "dup_color", "decoy_one")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 15..18", "valid": "14..22"},
    "grid_w":  {"type": "int", "default": "rng 15..18", "valid": "14..22"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|big_shape|dup_color|decoy_one",
                "doc": "big_shape: 4x4 shape truncates to its top-left "
                       "3x3; dup_color: repeated corner color; "
                       "decoy_one: non-7x7 1-object skipped."},
}

_COLORS = (2, 3, 4, 5, 6, 7, 8, 9)


def _grow3(rng, k, size=3):
    cells = [(rng.randrange(size), rng.randrange(size))]
    seen = set(cells)
    for _ in range(200):
        if len(cells) >= k:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen or not (0 <= p[0] < size and 0 <= p[1] < size):
            continue
        cells.append(p)
        seen.add(p)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _mirror(g):
    h, w = len(g), len(g[0])
    seen = set()
    legend = None
    for r in range(h):
        for c in range(w):
            if g[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w \
                            and (nr, nc) not in seen and g[nr][nc] == 1:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(rr for rr, _ in cells)
            r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells)
            c2 = max(cc for _, cc in cells)
            if r2 - r1 == 6 and c2 - c1 == 6 and legend is None:
                legend = (r1, c1)
    if legend is None:
        return None
    lr, lc = legend
    corner = {
        (0, 0): g[lr + 1][lc + 1], (0, 1): g[lr + 1][lc + 5],
        (1, 0): g[lr + 5][lc + 1], (1, 1): g[lr + 5][lc + 5],
    }

    def norm_window(color):
        cells = [(r, c) for r in range(h) for c in range(w)
                 if g[r][c] == color and
                 not (lr <= r <= lr + 6 and lc <= c <= lc + 6)]
        if not cells:
            return None
        r1 = min(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        s = set(cells)
        return lambda rr, cc: color if (r1 + rr, c1 + cc) in s else 0

    wins = {}
    for q, color in corner.items():
        wins[q] = norm_window(color)
        if wins[q] is None:
            return None
    out = [[0] * 7 for _ in range(7)]
    for r in range(7):
        for c in range(7):
            if r == 3 or c == 3:
                continue
            qr, rr = (0, r) if r <= 2 else (1, r - 4)
            qc, cc = (0, c) if c <= 2 else (1, c - 4)
            out[r][c] = wins[(qr, qc)](rr, cc)
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "big_shape",
                                              "dup_color", "decoy_one"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 15, 16)
        w = ctx.draw_int("grid_w", 15, 16)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 17, 18)
        w = ctx.draw_int("grid_w", 17, 18)
    else:
        h = ctx.draw_int("grid_h", 15, 18)
        w = ctx.draw_int("grid_w", 15, 18)
    rng = ctx.draw_rng("layout")

    for _attempt in range(150):
        g = full_grid(h, w, 0)
        lr = rng.randint(0, h - 7)
        lc = rng.randint(0, w - 7)
        for r in range(lr, lr + 7):
            for c in range(lc, lc + 7):
                g[r][c] = 1
        if texture == "dup_color":
            base = rng.sample(_COLORS, 3)
            colors = [base[0], base[1], base[0], base[2]]
        else:
            colors = rng.sample(_COLORS, 4)
        for (dr, dc), color in zip(((1, 1), (1, 5), (5, 1), (5, 5)),
                                   colors):
            g[lr + dr][lc + dc] = color

        def place_shape(color, big=False):
            size = 4 if big else 3
            shape = _grow3(rng, rng.randint(4, 6) if not big
                           else rng.randint(7, 10), size)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            for _t in range(200):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                cells = [(r0 + r, c0 + c) for r, c in shape]
                if any(lr - 1 <= r <= lr + 7 and lc - 1 <= c <= lc + 7
                       for r, c in cells):
                    continue
                if all(g[r][c] == 0 and
                       all(g[ar][ac] == 0
                           for ar, ac in ((r-1, c), (r+1, c),
                                          (r, c-1), (r, c+1))
                           if 0 <= ar < h and 0 <= ac < w)
                       for r, c in cells):
                    for r, c in cells:
                        g[r][c] = color
                    return True
            return False

        ok = True
        done = set()
        for i, color in enumerate(colors):
            if color in done:
                continue
            done.add(color)
            big = texture == "big_shape" and i == 0
            if not place_shape(color, big=big):
                ok = False
                break
        if not ok:
            continue
        if texture == "decoy_one":
            # small 1-object, NOT 7x7 bbox
            if not place_shape(1):
                continue
        out = _mirror(g)
        if out is None:
            continue
        return g
    raise ValueError("could not realize legend-lookup board")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly one color-1 object with a 7x7 bbox, and every color named by
    the legend corners has at least one outside-the-legend shape cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    legends = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != 1 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == 1:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
            if r2 - r1 + 1 == 7 and c2 - c1 + 1 == 7:
                legends.append((r1, c1, r2, c2))
    errors = []
    if len(legends) != 1:
        errors.append(f"expected exactly one color-1 object with a 7x7 bbox, found {len(legends)}")
        return errors
    lr, lc, _, _ = legends[0]
    corner_colors = [grid[lr + 1][lc + 1], grid[lr + 1][lc + 5],
                     grid[lr + 5][lc + 1], grid[lr + 5][lc + 5]]
    if any(v in (0, 1) for v in corner_colors):
        errors.append(f"legend corner colors must be non-zero and not 1, got {corner_colors}")
    for color in set(corner_colors):
        outside = [(r, c) for r in range(h) for c in range(w)
                   if grid[r][c] == color and not (lr <= r <= lr + 6 and lc <= c <= lc + 6)]
        if not outside:
            errors.append(f"legend names color {color}, but no outside shape cells have that color")
    if _mirror(grid) is None:
        errors.append("mirror rule could not build the 7x7 output")
    return errors
