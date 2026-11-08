"""Generator for arc_puzzle_bank_21_set16_bundle:hard_p05 — translate template by ref→target.

Rule: ref = single color-2 cell, target = single color-3 cell. Template = all
non-{0, 2, 3} cells. Translate template so its bbox top-left moves by
target - ref; paint over input.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_ref (no color-2 cell → rule's ref selector returns
nothing, vector undefined), no_target (no color-3 cell → rule's
target selector returns nothing), zero_vector (ref and target
coincide → vector is (0,0); rule's translation is identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a86bcdaad726"
VERSION = "1.1.1"
TASK_ID = "a86bcdaad726"

SUMMARY = "1 ref (color 2) + 1 target (color 3) + a small template shape; translate by ref→target."

INVARIANTS = [
    "background is 0",
    "exactly one color-2 cell (ref) and one color-3 cell (target)",
    "≥1 template cells in non-{0, 2, 3} colors",
    "template translated by (target - ref) lands within grid",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_ref", "no_target", "zero_vector")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 11..13", "valid": "10..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "ref_target_plus_template",
                          "valid": "ref_target_plus_template"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-2 (ref) and one color-3 (target); ≥1 template cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    template = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 2, 3)]
    if not twos and not threes:
        return errs  # degenerate (no_ref / no_target) — allowed
    if len(twos) != 1:
        errs.append(f"expected exactly 1 color-2 ref cell; got {len(twos)}")
    if len(threes) != 1:
        errs.append(f"expected exactly 1 color-3 target cell; got {len(threes)}")
    if not template:
        return errs  # degenerate — allowed (no template cells)
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 13, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        color = rng.choice([1, 4, 5, 6, 7, 8, 9])
        cells = [(0, 0)]
        seen = {(0, 0)}
        target_size = rng.randint(2, 4)
        while len(cells) < target_size:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if (nr, nc) not in seen:
                cells.append((nr, nc)); seen.add((nr, nc))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1
        sw = max(cs) - min(cs) + 1
        tr = rng.randint(0, h - sh)
        tc = rng.randint(0, w - sw)
        for r, c in cells:
            g[tr + r - min(rs)][tc + c - min(cs)] = color
        for _ in range(120):
            rr = rng.randint(0, h - 1); rc = rng.randint(0, w - 1)
            if g[rr][rc] != 0: continue
            dr = rng.randint(-3, 3); dc = rng.randint(-3, 3)
            if abs(dr) + abs(dc) < 2: continue
            tt_r = rr + dr; tt_c = rc + dc
            if not (0 <= tt_r < h and 0 <= tt_c < w):
                continue
            if g[tt_r][tt_c] != 0:
                continue
            new_tr = tr + dr
            new_tc = tc + dc
            if not (0 <= new_tr and new_tr + sh <= h and 0 <= new_tc and new_tc + sw <= w):
                continue
            g[rr][rc] = 2
            g[tt_r][tt_c] = 3
            return g
    raise ValueError("could not realize hard_p05 layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_ref":
        # No color-2 — rule's ref selector returns nothing; vector
        # undefined.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        g[7][9] = 3
        return g
    if name == "no_target":
        # No color-3 — rule's target selector returns nothing.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        g[7][9] = 2
        return g
    if name == "zero_vector":
        # Ref and target near-coincident — vector ≈ (0,0); rule's
        # translation is identity (template stays put).
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        g[6][7] = 2
        g[6][8] = 3   # adjacent — small vector
        return g
    return g
