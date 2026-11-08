"""Input generator for canonical task 0ab5dc1f5386.

Intended rule
-------------
Detect monochrome color-8 hollow rectangular frames.  In top-left frame order,
copy the first *unused-by-value* loose nonzero component whose cropped bounding
box exactly equals the frame interior.  Copy only nonzero crop cells and leave
the source component in place.

The default four-example curriculum is deliberately adversarial: it includes a
transposed-size decoy, competing equal-size sources, duplicate equal-valued
sources that teach value-based one-use, and a multicolor source.  Every four
consecutive default examples contain all four profiles, while explicit overrides
expose one additional unmatched-frame mode.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0ab5dc1f5386"
TASK_ID = GENERATOR_ID
RULE_HASH = "1529a4ef373b"
VERSION = "4.1.0"

SUMMARY = (
    "Color-8 rectangular frames receive the first unused loose component whose "
    "cropped bbox exactly matches the frame interior; source components remain. "
    "A four-example schedule teaches orientation-sensitive size matching, "
    "scan-order tie breaking, value-equality one-use, and multicolor preservation."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "every color-8 component is an exact hollow rectangular frame",
    "loose sources are 4-connected nonzero components and retain their bbox zeros",
    "frames process top-left first; sources process row-major first-component order",
    "shape use is by full (height,width,crop) value and source pixels are never cleared",
]

_TEXTURES = (
    "orientation_decoy",
    "scan_order",
    "single_use",
    "multicolor",
    "unmatched",
)
SCHEDULE_PROFILES = _TEXTURES[:4]
HELPFUL_TEXTURES = _TEXTURES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical schedule: 12|13",
        "valid": "12..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical schedule: 16|17|18",
        "valid": "16..22",
    },
    "texture": {
        "type": "str",
        "default": "period-4 semantic schedule",
        "valid": "|".join(_TEXTURES),
        "doc": (
            "orientation_decoy refutes rotate-to-fit; scan_order refutes last-match; "
            "single_use refutes reuse and occurrence-identity tracking; "
            "multicolor refutes mask-only flattening; "
            "unmatched retains a frame with no exact-size source"
        ),
    },
}
# Every cross-product of the finite texture domain and the documented size
# rectangle is constructive, including 12x16.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_CANONICAL_PROFILES = ((12, 16), (13, 17), (13, 18))
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the semantic profile used by the default period-four curriculum."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    value = overrides.get("texture")
    if value is not None and type(value) is not str:
        raise ValueError(f"texture must be a string, not {type(value).__name__}")


def _draw_exact_int(ctx, name, lo, hi, default):
    """Record a keyed default while retaining the entire exact override domain."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _draw_texture(ctx, default):
    if ctx.overrides.get("texture") is not None:
        return ctx.draw_choice("texture", _TEXTURES)
    return ctx.draw_choice("texture", (default,))


def _frame_tile(interior_h, interior_w):
    tile = [[0] * (interior_w + 2) for _ in range(interior_h + 2)]
    for r in range(interior_h + 2):
        for c in range(interior_w + 2):
            if r in (0, interior_h + 1) or c in (0, interior_w + 1):
                tile[r][c] = 8
    return tile


def _manhattan_path(rng, start, goal):
    r, c = start
    gr, gc = goal
    cells = [(r, c)]
    while (r, c) != (gr, gc):
        options = []
        if r != gr:
            options.append((r + (1 if gr > r else -1), c))
        if c != gc:
            options.append((r, c + (1 if gc > c else -1)))
        r, c = rng.choice(options)
        cells.append((r, c))
    return cells


def _shape_tile(rng, height, width, colors, difficulty):
    """Connected bbox-exact crop with varied mask; corners are not privileged."""
    if height < 1 or width < 1:
        raise ValueError("shape dimensions must be positive")
    colors = tuple(colors)
    if not colors:
        raise ValueError("shape must have at least one color")

    center = (rng.randrange(height), rng.randrange(width))
    anchors = {
        (0, rng.randrange(width)),
        (height - 1, rng.randrange(width)),
        (rng.randrange(height), 0),
        (rng.randrange(height), width - 1),
    }
    occupied = {center}
    for anchor in sorted(anchors):
        occupied.update(_manhattan_path(rng, anchor, center))

    base_density = {
        "easy": 0.45,
        "medium": 0.62,
        "hard": 0.78,
    }.get(difficulty, 0.62)
    # Density varies within every band; hard examples are denser on average,
    # not a single saturated mask for each bounding-box size.
    density = min(1.0, max(0.30, base_density + rng.choice((-0.16, -0.08, 0.0, 0.08))))
    target = max(len(colors), len(occupied), round(height * width * density))
    target = min(height * width, target)
    while len(occupied) < target:
        frontier = sorted({
            (r + dr, c + dc)
            for r, c in occupied
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if 0 <= r + dr < height and 0 <= c + dc < width
            and (r + dr, c + dc) not in occupied
        })
        if not frontier:
            break
        occupied.add(rng.choice(frontier))

    cells = sorted(occupied)
    rng.shuffle(cells)
    tile = [[0] * width for _ in range(height)]
    # Guarantee every requested color occurs; remaining cells vary freely.
    for index, (r, c) in enumerate(cells):
        tile[r][c] = colors[index] if index < len(colors) else rng.choice(colors)
    return tile


