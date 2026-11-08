"""Generator for 79a30e61d332.

Rule: matching 3x3 key tiles in a spaced tile grid become 8, and
intervening nonzero bridge tiles become 7.

Combinatorial axes (8): grid_h/w, bridge_axis, mask_shape,
palette_kind, anchor_corner, asymmetry_force, palette_size, position_bias.
Degenerates: no_keys, no_bridge, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "79a30e61d332"
VERSION = "3.1.0"
TASK_ID = "79a30e61d332"
SUMMARY = (
    "Canonical 4x6 lattice of 3x3 symbol tiles separated by zero gaps. "
    "One color-8 tile defines a sparse key mask; at least one other tile has "
    "the same mask, while nonzero tiles between key tiles become bridge color 7. "
    "Most tile slots are filled with distractor masks so the input stays in the "
    "high-object-count canonical regime instead of a three-tile toy demo."
)

INVARIANTS = [
    "tiles are 3x3 interiors separated by zero rows/columns at multiples of 4",
    "one key tile contains color 8",
    "at least two tiles share the key's nonzero mask",
    "nonzero bridge tiles lie between key tiles",
    "most lattice slots contain nonzero distractor symbols",
]

BRIDGE_AXES = ("horizontal", "vertical")
MASK_SHAPES = ("ell", "diag", "vee", "corner", "bar", "zig", "tee")
PALETTE_KINDS = ("canonical",)
DEGENERATE_TEXTURES = ("no_keys", "no_bridge", "full_grid")
HELPFUL_TEXTURES = MASK_SHAPES

MASKS = {
    "ell": [(0, 0), (0, 1), (1, 0), (2, 2)],
    "diag": [(0, 0), (1, 1), (2, 2)],
    "vee": [(0, 0), (1, 1), (0, 2), (2, 1)],
    "corner": [(0, 2), (1, 2), (2, 0), (2, 1), (2, 2)],
    "bar": [(0, 1), (1, 1), (2, 1)],
    "zig": [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)],
    "tee": [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
}

AXES = {
    "grid_h":         {"type": "int", "default": "17", "valid": "17"},
    "grid_w":         {"type": "int", "default": "25", "valid": "25"},
    "bridge_axis":    {"type": "str", "default": "rng", "valid": "|".join(BRIDGE_AXES)},
    "mask_shape":     {"type": "str", "default": "rng helpful", "valid": "|".join(MASK_SHAPES)},
    "palette_kind":   {"type": "str", "default": "canonical", "valid": "canonical"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "dense_tile_lattice", "valid": "dense_tile_lattice"},
    "texture":        {"type": "str", "default": "alias for mask_shape", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint_tile(g, tr, tc, color, cells):
    r0 = 1 + 4 * tr
    c0 = 1 + 4 * tc
    for dr, dc in cells:
        g[r0 + dr][c0 + dc] = color


def _tile_mask(grid, tr, tc):
    return tuple(
        1 if grid[1 + 4 * tr + dr][1 + 4 * tc + dc] != 0 else 0
        for dr in range(3) for dc in range(3)
    )


def _nonzero_tile(grid, tr, tc):
    return any(grid[1 + 4 * tr + dr][1 + 4 * tc + dc] != 0 for dr in range(3) for dc in range(3))


def _between(x, a, b):
    return min(a, b) < x < max(a, b)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    tile_rows, tile_cols = 4, 6
    h, w = 4 * tile_rows + 1, 4 * tile_cols + 1
    g = full_grid(h, w, 0)
    axis = ctx.draw_choice("bridge_axis", list(BRIDGE_AXES))
    tx = overrides.get("texture")
    if tx in MASKS:
        key_name = tx
    elif overrides.get("mask_shape") in MASKS:
        key_name = overrides["mask_shape"]
    else:
        key_name = ctx.draw_choice("mask_shape", list(MASKS))
    key_mask = MASKS[key_name]
    distractor_names = [name for name in MASKS if name != key_name]

    # Fill nearly every tile with a distractor symbol so the generator mirrors
    # the canonical dense symbol lattice and does not collapse to three objects.
    for tr in range(tile_rows):
        for tc in range(tile_cols):
            name = rng.choice(distractor_names)
            _paint_tile(g, tr, tc, 1, MASKS[name])

    if axis == "horizontal":
        tr = rng.randint(0, tile_rows - 1)
        c0 = rng.randint(0, tile_cols - 3)
        c1 = rng.randint(c0 + 2, tile_cols - 1)
        key_a, key_b = (tr, c0), (tr, c1)
        bridge = [(tr, c) for c in range(c0 + 1, c1)]
    else:
        tc = rng.randint(0, tile_cols - 1)
        r0 = rng.randint(0, tile_rows - 3)
        r1 = rng.randint(r0 + 2, tile_rows - 1)
        key_a, key_b = (r0, tc), (r1, tc)
        bridge = [(r, tc) for r in range(r0 + 1, r1)]

    # Overwrite the selected line: one visible key is color 8, the second key
    # is color 1 with the same mask, and bridge tiles remain nonzero distractors.
    _clear_tile(g, *key_a)
    _clear_tile(g, *key_b)
    _paint_tile(g, key_a[0], key_a[1], 8, key_mask)
    _paint_tile(g, key_b[0], key_b[1], 1, key_mask)
    for tr, tc in bridge:
        _clear_tile(g, tr, tc)
        # Solid or tee-like bridges both get recolored to 7 by the rule.
        cells = [(r, c) for r in range(3) for c in range(3)] if rng.randint(0, 1) else MASKS[rng.choice(distractor_names)]
        _paint_tile(g, tr, tc, 1, cells)
    return g


def _clear_tile(g, tr, tc):
    for dr in range(3):
        for dc in range(3):
            g[1 + 4 * tr + dr][1 + 4 * tc + dc] = 0


def self_check(grid, *, difficulty=None, meta=None):
    """Verify dense 3x3-tile key/bridge lattice invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    if (h, w) != (17, 25):
        errs.append(f"expected canonical 17x25 tile lattice; got {h}x{w}")
    if h < 5 or w < 5 or (h - 1) % 4 or (w - 1) % 4:
        return errs + ["shape is not a 3x3-tile lattice with one-cell zero gaps"]
    tile_rows, tile_cols = (h - 1) // 4, (w - 1) // 4
    for r in range(0, h, 4):
        if any(grid[r][c] != 0 for c in range(w)):
            errs.append(f"gap row {r} is not all zero")
            break
    for c in range(0, w, 4):
        if any(grid[r][c] != 0 for r in range(h)):
            errs.append(f"gap col {c} is not all zero")
            break
    nonempty = [(tr, tc) for tr in range(tile_rows) for tc in range(tile_cols) if _nonzero_tile(grid, tr, tc)]
    if len(nonempty) < 20:
        errs.append(f"expected dense symbol lattice; got only {len(nonempty)} nonempty tiles")
    seed_tiles = [(tr, tc) for tr, tc in nonempty if any(grid[1 + 4 * tr + dr][1 + 4 * tc + dc] == 8 for dr in range(3) for dc in range(3))]
    if len(seed_tiles) != 1:
        errs.append(f"expected exactly one color-8 key tile; got {len(seed_tiles)}")
        return errs
    key_mask = _tile_mask(grid, *seed_tiles[0])
    key_tiles = [(tr, tc) for tr, tc in nonempty if _tile_mask(grid, tr, tc) == key_mask]
    if len(key_tiles) < 2:
        errs.append("expected at least two tiles sharing the key mask")
    has_bridge = False
    for a in key_tiles:
        for b in key_tiles:
            if a == b:
                continue
            if a[0] == b[0]:
                has_bridge |= any(_nonzero_tile(grid, a[0], tc) for tc in range(tile_cols) if _between(tc, a[1], b[1]))
            if a[1] == b[1]:
                has_bridge |= any(_nonzero_tile(grid, tr, a[1]) for tr in range(tile_rows) if _between(tr, a[0], b[0]))
    if not has_bridge:
        errs.append("expected a nonzero bridge tile between key tiles")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(17, 25, 0)
    if name == "no_keys":
        for tr in range(4):
            for tc in range(6):
                _paint_tile(g, tr, tc, 1, MASKS["ell"])
        return g
    if name == "no_bridge":
        _paint_tile(g, 0, 0, 8, MASKS["ell"])
        _paint_tile(g, 0, 5, 1, MASKS["ell"])
        return g
    if name == "full_grid":
        for tr in range(4):
            for tc in range(6):
                _paint_tile(g, tr, tc, 8, [(r, c) for r in range(3) for c in range(3)])
        return g
    return g
