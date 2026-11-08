"""Generator for arc_puzzle_bank_21_set12_bundle:easy_l06 — Plus → X transform.

Rule: every interior cell whose 4 cardinal neighbors share its color
paints an X (center + diagonals) on a blank canvas. Cardinal-only test;
non-matching content vanishes.

Combinatorial axes: grid_h, grid_w, n_plus, texture
(plain|solid_block|diag_decor|partial_plus).
Degenerates: no_plus_shapes, plus_at_corner (both -> BLANK output).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "072fa5d50e96"
VERSION = "2.0.1"  # add executable self_check for plus-to-X trigger boards
TASK_ID = "072fa5d50e96"
SUMMARY = (
    "Cells whose 4 cardinal neighbors share their color produce an X "
    "(center + 4 diagonals) on a BLANK canvas; everything else "
    "vanishes. The test is cardinal-only, so a solid 3x3 block also "
    "fires, and diagonal decor neither breaks a plus nor survives. "
    "(Was: perfect pluses only - the cardinal-only check, the vanish "
    "behavior, and same-color pairs were never exercised.)"
)

# Rivals: 'must be a plus' refuted by solid_block boards (3x3 block ->
# same X). 'decor breaks the match' refuted by diag_decor (X still
# painted, decor gone). 'non-matching shapes stay' refuted by
# partial_plus boards whose shapes VANISH (blank rebuild). 'distinct
# colors' refuted by same-color pairs. 3 demos incl. >=1 decoy.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=1 matching center on every main-path board (output non-blank)",
    "plus centers pairwise >=4 manhattan apart (no accidental extra matches; mirror-verified)",
]

DEGENERATE_TEXTURES = ("no_plus_shapes", "plus_at_corner")
HELPFUL_TEXTURES = ("plain", "solid_block", "diag_decor", "partial_plus")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "grid_w":  {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "n_plus":  {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|solid_block|diag_decor|partial_plus|"
                         "no_plus_shapes|plus_at_corner",
                "doc": "solid_block: 3x3 block fires the cardinal test too; "
                       "diag_decor: other-color cells on a plus's diagonals "
                       "(match unaffected, decor vanishes); partial_plus: "
                       "an armless plus that vanishes."},
}


def _mirror(g):
    h, w = len(g), len(g[0])
    out = [[0] * w for _ in range(h)]
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            v = g[r][c]
            if v != 0 and g[r - 1][c] == v and g[r + 1][c] == v \
                    and g[r][c - 1] == v and g[r][c + 1] == v:
                for dr, dc in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
                    out[r + dr][c + dc] = v
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "solid_block", "diag_decor",
                        "partial_plus"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        n_plus = ctx.draw_int("n_plus", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        n_plus = ctx.draw_int("n_plus", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 7, 11)
        n_plus = ctx.draw_int("n_plus", 1, 3)
    rng = ctx.draw_rng("layout")

    for _attempt in range(60):
        g = full_grid(h, w, 0)
        palette = [rng.choice([1, 2, 3, 4, 6, 7, 8, 9]) for _ in range(n_plus)]
        if n_plus >= 2 and rng.random() < 0.6:
            palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_plus)
        centers = []
        expected = 0
        for ki, color in enumerate(palette):
            kind = "plus"
            if texture == "solid_block" and ki == 0:
                kind = "block"
            placed = False
            for _ in range(60):
                r = rng.randint(1, h - 2)
                c = rng.randint(1, w - 2)
                if any(abs(r - pr) + abs(c - pc) < 5 for pr, pc in centers):
                    continue
                if kind == "block":
                    if r < 1 or c < 1 or r > h - 2 or c > w - 2:
                        continue
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            g[r + dr][c + dc] = color
                else:
                    for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                        g[r + dr][c + dc] = color
                centers.append((r, c))
                expected += 1
                placed = True
                break
            if not placed:
                break
        if not centers:
            continue

        if texture == "diag_decor":
            # other-color cells on a plus's DIAGONALS: the cardinal
            # test still fires; the decor vanishes from the output
            r, c = centers[0]
            decor = rng.choice([v for v in (1, 2, 3, 4, 6, 7, 8, 9)
                                if v != g[r][c]])
            for dr, dc in rng.sample([(-1, -1), (-1, 1), (1, -1), (1, 1)],
                                     rng.randint(1, 3)):
                g[r + dr][c + dc] = decor
        elif texture == "partial_plus":
            # an armless plus elsewhere: no match, it VANISHES
            color = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
            for _ in range(60):
                r = rng.randint(1, h - 2)
                c = rng.randint(1, w - 2)
                if any(abs(r - pr) + abs(c - pc) < 5 for pr, pc in centers):
                    continue
                arms = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                arms.remove(rng.choice(arms))
                if any(g[r + dr][c + dc] != 0 for dr, dc in [(0, 0)] + arms):
                    continue
                g[r][c] = color
                for dr, dc in arms:
                    g[r + dr][c + dc] = color
                break

        out = _mirror(g)
        n_x = sum(1 for r in range(1, h - 1) for c in range(1, w - 1)
                  if out[r][c] != 0 and all(
                      out[r + dr][c + dc] == out[r][c]
                      for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))))
        if n_x != expected:
            continue  # accidental extra/missing match
        if all(v == 0 for row in out for v in row):
            continue
        return g
    raise ValueError("could not realize plus board")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_plus_shapes — scattered dots/short bars: nothing matches,
                     output is BLANK (the rule rebuilds from empty).
    plus_at_corner — a plus truncated by the border: its center is
                     never scanned with 4 in-bounds equal neighbors,
                     so the whole shape vanishes (blank output).
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 7, 10)
    g = full_grid(h, w, 0)
    if name == "no_plus_shapes":
        for color in rng.sample([1, 2, 3, 4, 6, 7, 8, 9], rng.randint(2, 4)):
            g[rng.randrange(h)][rng.randrange(w)] = color
        return g
    # plus_at_corner: center on the border row/col, up-arm clipped away
    c = rng.randint(1, w - 2)
    color = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    g[0][c] = color
    g[0][c - 1] = color
    g[0][c + 1] = color
    g[1][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h, w = len(grid), len(grid[0])
    centers = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            v = grid[r][c]
            if v != 0 and grid[r - 1][c] == v and grid[r + 1][c] == v \
                    and grid[r][c - 1] == v and grid[r][c + 1] == v:
                centers.append((r, c))
    if not centers:
        msgs.append("expected at least one cardinal matching center")
    out = _mirror(grid)
    if all(v == 0 for row in out for v in row):
        msgs.append("mirror output would be blank")
    x_centers = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
                 if out[r][c] != 0 and all(out[r + dr][c + dc] == out[r][c]
                                           for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)))]
    if len(x_centers) != len(centers):
        msgs.append("input matching centers and output X centers differ")
    return msgs
