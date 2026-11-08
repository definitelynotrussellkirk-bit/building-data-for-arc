"""Generator for arc_puzzle_bank_21_next:medium_c03.

Rule: crop input to its content's bbox; concatenate that crop with its
left-right flip, separated by a 1-col bg gap. Output dims are
crop_h × (crop_w * 2 + 1).

Combinatorial axes (8): grid_h/w, palette_kind, shape_id, color,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_blob, symmetric_blob, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2e1f0bb81a3b"
VERSION = "2.0.1"  # out=4 distinct, dup-outputs 42%: only ~9 fixed shapes -> few bbox sizes. Now RANDOM asymmetric polyominoes (3..8 cells, varied bbox incl. non-square) -> many distinct crop dims, single fg color (canonical n_distinct=1).
TASK_ID = "2e1f0bb81a3b"
SUMMARY = "Single asymmetric (non-LR-symmetric) connected blob. Rule crops the input to the blob's bbox, then concatenates that crop with its LR-flip using a 1-column bg separator. Output preserves the blob's color."

# Rivals: 'output is the input' refuted by any demo (output is mirrored
# pair). 'output is just the flip' refuted by any demo (original is on
# the left). 'use a different color in mirror' refuted by any demo
# (color is preserved). 'no separator' refuted by any demo (1-col gap
# is visible). 3 demos with varied shapes + colors cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly one connected blob, 3-5 cells",
    "blob is asymmetric (not lr-symmetric)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_blob", "symmetric_blob", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "shape_id":       {"type": "int", "default": "rng 0..N-1", "valid": "0..N-1"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "color":          {"type": "color", "default": "rng !{0,1}",
                       "valid": "2..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_ASYM_SHAPES = [
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],  # T (LR-sym, exclude actually)
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 0), (1, 0), (2, 0), (1, 1)],
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1)],
]


def _is_lr_sym(shape):
    cells = set(shape)
    max_c = max(c for _, c in cells)
    flipped = {(r, max_c - c) for r, c in cells}
    return cells == flipped


_ASYM_SHAPES = [s for s in _ASYM_SHAPES if not _is_lr_sym(s)]
_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rand_asym_poly(rng, k):
    """Random connected k-cell polyomino that is NOT LR-symmetric, normalized."""
    for _ in range(40):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice(_CARD)
            nb = (r + dr, c + dc)
            if nb not in seen:
                cells.append(nb); seen.add(nb)
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        norm = [(r - mr, c - mc) for r, c in cells]
        if not _is_lr_sym(norm):
            return norm
    return _ASYM_SHAPES[0]  # fallback (effectively never)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one connected non-bg blob."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    nonzero = set((r, c) for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not nonzero:
        return ["no non-bg cells found"]
    # count components
    visited = set()
    n_comp = 0
    for start in nonzero:
        if start in visited:
            continue
        n_comp += 1
        queue = [start]
        while queue:
            cell = queue.pop()
            if cell in visited:
                continue
            visited.add(cell)
            r, c = cell
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in nonzero and nb not in visited:
                    queue.append(nb)
    if n_comp != 1:
        return [f"expected exactly 1 connected blob, got {n_comp}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # rule crops to the blob bbox then concatenates with its LR-flip, so output dims =
    # crop_h x (crop_w*2+1). Random asymmetric polyominoes give many distinct bbox
    # sizes (was ~9 fixed shapes -> out=4 distinct, 42% dup-outputs).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7); w = ctx.draw_int("grid_w", 6, 8)
        k = rng.randint(3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 11, 14)
        k = rng.randint(5, 8)
    else:
        h = ctx.draw_int("grid_h", 7, 11); w = ctx.draw_int("grid_w", 8, 12)
        k = rng.randint(3, 7)
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    shape = _rand_asym_poly(rng, k)
    sh = min(max(r for r, _ in shape) + 1, h)
    sw = min(max(c for _, c in shape) + 1, w)
    g = full_grid(h, w, 0)
    r0 = rng.randint(0, h - sh)
    c0 = rng.randint(0, w - sw)
    for dr, dc in shape:
        if r0 + dr < h and c0 + dc < w:
            g[r0 + dr][c0 + dc] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 7, 0)
    if name == "no_blob":
        return g
    if name == "symmetric_blob":
        for r in range(2, 4):
            for c in range(2, 5):
                g[r][c] = 3
        return g
    if name == "full_grid":
        for r in range(6):
            for c in range(7):
                g[r][c] = 3
        return g
    return g
