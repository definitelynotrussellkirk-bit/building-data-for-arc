"""Generator for arc_additional_puzzles_21_set11_bundle:H76 — chamber fill.

Rule: color 9 is the wall. For each 4-connected open region, if its
non-zero palette is EXACTLY ONE color, every 0-cell fills with it;
markers always survive; multi-color or empty regions keep their zeros.

Combinatorial axes: grid bands (2-3 per axis), texture
(plain|gap_wall).
Degenerates: no_walls (one region, several colors, identity),
empty_grid_chambers (walls only, identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "085049d55da0"
VERSION = "3.1.0"  # FIX: require both fill and stay evidence after gap-wall merges
TASK_ID = "085049d55da0"

SUMMARY = (
    "9-walls carve a varied 2x2..3x3 chamber lattice; chambers hold a "
    "single marker / a same-color PAIR (still fills - dedup) / two "
    "colors (stays) / nothing (stays). gap_wall merges two chambers "
    "through a punched divider. Marker colors may repeat across "
    "chambers. (Was: always 2x2 chambers, one distinct marker each - "
    "the dedup, multi-color, and merge behaviors were unreachable.)"
)

# Rivals: 'fill chambers with exactly one MARKER' refuted by same-
# color pairs that still fill. 'fill everything' refuted by empty and
# two-color chambers. 'chambers are rectangles' refuted by gap_wall.
# 'colors unique per board' refuted by repeats. 3 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "9-walls partition the grid into >=4 rectangular chambers (plus outer frame)",
    ">=1 chamber fills and >=1 stays per main-path board",
    "markers never use colors 0 or 9",
]

DEGENERATE_TEXTURES = ("no_walls", "empty_grid_chambers")
HELPFUL_TEXTURES = ("plain", "gap_wall")

AXES = {
    "n_bands": {"type": "int", "default": "rng 2..3 per axis", "valid": "2..3"},
    "ch_size": {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|gap_wall|no_walls|empty_grid_chambers",
                "doc": "gap_wall: a divider cell punched out merges two "
                       "chambers into one non-rectangular region."},
}

_MARKERS = (1, 2, 3, 4, 5, 6, 7, 8)


def _mirror(g):
    h, w = len(g), len(g[0])
    out = [[9 if g[r][c] == 9 else 0 for c in range(w)] for r in range(h)]
    seen = [[False] * w for _ in range(h)]
    for r0 in range(h):
        for c0 in range(w):
            if g[r0][c0] == 9 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            region = []
            while stack:
                r, c = stack.pop()
                region.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and not seen[rr][cc] \
                            and g[rr][cc] != 9:
                        seen[rr][cc] = True
                        stack.append((rr, cc))
            colors = {g[r][c] for r, c in region if g[r][c] != 0}
            for r, c in region:
                if g[r][c] != 0:
                    out[r][c] = g[r][c]
                elif len(colors) == 1:
                    out[r][c] = next(iter(colors))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain",
                                              "gap_wall"))
    if difficulty == "easy":
        nr = nc = 2
        cs_lo, cs_hi = 3, 4
    elif difficulty == "hard":
        nr = ctx.draw_int("n_bands_r", 2, 3)
        nc = ctx.draw_int("n_bands_c", 2, 3)
        cs_lo, cs_hi = 3, 5
    else:
        nr = ctx.draw_int("n_bands_r", 2, 3)
        nc = ctx.draw_int("n_bands_c", 2, 3)
        cs_lo, cs_hi = 2, 4
    rng = ctx.draw_rng("layout")

    for _attempt in range(60):
        row_sizes = [rng.randint(cs_lo, cs_hi) for _ in range(nr)]
        col_sizes = [rng.randint(cs_lo, cs_hi) for _ in range(nc)]
        h = sum(row_sizes) + nr + 1
        w = sum(col_sizes) + nc + 1
        if h > 24 or w > 24:
            continue
        g = full_grid(h, w, 9)
        comps = []
        r0 = 1
        for rs in row_sizes:
            c0 = 1
            for cs in col_sizes:
                for r in range(r0, r0 + rs):
                    for c in range(c0, c0 + cs):
                        g[r][c] = 0
                comps.append((r0, c0, r0 + rs - 1, c0 + cs - 1))
                c0 += cs + 1
            r0 += rs + 1

        kinds = [rng.choice(("single", "single", "single", "pair",
                             "empty", "two_color")) for _ in comps]
        if not any(k in ("single", "pair") for k in kinds):
            kinds[rng.randrange(len(kinds))] = "single"
        if not any(k in ("empty", "two_color") for k in kinds):
            kinds[rng.randrange(len(kinds))] = rng.choice(("empty", "two_color"))

        for (r1, c1, r2, c2), kind in zip(comps, kinds):
            spots = [(r, c) for r in range(r1, r2 + 1)
                     for c in range(c1, c2 + 1)]
            rng.shuffle(spots)
            if kind == "single":
                g[spots[0][0]][spots[0][1]] = rng.choice(_MARKERS)
            elif kind == "pair" and len(spots) >= 2:
                color = rng.choice(_MARKERS)  # same color twice: fills
                g[spots[0][0]][spots[0][1]] = color
                g[spots[1][0]][spots[1][1]] = color
            elif kind == "two_color" and len(spots) >= 2:
                a, b = rng.sample(_MARKERS, 2)
                g[spots[0][0]][spots[0][1]] = a
                g[spots[1][0]][spots[1][1]] = b

        if texture == "gap_wall" and nr >= 2:
            wall_r = 1 + row_sizes[0]
            c1 = 1
            ci = rng.randrange(nc)
            for k in range(ci):
                c1 += col_sizes[k] + 1
            g[wall_r][rng.randint(c1, c1 + col_sizes[ci] - 1)] = 0
        fill_count, stay_count = _fill_stay_counts(g)
        if fill_count < 1 or stay_count < 1:
            continue
        if _mirror(g) == g:
            continue
        return g
    raise ValueError("could not realize chamber board")


def _regions(g, wall=9):
    h, w = len(g), len(g[0])
    seen = set()
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if g[r0][c0] == wall or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != wall and (rr, cc) not in seen:
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            comps.append(comp)
    return comps


def _fill_stay_counts(g):
    fill = stay = 0
    for comp in _regions(g, 9):
        colors = {g[r][c] for r, c in comp if g[r][c] != 0}
        has_zero = any(g[r][c] == 0 for r, c in comp)
        if has_zero and len(colors) == 1:
            fill += 1
        if has_zero and len(colors) != 1:
            stay += 1
    return fill, stay


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid has non-ARC color")
    if not any(v == 9 for row in grid for v in row):
        errors.append("missing color-9 chamber walls")
    fill_count, stay_count = _fill_stay_counts(grid)
    if fill_count < 1 or stay_count < 1:
        errors.append(f"need at least one fillable and one staying chamber, got {(fill_count, stay_count)}")
    return sorted(set(errors))


def _draw_from_degenerate(name, ctx):
    """no_walls — markers on an open grid: ONE region, >=2 colors,
    identity. empty_grid_chambers — walls only: identity. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    if name == "no_walls":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        g = full_grid(h, w, 0)
        for color in rng.sample(_MARKERS, rng.randint(2, 4)):
            g[rng.randrange(h)][rng.randrange(w)] = color
        return g
    cs = ctx.draw_int("ch_size", 3, 4)
    h = w = 2 * cs + 3
    g = full_grid(h, w, 9)
    for rr, cc in ((1, 1), (1, cs + 2), (cs + 2, 1), (cs + 2, cs + 2)):
        for r in range(rr, rr + cs):
            for c in range(cc, cc + cs):
                g[r][c] = 0
    return g
