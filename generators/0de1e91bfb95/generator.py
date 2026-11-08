"""Generator for arc_puzzle_bank_21_set10_s:S10_M1 — laser beam from 2-seed, deflected by 6/7 mirrors, stopped by 5-wall.

Rule: each 2-cell shoots a beam to the right. The beam paints 8 on
0-cells. On hitting a 6-mirror it turns left-of-incoming, on 7 it
turns right-of-incoming, on a 5-wall (or any other non-empty cell)
it stops.

Combinatorial axes (8): grid_h, grid_w, palette_kind, mirror_kind,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seed, no_mirror, no_wall.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0de1e91bfb95"
VERSION = "2.1.1"  # 2.0.0->2.1.0: optional 2nd mirror -> double-bend beam paths (was always single bend)
TASK_ID = "0de1e91bfb95"
SUMMARY = (
    "0-bg grid (h~7-10, w~"
    "9-12) with: (a) ONE "
    "COLOR-2 SEED at (sr, "
    "1) — left edge "
    "interior row sr ∈ [2, "
    "h-3]; (b) ONE MIRROR "
    "at (sr, mirror_c) "
    "with mirror_c ∈ [sr+3"
    ", w-3] — color either "
    "6 (UP-FROM-RIGHT "
    "reflector) or 7 "
    "(DOWN-FROM-RIGHT "
    "reflector); (c) ONE "
    "COLOR-5 WALL at "
    "(wall_r, mirror_c) "
    "placed in the column "
    "the beam will enter "
    "after deflection. "
    "Rule (LASER BEAM FROM "
    "2-SEED, DEFLECTED BY "
    "6/7 MIRRORS, STOPPED "
    "BY 5-WALL): from the "
    "2-seed at (sr, 1), "
    "cast a beam to the "
    "RIGHT. PAINT every "
    "0-cell along the "
    "beam's path with "
    "COLOR 8. When the "
    "beam hits a 6-mirror"
    ": turn LEFT-OF-"
    "INCOMING (right → "
    "up). When it hits a "
    "7-mirror: turn RIGHT-"
    "OF-INCOMING (right → "
    "down). When it hits "
    "a 5-WALL or grid "
    "edge, the beam STOPS. "
    "Net: a cyan-painted "
    "trajectory traces "
    "through the optical "
    "system from the "
    "seed."
)

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly 1 color-2 seed; >=1 mirror (6 or 7); >=1 color-5 wall."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    mirrors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (6, 7)]
    walls = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if len(seeds) != 1:
        errors.append(f"expected exactly 1 color-2 seed, found {len(seeds)}")
    if not mirrors:
        errors.append("no mirror cells (color 6 or 7)")
    if not walls:
        errors.append("no color-5 wall cell (beam would never stop)")
    return errors


INVARIANTS = [
    "background is 0",
    "exactly one 2-seed",
    "1-2 mirror cells (color 6 or 7) in the 2's row OR in a column the beam will hit after deflection",
    "exactly one 5-wall placed where the beam terminates",
    "beam length ≥1 before hitting the first mirror or wall",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seed", "no_mirror", "no_wall")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "mirror_kind":    {"type": "int", "default": "rng 6|7", "valid": "6..7"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "seed_mirror_wall",
                       "valid": "seed_mirror_wall"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    seed_r = rng.randint(2, h - 3)
    seed_c = 1
    g[seed_r][seed_c] = 2
    mirror_kind = rng.choice([6, 7])  # 6 turns up-from-right, 7 turns down-from-right
    mirror_c = rng.randint(seed_c + 3, w - 3)
    g[seed_r][mirror_c] = mirror_kind
    # after the first bend the beam travels vertically in column mirror_c:
    #   6 -> up (dr=-1), 7 -> down (dr=+1)
    vdir = -1 if mirror_kind == 6 else 1

    # Optionally add a SECOND mirror in the vertical path, bending the
    # beam horizontally again, then terminate with a wall.
    want_second = rng.random() < 0.6
    placed_second = False
    if want_second:
        # rows available in column mirror_c going in vdir (with room for
        # at least one beam cell before the 2nd mirror and a wall after).
        if vdir == -1:
            r_choices = list(range(1, seed_r - 1))
        else:
            r_choices = list(range(seed_r + 2, h - 1))
        rng.shuffle(r_choices)
        for m2_r in r_choices:
            m2_kind = rng.choice([6, 7])
            # incoming dir (vdir,0). 6: up->right / down->left.
            # 7: up->left / down->right. Compute outgoing horizontal dir.
            if m2_kind == 6:
                hdir = 1 if vdir == -1 else -1
            else:
                hdir = -1 if vdir == -1 else 1
            # need at least one column step in hdir then a wall in bounds
            if hdir > 0:
                max_dist = (w - 1) - mirror_c
            else:
                max_dist = mirror_c
            if max_dist < 2:
                continue
            wall_c = mirror_c + hdir * rng.randint(2, max_dist)
            # ensure the horizontal stretch m2_r row between mirror_c and
            # wall_c is empty (it is — fresh grid) and wall_c != mirror_c
            g[m2_r][mirror_c] = m2_kind
            g[m2_r][wall_c] = 5
            placed_second = True
            break

    if not placed_second:
        # single-bend: wall in the vertical path
        if vdir == -1:
            wall_r = rng.randint(0, seed_r - 1)
        else:
            wall_r = rng.randint(seed_r + 1, h - 1)
        g[wall_r][mirror_c] = 5
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_seed":
        # mirrors and wall but no 2-seed → no beam to fire
        g[3][5] = 6; g[1][5] = 5
        return g
    if name == "no_mirror":
        # seed + wall but no mirror → beam goes straight (still defined but no deflection)
        g[3][1] = 2
        g[3][7] = 5
        return g
    if name == "no_wall":
        # seed + mirror but no wall → beam never terminates
        g[3][1] = 2
        g[3][5] = 6
        return g
    return g
