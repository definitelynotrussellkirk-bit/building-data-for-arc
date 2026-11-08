"""Generator for arc_additional_puzzle_bank_volume16:E107 — connect
1-endpoint pairs with 2.

Rule: per ROW: exactly two 1s with only 0s strictly between -> fill
the span with 2. Per COLUMN: the same. Both passes read the ORIGINAL
grid, so a row span and a column span crossing at an empty cell BOTH
fill. Three 1s in a line, or any non-zero blocker between, kill that
line's fill.

Combinatorial axes: grid_h/w, n_pairs, texture
(plain|cross|blocked|three_ones|adjacent).
Degenerates: no_endpoints (blank), singles (no line has two 1s).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a61fb123081"
VERSION = "2.0.1"
TASK_ID = "0a61fb123081"
SUMMARY = (
    "Rows AND columns with exactly two 1s and a clear gap fill with "
    "2. Vertical pairs and row+column CROSSING spans now appear (was: "
    "row pairs only with column reuse banned, so the rule's whole "
    "column pass was dead). blocked boards put a decoy-colored cell "
    "inside a span (no fill); three_ones lines don't fill; adjacent "
    "pairs have nothing between. Decoy colors scatter like the "
    "train's 7s."
)

# Rivals: 'connect horizontal pairs only' refuted by vertical pairs.
# 'fill any span between 1s' refuted by blocked + three_ones. 'spans
# avoid each other' refuted by cross boards (both fill through the
# intersection). 3-4 demos incl. >=1 vertical pair.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    ">=1 row pair and >=1 column pair across the task's boards",
    "blocked boards: a non-zero non-1 cell strictly inside a span",
    "cross boards: a row span and column span sharing an empty cell",
]

DEGENERATE_TEXTURES = ("no_endpoints", "singles")
HELPFUL_TEXTURES = ("plain", "cross", "blocked", "three_ones", "adjacent")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 7..13", "valid": "5..18"},
    "grid_w":  {"type": "int", "default": "rng 8..14", "valid": "5..20"},
    "n_pairs": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|cross|blocked|three_ones|adjacent|"
                         "no_endpoints|singles",
                "doc": "cross: row+column spans share an empty cell, "
                       "both fill; blocked: decoy cell inside a span "
                       "kills it; three_ones: 3 in a line, no fill."},
}

_DECOYS = (3, 4, 5, 6, 7, 8, 9)


def _mirror(g):
    h, w = len(g), len(g[0])
    out = [row[:] for row in g]
    for r in range(h):
        ones = [c for c in range(w) if g[r][c] == 1]
        if len(ones) == 2 and all(g[r][c] == 0
                                  for c in range(ones[0] + 1, ones[1])):
            for c in range(ones[0] + 1, ones[1]):
                out[r][c] = 2
    for c in range(w):
        ones = [r for r in range(h) if g[r][c] == 1]
        if len(ones) == 2 and all(g[r][c] == 0
                                  for r in range(ones[0] + 1, ones[1])):
            for r in range(ones[0] + 1, ones[1]):
                out[r][c] = 2
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "cross",
                                              "blocked", "three_ones",
                                              "adjacent"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        n_pairs = ctx.draw_int("n_pairs", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
        n_pairs = ctx.draw_int("n_pairs", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 13)
        w = ctx.draw_int("grid_w", 8, 14)
        n_pairs = ctx.draw_int("n_pairs", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    def place_row_pair(r=None, gap=(2, None), block=None):
        for _t in range(120):
            rr = r if r is not None else rng.randint(0, h - 1)
            if any(g[rr][c] == 1 for c in range(w)):
                continue
            hi = gap[1] or (w - 1)
            c1 = rng.randint(0, w - 1 - gap[0] - 1)
            c2 = rng.randint(c1 + gap[0] + 1, min(w - 1, c1 + hi))
            if any(g[rr][c] != 0 for c in (c1, c2)):
                continue
            span = list(range(c1 + 1, c2))
            if any(g[rr][c] != 0 for c in span):
                continue
            g[rr][c1] = g[rr][c2] = 1
            if block and span:
                g[rr][rng.choice(span)] = block
            return rr, c1, c2
        return None

    def place_col_pair(c=None, gap=(2, None), block=None):
        for _t in range(120):
            cc = c if c is not None else rng.randint(0, w - 1)
            if any(g[r][cc] == 1 for r in range(h)):
                continue
            hi = gap[1] or (h - 1)
            r1 = rng.randint(0, h - 1 - gap[0] - 1)
            r2 = rng.randint(r1 + gap[0] + 1, min(h - 1, r1 + hi))
            if any(g[r][cc] != 0 for r in (r1, r2)):
                continue
            span = list(range(r1 + 1, r2))
            if any(g[r][cc] != 0 for r in span):
                continue
            g[r1][cc] = g[r2][cc] = 1
            if block and span:
                g[rng.choice(span)][cc] = block
            return cc, r1, r2
        return None

    if texture == "cross":
        # column span through the middle of a row span's gap
        rp = place_row_pair(r=rng.randint(2, h - 3), gap=(3, None))
        if rp:
            rr, c1, c2 = rp
            cc = rng.randint(c1 + 1, c2 - 1)
            # column pair straddling row rr at column cc
            for _t in range(80):
                r1 = rng.randint(0, rr - 1)
                r2 = rng.randint(rr + 1, h - 1)
                if g[r1][cc] == 0 and g[r2][cc] == 0 and \
                        all(g[r][cc] == 0 for r in range(r1 + 1, r2)):
                    g[r1][cc] = g[r2][cc] = 1
                    break
        n_pairs = max(0, n_pairs - 2)
    elif texture == "blocked":
        place_row_pair(block=rng.choice(_DECOYS)) if rng.random() < 0.5 \
            else place_col_pair(block=rng.choice(_DECOYS))
        n_pairs = max(1, n_pairs - 1)
    elif texture == "three_ones":
        for _t in range(120):
            r = rng.randint(0, h - 1)
            cs = sorted(rng.sample(range(w), 3))
            if all(g[r][c] == 0 for c in range(cs[0], cs[2] + 1)):
                for c in cs:
                    g[r][c] = 1
                break
        n_pairs = max(1, n_pairs - 1)
    elif texture == "adjacent":
        for _t in range(120):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 2)
            if g[r][c] == 0 and g[r][c + 1] == 0:
                g[r][c] = g[r][c + 1] = 1
                break
        n_pairs = max(1, n_pairs - 1)

    for _ in range(n_pairs):
        if rng.random() < 0.5:
            place_row_pair()
        else:
            place_col_pair()
    # decoy color cells (like the train's 7s) clear of 1-lines
    dcol = rng.choice(_DECOYS)
    for _ in range(rng.randint(0, 3)):
        for _t in range(60):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] != 0:
                continue
            g[r][c] = dcol
            if _mirror(g) == g and texture not in ("blocked", "three_ones",
                                                   "adjacent"):
                g[r][c] = 0  # decoy killed every span; undo
                continue
            break
    if _mirror(g) == g and texture not in ("blocked", "three_ones",
                                           "adjacent"):
        place_row_pair()
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=2 color-1 cells exist (at least some endpoints are present;
    adjacent/blocked/three_ones boards may produce identity output by design
    but still need 1-markers for training contrast)."""
    msgs = []
    h, w = len(grid), len(grid[0])
    ones = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if ones < 2:
        msgs.append(f"expected >=2 color-1 endpoint cells, found {ones}")
    return msgs


def _draw_from_degenerate(name, ctx):
    """no_endpoints — blank: identity. singles — scattered 1s, no row
    or column holds two: identity. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 11)
    w = ctx.draw_int("grid_w", 8, 12)
    g = full_grid(h, w, 0)
    if name == "no_endpoints":
        return g
    rows = rng.sample(range(h), min(3, h))
    cols = rng.sample(range(w), min(3, w))
    for r, c in zip(rows, cols):
        g[r][c] = 1
    return g
