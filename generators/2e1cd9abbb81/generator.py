"""Generator for arc_puzzle_bank_21_set4:S4_M7 — T shapes to pluses.

Rule: each color-3 four-cell T gets its missing arm filled to make a plus.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_shapes, non_t_shape, single_shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2e1cd9abbb81"
VERSION = "2.2.0"  # add executable T-shape/missing-arm self_check
TASK_ID = "2e1cd9abbb81"

SUMMARY = (
    "0-bg grid (h~10-13, w~12-16) with 1-3 ISOLATED color-3 "
    "(green) 4-cell T-tetrominoes, each one of 4 orientations "
    "(T-up, T-down, T-left, T-right). Each T has the missing "
    "plus arm in-bounds. Rule: detect each T-shaped color-3 "
    "object, identify which of the 4 plus-arms is missing "
    "(the cell opposite the existing stem), and paint that "
    "missing cell with color 3 to complete a 5-cell PLUS."
)

INVARIANTS = [
    "background is 0",
    "each color-3 object is exactly one of the four 4-cell T shapes",
    "each T has room for the missing plus arm in-bounds",
    "T objects are separated so they remain distinct",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shapes", "non_t_shape", "single_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_shapes":       {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "str", "default": "1 (color 3)", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "scattered_isolated",
                       "valid": "scattered_isolated"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_shapes|non_t_shape|single_shape"},
}


SHAPES = [
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (1, 0), (1, 1), (2, 0)],
    [(0, 1), (1, 0), (1, 1), (2, 1)],
]


def _clear(g, r0, c0, cells):
    h, w = len(g), len(g[0])
    rs = [r0 + r for r, _ in cells]
    cs = [c0 + c for _, c in cells]
    if min(rs) < 1 or min(cs) < 1 or max(rs) >= h - 1 or max(cs) >= w - 1:
        return False
    for r in range(min(rs) - 1, max(rs) + 2):
        for c in range(min(cs) - 1, max(cs) + 2):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 16, 18)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
    rng = ctx.draw_rng("layout")
    n_shapes = rng.randint(1, 3)
    # Up to 3 T-tetrominoes (each ≈3×3 with a 1-cell `_clear` buffer) must all
    # land. An early T can wedge a later one out → its 80 per-shape tries fail and
    # the for/else raises (~1/300 None). Per-shape retry can't reposition the
    # earlier Ts, so reset-and-retry the whole layout: n_shapes is drawn ONCE up
    # front so it's fixed, and outer attempt 0 replays the same per-shape
    # choice+placement, so every first-pass-success seed returns byte-identically;
    # only the previously-wedged seeds resample. Early-placement-wedging class
    # (17b0b2791dd2/13507b4f7614).
    for _outer in range(60):
        g = full_grid(h, w, 0)
        ok = True
        for _ in range(n_shapes):
            cells = rng.choice(SHAPES)
            for _attempt in range(80):
                r0 = rng.randint(1, h - 4)
                c0 = rng.randint(1, w - 4)
                if _clear(g, r0, c0, cells):
                    for dr, dc in cells:
                        g[r0 + dr][c0 + dc] = 3
                    break
            else:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place T shape")


def _draw_from_degenerate(name, rng):
    h, w = 11, 13
    g = full_grid(h, w, 0)
    if name == "no_shapes":
        # Empty grid — no T to extend into a plus.
        return g
    if name == "non_t_shape":
        # 2x2 squares — rule's T-match never fires, so the rule is a no-op.
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[2 + dr][2 + dc] = 3
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            g[6 + dr][7 + dc] = 3
        return g
    if name == "single_shape":
        # Just one T — minimal context.
        for dr, dc in SHAPES[0]:
            g[3 + dr][4 + dc] = 3
        return g
    return g


def _components(grid, color=3):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = [(r, c)]; seen.add((r, c)); cells = []
            for rr, cc in q:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc)); q.append((nr, nc))
            comps.append(cells)
    return comps


_SHAPE_SETS = {frozenset(s) for s in SHAPES}


def _norm(cells):
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _missing_plus_arm(cells):
    cells = set(cells)
    for r, c in cells:
        arms = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        present = [p for p in arms if p in cells]
        missing = [p for p in arms if p not in cells]
        if len(present) == 3 and len(missing) == 1:
            return missing[0]
    return None


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in (0, 3) for row in grid for v in row):
        errs.append("T-shape input should contain only colors 0 and 3")
    comps = _components(grid, 3)
    if not (1 <= len(comps) <= 3):
        errs.append(f"expected 1..3 isolated T components, found {len(comps)}")
    h, w = len(grid), len(grid[0])
    for comp in comps:
        if len(comp) != 4 or _norm(comp) not in _SHAPE_SETS:
            errs.append("a color-3 component is not a 4-cell T tetromino")
            continue
        miss = _missing_plus_arm(comp)
        if miss is None:
            errs.append("could not identify missing plus arm for a T")
        else:
            r, c = miss
            if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0:
                errs.append("missing plus-arm cell is not blank and in bounds")
    return errs
