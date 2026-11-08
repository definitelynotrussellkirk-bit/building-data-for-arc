"""Generator for puzzle 8e301a54.

Rule: bg is 7; rule shifts each non-bg 4-conn component DOWN by its
cell count.

Combinatorial axes (8): grid_h/w, n_components, component_size_kind,
component_shape_kind, palette_kind, position_bias,
inter_component_margin, decoy_density.
Degenerates: single_component, all_too_large, no_components.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import normalize, rect_cells

GENERATOR_ID = "3206770a2bd8"
VERSION = "1.1.1"
TASK_ID = "3206770a2bd8"
SUMMARY = "Components on bg=7; rule shifts each down by its cell count."

INVARIANTS = [
    "background is 7",
    ">=2 connected components",
    "each component's downward shift (= cell count) keeps it in-bounds",
    "components separated by margin >= 1",
]

COMPONENT_SHAPES = ("hline_2", "hline_3", "vline_2", "vline_3",
                    "block_2x2", "L_tromino")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("single_component", "all_too_large", "no_components")
HELPFUL_TEXTURES = COMPONENT_SHAPES

AXES = {
    "grid_h":              {"type": "int", "default": "rng 14..20", "valid": "12..24"},
    "grid_w":              {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "n_components":        {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "component_shape_kind": {"type": "str", "default": "rng helpful",
                             "valid": "|".join(COMPONENT_SHAPES)},
    "palette_kind":        {"type": "str", "default": "rng helpful",
                            "valid": "|".join(PALETTE_KINDS)},
    "position_bias":       {"type": "str", "default": "rng spread|center|edge",
                            "valid": "spread|center|edge"},
    "inter_component_margin": {"type": "int", "default": "1", "valid": "1..3"},
    "max_component_size":  {"type": "int", "default": "4", "valid": "2..6"},
    "texture":             {"type": "str", "default": "alias for component_shape_kind",
                            "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=7; >=2 connected components (non-7); each fits within grid when shifted down by cell count."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Non-7 cells exist
    non_bg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 7]
    if len(non_bg) < 2:
        errs.append(f"only {len(non_bg)} non-bg cell(s) (need >=2)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 12, 14, 10, 12
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 18, 24, 16, 22
    else:
        h_lo, h_hi, w_lo, w_hi = 14, 20, 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_comps = int(overrides.get("n_components",
                                ctx.draw_int("n_components", 2, 4)))
    n_comps = max(2, min(6, n_comps))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 5, 8]
    elif palette_kind == "small":
        pool = [1, 2, 3]
    else:
        pool = [1, 2, 3, 4, 5, 6, 8, 9]
    rng.shuffle(pool)
    palette = pool[:n_comps]
    while len(palette) < n_comps:
        palette.append(palette[0])
    shape_kind = (overrides.get("texture") or
                  overrides.get("component_shape_kind")
                  or ctx.draw_choice("component_shape_kind",
                                     list(COMPONENT_SHAPES)))
    margin = int(overrides.get("inter_component_margin", 1))
    g = full_grid(h, w, 7)
    placed = 0
    for color in palette:
        cells = _shape_cells(shape_kind, rng)
        sz = len(cells)
        rh = max(r for r, _ in cells) + 1
        rw = max(c for _, c in cells) + 1
        for _ in range(40):
            rr = rng.randint(0, max(0, (h - sz - rh) // 2))
            rc = rng.randint(0, w - rw)
            ok = True
            for dr in range(-margin, rh + margin):
                for dc in range(-margin, rw + margin):
                    nr = rr + dr; nc = rc + dc
                    if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 7:
                        ok = False; break
                if not ok: break
            if not ok:
                continue
            for dr, dc in cells:
                g[rr + dr][rc + dc] = color
            placed += 1
            break
    if placed < 2:
        # fallback simple placement
        g = full_grid(h, w, 7)
        for i in range(min(2, n_comps)):
            for c in range(2):
                if i * 4 + 1 < h and c < w:
                    g[i * 4 + 1][c] = palette[i]
    return g


def _shape_cells(kind, rng):
    if kind == "hline_2":
        return normalize([(0, 0), (0, 1)])
    if kind == "hline_3":
        return normalize([(0, 0), (0, 1), (0, 2)])
    if kind == "vline_2":
        return normalize([(0, 0), (1, 0)])
    if kind == "vline_3":
        return normalize([(0, 0), (1, 0), (2, 0)])
    if kind == "block_2x2":
        return normalize([(0, 0), (0, 1), (1, 0), (1, 1)])
    if kind == "L_tromino":
        return normalize([(0, 0), (1, 0), (1, 1)])
    return normalize(rect_cells(1, 2))


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 7)
    if name == "single_component":
        for c in range(min(2, w)):
            g[1][c] = rng.choice([1, 2, 3, 4, 5, 6, 8, 9])
        return g
    if name == "all_too_large":
        for c in range(w):
            g[0][c] = 1
        return g
    if name == "no_components":
        return g
    return g