def _tile(name, cells, *, order_group=None, rank=None):
    return {
        "name": name,
        "cells": cells,
        "order_group": order_group,
        "rank": rank,
    }


def _profile_tiles(texture, rng, colors, difficulty):
    a, b, c = colors
    if texture == "orientation_decoy":
        return [
            _tile("frame_2x3", _frame_tile(2, 3)),
            _tile("frame_2x2", _frame_tile(2, 2)),
            _tile("rotated_3x2", _shape_tile(rng, 3, 2, (a, c), difficulty)),
            _tile("exact_2x2", _shape_tile(rng, 2, 2, (b,), difficulty)),
        ]
    if texture == "scan_order":
        return [
            _tile("frame_2x3", _frame_tile(2, 3)),
            _tile("first_2x3", _shape_tile(rng, 2, 3, (a,), difficulty),
                  order_group="matching", rank=0),
            _tile("last_2x3", _shape_tile(rng, 2, 3, (b,), difficulty),
                  order_group="matching", rank=1),
            _tile("unmatched_2x2", _shape_tile(rng, 2, 2, (c,), difficulty)),
        ]
    if texture == "single_use":
        # Used sources are compared by crop value, not component identity.
        shape = _shape_tile(rng, 2, 2, (a, b, c), difficulty)
        duplicate = [row[:] for row in shape]
        return [
            _tile("first_frame_2x2", _frame_tile(2, 2)),
            _tile("second_frame_2x2", _frame_tile(2, 2)),
            _tile("first_equal_shape_2x2", shape),
            _tile("second_equal_shape_2x2", duplicate),
        ]
    if texture == "multicolor":
        return [
            _tile("frame_3x3", _frame_tile(3, 3)),
            _tile("frame_2x3", _frame_tile(2, 3)),
            _tile("shape_3x3", _shape_tile(rng, 3, 3, (a, b), difficulty)),
            _tile("shape_2x3", _shape_tile(rng, 2, 3, (c,), difficulty)),
        ]
    if texture == "unmatched":
        return [
            _tile("unmatched_frame_3x4", _frame_tile(3, 4)),
            _tile("frame_2x2", _frame_tile(2, 2)),
            _tile("shape_2x2", _shape_tile(rng, 2, 2, (a, b), difficulty)),
            _tile("unmatched_shape_2x3", _shape_tile(rng, 2, 3, (c,), difficulty)),
        ]
    raise ValueError(f"unknown texture {texture!r}")


def _slot_regions(height, width):
    gap_r = (height - 1) // 2
    gap_c = (width - 1) // 2
    return [
        (0, gap_r - 1, 0, gap_c - 1),
        (0, gap_r - 1, gap_c + 1, width - 1),
        (gap_r + 1, height - 1, 0, gap_c - 1),
        (gap_r + 1, height - 1, gap_c + 1, width - 1),
    ]


def _first_nonzero(cells):
    return min((r, c) for r, row in enumerate(cells) for c, value in enumerate(row) if value)


