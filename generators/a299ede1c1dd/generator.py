"""Generator for 865f9924.

Rule: for each non-bg object, if its bbox touches grid border, recolor
to 2; else recolor to 8.

Combinatorial axes (8): grid_h/w, n_border_blobs, n_interior_blobs,
blob_size_range, blob_layout, palette_kind, position_bias,
blob_color_distribution.
Degenerates: all_border, all_interior, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "a299ede1c1dd"
VERSION = "1.1.1"
TASK_ID = "a299ede1c1dd"
SUMMARY = "Border-touching blobs → 2, interior → 8."

INVARIANTS = [
    "background is 0",
    ">=1 border-touching blob",
    ">=1 interior blob",
    "blobs don't touch (4-conn separation)",
    "no colors 2 or 8 in input (rule writes them for output)",
]

BLOB_LAYOUTS = ("scattered", "edges", "corners", "balanced", "compact")
DEGENERATE_TEXTURES = ("all_border", "all_interior", "no_blobs")
HELPFUL_TEXTURES = BLOB_LAYOUTS

AXES = {
    "grid_h":               {"type": "int", "default": "rng 8..14", "valid": "7..18"},
    "grid_w":               {"type": "int", "default": "rng 8..14", "valid": "7..18"},
    "n_border_blobs":       {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_interior_blobs":     {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "blob_size_range":      {"type": "str", "default": "rng small|medium|large",
                             "valid": "small|medium|large"},
    "blob_layout":          {"type": "str", "default": "rng helpful",
                             "valid": "|".join(BLOB_LAYOUTS)},
    "palette_kind":         {"type": "str", "default": "rng all_six|broad",
                             "valid": "all_six|broad"},
    "position_bias":        {"type": "str", "default": "rng spread|center",
                             "valid": "spread|center"},
    "texture":              {"type": "str", "default": "alias for blob_layout",
                             "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: no colors 2 or 8 present (rule writes them); both border and
    interior non-bg blobs exist."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in (2, 8):
                errs.append(f"color {grid[r][c]} in input at ({r},{c}); rule writes 2/8 for output")
                return errs
    # Check we have at least one border blob and one interior blob
    border_rows = {0, h - 1}
    border_cols = {0, w - 1}
    has_border_nonbg = any(
        grid[r][c] != 0
        for r in range(h) for c in range(w)
        if r in border_rows or c in border_cols
    )
    has_interior_nonbg = any(
        grid[r][c] != 0
        for r in range(1, h - 1) for c in range(1, w - 1)
    )
    if not has_border_nonbg:
        errs.append("no non-bg cell touches the border (no border blob)")
    if not has_interior_nonbg:
        errs.append("no non-bg cell in the interior (no interior blob)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 7, 9
    elif difficulty == "hard":
        h_lo, h_hi = 13, 18
    else:
        h_lo, h_hi = 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_border = int(overrides.get("n_border_blobs",
                                 ctx.draw_int("n_border_blobs", 1, 3)))
    n_interior = int(overrides.get("n_interior_blobs",
                                   ctx.draw_int("n_interior_blobs", 1, 3)))
    n_border = max(1, min(5, n_border))
    n_interior = max(1, min(5, n_interior))
    size_kind = overrides.get("blob_size_range",
                              ctx.draw_choice("blob_size_range",
                                              ["small", "medium", "large"]))
    s_lo, s_hi = {"small": (2, 3), "medium": (3, 4),
                  "large": (4, 5)}[size_kind]
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 ["all_six", "broad"]))
    if palette_kind == "all_six":
        palette = [6]
    else:
        palette = [c for c in [1, 3, 4, 5, 6, 7, 9] if c not in (2, 8)]
    g = full_grid(h, w, 0)
    used = set()
    placed_border = 0
    placed_interior = 0
    for _ in range(n_border * 6):
        if placed_border >= n_border:
            break
        size = rng.randint(s_lo, s_hi)
        seed_r = rng.choice([0, h - 1])
        seed_c = rng.randint(0, w - 1)
        if (seed_r, seed_c) in used:
            continue
        blob = _grow_from(seed_r, seed_c, h, w, used, size, rng)
        if blob is None:
            continue
        on_border = any(r in (0, h - 1) or c in (0, w - 1)
                        for r, c in blob)
        if not on_border:
            continue
        used |= blob
        color = rng.choice(palette)
        for r, c in blob:
            g[r][c] = color
        placed_border += 1
    for _ in range(n_interior * 6):
        if placed_interior >= n_interior:
            break
        size = rng.randint(s_lo, s_hi)
        seed_r = rng.randint(2, h - 3) if h >= 5 else h // 2
        seed_c = rng.randint(2, w - 3) if w >= 5 else w // 2
        if (seed_r, seed_c) in used:
            continue
        blob = _grow_from(seed_r, seed_c, h, w, used, size, rng)
        if blob is None:
            continue
        on_border = any(r in (0, h - 1) or c in (0, w - 1)
                        for r, c in blob)
        if on_border:
            continue
        used |= blob
        color = rng.choice(palette)
        for r, c in blob:
            g[r][c] = color
        placed_interior += 1
    if placed_border < 1:
        g[0][0] = palette[0]
    if placed_interior < 1:
        g[h // 2][w // 2] = palette[0]
    return g


def _grow_from(sr, sc, h, w, used, target_size, rng):
    cells = {(sr, sc)}
    if (sr, sc) in used:
        return None
    frontier = [(sr, sc)]
    while frontier and len(cells) < target_size:
        r, c = frontier.pop(rng.randint(0, len(frontier) - 1))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            if (nr, nc) in used or (nr, nc) in cells:
                continue
            cells.add((nr, nc))
            frontier.append((nr, nc))
            if len(cells) >= target_size:
                break
    if len(cells) < 2:
        return None
    # Check no neighbor of cells is already used (4-conn separation)
    for r, c in cells:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if (nr, nc) in used:
                return None
    return cells


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    color = 6
    if name == "all_border":
        for c in range(w):
            g[0][c] = color
        return g
    if name == "all_interior":
        for r in range(2, h - 2):
            for c in range(2, w - 2):
                if rng.random() < 0.4:
                    g[r][c] = color
        return g
    if name == "no_blobs":
        return g
    return g
