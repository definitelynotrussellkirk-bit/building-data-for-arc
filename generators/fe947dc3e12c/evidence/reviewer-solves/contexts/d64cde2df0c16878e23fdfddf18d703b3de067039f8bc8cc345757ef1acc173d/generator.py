"""Generator for ea32f347.

Rule: take all color-5 blobs, sort by size descending, recolor largest → 1,
2nd → 4, 3rd → 2.

Canonical scene: 10x10 grids with exactly three straight-bar color-5 blobs
(horizontal or vertical) of strictly distinct sizes (2..7), separated so
they stay three 4-connected components. The rule indexes a length-3 color
list by rank, so a 4th object or tied sizes would break it.

Combinatorial axes (6): grid_h/w, n_blobs (rule-locked 3), size_profile,
orientation, palette_mode, texture. Degenerates: single_blob,
equal_size_blobs, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fe947dc3e12c"
VERSION = "4.0.0"
TASK_ID = "fe947dc3e12c"
RULE_HASH = "0ef10b0042c4"
SUMMARY = (
    "0-bg grid (10x10 canonical) with exactly 3 straight-bar color-5 blobs "
    "of strictly distinct sizes; the rule recolors them by size rank "
    "1/4/2. Generalized draws vary shapes and colors (the rule is "
    "color-blind on source)."
)

INVARIANTS = [
    "background is 0",
    "exactly 3 connected non-bg components (a 4th breaks the rule)",
    "all 3 sizes strictly distinct (rank unambiguous)",
    "blobs separated by >=1-cell buffer (4-conn separation)",
]

ORIENTATIONS = ("horizontal", "vertical", "mixed")
PALETTE_MODES = ("canonical", "varied")
DEGENERATE_TEXTURES = ("single_blob", "equal_size_blobs", "no_blobs")

AXES = {
    "grid_h":       {"type": "int", "default": "band rng 9..14",
                     "valid": "7..20"},
    "grid_w":       {"type": "int", "default": "band rng 9..16",
                     "valid": "9..22"},
    "orientation":  {"type": "str", "default": "rng helpful",
                     "valid": "|".join(ORIENTATIONS)},
    "palette_mode": {"type": "str", "default": "rng 0.7 canonical / 0.3 varied",
                     "valid": "|".join(PALETTE_MODES)},
    "texture":      {"type": "str", "default": "alias for orientation",
                     "valid": "|".join(ORIENTATIONS + DEGENERATE_TEXTURES)},
}

# Official size tuples (sorted desc), all on 10x10 with color-5 bars.
_CANONICAL_FORMS = (
    (6, 5, 3), (6, 4, 2), (7, 5, 4),
)


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            stack, cells = [(r, c)], set()
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] != 0):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            out.append(cells)
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance (all canonical pairs
    satisfy them): rectangular grid inside the declared 7..20 x 9..22
    envelope, background 0; exactly 3 non-bg 4-connected components on the
    normal path (single_blob/no_blobs are declared degenerates), all
    strictly distinct sizes. equal_size_blobs (3 same-size blobs) is the
    declared ambiguity degenerate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not 0 <= v <= 9 for row in grid for v in row):
        errs.append("color outside 0..9")
        return errs
    if not (7 <= h <= 20 and 9 <= w <= 22):
        errs.append(f"dims {h}x{w} outside the declared 7..20 x 9..22 envelope")
        return errs
    comps = _components(grid)
    if not comps:
        return errs  # no_blobs degenerate (declared)
    sizes = sorted((len(c) for c in comps), reverse=True)
    if len(comps) == 1:
        return errs  # single_blob degenerate (declared)
    if len(comps) != 3:
        errs.append(f"{len(comps)} components (the rule indexes exactly 3)")
        return errs
    if len(set(sizes)) != 3:
        return errs  # equal_size_blobs degenerate (declared, rule-ambiguous)
    return errs


def observe_overrides(grid):
    """Realized exact-axis values (KRF-0002): the three blob sizes,
    sorted descending."""
    comps = _components(grid)
    sizes = sorted((len(c) for c in comps), reverse=True)
    while len(sizes) < 3:
        sizes.append(0)
    return {"size_1": sizes[0], "size_2": sizes[1], "size_3": sizes[2]}


def _place_bars(rng, h, w, sizes, colors, orientation):
    """Place straight bars of the given sizes/colors with >=1-cell buffer."""
    g = full_grid(h, w, 0)
    used = set()
    for size, col in zip(sizes, colors):
        placed = False
        for _try in range(300):
            horiz = (orientation == "horizontal" or
                     (orientation == "mixed" and rng.random() < 0.5))
            if horiz:
                if size > w:
                    continue
                r = rng.randrange(h)
                c = rng.randrange(w - size + 1)
                cells = [(r, c + i) for i in range(size)]
            else:
                if size > h:
                    continue
                r = rng.randrange(h - size + 1)
                c = rng.randrange(w)
                cells = [(r + i, c) for i in range(size)]
            if any((rr, cc) in used or
                   any((rr + dr, cc + dc) in used
                       for dr in (-1, 0, 1) for dc in (-1, 0, 1))
                   for rr, cc in cells):
                continue
            for rr, cc in cells:
                g[rr][cc] = col
            used |= set(cells)
            placed = True
            break
        if not placed:
            return None
    return g


def _place_shapes(rng, h, w, sizes, colors):
    """Generalized path: random 4-connected polyominoes, exact sizes."""
    g = full_grid(h, w, 0)
    used = set()
    for size, col in zip(sizes, colors):
        placed = False
        for _try in range(200):
            cells = {(rng.randrange(h), rng.randrange(w))}
            while len(cells) < size:
                r, c = list(cells)[rng.randrange(len(cells))]
                dr, dc = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
                nxt = (r + dr, c + dc)
                if 0 <= nxt[0] < h and 0 <= nxt[1] < w:
                    cells.add(nxt)
            if any((rr, cc) in used or
                   any((rr + dr, cc + dc) in used
                       for dr in (-1, 0, 1) for dc in (-1, 0, 1))
                   for rr, cc in cells):
                continue
            for rr, cc in cells:
                g[rr][cc] = col
            used |= set(cells)
            placed = True
            break
        if not placed:
            return None
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    tex = overrides.get("texture")
    if tex in DEGENERATE_TEXTURES:
        extra = sorted(k for k, v in overrides.items()
                       if k != "texture" and v is not None)
        if extra:
            raise ValueError(
                f"degenerate texture {tex!r} is a fixed diagnostic layout; "
                f"it takes no other overrides, got {extra}")
        rng = ctx.draw_rng("layout")
        return _draw_from_degenerate(tex, rng)
    if tex is not None and tex not in ORIENTATIONS:
        raise ValueError(f"unknown texture {tex!r}; valid: "
                         f"{ORIENTATIONS + DEGENERATE_TEXTURES}")
    if tex in ORIENTATIONS and overrides.get("orientation") is not None \
            and overrides["orientation"] != tex:
        raise ValueError(
            f"texture={tex!r} is itself an orientation alias and "
            f"orientation={overrides['orientation']!r} disagrees; drop one")
    rng = ctx.draw_rng("layout")

    # Canonical-form prior (KRF-0003): ~30% of fully-unoverridden draws pin
    # the 10x10 color-5 bar scene with one official size tuple.
    if not any(k in overrides for k in ("grid_h", "grid_w", "orientation",
                                        "palette_mode", "texture")):
        if ctx.draw_rng("canonical_prior").random() < 0.30:
            sizes = ctx.draw_choice("canonical_form", list(_CANONICAL_FORMS))
            for label, value in (("grid_h", 10), ("grid_w", 10),
                                 ("size_1", sizes[0]), ("size_2", sizes[1]),
                                 ("size_3", sizes[2])):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)
            g = _place_bars(rng, 10, 10, sizes, (5, 5, 5), "mixed")
            if g is not None:
                return g
            raise ValueError("canonical 10x10 bar scene did not fit")

    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, s_lo, s_hi = 9, 11, 9, 11, 2, 6
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, s_lo, s_hi = 11, 14, 12, 16, 3, 9
    else:
        h_lo, h_hi, w_lo, w_hi, s_lo, s_hi = 9, 12, 10, 14, 2, 7
    h = ctx.draw_int("grid_h", *( (7, 20) if overrides.get("grid_h") is not None
                                  else (h_lo, h_hi)))
    w = ctx.draw_int("grid_w", *( (9, 22) if overrides.get("grid_w") is not None
                                  else (w_lo, w_hi)))
    orientation = (tex or overrides.get("orientation")
                   or ctx.draw_choice("orientation", list(ORIENTATIONS)))
    if overrides.get("palette_mode") is not None:
        palette_mode = overrides["palette_mode"]
    elif tex in ORIENTATIONS or overrides.get("orientation") is not None:
        palette_mode = "canonical"   # explicit orientation implies the bar form
    else:
        palette_mode = "canonical" if rng.random() < 0.7 else "varied"
    if palette_mode not in PALETTE_MODES:
        raise ValueError(f"unknown palette_mode {palette_mode!r}")
    if palette_mode == "varied" and (tex in ORIENTATIONS
                                     or overrides.get("orientation") is not None):
        raise ValueError(
            "orientation constrains the canonical bar form only; "
            "palette_mode='varied' (polyomino shapes) is incompatible with "
            f"an explicit orientation ({tex or overrides.get('orientation')!r})")
    # Three strictly distinct sizes, feasible on the drawn canvas FOR THE
    # DRAWN ORIENTATION (a vertical bar of size > h can never fit).
    hi_cap = (min(s_hi, w) if orientation == "horizontal"
              else min(s_hi, h) if orientation == "vertical"
              else min(s_hi, max(h, w)))
    pool = sorted(rng.sample(range(s_lo, hi_cap + 1), 3), reverse=True)
    ctx.overrides["size_1"] = pool[0]
    ctx.draw_int("size_1", pool[0], pool[0])
    ctx.overrides["size_2"] = pool[1]
    ctx.draw_int("size_2", pool[1], pool[1])
    ctx.overrides["size_3"] = pool[2]
    ctx.draw_int("size_3", pool[2], pool[2])
    if palette_mode == "canonical":
        colors = (5, 5, 5)
    else:
        colors = tuple(rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3))
        if list(colors) == [1, 4, 2]:
            colors = (5, 5, 5)  # never an all-identity scene
    g = (_place_bars(rng, h, w, pool, colors, orientation)
         if palette_mode == "canonical"
         else _place_shapes(rng, h, w, pool, colors))
    if g is None:
        raise ValueError(
            f"cannot place 3 strictly-distinct blobs {pool} on {h}x{w} "
            "(infeasible combination)")
    errs = self_check(g)
    if errs:
        raise ValueError(f"internal layout violated self_check: {errs}")
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "single_blob":
        for c in range(5):
            g[5][c + 2] = 5
        return g
    if name == "equal_size_blobs":
        g[2][2] = g[2][3] = 5
        g[5][5] = g[5][6] = 5
        g[7][3] = g[7][4] = 5
        return g
    if name == "no_blobs":
        return g
    return g
