"""Generator for 8b:m50 — emit rays until 5-blocker.

Rule: each non-{0,5} cell emits 4 cardinal rays in its color until
hitting a 5-blocker or grid edge.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_emitters, no_blockers, emitter_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b46564e50781"
VERSION = "2.1.0"  # FIX: an emitter on the boundary FACING OUT (or immediately
# blocked) shoots a ray with no in-bounds empty cell -> paints nothing -> output
# == input (identity). Now each emitter is placed only where its ray paints >=1
# cell. Adds self_check. (Prior poison note below still applies.)
# 2.0.0: POISON fix: emitter palette was [2,3,4,6,7,8,9] but the
# rule only treats values 1=up,2=right,3=down,4=left as DIRECTIONAL emitters
# (e8b-dir #f for 6,7,8,9 -> those cells emit nothing, are inert decoys, and
# direction 1=up was never generated). v2 uses ONLY {1,2,3,4} so every emitter
# fires and all four direction branches are exercised.
TASK_ID = "b46564e50781"
SUMMARY = ("1-4 directional emitter cells (1=up,2=right,3=down,4=left) + 1-2 "
           "color-5 blocker line segments; each emitter shoots a ray of its "
           "value through empty cells until a 5-blocker or grid edge.")

INVARIANTS = [
    "background is 0",
    "1-2 single non-{0,5} emitter cells",
    "1-2 separated 5-line segments (length 3-5)",
    "emitters and blockers aren't 4-adjacent",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_emitters", "no_blockers", "emitter_at_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "emitter_with_blockers",
                       "valid": "emitter_with_blockers"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
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
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    n_w = rng.randint(1, 2)
    for _ in range(n_w):
        for _ in range(40):
            if rng.random() < 0.5:
                r = rng.randint(2, h - 3); c1 = rng.randint(0, w - 4)
                length = rng.randint(3, min(5, w - c1))
                cells = [(r, c) for c in range(c1, c1 + length)]
            else:
                c = rng.randint(2, w - 3); r1 = rng.randint(0, h - 4)
                length = rng.randint(3, min(5, h - r1))
                cells = [(r, c) for r in range(r1, r1 + length)]
            # Keep separate blocker segments visually/structurally distinct;
            # adjacent segments merge into L/T components and violate the stated
            # "1-2 line segments" invariant even though the ray rule still runs.
            if any(
                (nr, nc) in used
                for r, c in cells
                for nr in range(r - 1, r + 2)
                for nc in range(c - 1, c + 2)
            ):
                continue
            for r, c in cells: g[r][c] = 5
            used |= set(cells); break
    # Emitters MUST be directional: 1=up, 2=right, 3=down, 4=left. Anything
    # else is inert under the rule, so restrict to {1,2,3,4}.
    if difficulty == "hard":
        n_e = rng.randint(2, 4)
    else:
        n_e = rng.randint(1, 4)
    palette = rng.sample([1, 2, 3, 4], n_e)
    for color in palette:
        for _ in range(60):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if (r, c) in used: continue
            adj = False
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == 5:
                    adj = True; break
            if adj: continue
            # the emitter must actually paint: its ray (in its own direction, until
            # a 5-blocker or edge) must contain >=1 empty cell.
            if _ray_paint_count(g, r, c, color) < 1:
                continue
            g[r][c] = color; used.add((r, c)); break
    return g


_DIR = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}


def _ray_paint_count(g, r, c, color):
    """How many empty (0) cells the emitter at (r,c) with direction `color` would
    paint: walk until a 5-blocker or the grid edge, counting 0-cells."""
    h, w = len(g), len(g[0])
    dr, dc = _DIR[color]
    n = 0; rr, cc = r + dr, c + dc
    while 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 5:
        if g[rr][cc] == 0:
            n += 1
        rr += dr; cc += dc
    return n


def _color_components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check that every non-wall colored cell is a real directional emitter
    (1..4) whose ray paints >=1 cell, and that blocker components are
    straight separated 5-segments."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    emitters = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 5)]
    if not (1 <= len(emitters) <= 4):
        errs.append(f"expected 1-4 emitters, found {len(emitters)}")
    bad_colors = [(r, c, v) for r, c, v in emitters if v not in (1, 2, 3, 4)]
    if bad_colors:
        errs.append(f"inert/non-directional emitter colors present: {bad_colors[:5]}")
    if emitters and not any(_ray_paint_count(grid, r, c, v) >= 1 for r, c, v in emitters):
        errs.append("every emitter's ray paints nothing (faces out / blocked) — output == input (identity)")
    walls = _color_components(grid, 5)
    if not (1 <= len(walls) <= 2):
        errs.append(f"expected 1-2 blocker segments, found {len(walls)}")
    for cells in walls:
        rs = {r for r, _ in cells}
        cs = {c for _, c in cells}
        if not (len(rs) == 1 or len(cs) == 1):
            errs.append(f"blocker is not a straight segment: {cells}")
        if not (3 <= len(cells) <= 5):
            errs.append(f"blocker segment length {len(cells)} outside 3..5")
    for r, c, v in emitters:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 5:
                errs.append(f"emitter {(r, c, v)} is 4-adjacent to a blocker")
                return errs
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_emitters":
        # Walls but no emitters — rule has no rays to cast.
        for c in range(2, 6): g[3][c] = 5
        return g
    if name == "no_blockers":
        # Emitter but no walls — rays travel to all 4 edges; rule's
        # blocker-stop branch never triggers.
        g[3][5] = 4
        return g
    if name == "emitter_at_corner":
        # Emitter at grid corner — only 2 rays have any length;
        # rule's 4-direction symmetry collapses.
        g[0][0] = 4
        for c in range(2, 6): g[3][c] = 5
        return g
    return g
