"""Generator for arc_puzzle_bank_21_set21_bundle:medium_p07 — corner-key transform crop.

Rule: at(0,0) is a key (1..7) selecting a transform. Pick the largest
non-corner blob, transform it (1=identity, 2=cw, 3=180, 4=ccw, 5=flip_lr,
6=flip_ud, else=transpose) and output its cropped grid.

Combinatorial axes (8): grid_h, grid_w, palette_kind, key,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_key, no_blob, square_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "42a0c35b41fd"
VERSION = "3.0.0"  # distinct=54/dup 38%: target = LARGEST object but the big blob was only 4-5 cells -> few distinct shapes. Enlarged the target blob to 4-8 cells (varied non-square via grow_blob) -> many more distinct shapes; output = target transformed by the (0,0) key.
TASK_ID = "42a0c35b41fd"
SUMMARY = (
    "0-bg grid (h ∈ 8-11, w ∈ 9-12) "
    "with: (a) ONE CORNER KEY at FIXED "
    "position (0, 0) — value ∈ {1..7} "
    "selecting a transform (per demos: "
    "1=identity, 2=cw90, 3=180, 4=ccw90, "
    "5=flip-LR, 6=flip-UD, 7=transpose); "
    "(b) ONE LARGE NON-CORNER BLOB — "
    "an irregular 4-5 cell blob in "
    "palette[0] (a non-key color "
    "drawn from {1..9}\\{key}) built by "
    "grow_blob random walk, placed "
    "away from (0, 0); (c) ONE SMALLER "
    "DECOY BLOB — a 2-cell blob in "
    "palette[1] (distinct from key + "
    "primary), placed to add visual "
    "noise but smaller than the "
    "primary. Rule (READ THE CORNER "
    "KEY, FIND THE LARGEST NON-CORNER "
    "BLOB, TRANSFORM IT BY THE KEY, "
    "CROP, OUTPUT): READ key from "
    "(0, 0) → select transform. EXTRACT "
    "every non-bg blob excluding the "
    "key cell. FIND the LARGEST blob "
    "(by cell count). CROP it to its "
    "bbox. APPLY the key's transform "
    "(identity / cw / 180 / ccw / "
    "flip_lr / flip_ud / transpose). "
    "OUTPUT the transformed crop. "
    "Net: the corner key picks one "
    "of 7 dihedral operations to "
    "apply to the cropped largest "
    "blob; smaller blobs are "
    "discarded."
)

INVARIANTS = [
    "background is 0",
    "(0,0) ∈ {1, 2, 3, 4, 5, 6, 7}",
    "the largest non-corner blob is strictly larger than any other (so target is unique)",
    "the largest blob is not at (0,0)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_key", "no_blob", "square_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "key":            {"type": "int", "default": "rng 1..7", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "key_corner_blob_body",
                       "valid": "key_corner_blob_body"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 9, 10); b_lo, b_hi = 4, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 12, 15); b_lo, b_hi = 5, 8
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 10, 13); b_lo, b_hi = 4, 7
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    key = rng.randint(1, 7)
    g[0][0] = key
    used = {(0, 0)}
    palette = rng.sample([c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c != key], 2)
    # the TARGET is the LARGEST object; bigger/varied target -> more distinct
    # transformed outputs (was 4-5 cells -> few shapes -> dup 38%).
    big = grow_blob(rng, h, w, used, rng.randint(b_lo, b_hi), max_attempts=80)
    if big is None:
        return g
    for r, c in big:
        g[r][c] = palette[0]
    used |= big
    small = grow_blob(rng, h, w, used, rng.randint(2, 2), max_attempts=40)
    if small is not None:
        for r, c in small:
            g[r][c] = palette[1]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_key":
        # blob without corner key → no transform dispatch
        for r, c in [(3, 3), (3, 4), (4, 3), (4, 4)]: g[r][c] = 4
        return g
    if name == "no_blob":
        # corner key alone, no blob → nothing to transform
        g[0][0] = 3
        return g
    if name == "square_blob":
        # blob is solid 2x2 square → all rotations/flips identical
        g[0][0] = 2
        for r in range(3, 5):
            for c in range(4, 6):
                g[r][c] = 4
        return g
    return g



def _components_for_self_check(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if (r, c) == (0, 0) or grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) != (0, 0)
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    key = grid[0][0]
    if key not in range(1, 8):
        msgs.append(f"corner key out of range: {key}")
    comps = _components_for_self_check(grid)
    if not comps:
        msgs.append("missing non-corner blob")
    else:
        sizes = sorted((len(c) for c in comps), reverse=True)
        if len(sizes) > 1 and sizes[0] <= sizes[1]:
            msgs.append(f"largest non-corner blob is not unique: sizes={sizes}")
        if sizes[0] < 4:
            msgs.append(f"target blob too small: sizes={sizes}")
    return msgs
