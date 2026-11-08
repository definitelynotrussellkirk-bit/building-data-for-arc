"""Generator for arc_puzzle_bank_fourth21:H27.

Rule: find the monochromatic 4-connected objects, rank them by descending
occupied-cell count and then top-left position, normalize the two winners,
and paint the union of their normalized shapes in color 8.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "306f5b5f899c"
RULE_HASH = "2cde2dccfbeb"
VERSION = "3.1.1"
TASK_ID = "306f5b5f899c"

SUMMARY = (
    "A sparse 0-background scene contains 2-5 separated connected motifs, "
    "including canonical singleton distractors. The output is the normalized "
    "union of the two largest motifs, painted color 8; ties use top-left order."
)

INVARIANTS = [
    "background is 0 and every non-zero cell belongs to a connected motif",
    "2-5 motifs are separated by at least one background cell",
    "the two largest motifs determine the normalized color-8 output",
]

PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 3, 4, 6, 9),
    "cool": (1, 5, 7, 8, 9),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}
PALETTE_KINDS = tuple(PALETTES)
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS
# Repeated object colors are unusual but still legal for the executable rule.
LAWFUL_DEGENERATE_TEXTURES = ("all_same_color",)

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "difficulty-skewed 9..16", "valid": "9..16"},
    "n": {"type": "int", "default": "difficulty-skewed 2..5", "valid": "2..5"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "default|warm|cool|varied",
    },
    "palette_size": {
        "type": "int",
        "default": "difficulty-skewed 2..5",
        "valid": "2..5",
        "probe": "diagnostic",
    },
    "position_bias": {
        "type": "str",
        "default": "scattered_colored_motifs",
        "valid": "scattered_colored_motifs",
        "probe": "diagnostic",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "2..min(n,palette_size)",
        "valid": "2..5",
    },
    "density": {"type": "str", "default": "sparse", "valid": "sparse",
                "probe": "diagnostic"},
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "default|warm|cool|varied",
    },
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


def _objects(grid):
    """Return monochromatic 4-connected objects in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < h and 0 <= cc < w):
                    continue
                if (rr, cc) in seen or grid[rr][cc] != color:
                    continue
                seen.add((rr, cc))
                cells.append((rr, cc))
                stack.extend(
                    ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1))
                )
            result.append((color, cells))
    return result


def _object_info(entry):
    color, cells = entry
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    normalized = {(r - r0, c - c0) for r, c in cells}
    return {
        "color": color,
        "cells": cells,
        "top_left": (r0, c0),
        "normalized": normalized,
        "height": max(r for r, _ in normalized) + 1,
        "width": max(c for _, c in normalized) + 1,
    }


