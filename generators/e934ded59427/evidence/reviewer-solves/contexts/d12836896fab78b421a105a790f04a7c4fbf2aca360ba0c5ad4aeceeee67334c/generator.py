"""Generator for e934ded59427 — draw rectangle borders from color pairs.

For every non-background color, the two input cells are opposite corners of
one axis-aligned rectangle.  The output draws that rectangle's border in the
same color.  Helpful variants change only the palette; negative textures are
kept outside the declared lawful AXES domain and exist solely for mutation
probes of ``self_check``.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e934ded59427"
VERSION = "3.1.0"
TASK_ID = "e934ded59427"
RULE_HASH = "fd190ef6787c"

SUMMARY = (
    "A 0-background grid contains 2-5 distinct colors. Each color occurs "
    "exactly twice at opposite corners of a proper axis-aligned rectangle. "
    "The rectangles occupy disjoint bounding boxes, so their borders have no "
    "undefined color-overwrite intersections. The rule draws every rectangle "
    "border in its marker color. Grid shape, pair count, rectangle dimensions, "
    "diagonal orientation, position, and palette vary."
)

INVARIANTS = [
    "the grid is rectangular, uses ARC colors 0..9, and has background 0",
    "2-5 distinct nonzero colors occur, each at exactly two cells",
    "each same-color pair differs in both row and column",
    "the implied rectangle bounding boxes are pairwise disjoint",
    "exactly one palette anchor identifies the selected helpful texture",
    "each output adds border cells beyond the two input markers",
]

HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("collinear_pair", "no_pairs", "overlapping_rectangles")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Every helpful texture has one mandatory, mutually exclusive anchor.  The
# remaining colors come from a shared pool.  This makes the texture recoverable
# from the returned grid, which lets the override contract verify exact use.
_TEXTURE_ANCHOR = {
    "default": 1,
    "warm": 2,
    "cool": 8,
    "varied": 4,
}
_SHARED_COLORS = (3, 5, 6, 7, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "easy 7..10; medium 9..14; hard 12..20",
        "valid": "6..20",
    },
    "grid_w": {
        "type": "int",
        "default": "easy 9..12; medium 11..16; hard 14..20",
        "valid": "7..20",
    },
    "n_pairs": {
        "type": "int",
        "default": "easy 2; medium 2..3; hard 3..5",
        "valid": "2..5",
    },
    "texture": {
        "type": "str",
        "default": "keyed draw across helpful palette families",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}

_BAND_DEFAULTS = {
    "easy": {"grid_h": (7, 10), "grid_w": (9, 12), "n_pairs": (2, 2)},
    "medium": {"grid_h": (9, 14), "grid_w": (11, 16), "n_pairs": (2, 3)},
    "hard": {"grid_h": (12, 20), "grid_w": (14, 20), "n_pairs": (3, 5)},
}
_VALID_RANGES = {
    "grid_h": (6, 20),
    "grid_w": (7, 20),
    "n_pairs": (2, 5),
}


def _draw_band_int(ctx, name: str, band: str) -> int:
    """Honor explicit global boundaries in every band; skew defaults by band."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        lo, hi = _VALID_RANGES[name]
    else:
        lo, hi = _BAND_DEFAULTS[band][name]
    return ctx.draw_int(name, lo, hi)


def _partition(total: int, parts: int, rng) -> list[tuple[int, int]]:
    """Partition ``range(total)`` into random contiguous spans of size >=2."""
    if parts < 1 or total < 2 * parts:
        raise ValueError(f"cannot partition length {total} into {parts} spans >=2")
    sizes = [2] * parts
    for _ in range(total - 2 * parts):
        sizes[rng.randrange(parts)] += 1
    rng.shuffle(sizes)
    spans = []
    start = 0
    for size in sizes:
        spans.append((start, start + size - 1))
        start += size
    return spans


