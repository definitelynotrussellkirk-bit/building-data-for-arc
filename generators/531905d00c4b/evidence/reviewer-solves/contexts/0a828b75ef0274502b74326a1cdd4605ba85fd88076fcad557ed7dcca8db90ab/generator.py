"""Lawful sampler for "Decode the Index Grid into a Prototype Mosaic".

The first all-zero row separates a color-keyed prototype library from a lower
index matrix.  The canonical rule crops each connected prototype independently,
top-left pads every crop to the largest prototype height/width, crops the lower
nonzero index rectangle, and replaces each index token with its prototype tile.

Version 4 deliberately schedules counterexamples to three shortcuts that fit all
canonical demonstrations: preserving absolute library-row offsets, failing to
crop blank padding around the lower index, and assuming every tile is 3x3.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "531905d00c4b"
TASK_ID = GENERATOR_ID
RULE_HASH = "2ace815dad55"
VERSION = "4.0.0"

SUMMARY = (
    "A first all-zero row separates a left-to-right library of 3-5 distinct-"
    "color connected prototypes from a dense lower color-index matrix. Each "
    "prototype is cropped independently and top-left padded to the common "
    "maximum crop size; the lower nonzero rectangle is cropped; each index "
    "token is then replaced by its matching padded prototype with no gaps. "
    "Scheduled variants include canonical 6/7x11 layouts, vertically shifted "
    "prototypes, blank padding around the index, and non-3x3 tile sizes."
)

INVARIANTS = [
    "the first all-zero row is the unambiguous library/index separator",
    "the library contains 3-5 distinct-color 4-connected prototypes ordered left-to-right",
    "prototype crops have maximum width 2-4 and fit within a 3-5 row library",
    "the cropped lower index is a dense 2-5 by 2-5 matrix using only prototype colors",
    "independent prototype and index cropping, not absolute placement, determines the output",
]

AXES = {
    "library_h": {"type": "int", "default": "scheduled 3..5", "valid": "3..5"},
    "prototype_count": {"type": "int", "default": "scheduled 3..5", "valid": "3..5"},
    "prototype_w": {
        "type": "int",
        "default": "scheduled maximum cropped width 2..4",
        "valid": "2..4",
    },
    "index_h": {"type": "int", "default": "scheduled 2..5", "valid": "2..5"},
    "index_w": {"type": "int", "default": "scheduled 2..5", "valid": "2..5"},
    "index_top_padding": {"type": "int", "default": "scheduled 0..2", "valid": "0..2"},
    "index_left_padding": {"type": "int", "default": "scheduled 0..2", "valid": "0..2"},
    "vertical_layout": {
        "type": "str",
        "default": "scheduled",
        "valid": "top_aligned|bottom_aligned|mixed",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = (
    "canonical_core",
    "shifted_prototype",
    "padded_index",
    "broad_tiles",
)
MIN_STRICT_FRAC = 1.0

_INT_DOMAINS = {
    "library_h": tuple(range(3, 6)),
    "prototype_count": tuple(range(3, 6)),
    "prototype_w": tuple(range(2, 5)),
    "index_h": tuple(range(2, 6)),
    "index_w": tuple(range(2, 6)),
    "index_top_padding": tuple(range(0, 3)),
    "index_left_padding": tuple(range(0, 3)),
}
_LAYOUTS = ("top_aligned", "bottom_aligned", "mixed")


def schedule_profile(seed, sample_index, difficulty=None):
    """Four-cycle schedule; any four consecutive pair slots cover all branches."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, domain in _INT_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if value not in domain:
            raise ValueError(f"{name}={value} outside {domain[0]}..{domain[-1]}")
    if "vertical_layout" in overrides and overrides["vertical_layout"] is not None:
        value = overrides["vertical_layout"]
        if type(value) is not str:
            raise TypeError(f"vertical_layout must be a string, not {type(value).__name__}")
        if value not in _LAYOUTS:
            raise ValueError(f"vertical_layout={value!r} not in {_LAYOUTS}")


