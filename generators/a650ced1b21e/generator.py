"""Generator for 7837ac64.

Rule: colored anomalies on a lattice are summarized by corner, edge
and center groups into a 3x3 grid.

Combinatorial axes (8): grid_size, line_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
line_color.
Degenerates: no_lines, no_anomalies, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a650ced1b21e"
VERSION = "2.1.1"  # shape-locked-in: hardcoded 9x9 + lines at {1,3,5,7} (canonical 27-29). Output is always 3x3 (anomaly grouping) -> out-shape intrinsic. Vary grid size (9..29) + line positions -> in_shapes 1->13."
TASK_ID = "a650ced1b21e"
SUMMARY = (
    "Fixed 9×9 grid with: (a) a LATTICE of full rows + "
    "full cols at rows/cols [1, 3, 5, 7] in some non-bg "
    "LATTICE COLOR (forms a 4×4 grid of intersections); "
    "(b) at each lattice intersection (4×4 = 16 cells), "
    "an ANOMALY cell in some non-{0, lattice} color "
    "(may be 0 for inner intersections). Rule: detect "
    "the lattice color and the 4×4 anomaly grid at "
    "intersections. SUMMARIZE the anomalies by CORNER "
    "(outer 4 intersections), EDGE (middle of each "
    "side), and CENTER groups into a 3×3 output grid "
    "where each output cell is the dominant or "
    "representative anomaly color from that zone."
)

INVARIANTS = [
    "background is color 0",
    "one lattice color forms majority horizontal and vertical lines",
    "non-lattice colors appear only at lattice intersections",
    "each 3x3 summary zone has at least one anomaly",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_lines", "no_anomalies", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_size":      {"type": "int", "default": "9", "valid": "9"},
    "line_count":     {"type": "int", "default": "4", "valid": "4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "7", "valid": "7"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "line_color":     {"type": "color", "default": "rng !0", "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: dominant non-bg color forms a lattice (appears in >=2 full rows
    that span the grid width); at least one non-{0,dominant} anomaly color."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Count colors
    counts: dict[int, int] = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        errs.append("no non-bg cells")
        return errs
    # Dominant non-bg color is the lattice color (most cells)
    lc = max(counts, key=lambda k: counts[k])
    # Check it spans at least 2 rows (each row has the lattice color >= w*0.5)
    lc_rows = sum(1 for r in range(h)
                  if sum(1 for c in range(w) if grid[r][c] == lc) >= w // 2)
    if lc_rows < 2:
        errs.append(f"lattice color {lc} spans fewer than 2 half-rows ({lc_rows})")
    # Check anomaly colors exist
    anomaly = set(v for v in counts if v != lc)
    if not anomaly:
        errs.append("no anomaly colors (only lattice color + bg)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    ctx.draw_int("line_count", 4, 4)
    lc = ctx.draw_color("line_color", exclude={0})
    colors = ctx.draw_distinct_colors("anomaly_colors", n=6, exclude={0, lc})
    # Output is always 3x3 (rule groups anomalies into corners+middle) -> out-shape
    # rule-intrinsic. v1.x hardcoded 9x9 with 4 lines at {1,3,5,7} (shape-locked-in)
    # though canonical uses 27-29. The rule finds lc-lines at ANY size, so vary the
    # grid size + line positions (4 full lc rows/cols) to lift the input lock.
    if difficulty == "easy":
        N = ctx.draw_int("grid_n", 9, 13)
    elif difficulty == "hard":
        N = ctx.draw_int("grid_n", 19, 29)
    else:
        N = ctx.draw_int("grid_n", 11, 23)
    g = full_grid(N, N, 0)
    # 4 line positions, interior, pairwise gap >= 2. The greedy pick from a single
    # shuffle can get STUCK below 4 (e.g. choosing 4 first on N=9 blocks reaching
    # four), but the 4x4 anomaly_grid below indexes lines[0..3] -> IndexError.
    # Retry the shuffle, then fall back to a guaranteed even spread (N>=9 always
    # fits four lines with gap >= 2).
    pool = list(range(1, N - 1))
    lines = []
    for _attempt in range(40):
        rng.shuffle(pool)
        cand = []
        for p in pool:
            if all(abs(p - q) >= 2 for q in cand):
                cand.append(p)
            if len(cand) == 4:
                break
        if len(cand) == 4:
            lines = cand
            break
    if len(lines) < 4:
        lines = [1 + round(i * (N - 3) / 3) for i in range(4)]
    lines.sort()
    for r in lines:
        for c in range(N):
            g[r][c] = lc
    for c in lines:
        for r in range(N):
            g[r][c] = lc
    # 4x4 anomaly grid spanning the corners (symmetric-ish, like canonical)
    anomaly_grid = [
        [colors[0], colors[1], colors[1], colors[2]],
        [colors[3], 0, 0, colors[4]],
        [colors[3], 0, 0, colors[4]],
        [colors[5], colors[2], colors[2], colors[0]],
    ]
    for ri, row in enumerate(anomaly_grid):
        for ci, value in enumerate(row):
            if value:
                g[lines[ri]][lines[ci]] = value
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_lines":
        g[3][3] = 2
        return g
    if name == "no_anomalies":
        for r in [1, 3, 5, 7]:
            for c in range(9):
                g[r][c] = 5
        for c in [1, 3, 5, 7]:
            for r in range(9):
                g[r][c] = 5
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 5
        return g
    return g