def _layout_shape(n_pairs: int, h: int, w: int, rng, *, need_hollow: bool) -> tuple[int, int]:
    candidates = {
        2: ((1, 2), (2, 1), (2, 2)),
        3: ((1, 3), (3, 1), (2, 2)),
        4: ((2, 2), (1, 4), (4, 1)),
        5: ((2, 3), (3, 2), (1, 5), (5, 1)),
    }[n_pairs]
    feasible = [
        (nr, nc)
        for nr, nc in candidates
        if nr * nc >= n_pairs
        and h >= 2 * nr
        and w >= 2 * nc
        and (not need_hollow or (h >= 2 * nr + 1 and w >= 2 * nc + 1))
    ]
    if not feasible:
        raise ValueError(
            f"grid {h}x{w} cannot hold {n_pairs} disjoint proper rectangles"
        )
    return rng.choice(feasible)


def _rectangle_in_slot(
    row_span: tuple[int, int],
    col_span: tuple[int, int],
    *,
    mode: int,
    rng,
) -> tuple[int, int, int, int]:
    """Choose a >=2x2 rectangle, deliberately rotating shape grammars."""
    sr0, sr1 = row_span
    sc0, sc1 = col_span
    slot_h = sr1 - sr0 + 1
    slot_w = sc1 - sc0 + 1

    if mode == 0:  # thin horizontal extent: canonical has width-2 examples
        rh = rng.randint(2, slot_h)
        rw = 2
    elif mode == 1:  # thin vertical extent
        rh = 2
        rw = rng.randint(2, slot_w)
    elif mode == 2:  # hollow square witness; separates border from bbox fill
        if min(slot_h, slot_w) < 3:
            raise ValueError("mode 2 requires a slot at least 3x3")
        side = rng.randint(3, min(slot_h, slot_w))
        rh = rw = side
    else:  # broad free rectangle; prefer non-square when the slot permits it
        rh = rng.randint(2, slot_h)
        rw = rng.randint(2, slot_w)
        if rh == rw:
            if rw < slot_w:
                rw += 1
            elif rh < slot_h:
                rh += 1

    r0 = rng.randint(sr0, sr1 - rh + 1)
    c0 = rng.randint(sc0, sc1 - rw + 1)
    return r0, c0, r0 + rh - 1, c0 + rw - 1


