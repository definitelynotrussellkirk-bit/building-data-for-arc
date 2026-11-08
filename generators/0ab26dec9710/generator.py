"""Generator for arc_puzzle_bank_21_set8_s:S8_E1 — keep the longest
run per row.

Rule: per row, the maximal same-color non-0 runs are compared; only
the LONGEST survives (ties -> LEFTMOST start), everything else is
erased (output rebuilt from blank). Adjacent different-color cells
with no gap are SEPARATE runs.

Combinatorial axes: grid_h/w, runs per row, texture
(plain|tie|touching|single|dense).
Degenerates: no_runs (blank -> blank).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0ab26dec9710"
VERSION = "2.0.1"
TASK_ID = "0ab26dec9710"

SUMMARY = (
    "Rows hold 2-4 runs at free positions; only the longest per row "
    "survives. tie boards have two equal-longest runs (LEFTMOST wins, "
    "promoted from a mislabeled degenerate); touching boards put "
    "different-color runs side by side with NO gap (still separate "
    "runs - the split is by color change, not by 0s); single boards "
    "mix one-run rows (kept) among multi-run rows. (Was: exactly 2 "
    "edge-anchored runs per row.)"
)

# Rivals: 'keep the first/left run' refuted by long runs on the
# right. 'ties keep both' refuted by tie boards (leftmost only).
# 'runs split only at 0s' refuted by touching boards. 3-4 demos
# incl. >=1 tie or touching row.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "runs are maximal same-color segments (color change splits)",
    "tie boards: >=1 row with two equal-longest runs",
    "touching boards: >=1 pair of adjacent different-color runs",
]

DEGENERATE_TEXTURES = ("no_runs",)
HELPFUL_TEXTURES = ("plain", "tie", "touching", "single", "dense")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 5..10", "valid": "3..14"},
    "grid_w":  {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|tie|touching|single|dense|no_runs",
                "doc": "tie: equal-longest, leftmost wins; touching: "
                       "no-gap different-color runs are separate; "
                       "single: one-run rows survive unchanged."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _mirror(g):
    h, w = len(g), len(g[0])
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        runs = []
        c = 0
        while c < w:
            v = g[r][c]
            if v == 0:
                c += 1
                continue
            start = c
            while c + 1 < w and g[r][c + 1] == v:
                c += 1
            runs.append((start, c, v))
            c += 1
        if not runs:
            continue
        best = sorted(runs, key=lambda t: (-(t[1] - t[0] + 1), t[0]))[0]
        for cc in range(best[0], best[1] + 1):
            out[r][cc] = best[2]
    return out


def _row_layout(rng, w, n_runs, lengths=None, touching=False):
    """Return [(start, length, color)] for one row, or None."""
    for _t in range(150):
        lens = lengths or [rng.randint(1, 5) for _ in range(n_runs)]
        gaps = [0 if touching and i == 1 else rng.randint(1, 3)
                for i in range(n_runs)]
        gaps[0] = rng.randint(0, 2)
        total = sum(lens) + sum(gaps)
        if total > w:
            continue
        start = rng.randint(0, w - total)
        out = []
        pos = start
        colors = []
        for i in range(n_runs):
            pos += gaps[i]
            color = rng.choice([c for c in _COLORS
                                if not colors or c != colors[-1]])
            colors.append(color)
            out.append((pos, lens[i], color))
            pos += lens[i]
        return out
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty,
                  overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "tie",
                                              "touching", "single",
                                              "dense"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 10, 12)
        active = ctx.draw_int("active_rows", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 13, 16)
        active = ctx.draw_int("active_rows", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 5, 10)
        w = ctx.draw_int("grid_w", 10, 16)
        active = ctx.draw_int("active_rows", 2, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), min(active, h))
    special_done = False
    for i, r in enumerate(rows):
        if texture == "tie" and not special_done:
            length = rng.randint(2, 4)
            lay = _row_layout(rng, w, 2, lengths=[length, length])
            special_done = lay is not None
        elif texture == "touching" and not special_done:
            lay = _row_layout(rng, w, rng.randint(2, 3), touching=True)
            special_done = lay is not None
        elif texture == "single" and i % 2 == 0:
            lay = _row_layout(rng, w, 1)
        elif texture == "dense":
            lay = _row_layout(rng, w, rng.randint(3, 4))
        else:
            # unique longest: re-roll until lengths have a unique max
            lay = None
            for _t in range(60):
                cand = _row_layout(rng, w, rng.randint(2, 3))
                if cand is None:
                    continue
                lens = [l for _, l, _ in cand]
                if lens.count(max(lens)) == 1:
                    lay = cand
                    break
        if lay is None:
            continue
        for start, length, color in lay:
            for c in range(start, start + length):
                g[r][c] = color
    if all(v == 0 for row in g for v in row):
        lay = _row_layout(rng, w, 2)
        if lay:
            for start, length, color in lay:
                for c in range(start, start + length):
                    g[0][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 row containing >=2 non-zero runs (so longest run != trivially all)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    for r in range(h):
        runs = 0
        in_run = False
        for c in range(w):
            if grid[r][c] != 0:
                if not in_run:
                    runs += 1
                    in_run = True
            else:
                in_run = False
        if runs >= 2:
            return []
    return ["no row has >=2 non-zero runs — rule picks the trivially unique longest run"]


def _draw_from_degenerate(name, ctx):
    """no_runs — blank grid: the rebuilt output is also blank."""
    h = ctx.draw_int("grid_h", 5, 9)
    w = ctx.draw_int("grid_w", 10, 14)
    return full_grid(h, w, 0)
