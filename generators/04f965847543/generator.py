"""Generator for arc_puzzle_bank_thirteenth21:E89.

Combinatorial axes (8): grid_h, grid_w, palette_kind, pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, axis_aligned, midpoint_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "04f965847543"
VERSION = "2.1.1"
TASK_ID = "04f965847543"

SUMMARY = (
    "0-bg grid with N (2-5) pairs of same-color cells positioned on a "
    "DIAGONAL 2-step apart (one cell at (r, c) and another at (r±2, "
    "c±2), with the (r±1, c±1) midpoint being 0). Pairs use distinct "
    "colors and are separated (1-cell buffer) so the rule's diagonal-"
    "midpoint test doesn't accidentally fire on other cell triples. "
    "Rule: scan every cell. If g[r][c] == g[r+2][c+2] (non-zero) AND "
    "g[r+1][c+1] == 0, set g[r+1][c+1] = g[r][c]. Same for "
    "anti-diagonal: g[r][c] == g[r+2][c-2] non-zero AND g[r+1][c-1] "
    "== 0 → fill."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 pairs of same-color cells positioned diagonally 2-step apart",
    "midpoint cells of each pair are 0 in input",
    "pairs are spaced ≥1 cell apart to avoid accidental triples",
]

# Rivals: 'fill between any 2-apart pair' refuted by axis-aligned
# pairs that stay dots. 'overwrite the midpoint' refuted by occupied
# midpoints that stay. 3 demos incl. >=1 near-miss pair.
DEGENERATE_TEXTURES = ("no_pairs",)
HELPFUL_TEXTURES = ("plain", "axis_aligned_decoy", "filled_mid_decoy")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "grid_w":  {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "pairs":   {"type": "int", "default": "rng 2..4", "valid": "1..9",
                "doc": "Diagonal pairs whose midpoints fill."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|axis_aligned_decoy|filled_mid_decoy|no_pairs",
                "doc": "Adds one near-miss pair the rule must skip."},
}


def _free(g, cells):
    h, w = len(g), len(g[0])
    for r, c in cells:
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if g[rr][cc] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "axis_aligned_decoy", "filled_mid_decoy"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("pairs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("pairs", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(9, target))
    placed = 0
    for _ in range(140):
        if placed >= target:
            break
        dr = rng.choice([-2, 2])
        dc = rng.choice([-2, 2])
        r = rng.randint(max(0, -dr), min(h - 1, h - 1 - dr))
        c = rng.randint(max(0, -dc), min(w - 1, w - 1 - dc))
        cells = [(r, c), (r + dr, c + dc)]
        if _free(g, cells):
            color = colors[placed % len(colors)]
            for rr, cc in cells:
                g[rr][cc] = color
            placed += 1

    # one near-miss pair the rule must NOT fill
    spare = [v for v in range(1, 10) if v not in colors[:placed]]
    if texture == "axis_aligned_decoy" and spare:
        for _ in range(60):
            if rng.random() < 0.5:
                r, c = rng.randint(0, h - 1), rng.randint(0, w - 3)
                cells = [(r, c), (r, c + 2)]
                mid = (r, c + 1)
            else:
                r, c = rng.randint(0, h - 3), rng.randint(0, w - 1)
                cells = [(r, c), (r + 2, c)]
                mid = (r + 1, c)
            if _free(g, cells + [mid]):
                for rr, cc in cells:
                    g[rr][cc] = spare[0]
                break
    elif texture == "filled_mid_decoy" and len(spare) >= 2:
        for _ in range(60):
            dr = rng.choice([-2, 2])
            dc = rng.choice([-2, 2])
            r = rng.randint(max(0, -dr), min(h - 1, h - 1 - dr))
            c = rng.randint(max(0, -dc), min(w - 1, w - 1 - dc))
            cells = [(r, c), (r + dr, c + dc)]
            if _free(g, cells):
                for rr, cc in cells:
                    g[rr][cc] = spare[0]
                g[r + dr // 2][c + dc // 2] = spare[1]  # midpoint occupied
                break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=2 diagonal pairs: same-color cells at distance 2 diagonally with empty midpoint."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    pairs = 0
    seen_cells: set = set()
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0 or (r, c) in seen_cells:
                continue
            for dr, dc in ((2, 2), (2, -2)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == v:
                    mr, mc = r + dr // 2, c + dc // 2
                    if grid[mr][mc] == 0:
                        pairs += 1
                        seen_cells.add((r, c))
                        seen_cells.add((nr, nc))
    errors = []
    if pairs < 2:
        errors.append(f"found {pairs} qualifying diagonal pair(s); need >=2")
    return errors


def _draw_from_degenerate(name, ctx):
    """no_pairs — singletons only: nothing fills. rng-varied.
    (axis_aligned / midpoint_filled were PROMOTED to helpful decoys.)"""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 9)
    w = ctx.draw_int("grid_w", 7, 10)
    g = full_grid(h, w, 0)
    for color in rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], rng.randint(2, 3)):
        g[rng.randrange(h)][rng.randrange(w)] = color
    return g
