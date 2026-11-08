"""Generator for ARC task 1c0d0a4b.

Rule: `(rule! (lambda (g) (cellmap g (r c v) (if (or (zero? (mod r 4)) (zero? (mod c 4))) 0 (if (= v 8) 0 2)))))`.
For each cell: if r % 4 == 0 OR c % 4 == 0 → 0 (lattice grid stays bg);
otherwise if cell == 8 → 0 (8s are erased); otherwise → 2.

Effect: the output shows a periodic 4-spacing lattice of 0s, with cyan
(8) holes erased to 0 and everything else painted red(2).

Combinatorial axes:
  * grid_h / grid_w     — outer canvas size (multiples of 4 + 1
                          maximize visible lattice cells)
  * eight_density       — fraction of non-lattice cells that are 8
  * eight_layout        — random / cluster / aligned_to_4grid /
                          column / row
  * decoy_palette       — extra non-8 colors planted (rule paints
                          them all to 2 anyway)
  * caller-opt-in degenerates: no_eights (output uniform red lattice),
                               all_eights (output all 0),
                               only_lattice (no interior content)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9ee024f29fdb"
VERSION = "2.0.1"
TASK_ID = "9ee024f29fdb"
SUMMARY = (
    "Grid (h, w ∈ {5, 9, 13, 17}) on "
    "0-bg with: (a) COLOR-8 (cyan) CELLS "
    "scattered in INTERIOR positions "
    "(r%4 != 0 AND c%4 != 0) at density "
    "0.20-0.55 using one of 5 layouts "
    "(random/cluster/aligned_to_4grid/"
    "column/row); (b) 0-3 DECOY COLORS "
    "(non-{2,8}) sprinkled at 20% rate "
    "in remaining interior cells. The "
    "ROWS/COLS where r%4==0 OR c%4==0 "
    "stay 0 (form a 4-spacing LATTICE). "
    "Rule (LATTICE + ERASE 8 + PAINT "
    "REST): for EACH CELL at (r, c): "
    "(1) if r%4==0 OR c%4==0 → OUTPUT 0 "
    "(lattice cells stay bg); (2) ELSE "
    "if input cell == 8 → OUTPUT 0 (8s "
    "are erased to bg); (3) ELSE → "
    "OUTPUT 2 (red). Net: every 4th "
    "row/col stays 0 forming a lattice; "
    "cyan cells erase to 0; all other "
    "interior cells become red."
)

INVARIANTS = [
    "input dims expose at least one r%4≠0 row and one c%4≠0 col",
    "input contains some 8s (so some interior cells become 0)",
    "input contains some non-8 non-bg cells (so output has 2s)",
]

EIGHT_LAYOUTS = ("random", "cluster", "aligned_to_4grid", "column", "row")
DEGENERATE_TEXTURES = ("no_eights", "all_eights", "only_lattice")
HELPFUL_TEXTURES = EIGHT_LAYOUTS

AXES = {
    "grid_h":         {"type": "choice", "default": "rng 5|9|13|17",
                       "valid": "5|9|13|17"},
    "grid_w":         {"type": "choice", "default": "rng 5|9|13|17",
                       "valid": "5|9|13|17"},
    "eight_density":  {"type": "float", "default": "rng 0.20..0.55",
                       "valid": "0.05..0.9"},
    "eight_layout":   {"type": "str",   "default": "rng helpful",
                       "valid": "|".join(EIGHT_LAYOUTS)},
    "decoy_palette_size": {"type": "int", "default": "rng 0..3", "valid": "0..6"},
    "texture":        {"type": "str",   "default": "alias for eight_layout",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Grid has >=1 interior cell (r%4!=0, c%4!=0) with value 8."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    interior_8 = [(r, c) for r in range(h) for c in range(w)
                  if r % 4 != 0 and c % 4 != 0 and grid[r][c] == 8]
    if not interior_8:
        errs.append("no color-8 cells in interior positions (r%4!=0, c%4!=0)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_choices = [5, 9]
    elif difficulty == "hard":
        h_choices = [13, 17]
    else:
        h_choices = [5, 9, 13, 17]

    h = ctx.draw_choice("grid_h", h_choices)
    w = ctx.draw_choice("grid_w", h_choices)
    rng = ctx.draw_rng("cells")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    density = float(overrides.get(
        "eight_density",
        ctx.draw_rng("eight_density").uniform(0.20, 0.55)))
    layout = (overrides.get("texture")
              or overrides.get("eight_layout")
              or ctx.draw_choice("eight_layout", list(EIGHT_LAYOUTS)))
    n_decor = int(overrides.get("decoy_palette_size",
                                ctx.draw_int("decoy_palette_size", 0, 3)))

    g = full_grid(h, w, 0)

    interior_cells = [(r, c) for r in range(h) for c in range(w)
                      if r % 4 != 0 and c % 4 != 0]
    eight_cells = _eight_layout(layout, h, w, density, interior_cells, rng)
    for r, c in eight_cells:
        g[r][c] = 8

    decor_palette = [c for c in range(1, 10) if c not in {2, 8}]
    rng.shuffle(decor_palette)
    decor_palette = decor_palette[:max(0, n_decor)]
    if decor_palette:
        for r, c in interior_cells:
            if g[r][c] == 0 and rng.random() < 0.20:
                g[r][c] = rng.choice(decor_palette)
    return g


def _eight_layout(layout, h, w, density, interior_cells, rng):
    if not interior_cells:
        return []
    n = max(1, int(len(interior_cells) * density))
    if layout == "cluster":
        cr, cc = rng.choice(interior_cells)
        cells = sorted(interior_cells,
                       key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells[:n]
    if layout == "aligned_to_4grid":
        # Cells where both r%4 and c%4 are exactly 2 (centers of 4×4 cells).
        aligned = [(r, c) for r, c in interior_cells
                   if r % 4 == 2 and c % 4 == 2]
        return aligned[:n] or interior_cells[:n]
    if layout == "column":
        c = rng.choice([c for c in range(w) if c % 4 != 0])
        col_cells = [(r, c) for r in range(h) if r % 4 != 0]
        rng.shuffle(col_cells)
        return col_cells[:n]
    if layout == "row":
        r = rng.choice([r for r in range(h) if r % 4 != 0])
        row_cells = [(r, c) for c in range(w) if c % 4 != 0]
        rng.shuffle(row_cells)
        return row_cells[:n]
    cells = list(interior_cells)
    rng.shuffle(cells)
    return cells[:n]


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the periodic-lattice + erase-8 signal collapses.

    no_eights     — no 8s; output is "all interior cells = 2, lattice
                     stays 0" (visually fine but minimal rule signal).
    all_eights    — every interior cell is 8; output is all 0.
    only_lattice  — no interior content; output is fully 0.
    """
    g = full_grid(h, w, 0)
    if name == "no_eights":
        for r in range(h):
            for c in range(w):
                if r % 4 != 0 and c % 4 != 0 and rng.random() < 0.4:
                    g[r][c] = rng.choice([1, 3, 4, 5, 6, 7, 9])
        return g
    if name == "all_eights":
        for r in range(h):
            for c in range(w):
                if r % 4 != 0 and c % 4 != 0:
                    g[r][c] = 8
        return g
    if name == "only_lattice":
        return g
    return g