def _scheduled_defaults(ctx, profile):
    """Profile defaults; exact overrides always supersede these anchors."""
    band = ctx.difficulty if ctx.difficulty in ("easy", "medium", "hard") else "medium"
    rng = ctx.draw_rng("profile_defaults")
    if profile == "canonical_core":
        return {
            "library_h": 3,
            "prototype_count": 3,
            "prototype_w": 3,
            "index_h": 2 + rng.randrange(2),
            "index_w": 3,
            "index_top_padding": 0,
            "index_left_padding": 0,
            "vertical_layout": "top_aligned",
        }
    if profile == "shifted_prototype":
        return {
            "library_h": 4 if band != "hard" else 5,
            "prototype_count": 3 if band == "easy" else 4,
            "prototype_w": 3,
            "index_h": 3 if band == "easy" else 4,
            "index_w": 4 if band == "hard" else 3,
            "index_top_padding": 0,
            "index_left_padding": 0,
            "vertical_layout": "mixed",
        }
    if profile == "padded_index":
        return {
            "library_h": 3 if band == "easy" else 4,
            "prototype_count": 3 if band != "hard" else 4,
            "prototype_w": 3,
            "index_h": 2 if band == "easy" else 3,
            "index_w": 4 if band == "hard" else 3,
            "index_top_padding": 1 + rng.randrange(2),
            "index_left_padding": 1 + ctx.draw_rng("profile_left_padding").randrange(2),
            "vertical_layout": "top_aligned",
        }
    # broad_tiles: guarantee a non-3x3 common tile while increasing hard scale.
    return {
        "library_h": {"easy": 4, "medium": 4, "hard": 5}[band],
        "prototype_count": {"easy": 4, "medium": 4, "hard": 5}[band],
        "prototype_w": {"easy": 2, "medium": 4, "hard": 4}[band],
        "index_h": {"easy": 3, "medium": 4, "hard": 5}[band],
        "index_w": {"easy": 4, "medium": 4, "hard": 5}[band],
        "index_top_padding": 0,
        "index_left_padding": 1 if band == "medium" else 0,
        "vertical_layout": "bottom_aligned",
    }


def _draw_axis(ctx, name, domain, scheduled_value):
    """Expose the full exact domain while recording the scheduled default honestly."""
    value = ctx.draw_choice(name, domain)
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return value
    # GenCtx has no public scheduled-value setter. `_record` is the same path
    # typed draws use, and keeps the realized value visible to provenance tools.
    return ctx._record(name, scheduled_value, from_override=False)


