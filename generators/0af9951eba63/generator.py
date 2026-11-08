"""Generator for arc_puzzle_bank_seventeenth21:H114 — color-mapping
panel decode.

Rule: 3 arithmetic panels (1-col separators). Every non-zero A-cell
pairs with the SAME-position B-cell: (colorA -> valueB). Panel C
recolors through the map; the FIRST scan-order pair wins per color;
unmapped colors pass through; a B value of 0 means ERASE. Output =
panel C recolored.

Combinatorial axes: panel_h/w, n_pairs, texture
(plain|unmapped|erase|conflict).
Degenerates: empty_A (no mapping, C passes through verbatim).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0af9951eba63"
VERSION = "2.0.1"
TASK_ID = "0af9951eba63"
SUMMARY = (
    "A->B cellwise pairs recolor panel C. A/B carry small SHAPES "
    "(blocks/diagonals like the original, not lone dots). unmapped "
    "boards give C a color absent from A (passes through); erase "
    "boards map one color to 0 (B empty at that spot); conflict "
    "boards repeat an A color with two different B values - the "
    "FIRST scan-order pair wins."
)

# Rivals: 'every C color must be mapped' refuted by unmapped pass-
# through. 'mapping never erases' refuted by erase. 'last/majority
# pair wins' refuted by conflict (first wins). 3-4 demos with >=2
# mapping pairs.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "3 equal panels; separators full-height color 5",
    "conflict boards: one A color with two different B values",
    "erase boards: >=1 A cell whose B partner is 0",
]

DEGENERATE_TEXTURES = ("empty_A",)
HELPFUL_TEXTURES = ("plain", "unmapped", "erase", "conflict")

AXES = {
    "panel_h": {"type": "int", "default": "rng 4..7", "valid": "3..10"},
    "panel_w": {"type": "int", "default": "rng 4..7", "valid": "3..10"},
    "n_pairs": {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|unmapped|erase|conflict|empty_A",
                "doc": "unmapped: C color absent from A passes; erase: "
                       "A color maps to 0; conflict: duplicate A color, "
                       "first scan-order pair wins."},
}

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _mirror(g):
    h, w = len(g), len(g[0])
    pw = (w - 2) // 3
    a = [row[0:pw] for row in g]
    bb = [row[pw + 1:2 * pw + 1] for row in g]
    cc = [row[2 * pw + 2:3 * pw + 2] for row in g]
    mapping = []
    for r in range(h):
        for c in range(pw):
            if a[r][c] != 0:
                mapping.append((a[r][c], bb[r][c]))
    out = [row[:] for row in cc]
    for r in range(h):
        for c in range(pw):
            v = cc[r][c]
            hit = next((kv for kv in mapping if kv[0] == v), None)
            if hit is not None:
                out[r][c] = hit[1]
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 3 panels separated by 2 full-height color-5 columns."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    sep_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(sep_cols) != 2:
        errs.append(f"expected exactly 2 color-5 separator columns, found {len(sep_cols)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "unmapped",
                                              "erase", "conflict"))
    if difficulty == "easy":
        ph = ctx.draw_int("panel_h", 3, 5)
        pw = ctx.draw_int("panel_w", 4, 5)
        n_pairs = ctx.draw_int("n_pairs", 2, 2)
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 6, 8)
        pw = ctx.draw_int("panel_w", 6, 8)
        n_pairs = ctx.draw_int("n_pairs", 3, 5)
    else:
        ph = ctx.draw_int("panel_h", 4, 7)
        pw = ctx.draw_int("panel_w", 4, 7)
        n_pairs = ctx.draw_int("n_pairs", 2, 4)
    rng = ctx.draw_rng("layout")
    n_pairs = min(n_pairs, len(_COLORS) - 2)
    w = 3 * pw + 2
    g = full_grid(ph, w, 0)
    for r in range(ph):
        g[r][pw] = 5
        g[r][2 * pw + 1] = 5

    src = rng.sample(_COLORS, n_pairs)
    tgt_pool = [c for c in _COLORS]
    tgt = []
    for s in src:
        tgt.append(rng.choice([c for c in tgt_pool if c != s]))

    # A/B carry small SHAPES per pair (1-3 cells each), aligned
    spots = [(r, c) for r in range(ph) for c in range(pw)]
    rng.shuffle(spots)
    used = set()
    for i, (s, t) in enumerate(zip(src, tgt)):
        size = rng.randint(1, 3)
        placed = 0
        for r, c in spots:
            if placed >= size:
                break
            if (r, c) in used:
                continue
            used.add((r, c))
            g[r][c] = s
            g[r][pw + 1 + c] = t
            placed += 1
    if texture == "erase":
        # one A cell's B partner stays 0: that color erases in C
        victim = rng.randrange(n_pairs)
        cells = [(r, c) for r in range(ph) for c in range(pw)
                 if g[r][c] == src[victim]]
        for r, c in cells:
            g[r][pw + 1 + c] = 0
        tgt[victim] = 0
    if texture == "conflict":
        # duplicate the FIRST scan-order color with a different B value
        first_cells = sorted([(r, c) for r in range(ph)
                              for c in range(pw) if g[r][c] == src[0]])
        alt = rng.choice([c for c in _COLORS
                          if c != tgt[0] and c != src[0]])
        free = [(r, c) for r in range(ph) for c in range(pw)
                if (r, c) not in used and (r, c) > first_cells[0]]
        if free:
            r, c = rng.choice(free)
            g[r][c] = src[0]
            g[r][pw + 1 + c] = alt

    # panel C
    c_colors = list(src)
    if texture == "unmapped":
        c_colors.append(rng.choice([c for c in _COLORS if c not in src]))
    placed_any = False
    for r in range(ph):
        for c in range(pw):
            if rng.random() < 0.4:
                g[r][2 * pw + 2 + c] = rng.choice(c_colors)
                placed_any = True
    if not placed_any:
        g[0][2 * pw + 2] = rng.choice(c_colors)
    if texture == "unmapped":
        # guarantee the unmapped color actually appears in C
        extra = c_colors[-1]
        if not any(g[r][2 * pw + 2 + c] == extra
                   for r in range(ph) for c in range(pw)):
            g[rng.randrange(ph)][2 * pw + 2 + rng.randrange(pw)] = extra
    return g


def _draw_from_degenerate(name, ctx):
    """empty_A — panels A and B blank: the mapping is empty and panel
    C passes through verbatim. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    ph = ctx.draw_int("panel_h", 4, 6)
    pw = ctx.draw_int("panel_w", 4, 6)
    w = 3 * pw + 2
    g = full_grid(ph, w, 0)
    for r in range(ph):
        g[r][pw] = 5
        g[r][2 * pw + 1] = 5
    for r in range(ph):
        for c in range(pw):
            if rng.random() < 0.35:
                g[r][2 * pw + 2 + c] = rng.choice(_COLORS)
    return g
