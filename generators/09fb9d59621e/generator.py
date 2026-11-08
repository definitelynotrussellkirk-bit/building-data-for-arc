"""Generator for puzzle 505fff84 — extract between-marker payload rows.

Rule: each row holding BOTH a 1 and an 8 (first occurrence of each,
either order) contributes the cells strictly between them; the output
stacks those segments. Output width = the FIRST payload row's gap:
wider later rows are TRUNCATED to it; narrower later rows leak #f
cells (invalid) and a gap-0 or payload-free board yields an empty
grid (invalid) — never generated.

Combinatorial axes: payload_width/rows, per-row marker column + order,
texture (plain|noise|near_miss|wider_later).
Degenerates: none survivable (all invalid-output, documented above).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "09fb9d59621e"
VERSION = "2.0.1"
TASK_ID = "09fb9d59621e"
SUMMARY = (
    "Rows with a 1-8 marker pair contribute their between-cells; "
    "marker columns and 1/8 order vary PER ROW (the extraction is "
    "per-row, not columnar). noise boards bury payload rows in dense "
    "0/2 noise like the original task; near_miss boards add rows with "
    "only a 1 or only an 8 (skipped); wider_later boards give later "
    "rows a wider gap that truncates to the first row's width. (Was: "
    "markers frozen at columns 1/pw+2 in every row on a blank "
    "background - per-row freedom and noise never exercised.)"
)

# Rivals: 'markers form straight columns' refuted by per-row marker
# offsets. 'any marker row counts' refuted by near_miss (single-marker
# rows skipped). 'payload is everything right of the 1' refuted by
# 8-before-1 rows. 3-4 demos incl. >=1 noisy board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "first payload row's gap is the minimum (narrower-later leaks #f)",
    "every board has >=1 payload row with gap >=1 (else empty output)",
    "no stray 1/8 left of a payload row's markers (first-occurrence)",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ("plain", "noise", "near_miss", "wider_later")

AXES = {
    "payload_width": {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "payload_rows":  {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "texture":       {"type": "str", "default": "rng helpful",
                      "valid": "plain|noise|near_miss|wider_later",
                      "doc": "noise: dense 0/2 background everywhere "
                             "(payload rows too, outside the span); "
                             "near_miss: rows with only one marker are "
                             "skipped; wider_later: later rows' wider "
                             "gaps truncate to the first row's width."},
}

_FILL = (0, 2)


def _mirror(g):
    h, w = len(g), len(g[0])
    payload = []
    for r in range(h):
        c1 = next((c for c in range(w) if g[r][c] == 1), None)
        c8 = next((c for c in range(w) if g[r][c] == 8), None)
        if c1 is None or c8 is None:
            continue
        lo, hi = min(c1, c8), max(c1, c8)
        payload.append([g[r][c] for c in range(lo + 1, hi)])
    if not payload:
        return None
    ncols = len(payload[0])
    return [row[:ncols] for row in payload]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "noise", "noise",
                                              "near_miss", "wider_later"))
    if difficulty == "easy":
        pw = ctx.draw_int("payload_width", 2, 3)
        n_pay = ctx.draw_int("payload_rows", 2, 2)
    elif difficulty == "hard":
        pw = ctx.draw_int("payload_width", 4, 6)
        n_pay = ctx.draw_int("payload_rows", 3, 5)
    else:
        pw = ctx.draw_int("payload_width", 2, 5)
        n_pay = ctx.draw_int("payload_rows", 2, 4)
    rng = ctx.draw_rng("layout")
    max_gap = pw + (2 if texture == "wider_later" else 0)
    w = max_gap + 4 + rng.randint(0, 3)
    n_skip = rng.randint(1, 3)
    h = n_pay + n_skip + rng.randint(0, 2)
    g = full_grid(h, w, 0)
    noisy = texture == "noise"
    if noisy:
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.choice(_FILL)

    pay_rows = sorted(rng.sample(range(h), n_pay))
    first = True
    for r in pay_rows:
        gap = pw if first or texture != "wider_later" \
            else pw + rng.randint(1, 2)
        lo = rng.randint(0, w - gap - 2)
        hi = lo + gap + 1
        # wipe any noise 1/8 hijack risk: this row uses only _FILL
        for c in range(w):
            if g[r][c] not in _FILL:
                g[r][c] = rng.choice(_FILL)
        if rng.random() < 0.5:
            g[r][lo], g[r][hi] = 1, 8
        else:
            g[r][lo], g[r][hi] = 8, 1
        for c in range(lo + 1, hi):
            g[r][c] = rng.choice(_FILL)
        first = False
    if texture == "near_miss":
        skips = [r for r in range(h) if r not in pay_rows]
        for r in rng.sample(skips, min(len(skips), rng.randint(1, 2))):
            g[r][rng.randint(0, w - 1)] = rng.choice([1, 8])
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=1 payload row (a row with both a 1 and an 8 such that
    the gap between them is >=1 and contains no other 1/8 cells)."""
    msgs = []
    h, w = len(grid), len(grid[0])
    payload_rows = []
    for r in range(h):
        row = grid[r]
        ones = [c for c in range(w) if row[c] == 1]
        eights = [c for c in range(w) if row[c] == 8]
        if not ones or not eights:
            continue
        lo = min(ones[0], eights[0])
        hi = max(ones[0], eights[0])  # first 1 and first 8
        if hi - lo >= 2:
            # Check no other 1/8 strictly between
            interior = row[lo + 1:hi]
            if 1 not in interior and 8 not in interior:
                payload_rows.append(r)
    if not payload_rows:
        msgs.append(
            "no valid payload row found (a row with both 1 and 8 and a "
            "gap >=1 with no stray 1/8 inside)"
        )
    return msgs
