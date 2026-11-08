"""Generator for puzzle 1f876c06.

Rule: for each color, for each pair of cells of that color whose row
distance equals col distance (i.e. on a diagonal), draw a diagonal
line between them in that color.

Combinatorial axes (8): grid_h/w, n_colors, palette_kind,
diag_direction, n_pairs_per_color, position_bias, anchor_corner,
asymmetry_force.
Degenerates: no_pairs, all_same_color, antidiagonals_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c7de5e8abc29"
VERSION = "2.0.2"
TASK_ID = "c7de5e8abc29"
SUMMARY = (
    "0-bg grid (h~6-10, w~"
    "9-14) with 2-3 PAIRS "
    "of SAME-COLOR CELLS, "
    "each pair on a "
    "DIAGONAL (|dr| == "
    "|dc| ≥ 2), direction "
    "drawn from {nw_se, "
    "ne_sw, mixed}. Each "
    "pair color is "
    "DISTINCT from a palette "
    "(warm/cool/broad/"
    "primary). Pairs don't "
    "share cells. Rule "
    "(CONNECT DIAGONAL "
    "SAME-COLOR PAIRS WITH "
    "DIAGONAL LINES): For "
    "EACH COLOR C with "
    "EXACTLY 2 cells (r1, "
    "c1) and (r2, c2) "
    "where |r2-r1| == "
    "|c2-c1| (diagonal): "
    "PAINT every cell "
    "along the DIAGONAL "
    "LINE between them in "
    "color C (Bresenham/"
    "step-1 diagonal). "
    "Endpoints stay. Net: "
    "each diagonal "
    "endpoint pair becomes "
    "a solid colored "
    "diagonal line."
)

INVARIANTS = [
    "background is 0",
    ">=2 colors with cells aligned on a diagonal (|dr| == |dc| >= 2)",
    "diagonal directions can be NE-SW or NW-SE",
    "pairs do not share endpoint cells or drawn diagonal-line footprints",
]

DIAG_DIRECTIONS = ("nw_se", "ne_sw", "mixed")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_pairs", "all_same_color", "antidiagonals_only")
HELPFUL_TEXTURES = DIAG_DIRECTIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "6..18"},
    "n_colors":       {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "diag_direction": {"type": "str", "default": "rng helpful",
                       "valid": "|".join(DIAG_DIRECTIONS)},
    "min_diag_len":   {"type": "int", "default": "2", "valid": "2..6"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for diag_direction",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 4, 6
    elif difficulty == "hard":
        h_lo, h_hi = 10, 14
    else:
        h_lo, h_hi = 6, 10
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo + 3, h_hi + 4)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_colors = int(overrides.get("n_colors",
                                 ctx.draw_int("n_colors", 2, 3)))
    n_colors = max(1, min(5, n_colors))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    direction = (overrides.get("texture") or
                 overrides.get("diag_direction")
                 or ctx.draw_choice("diag_direction",
                                    list(DIAG_DIRECTIONS)))
    min_len = int(overrides.get("min_diag_len", 2))
    palette = _build_palette(palette_kind, n_colors, rng)
    for _attempt in range(40):
        g = full_grid(h, w, 0)
        reserved_paths: set[tuple[int, int]] = set()
        placed = 0
        for color in palette:
            for _ in range(40):
                d_dir = direction if direction != "mixed" \
                        else rng.choice(["nw_se", "ne_sw"])
                r1 = rng.randint(0, h - 1 - min_len)
                if d_dir == "nw_se":
                    c1 = rng.randint(0, w - 1 - min_len)
                    d = rng.randint(min_len, min(h - 1 - r1, w - 1 - c1))
                    r2 = r1 + d; c2 = c1 + d
                else:
                    c1 = rng.randint(min_len, w - 1)
                    d = rng.randint(min_len, min(h - 1 - r1, c1))
                    r2 = r1 + d; c2 = c1 - d
                path = set(_diag_path((r1, c1), (r2, c2)))
                if (0 <= r2 < h and 0 <= c2 < w and
                    g[r1][c1] == 0 and g[r2][c2] == 0 and
                    not (path & reserved_paths)):
                    g[r1][c1] = color
                    g[r2][c2] = color
                    reserved_paths.update(path)
                    placed += 1
                    break
        if placed == len(palette):
            return g
    raise ValueError("could not place non-overlapping diagonal endpoint pairs")


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    while len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
    return pool[:n]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    if name == "no_pairs":
        # Single cell of one color, no pair → no diag drawn
        g[h // 2][w // 2] = color
        return g
    if name == "all_same_color":
        # Several cells of one color forming many diagonals → tangled output
        for r, c in [(0, 0), (h - 1, w - 1), (0, w - 1), (h - 1, 0)]:
            g[r][c] = color
        return g
    if name == "antidiagonals_only":
        c1 = w - 2; c2 = 1
        d = min(h - 1, c1 - c2)
        if d >= 2:
            g[0][c1] = color
            g[d][c1 - d] = color
        return g
    return g


def _diag_path(a, b):
    (r1, c1), (r2, c2) = a, b
    dr, dc = r2 - r1, c2 - c1
    if abs(dr) != abs(dc):
        return []
    sr = 1 if dr > 0 else -1
    sc = 1 if dc > 0 else -1
    return [(r1 + k * sr, c1 + k * sc) for k in range(abs(dr) + 1)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Each non-bg color has exactly one diagonal pair; drawn paths are disjoint."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if not h or any(len(row) != w for row in grid):
        return ["grid must be nonempty and rectangular"]
    cells_by_color: dict[int, list[tuple[int, int]]] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                cells_by_color.setdefault(v, []).append((r, c))
    if len(cells_by_color) < 2:
        msgs.append(f"expected at least two diagonal-pair colors, got {len(cells_by_color)}")
    reserved: dict[tuple[int, int], int] = {}
    for color, cells in cells_by_color.items():
        if len(cells) != 2:
            msgs.append(f"color {color} has {len(cells)} cells (expected 2)")
            continue
        (r1, c1), (r2, c2) = cells
        dr, dc = abs(r2 - r1), abs(c2 - c1)
        if dr != dc:
            msgs.append(f"color {color} pair at ({r1},{c1})-({r2},{c2}) not on diagonal (|dr|={dr}, |dc|={dc})")
            continue
        if dr < 2:
            msgs.append(f"color {color} diagonal too short (|dr|={dr} < 2)")
            continue
        for cell in _diag_path((r1, c1), (r2, c2)):
            prev = reserved.get(cell)
            if prev is not None:
                msgs.append(f"drawn diagonal paths for colors {prev} and {color} overlap at {cell}")
                break
            reserved[cell] = color
    return msgs
