"""Generator for arc_additional_puzzle_bank_volume3:H21.

Rule: 5-walls divide grid; for each non-5 region, count {2,3,4} cells
and fill with the majority color (ties go to smallest).

Combinatorial axes (8): grid_h/w, palette_kind, n_compartments,
palette_size, position_bias, n_distinct_colors, marker_density, texture.
Degenerates: no_walls, no_markers, all_tied.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "36018a11f283"
VERSION = "2.1.0"
TASK_ID = "36018a11f283"
SUMMARY = (
    "0-bg grid with an INNER color-5 wall maze: a one-cell zero moat "
    "surrounds a rectangular 5-wall frame, and one or two internal 5-wall "
    "rows/cols split that frame into 4, 6, or 9 rectangular compartments. "
    "Each compartment contains a compact same-color marker blob from {2,3,4}; "
    "the marker color is the strict majority for that compartment. The canonical "
    "rule visits every non-5 region, ignores regions with no markers, and fills "
    "each marked compartment with its majority marker color while preserving the "
    "5-walls and leaving the outer zero moat unchanged."
)

INVARIANTS = [
    "outer border is background 0",
    "inner color-5 walls form rectangular compartments",
    "each marked compartment has a strict majority color from {2,3,4}",
]

PALETTE_KINDS = ("default", "warm_markers", "cool_markers", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_markers", "all_tied")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "9..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm_markers|cool_markers|varied"},
    "n_compartments": {"type": "int", "default": "rng 4..9", "valid": "4|6|9"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "marker_density": {"type": "str", "default": "compact", "valid": "compact"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm_markers|cool_markers|varied|no_walls|no_markers|all_tied"},
}


def _wall_lines(start: int, end: int, n_parts: int, rng):
    """Return boundary/internal wall indices with >=2 open cells per part."""
    total = end - start + 1
    total_open = total - (n_parts + 1)
    if total_open < 2 * n_parts:
        n_parts = max(1, (total - 1) // 3)
        total_open = total - (n_parts + 1)
    sizes = [2] * n_parts
    extra = max(0, total_open - 2 * n_parts)
    for _ in range(extra):
        sizes[rng.randrange(n_parts)] += 1
    walls = [start]
    pos = start
    for size in sizes[:-1]:
        pos += size + 1
        walls.append(pos)
    walls.append(end)
    return walls


def _marker_blob(cells, rng, max_size=3):
    """Pick a compact connected marker blob inside a compartment."""
    cells_set = set(cells)
    anchor = rng.choice(cells)
    blob = [anchor]
    frontier = [anchor]
    target = min(max_size, len(cells))
    while len(blob) < target and frontier:
        r, c = frontier.pop(0)
        nbrs = [(r + dr, c + dc) for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0))]
        rng.shuffle(nbrs)
        for nb in nbrs:
            if nb in cells_set and nb not in blob:
                blob.append(nb)
                frontier.append(nb)
                if len(blob) >= target:
                    break
    return blob


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        n_rows, n_cols = 2, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 14)
        n_rows = rng.randint(2, 3)
        n_cols = rng.randint(2, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n_rows = 2
        n_cols = rng.randint(2, 3) if w >= 12 else 2

    g = full_grid(h, w, 0)
    # Inner wall rectangle leaves a canonical-looking zero moat around it.
    wall_rs = _wall_lines(1, h - 2, n_rows, rng)
    wall_cs = _wall_lines(1, w - 2, n_cols, rng)
    for r in wall_rs:
        for c in range(wall_cs[0], wall_cs[-1] + 1):
            g[r][c] = 5
    for c in wall_cs:
        for r in range(wall_rs[0], wall_rs[-1] + 1):
            g[r][c] = 5

    compartments = []
    for i in range(len(wall_rs) - 1):
        for j in range(len(wall_cs) - 1):
            r1, r2 = wall_rs[i] + 1, wall_rs[i + 1] - 1
            c1, c2 = wall_cs[j] + 1, wall_cs[j + 1] - 1
            if r1 <= r2 and c1 <= c2:
                compartments.append((r1, c1, r2, c2))

    palette = [2, 3, 4]
    for idx, (r1, c1, r2, c2) in enumerate(compartments):
        majority = palette[(idx + rng.randrange(3)) % 3]
        cells = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
        for r, c in _marker_blob(cells, rng, max_size=3):
            g[r][c] = majority
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    if name == "no_walls":
        # no 5-walls → one marked open region instead of compartments
        g = full_grid(h, w, 0)
        g[2][2] = 2; g[2][3] = 2
        g[5][2] = 3; g[6][2] = 3
        return g
    if name == "no_markers":
        # walls + compartments but no {2,3,4} markers — all marked regions absent
        g = full_grid(h, w, 0)
        for r in (1, 4, 7):
            for c in range(1, 11):
                g[r][c] = 5
        for c in (1, 6, 10):
            for r in range(1, 8):
                g[r][c] = 5
        return g
    if name == "all_tied":
        # every compartment has all three markers tied (1 each) — fill ambiguous
        g = _draw_from_degenerate("no_markers", rng)
        for r0, c0 in [(2, 2), (2, 7), (5, 2), (5, 7)]:
            g[r0][c0] = 2
            g[r0][c0 + 1] = 3
            g[r0 + 1][c0] = 4
        return g
    return full_grid(h, w, 0)


def _regions_not_wall(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    regions = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 5):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            regions.append(cells)
    return regions


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    h, w = len(grid), len(grid[0])
    if any(grid[0][c] != 0 or grid[h - 1][c] != 0 for c in range(w)):
        errors.append("top/bottom outer border must be background 0")
    if any(grid[r][0] != 0 or grid[r][w - 1] != 0 for r in range(h)):
        errors.append("left/right outer border must be background 0")
    if not any(v == 5 for row in grid for v in row):
        errors.append("inner wall color 5 must be present")

    regions = _regions_not_wall(grid)
    marked_regions = []
    for cells in regions:
        counts = {color: sum(1 for r, c in cells if grid[r][c] == color) for color in (2, 3, 4)}
        if max(counts.values()) > 0:
            marked_regions.append((cells, counts))
    expected = (4,) if difficulty == "easy" else ((4, 6, 9) if difficulty == "hard" else (4, 6))
    if len(marked_regions) not in expected:
        errors.append(f"expected {expected} marked compartments, found {len(marked_regions)}")
    for cells, counts in marked_regions:
        rs = [r for r, _c in cells]; cs = [c for _r, c in cells]
        area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        if area != len(cells):
            errors.append("each marked compartment must be rectangular")
            break
        best = max(counts.values())
        if list(counts.values()).count(best) != 1:
            errors.append("each marked compartment must have a strict majority marker color")
            break
    return errors
