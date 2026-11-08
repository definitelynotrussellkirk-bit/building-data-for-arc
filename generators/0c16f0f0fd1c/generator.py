"""Generator for 0c16f0f0fd1c — complete 3/4 seven-squares.

Rule: every 2x2 window holding exactly three 7s and exactly one 0
fills that 0 with 7 (the condition reads the ORIGINAL grid - no
cascade). A window whose fourth cell is a non-7 color does NOT fill;
windows with two 7s do nothing; full 2x2 squares stay.

Combinatorial axes: grid_h/w, n_windows, texture
(plain|blocked|pair_only|chain|decoy).
Degenerates: no_windows, full_2x2, pair_only (all identity - a
2-seven domino never qualifies).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0c16f0f0fd1c"
VERSION = "2.0.1"
TASK_ID = "0c16f0f0fd1c"
SUMMARY = (
    "L-triominoes of 7 complete into 2x2 squares. blocked boards put "
    "a non-7 color in the fourth cell (no fill - the slot must be "
    "0); pair_only boards scatter 2-seven dominoes (no window "
    "qualifies); chain boards overlap two Ls sharing a column of 7s "
    "(both windows fill from the original); decoy boards scatter "
    "other colors near the Ls."
)

# Rivals: 'fill any gap next to 7s' refuted by pair_only. 'any
# occupied 4th cell completes' refuted by blocked. 'fills cascade'
# refuted by chain reading the original. 3 demos incl. >=1 blocked
# or pair board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "main-path boards: >=1 three-seven window with a 0 fourth cell",
    "blocked boards: >=1 three-seven window with a colored 4th cell",
    "L placements never create accidental extra qualifying windows "
    "except in chain boards (mirror-verified)",
]

DEGENERATE_TEXTURES = ("no_windows", "full_2x2", "pair_only")
HELPFUL_TEXTURES = ("plain", "blocked", "chain", "decoy")

AXES = {
    "grid_h":    {"type": "int", "default": "rng 7..13", "valid": "5..16"},
    "grid_w":    {"type": "int", "default": "rng 7..13", "valid": "5..16"},
    "n_windows": {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "texture":   {"type": "str", "default": "rng helpful",
                  "valid": "plain|blocked|pair_only|chain|decoy|"
                           "no_windows|full_2x2",
                  "doc": "blocked: colored 4th cell stays; pair_only: "
                         "dominoes never fill; chain: overlapping "
                         "windows both fill."},
}

_CORNERS = ((0, 0), (0, 1), (1, 0), (1, 1))
_DECOYS = (1, 2, 3, 4, 5, 6, 8, 9)


def _mirror(g):
    h, w = len(g), len(g[0])
    out = [row[:] for row in g]
    for r in range(h - 1):
        for c in range(w - 1):
            cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
            vals = [g[a][b] for a, b in cells]
            zeros = [(a, b) for a, b in cells if g[a][b] == 0]
            if vals.count(7) == 3 and len(zeros) == 1:
                out[zeros[0][0]][zeros[0][1]] = 7
    return out


def _free(g, r0, c0, rh=2, rw=2):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + rh > h or c0 + rw > w:
        return False
    return all(g[r][c] == 0
               for r in range(max(0, r0 - 1), min(h, r0 + rh + 1))
               for c in range(max(0, c0 - 1), min(w, c0 + rw + 1)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "blocked",
                                              "chain", "decoy"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        n_win = ctx.draw_int("n_windows", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
        n_win = ctx.draw_int("n_windows", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 13)
        w = ctx.draw_int("grid_w", 7, 13)
        n_win = ctx.draw_int("n_windows", 2, 4)
    rng = ctx.draw_rng("layout")
    if texture == "blocked":
        n_win = max(2, n_win)  # blocked window + >=1 real fill

    for _attempt in range(150):
        g = full_grid(h, w, 0)
        placed = 0
        if texture == "chain":
            # 2x3 block of 7s minus two corners: two windows fill
            for _t in range(80):
                r0 = rng.randint(0, h - 2)
                c0 = rng.randint(0, w - 3)
                if _free(g, r0, c0, 2, 3):
                    for r in range(2):
                        for c in range(3):
                            g[r0 + r][c0 + c] = 7
                    g[r0][c0] = 0
                    g[r0][c0 + 2] = 0
                    placed += 1
                    break
            n_left = max(0, n_win - 1)
        else:
            n_left = n_win
        for _ in range(n_left):
            for _t in range(120):
                r0 = rng.randint(0, h - 2)
                c0 = rng.randint(0, w - 2)
                if not _free(g, r0, c0):
                    continue
                missing = _CORNERS[rng.randrange(4)]
                for dr, dc in _CORNERS:
                    if (dr, dc) != missing:
                        g[r0 + dr][c0 + dc] = 7
                if texture == "blocked" and placed == 0:
                    # block the FIRST window; later windows fill
                    g[r0 + missing[0]][c0 + missing[1]] = \
                        rng.choice(_DECOYS)
                placed += 1
                break
        if placed == 0:
            continue
        if texture == "decoy":
            for _ in range(rng.randint(2, 4)):
                for _t in range(60):
                    r = rng.randrange(h)
                    c = rng.randrange(w)
                    if g[r][c] == 0 and \
                       all(g[ar][ac] != 7
                           for ar in range(max(0, r - 1), min(h, r + 2))
                           for ac in range(max(0, c - 1), min(w, c + 2))):
                        g[r][c] = rng.choice(_DECOYS)
                        break
        out = _mirror(g)
        if out == g:
            continue  # every main-path board must visibly change
        return g
    raise ValueError("could not realize seven-square board")


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=1 fillable window (a 2x2 window with exactly 3 sevens
    and one 0 cell the rule would complete)."""
    msgs = []
    h, w = len(grid), len(grid[0])
    fillable = False
    for r0 in range(h - 1):
        for c0 in range(w - 1):
            window = [grid[r0 + dr][c0 + dc] for dr, dc in ((0,0),(0,1),(1,0),(1,1))]
            if window.count(7) == 3 and window.count(0) == 1:
                fillable = True
                break
        if fillable:
            break
    if not fillable:
        msgs.append(
            "no 2x2 window with exactly 3 sevens and 1 zero "
            "(rule would produce identity output)"
        )
    return msgs


