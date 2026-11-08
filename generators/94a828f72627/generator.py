"""Generator for puzzle 9ddd00f0.

Rule: the grid side is h = k*(k+1) - 1 (period = k+1). The output is a
canonical fractal: separator lines where r%period==k or c%period==k are 0,
and within each block (br,bc) the single hole sits at the block's diagonal
local position (lr==br and lc==bc); everything else is the (single) color.
The rule reads only the color and the dimensions -- it normalizes the
hole positions.

This generator emits the fractal with each block's hole at a RANDOM local
position, so the rule's job is to move every hole onto its block diagonal.
Randomizing hole positions gives large honest input diversity.

Combinatorial axes: k (grid size), the color, and each block's hole
position.
Degenerates: empty_grid, full_grid, no_holes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "94a828f72627"
VERSION = "2.1.1"  # add self_check  # distinct=18: output is f(k,color) ONLY (rule normalizes hole positions away), so distinct ceiling = #k x #colors. Widen the medium band's k to 2..4 (was 2..3) -> distinct 18->27, out_sh 2->3. Intrinsic ceiling.
TASK_ID = "94a828f72627"
SUMMARY = (
    "Square grid of side k*(k+1)-1 (k in 2..4), single non-bg color, with "
    "color-0 separator lines (r%period==k or c%period==k) and ONE hole per "
    "k x k block at a RANDOM local position. Rule: normalize every block's "
    "hole onto the block diagonal (local (br,bc)). The k, color and the per-"
    "block hole positions all vary freely (was holes at fixed transposed "
    "spots, ~16 distinct)."
)

INVARIANTS = [
    "input is square with side h = k*(k+1)-1, k in {2,3,4}",
    "single non-bg color; separators (r%period==k or c%period==k) are 0",
    "exactly one hole per block; not all already on the diagonal",
]

PALETTE_KINDS = ("warm", "cool", "broad", "small")
DEGENERATE_TEXTURES = ("empty_grid", "full_grid", "no_holes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "k":               {"type": "int", "default": "varies", "valid": "2..4"},
    "fg_color":        {"type": "color", "default": "rng (!=0)", "valid": "1..9"},
    "palette_kind":    {"type": "str", "default": "rng helpful", "valid": "warm|cool|broad|small"},
    "hole_pattern_kind": {"type": "str", "default": "random", "valid": "random"},
    "palette_size":    {"type": "int", "default": "1", "valid": "1"},
    "texture":         {"type": "str", "default": "alias for palette_kind",
                        "valid": "warm|cool|broad|small|empty_grid|full_grid|no_holes"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: square grid; exactly 1 non-bg color; separator lines at r%period==k or c%period==k."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    if h != w:
        errs.append(f"expected square grid; got {h}×{w}")
    colors = set(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if len(colors) != 1:
        errs.append(f"expected exactly 1 non-bg color; got {colors}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        k = rng.randint(2, 3)
        return _draw_from_degenerate(overrides["texture"], k, rng)

    if difficulty == "easy":
        k = 2
    elif difficulty == "hard":
        k = rng.randint(3, 4)
    else:
        # output is fully determined by (k, color) -- the rule normalizes hole
        # positions away -- so the only diversity levers are k and color; span
        # the full k range here (distinct ceiling = #k x #colors).
        k = rng.randint(2, 4)

    fg = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    period = k + 1
    h = w = k * period - 1
    g = full_grid(h, w, fg)
    # separators
    for r in range(h):
        for c in range(w):
            if r % period == k or c % period == k:
                g[r][c] = 0
    # one hole per block at a random local position
    holes = {}
    for br in range(k):
        for bc in range(k):
            lr = rng.randint(0, k - 1); lc = rng.randint(0, k - 1)
            holes[(br, bc)] = (lr, lc)
            g[br * period + lr][bc * period + lc] = 0
    # avoid no-change: if every hole already sits on its diagonal, perturb one
    if all(holes[(br, bc)] == (br, bc) for br in range(k) for bc in range(k)):
        br = rng.randint(0, k - 1); bc = rng.randint(0, k - 1)
        g[br * period + br][bc * period + bc] = fg          # restore diagonal cell
        lr = (br + 1) % k; lc = bc
        g[br * period + lr][bc * period + lc] = 0           # new off-diagonal hole
    return g


def _draw_from_degenerate(name, k, rng):
    period = k + 1
    h = w = k * period - 1
    fg = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    g = full_grid(h, w, fg)
    if name == "empty_grid":
        return [[0] * w for _ in range(h)]
    if name == "full_grid":
        return g
    if name == "no_holes":
        for r in range(h):
            for c in range(w):
                if r % period == k or c % period == k:
                    g[r][c] = 0
        return g
    return g
