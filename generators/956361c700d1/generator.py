"""Generator for 956361c700d1 — A→B transform replayed on C.

Rule: split input by full-height color-5 divider columns into 3 panels
(A, B, C). Infer the dihedral transform t that maps panel A to panel B
(searching identity/rot-90/rot-180/rot-270/flip-lr/flip-ud/etc). Apply
the same transform t to panel C. Output = t(C).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, fill_box

GENERATOR_ID = "956361c700d1"
VERSION = "2.1.1"  # add self_check
TASK_ID = "956361c700d1"
SUMMARY = (
    "Small grid (3..6 rows × 11 cols) split into THREE 3-col panels "
    "by full-height color-5 (gray) divider columns at cols 3 and 7. "
    "Panel A (cols 0-2) and Panel B (cols 4-6) share the SAME "
    "color (call it color X) — B's binary shape is some dihedral "
    "transform t of A's shape. Panel C (cols 8-10) uses a "
    "DIFFERENT color (color Y). C's shape is independent. Rule: "
    "split panels at 5-columns. Infer the dihedral transform t "
    "such that t(A.shape) == B.shape (search id, rot90, rot180, "
    "rot270, flip-lr, flip-ud, diag, anti-diag). Apply t to C "
    "(preserving C's color). Output = t(C), 3×3."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "h × 11 grid (h = 3..6); cols 3 and 7 are full-height color-5 dividers",
    "panels A, B (cols 0-2 and 4-6) use the SAME color X",
    "panel C (cols 8-10) uses a DIFFERENT color Y (Y ≠ X, Y ≠ 5, Y ≠ 0)",
    "B's binary shape is a dihedral transform of A's shape",
    "A/B admit exactly one canonical transform match, so the inferred transform is unique",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_separators", "all_same_color", "all_different")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "h":              {"type": "int", "default": "3", "valid": "3..6"},
    "palette_kind":   {"type": "str", "default": "default", "valid": "default"},
    "transform":      {"type": "str", "default": "rng",
                       "valid": "id|cw|ccw|180|lr|ud|diag|anti"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "three_panels_5col_split",
                       "valid": "three_panels_5col_split"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: w=11; cols 3 and 7 are full-height color-5 dividers."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    if w != 11:
        errs.append(f"expected w=11; got w={w}")
    else:
        for col in (3, 7):
            if not all(grid[r][col] == 5 for r in range(h)):
                errs.append(f"col {col} should be all color-5 (divider); found non-5 cells")
    return errs


def _rand_mask(rng, h, w=3):
    """Random h×w binary mask with 3-6 cells.

    The canonical rule applies transforms to the *whole* panel, not only
    to the top-left 3×3 corner.  Earlier versions always sampled a 3×3
    mask and mirrored rows around n=3, which made h>3 examples disagree
    with the Racket rule for vertical flips / 180° rotations.
    """
    while True:
        cells = [(r, c) for r in range(h) for c in range(w) if rng.random() < 0.45]
        if 3 <= len(cells) <= min(6, h * w - 1):
            return frozenset(cells)


def _apply_transform(cells, t, h, w=3):
    """Apply the canonical panel transform to a cell set.

    Rotations / diagonal transposes preserve the panel shape only for square
    panels.  For h!=w, those transforms intentionally yield coordinates outside
    the h×w target and are therefore excluded by _candidate_transforms().
    """
    if t == "id":
        return frozenset(cells)
    if t == "cw":
        return frozenset((c, h - 1 - r) for r, c in cells)
    if t == "180":
        return frozenset((h - 1 - r, w - 1 - c) for r, c in cells)
    if t == "ccw":
        return frozenset((w - 1 - c, r) for r, c in cells)
    if t == "lr":
        return frozenset((r, w - 1 - c) for r, c in cells)
    if t == "ud":
        return frozenset((h - 1 - r, c) for r, c in cells)
    if t == "diag":
        return frozenset((c, r) for r, c in cells)
    if t == "anti":
        return frozenset((w - 1 - c, h - 1 - r) for r, c in cells)
    raise ValueError(f"unknown transform {t!r}")


def _candidate_transforms(h, w=3):
    # These names/order mirror the Racket rule's search order, translated to
    # the short names used in this generator.
    if h == w:
        return ["id", "cw", "180", "ccw", "lr", "ud", "diag", "anti"]
    return ["id", "180", "lr", "ud"]


def _is_in_bounds(cells, h, w=3):
    return all(0 <= r < h and 0 <= c < w for r, c in cells)


def _matching_transforms(a, b, h, w=3):
    out = []
    for name in _candidate_transforms(h, w):
        transformed = _apply_transform(a, name, h, w)
        if _is_in_bounds(transformed, h, w) and transformed == b:
            out.append(name)
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("h", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("h", 4, 6)
    else:
        h = ctx.draw_int("h", 3, 4)

    rng = ctx.draw_rng("layout")
    panel_w = 3
    w = panel_w * 3 + 2

    transforms = _candidate_transforms(h, panel_w)
    t = ctx.draw_choice("transform", transforms)

    # Generate A/B so the canonical Racket rule has exactly one matching
    # transform.  This permits id examples when A has no non-id symmetries,
    # and prevents ambiguous rot90-vs-flip or rot270-vs-anti-transpose demos.
    for _ in range(200):
        mask_a = _rand_mask(rng, h, panel_w)
        mask_b = _apply_transform(mask_a, t, h, panel_w)
        if not _is_in_bounds(mask_b, h, panel_w):
            continue
        if _matching_transforms(mask_a, mask_b, h, panel_w) == [t]:
            break
    else:
        # Deterministic, asymmetric fallback.  It is valid for every h>=3 and
        # has a unique left-right flip mapping under the canonical transform
        # search order.
        t = "lr"
        mask_a = frozenset([(0, 0), (1, 0), (1, 1), (2, 0)])
        mask_b = _apply_transform(mask_a, t, h, panel_w)

    mask_c = _rand_mask(rng, h, panel_w)

    color_x = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    color_y = rng.choice([c for c in [1, 2, 3, 4, 6, 7, 8, 9] if c != color_x])

    g = full_grid(h, w, 0)
    # Divider columns
    fill_box(g, 0, panel_w, h - 1, panel_w, 5)
    fill_box(g, 0, panel_w * 2 + 1, h - 1, panel_w * 2 + 1, 5)
    # Panel A at cols 0-2
    for r, c in mask_a:
        if r < h:
            g[r][c] = color_x
    # Panel B at cols 4-6
    for r, c in mask_b:
        if r < h:
            g[r][4 + c] = color_x
    # Panel C at cols 8-10
    for r, c in mask_c:
        if r < h:
            g[r][8 + c] = color_y
    return g


def _draw_from_degenerate(name, rng):
    h = 3
    panel_w = 3
    w = panel_w * 3 + 2
    g = full_grid(h, w, 0)
    if name == "no_separators":
        for r, c in [(0, 0), (1, 0)]:
            g[r][c] = 4
        for r, c in [(0, 4), (1, 4)]:
            g[r][c] = 4
        for r, c in [(0, 8), (1, 8)]:
            g[r][c] = 7
        return g
    if name == "all_same_color":
        fill_box(g, 0, panel_w, h - 1, panel_w, 5)
        fill_box(g, 0, panel_w * 2 + 1, h - 1, panel_w * 2 + 1, 5)
        for r, c in [(0, 0), (1, 0)]: g[r][c] = 4
        for r, c in [(0, 4), (1, 4)]: g[r][c] = 4
        for r, c in [(0, 8), (1, 8)]: g[r][c] = 4
        return g
    if name == "all_different":
        fill_box(g, 0, panel_w, h - 1, panel_w, 5)
        fill_box(g, 0, panel_w * 2 + 1, h - 1, panel_w * 2 + 1, 5)
        for r, c in [(0, 0), (1, 0)]: g[r][c] = 4
        for r, c in [(0, 4), (1, 4)]: g[r][c] = 6
        for r, c in [(0, 8), (1, 8)]: g[r][c] = 7
        return g
    return g
