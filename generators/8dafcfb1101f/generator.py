"""Generator for arc_puzzle_bank_ninth21:M61 — translate by anchor vector.

Rule: 1-cell = src marker, 2-cell = dst marker. Each non-{0,1,2} cell
moves by (dst - src). Output: empty grid + translated cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: missing_src, missing_dst, no_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "8dafcfb1101f"
VERSION = "1.3.2"
RULE_HASH = "8ab33123477f"
TASK_ID = "8dafcfb1101f"
SUMMARY = "Color-1 src + color-2 dst markers define a translation vector; rule translates each non-{0,1,2} cell by (dst-src) on a fresh empty grid (markers erased)."

# Rivals: 'translate by fixed offset' refuted by ≥2 demos with
# different vectors. 'preserve markers in output' refuted by any
# demo (markers gone). 'use marker color for translated cells'
# refuted by ≥1 demo with multi-color blobs each translated in its
# own color. 'apply to grid as whole (shift)' refuted by any demo
# where bg cells in output are not src/dst positions.
# 4 demos with varied vectors + blob shapes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one 1-cell, exactly one 2-cell, ≥2 non-{0,1,2} blob cells",
    "translated blob cells are in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_src", "missing_dst", "no_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1",
                       "probe": "diagnostic"},
    "position_bias":  {"type": "str", "default": "src_dst_blob",
                       "valid": "src_dst_blob", "probe": "diagnostic"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1",
                          "probe": "diagnostic"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse",
                       "probe": "diagnostic"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 11)
        n_blobs = 1
        blob_size_lo, blob_size_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        n_blobs = rng.randint(2, 4)
        blob_size_lo, blob_size_hi = 3, 6
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        n_blobs = rng.randint(1, 3)
        blob_size_lo, blob_size_hi = 2, 4
    for _layout_attempt in range(80):
        g = full_grid(h, w, 0)
        used: set[tuple[int, int]] = set()
        # Rotate deterministically through all four signed quadrants.  The old
        # upper-left -> middle placement made every production displacement
        # nonnegative, so an absolute-vector rival fit all generated labels.
        sign_r, sign_c = ((1, 1), (-1, 1), (1, -1), (-1, -1))[sample_index % 4]
        dr = sign_r * rng.randint(1, max(1, h // 3))
        dc = sign_c * rng.randint(1, max(1, w // 3))
        src_r_lo, src_r_hi = max(0, -dr), min(h - 1, h - 1 - dr)
        src_c_lo, src_c_hi = max(0, -dc), min(w - 1, w - 1 - dc)
        src = (rng.randint(src_r_lo, src_r_hi), rng.randint(src_c_lo, src_c_hi))
        dst = (src[0] + dr, src[1] + dc)
        g[src[0]][src[1]] = 1
        g[dst[0]][dst[1]] = 2
        used.add(src); used.add(dst)
        translated_used: set[tuple[int, int]] = set()
        payload_cells = 0
        # One episode-level size is both a meaningful declared control and
        # recoverable from the returned grid (each blob has a unique color).
        blob_size = ctx.draw_int_strict("blob_size", blob_size_lo, blob_size_hi)
        blob_colors = rng.sample([3, 4, 5, 6, 7, 8, 9], min(7, n_blobs))
        for color in blob_colors:
            for _ in range(30):
                blob = grow_blob(rng, h, w, used, blob_size,
                                 max_attempts=80)
                if blob is None:
                    continue
                translated = {(r + dr, c + dc) for r, c in blob}
                if not all(0 <= rr < h and 0 <= cc < w for rr, cc in translated):
                    continue
                # Keep the executed output unambiguous: payload cells may not
                # translate onto markers or onto another translated payload cell.
                if translated & used or translated & translated_used:
                    continue
                for r, c in blob:
                    g[r][c] = color
                used |= blob
                translated_used |= translated
                payload_cells += len(blob)
                break
        if payload_cells >= 2:
            return g
    raise ValueError("could not place a nonempty translated payload")


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "missing_src":
        # only dst (2), no src (1) → no source anchor, translation undefined
        g[2][2] = 2
        for r, c in [(5, 5), (5, 6)]: g[r][c] = 4
        return g
    if name == "missing_dst":
        # only src (1), no dst (2) → no destination anchor
        g[2][2] = 1
        for r, c in [(5, 5), (5, 6)]: g[r][c] = 4
        return g
    if name == "no_blob":
        # markers but no payload to translate → no-op rule
        g[2][2] = 1
        g[5][5] = 2
        return g
    return g
def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    src = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    dst = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    payload = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 1, 2)]
    if len(src) != 1 or len(dst) != 1:
        errors.append(f"expected exactly one src and dst marker, got src={len(src)} dst={len(dst)}")
        return errors
    if len(payload) < 2:
        errors.append(f"expected at least two payload cells, got {len(payload)}")
    dr = dst[0][0] - src[0][0]; dc = dst[0][1] - src[0][1]
    translated = [(r + dr, c + dc) for r, c in payload]
    if any(not (0 <= r < h and 0 <= c < w) for r, c in translated):
        errors.append("some translated payload cells leave the grid")
    if set(translated) & set(src + dst):
        errors.append("translated payload collides with a marker, hiding output")
    if len(set(translated)) != len(translated):
        errors.append("multiple payload cells translate to the same output cell")
    return errors


def observe_overrides(grid):
    """Recover exact, externally controllable axes from one generated grid."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    counts = {}
    for row in grid:
        for value in row:
            if value not in (0, 1, 2):
                counts[value] = counts.get(value, 0) + 1
    if not counts:
        raise ValueError("grid has no payload blob")
    sizes = set(counts.values())
    if len(sizes) != 1:
        raise ValueError(f"payload blobs do not share one declared blob_size: {sorted(sizes)}")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "blob_size": next(iter(sizes))}
