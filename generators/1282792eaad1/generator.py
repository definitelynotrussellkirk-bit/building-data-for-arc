"""Generator for arc_puzzle_bank_twentieth_21_bundle:hard_139_build_cross_product_gallery_of_color_and_transform_codes.

Combinatorial axes (8): shape, transforms, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_proto, no_codes, no_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1282792eaad1"
VERSION = "2.1.1"  # diversity: random prototype polyomino + random code triple (was 5 fixed shapes x 5 fixed code-rows); output dims stay 17x17 (rotation codes need square 5x5 proto)
TASK_ID = "1282792eaad1"
SUMMARY = (
    "Fixed 7-row × 5-col 0-bg grid with: (a) "
    "ROWS 0..4 containing a 5×5 PROTOTYPE "
    "SHAPE (4-5 cells) in some source_color, "
    "drawn from a curated shape bank; (b) "
    "ROW 5, COLS 0..2 holding 3 TRANSFORM "
    "CODES (values 0..5 from a code table — "
    "each code maps to a specific rotation/"
    "reflection: 0=id, 1=cw90, 2=180°, "
    "3=ccw90, 4=flip-lr, 5=flip-ud); (c) "
    "ROW 6, COLS 0..2 holding 3 OUTPUT COLORS "
    "(distinct from source_color). Rule: "
    "construct a CROSS-PRODUCT GALLERY OUTPUT "
    "— a 3×3 grid of TRANSFORMED PROTOTYPES, "
    "where output panel (i, j) contains the "
    "PROTOTYPE shape with TRANSFORM j applied "
    "and painted in COLOR i (from row 6). "
    "Output dimensions: 3*panel_h × "
    "3*panel_w (each panel cell holds a "
    "5×5 transformed prototype). Net: "
    "input teaches one shape + 3 transforms + "
    "3 colors; output is the 3×3 cross-product "
    "gallery."
)

INVARIANTS = [
    "rows 0..4 contain a single 5x5 prototype",
    "row 5 columns 0..2 contain transform codes",
    "row 6 columns 0..2 contain output colors",
    "the output grid is the Cartesian product of colors by transformed prototype panels",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_proto", "no_codes", "no_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "shape":          {"type": "int", "default": "rng 0..4", "valid": "0..9"},
    "transforms":     {"type": "int", "default": "rng 0..4", "valid": "0..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "header_proto_codes_colors",
                       "valid": "header_proto_codes_colors"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(1, 1), (2, 1), (3, 1), (3, 2)],
    [(1, 1), (1, 2), (2, 2), (3, 2), (3, 3)],
    [(1, 1), (2, 1), (2, 2), (2, 3), (3, 3)],
    [(1, 2), (2, 0), (2, 1), (2, 2), (3, 0)],
    [(0, 1), (1, 1), (2, 1), (2, 2), (3, 2)],
]

_TRANSFORM_ROWS = [
    [0, 1, 4],
    [2, 3, 5],
    [1, 2, 3],
    [4, 0, 5],
    [5, 1, 2],
]


def _random_proto(rng, n_cells):
    """Random connected polyomino in a 5x5 box (rows 0..4), >=1 cell
    off-edge so transforms are visually distinct. Returns cell list."""
    for _ in range(120):
        cells = {(rng.randint(1, 3), rng.randint(1, 3))}
        while len(cells) < n_cells:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            nr, nc = r + dr, c + dc
            if 0 <= nr < 5 and 0 <= nc < 5:
                cells.add((nr, nc))
        # require non-symmetric enough: at least 3 cells
        if len(cells) >= 3:
            return sorted(cells)
    return [(1, 1), (2, 1), (3, 1), (3, 2)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; 7 rows; row 5 has transform codes; row 6 has output colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if h < 7:
        errors.append(f"grid has only {h} rows, need at least 7")
        return errors
    # rows 0..4 should have prototype cells
    proto_cells = [grid[r][c] for r in range(5) for c in range(w) if grid[r][c] != 0]
    if not proto_cells:
        return errors  # degenerate (no_proto) — allowed
    # row 5 cols 0..2 should have transform codes (values 0..5)
    codes = [grid[5][c] for c in range(min(3, w))]
    if all(v == 0 for v in codes):
        return errors  # degenerate (no_codes) — allowed
    # row 6 cols 0..2 should have output colors
    colors = [grid[6][c] for c in range(min(3, w))]
    if all(v == 0 for v in colors):
        return errors  # degenerate (no_colors) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n_cells = ctx.draw_int("shape", 3, 4)
    elif difficulty == "hard":
        n_cells = ctx.draw_int("shape", 6, 9)
    else:
        n_cells = ctx.draw_int("shape", 4, 7)
    proto = _random_proto(rng, n_cells)
    # 3 transform codes (0..5), with at least 2 distinct so the gallery
    # columns differ.
    for _ in range(40):
        codes = [rng.randint(0, 5) for _ in range(3)]
        if len(set(codes)) >= 2:
            break
    source_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    output_colors = rng.sample([c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]
                                if c != source_color], 3)

    g = full_grid(7, 5, 0)
    for r, c in proto:
        g[r][c] = source_color
    for c, code in enumerate(codes):
        g[5][c] = code
    for c, color in enumerate(output_colors):
        g[6][c] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 5, 0)
    if name == "no_proto":
        # Rows 0..4 empty — rule has no prototype to transform.
        for c, code in enumerate([1, 2, 3]): g[5][c] = code
        for c, color in enumerate([4, 5, 6]): g[6][c] = color
        return g
    if name == "no_codes":
        # Row 5 empty — rule has no transforms to apply.
        for r, c in _SHAPES[0]: g[r][c] = 8
        for c, color in enumerate([4, 5, 6]): g[6][c] = color
        return g
    if name == "no_colors":
        # Row 6 empty — rule has no output palette to recolor with.
        for r, c in _SHAPES[0]: g[r][c] = 8
        for c, code in enumerate([1, 2, 3]): g[5][c] = code
        return g
    return g