def rule_mirror(grid):
    """Python mirror of the canonical executable rule."""
    ranked = sorted(
        (_object_info(entry) for entry in _objects(grid)),
        key=lambda obj: (-len(obj["cells"]), obj["top_left"]),
    )
    if len(ranked) < 2:
        raise ValueError("rule requires at least two objects")
    first, second = ranked[:2]
    union = first["normalized"] | second["normalized"]
    h = max(first["height"], second["height"])
    w = max(first["width"], second["width"])
    return [[8 if (r, c) in union else 0 for c in range(w)] for r in range(h)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical sparse-object grammar, including singletons."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    entries = _objects(grid)
    errors = []
    if not (2 <= len(entries) <= 5):
        errors.append(f"expected 2-5 motifs, found {len(entries)}")
        return errors

    occupied = [(r, c, color) for color, cells in entries for r, c in cells]
    for i, (r, c, color) in enumerate(occupied):
        for rr, cc, other_color in occupied[i + 1:]:
            if color != other_color and abs(r - rr) + abs(c - cc) == 1:
                errors.append("different-colored motifs touch orthogonally")
                return errors
    try:
        rule_mirror(grid)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def observe_overrides(grid):
    """Recover exact object and distinct-color counts from a returned grid."""
    entries = _objects(grid)
    return {
        "n": len(entries),
        "n_distinct_colors": len({color for color, _ in entries}),
    }


def _build_motif(rng, size, max_span):
    """Grow a connected polyomino in a compact but shape-diverse box."""
    if size == 1:
        return [(0, 0)]
    if size > max_span * max_span:
        raise ValueError(f"size {size} exceeds {max_span}x{max_span} motif box")
    center = max_span // 2
    cells = {(center, center)}
    while len(cells) < size:
        frontier = set()
        for r, c in cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if (0 <= nxt[0] < max_span and 0 <= nxt[1] < max_span
                        and nxt not in cells):
                    frontier.add(nxt)
        cells.add(rng.choice(sorted(frontier)))
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _shape_sizes(n, sample_index, rng, h, w):
    max_leader = 9 if min(h, w) >= 9 and n <= 4 else 7
    if n == 2:
        first = rng.randint(4, max_leader)
        second = rng.randint(3, max_leader)
        return [first, second]

    mode = sample_index % 4
    first = rng.randint(5, max_leader)
    if mode == 1:
        second = first
    elif mode == 0:
        second = rng.randint(3, min(5, max_leader))
    else:
        second = rng.randint(3, max_leader)
    leaders = [first, second]
    distractors = [1]
    while len(leaders) + len(distractors) < n:
        distractors.append(rng.randint(1, max(1, min(3, min(leaders) - 1))))
    sizes = leaders + distractors
    rng.shuffle(sizes)
    return sizes


def _bbox(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _free(grid, r0, c0, sh, sw):
    h, w = len(grid), len(grid[0])
    for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
            if grid[r][c] != 0:
                return False
    return True


def _place_scene(h, w, colors, sizes, rng):
    specifications = []
    max_span = 4 if min(h, w) >= 9 and len(colors) <= 4 else 3
    for color, size in zip(colors, sizes):
        shape = _build_motif(rng, size, max_span)
        sh, sw = _bbox(shape)
        specifications.append((sh * sw, size, color, shape, sh, sw))
    # Hardest-to-place motifs first; positions remain fully random.
    specifications.sort(reverse=True, key=lambda item: (item[0], item[1]))

    grid = full_grid(h, w, 0)
    for _, _, color, shape, sh, sw in specifications:
        candidates = [
            (r0, c0)
            for r0 in range(h - sh + 1)
            for c0 in range(w - sw + 1)
            if _free(grid, r0, c0, sh, sw)
        ]
        rng.shuffle(candidates)
        if not candidates:
            return None
        r0, c0 = candidates[0]
        for r, c in shape:
            grid[r0 + r][c0 + c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    normalized = dict(overrides)
    texture = normalized.get("texture")
    if texture in HELPFUL_TEXTURES:
        palette_override = normalized.get("palette_kind")
        if palette_override is not None and palette_override != texture:
            raise ValueError(
                f"texture {texture!r} conflicts with palette_kind {palette_override!r}"
            )
        normalized["palette_kind"] = texture

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=normalized,
    )
    h = ctx.draw_int_diff("grid_h", 7, 14)
    w = ctx.draw_int_diff("grid_w", 9, 16)
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, h, w)

    requested_distinct = normalized.get("n_distinct_colors")
    distinct_floor = 2 if requested_distinct is None else int(requested_distinct)
    if not 2 <= distinct_floor <= 5:
        raise ValueError(
            "n_distinct_colors override must be an integer in [2, 5]"
        )
    requested_n = normalized.get("n")
    if requested_n is not None and int(requested_n) < distinct_floor:
        raise ValueError(
            "n must be at least n_distinct_colors when both are overridden"
        )
    requested_palette_size = normalized.get("palette_size")
    if (requested_palette_size is not None
            and int(requested_palette_size) < distinct_floor):
        raise ValueError(
            "palette_size must be at least n_distinct_colors when both are overridden"
        )

    n = ctx.draw_int_diff("n", distinct_floor, 5)
    palette_kind = ctx.draw_choice("palette_kind", list(PALETTE_KINDS))
    palette_size = ctx.draw_int_diff("palette_size", distinct_floor, 5)
    distinct_count = ctx.draw_int_diff(
        "n_distinct_colors", 2, min(n, palette_size)
    )
    ctx.draw_choice("position_bias", ["scattered_colored_motifs"])
    ctx.draw_choice("density", ["sparse"])

    palette_rng = ctx.draw_rng("palette")
    pool = list(PALETTES[palette_kind])
    palette_rng.shuffle(pool)
    palette = pool[:palette_size]
    distinct = palette_rng.sample(palette, distinct_count)
    colors = list(distinct)
    colors.extend(palette_rng.choice(distinct) for _ in range(n - len(colors)))
    palette_rng.shuffle(colors)

    shape_rng = ctx.draw_rng("shapes")
    sizes = _shape_sizes(n, sample_index, shape_rng, h, w)
    layout_rng = ctx.draw_rng("layout")
    for _ in range(128):
        grid = _place_scene(h, w, colors, sizes, layout_rng)
        if grid is not None and not self_check(grid):
            return grid
        # A fresh compact growth can change bboxes while preserving sizes.
        layout_rng.random()
    raise ValueError(f"could not realize {n} separated motifs on {h}x{w}")


def _draw_from_degenerate(name, h=10, w=12):
    grid = full_grid(h, w, 0)
    if name == "no_motifs":
        return grid
    if name == "single_motif":
        for r, c in ((1, 1), (1, 2), (2, 2), (2, 3)):
            if r < h and c < w:
                grid[r][c] = 4
        return grid
    if name == "all_same_color":
        placements = (
            ((0, 0), (0, 1), (1, 1)),
            ((max(0, h // 2 - 1), max(0, w // 2 - 1)),
             (max(0, h // 2 - 1), w // 2),
             (h // 2, w // 2)),
            ((h - 1, w - 1),),
        )
        for shape in placements:
            for r, c in shape:
                if 0 <= r < h and 0 <= c < w:
                    grid[r][c] = 4
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")
