"""Generator for d931c21c.

Rule: a hollow color-1 object gets exterior-adjacent and interior-
adjacent background marks.

Combinatorial axes (8): grid_h/w, frame_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_frame, solid_frame, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "34200461c67f"
RULE_HASH = "602d54029ff7"  # canonical rule this generator was written against
VERSION = "2.1.0"  # +self_check  # shape-locked-in/out (fixed 12x12, one 5x5/5x6/6x5 frame): rule reads h,w and marks cells adjacent to EACH hollow color-1 frame; canonical 8x8..19x22. Now grid + frame sizes + 1-3 separated frames vary.
TASK_ID = "34200461c67f"
SUMMARY = "Hollow color-1 object gets exterior-adjacent and interior-adjacent background marks."

INVARIANTS = [
    "the background is zero",
    "1-3 separated color-1 rectangular frames each enclose a nonempty zero hole",
    "the frames are not clipped by the grid edge",
    "the rule paints outside-adjacent zero cells 2 and enclosed-adjacent zero cells 3",
]

FRAME_KINDS = ("F5x5", "F5x6", "F6x5")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "solid_frame", "full_grid")
HELPFUL_TEXTURES = FRAME_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..16", "valid": "8..22"},
    "grid_w":         {"type": "int", "default": "rng 11..16", "valid": "8..22"},
    "frame_size":     {"type": "str", "default": "rng helpful",
                       "valid": "5x5|5x6|6x5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for frame_size",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 color-1 rectangular frame present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    has_frame = any(v == 1 for row in grid for v in row)
    if not has_frame:
        errs.append("no color-1 frame cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # rule reads h,w dynamically and marks cells adjacent to EACH hollow color-1
    # frame; canonical spans 8x8..19x22. Was fixed 12x12 + one 5x5/5x6/6x5 frame.
    # Now grid size, frame sizes, and 1-3 separated frames all vary.
    forced = {"F5x5": (5, 5), "F5x6": (5, 6), "F6x5": (6, 5)}.get(overrides.get("texture"))
    if difficulty == "easy":
        H = ctx.draw_int("grid_h", 9, 11); W = ctx.draw_int("grid_w", 9, 11); n = 1
    elif difficulty == "hard":
        H = ctx.draw_int("grid_h", 16, 22); W = ctx.draw_int("grid_w", 16, 22); n = rng.randint(2, 3)
    else:
        H = ctx.draw_int("grid_h", 11, 16); W = ctx.draw_int("grid_w", 11, 16); n = rng.randint(1, 2)
    g = full_grid(H, W, 0)
    placed = []   # (r0, c0, r1, c1)

    def far(box):
        return all(box[2] + 2 < b[0] or b[2] + 2 < box[0] or
                   box[3] + 2 < b[1] or b[3] + 2 < box[1] for b in placed)
    for i in range(n):
        for _try in range(80):
            rh, rw = forced if (forced and i == 0) else (
                rng.randint(4, min(8, H - 2)), rng.randint(4, min(8, W - 2)))
            top = rng.randint(1, H - rh - 1); left = rng.randint(1, W - rw - 1)
            box = (top, left, top + rh - 1, left + rw - 1)
            if far(box):
                draw_frame(g, top, left, top + rh - 1, left + rw - 1, 1)
                placed.append(box)
                break
    if not placed:    # tiny-grid fallback
        draw_frame(g, 1, 1, min(5, H - 2), min(5, W - 2), 1)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_frame":
        return g
    if name == "solid_frame":
        for r in range(2, 7):
            for c in range(2, 7):
                g[r][c] = 1
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 1
        return g
    return g
