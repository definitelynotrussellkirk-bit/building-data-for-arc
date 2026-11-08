"""Generator for arc_puzzle_bank_21_next:hard_c05 — frame parity flips interior.

Rectangular frame color controls the flip applied to its interior contents:
odd frame colors flip left-right, even frame colors flip top-bottom.

Combinatorial axes (8): n_frames, interior_h, interior_w, palette_kind,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_interior, single_parity.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "79a14745b917"
VERSION = "1.2.1"
TASK_ID = "79a14745b917"
SUMMARY = "Two frames contain asymmetric interior marks; one odd and one even frame color teach both parity flips."

INVARIANTS = [
    "all frames are rectangular outlines",
    "every normal sample contains one odd-color frame and one even-color frame",
    "odd frame colors require a left-right interior flip",
    "even frame colors require an up-down interior flip",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_interior", "single_parity")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "n_frames":       {"type": "int", "default": "2", "valid": "2"},
    "interior_h":     {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "interior_w":     {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "position_bias":  {"type": "str", "default": "side_by_side_frames",
                       "valid": "side_by_side_frames"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint_pattern(g, r0, c0, ih, iw, colors):
    cells = [(0, 0, colors[0]), (1, 0, colors[0]), (1, 1, colors[1]),
             (ih - 1, iw - 2, colors[2]), (ih - 2, iw - 1, colors[2])]
    for r, c, v in cells:
        g[r0 + r][c0 + c] = v


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥2 distinct non-zero colors (one odd, one even) and ≥2 nonzero cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    odd_colors = {c for c in colors if c % 2 == 1}
    even_colors = {c for c in colors if c % 2 == 0}
    if not odd_colors:
        errs.append("no odd-color frame found (rule branch for LR flip absent)")
    if not even_colors:
        errs.append("no even-color frame found (rule branch for UD flip absent)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # A single-frame example only demonstrates one branch of the conditional
    # rule.  Always include one odd and one even frame so every generated pair
    # teaches both LR-vs-UD cases directly, matching the original hard task's
    # pedagogy while preserving the same canonical transformation.
    n_frames = ctx.draw_int("n_frames", 2, 2)
    if difficulty == "easy":
        ih = ctx.draw_int("interior_h", 3, 3)
        iw = ctx.draw_int("interior_w", 4, 4)
    elif difficulty == "hard":
        ih = ctx.draw_int("interior_h", 4, 5)
        iw = ctx.draw_int("interior_w", 5, 6)
    else:
        ih = ctx.draw_int("interior_h", 3, 4)
        iw = ctx.draw_int("interior_w", 4, 5)
    fh, fw = ih + 2, iw + 2
    h = fh + 4
    w = n_frames * fw + (n_frames + 1) * 2
    g = full_grid(h, w, 0)
    odds = [3, 7]
    evens = [4, 8]
    frame_options = [rng.choice(odds), rng.choice(evens)]
    rng.shuffle(frame_options)

    for i in range(n_frames):
        r0 = 2
        c0 = 2 + i * (fw + 2)
        frame_color = frame_options[i]
        draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, frame_color)
        inside_colors = rng.sample([c for c in range(1, 10) if c != frame_color], 3)
        _paint_pattern(g, r0 + 1, c0 + 1, ih, iw, inside_colors)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 14, 0)
    if name == "no_frame":
        # Interior pattern present but no frame outline — rule has no
        # frame-color parity to read from.
        _paint_pattern(g, 3, 3, 4, 5, [4, 6, 7])
        return g
    if name == "no_interior":
        # Frame present but interior is empty — rule has no asymmetric
        # marks to flip.
        draw_frame(g, 2, 2, 7, 7, 3)
        return g
    if name == "single_parity":
        # Two frames but both odd-colored — rule's parity-vs-flip
        # mapping has only one demonstrated case.
        draw_frame(g, 2, 2, 7, 6, 3)
        _paint_pattern(g, 3, 3, 4, 4, [1, 2, 6])
        draw_frame(g, 2, 8, 7, 12, 7)
        _paint_pattern(g, 3, 9, 4, 4, [1, 2, 6])
        return g
    return g