def _place_tiles(height, width, tiles, rng):
    """Place at most one object in each quadrant separated by a zero cross."""
    if len(tiles) > 4:
        raise ValueError("four-slot layout received too many tiles")
    regions = _slot_regions(height, width)
    rng.shuffle(regions)
    placements = []
    for tile, (r1, r2, c1, c2) in zip(tiles, regions):
        cells = tile["cells"]
        th, tw = len(cells), len(cells[0])
        if th > r2 - r1 + 1 or tw > c2 - c1 + 1:
            raise ValueError(
                f"tile {tile['name']} ({th}x{tw}) does not fit slot "
                f"{r2-r1+1}x{c2-c1+1}"
            )
        r0 = rng.randint(r1, r2 - th + 1)
        c0 = rng.randint(c1, c2 - tw + 1)
        placements.append([tile, r0, c0])

    # Assign ranked equal-size shapes to their *actual* row-major component
    # positions, so scan-order lessons survive slot shuffling and jitter.
    groups = {}
    for index, (tile, r0, c0) in enumerate(placements):
        group = tile.get("order_group")
        if group is not None:
            lr, lc = _first_nonzero(tile["cells"])
            groups.setdefault(group, []).append((index, (r0 + lr, c0 + lc)))
    for group, entries in groups.items():
        indices_by_position = [index for index, _ in sorted(entries, key=lambda item: item[1])]
        patterns = sorted((placements[index][0] for index, _ in entries),
                          key=lambda tile: tile["rank"])
        sizes = {(len(tile["cells"]), len(tile["cells"][0])) for tile in patterns}
        if len(sizes) != 1:
            raise ValueError(f"ordered group {group!r} must use equal-size crops")
        for index, pattern in zip(indices_by_position, patterns):
            placements[index][0] = pattern

    grid = full_grid(height, width, 0)
    for tile, r0, c0 in placements:
        for r, row in enumerate(tile["cells"]):
            for c, value in enumerate(row):
                if value:
                    if grid[r0 + r][c0 + c] != 0:
                        raise RuntimeError("slot placement overlap")
                    grid[r0 + r][c0 + c] = value
    return grid


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
    anchor_h, anchor_w = _CANONICAL_PROFILES[(int(sample_index) // 4) % len(_CANONICAL_PROFILES)]
    height = _draw_exact_int(ctx, "grid_h", 12, 18, anchor_h)
    width = _draw_exact_int(ctx, "grid_w", 16, 22, anchor_w)
    texture = _draw_texture(ctx, schedule_profile(seed, sample_index, difficulty))
    colors = ctx.draw_distinct_colors("shape_colors", n=3, exclude=(0, 8))
    tiles = _profile_tiles(texture, ctx.draw_rng("shape_masks"), colors, difficulty)
    grid = _place_tiles(height, width, tiles, ctx.draw_rng("layout"))
    problems = self_check(grid, difficulty=difficulty)
    if problems:
        raise RuntimeError(f"constructive generator violated its contract: {problems}")
    return grid


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _components(grid, *, same_color):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            start = (r, c)
            color = grid[r][c]
            stack = [start]
            seen.add(start)
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < height and 0 <= nc < width) or (nr, nc) in seen:
                        continue
                    value = grid[nr][nc]
                    if value != 0 and (not same_color or value == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((start, cells))
    return result


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _frame_boxes(grid, *, exact_border=False):
    frames = []
    for start, cells in _components(grid, same_color=True):
        if grid[start[0]][start[1]] != 8:
            continue
        r1, c1, r2, c2 = _bbox(cells)
        height, width = r2 - r1 + 1, c2 - c1 + 1
        if height < 2 or width < 2:
            continue
        perimeter = 2 * (height + width) - 4
        if len(cells) != perimeter:
            continue
        if exact_border:
            border = {
                (r, c)
                for r in range(r1, r2 + 1)
                for c in range(c1, c2 + 1)
                if r in (r1, r2) or c in (c1, c2)
            }
            if set(cells) != border:
                continue
        frames.append((r1, c1, r2, c2))
    return sorted(frames)


def _shape_info(grid):
    shapes = []
    for start, cells in _components(grid, same_color=False):
        if grid[start[0]][start[1]] == 8:
            continue
        r1, c1, r2, c2 = _bbox(cells)
        crop = tuple(
            tuple(grid[r][c] for c in range(c1, c2 + 1))
            for r in range(r1, r2 + 1)
        )
        shapes.append((r2 - r1 + 1, c2 - c1 + 1, crop))
    return shapes


def _paint_crop(out, frame, crop):
    r1, c1, _, _ = frame
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value:
                out[r1 + 1 + r][c1 + 1 + c] = value


def _intended(grid):
    """Faithful Python mirror used only for semantic probes, never as authority."""
    out = deepcopy(grid)
    shapes = _shape_info(grid)
    used = []
    for frame in _frame_boxes(grid):
        ih = frame[2] - frame[0] - 1
        iw = frame[3] - frame[1] - 1
        match = next((shape for shape in shapes
                      if shape[0] == ih and shape[1] == iw and shape not in used), None)
        if match is not None:
            used.append(match)
            _paint_crop(out, frame, match[2])
    return out


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
        return ["grid exceeds ARC 30x30 limit"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    problems = []
    frames = _frame_boxes(grid, exact_border=True)
    color8_components = [cells for start, cells in _components(grid, same_color=True)
                         if grid[start[0]][start[1]] == 8]
    if len(frames) != len(color8_components):
        problems.append("every color-8 component must be an exact hollow rectangle")
    if not frames:
        problems.append("expected at least one color-8 destination frame")
    for r1, c1, r2, c2 in frames:
        if r2 - r1 < 2 or c2 - c1 < 2:
            problems.append("frame interior must be at least 1x1")
        if any(grid[r][c] != 0
               for r in range(r1 + 1, r2)
               for c in range(c1 + 1, c2)):
            problems.append("frame interiors must initially be background")
    shapes = _shape_info(grid)
    if not shapes:
        problems.append("expected at least one loose nonzero source component")
    return problems


def strict_canonical_like(grid):
    return self_check(grid)


def _rotate_to_fit(grid):
    out = deepcopy(grid)
    shapes = _shape_info(grid)
    used = []
    for frame in _frame_boxes(grid):
        ih = frame[2] - frame[0] - 1
        iw = frame[3] - frame[1] - 1
        match = next((shape for shape in shapes
                      if shape[0] == ih and shape[1] == iw and shape not in used), None)
        crop = match[2] if match is not None else None
        if match is None:
            match = next((shape for shape in shapes
                          if shape[0] == iw and shape[1] == ih and shape not in used), None)
            if match is not None:
                crop = tuple(tuple(row) for row in zip(*match[2][::-1]))
        if match is not None:
            used.append(match)
            _paint_crop(out, frame, crop)
    return out


def _last_match(grid):
    out = deepcopy(grid)
    shapes = _shape_info(grid)
    used = []
    for frame in _frame_boxes(grid):
        ih = frame[2] - frame[0] - 1
        iw = frame[3] - frame[1] - 1
        candidates = [shape for shape in shapes
                      if shape[0] == ih and shape[1] == iw and shape not in used]
        if candidates:
            match = candidates[-1]
            used.append(match)
            _paint_crop(out, frame, match[2])
    return out


def _flatten_shape(grid):
    out = deepcopy(grid)
    shapes = _shape_info(grid)
    used = []
    for frame in _frame_boxes(grid):
        ih = frame[2] - frame[0] - 1
        iw = frame[3] - frame[1] - 1
        match = next((shape for shape in shapes
                      if shape[0] == ih and shape[1] == iw and shape not in used), None)
        if match is None:
            continue
        used.append(match)
        color = next(value for row in match[2] for value in row if value)
        crop = tuple(tuple(color if value else 0 for value in row) for row in match[2])
        _paint_crop(out, frame, crop)
    return out


def _reuse_shape(grid):
    out = deepcopy(grid)
    shapes = _shape_info(grid)
    for frame in _frame_boxes(grid):
        ih = frame[2] - frame[0] - 1
        iw = frame[3] - frame[1] - 1
        match = next((shape for shape in shapes if shape[0] == ih and shape[1] == iw), None)
        if match is not None:
            _paint_crop(out, frame, match[2])
    return out


def _occurrence_use(grid):
    """Wrong rival: track equal source occurrences separately."""
    out = deepcopy(grid)
    shapes = _shape_info(grid)
    used_indices = set()
    for frame in _frame_boxes(grid):
        ih = frame[2] - frame[0] - 1
        iw = frame[3] - frame[1] - 1
        match_index = next((index for index, shape in enumerate(shapes)
                            if index not in used_indices
                            and shape[0] == ih and shape[1] == iw), None)
        if match_index is not None:
            used_indices.add(match_index)
            _paint_crop(out, frame, shapes[match_index][2])
    return out


def _differs(rival):
    return lambda grid: rival(grid) != _intended(grid)


SEMANTIC_WITNESSES = {
    "orientation_decoy": _differs(_rotate_to_fit),
    "scan_order": _differs(_last_match),
    "single_use": _differs(_reuse_shape),
    "multicolor": _differs(_flatten_shape),
}
SEMANTIC_RIVALS = {
    "rotate_to_fit": _rotate_to_fit,
    "last_match": _last_match,
    "reuse_shape": _reuse_shape,
    "flatten_shape": _flatten_shape,
    "occurrence_use": _occurrence_use,
}
WITNESS_RIVALS = {
    "orientation_decoy": ["rotate_to_fit"],
    "scan_order": ["last_match"],
    "single_use": ["reuse_shape", "occurrence_use"],
    "multicolor": ["flatten_shape"],
}
CANONICAL_SHORTCUTS = {
    "rotate_to_fit": _rotate_to_fit,
    "last_match": _last_match,
    "flatten_shape": _flatten_shape,
    "occurrence_use": _occurrence_use,
}
LESSON_COMPETITORS = {
    "rotate_to_fit": _rotate_to_fit,
    "last_match": _last_match,
    "reuse_shape": _reuse_shape,
    "flatten_shape": _flatten_shape,
    "occurrence_use": _occurrence_use,
}