def _connected_exact_bbox(rng, height, width):
    """Random connected cells whose bounding box is exactly height x width."""
    steps = [(1, 0)] * (height - 1) + [(0, 1)] * (width - 1)
    rng.shuffle(steps)
    r = c = 0
    cells = {(r, c)}
    for dr, dc in steps:
        r += dr
        c += dc
        cells.add((r, c))

    # Grow from the connected set without changing the already exact bbox.
    budget = rng.randint(0, max(1, (height * width) // 2))
    for _ in range(budget):
        frontier = []
        for rr, cc in cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in cells:
                    frontier.append((nr, nc))
        if not frontier:
            break
        cells.add(rng.choice(frontier))

    if rng.randrange(2):
        cells = {(height - 1 - rr, cc) for rr, cc in cells}
    if rng.randrange(2):
        cells = {(rr, width - 1 - cc) for rr, cc in cells}
    return sorted(cells)


def _prototype_geometry(ctx, count, library_h, maximum_w, layout):
    rng = ctx.draw_rng("prototype_geometry")
    heights = [library_h]
    heights.extend(rng.randint(2, library_h) for _ in range(count - 1))
    if count > 1 and library_h > 2:
        heights[-1] = library_h - 1

    widths = [maximum_w]
    widths.extend(rng.randint(1, maximum_w) for _ in range(count - 1))
    if count > 1 and maximum_w > 1:
        widths[-1] = maximum_w - 1

    if layout == "top_aligned":
        offsets = [0] * count
    elif layout == "bottom_aligned":
        offsets = [library_h - h for h in heights]
    else:
        # One full-height anchor keeps every library row nonblank. One shorter
        # top-aligned and one shorter shifted object make this neither top- nor
        # bottom-aligned, producing a guaranteed crop-vs-absolute-row witness.
        heights[0] = library_h
        heights[1] = library_h - 1
        heights[2] = library_h - 1
        offsets = [0, 0, 1]
        for h in heights[3:]:
            offsets.append(rng.randint(0, library_h - h))
    return heights, widths, offsets


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _scheduled_defaults(ctx, profile)

    library_h = _draw_axis(ctx, "library_h", _INT_DOMAINS["library_h"], defaults["library_h"])
    count = _draw_axis(ctx, "prototype_count", _INT_DOMAINS["prototype_count"], defaults["prototype_count"])
    maximum_w = _draw_axis(ctx, "prototype_w", _INT_DOMAINS["prototype_w"], defaults["prototype_w"])
    index_h = _draw_axis(ctx, "index_h", _INT_DOMAINS["index_h"], defaults["index_h"])
    index_w = _draw_axis(ctx, "index_w", _INT_DOMAINS["index_w"], defaults["index_w"])
    top_padding = _draw_axis(
        ctx, "index_top_padding", _INT_DOMAINS["index_top_padding"], defaults["index_top_padding"]
    )
    left_padding = _draw_axis(
        ctx, "index_left_padding", _INT_DOMAINS["index_left_padding"], defaults["index_left_padding"]
    )
    layout = _draw_axis(ctx, "vertical_layout", _LAYOUTS, defaults["vertical_layout"])

    colors = list(ctx.draw_distinct_colors("prototype_colors", n=count, exclude={0}))
    heights, widths, row_offsets = _prototype_geometry(
        ctx, count, library_h, maximum_w, layout
    )
    gap = 1 if profile == "canonical_core" else ctx.draw_rng("library_gap").choice((1, 2))
    library_w = count * maximum_w + (count - 1) * gap
    total_h = library_h + 1 + top_padding + index_h
    total_w = max(library_w, left_padding + index_w)
    if total_h > 30 or total_w > 30:
        raise RuntimeError(f"constructive layout exceeded ARC bounds: {total_h}x{total_w}")
    grid = full_grid(total_h, total_w, 0)

    for i, (color, shape_h, shape_w, row0) in enumerate(
        zip(colors, heights, widths, row_offsets)
    ):
        slot0 = i * (maximum_w + gap)
        col0 = slot0 + ctx.draw_rng(f"prototype_col_offset_{i}").randint(0, maximum_w - shape_w)
        for rr, cc in _connected_exact_bbox(
            ctx.draw_rng(f"prototype_shape_{i}"), shape_h, shape_w
        ):
            grid[row0 + rr][col0 + cc] = color

    # The separator row library_h stays zero. The lower dense token rectangle
    # may have top/left zero padding; the authority crops that padding away.
    area = index_h * index_w
    token_rng = ctx.draw_rng("index_tokens")
    if area >= count:
        tokens = list(colors)
        tokens.extend(token_rng.choice(colors) for _ in range(area - count))
    else:
        tokens = token_rng.sample(colors, area)
    token_rng.shuffle(tokens)
    start_r = library_h + 1 + top_padding
    k = 0
    for r in range(index_h):
        for c in range(index_w):
            grid[start_r + r][left_padding + c] = tokens[k]
            k += 1
    return grid


def _components_4_same_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, tuple(sorted(cells))))
    return components


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _separator(grid):
    for r, row in enumerate(grid):
        if all(value == 0 for value in row):
            return r
    raise ValueError("no all-zero separator row")


