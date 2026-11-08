"""Generator for arc_puzzle_bank_21_set19_s:S19_E3.

Rule: among vertical panels, select the one with the most occupied
cells; recolor it to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_panels,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_max, single_panel, equal_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels

GENERATOR_ID = "2e4e1d2834ee"
VERSION = "2.0.1"
TASK_ID = "2e4e1d2834ee"
SUMMARY = (
    "h × (3*w+2) grid (0-bg, h=5..6, w=5..6) with THREE same-"
    "size w-column panels separated by full-height color-9 "
    "(maroon) divider columns. Each panel contains a different "
    "count of occupied cells (e.g., 3, 5, 8) in DIFFERENT colors "
    "(one color per panel, all distinct from 0 and 9). One panel "
    "is the STRICT WINNER (most cells). Rule: split panels at "
    "color-9 cols. Count occupied (non-zero) cells per panel. "
    "Pick the panel with the most cells. Recolor all its cells "
    "to 8 (cyan). Output: just that panel (cropped, w columns "
    "wide, h rows tall) with original positions kept and color "
    "8 in non-zero slots."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "h × (3*w+2) grid; 3 vertical panels separated by color-9 dividers",
    "each panel has a distinct cell count (no ties on max)",
    "panel colors are distinct from each other and from 0 and 9",
    "winning panel has the strict maximum cell count",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_max", "single_panel", "all_panels_equal")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..6", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 5..6", "valid": "4..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_panels":       {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "vertical_three_panels",
                       "valid": "vertical_three_panels"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "panels", "valid": "panels"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _panel(h: int, w: int, cells: list[tuple[int, int]], color: int):
    panel = full_grid(h, w, 0)
    for r, c in cells:
        panel[r][c] = color
    return panel


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-9 full-height divider columns (3 panels with 2 dividers)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(dividers) < 2:
        return [f"expected >=2 full-height color-9 divider columns, got {len(dividers)}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 5, 5)
        w = ctx.draw_int("width", 5, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 6, 6)
        w = ctx.draw_int("width", 6, 6)
    else:
        h = ctx.draw_int("height", 5, 6)
        w = ctx.draw_int("width", 5, 6)
    rng = ctx.draw_rng("cells")
    counts = [3, 5, 8]
    rng.shuffle(counts)
    panels = []
    for idx, count in enumerate(counts):
        cells = [(r, c) for r in range(h) for c in range(w)]
        rng.shuffle(cells)
        panels.append(_panel(h, w, cells[:count], 2 + idx))
    return assemble_vertical_panels(panels)


def _draw_from_degenerate(name, rng):
    h, w = 5, 5
    if name == "tied_max":
        # two panels share the maximum count → which to recolor is ambiguous
        cells = [(r, c) for r in range(h) for c in range(w)]
        panels = []
        for idx, count in enumerate([5, 5, 3]):
            sub = cells.copy()
            panels.append(_panel(h, w, sub[:count], 2 + idx))
        return assemble_vertical_panels(panels)
    if name == "single_panel":
        # only one panel → trivial selection, no comparison
        cells = [(r, c) for r in range(h) for c in range(w)]
        return _panel(h, w, cells[:5], 2)
    if name == "all_panels_equal":
        # all panels have equal counts → no unique max
        cells = [(r, c) for r in range(h) for c in range(w)]
        panels = []
        for idx in range(3):
            panels.append(_panel(h, w, cells[:4], 2 + idx))
        return assemble_vertical_panels(panels)
    return _panel(h, w, [], 0)
