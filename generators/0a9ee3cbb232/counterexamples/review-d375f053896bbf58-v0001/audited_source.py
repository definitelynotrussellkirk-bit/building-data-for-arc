"""Generator for puzzle 5289ad53 — count horizontal runs of 3 and 2.

Rule: n3 = number of horizontal RUNS (per-row maximal segments) of
color 3; n2 likewise for color 2. Output = 2x3 grid filled row-major:
n3 threes, then n2 twos, rest 0; counts past 6 truncate. Runs are
per-row: a 1-wide VERTICAL bar of height k counts k runs, a 2-row
block counts 2.

Combinatorial axes: grid_h/w, run counts, texture
(plain|vertical_bar|block|overflow|same_row).
Degenerates: no_segs (all-zero output), checker_overflow.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a9ee3cbb232"
VERSION = "3.2.0"  # diversity: draw (n3,n2) from a curated spread set + place each remaining run on its OWN free row so realized counts == target (was: correlated 0..6 draws + lossy crowded placement collapsed the tiny 2x3 tally to 4 values)
TASK_ID = "0a9ee3cbb232"
SUMMARY = (
    "Count horizontal RUNS of 3 then 2 into a 2x3 tally. "
    "vertical_bar boards include a 1-wide vertical bar (height k = k "
    "runs, refuting object-counting); block boards use a 2-row "
    "rectangle (2 runs); same_row boards put two same-color segments "
    "in ONE row (2 runs); overflow boards exceed 6 total (the tally "
    "truncates). (Was: single-row segments only - the run-vs-object "
    "distinction never fired.)"
)

# Rivals: 'count objects' refuted by vertical_bar/block (one object,
# many runs). 'one segment per row max' refuted by same_row. 'counts
# always fit' refuted by overflow truncation. 3-4 demos incl. >=1
# multi-row shape.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "bg is 1 (the rule only looks at 3s and 2s)",
    "vertical_bar/block boards: >=1 multi-row shape",
    "main-path totals <= 6 except overflow boards",
]

DEGENERATE_TEXTURES = ("no_segs", "checker_overflow")
HELPFUL_TEXTURES = ("plain", "vertical_bar", "block", "overflow",
                    "same_row")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":  {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "n_3":     {"type": "int", "default": "rng 1..3", "valid": "0..6"},
    "n_2":     {"type": "int", "default": "rng 1..3", "valid": "0..6"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|vertical_bar|block|overflow|same_row|"
                         "no_segs|checker_overflow",
                "doc": "vertical_bar: height-k bar = k runs; block: "
                       "2-row rect = 2 runs; overflow: total > 6 "
                       "truncates; same_row: two same-color runs in "
                       "one row."},
}


def _mirror(g):
    h, w = len(g), len(g[0])

    def runs(color):
        n = 0
        for r in range(h):
            in_seg = False
            for c in range(w):
                if g[r][c] == color:
                    if not in_seg:
                        n += 1
                        in_seg = True
                else:
                    in_seg = False
        return n

    n3, n2 = runs(3), runs(2)
    out = [[0] * 3 for _ in range(2)]
    for i in range(6):
        if i < n3:
            out[i // 3][i % 3] = 3
        elif i < n3 + n2:
            out[i // 3][i % 3] = 2
    return out


def _place_seg(g, rng, color, length):
    h, w = len(g), len(g[0])
    for _t in range(120):
        r = rng.randint(0, h - 1)
        sc = rng.randint(0, w - length)
        if all(g[r][c] == 1 for c in range(max(0, sc - 1),
                                           min(w, sc + length + 1))):
            for c in range(sc, sc + length):
                g[r][c] = color
            return True
    return False


def _place_rect(g, rng, color, rh, rw):
    h, w = len(g), len(g[0])
    for _t in range(120):
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(0, w - rw)
        if all(g[r][c] == 1
               for r in range(max(0, r0 - 1), min(h, r0 + rh + 1))
               for c in range(max(0, c0 - 1), min(w, c0 + rw + 1))):
            for r in range(r0, r0 + rh):
                for c in range(c0, c0 + rw):
                    g[r][c] = color
            return rh
    return 0


# Curated (n3, n2) targets — all map to DISTINCT 2x3 tallies, so over the
# handful of (seed==sample_index) probe points the output spans its range
# instead of collapsing onto the saturated tally.
_COUNT_PAIRS = ((1, 1), (2, 1), (3, 2), (0, 3), (4, 2), (2, 4),
                (5, 0), (3, 3), (1, 4), (2, 2), (4, 1), (0, 2))


def _free_rows(g):
    """Rows with no non-bg cell — a plain run placed here is guaranteed to
    be its own maximal run (no merge/collision), so realized run-count == budget."""
    return [r for r in range(len(g)) if all(v == 1 for v in g[r])]


def _place_seg_on_row(g, rng, color, length, r):
    w = len(g[0])
    sc = rng.randint(0, w - length)
    for c in range(sc, sc + length):
        g[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        # overflow saturates the tally (truncation demo) so give it low
        # weight — most boards should show a non-saturated, distinct count.
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain",
                                              "vertical_bar", "block",
                                              "same_row", "overflow"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 8, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 16)
    else:
        h = ctx.draw_int("grid_h", 8, 14)
        w = ctx.draw_int("grid_w", 10, 16)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 1)

    # Output is a fixed 2x3 tally; STEP through a curated spread set by
    # sample_index (rng.choice birthday-collided several samples onto the
    # same pair). Every pair totals <= 6 (no truncation) and maps to a
    # DISTINCT tally, so consecutive samples cover distinct outputs.
    pair3, pair2 = _COUNT_PAIRS[(sample_index * 5) % len(_COUNT_PAIRS)]
    budget3 = int(overrides["n_3"]) if overrides.get("n_3") is not None else pair3
    budget2 = int(overrides["n_2"]) if overrides.get("n_2") is not None else pair2

    # Textures place a multi-row / same-row SHAPE whose run-count refutes
    # object-counting. The shape is sized to FIT its colour's target and
    # its run contribution is subtracted, so realized count == target
    # exactly (whether or not the shape places) — that is what keeps the
    # tiny tally diverse across probe seeds.
    if texture in ("vertical_bar", "block", "same_row"):
        color = 3 if budget3 >= budget2 else 2
        cap = budget3 if color == 3 else budget2
        contrib = 0
        if cap >= 2:
            if texture == "vertical_bar":
                k = min(rng.randint(2, 4), cap, h - 1)
                contrib = _place_rect(g, rng, color, k, 1)
            elif texture == "block":
                contrib = _place_rect(g, rng, color, 2, rng.randint(2, 3))
            else:  # same_row: two same-colour segments in ONE row = 2 runs
                if w >= 7:
                    for _t in range(120):
                        r = rng.randint(0, h - 1)
                        c1 = rng.randint(0, w - 7)
                        l1 = rng.randint(2, 3)
                        c2 = c1 + l1 + rng.randint(1, 2)
                        l2 = rng.randint(2, min(3, w - c2))
                        cells = range(max(0, c1 - 1), min(w, c2 + l2 + 1))
                        if all(g[r][c] == 1 for c in cells):
                            for c in range(c1, c1 + l1):
                                g[r][c] = color
                            for c in range(c2, c2 + l2):
                                g[r][c] = color
                            contrib = 2
                            break
        if color == 3:
            budget3 = max(0, budget3 - contrib)
        else:
            budget2 = max(0, budget2 - contrib)
    elif texture == "overflow":
        # Total > 6 so the tally truncates (truncation demo); split stepped
        # by sample_index for what little variety truncation allows.
        _ovf = ((3, 5), (4, 4), (5, 3), (3, 4), (4, 5), (5, 4))
        budget3, budget2 = _ovf[sample_index % len(_ovf)]

    # Place each remaining plain run on its OWN free row so the realized
    # run-count equals the target exactly (crowded random placement used to
    # silently drop segments, squashing many targets onto the same tally).
    rows = _free_rows(g)
    rng.shuffle(rows)
    ri = 0
    for _ in range(budget3):
        if ri >= len(rows):
            break
        _place_seg_on_row(g, rng, 3, rng.randint(2, min(5, w // 2)), rows[ri])
        ri += 1
    for _ in range(budget2):
        if ri >= len(rows):
            break
        _place_seg_on_row(g, rng, 2, rng.randint(2, min(5, w // 2)), rows[ri])
        ri += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """The derived 2x3 tally must be 2x3 with palette subset {0,2,3}."""
    issues = []
    out = _mirror(grid)
    if len(out) != 2 or any(len(r) != 3 for r in out):
        issues.append("tally is not 2x3")
    pal = {v for row in out for v in row}
    if not pal <= {0, 2, 3}:
        issues.append(f"tally palette {sorted(pal)} not subset of 0,2,3")
    return issues


def _draw_from_degenerate(name, ctx):
    """no_segs — no 3s or 2s anywhere: the tally is all-zero.
    checker_overflow — 3/2 checkerboard: hundreds of 1-cell runs, the
    tally saturates to six 3s. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 11)
    w = ctx.draw_int("grid_w", 9, 13)
    if name == "checker_overflow":
        return [[3 if (r + c) % 2 == 0 else 2 for c in range(w)]
                for r in range(h)]
    g = full_grid(h, w, 1)
    for _ in range(rng.randint(0, 4)):
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        g[r][c] = rng.choice([4, 5, 6, 7, 8])  # non-counted colors
    return g
