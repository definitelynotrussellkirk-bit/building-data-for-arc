"""Generator for 46c35fc7.

Rule: eight colored cells around each 3x3 orange-centered block undergo the
canonical ring permutation.

Combinatorial axes (9): grid_h, grid_w, block_count, palette_kind,
position_bias, anchor_corner, asymmetry_force, palette_size, ring_variant.
Degenerates: no_blocks, no_centers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import RING_3X3

GENERATOR_ID = "630d6cc550e4"
RULE_HASH = "6dfce0f7503c"
VERSION = "2.1.1"
TASK_ID = "630d6cc550e4"
SUMMARY = "Eight colored cells around 3x3 orange-centered block rotate clockwise."

INVARIANTS = [
    "the background and every block center are color 7",
    "each active block is a 3x3 ring with all eight border cells non-7",
    "blocks are separated so no extra overlapping 3x3 detections appear",
    "the canonical rule permutes only the border cells of each detected block",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_blocks", "no_centers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "block_count":    {"type": "int", "default": "rng 1..6 (band/capacity skewed)",
                       "valid": "1..6"},
    "grid_h":         {"type": "int", "default": "rng 7..16 (band-skewed)",
                       "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 7..16 (band-skewed)",
                       "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "position_bias":  {"type": "str", "default": "rng, skewed alternating",
                       "valid": "alternating|left|right"},
    "anchor_corner":  {"type": "bool", "default": "rng, skewed false",
                       "valid": "true|false", "probe": "diagnostic"},
    "asymmetry_force":{"type": "bool", "default": "rng",
                       "valid": "true|false", "probe": "diagnostic"},
    "palette_size":   {"type": "int", "default": "rng 2..available",
                       "valid": "2..9"},
    "ring_variant":   {"type": "str", "default": "ring", "valid": "ring",
                       "probe": "diagnostic"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary"},
}

# One 3x3 ring exposes eight border cells, so nine distinct observable colors
# require at least two blocks. This exact refusal is part of the public override
# contract rather than an accidental sampler failure.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"block_count": 1, "palette_size": 9},
]

# Destination ring cell -> source ring cell. This is copied from the canonical
# executable rule rather than inferred from the English rotation direction.
_RING_SOURCE = {
    (0, 0): (0, 2),
    (0, 1): (1, 0),
    (0, 2): (2, 2),
    (1, 0): (2, 1),
    (1, 2): (0, 1),
    (2, 0): (0, 0),
    (2, 1): (1, 2),
    (2, 2): (2, 0),
}


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    texture = overrides.get("texture")
    valid_textures = set(HELPFUL_TEXTURES) | set(DEGENERATE_TEXTURES)
    if texture is not None and texture not in valid_textures:
        raise ValueError(
            f"unknown texture {texture!r}; valid: {sorted(valid_textures)}"
        )
    for label in ("anchor_corner", "asymmetry_force"):
        value = overrides.get(label)
        if value is not None and type(value) is not bool:
            raise TypeError(f"{label} must be boolean")


def _detect_blocks(grid):
    """Canonical top-left detector used by both validation and rule_mirror."""
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(h - 2)
        for c in range(w - 2)
        if grid[r][c] != 7
        and grid[r + 1][c + 1] == 7
        and grid[r][c + 1] != 7
        and grid[r + 1][c] != 7
    ]


def rule_mirror(grid):
    """Python mirror of the canonical Racket cell permutation."""
    result = [row[:] for row in grid]
    for r0, c0 in _detect_blocks(grid):
        for (dr, dc), (sr, sc) in _RING_SOURCE.items():
            result[r0 + dr][c0 + dc] = grid[r0 + sr][c0 + sc]
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate a normal ring scene; canonical 7x7 inputs are in-domain."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []

    errors = []
    blocks = _detect_blocks(grid)
    if not blocks:
        errors.append("no canonical 3x3 orange-centered block found")
        return errors

    covered = set()
    for r0, c0 in blocks:
        for dr, dc in RING_3X3:
            if grid[r0 + dr][c0 + dc] == 7:
                errors.append(f"block at {(r0, c0)} has a color-7 border cell")
            covered.add((r0 + dr, c0 + dc))
        if grid[r0 + 1][c0 + 1] != 7:
            errors.append(f"block at {(r0, c0)} lacks a color-7 center")

    stray = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 7 and (r, c) not in covered
    ]
    if stray:
        errors.append(f"{len(stray)} non-7 cells lie outside detected rings")
    return errors


def observe_overrides(grid):
    """Recover exact returned-grid counts used by the override contract."""
    blocks = _detect_blocks(grid)
    ring_values = {
        grid[r0 + dr][c0 + dc]
        for r0, c0 in blocks
        for dr, dc in RING_3X3
    }
    return {
        "block_count": len(blocks),
        "palette_size": len(ring_values),
    }


def _boxes_conflict(left, right):
    """Require at least one background row or column between 3x3 blocks."""
    lr, lc = left
    rr, rc = right
    return not (
        lr + 3 < rr or rr + 3 < lr or lc + 3 < rc or rc + 3 < lc
    )


def _ordered_candidates(h, w, bias, rng):
    candidates = [(r, c) for r in range(h - 2) for c in range(w - 2)]
    jitter = {position: rng.random() for position in candidates}
    if bias == "left":
        candidates.sort(key=lambda p: (p[1], jitter[p]))
    elif bias == "right":
        candidates.sort(key=lambda p: (w - 3 - p[1], jitter[p]))
    else:
        candidates.sort(key=jitter.__getitem__)
    return candidates


def _choose_positions(h, w, count, *, bias, anchor_corner, rng):
    candidates = _ordered_candidates(h, w, bias, rng)
    corners = ((0, 0), (0, w - 3), (h - 3, 0), (h - 3, w - 3))

    for attempt in range(160):
        if attempt:
            rng.shuffle(candidates)
            # Restore the broad bias without collapsing support to fixed slots.
            if bias == "left":
                candidates.sort(key=lambda p: p[1] + rng.random() * max(1, w // 2))
            elif bias == "right":
                candidates.sort(
                    key=lambda p: (w - 3 - p[1]) + rng.random() * max(1, w // 2)
                )
        chosen = []
        if anchor_corner:
            allowed_corners = list(corners)
            if bias == "left":
                allowed_corners = [p for p in allowed_corners if p[1] == 0]
            elif bias == "right":
                allowed_corners = [p for p in allowed_corners if p[1] == w - 3]
            chosen.append(rng.choice(allowed_corners))
            if len(chosen) == count:
                return chosen
        for position in candidates:
            if position in chosen:
                continue
            if all(not _boxes_conflict(position, prior) for prior in chosen):
                chosen.append(position)
                if len(chosen) == count:
                    return chosen
    # Exact capacity fallback: edge-aligned slots preserve a full one-cell
    # separator and include all four corners. The randomized search above keeps
    # broad off-lattice support; this branch makes declared capacity reliable.
    def axis_slots(length):
        slot_count = (length + 1) // 4
        if slot_count <= 1:
            return [0]
        return [4 * index for index in range(slot_count - 1)] + [length - 3]

    fallback = [(r, c) for r in axis_slots(h) for c in axis_slots(w)]
    if bias == "left":
        fallback.sort(key=lambda position: (position[1], position[0]))
    elif bias == "right":
        fallback.sort(key=lambda position: (-position[1], position[0]))
    else:
        rng.shuffle(fallback)

    chosen = []
    if anchor_corner:
        allowed_corners = list(corners)
        if bias == "left":
            allowed_corners = [p for p in allowed_corners if p[1] == 0]
        elif bias == "right":
            allowed_corners = [p for p in allowed_corners if p[1] == w - 3]
        chosen.append(rng.choice(allowed_corners))
    for position in fallback:
        if position not in chosen:
            chosen.append(position)
        if len(chosen) == count:
            return chosen
    raise ValueError(f"could not place {count} separated blocks on {h}x{w}")


def _build_palette(kind, rng):
    """Return all nine non-center colors with a kind-specific prefix prior."""
    all_colors = [0, 1, 2, 3, 4, 5, 6, 8, 9]
    preferred = {
        "warm": [0, 2, 3, 4, 6, 9],
        "cool": [0, 1, 5, 8],
        "primary": [0, 1, 2, 3, 4],
        "broad": all_colors[:],
    }[kind]
    remainder = [color for color in all_colors if color not in preferred]
    rng.shuffle(preferred)
    rng.shuffle(remainder)
    return preferred + remainder


def _required_other_dimension(block_count, fixed_dimension):
    fixed_slots = max(1, (fixed_dimension + 1) // 4)
    other_slots = (block_count + fixed_slots - 1) // fixed_slots
    return max(7, 4 * other_slots - 1)


def _draw_dimensions(ctx, block_count_override):
    """Draw dimensions, expanding an unpinned side for an exact count request."""
    h_override = ctx.overrides.get("grid_h")
    w_override = ctx.overrides.get("grid_w")
    if block_count_override is None:
        return (
            ctx.draw_int_diff("grid_h", 7, 16),
            ctx.draw_int_diff("grid_w", 7, 16),
        )

    if h_override is not None:
        h = ctx.draw_int_diff("grid_h", 7, 16)
    else:
        h = None
    if w_override is not None:
        w = ctx.draw_int_diff("grid_w", 7, 16)
    else:
        w = None

    if h is not None and w is not None:
        return h, w
    if h is not None:
        minimum = _required_other_dimension(block_count_override, h)
        if minimum > 16:
            raise ValueError(
                f"block_count={block_count_override} cannot fit with grid_h={h}"
            )
        return h, ctx.draw_int_diff("grid_w", minimum, 16)
    if w is not None:
        minimum = _required_other_dimension(block_count_override, w)
        if minimum > 16:
            raise ValueError(
                f"block_count={block_count_override} cannot fit with grid_w={w}"
            )
        return ctx.draw_int_diff("grid_h", minimum, 16), w

    if block_count_override <= 4:
        return (
            ctx.draw_int_diff("grid_h", 7, 16),
            ctx.draw_int_diff("grid_w", 7, 16),
        )
    if ctx.draw_rng("count_dimension_orientation").choice((False, True)):
        return (
            ctx.draw_int_diff("grid_h", 11, 16),
            ctx.draw_int_diff("grid_w", 7, 16),
        )
    return (
        ctx.draw_int_diff("grid_h", 7, 16),
        ctx.draw_int_diff("grid_w", 11, 16),
    )


def _ring_is_invariant(values):
    by_cell = dict(zip(RING_3X3, values))
    return all(by_cell[cell] == by_cell[source]
               for cell, source in _RING_SOURCE.items())


def _make_ring_values(palette, rng, *, force_asymmetry):
    values = [rng.choice(palette) for _ in RING_3X3]
    if force_asymmetry and _ring_is_invariant(values):
        replacement = next(color for color in palette if color != values[-1])
        values[-1] = replacement
    return values


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    texture = overrides.get("texture")
    explicit_count = None
    if overrides.get("block_count") is not None:
        explicit_count = ctx.draw_int("block_count", 1, 6)
    explicit_palette_size = None
    if overrides.get("palette_size") is not None:
        explicit_palette_size = ctx.draw_int("palette_size", 2, 9)

    h, w = _draw_dimensions(ctx, explicit_count)
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx.draw_rng("degenerate"), h, w)

    capacity = min(6, ((h + 1) // 4) * ((w + 1) // 4))
    if explicit_count is not None:
        block_count = explicit_count
        if block_count > capacity:
            raise ValueError(
                f"block_count={block_count} cannot fit separated 3x3 rings on {h}x{w}"
            )
    else:
        minimum_for_palette = 2 if explicit_palette_size == 9 else 1
        if difficulty == "easy":
            lo, hi = minimum_for_palette, min(2, capacity)
        elif difficulty == "hard":
            lo, hi = max(minimum_for_palette, min(2, capacity)), capacity
        else:
            lo, hi = minimum_for_palette, min(4, capacity)
        if lo > hi:
            raise ValueError(
                f"palette_size={explicit_palette_size} cannot fit on {h}x{w}"
            )
        block_count = ctx.draw_int("block_count", lo, hi)

    palette_override = overrides.get("palette_kind")
    texture_palette = texture if texture in HELPFUL_TEXTURES else None
    if palette_override and texture_palette and palette_override != texture_palette:
        raise ValueError(
            f"texture {texture_palette!r} conflicts with palette_kind "
            f"{palette_override!r}"
        )
    if texture_palette and palette_override is None:
        ctx.overrides["palette_kind"] = texture_palette
    palette_kind = ctx.draw_choice("palette_kind", list(PALETTE_KINDS))

    position_bias = ctx.draw_choice(
        "position_bias", ["alternating", "alternating", "left", "right"]
    )
    anchor_corner = ctx.draw_choice(
        "anchor_corner", [False, False, False, True]
    )
    asymmetry_force = ctx.draw_choice("asymmetry_force", [False, True])
    ctx.draw_choice("ring_variant", ["ring"])

    layout_rng = ctx.draw_rng("layout")
    positions = _choose_positions(
        h, w, block_count, bias=position_bias,
        anchor_corner=anchor_corner, rng=layout_rng,
    )

    pool = _build_palette(palette_kind, ctx.draw_rng("palette"))
    if explicit_palette_size is not None:
        palette_size = explicit_palette_size
        if palette_size > 8 * block_count:
            raise ValueError(
                f"palette_size={palette_size} needs at least "
                f"{(palette_size + 7) // 8} blocks"
            )
    else:
        palette_size = ctx.draw_int("palette_size", 2, min(9, 8 * block_count))
    palette = pool[:palette_size]

    # Guarantee the declared palette is observable across the scene while still
    # sampling with replacement, which admits canonical repetitions.
    total = 8 * block_count
    flat_values = list(palette)
    flat_values.extend(layout_rng.choice(palette) for _ in range(total - len(palette)))
    layout_rng.shuffle(flat_values)

    g = full_grid(h, w, 7)
    for index, (r0, c0) in enumerate(positions):
        values = flat_values[index * 8:(index + 1) * 8]
        if asymmetry_force and _ring_is_invariant(values):
            replacement = next(color for color in palette if color != values[-1])
            values[-1] = replacement
        for (dr, dc), color in zip(RING_3X3, values):
            g[r0 + dr][c0 + dc] = color
        g[r0 + 1][c0 + 1] = 7
    return g


def _draw_from_degenerate(name, rng, h=7, w=11):
    g = full_grid(h, w, 7)
    if name == "no_blocks":
        return g
    if name == "no_centers":
        r0 = min(1, h - 3)
        c0 = min(1, w - 3)
        for r in range(r0, r0 + 3):
            for c in range(c0, c0 + 3):
                g[r][c] = 2
        return g
    if name == "full_grid":
        return full_grid(h, w, 2)
    raise ValueError(f"unknown degenerate texture {name!r}")
