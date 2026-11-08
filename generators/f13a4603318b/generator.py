"""Generator for arc_puzzle_bank_fifteenth21:H103.

Rule: a 1/2/3/4 marker selects the sweep direction. A colored object is
translated in that direction until the next step would hit an 8 wall or the
grid boundary; the output is the union of all swept object positions plus the
walls.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f13a4603318b"
VERSION = "3.0.1"  # wall is a perpendicular barrier LINE (was single 8-cell) + bigger grids + random shapes
TASK_ID = "f13a4603318b"

SUMMARY = (
    "0-bg grid with: (a) one DIRECTION marker (color 1/2/3/4) at a corner — 1=up, "
    "2=down, 3=left, 4=right; (b) one connected OBJECT in a non-{0,1,2,3,4,8} color "
    "(3-6 cells); (c) a color-8 WALL LINE perpendicular to the sweep, placed so the "
    "object hits it after >=2 steps. Rule: translate the object in the marked "
    "direction until the next step would hit a wall or the boundary; output = union "
    "of all swept positions + the walls, marker removed. (Was: a single 8-cell wall.)"
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one direction marker in {1, 2, 3, 4} at a grid corner",
    "exactly one connected object in non-marker non-wall color (3-6 cells)",
    "≥1 color-8 wall positioned to block the sweep after ≥2 steps",
    "object can sweep ≥2 steps before being blocked",
]

AXES = {
    "grid_h": {"type": "int", "default": "rng by difficulty", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "rng by difficulty", "valid": "7..16"},
    "direction": {"type": "choice", "default": "rng 1/2/3/4", "valid": "1..4"},
    "object_color": {"type": "color", "default": "rng excluding 0..4,8", "valid": "5/6/7/9"},
    "shape": {"type": "choice", "default": "rng small connected motifs", "valid": "0..4"},
    "steps_before_block": {"type": "int", "default": "rng 2..available", "valid": "2..5"},
}

DIRECTIONS = {
    1: (-1, 0),
    2: (1, 0),
    3: (0, -1),
    4: (0, 1),
}

SHAPES = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
]


def _rand_shape(rng, k):
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _shape_size(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _place_wall(g, code, r0, c0, cells, steps, h, w, rng):
    """A color-8 barrier LINE perpendicular to the sweep, one cell beyond the
    object's leading edge after `steps` steps (blocks the whole leading edge)."""
    max_r = max(r for r, _ in cells); max_c = max(c for _, c in cells)
    if code in (3, 4):                                   # horizontal sweep -> vertical wall
        bc = c0 + max_c + steps + 1 if code == 4 else c0 - steps - 1
        lo = max(0, r0 - rng.randint(0, 2)); hi = min(h - 1, r0 + max_r + rng.randint(0, 2))
        for r in range(lo, hi + 1):
            if g[r][bc] == 0:
                g[r][bc] = 8
    else:                                                # vertical sweep -> horizontal wall
        br = r0 + max_r + steps + 1 if code == 2 else r0 - steps - 1
        lo = max(0, c0 - rng.randint(0, 2)); hi = min(w - 1, c0 + max_c + rng.randint(0, 2))
        for c in range(lo, hi + 1):
            if g[br][c] == 0:
                g[br][c] = 8


def _start_for_direction(rng, code, cells, h, w):
    shape_h, shape_w = _shape_size(cells)
    if code == 4:
        return rng.randint(1, h - shape_h - 1), 1
    if code == 3:
        return rng.randint(1, h - shape_h - 1), w - shape_w - 1
    if code == 2:
        return 1, rng.randint(1, w - shape_w - 1)
    return h - shape_h - 1, rng.randint(1, w - shape_w - 1)


def _max_steps_before_wall(code, r0, c0, cells, h, w):
    max_r = max(r for r, _ in cells)
    max_c = max(c for _, c in cells)
    if code == 4:
        return w - (c0 + max_c) - 2
    if code == 3:
        return c0 - 1
    if code == 2:
        return h - (r0 + max_r) - 2
    return r0 - 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 7, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 11, 16)
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 9, 12)
    code = ctx.draw_choice("direction", [1, 2, 3, 4])
    color = ctx.draw_color("object_color", exclude={0, 1, 2, 3, 4, 8})
    rng = ctx.draw_rng("layout")
    # mix curated + random connected shapes (3-6 cells)
    cells = (rng.choice(SHAPES) if rng.random() < 0.4
             else _rand_shape(rng, rng.randint(3, 6)))

    r0, c0 = _start_for_direction(rng, code, cells, h, w)
    max_steps = _max_steps_before_wall(code, r0, c0, cells, h, w)
    if max_steps < 2:
        cells = SHAPES[0]                      # small fallback shape -> guaranteed room
        r0, c0 = _start_for_direction(rng, code, cells, h, w)
        max_steps = _max_steps_before_wall(code, r0, c0, cells, h, w)
    steps = ctx.draw_int("steps_before_block", 2, max(2, max_steps))

    g = full_grid(h, w, 0)
    for r, c in cells:
        g[r0 + r][c0 + c] = color

    _place_wall(g, code, r0, c0, cells, steps, h, w, rng)

    marker_positions = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    for mr, mc in marker_positions:
        if g[mr][mc] == 0:
            g[mr][mc] = code
            return g
    raise ValueError("no free corner for direction marker")

def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); comp = []
            while stack:
                rr, cc = stack.pop(); comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(comp)
    return comps


def _sweep_steps_until_block(grid, marker, cells):
    h, w = len(grid), len(grid[0])
    dr, dc = DIRECTIONS[marker]
    steps = 0
    while True:
        nxt = [(r + (steps + 1) * dr, c + (steps + 1) * dc) for r, c in cells]
        if any(not (0 <= r < h and 0 <= c < w) or grid[r][c] == 8 for r, c in nxt):
            return steps
        steps += 1
        if steps > max(h, w):
            return steps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariant for the corner-marker sweep-to-wall examples."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    markers = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
               if grid[r][c] in DIRECTIONS and (r, c) in ((0,0), (0,w-1), (h-1,0), (h-1,w-1))]
    if len(markers) != 1:
        errs.append(f"expected exactly one corner direction marker, got {len(markers)}")
    wall_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if not wall_cells:
        errs.append("expected at least one color-8 wall cell")
    obj_colors = [c for c in sorted({v for row in grid for v in row}) if c not in (0, 1, 2, 3, 4, 8)]
    if len(obj_colors) != 1:
        errs.append(f"expected exactly one object color, got {obj_colors}")
        return errs
    comps = _components_of_color(grid, obj_colors[0])
    if len(comps) != 1:
        errs.append(f"expected one connected object component, got {len(comps)}")
        return errs
    obj = comps[0]
    if not (3 <= len(obj) <= 6):
        errs.append(f"object has {len(obj)} cells; expected 3..6")
    if markers:
        steps = _sweep_steps_until_block(grid, markers[0][2], obj)
        if steps < 2:
            errs.append(f"object can sweep only {steps} step(s); expected >=2")
    return errs