def _index_bbox(grid, separator):
    cells = [
        (r, c)
        for r in range(separator + 1, len(grid))
        for c, value in enumerate(grid[r])
        if value != 0
    ]
    if not cells:
        raise ValueError("index area has no nonzero cells")
    return _bbox(cells)


def _parts(grid):
    separator = _separator(grid)
    library = [list(row) for row in grid[:separator]]
    components = sorted(
        _components_4_same_color(library),
        key=lambda item: (_bbox(item[1])[1], _bbox(item[1])[0]),
    )
    crops = []
    for color, cells in components:
        r0, c0, r1, c1 = _bbox(cells)
        crop = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
        for r, c in cells:
            crop[r - r0][c - c0] = color
        crops.append((color, crop))
    tile_h = max(len(crop) for _, crop in crops)
    tile_w = max(len(crop[0]) for _, crop in crops)
    tiles = {}
    for color, crop in crops:
        tile = [[0] * tile_w for _ in range(tile_h)]
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                tile[r][c] = value
        tiles[color] = tile
    r0, c0, r1, c1 = _index_bbox(grid, separator)
    index = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    return {
        "separator": separator,
        "library": library,
        "components": components,
        "tiles": tiles,
        "tile_h": tile_h,
        "tile_w": tile_w,
        "index_bbox": (r0, c0, r1, c1),
        "index": index,
    }


def observe_overrides(grid):
    parts = _parts(grid)
    separator = parts["separator"]
    boxes = [_bbox(cells) for _, cells in parts["components"]]
    tops = [box[0] for box in boxes]
    bottoms = [box[2] for box in boxes]
    if all(top == 0 for top in tops):
        layout = "top_aligned"
    elif all(bottom == separator - 1 for bottom in bottoms):
        layout = "bottom_aligned"
    else:
        layout = "mixed"
    r0, c0, r1, c1 = parts["index_bbox"]
    return {
        "library_h": separator,
        "prototype_count": len(parts["components"]),
        "prototype_w": max(box[3] - box[1] + 1 for box in boxes),
        "index_h": r1 - r0 + 1,
        "index_w": c1 - c0 + 1,
        "index_top_padding": r0 - separator - 1,
        "index_left_padding": c0,
        "vertical_layout": layout,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC bounds ({len(grid)}x{width})"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    errors = []
    try:
        parts = _parts(grid)
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]
    separator = parts["separator"]
    if not 3 <= separator <= 5:
        errors.append(f"library height {separator} outside 3..5")
    if separator >= len(grid) - 1:
        errors.append("separator must have a nonempty lower area")

    components = parts["components"]
    if not 3 <= len(components) <= 5:
        errors.append(f"expected 3-5 prototype objects, found {len(components)}")
    colors = [color for color, _ in components]
    if len(set(colors)) != len(colors):
        errors.append(f"prototype colors are not distinct: {colors}")
    boxes = [_bbox(cells) for _, cells in components]
    for (color, _), (r0, c0, r1, c1) in zip(components, boxes):
        height, box_width = r1 - r0 + 1, c1 - c0 + 1
        if not 1 <= height <= separator:
            errors.append(f"prototype color {color} has invalid crop height {height}")
        if not 1 <= box_width <= 4:
            errors.append(f"prototype color {color} has invalid crop width {box_width}")
    if boxes and not 2 <= max(c1 - c0 + 1 for _, c0, _, c1 in boxes) <= 4:
        errors.append("maximum prototype width must be 2..4")
    for left, right in zip(boxes, boxes[1:]):
        if left[3] + 1 >= right[1]:
            errors.append("prototype bounding boxes need at least one blank separator column")
            break

    r0, c0, r1, c1 = parts["index_bbox"]
    index_h, index_w = r1 - r0 + 1, c1 - c0 + 1
    if not 2 <= index_h <= 5 or not 2 <= index_w <= 5:
        errors.append(f"cropped index shape {index_h}x{index_w} outside 2..5")
    if not 0 <= r0 - separator - 1 <= 2:
        errors.append("index top padding outside 0..2")
    if not 0 <= c0 <= 2:
        errors.append("index left padding outside 0..2")
    index_colors = []
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            value = grid[r][c]
            if value == 0:
                errors.append(f"zero hole inside dense index bbox at ({r},{c})")
                return errors
            index_colors.append(value)
    unknown = sorted(set(index_colors) - set(colors))
    if unknown:
        errors.append(f"index references colors without prototypes: {unknown}")
    if parts["tile_h"] * index_h > 30 or parts["tile_w"] * index_w > 30:
        errors.append("implied output exceeds ARC bounds")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _mosaic(index, tiles, tile_h, tile_w):
    out = [[0] * (len(index[0]) * tile_w) for _ in range(len(index) * tile_h)]
    blank = [[0] * tile_w for _ in range(tile_h)]
    for ir, row in enumerate(index):
        for ic, token in enumerate(row):
            tile = tiles.get(token, blank)
            for r in range(tile_h):
                for c in range(tile_w):
                    value = tile[r][c]
                    if value:
                        out[ir * tile_h + r][ic * tile_w + c] = value
    return out


