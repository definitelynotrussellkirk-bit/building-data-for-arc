"""Generator for f1bcbc2c.

Rule: a marker at the inner corner of an orange L-channel selects the
larger adjacent half of the channel-adjacency band to fill cyan.

Combinatorial axes: grid size, the two arm lengths (which decides the
larger half), the L position, and the dihedral orientation (8).
Degenerates: no_channel, no_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b9e736518d82"
VERSION = "3.0.1"  # 3.0.0->3.0.1: add self_check. diversity: random arm lengths + grid + position + dihedral (was fixed 13x13, ~12 configs)
TASK_ID = "b9e736518d82"
SUMMARY = (
    "0-bg grid (size varies). An L-shaped CHANNEL boundary in color 7 "
    "(orange): a horizontal arm meeting a vertical arm at a right angle, "
    "with a single color-9 MARKER at the INNER (concave) corner. The two "
    "arm lengths differ, and the whole figure is placed at a random "
    "position and in one of 8 dihedral orientations. Rule: take the band "
    "of cells adjacent to the orange channel that is connected to the "
    "marker; the marker sits at the corner, so removing it splits the "
    "band into two halves — paint the LARGER half color 8 (cyan). Grid "
    "size, the arm lengths (which decides the larger half), position and "
    "orientation all vary freely (was a fixed 13x13 grid with ~12 "
    "configs)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "orange cells define a bent channel boundary (L)",
    "exactly one color-9 marker adjacent to orange, at the inner corner",
    "the marker's channel split produces a clearly larger half",
    "the larger adjacent half is filled with color 8",
]

TURN_KINDS = ("t0", "t1", "t2")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_channel", "no_marker", "full_grid")
HELPFUL_TEXTURES = TURN_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..24"},
    "turn":           {"type": "choice", "default": "n/a (now 8 dihedral)",
                       "valid": "0|1|2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for turn",
                       "valid": "t0|t1|t2|no_channel|no_marker|full_grid"},
}


def _rot90(g):
    H = len(g); W = len(g[0])
    return [[g[H - 1 - r][c] for r in range(H)] for c in range(W)]


def _flip(g):
    return [list(reversed(row)) for row in g]


def _dihedral(g, k, f):
    for _ in range(k % 4):
        g = _rot90(g)
    if f:
        g = _flip(g)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has orange(7) cells defining L-channel; has color-9 marker."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not colors:
        return errs  # degenerate
    if 7 not in colors:
        errs.append("missing orange(7) L-channel cells")
    if 9 not in colors:
        errs.append("missing color-9 marker cell")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        long_lo, long_hi, pad = 7, 8, (2, 3)
    elif difficulty == "hard":
        long_lo, long_hi, pad = 8, 11, (2, 5)
    else:
        long_lo, long_hi, pad = 7, 9, (2, 4)

    long_arm = rng.randint(long_lo, long_hi)
    short_arm = rng.randint(4, long_arm - 3)        # differ by >=3 → clear winner
    # Randomly assign which arm is horizontal vs vertical.
    if rng.random() < 0.5:
        hlen, vlen = long_arm, short_arm
    else:
        hlen, vlen = short_arm, long_arm

    # Canonical ┐ L: horizontal arm = row R cols [Cv-hlen+1, Cv]; vertical arm =
    # col Cv rows [R, R+vlen-1]; marker at the inner corner (R+1, Cv-1).
    wc = hlen + rng.randint(*pad) + 1
    hc = vlen + rng.randint(*pad) + 1
    cv = rng.randint(hlen, wc - 2)
    r0 = rng.randint(1, hc - vlen - 1)

    g = full_grid(hc, wc, 0)
    for c in range(cv - hlen + 1, cv + 1):
        g[r0][c] = 7
    for r in range(r0, r0 + vlen):
        g[r][cv] = 7
    g[r0 + 1][cv - 1] = 9

    return _dihedral(g, rng.randint(0, 3), rng.random() < 0.5)


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_channel":
        g[5][8] = 9
        return g
    if name == "no_marker":
        for c in range(2, 10):
            g[6][c] = 7
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 7
        return g
    return g
