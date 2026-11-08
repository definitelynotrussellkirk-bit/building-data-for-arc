"""Generator for 447fd412.

Rule: a small 1-template with adjacent 2 markers is scaled and stamped
at matching standalone 2-blocks.

Combinatorial axes (8): grid_h/w, scale, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_template, no_blocks, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5f7e273c56dd"
RULE_HASH = "90fa58364a4f"  # canonical rule this generator was written against
VERSION = "2.0.1"
TASK_ID = "5f7e273c56dd"
SUMMARY = (
    "0-bg grid (h, w~17-23 depending on scale ∈ "
    "{1, 2, 3}) with: (a) a small TEMPLATE in the "
    "upper-left — 3 color-1 cells at fixed offsets "
    "[(0,0),(0,1),(1,1)] PLUS 2 color-2 MARKER cells "
    "at adjacent offsets [(1,2),(2,1)] sitting just "
    "outside the 1-template; (b) STANDALONE color-2 "
    "BLOCKS placed somewhere in the lower-right "
    "region — each block is a scale×scale solid "
    "square of color 2 at scaled marker positions, "
    "matching the template's marker layout but at "
    "the given SCALE. Rule: extract the 1-template "
    "shape and its 2-marker offsets. The standalone "
    "2-blocks indicate scaled stamp positions — each "
    "block's side length is the SCALE factor. STAMP "
    "the 1-template (recolored to 1) at each scaled "
    "anchor, upscaled by SCALE. The 2-blocks vanish "
    "or stay depending on canonical convention. Net: "
    "scale + scaled-block markers drive multiple "
    "stamps of the template at upscaled positions."
)

INVARIANTS = [
    "background is color 0",
    "the source template contains color 1 cells and adjacent color 2 marker cells",
    "standalone color 2 blocks mark scaled copies of the template markers",
    "standalone block side length is the template scale",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_template", "no_blocks", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varied", "valid": "varied"},
    "grid_w":         {"type": "int", "default": "varied", "valid": "varied"},
    "scale":          {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        scale = ctx.draw_int("scale", 1, 1)
    elif difficulty == "hard":
        scale = ctx.draw_int("scale", 3, 3)
    else:
        scale = ctx.draw_int("scale", 1, 3)
    h = 14 + 3 * scale + rng.randint(0, 2)
    w = 14 + 3 * scale + rng.randint(0, 2)
    g = full_grid(h, w, 0)

    template_r = 1 + (sample_index % 2)
    template_c = 1 + ((sample_index // 2) % 2)
    one_cells = [(0, 0), (0, 1), (1, 1)]
    marker_cells = [(1, 2), (2, 1)]
    for dr, dc in one_cells:
        g[template_r + dr][template_c + dc] = 1
    for dr, dc in marker_cells:
        g[template_r + dr][template_c + dc] = 2

    origin_r = 6 + rng.randint(0, 2)
    origin_c = 6 + rng.randint(0, 2)
    for mr, mc in marker_cells:
        br = origin_r + mr * scale
        bc = origin_c + mc * scale
        for dr in range(scale):
            for dc in range(scale):
                g[br + dr][bc + dc] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Color-1 (template) and color-2 (markers/blocks) must both be present."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    has_1 = any(grid[r][c] == 1 for r in range(h) for c in range(w))
    has_2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_1:
        errors.append("no color-1 template cells found")
    if not has_2:
        errors.append("no color-2 marker/block cells found")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(18, 18, 0)
    if name == "no_template":
        g[10][10] = 2
        return g
    if name == "no_blocks":
        for dr, dc in [(0, 0), (0, 1), (1, 1)]:
            g[1 + dr][1 + dc] = 1
        for dr, dc in [(1, 2), (2, 1)]:
            g[1 + dr][1 + dc] = 2
        return g
    if name == "full_grid":
        for r in range(18):
            for c in range(18):
                g[r][c] = 2
        return g
    return g