def _intended_python(grid):
    parts = _parts(grid)
    return _mosaic(parts["index"], parts["tiles"], parts["tile_h"], parts["tile_w"])


def _absolute_row_padding(grid):
    """Rival: retain absolute library rows instead of cropping each object."""
    parts = _parts(grid)
    tile_h = parts["separator"]
    tile_w = parts["tile_w"]
    tiles = {}
    for color, cells in parts["components"]:
        _, c0, _, c1 = _bbox(cells)
        tile = [[0] * tile_w for _ in range(tile_h)]
        for r, c in cells:
            tile[r][c - c0] = color
        tiles[color] = tile
    return _mosaic(parts["index"], tiles, tile_h, tile_w)


def _uncropped_index(grid):
    """Rival: include lower top/left zero padding as blank prototype cells."""
    parts = _parts(grid)
    _, _, r1, c1 = parts["index_bbox"]
    raw = [row[:c1 + 1] for row in grid[parts["separator"] + 1:r1 + 1]]
    return _mosaic(raw, parts["tiles"], parts["tile_h"], parts["tile_w"])


def _fixed_3x3(grid):
    """Rival: force every prototype crop to the canonical 3x3 tile size."""
    parts = _parts(grid)
    tiles = {}
    for color, tile in parts["tiles"].items():
        fixed = [[0] * 3 for _ in range(3)]
        for r in range(min(3, len(tile))):
            for c in range(min(3, len(tile[0]))):
                fixed[r][c] = tile[r][c]
        tiles[color] = fixed
    return _mosaic(parts["index"], tiles, 3, 3)


def _has_vertical_crop_witness(grid):
    return observe_overrides(grid)["vertical_layout"] != "top_aligned"


def _has_index_crop_witness(grid):
    observed = observe_overrides(grid)
    return observed["index_top_padding"] > 0 or observed["index_left_padding"] > 0


def _has_non_3x3_tile(grid):
    parts = _parts(grid)
    return parts["tile_h"] != 3 or parts["tile_w"] != 3


SEMANTIC_WITNESSES = {
    "vertical_object_crop": _has_vertical_crop_witness,
    "lower_index_crop": _has_index_crop_witness,
    "variable_tile_size": _has_non_3x3_tile,
}
SEMANTIC_RIVALS = {
    "absolute_row_padding": _absolute_row_padding,
    "uncropped_index": _uncropped_index,
    "fixed_3x3": _fixed_3x3,
}
WITNESS_RIVALS = {
    "vertical_object_crop": ["absolute_row_padding"],
    "lower_index_crop": ["uncropped_index"],
    "variable_tile_size": ["fixed_3x3"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