def _palette(texture: str, n_pairs: int, rng) -> list[int]:
    anchor = _TEXTURE_ANCHOR[texture]
    colors = [anchor, *rng.sample(list(_SHARED_COLORS), n_pairs - 1)]
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unsupported override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    if band not in _BAND_DEFAULTS:
        raise ValueError(f"difficulty must be easy, medium, hard, or None; got {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    requested_texture = overrides.get("texture")
    if requested_texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(str(requested_texture))

    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    h = _draw_band_int(ctx, "grid_h", band)
    w = _draw_band_int(ctx, "grid_w", band)
    n_pairs = _draw_band_int(ctx, "n_pairs", band)

    rng = ctx.draw_rng("layout")
    modes = [(sample_index + index) % 4 for index in range(n_pairs)]
    # At most one hollow witness is required. Re-map a possible second mode-2
    # occurrence (only n_pairs=5 can have one) to the broad non-square mode so
    # no second spacious slot is required at the smallest legal dimensions.
    seen_hollow = False
    for index, mode in enumerate(modes):
        if mode == 2:
            if seen_hollow:
                modes[index] = 3
            else:
                seen_hollow = True
    need_hollow = seen_hollow
    n_slot_rows, n_slot_cols = _layout_shape(
        n_pairs, h, w, rng, need_hollow=need_hollow
    )
    row_spans = _partition(h, n_slot_rows, rng)
    col_spans = _partition(w, n_slot_cols, rng)
    available_slots = [(rows, cols) for rows in row_spans for cols in col_spans]
    rng.shuffle(available_slots)

    # When this sample carries mode 2, reserve a >=3x3 slot for it. Because
    # every three consecutive sample indices for n_pairs>=2 include mode 2,
    # every three-demo lesson contains a hollow interior and distinguishes
    # rectangle borders from filled bounding boxes.
    slots: list[tuple[tuple[int, int], tuple[int, int]] | None] = [None] * n_pairs
    if need_hollow:
        mode2_index = modes.index(2)
        spacious_index = next(
            index
            for index, (rows, cols) in enumerate(available_slots)
            if rows[1] - rows[0] + 1 >= 3 and cols[1] - cols[0] + 1 >= 3
        )
        slots[mode2_index] = available_slots.pop(spacious_index)
    for index in range(n_pairs):
        if slots[index] is None:
            slots[index] = available_slots.pop()

    colors = _palette(texture, n_pairs, ctx.draw_rng("palette"))
    grid = full_grid(h, w, 0)
    for index, (color, slot) in enumerate(zip(colors, slots)):
        assert slot is not None
        row_span, col_span = slot
        r0, c0, r1, c1 = _rectangle_in_slot(
            row_span,
            col_span,
            mode=modes[index],
            rng=rng,
        )
        if rng.random() < 0.5:
            corners = ((r0, c0), (r1, c1))
        else:
            corners = ((r0, c1), (r1, c0))
        for r, c in corners:
            grid[r][c] = color
    return grid


def _by_color(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    points: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                points[value].append((r, c))
    return dict(points)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _boxes_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def observe_overrides(grid) -> dict[str, int | str]:
    by_color = _by_color(grid)
    anchors = [name for name, color in _TEXTURE_ANCHOR.items() if color in by_color]
    texture = anchors[0] if len(anchors) == 1 else "invalid"
    n_pairs = sum(
        len(cells) == 2
        and cells[0][0] != cells[1][0]
        and cells[0][1] != cells[1][1]
        for cells in by_color.values()
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_pairs": int(n_pairs),
        "texture": texture,
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Testing mirror only; generation remains independent of the oracle."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = full_grid(h, w, 0)
    for color, cells in _by_color(grid).items():
        if len(cells) != 2:
            continue
        r0, c0, r1, c1 = _bbox(cells)
        for c in range(c0, c1 + 1):
            out[r0][c] = color
            out[r1][c] = color
        for r in range(r0, r1 + 1):
            out[r][c0] = color
            out[r][c1] = color
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid is empty or not a list of rows"]
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid is ragged or has zero width"]
    if not (6 <= h <= 20 and 7 <= w <= 20):
        errors.append(f"grid dimensions {h}x{w} outside lawful 6..20 by 7..20")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell {(r, c)} is not an ARC color: {value!r}")

    by_color = _by_color(grid)
    if not 2 <= len(by_color) <= 5:
        errors.append(f"expected 2-5 marker colors, found {len(by_color)}")

    anchors = [color for color in _TEXTURE_ANCHOR.values() if color in by_color]
    if len(anchors) != 1:
        errors.append(f"expected exactly one palette anchor, found {anchors}")

    boxes: list[tuple[int, int, int, int, int]] = []
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            errors.append(f"color {color} has {len(cells)} cells, expected exactly 2")
            continue
        (ra, ca), (rb, cb) = cells
        if ra == rb or ca == cb:
            errors.append(f"color {color} pair is collinear: {cells}")
            continue
        r0, c0, r1, c1 = _bbox(cells)
        box = (r0, c0, r1, c1)
        for or0, oc0, or1, oc1, other_color in boxes:
            if _boxes_overlap(box, (or0, oc0, or1, oc1)):
                errors.append(
                    f"rectangle bboxes for colors {other_color} and {color} overlap"
                )
        boxes.append((r0, c0, r1, c1, color))

    if not errors:
        output = rule_mirror(grid)
        added = sum(
            output[r][c] != 0 and grid[r][c] == 0
            for r in range(h)
            for c in range(w)
        )
        if added < 2 * len(by_color):
            errors.append(
                f"rectangle completion added only {added} cells for {len(by_color)} pairs"
            )
    return errors


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(8, 10, 0)
    if name == "collinear_pair":
        grid[2][1] = 1
        grid[2][6] = 1
        grid[5][2] = 5
        grid[5][8] = 5
    elif name == "no_pairs":
        grid[1][1] = 1
        grid[5][6] = 5
    elif name == "overlapping_rectangles":
        grid[1][1] = 1
        grid[6][8] = 1
        grid[1][8] = 5
        grid[6][1] = 5
    else:
        raise ValueError(f"unknown texture {name!r}")
    return grid
