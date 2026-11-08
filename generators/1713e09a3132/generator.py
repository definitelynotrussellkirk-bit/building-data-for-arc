"""Generator for 1713e09a3132 — rectangle borders from diagonal pairs.

Each nonzero color appears exactly twice at opposite rectangle corners.  The
canonical Racket rule processes colors by first reading-order occurrence and
paints each bounding-box border, so later colors overwrite earlier borders at
collisions.  This generator deliberately includes both diagonal orientations,
long spans, and overlapping boxes.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1713e09a3132"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
SUMMARY = (
    "One to four colors each mark two diagonal corners of a rectangle. Draw "
    "every bounding-box border in first-reading-order color order; later "
    "borders overwrite earlier ones at overlaps. Native profiles include both "
    "diagonal orientations, overlapping boxes, and spans of eight or more."
)

INVARIANTS = [
    "background is 0",
    "each nonzero color occurs exactly twice at diagonal corners",
    "overlapping bounding boxes are lawful and teach reading-order overwrite",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_pairs", "collinear_pair")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
POSITION_BIASES = ("mixed", "separated", "overlap")
DENSITIES = ("sparse", "wide")

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 8..14", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "scheduled 9..14", "valid": "9..14"},
    "palette_kind": {"type": "str", "default": "scheduled helpful", "valid": "|".join(PALETTE_KINDS)},
    "n_pairs": {"type": "int", "default": "scheduled 2..4", "valid": "1..4"},
    "palette_size": {"type": "int", "default": "same as n_pairs", "valid": "same as n_pairs"},
    "position_bias": {"type": "str", "default": "scheduled mixed/overlap", "valid": "|".join(POSITION_BIASES)},
    "n_distinct_colors": {"type": "int", "default": "same as n_pairs", "valid": "same as n_pairs"},
    "density": {"type": "str", "default": "wide every fourth profile", "valid": "|".join(DENSITIES)},
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}

_PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (1, 2, 3, 4, 7, 8, 9),
    "cool": (1, 2, 5, 6, 7, 8),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for name, lo, hi in (("grid_h", 8, 14), ("grid_w", 9, 14), ("n_pairs", 1, 4),
                         ("palette_size", 1, 4), ("n_distinct_colors", 1, 4)):
        if name in overrides and (type(overrides[name]) is not int or not lo <= overrides[name] <= hi):
            raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    counts = {overrides[name] for name in ("n_pairs", "palette_size", "n_distinct_colors") if name in overrides}
    if len(counts) > 1:
        raise ValueError("n_pairs, palette_size, and n_distinct_colors must agree")
    if "palette_kind" in overrides and overrides["palette_kind"] not in PALETTE_KINDS:
        raise ValueError(f"palette_kind must be one of {PALETTE_KINDS}")
    if "texture" in overrides and overrides["texture"] not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError("unknown texture")
    if "position_bias" in overrides and overrides["position_bias"] not in POSITION_BIASES:
        raise ValueError(f"position_bias must be one of {POSITION_BIASES}")
    if "density" in overrides and overrides["density"] not in DENSITIES:
        raise ValueError(f"density must be one of {DENSITIES}")
    texture = overrides.get("texture")
    palette = overrides.get("palette_kind")
    if texture in HELPFUL_TEXTURES and palette is not None and texture != palette:
        raise ValueError("helpful texture and palette_kind must agree")


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    values = dict(overrides)
    counts = [values[name] for name in ("n_pairs", "palette_size", "n_distinct_colors") if name in values]
    if counts:
        for name in ("n_pairs", "palette_size", "n_distinct_colors"):
            values[name] = counts[0]
    texture = values.get("texture")
    palette = values.get("palette_kind")
    if texture in HELPFUL_TEXTURES and palette is None:
        values["palette_kind"] = texture
    elif palette is not None and texture is None:
        values["texture"] = palette
    return values


def _scheduled_int(ctx, overrides, name, lo, hi, default):
    if name in overrides:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def _scheduled_choice(ctx, overrides, name, options, default):
    if name in overrides:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _bbox_intersects(a, b) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return max(ar0, br0) <= min(ar1, br1) and max(ac0, bc0) <= min(ac1, bc1)


def _corners(box, positive: bool):
    r0, c0, r1, c1 = box
    return ((r0, c0), (r1, c1)) if positive else ((r0, c1), (r1, c0))


def _add_box(boxes, used_corners, box, positive):
    points = _corners(box, positive)
    if any(point in used_corners for point in points):
        return False
    boxes.append((box, positive))
    used_corners.update(points)
    return True


def _seed_boxes(h: int, w: int, count: int, bias: str, density: str, rng):
    boxes: list[tuple[tuple[int, int, int, int], bool]] = []
    used_corners: set[tuple[int, int]] = set()

    if bias == "separated":
        anchors = [
            (0, 0, min(2, h - 1), min(2, w - 1)),
            (0, max(0, w - 3), min(2, h - 1), w - 1),
            (max(0, h - 3), 0, h - 1, min(2, w - 1)),
            (max(0, h - 3), max(0, w - 3), h - 1, w - 1),
        ]
        for i, box in enumerate(anchors[:count]):
            _add_box(boxes, used_corners, box, i % 2 == 0)
        return boxes

    if density == "wide":
        # At least one axis reaches span 8 whenever the declared grid permits it.
        box = (0, 0, min(h - 1, 8), min(w - 1, 8))
    else:
        box = (1, 1, min(h - 2, 4), min(w - 2, 5))
    _add_box(boxes, used_corners, box, True)

    if count >= 2 and bias == "overlap":
        # Intersects the first bbox but uses four distinct corner cells.
        box2 = (2, 2, h - 1, w - 1)
        if box2[2] - box2[0] < 2 or box2[3] - box2[1] < 2:
            box2 = (1, 2, h - 1, w - 1)
        _add_box(boxes, used_corners, box2, False)

    attempts = 0
    while len(boxes) < count and attempts < 1000:
        attempts += 1
        r0 = rng.randint(0, h - 3)
        c0 = rng.randint(0, w - 3)
        r1 = rng.randint(r0 + 2, h - 1)
        c1 = rng.randint(c0 + 2, w - 1)
        box = (r0, c0, r1, c1)
        if bias == "separated" and any(_bbox_intersects(box, old) for old, _ in boxes):
            continue
        _add_box(boxes, used_corners, box, len(boxes) % 2 == 0)
    if len(boxes) != count:
        raise RuntimeError("could not place requested diagonal pairs")
    return boxes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    normalized = _normalize_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=normalized,
    )

    if normalized.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(ctx.draw_choice("texture", DEGENERATE_TEXTURES), None)

    if difficulty == "easy":
        default_h, default_w, default_n = 8 + sample_index % 3, 9 + sample_index % 3, 2
    elif difficulty == "hard":
        default_h, default_w, default_n = 12 + sample_index % 3, 12 + (sample_index + 1) % 3, 4
    else:
        default_h, default_w, default_n = 8 + sample_index % 7, 9 + (sample_index * 2) % 6, 2 + sample_index % 3
    h = _scheduled_int(ctx, normalized, "grid_h", 8, 14, default_h)
    w = _scheduled_int(ctx, normalized, "grid_w", 9, 14, default_w)
    n = _scheduled_int(ctx, normalized, "n_pairs", 1, 4, default_n)
    ctx.draw_int_strict("palette_size", n, n)
    ctx.draw_int_strict("n_distinct_colors", n, n)

    palette_default = PALETTE_KINDS[sample_index % len(PALETTE_KINDS)]
    palette_kind = _scheduled_choice(ctx, normalized, "palette_kind", PALETTE_KINDS, palette_default)
    ctx.draw_choice("texture", (palette_kind,))
    default_bias = "overlap" if sample_index % 3 == 0 else "mixed"
    bias = _scheduled_choice(ctx, normalized, "position_bias", POSITION_BIASES, default_bias)
    default_density = "wide" if sample_index % 4 == 0 else "sparse"
    density = _scheduled_choice(ctx, normalized, "density", DENSITIES, default_density)

    rng = ctx.draw_rng("layout")
    palette = rng.sample(list(_PALETTES[palette_kind]), n)
    boxes = _seed_boxes(h, w, n, bias, density, rng)
    grid = full_grid(h, w, 0)
    for color, (box, positive) in zip(palette, boxes):
        for r, c in _corners(box, positive):
            grid[r][c] = color
    return grid


def _draw_from_degenerate(name, rng):
    del rng
    grid = full_grid(10, 11, 0)
    if name == "no_pairs":
        grid[2][2] = 4
        grid[5][7] = 6
    elif name == "collinear_pair":
        grid[3][1] = 4
        grid[3][8] = 4
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"]
    messages = []
    if len(grid) > 30 or width > 30:
        messages.append("grid exceeds 30x30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        messages.append("grid contains a non-integer color or color outside 0..9")
        return messages
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append((r, c))
    if not by_color:
        messages.append("no corner-pair colors")
    for color, points in by_color.items():
        if len(points) != 2:
            messages.append(f"color {color} occurs {len(points)} times, expected 2")
            continue
        (r0, c0), (r1, c1) = points
        if r0 == r1 or c0 == c1:
            messages.append(f"color {color} pair is collinear, not diagonal")
    return messages
