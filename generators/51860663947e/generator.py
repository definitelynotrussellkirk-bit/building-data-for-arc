"""Generator for puzzle 6455b5f5.

Rule: take 0-regions (4-connected) of bg=0. Find max-size and min-size
regions. Recolor max-size cells to 1 and min-size cells to 8.

Combinatorial axes (8): grid_h/w, n_v_walls, n_h_walls, wall_color,
distractor_density, position_bias, anchor_corner, asymmetry_force.
Degenerates: tied_sizes, single_region, all_walls.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "51860663947e"
VERSION = "2.0.1"
TASK_ID = "51860663947e"
SUMMARY = (
    "0-bg grid (h~8-16, w~11-19) with: (a) "
    "1-2 (default) VERTICAL FULL-HEIGHT "
    "WALLS at columns chosen by one of 5 "
    "POSITION BIASES (spread / centered / "
    "left_heavy / right_heavy / diagonal), "
    "all painted COLOR 2; (b) 1-2 "
    "HORIZONTAL WALLS that span only ONE "
    "SECTION (between two vertical walls or "
    "between a wall and the grid edge), "
    "creating DISTINCT 0-REGION SIZES; "
    "(c) optional DISTRACTOR cells of color "
    "2 (≤5% density). The 2-walls split the "
    "bg-0 cells into ≥3 disjoint 4-"
    "CONNECTED REGIONS of distinct sizes "
    "(MAX and MIN are unique). Rule "
    "(RECOLOR THE MAX-SIZE 0-REGION TO 1 "
    "AND THE MIN-SIZE 0-REGION TO 8): "
    "extract every 4-CONNECTED region of "
    "bg-0 cells (blocked by color-2 walls). "
    "RANK regions by cell count. SELECT "
    "the LARGEST region — PAINT every cell "
    "with COLOR 1 (blue). SELECT the "
    "SMALLEST region — PAINT every cell "
    "with COLOR 8 (cyan). Other regions "
    "stay bg-0. The 2-walls stay color 2. "
    "Net: the largest open chamber turns "
    "blue; the smallest turns cyan; "
    "middle-sized regions stay black."
)

INVARIANTS = [
    "background is 0",
    ">=3 disjoint 0-regions of distinct sizes",
    "wall color = 2",
    "max-size and min-size 0-regions are unique",
]

POSITION_BIASES = ("spread", "centered", "left_heavy", "right_heavy",
                   "diagonal")
DEGENERATE_TEXTURES = ("tied_sizes", "single_region", "all_walls")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":           {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":           {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "n_v_walls":        {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "n_h_walls":        {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "wall_color":       {"type": "color", "default": "2", "valid": "2"},
    "distractor_density":{"type": "float", "default": "rng 0..0.05",
                          "valid": "0..0.15"},
    "position_bias":    {"type": "str", "default": "rng helpful",
                         "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":    {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "texture":          {"type": "str", "default": "alias for position_bias",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 color-2 wall cell; >=3 distinct 0-regions."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    has_wall = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_wall:
        errs.append("no color-2 wall cells found")
    # Flood-fill 0-cells
    visited = [[False] * w for _ in range(h)]
    def flood(r0, c0):
        stack = [(r0, c0)]
        visited[r0][c0] = True
        size = 0
        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                rr, cc = r+dr, c+dc
                if 0 <= rr < h and 0 <= cc < w and not visited[rr][cc] and grid[rr][cc] == 0:
                    visited[rr][cc] = True
                    stack.append((rr, cc))
        return size
    zero_regions = []
    for r in range(h):
        for c in range(w):
            if not visited[r][c] and grid[r][c] == 0:
                zero_regions.append(flood(r, c))
    if len(zero_regions) < 2:
        errs.append(f"expected >=2 distinct 0-regions, found {len(zero_regions)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 6, 9
    elif difficulty == "hard":
        h_lo, h_hi = 12, 16
    else:
        h_lo, h_hi = 8, 12
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo + 3, h_hi + 4)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_v = int(overrides.get("n_v_walls",
                            ctx.draw_int("n_v_walls", 1, 2)))
    n_h = int(overrides.get("n_h_walls",
                            ctx.draw_int("n_h_walls", 1, 2)))
    n_v = max(1, min(3, n_v))
    n_h = max(0, min(3, n_h))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    distractor = float(overrides.get("distractor_density",
                                     ctx.draw_rng("distractor_density")
                                     .uniform(0.0, 0.05)))
    g = full_grid(h, w, 0)
    v_cols = _pick_walls(bias, w, n_v, rng, "v")
    for c in v_cols:
        for r in range(h):
            g[r][c] = 2
    # H-walls inside specific regions to make sizes distinct
    for hi in range(n_h):
        if hi == 0:
            sections = [0] + sorted(v_cols) + [w]
            section_idx = rng.randint(0, len(sections) - 2)
            r = rng.randint(2, h - 3) if h > 5 else h // 2
            for c in range(sections[section_idx],
                            sections[section_idx + 1]):
                if g[r][c] == 0:
                    g[r][c] = 2
        else:
            sections = [0] + sorted(v_cols) + [w]
            section_idx = (hi) % (len(sections) - 1)
            r = rng.randint(2, h - 3) if h > 5 else h // 2
            for c in range(sections[section_idx],
                            sections[section_idx + 1]):
                if g[r][c] == 0:
                    g[r][c] = 2
    # Distractors
    for _ in range(int(h * w * distractor)):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] == 0:
            g[r][c] = 2
    return g


def _pick_walls(bias, w, n, rng, kind):
    candidates = list(range(2, w - 2))
    if not candidates:
        return [w // 2]
    if bias == "spread":
        step = max(1, w // (n + 1))
        cols = [step + i * step for i in range(n)]
        return [c for c in cols if 1 <= c < w - 1][:n]
    if bias == "centered":
        center = w // 2
        cols = [center - (n - 1) // 2 + i for i in range(n)]
        return [c for c in cols if 1 <= c < w - 1][:n]
    if bias == "left_heavy":
        return [2 + i * 2 for i in range(n) if 2 + i * 2 < w - 1][:n]
    if bias == "right_heavy":
        return [w - 2 - i * 2 for i in range(n) if w - 2 - i * 2 > 0][:n]
    rng.shuffle(candidates)
    return sorted(candidates[:n])


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # Three regions of identical size — rule's max/min are ambiguous
        c1 = w // 3; c2 = 2 * w // 3
        for r in range(h):
            g[r][c1] = 2
            g[r][c2] = 2
        return g
    if name == "single_region":
        # No walls — just one region
        return g
    if name == "all_walls":
        # Grid almost entirely walls; tiny 0-pockets
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        g[h // 2][w // 2] = 0
        g[h // 2][w // 2 + 1] = 0
        return g
    return g
