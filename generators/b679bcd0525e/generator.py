"""Generator for b679bcd0525e — rotate an object about a 9-pivot by a token key.

Rule (verified from canonical): exactly ONE color-9 cell is the PIVOT; exactly
ONE cell of color in {1,2,3,4} is the TOKEN (turns = token_color - 1, i.e. a
number of 90deg quarter-turns). The remaining single 4-connected object is
ROTATED about the pivot by `turns` quarter-turns (CW). Output = empty grid with
the rotated object (its color preserved) plus the 9 pivot restored. Token and
original object are erased.

So the discriminators that MUST vary: the TOKEN COLOR (1..4 -> 0..3 turns) so
all four rotation amounts fire, the OBJECT SHAPE, and the object's OFFSET from
the pivot (so the rotated landing position differs). The object is placed so
every quarter-turn about the pivot stays in bounds (the rule drops OOB cells),
keeping the whole object preserved.

Combinatorial axes (8): grid_h, grid_w, token_turns, obj_size, obj_shape,
pivot_pos, obj_color, obj_quadrant.
Degenerates: turns0_identity, single_cell_obj, obj_far.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b679bcd0525e"
VERSION = "3.0.1"  # 2.1.0 was a WRONG-TASK generator (6-panel 9-divider
# "find matching pair") that did not match the canonical rotate-about-9-pivot
# rule at all: many 9s, no {1,2,3,4} token, multiple objects. 3.0.0 builds the
# correct single-pivot + single-token + single-object structure and varies the
# token turns (0..3), object shape/offset/color so all rotation branches fire.
TASK_ID = "b679bcd0525e"

SUMMARY = (
    "0-bg grid (h,w ~ 9..14) holding exactly THREE "
    "things: ONE color-9 PIVOT cell at an interior "
    "position; ONE TOKEN cell of color in {1,2,3,4} "
    "(token-1 = the number of 90deg CW quarter-turns); "
    "and ONE 4-connected OBJECT (2-6 cells) in a "
    "color from {5,6,7,8} (disjoint from pivot 9 and "
    "tokens 1-4). The object sits within a radius of "
    "the pivot small enough that ALL quarter-turns "
    "about the pivot stay in bounds. Rule: erase token "
    "and object, ROTATE the object about the pivot by "
    "(token-1) quarter-turns, repaint it in its color, "
    "and restore the 9 pivot. Net: the object swings "
    "around the pivot by the token-selected angle."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-9 pivot cell",
    "exactly one token cell of color in {1,2,3,4}",
    "exactly one 4-connected object in a color from {5,6,7,8}",
    "every quarter-turn of the object about the pivot stays in bounds",
]

DEGENERATE_TEXTURES = ("turns0_identity", "single_cell_obj", "obj_far")
TOKEN_COLORS = (1, 2, 3, 4)
OBJ_COLORS = (5, 6, 7, 8)

AXES = {
    "grid_h":     {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "grid_w":     {"type": "int", "default": "rng 9..12", "valid": "7..16"},
    "token_turns":{"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "obj_size":   {"type": "int", "default": "rng 2..5", "valid": "1..6"},
    "obj_shape":  {"type": "str", "default": "random polyomino", "valid": "varied"},
    "pivot_pos":  {"type": "str", "default": "interior", "valid": "varied"},
    "obj_color":  {"type": "int", "default": "rng {5,6,7,8}", "valid": "5..8"},
    "obj_quadrant":{"type": "str", "default": "varied", "valid": "varied"},
    "texture":    {"type": "str", "default": "none",
                   "valid": "|".join(DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 pivot(9), exactly 1 token({1..4}), ≥1 object cell({5..8})."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    pivots = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 9)
    if pivots != 1:
        errs.append(f"expected exactly 1 pivot(9), found {pivots}")
    tokens = sum(1 for r in range(h) for c in range(w) if grid[r][c] in (1, 2, 3, 4))
    if tokens != 1:
        errs.append(f"expected exactly 1 token(1..4), found {tokens}")
    obj_cells = sum(1 for r in range(h) for c in range(w) if grid[r][c] in (5, 6, 7, 8))
    if obj_cells < 1:
        errs.append("no object cells (5..8) found")
    return errs


def _build_obj(rng, k):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    return cells


def _rotate_about(cells, pr, pc, turns):
    out = []
    k = turns % 4
    for (r, c) in cells:
        y = r - pr
        x = c - pc
        if k == 0:
            ny, nx = y, x
        elif k == 1:
            ny, nx = x, -y
        elif k == 2:
            ny, nx = -y, -x
        else:
            ny, nx = -x, y
        out.append((pr + ny, pc + nx))
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        smax = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        smax = 6
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        smax = 5
    rng = ctx.draw_rng("layout")
    turns = int(overrides.get("token_turns", rng.randint(0, 3)))
    turns = max(0, min(3, turns))

    for _outer in range(200):
        g = full_grid(h, w, 0)
        # pivot somewhere interior so the object has room on all sides
        pr = rng.randint(2, h - 3)
        pc = rng.randint(2, w - 3)
        obj_n = rng.randint(2, smax)
        cells = _build_obj(rng, obj_n)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1
        sw = max(cs) - min(cs) + 1
        # max extent so all 4 rotations stay in bounds
        radius = max(sh, sw)
        # choose an offset of the object's top-left from the pivot
        # keep object near pivot but not on it
        placed = False
        for _ in range(60):
            dr = rng.randint(-(radius + 1), radius + 1)
            dc = rng.randint(-(radius + 1), radius + 1)
            base_cells = [(pr + dr + r - min(rs), pc + dc + c - min(cs))
                          for r, c in cells]
            # object must not cover the pivot
            if any(rc == (pr, pc) for rc in base_cells):
                continue
            # every quarter-turn must stay in bounds
            ok = True
            for t in range(4):
                rot = _rotate_about(base_cells, pr, pc, t)
                for (rr, cc) in rot:
                    if not (0 <= rr < h and 0 <= cc < w):
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue
            obj_color = rng.choice(list(OBJ_COLORS))
            for (rr, cc) in base_cells:
                g[rr][cc] = obj_color
            placed = True
            break
        if not placed:
            continue
        # token cell: color = turns+1, placed on a free bg cell not on object/pivot
        token_color = turns + 1
        tplaced = False
        for _ in range(200):
            tr = rng.randint(0, h - 1)
            tc = rng.randint(0, w - 1)
            if g[tr][tc] != 0 or (tr, tc) == (pr, pc):
                continue
            g[tr][tc] = token_color
            tplaced = True
            break
        if not tplaced:
            continue
        g[pr][pc] = 9
        return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    pr, pc = 4, 4
    g[pr][pc] = 9
    if name == "turns0_identity":
        # token color 1 -> 0 turns -> object stays put
        for (r, c) in [(1, 1), (1, 2), (2, 1)]:
            g[r][c] = 6
        g[6][6] = 1
        return g
    if name == "single_cell_obj":
        g[2][2] = 7
        g[6][6] = 3  # 2 turns
        return g
    if name == "obj_far":
        # object near a corner with a 3-turn token
        for (r, c) in [(0, 0), (0, 1), (1, 0)]:
            g[r][c] = 5
        g[8][8] = 4  # 3 turns
        return g
    return g
