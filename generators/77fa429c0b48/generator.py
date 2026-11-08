"""Generator for arc_puzzle_bank_21_set24_bundle:medium_p07 — paste largest component at color-8 marker.

Rule: a single color-8 marker cell + a single multi-cell component in some
non-{0, 8} color. Output centers the component's bbox crop at the marker.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker (no color-8 cell → rule's marker selector
returns nothing, paste position undefined), no_motif (marker present
but no multi-cell motif → rule has nothing to paste), motif_at_marker
(motif and marker overlap → rule's center-place collides with motif).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "77fa429c0b48"
VERSION = "2.0.1"
TASK_ID = "77fa429c0b48"

SUMMARY = (
    "0-bg grid (h~9-11, w~10-12) with: (a) ONE "
    "connected MOTIF (3-5 cells, polyomino-shaped) in "
    "some non-{0, 8} color, placed at a random "
    "position; (b) EXACTLY ONE color-8 (cyan) MARKER "
    "single-cell, placed elsewhere with no non-bg "
    "neighbors. Rule: find the motif (the largest "
    "connected non-{0, 8} component) and the marker "
    "(the lone color-8 cell). Compute the motif's bbox "
    "and CENTER. ERASE the motif from its current "
    "location and PASTE its bbox-cropped image onto the "
    "grid CENTERED at the marker cell. The marker is "
    "OVERWRITTEN by the motif (or remains if not "
    "covered). Net: input has a motif + a far-away "
    "marker; output has the motif relocated so its "
    "center sits where the marker was."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-8 single-cell marker",
    "exactly one connected motif (3-5 cells) in a non-{0, 8} color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_motif", "motif_at_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 10..12", "valid": "8..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "position_bias":     {"type": "str", "default": "marker_plus_motif",
                          "valid": "marker_plus_motif"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, exactly one color-8 marker, ≥1 multi-cell non-8 motif."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    marker_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(marker_cells) != 1:
        errs.append(f"found {len(marker_cells)} color-8 cells; expected exactly 1")
    motif_cells = [(r, c) for r in range(h) for c in range(w)
                   if grid[r][c] != 0 and grid[r][c] != 8]
    if len(motif_cells) < 3:
        errs.append(f"only {len(motif_cells)} non-8 cells; expected a ≥3-cell motif")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 12, 12)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 12)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
        cells = _build_motif(rng, rng.randint(3, 5))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        placed = False
        for _ in range(120):
            r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
            if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
            for r, c in cells:
                g[r0 + r - min(rs)][c0 + c - min(cs)] = color
            placed = True; break
        if not placed:
            continue
        for _ in range(120):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            if any(g[r + dr][c + dc] != 0 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                   if 0 <= r + dr < h and 0 <= c + dc < w):
                continue
            g[r][c] = 8
            return g
    raise ValueError("could not realize set24 medium_p07 layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # No color-8 — rule's marker selector returns nothing.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        return g
    if name == "no_motif":
        # Marker present but no motif — rule has nothing to paste.
        g[5][5] = 8
        return g
    if name == "motif_at_marker":
        # Motif and marker too close — center-place will collide.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 4
        g[3][5] = 8   # marker adjacent to motif
        return g
    return g