def _draw_from_degenerate(name, ctx):
    """no_windows — scattered lone 7s: identity. full_2x2 — complete
    squares (no zero in the window): identity. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 11)
    w = ctx.draw_int("grid_w", 7, 11)
    g = full_grid(h, w, 0)
    if name == "pair_only":
        for _ in range(rng.randint(2, 4)):
            for _t in range(80):
                r0 = rng.randint(0, h - 2)
                c0 = rng.randint(0, w - 2)
                if _free(g, r0, c0):
                    keep = rng.sample(_CORNERS, 2)
                    for dr, dc in keep:
                        g[r0 + dr][c0 + dc] = 7
                    break
        if _mirror(g) != g:
            return _draw_from_degenerate("no_windows", ctx)
        return g
    if name == "no_windows":
        spots = []
        for _ in range(rng.randint(3, 5)):
            for _t in range(60):
                r = rng.randrange(h)
                c = rng.randrange(w)
                if all(abs(r - sr) > 2 or abs(c - sc) > 2
                       for sr, sc in spots):
                    g[r][c] = 7
                    spots.append((r, c))
                    break
        return g
    for _ in range(rng.randint(1, 2)):
        for _t in range(60):
            r0 = rng.randint(0, h - 2)
            c0 = rng.randint(0, w - 2)
            if _free(g, r0, c0):
                for dr, dc in _CORNERS:
                    g[r0 + dr][c0 + dc] = 7
                break
    return g
