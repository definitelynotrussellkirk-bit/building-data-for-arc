"""Generator for arc_puzzle_bank_twentyfirst21:H144.

Rooms are separated by color-8 walls.  Non-wall seed colors spread through
the open cells by shortest-path distance under the canonical rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "78c2e20ad0f8"
VERSION = "2.0.1"
TASK_ID = "78c2e20ad0f8"

SUMMARY = (
    "Grid (h, w~6-8) with: "
    "(a) COLOR-8 (cyan) "
    "OUTER WALL — full "
    "border of color 8; "
    "(b) OPTIONAL INTERIOR "
    "WALLS by LAYOUT: "
    "none (single room), "
    "vertical (full-height "
    "color-8 column at "
    "random interior col)"
    ", horizontal (full-"
    "width color-8 row), "
    "or cross (both a "
    "horizontal + vertical "
    "wall dividing into 4 "
    "rooms); (c) COLORED "
    "SEEDS — 2-3 seeds "
    "per room placed at "
    "random interior cells "
    "in DISTINCT non-{0, "
    "8} colors. Rule (BFS "
    "FLOOD: EACH 0-CELL "
    "GOES TO ITS NEAREST "
    "SEED'S COLOR, "
    "BLOCKED BY 8-WALLS): "
    "For EACH bg-0 cell "
    "in any room: compute "
    "BFS DISTANCES "
    "(through 0-cells "
    "blocked by 8-walls) "
    "to ALL SEEDS in "
    "that room. ASSIGN "
    "the cell to its "
    "NEAREST seed's "
    "color. PAINT it "
    "with that color. "
    "Seeds and walls "
    "stay. Net: each "
    "room partitions "
    "into Voronoi-like "
    "regions colored by "
    "nearest seed."
)

INVARIANTS = [
    "background/open cells are 0",
    "walls are color 8 and include the outer border",
    "each room contains colored seeds and at least one zero to be filled",
]

AXES = {
    "grid_h": {"type": "int", "default": "rng 6..8", "valid": "5..10"},
    "grid_w": {"type": "int", "default": "rng 6..8", "valid": "5..10"},
    "layout": {"type": "choice", "default": "rng none|vertical|horizontal|cross"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: outer border is all color 8, ≥1 non-8 seed inside, ≥1 background (0) cell inside."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Outer border must be all color 8
    border_not_8 = []
    for r in range(h):
        for c in range(w):
            if (r == 0 or r == h-1 or c == 0 or c == w-1) and grid[r][c] != 8:
                border_not_8.append((r, c))
    if border_not_8:
        errs.append(f"{len(border_not_8)} border cell(s) not color 8 (e.g. {border_not_8[:2]})")
    # Must have ≥1 non-{0,8} seed inside
    seeds = [(r, c) for r in range(1, h-1) for c in range(1, w-1)
             if grid[r][c] not in (0, 8)]
    if not seeds:
        errs.append("no non-8 seed cells in the interior")
    # Must have ≥1 background cell inside (room to fill)
    bg_inside = any(grid[r][c] == 0 for r in range(1, h-1) for c in range(1, w-1))
    if not bg_inside:
        errs.append("no background (0) cells in interior (room already full)")
    return errs


def _rect_cells(r1, c1, r2, c2):
    return [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]


def _seed_room(grid, cells, rng, palette):
    count = min(len(cells) - 1, rng.randint(2, 3))
    if count <= 0:
        return
    chosen = rng.sample(cells, count)
    colors = rng.sample(palette, count)
    for (r, c), color in zip(chosen, colors):
        grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 6, 8)
    w = ctx.draw_int("grid_w", 6, 8)
    rng = ctx.draw_rng("layout_rng")

    requested = overrides.get("layout")
    if requested is not None:
        if requested not in {"none", "vertical", "horizontal", "cross"}:
            raise ValueError("layout override must be none, vertical, horizontal, or cross")
        layout = requested
    else:
        choices = ["none", "vertical", "horizontal"]
        if h >= 7 and w >= 7:
            choices.append("cross")
        layout = rng.choice(choices)

    grid = full_grid(h, w, 8)
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            grid[r][c] = 0

    rooms = [(1, 1, h - 2, w - 2)]
    if layout == "vertical":
        wall_c = rng.randint(2, w - 3)
        for r in range(1, h - 1):
            grid[r][wall_c] = 8
        rooms = [(1, 1, h - 2, wall_c - 1), (1, wall_c + 1, h - 2, w - 2)]
    elif layout == "horizontal":
        wall_r = rng.randint(2, h - 3)
        for c in range(1, w - 1):
            grid[wall_r][c] = 8
        rooms = [(1, 1, wall_r - 1, w - 2), (wall_r + 1, 1, h - 2, w - 2)]
    elif layout == "cross":
        wall_r = rng.randint(2, h - 3)
        wall_c = rng.randint(2, w - 3)
        for c in range(1, w - 1):
            grid[wall_r][c] = 8
        for r in range(1, h - 1):
            grid[r][wall_c] = 8
        rooms = [
            (1, 1, wall_r - 1, wall_c - 1),
            (1, wall_c + 1, wall_r - 1, w - 2),
            (wall_r + 1, 1, h - 2, wall_c - 1),
            (wall_r + 1, wall_c + 1, h - 2, w - 2),
        ]

    palette = [1, 2, 3, 4, 5, 6, 7, 9]
    for box in rooms:
        cells = _rect_cells(*box)
        if len(cells) >= 2:
            _seed_room(grid, cells, rng, palette)

    return grid
