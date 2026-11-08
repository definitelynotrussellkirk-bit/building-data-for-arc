"""Generator for 4b:m25 — rotate the color-1 template by a {2,3,4,5} key, center.

Rule (verified against the canonical Racket):
  The TEMPLATE is the bbox of the color-1 cells (a non-rectangular blob).
  The KEY is the single cell whose color is in {2,3,4,5}; it selects a
  rotation: 2=identity, 3=rotate-cw, 4=rotate-180, 5=rotate-ccw. The
  output is a blank same-size canvas with the rotated template pasted
  (as color 1) centered.

POISON FIX (was v1.1.0): the old generator painted the blob and the key
with a RANDOM 2-colour sample, so most instances had no color-1 template
(`find-color 1` empty -> degenerate/identical outputs, the 28% dup) and a
key that was usually NOT in {2,3,4,5}. The blob colour MUST be 1 and the
key MUST be in {2,3,4,5}; the key also drives a 4-way rotation branch, so
it must vary across all four values and every difficulty.

Combinatorial axes (8): grid_h, grid_w, key (rotation), blob_size,
blob_shape, corner, blob_position, difficulty.
Degenerates: no_key, no_blob, rectangular_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "1aec632783b9"
VERSION = "2.0.1"  # POISON FIX: blob MUST be color 1 (the template) and key MUST be in {2,3,4,5} (rotation selector). Old gen used a random 2-color sample -> usually no color-1 template (degenerate identical outputs, 28% dup) and a non-rotation key. Now: blob always color 1, key drawn from {2,3,4,5} so all 4 rotation branches fire across difficulties; bigger non-rectangular blobs + varied corner/grid size -> distinct 40 -> ~140.
TASK_ID = "1aec632783b9"
SUMMARY = (
    "0-bg grid with: (a) ONE non-rectangular "
    "BLOB of color 1 (the template); (b) ONE KEY "
    "cell whose color is in {2,3,4,5} at a corner "
    "(2=identity, 3=cw, 4=180, 5=ccw). Rule: "
    "extract the color-1 bbox as a template, "
    "rotate it by the key, and paste it (color 1) "
    "centered on a blank same-size canvas."
)

INVARIANTS = [
    "background is 0",
    "exactly one blob, colored 1 (the template)",
    "the blob is non-rectangular (bbox has at least one hole) so rotations differ",
    "exactly one key cell, color in {2,3,4,5} (the rotation selector)",
    "the key is the only cell whose color is in {2,3,4,5}",
]

KEYS = (2, 3, 4, 5)  # rotation selectors: 2=id, 3=cw, 4=180, 5=ccw
DEGENERATE_TEXTURES = ("no_key", "no_blob", "rectangular_blob")
HELPFUL_TEXTURES = ("identity", "cw", "rot180", "ccw")

AXES = {
    "grid_h":   {"type": "int", "default": "rng 8..14", "valid": "7..16"},
    "grid_w":   {"type": "int", "default": "rng 8..14", "valid": "7..16"},
    "key":      {"type": "int", "default": "rng {2,3,4,5}", "valid": "2|3|4|5"},
    "blob_size":{"type": "int", "default": "rng by difficulty", "valid": "3..9"},
    "corner":   {"type": "str", "default": "rng of 4 corners",
                 "valid": "tl|tr|bl|br"},
    "texture":  {"type": "str", "default": "alias for key/rotation",
                 "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _is_rectangular(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    bb = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
    return bb == len(cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        b_lo, b_hi = 3, 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        b_lo, b_hi = 6, 9
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        b_lo, b_hi = 4, 7
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    # KEY: the rotation selector, MUST be in {2,3,4,5}. Draw it explicitly so
    # all four rotation branches are exercised across instances/difficulties.
    key = int(overrides.get("key", ctx.draw_choice("key", list(KEYS))))
    corner = ctx.draw_choice("corner",
                             [(0, w - 1), (0, 0), (h - 1, 0), (h - 1, w - 1)])
    g[corner[0]][corner[1]] = key
    # reserve the key corner + its neighbours so the blob stays separate
    used = {corner}
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            used.add((corner[0] + dr, corner[1] + dc))

    # BLOB: the template, MUST be color 1, and non-rectangular so rotations
    # produce visibly different outputs. Bigger blobs -> richer distinct shapes.
    target = max(3, min(ctx.draw_int("blob_size", b_lo, b_hi), (h * w) // 3))
    placed = False
    for _ in range(80):
        cells = grow_blob(rng, h, w, used, target, max_attempts=40)
        if cells is None:
            continue
        if _is_rectangular(cells):
            continue
        for r, c in cells:
            g[r][c] = 1
        placed = True
        break
    if not placed:
        # guaranteed non-rectangular fallback: an L-tetromino near the center
        cr, cc = h // 2, w // 2
        for r, c in [(cr, cc), (cr + 1, cc), (cr + 1, cc + 1), (cr + 1, cc + 2)]:
            if 0 <= r < h and 0 <= c < w and (r, c) not in used:
                g[r][c] = 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: color-1 blob cells present; exactly one key cell in {2,3,4,5}."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    c1 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    keys = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (2, 3, 4, 5)]
    if not c1:
        errs.append("no color-1 template cells")
    if len(keys) != 1:
        errs.append(f"expected exactly 1 key cell in {{2,3,4,5}}, found {len(keys)}")
    return errs


def _draw_from_degenerate(name):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_key":
        # color-1 blob without a {2,3,4,5} key -> rotation undefined
        for r, c in [(4, 3), (4, 4), (4, 5), (5, 4)]:
            g[r][c] = 1
        return g
    if name == "no_blob":
        # key without a color-1 template -> nothing to rotate
        g[0][w - 1] = 3
        return g
    if name == "rectangular_blob":
        # exact-bbox-fill template -> rotation under any key looks identical
        g[0][w - 1] = 3
        for r in range(4, 6):
            for c in range(3, 6):
                g[r][c] = 1
        return g
    return g
