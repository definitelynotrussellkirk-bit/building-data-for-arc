"""Nested rectangular frames: zero cells belong to their smallest container.

Normal samples contain two hollow frames (three on hard). Each sample has
both an outer-annulus zero and an innermost zero, distinguishing ownership
from indiscriminate filling with the outer frame color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at, draw_rect_outline

GENERATOR_ID = "6470a9c16f7b"
VERSION = "1.3.0"
TASK_ID = "6470a9c16f7b"
SUMMARY = "Fill nested hollow frames by the smallest enclosing frame's color."
INVARIANTS = [
    "2 or 3 strictly nested hollow rectangular frames of distinct nonzero colors",
    "production draws have outer-annulus and innermost zero witnesses",
]
PALETTES = {
    "default": tuple(range(1, 10)),
    "warm": (2, 4, 7, 9),
    "cool": (1, 3, 6, 8),
    "varied": tuple(range(1, 10)),
}
PALETTE_KINDS = tuple(PALETTES)
DEGENERATE_TEXTURES = ("no_frame", "no_inner_shape", "frame_too_small")
HELPFUL_TEXTURES = PALETTE_KINDS
AXES = {
    "grid_h": {"type": "int", "default": "rng 8..10; hard 9..10", "valid": "7..14, must fit frames"},
    "grid_w": {"type": "int", "default": "rng 11..13", "valid": "7..16, must fit frames"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "default|warm|cool|varied"},
    "frame_h": {"type": "int", "default": "rng minimum..grid_h", "valid": "7..14; minimum 9 for 3 frames"},
    "frame_w": {"type": "int", "default": "rng minimum..grid_w", "valid": "7..16; minimum 9 for 3 frames"},
    "n_frames": {"type": "int", "default": "2; hard 3", "valid": "2..3"},
    "palette_size": {"type": "int", "default": "n_frames", "valid": "2..3; must equal n_frames"},
    "n_distinct_colors": {"type": "int", "default": "n_frames", "valid": "2..3; must equal n_frames"},
    "position_bias": {"type": "str", "default": "frame_with_inner", "valid": "frame_with_inner"},
    "density": {"type": "str", "default": "frame", "valid": "frame"},
    "texture": {"type": "str", "default": "alias for palette_kind",
                "valid": "default|warm|cool|varied|no_frame|no_inner_shape|frame_too_small"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown overrides: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None:
            expected = int if AXES[name]["type"] == "int" else str
            if type(value) is not expected:
                raise TypeError(f"{name} must be {expected.__name__}")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        if any(value is not None for name, value in overrides.items() if name != "texture"):
            raise ValueError("degenerate textures do not support additional axis overrides")
        return _draw_from_degenerate(texture, None)
    requested_counts = {overrides[k] for k in ("n_frames", "palette_size", "n_distinct_colors")
                        if overrides.get(k) is not None}
    if len(requested_counts) > 1:
        raise ValueError("n_frames, palette_size and n_distinct_colors must agree")
    settings = dict(overrides)
    if requested_counts:
        settings["n_frames"] = requested_counts.pop()
    if texture is not None:
        if overrides.get("palette_kind") not in (None, texture):
            raise ValueError("texture and palette_kind must agree")
        settings["palette_kind"] = texture
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=settings)
    if settings.get("n_frames") is not None:
        count = ctx.draw_int_strict("n_frames", 2, 3)
    else:
        count = ctx.draw_int_strict("n_frames", 3 if difficulty == "hard" else 2,
                             3 if difficulty == "hard" else 2)
    ctx.draw_int_strict("palette_size", count, count)
    ctx.draw_int_strict("n_distinct_colors", count, count)
    ctx.draw_choice("position_bias", ("frame_with_inner",))
    ctx.draw_choice("density", ("frame",))
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    minimum = 2 * count + 3

    def dimension(label, lo, hi, default_lo, default_hi):
        if settings.get(label) is not None:
            return ctx.draw_int_strict(label, lo, hi)
        return ctx.draw_int_strict(label, max(lo, default_lo), max(lo, default_hi))

    h = dimension("grid_h", minimum, 14, 9 if difficulty == "hard" else 8,
                  8 if difficulty == "easy" else 10)
    w = dimension("grid_w", minimum, 16, 12 if difficulty == "hard" else 11,
                  11 if difficulty == "easy" else 13)
    fr = ctx.draw_int_strict("frame_h", minimum, h)
    fc = ctx.draw_int_strict("frame_w", minimum, w)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    colors = rng.sample(PALETTES[palette_kind], count)
    r0 = rng.randint(0, h - fr); c0 = rng.randint(0, w - fc)
    for index, color in enumerate(colors):
        draw_rect_outline(g, r0, c0, fr, fc, color)
        remaining = count - index - 1
        if remaining:
            # A full zero-cell gap at the first boundary guarantees an outer
            # annulus. Later frames may be adjacent, as in canonical examples.
            gap = 2 if index == 0 else 1
            inner_h = rng.randint(2 * remaining + 1, fr - 2 * gap)
            inner_w = rng.randint(2 * remaining + 1, fc - 2 * gap)
            r0 += rng.randint(gap, fr - inner_h - gap)
            c0 += rng.randint(gap, fc - inner_w - gap)
            fr, fc = inner_h, inner_w
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 12, 0)
    if name == "no_frame":
        paint_at(g, 4, 3, [(0, i) for i in range(4)], 6)
    elif name == "no_inner_shape":
        draw_rect_outline(g, 1, 1, 6, 8, 4)
    elif name == "frame_too_small":
        draw_rect_outline(g, 2, 2, 3, 3, 4)
    return g


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is not rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["grid colors must be integers in 0..9"]
    colors = {v for row in grid for v in row if v != 0}
    if len(colors) not in (2, 3):
        return ["expected 2 or 3 distinct frame colors"]
    frames = []
    for color in colors:
        cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
        r1, c1, r2, c2 = _bbox(cells)
        outline = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                   if r in (r1, r2) or c in (c1, c2)}
        if r2 - r1 < 2 or c2 - c1 < 2 or cells != outline:
            return ["every nonzero color must form exactly one hollow rectangular frame"]
        frames.append((r1, c1, r2, c2))
    frames.sort(key=lambda f: (f[2] - f[0] + 1) * (f[3] - f[1] + 1), reverse=True)
    for outer, inner in zip(frames, frames[1:]):
        if not (outer[0] < inner[0] < inner[2] < outer[2]
                and outer[1] < inner[1] < inner[3] < outer[3]):
            return ["frames must be strictly nested"]
    return []
