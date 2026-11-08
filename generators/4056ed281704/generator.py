"""Generator for ARC task 332efdb3.

Rule: `(rule! (lambda (g) (grid-from-fn h w (lambda (r c) (if (and (= 1 (mod r 2)) (= 1 (mod c 2))) 0 1)))))`.
Output is a fixed lattice (1 everywhere except odd-row + odd-col cells
which are 0). Input contents are ignored — only h and w matter.

Combinatorial axes: side, input_decoration, decoration_palette_size.
Degenerates: structured_decoy_lattice (input mimics output to mislead),
max_size, min_size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4056ed281704"
VERSION = "2.0.1"
TASK_ID = "4056ed281704"
SUMMARY = "Square input grid; rule emits a fixed 1/0 parity-lattice mask of the same dims."

INVARIANTS = [
    "input is an odd square (side ∈ {5, 7, 9, 11, 13})",
    "input contents do not affect output",
    "output is fixed by dims",
]

INPUT_DECORATIONS = ("all_zero", "random", "sparse", "blob", "structured")
DEGENERATE_TEXTURES = ("structured_decoy_lattice", "max_size", "min_size")
HELPFUL_TEXTURES = INPUT_DECORATIONS

AXES = {
    "side":              {"type": "choice", "default": "rng odd 5..13",
                          "valid": "5|7|9|11|13"},
    "input_decoration":  {"type": "str", "default": "rng helpful",
                          "valid": "|".join(INPUT_DECORATIONS)},
    "decoration_palette_size": {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "texture":           {"type": "str", "default": "alias for input_decoration",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: all cells are 0 (rule ignores input content; canonical input is all-zero)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if nonzero:
        errs.append(f"expected all-zero input; {len(nonzero)} non-zero cell(s) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        side = 13 if overrides["texture"] == "max_size" else 5
        return _draw_from_degenerate(overrides["texture"], side, rng)
    # The rule IGNORES input content (output = a pure r/c parity pattern of the
    # grid dims). Canonical input is ALL ZEROS, so any decoration is poison.
    # Output diversity = #distinct grid sizes -> vary h,w independently (incl.
    # non-square) over a wide range.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 8); w = ctx.draw_int("grid_w", 4, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 24); w = ctx.draw_int("grid_w", 12, 24)
    else:
        h = ctx.draw_int("grid_h", 5, 16); w = ctx.draw_int("grid_w", 5, 16)
    return full_grid(h, w, 0)


def _draw_from_degenerate(name, side, rng):
    palette = list(range(1, 10))
    rng.shuffle(palette)
    if name == "max_size":
        side = 13
    elif name == "min_size":
        side = 5
    g = full_grid(side, side, 0)
    if name == "structured_decoy_lattice":
        c = palette[0]
        for r in range(side):
            for cc in range(side):
                if not (r % 2 == 1 and cc % 2 == 1):
                    g[r][cc] = c
        return g
    return g
