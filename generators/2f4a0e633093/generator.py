"""Generator for 15b:hard_104 — build a shape × color gallery.

The ordinary grammar is deliberately exact: a five-by-eleven input contains
three distinct legend colors in row zero and three monochrome 3x3 mask panels
at fixed offsets.  The canonical rule crops each panel to its nonzero bounding
box, binarizes it, and lays out every mask/color product in an 11x11 gallery.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2f4a0e633093"
VERSION = "1.2.0"
TASK_ID = GENERATOR_ID
SUMMARY = "Three top-row legend colors crossed with three fixed 3x3 mask panels."
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the ordinary input is exactly 5x11 with background 0",
    "row 0 has exactly three distinct legend colors",
    "rows 2..4 contain exactly three fixed monochrome mask panels",
    "each ordinary panel has 3..6 cells and a color outside the legend",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_legend", "empty_panels", "full_panels")
HELPFUL_TEXTURES = PALETTE_KINDS
_ALLOWED_OVERRIDES = {"grid_h", "grid_w", "palette_kind", "n_panel_cells", "texture"}
_LEGEND_PALETTES = {
    "default": (2, 3, 4, 6, 7, 8, 9),
    "warm": (2, 3, 4),
    "cool": (1, 5, 6),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}

AXES = {
    "grid_h": {"type": "int", "default": "5", "valid": "5..5"},
    "grid_w": {"type": "int", "default": "11", "valid": "11..11"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "n_panel_cells": {"type": "int", "default": "rng 3..6", "valid": "3..6"},
    "palette_size": {"type": "int", "default": "6", "valid": "6..6"},
    "position_bias": {"type": "str", "default": "fixed_panel_layout", "valid": "fixed_panel_layout"},
    "n_distinct_colors": {"type": "int", "default": "6", "valid": "6..6"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative exact integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    if "grid_h" in overrides and (type(overrides["grid_h"]) is not int or overrides["grid_h"] != 5):
        raise ValueError("grid_h must be exactly 5")
    if "grid_w" in overrides and (type(overrides["grid_w"]) is not int or overrides["grid_w"] != 11):
        raise ValueError("grid_w must be exactly 11")
    if "n_panel_cells" in overrides and (
        type(overrides["n_panel_cells"]) is not int or not 3 <= overrides["n_panel_cells"] <= 6
    ):
        raise ValueError("n_panel_cells must be an exact integer in 3..6")
    if "palette_kind" in overrides and overrides["palette_kind"] not in PALETTE_KINDS:
        raise ValueError("unknown palette_kind")
    if "texture" in overrides and overrides["texture"] not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError("unknown texture")
    if (
        overrides.get("texture") in HELPFUL_TEXTURES
        and "palette_kind" in overrides
        and overrides["texture"] != overrides["palette_kind"]
    ):
        raise ValueError("helpful texture and palette_kind must agree")


def _binary_crop(panel):
    cells = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    return [[1 if panel[r][c] else 0 for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]


def rule_mirror(grid):
    """Independent Python mirror of the canonical fixed-panel Racket rule."""
    legend = [value for value in grid[0] if value]
    masks = []
    for c0 in (0, 4, 8):
        masks.append(_binary_crop([[grid[r][c] for c in range(c0, c0 + 3)] for r in range(2, 5)]))
    out = full_grid(11, 11, 0)
    for i, mask in enumerate(masks):
        for j, color in enumerate(legend):
            for r, row in enumerate(mask):
                for c, value in enumerate(row):
                    if value:
                        out[i * 4 + r][j * 4 + c] = color
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(type(row) is not list or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer ARC colors"]
    if (meta or {}).get("texture") in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errors = []
    if (h, w) != (5, 11):
        return [f"ordinary grid must be exactly 5x11, got {h}x{w}"]
    legend = [value for value in grid[0] if value]
    if len(legend) != 3 or len(set(legend)) != 3:
        errors.append("legend must contain exactly three distinct nonzero colors")
    if any(grid[1][c] != 0 for c in range(w)):
        errors.append("separator row 1 must be empty")
    panel_colors = []
    for index, c0 in enumerate((0, 4, 8)):
        values = [grid[r][c] for r in range(2, 5) for c in range(c0, c0 + 3) if grid[r][c] != 0]
        colors = set(values)
        if not 3 <= len(values) <= 6:
            errors.append(f"panel {index} must contain 3..6 nonzero cells")
        if len(colors) != 1:
            errors.append(f"panel {index} must be monochrome")
        elif next(iter(colors)) in set(legend):
            errors.append(f"panel {index} color must not be a legend color")
        else:
            panel_colors.append(next(iter(colors)))
    if len(panel_colors) == 3 and len(set(panel_colors)) != 3:
        errors.append("panel colors must be distinct")
    for r in range(2, 5):
        for c in (3, 7):
            if grid[r][c] != 0:
                errors.append("panel separator columns must be empty")
                break
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)
    effective = dict(overrides)
    if texture in HELPFUL_TEXTURES:
        effective.setdefault("palette_kind", texture)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=effective)
    rng = ctx.draw_rng("layout")
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    n_panel_cells = ctx.draw_int_strict("n_panel_cells", 3, 6)
    g = full_grid(5, 11, 0)
    legend_candidates = _LEGEND_PALETTES[palette_kind]
    legend = list(legend_candidates) if len(legend_candidates) == 3 else rng.sample(list(legend_candidates), 3)
    legend_cols = rng.sample(range(11), 3)
    for col, color in zip(legend_cols, legend):
        g[0][col] = color
    panel_candidates = [color for color in range(1, 10) if color not in legend]
    panel_colors = rng.sample(panel_candidates, 3)
    for c0, color in zip((0, 4, 8), panel_colors):
        cells = [(r, c0 + dc) for r in range(2, 5) for dc in range(3)]
        for r, c in rng.sample(cells, n_panel_cells):
            g[r][c] = color
    findings = self_check(g, difficulty=difficulty, meta={"texture": palette_kind})
    if findings:
        raise RuntimeError(f"constructed invalid ordinary scene: {findings}")
    return g


def _draw_from_degenerate(name):
    g = full_grid(5, 11, 0)
    if name == "empty_legend":
        for c0, color in zip((0, 4, 8), (4, 6, 8)):
            for r, c in ((2, c0), (3, c0), (3, c0 + 1)):
                g[r][c] = color
    elif name == "empty_panels":
        for col, color in zip((1, 5, 9), (2, 3, 4)):
            g[0][col] = color
    elif name == "full_panels":
        for col, color in zip((1, 5, 9), (2, 3, 4)):
            g[0][col] = color
        for c0, color in zip((0, 4, 8), (6, 7, 8)):
            for r in range(2, 5):
                for c in range(c0, c0 + 3):
                    g[r][c] = color
    return g
