"""Generator for 16b:m108 — apply gravity inside vertical chambers.

Rule: vertical full-height 8-walls divide the grid into chambers.
Inside each chamber, all non-zero non-wall cells fall to the bottom row.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_walls, no_pebbles, all_in_bottom_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b9ada70e7181"
VERSION = "2.2.0"  # 2.1.0->2.2.0: construct an explicit non-palindromic
# multi-pebble column in every ordinary draw, closing the retained reverse-stack
# teaching ambiguity; dimension overrides now honor the documented full range.
TASK_ID = "b9ada70e7181"
SUMMARY = (
    "0-bg grid (h×w, ~7-11 by ~10-16) with 2-3 FULL-HEIGHT "
    "vertical color-8 (cyan) WALL columns dividing the grid "
    "into chambers. Each chamber has 2-5 SCATTERED non-zero "
    "non-8 'pebble' cells at various rows (above the bottom). "
    "Rule: walls preserved. For each non-wall column "
    "independently, collect all non-zero non-8 values top-to-"
    "bottom. Stack them at the BOTTOM of the column with the "
    "topmost-original at the top of the stack. Other cells "
    "become 0. Walls divide gravity into chamber-local "
    "computation (each column processes alone)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-3 full-height color-8 wall columns",
    "each positive-width chamber has 2-5 non-bg non-8 pebble cells (not on bottom row)",
    "wall columns are separated by at least one non-wall chamber column",
    "at least one column has a non-palindromic multi-pebble stack exposing stable order",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_pebbles", "all_in_bottom_row")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "vertical_chambers",
                       "valid": "vertical_chambers"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..7", "valid": "3..9"},
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
    # Explicit overrides use the full documented domain while ordinary draws keep
    # their original difficulty distributions.
    if "grid_h" in overrides:
        h = ctx.draw_int("grid_h", 6, 12)
    elif difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
    if "grid_w" in overrides:
        w = ctx.draw_int("grid_w", 9, 16)
    elif difficulty == "easy":
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        w = ctx.draw_int("grid_w", 13, 16)
    else:
        w = ctx.draw_int("grid_w", 10, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_walls = rng.randint(2, 3)
    wall_candidates = list(range(2, w - 2))
    for _ in range(80):
        walls = sorted(rng.sample(wall_candidates, n_walls))
        if all(b - a >= 2 for a, b in zip(walls, walls[1:])):
            break
    else:
        # Deterministic spread fallback for the smallest/easiest grids.
        step = max(2, (w - 4) // max(1, n_walls))
        walls = []
        c = 2
        while len(walls) < n_walls and c < w - 2:
            walls.append(c)
            c += step
        while len(walls) < n_walls:
            cand = w - 3 - 2 * (n_walls - len(walls) - 1)
            if all(abs(cand - x) >= 2 for x in walls):
                walls.append(cand)
            else:
                cand -= 1
                walls.append(cand)
        walls = sorted(walls[:n_walls])
    for c in walls:
        for r in range(h):
            g[r][c] = 8
    edges = [-1] + walls + [w]
    chambers = [(left + 1, right - 1) for left, right in zip(edges, edges[1:])
                if right - left > 1]
    palette_pool = [1, 2, 3, 4, 5, 6, 7, 9]

    # The first and last chambers are always at least two columns wide under the
    # wall-placement constraints. Randomly choose one as a stable-order witness,
    # reserve exactly two cells in one column, and give them distinct colors.
    # Keeping later placements out of that column prevents an accidental
    # palindrome from reviving the reverse-stack shortcut.
    witness_index = rng.choice([0, len(chambers) - 1])
    witness_lo, witness_hi = chambers[witness_index]
    witness_col = rng.randint(witness_lo, witness_hi)
    witness_rows = sorted(rng.sample(range(h - 1), 2))
    witness_colors = rng.sample(palette_pool, 2)

    for index, (c_lo, c_hi) in enumerate(chambers):
        capacity = (c_hi - c_lo + 1) * (h - 1)
        n_pebbles = rng.randint(2, min(5, capacity))
        reserved: list[tuple[int, int, int]] = []
        forbidden: set[tuple[int, int]] = set()
        if index == witness_index:
            reserved = [
                (witness_rows[0], witness_col, witness_colors[0]),
                (witness_rows[1], witness_col, witness_colors[1]),
            ]
            forbidden.update((r, witness_col) for r in range(h - 1))
            n_pebbles = max(n_pebbles, 2)
        for r, c, color in reserved:
            g[r][c] = color
        available = [
            (r, c)
            for r in range(h - 1)
            for c in range(c_lo, c_hi + 1)
            if (r, c) not in forbidden and g[r][c] == 0
        ]
        remaining = n_pebbles - len(reserved)
        if remaining > len(available):
            # This cannot occur for the documented dimensions, but fail loudly
            # rather than silently weakening the order witness.
            raise ValueError("insufficient chamber capacity after reserving order witness")
        for r, c in rng.sample(available, remaining):
            g[r][c] = rng.choice(palette_pool)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 12
    g = full_grid(h, w, 0)
    if name == "no_walls":
        # Pebbles but no 8-walls — chambers are undefined, gravity has
        # no per-chamber boundary to respect.
        g[2][3] = 4; g[3][7] = 6; g[1][9] = 7
        return g
    if name == "no_pebbles":
        # 8-walls but no pebbles in any chamber — rule has nothing
        # to drop.
        for r in range(h): g[r][3] = 8; g[r][7] = 8
        return g
    if name == "all_in_bottom_row":
        # Walls + pebbles already on the bottom row — gravity is a
        # no-op, rule's effect is invisible.
        for r in range(h): g[r][3] = 8; g[r][7] = 8
        g[h - 1][1] = 4; g[h - 1][5] = 6; g[h - 1][9] = 7
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for vertical-chamber gravity inputs."""
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid is empty or not rectangular"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows have inconsistent widths"]
    walls = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if not (2 <= len(walls) <= 3):
        errs.append(f"expected 2..3 full-height 8-wall columns, got {walls}")
    if any(b - a < 2 for a, b in zip(walls, walls[1:])):
        errs.append(f"adjacent wall columns create a zero-width chamber: {walls}")
    edges = [-1] + walls + [w]
    for left, right in zip(edges, edges[1:]):
        if right - left <= 1:
            continue
        pebbles = [(r, c) for r in range(h) for c in range(left + 1, right)
                   if grid[r][c] not in (0, 8)]
        if not (2 <= len(pebbles) <= 5):
            errs.append(
                f"chamber {left + 1}..{right - 1} needs 2..5 pebbles, got {len(pebbles)}"
            )
        if any(r == h - 1 for r, _c in pebbles):
            errs.append("pebble appears on the bottom row before gravity")
        if any(grid[r][c] == 8 for r, c in pebbles):
            errs.append("pebble list included wall color 8")
    stacks = []
    for c in range(w):
        values = [grid[r][c] for r in range(h) if grid[r][c] not in (0, 8)]
        if len(values) >= 2 and values != list(reversed(values)):
            stacks.append((c, values))
    if not stacks:
        errs.append("no non-palindromic multi-pebble column exposes stable stack order")
    return errs
