"""Generator for arc_additional_puzzle_bank_volume14:E93 — fill between red endpoints with yellow.

Rule: rows with exactly two red endpoints are filled between with yellow.

Combinatorial axes: grid_h, grid_w, n_rows, texture
(plain|blocked_span|three_reds|col_pair|adjacent).
Degenerates: no_endpoints, single_endpoint_per_row, span_already_filled
(all identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "082f5a2cd092"
VERSION = "2.0.0"
TASK_ID = "082f5a2cd092"
SUMMARY = (
    "Rows with EXACTLY two reds and an all-zero span between them "
    "fill with yellow; rows with 3+ reds, a blocked span (any non-"
    "zero cell between), or one red stay untouched, and vertical red "
    "pairs do nothing (the rule is row-only). (Was: every red pair "
    "was an active clean row - none of the rule's guards were ever "
    "contested.)"
)

# Rivals: 'fill between any two reds' refuted by blocked spans that
# stay. 'fill rows with any reds' refuted by 3-red rows staying.
# 'fill vertically too' refuted by column pairs doing nothing.
# 'adjacent endpoints break' refuted by c2=c1+1 rows (empty span,
# no-op but valid). 3 demos incl. >=1 guard case.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0; reds are color 2; fills are color 4",
    ">=1 active clean row on every main-path board",
    "blockers between endpoints never use color 2 (would change the count)",
]

DEGENERATE_TEXTURES = ("no_endpoints", "single_endpoint_per_row",
                       "span_already_filled")
HELPFUL_TEXTURES = ("plain", "blocked_span", "three_reds", "col_pair",
                    "adjacent")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 7..12", "valid": "5..18"},
    "grid_w":  {"type": "int", "default": "rng 8..14", "valid": "5..22"},
    "n_rows":  {"type": "int", "default": "rng 2..4", "valid": "1..8",
                "doc": "Active clean rows that fill."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|blocked_span|three_reds|col_pair|adjacent|"
                         "no_endpoints|single_endpoint_per_row|"
                         "span_already_filled",
                "doc": "blocked_span: a non-red cell between endpoints "
                       "(row stays); three_reds: 3 reds in a row (stays); "
                       "col_pair: a vertical red pair (rule is row-only); "
                       "adjacent: touching endpoints (empty span, no-op)."},
}


def _add_pair(g, rng, r, min_gap=2):
    w = len(g[0])
    for _ in range(60):
        c1, c2 = sorted(rng.sample(range(w), 2))
        if c2 - c1 < min_gap:
            continue
        if any(g[r][c] != 0 for c in range(c1, c2 + 1)):
            continue
        g[r][c1] = 2
        g[r][c2] = 2
        return (c1, c2)
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
            "texture", ("plain", "plain", "blocked_span", "three_reds",
                        "col_pair", "adjacent"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        n_rows = ctx.draw_int("n_rows", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 14)
        n_rows = ctx.draw_int("n_rows", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 8, 14)
        n_rows = ctx.draw_int("n_rows", 2, 4)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)

    rows = list(range(h))
    rng.shuffle(rows)
    active = 0
    it = iter(rows)
    for r in it:
        if active >= n_rows:
            break
        if _add_pair(g, rng, r):
            active += 1
    if active == 0:
        g[0][0] = 2
        g[0][min(3, w - 1)] = 2

    spare = [r for r in range(h) if all(v == 0 for v in g[r])]
    rng.shuffle(spare)
    if texture == "blocked_span" and spare:
        r = spare.pop()
        pair = _add_pair(g, rng, r, min_gap=3)
        if pair:
            c1, c2 = pair
            g[r][rng.randint(c1 + 1, c2 - 1)] = rng.choice([1, 3, 5, 6, 7, 8, 9])
    elif texture == "three_reds" and spare:
        r = spare.pop()
        cols = sorted(rng.sample(range(w), 3))
        for c in cols:
            g[r][c] = 2
    elif texture == "col_pair" and len(spare) >= 2:
        spare.sort()
        # two reds in one COLUMN on otherwise-empty rows: row-only
        # rule sees one red per row -> nothing fills
        c = rng.randrange(w)
        r1, r2 = spare[0], spare[-1]
        g[r1][c] = 2
        g[r2][c] = 2
    elif texture == "adjacent" and spare:
        r = spare.pop()
        c = rng.randint(0, w - 2)
        g[r][c] = 2
        g[r][c + 1] = 2  # empty span: fills nothing, still "clean"
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_endpoints            — blank: identity.
    single_endpoint_per_row — one red per row: no spans, identity.
    span_already_filled     — solid red bars: each row has >2 reds,
                              identity (the count guard fails first).
    """
    rng = ctx.draw_rng("degenerate_placement")
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 8, 12)
    g = full_grid(h, w, 0)
    if name == "no_endpoints":
        return g
    if name == "single_endpoint_per_row":
        for r in rng.sample(range(h), rng.randint(2, 4)):
            g[r][rng.randrange(w)] = 2
        return g
    for r in rng.sample(range(h), rng.randint(1, 2)):
        c1 = rng.randint(0, w - 5)
        c2 = c1 + rng.randint(4, min(6, w - 1 - c1))
        for c in range(c1, c2 + 1):
            g[r][c] = 2
    return g



def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    active = 0
    for row in grid:
        reds = [i for i, v in enumerate(row) if v == 2]
        if len(reds) == 2:
            c1, c2 = reds
            span = row[c1 + 1:c2]
            if all(v == 0 for v in span):
                active += 1
            elif any(v == 2 for v in span):
                msgs.append("blocked span uses color 2 and changes the endpoint count")
    if active < 1:
        msgs.append("main-path board has no clean two-red row to fill")
    return msgs
