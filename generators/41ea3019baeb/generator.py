"""Generator for arc_puzzle_bank_21_set10_s:S10_H1 — laser-bounce trail with mirrors.

Rule: each color-2 emitter shoots a ray; mirrors (5, 6, 7) deflect; trail
painted color 8 on bg cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_emitters,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_emitters, no_mirrors, emitter_at_mirror.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "41ea3019baeb"
VERSION = "1.2.0"  # keep every sampled emitter active: not on right edge and not immediately blocked
TASK_ID = "41ea3019baeb"

SUMMARY = "1-2 color-2 emitters + 1-3 mirrors (5, 6, or 7)."

INVARIANTS = [
    "background is 0",
    "1-2 color-2 emitter cells",
    "1-3 mirror cells in colors {5, 6, 7}",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_emitters", "no_mirrors", "emitter_at_mirror")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_emitters":     {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "n_mirrors":      {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "emitters_plus_mirrors",
                       "valid": "emitters_plus_mirrors"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_emitters|no_mirrors|emitter_at_mirror"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 9, 9)
        n_emitters = ctx.draw_int("n_emitters", 1, 1)
        n_mirrors = ctx.draw_int("n_mirrors", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        n_emitters = ctx.draw_int("n_emitters", 2, 2)
        n_mirrors = ctx.draw_int("n_mirrors", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        n_emitters = ctx.draw_int("n_emitters", 1, 2)
        n_mirrors = ctx.draw_int("n_mirrors", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    emitters = []
    reserved = set()
    for _ in range(n_emitters):
        for _t in range(80):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 2)  # the canonical beam starts by moving right
            if (g[r][c] != 0 or g[r][c + 1] != 0
                    or (r, c) in reserved or (r, c + 1) in reserved):
                continue
            g[r][c] = 2
            emitters.append((r, c))
            reserved.add((r, c + 1))  # guarantee at least one paintable ray cell
            break
    for _ in range(n_mirrors):
        for _t in range(80):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] != 0 or (r, c) in reserved:
                continue
            g[r][c] = rng.choice([5, 6, 7])
            break
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not isinstance(grid, list) or not all(isinstance(row, list) for row in grid):
        return ["grid is not a non-empty 2D list"]
    h = len(grid)
    w = len(grid[0]) if h else 0
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    emitters = []
    mirrors = []
    bad = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 2:
                emitters.append((r, c))
            elif v in (5, 6, 7):
                mirrors.append((r, c, v))
            elif v != 0:
                bad.append((r, c, v))
    if bad:
        errors.append(f"unexpected non-background colors outside emitters/mirrors: {bad[:3]}")
    if not (1 <= len(emitters) <= 2):
        errors.append(f"expected 1-2 color-2 emitters, got {len(emitters)}")
    if not (1 <= len(mirrors) <= 3):
        errors.append(f"expected 1-3 mirror cells, got {len(mirrors)}")
    if len(set(emitters)) != len(emitters):
        errors.append("duplicate emitter coordinates")
    inactive = [pos for pos in emitters if not _ray_paints(grid, *pos)]
    if inactive:
        errors.append(f"emitter(s) have no paintable ray cell: {inactive}")
    return errors


def _turn(v, dr, dc):
    if v == 6:
        if (dr, dc) == (0, 1):
            return (-1, 0)
        if (dr, dc) == (0, -1):
            return (1, 0)
        if (dr, dc) == (-1, 0):
            return (0, 1)
        return (0, -1)
    if v == 7:
        if (dr, dc) == (0, 1):
            return (1, 0)
        if (dr, dc) == (0, -1):
            return (-1, 0)
        if (dr, dc) == (-1, 0):
            return (0, -1)
        return (0, 1)
    return (dr, dc)


def _ray_paints(grid, r, c):
    h, w = len(grid), len(grid[0])
    rr, cc, dr, dc = r, c, 0, 1
    fuel = h * w * 8
    while fuel > 0:
        nr, nc = rr + dr, cc + dc
        if not (0 <= nr < h and 0 <= nc < w):
            return False
        v = grid[nr][nc]
        if v == 5 or (v != 0 and v not in (6, 7)):
            return False
        if v == 0:
            return True
        dr, dc = _turn(v, dr, dc)
        rr, cc = nr, nc
        fuel -= 1
    return False


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_emitters":
        # mirrors only, no emitters → no rays to trace
        g[2][3] = 5
        g[5][7] = 6
        return g
    if name == "no_mirrors":
        # emitters only, no mirrors → ray trail is undefined direction
        g[3][3] = 2
        g[5][7] = 2
        return g
    if name == "emitter_at_mirror":
        # emitter and mirror at same logical cell impossible → place adjacent which makes ray immediately deflected with no straight segment
        g[3][3] = 2
        g[3][4] = 5  # mirror immediately to the right of emitter
        return g
    return g
