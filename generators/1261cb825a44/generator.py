"""Generator for arc_puzzle_bank_21_set19_bundle:medium_p03 — corner-key crop.

Rule: one of 4 corner cells is non-zero (the "key color"). Output is
the cells of all `key-color` cells in the grid (excluding any corner
positions), packed to a min-bbox subgrid.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_distractors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_corner_key, no_blob, no_distractors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "1261cb825a44"
VERSION = "2.2.0"  # reject incomplete layouts; resample until key and distractors are present
TASK_ID = "1261cb825a44"
SUMMARY = (
    "0-bg grid (h ∈ 9-12, w ∈ 10-13) with: "
    "(a) ONE CORNER KEY CELL — exactly "
    "one of the 4 grid corners (0,0), "
    "(0,w-1), (h-1,0), or (h-1,w-1) is "
    "painted in key_color (drawn from "
    "palette[0] ∈ {1..9}); (b) ONE "
    "KEY-COLORED BLOB inside the grid — "
    "a 3-5 cell irregular blob via "
    "grow_blob in the SAME key_color, "
    "placed AWAY from any corner (retry "
    "if any cell lands on a corner); "
    "(c) 1-2 DISTRACTOR BLOBS in OTHER "
    "colors (palette[1:] = 2 distinct "
    "non-key colors), each a 3-5 cell "
    "blob also placed away from "
    "corners. Rule (READ THE CORNER "
    "KEY, FILTER THE GRID TO KEEP ONLY "
    "KEY-COLORED NON-CORNER CELLS, "
    "CROP TO THEIR BBOX, OUTPUT): "
    "IDENTIFY the unique non-bg CORNER "
    "cell — its color is the KEY. "
    "FILTER all grid cells: KEEP only "
    "cells whose color == key_color "
    "AND whose position is NOT a "
    "corner. COMPUTE the bbox of the "
    "kept cells. CROP to that bbox: "
    "OUTPUT a smaller grid containing "
    "only the key-colored blob "
    "(with 0s where the bbox has no "
    "key cells). Net: the corner "
    "color picks which blob to "
    "extract; the cropped key-blob "
    "is the answer; distractors and "
    "corner are discarded."
)

INVARIANTS = [
    "background is 0",
    "exactly one corner cell is non-zero (the key)",
    "at least one non-corner blob has the key color (so output is non-empty)",
    "1-2 other-colored distractor blobs exist (so the key matters)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_corner_key", "no_blob", "no_distractors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_distractors":  {"type": "int", "default": "2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "corner_key_blobs_inside",
                       "valid": "corner_key_blobs_inside"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject ordinary draws without the key, payload, and distractor roles."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    key_positions = [(r, c) for r, c in corners if grid[r][c] != 0]
    texture = (meta or {}).get("texture") if isinstance(meta, dict) else None
    if texture in DEGENERATE_TEXTURES:
        return []
    errors = []
    if len(key_positions) != 1:
        errors.append(f"expected exactly one corner key, got {len(key_positions)}")
        return errors
    r, c = key_positions[0]
    key = grid[r][c]
    interior_keys = sum(v == key for rr, row in enumerate(grid)
                        for cc, v in enumerate(row) if (rr, cc) not in corners)
    other_colors = {v for row in grid for v in row if v not in (0, key)}
    if interior_keys < 3:
        errors.append(f"expected an interior key-colored blob, found {interior_keys} cells")
    if not other_colors:
        errors.append("expected at least one other-colored distractor")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 13, 16)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
    n_distractors = ctx.draw_int("n_distractors", 1, 3)
    if not 1 <= n_distractors <= 3:
        raise ValueError("n_distractors must be 1..3")
    rng = ctx.draw_rng("layout")
    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}

    # grow_blob does not mutate its forbidden set; using ALL corners as forbidden
    # prevents spurious second corner keys.  Never return partially built scenes.
    for _ in range(128):
        g = full_grid(h, w, 0)
        palette = rng.sample(range(1, 10), n_distractors + 1)
        key_color = palette[0]
        corner = rng.choice(sorted(corners))
        g[corner[0]][corner[1]] = key_color
        used = set(corners)
        blob = grow_blob(rng, h, w, used, rng.randint(4, 9), max_attempts=160)
        if blob is None:
            continue
        used.update(blob)
        for r, c in blob:
            g[r][c] = key_color
        success = True
        for color in palette[1:]:
            size = rng.randint(3, 5)
            distractor = grow_blob(rng, h, w, used, size, max_attempts=160)
            if distractor is None:
                success = False
                break
            used.update(distractor)
            for r, c in distractor:
                g[r][c] = color
        if success and not self_check(g):
            return g
    raise RuntimeError("could not place key blob and requested distractors")


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_corner_key":
        # No corner cell set — rule has no key color to filter by.
        g[3][3] = 4; g[3][4] = 4; g[4][3] = 4
        g[6][6] = 5; g[6][7] = 5
        return g
    if name == "no_blob":
        # Corner key set but no matching blob inside — output is empty.
        g[0][0] = 4
        g[5][5] = 6; g[5][6] = 6
        return g
    if name == "no_distractors":
        # Only the key color anywhere — rule has nothing to filter against.
        g[0][0] = 4
        g[3][3] = 4; g[3][4] = 4; g[4][3] = 4
        return g
    return g
