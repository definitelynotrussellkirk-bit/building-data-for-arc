"""Generator for puzzle b94a9452.

Rule: find the single two-color region on background 0, crop to its
nonzero bounding box, and swap the outer and inner colors.

The sampler deliberately varies inner-mask topology. Centered solid blocks
remain in support, but off-center rectangles, connected non-solid masks, and
hollow rings prevent a solid-centered-bbox shortcut from fitting every draw.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f22baf82ea81"
VERSION = "2.2.0"
TASK_ID = "f22baf82ea81"
SUMMARY = (
    "0-bg grid (h, w~10-16) with one filled two-color rectangular region. "
    "The outer color fills the bbox and the inner color forms a centered solid "
    "block, an off-center block, a connected non-solid mask, or a hollow ring, "
    "always strictly inside the bbox. Rule: crop the nonzero bbox and swap the "
    "outer and inner colors everywhere in the crop."
)

INVARIANTS = [
    "background is 0",
    "single filled rectangular two-color region",
    "bbox top-left cell is the outer color",
    ">=1 inner-color cell occurs strictly inside",
]

POSITION_BIASES = ("scattered", "centered", "corners", "spread")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
INNER_SHAPES = ("centered_rect", "off_center_rect", "connected_growth", "hollow_ring")
DEGENERATE_TEXTURES = ("single_color", "no_region", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h": {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "grid_w": {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "region_h": {"type": "int", "default": "rng 4..7", "valid": "3..10"},
    "region_w": {"type": "int", "default": "rng 4..7", "valid": "3..10"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
    },
    "inner_shape": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(INNER_SHAPES),
    },
    "position_bias": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(POSITION_BIASES),
    },
    "texture": {
        "type": "str",
        "default": "alias for position_bias",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        h_lo, h_hi = 8, 11
    elif difficulty == "hard":
        h_lo, h_hi = 16, 20
    else:
        h_lo, h_hi = 10, 16
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    placement_rng = ctx.draw_rng("placement")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, h, w, placement_rng)

    # Preserve the ordinary 4..7 distribution while honoring the documented
    # 3..10 override domain without eagerly validating overrides against 4..7.
    if overrides.get("region_h") is not None:
        rh = ctx.draw_int("region_h", 3, 10)
    else:
        rh = ctx.draw_int("region_h", 4, 7)
    if overrides.get("region_w") is not None:
        rw = ctx.draw_int("region_w", 3, 10)
    else:
        rw = ctx.draw_int("region_w", 4, 7)
    rh = max(3, min(h - 2, rh))
    rw = max(3, min(w - 2, rw))

    palette_kind = ctx.draw_choice("palette_kind", list(PALETTE_KINDS))
    outer, inner = _build_palette(palette_kind, 2, placement_rng)
    if texture in HELPFUL_TEXTURES:
        bias = texture
    else:
        bias = ctx.draw_choice("position_bias", list(POSITION_BIASES))
    rr, rc = _pick_position(bias, h, w, rh, rw, placement_rng)
    inner_shape = ctx.draw_choice("inner_shape", list(INNER_SHAPES))
    inner_rng = ctx.draw_rng("inner_layout")

    grid = full_grid(h, w, 0)
    for r in range(rr, rr + rh):
        for c in range(rc, rc + rw):
            grid[r][c] = outer
    for r, c in _sample_inner_cells(inner_shape, rh, rw, inner_rng):
        grid[rr + r][rc + c] = inner
    return grid


def _sample_inner_cells(shape, rh, rw, rng):
    """Return local cells strictly inside a region of shape rh x rw."""
    ih, iw = rh - 2, rw - 2
    if ih <= 0 or iw <= 0:
        return {(1, 1)}

    if shape == "centered_rect":
        sh = rng.randint(1, ih)
        sw = rng.randint(1, iw)
        r0 = (ih - sh) // 2
        c0 = (iw - sw) // 2
        cells = {(r, c) for r in range(r0, r0 + sh) for c in range(c0, c0 + sw)}
    elif shape == "off_center_rect":
        sh = max(1, min(ih, rng.randint(1, max(1, ih - 1))))
        sw = max(1, min(iw, rng.randint(1, max(1, iw - 1))))
        choices = [(0, 0), (0, iw - sw), (ih - sh, 0), (ih - sh, iw - sw)]
        centered = ((ih - sh) // 2, (iw - sw) // 2)
        choices = [pos for pos in dict.fromkeys(choices) if pos != centered] or [(0, 0)]
        r0, c0 = rng.choice(choices)
        cells = {(r, c) for r in range(r0, r0 + sh) for c in range(c0, c0 + sw)}
    elif shape == "hollow_ring" and ih >= 3 and iw >= 3:
        cells = {
            (r, c)
            for r in range(ih)
            for c in range(iw)
            if r in (0, ih - 1) or c in (0, iw - 1)
        }
    else:
        # Connected L-shaped support, optionally reflected. It is non-solid for
        # any interior at least 2x2 and remains a single 4-connected component.
        cells = {(r, 0) for r in range(ih)} | {(ih - 1, c) for c in range(iw)}
        if rng.random() < 0.5:
            cells = {(ih - 1 - r, c) for r, c in cells}
        if rng.random() < 0.5:
            cells = {(r, iw - 1 - c) for r, c in cells}

    return {(r + 1, c + 1) for r, c in cells}


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    return pool[:n]


def _pick_position(bias, h, w, rh, rw, rng):
    if bias == "centered":
        return max(1, (h - rh) // 2), max(1, (w - rw) // 2)
    if bias == "corners":
        return rng.choice(
            [
                (1, 1),
                (1, w - rw - 1),
                (h - rh - 1, 1),
                (h - rh - 1, w - rw - 1),
            ]
        )
    return rng.randint(1, h - rh - 1), rng.randint(1, w - rw - 1)


def _draw_from_degenerate(name, h, w, rng):
    grid = full_grid(h, w, 0)
    if name == "single_color":
        for r in range(2, min(6, h)):
            for c in range(2, min(6, w)):
                grid[r][c] = 3
        return grid
    if name == "no_region":
        return grid
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                grid[r][c] = 3 if (r + c) % 2 == 0 else 4
        return grid
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not all(isinstance(row, list) and row for row in grid):
        return ["grid is empty or malformed"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["rows are ragged"]
    cells = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    ]
    if not cells:
        return ["missing nonzero 2-color region"]
    colors = {v for _, _, v in cells}
    if len(colors) != 2:
        errors.append(f"expected exactly 2 region colors, got {sorted(colors)}")
    r0 = min(r for r, _, _ in cells)
    r1 = max(r for r, _, _ in cells)
    c0 = min(c for _, c, _ in cells)
    c1 = max(c for _, c, _ in cells)
    if r0 <= 0 or c0 <= 0 or r1 >= h - 1 or c1 >= w - 1:
        errors.append("region bbox should have a 0-background margin")
    for r in range(h):
        for c in range(w):
            in_bbox = r0 <= r <= r1 and c0 <= c <= c1
            if in_bbox and grid[r][c] == 0:
                errors.append("region bbox contains background holes")
                break
            if not in_bbox and grid[r][c] != 0:
                errors.append("nonzero cell outside the single region bbox")
                break
        if errors and errors[-1] in {
            "region bbox contains background holes",
            "nonzero cell outside the single region bbox",
        }:
            break
    outer = grid[r0][c0]
    inner_colors = colors - {outer}
    if not inner_colors:
        errors.append("bbox top-left outer color has no distinct inner color")
    else:
        inner = next(iter(inner_colors))
        if not any(
            grid[r][c] == inner
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
        ):
            errors.append("inner color is not present strictly inside the bbox")
    return errors
