"""Generator for ARC task 5adee1b2 — palette-keyed exterior framing.

A two-column palette sits somewhere on the left edge.  Each palette entry is a
2x2 swatch whose left color names one or more icons and whose right color is
the frame color for those icons.  The output preserves the palette and icons,
then paints only the exterior zero region of each icon's one-cell-expanded
bounding box.  Enclosed holes remain zero and edge-touching frames are clipped.

The generated distribution is anchored to the official 20x20 and 26x26
profiles and deliberately exercises multiple icons, concavities, enclosed
holes, top/bottom palettes, rectangular canvases, and clipped edge cases.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "e79b2a917a36"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ef84d572bc85"

SUMMARY = (
    "A left-edge palette contains 1-4 two-row source/frame color pairs. "
    "Every connected icon in a source color, excluding the palette swatch, "
    "gets its exterior zero region framed inside the icon bounding box "
    "expanded by one cell. Enclosed holes stay zero and frames clip at grid "
    "edges. Official-scale 20x20 and 26x26 scenes occur normally."
)

INVARIANTS = [
    "background is color 0 and all colors are integers 0..9",
    "1-4 distinct two-row source/frame palette pairs occupy columns 0-1",
    "every source color has 1-3 connected icons outside the palette columns",
    "frame colors occur only in their palette swatches in the input",
    "every icon has exterior zero support, so the framing operation is visible",
    "generated scenes expose compact, concave, hollow, and clipped branches",
]

_GRID_SIZES = (20, 26)
_PALETTE_POSITIONS = ("top", "bottom")
_SHAPE_FAMILIES = ("compact", "concave", "hollow")
_EDGE_MODES = ("interior", "clipped")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "20 on easy; 20|26 on medium; 26 on hard",
        "valid": "20|26",
    },
    "grid_w": {
        "type": "int",
        "default": "20 on easy; 20|26 on medium; 26 on hard",
        "valid": "20|26",
    },
    "entry_count": {
        "type": "int",
        "default": "difficulty-weighted 1..4",
        "valid": "1..4",
    },
    "max_icons_per": {
        "type": "int",
        "default": "difficulty-weighted 1..3",
        "valid": "1..3",
    },
    "palette_position": {
        "type": "str",
        "default": "sample-index schedule top|bottom",
        "valid": "top|bottom",
    },
    "shape_family": {
        "type": "str",
        "default": "sample-index schedule compact|concave|hollow",
        "valid": "compact|concave|hollow",
    },
    "edge_mode": {
        "type": "str",
        "default": "sample-index schedule interior|clipped",
        "valid": "interior|clipped",
    },
}


def _draw_choice(ctx, label, full_options, default_options):
    options = full_options if ctx.overrides.get(label) is not None else default_options
    return ctx.draw_choice(label, options)


def _band_defaults(difficulty, sample_index):
    slot = int(sample_index) % 6
    if difficulty == "easy":
        return {
            "grid_h": (20,),
            "grid_w": (20,),
            "entry_count": (1, 2, 2),
            "max_icons_per": (1, 2),
        }
    if difficulty == "hard":
        return {
            "grid_h": (26,),
            "grid_w": (26,),
            "entry_count": (2, 3, 4),
            "max_icons_per": (2, 3),
        }
    return {
        "grid_h": _GRID_SIZES,
        "grid_w": _GRID_SIZES,
        "entry_count": (1, 2, 2, 3, 4),
        "max_icons_per": (1, 2, 3),
        "slot": slot,
    }


def _palette_rows(height, count, position):
    if position == "top":
        return [3 * index for index in range(count)]
    start = height - (3 * count - 1)
    return [start + 3 * index for index in range(count)]


def _compact_shape(rng, dense):
    if dense:
        return [(0, 0)]
    return rng.choice(
        [
            [(0, 0)],
            [(0, 0), (0, 1)],
            [(0, 0), (1, 0)],
            [(0, 0), (0, 1), (1, 0), (1, 1)],
        ]
    )


def _anchor_shape(family, rng):
    if family == "compact":
        return rng.choice(
            [
                [(0, 0), (0, 1), (1, 0), (1, 1)],
                [(0, 0), (0, 1), (0, 2)],
                [(0, 0), (1, 0), (2, 0)],
            ]
        )
    if family == "concave":
        return rng.choice(
            [
                [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
                [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
                [(0, 0), (0, 1), (1, 0)],
            ]
        )
    # A 5x5 ring is deliberately larger than the ordinary distractor icons.
    # Its 3x3 interior proves that the oracle frames exterior background only.
    return [
        (r, c)
        for r in range(5)
        for c in range(5)
        if r in (0, 4) or c in (0, 4)
    ]


def _normalize_shape(shape):
    r0 = min(r for r, _ in shape)
    c0 = min(c for _, c in shape)
    return [(r - r0, c - c0) for r, c in shape]


def _rects_conflict(a, b):
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return not (ar2 < br1 or br2 < ar1 or ac2 < bc1 or bc2 < ac1)


def _place_shape(
    grid,
    rng,
    shape,
    color,
    clearance_boxes,
    palette_cells,
    *,
    edge_mode="interior",
):
    shape = _normalize_shape(shape)
    height, width = len(grid), len(grid[0])
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    positions = [
        (r0, c0)
        for r0 in range(0, height - shape_h + 1)
        for c0 in range(3, width - shape_w + 1)
    ]
    rng.shuffle(positions)
    for r0, c0 in positions:
        touches_edge = (
            r0 == 0
            or r0 + shape_h == height
            or c0 + shape_w == width
        )
        if edge_mode == "clipped" and not touches_edge:
            continue
        if edge_mode == "interior" and touches_edge:
            continue
        cells = {(r0 + r, c0 + c) for r, c in shape}
        r1, c1 = min(r for r, _ in cells), min(c for _, c in cells)
        r2, c2 = max(r for r, _ in cells), max(c for _, c in cells)
        frame_box = (
            max(0, r1 - 1),
            max(0, c1 - 1),
            min(height - 1, r2 + 1),
            min(width - 1, c2 + 1),
        )
        if any(
            frame_box[0] <= r <= frame_box[2]
            and frame_box[1] <= c <= frame_box[3]
            for r, c in palette_cells
        ):
            continue
        clearance = (
            max(0, r1 - 2),
            max(0, c1 - 2),
            min(height - 1, r2 + 2),
            min(width - 1, c2 + 2),
        )
        if any(_rects_conflict(clearance, prior) for prior in clearance_boxes):
            continue
        if any(grid[r][c] != 0 for r, c in cells):
            continue
        for r, c in cells:
            grid[r][c] = color
        clearance_boxes.append(clearance)
        return True
    return False


def _build_scene(
    height,
    width,
    entries,
    icon_counts,
    palette_position,
    shape_family,
    edge_mode,
    rng,
):
    grid = full_grid(height, width, 0)
    rows = _palette_rows(height, len(entries), palette_position)
    palette_cells = set()
    for row, (source, frame) in zip(rows, entries):
        for rr in (row, row + 1):
            grid[rr][0] = source
            grid[rr][1] = frame
            palette_cells.add((rr, 0))
            palette_cells.add((rr, 1))

    anchor_source = rng.randrange(len(entries))
    dense = sum(icon_counts) >= 7
    clearance_boxes = []
    for entry_index, ((source, _frame), count) in enumerate(zip(entries, icon_counts)):
        for icon_index in range(count):
            is_anchor = entry_index == anchor_source and icon_index == 0
            shape = (
                _anchor_shape(shape_family, rng)
                if is_anchor
                else _compact_shape(rng, dense)
            )
            requested_edge = edge_mode if is_anchor else "interior"
            if not _place_shape(
                grid,
                rng,
                shape,
                source,
                clearance_boxes,
                palette_cells,
                edge_mode=requested_edge,
            ):
                return None
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, structurally valid lesson input."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None/easy/medium/hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _band_defaults(difficulty, sample_index)
    height = _draw_choice(ctx, "grid_h", _GRID_SIZES, defaults["grid_h"])
    width = _draw_choice(ctx, "grid_w", _GRID_SIZES, defaults["grid_w"])
    entry_count = _draw_choice(
        ctx, "entry_count", (1, 2, 3, 4), defaults["entry_count"]
    )
    max_icons = _draw_choice(
        ctx, "max_icons_per", (1, 2, 3), defaults["max_icons_per"]
    )

    slot = int(sample_index) % 6
    palette_position = _draw_choice(
        ctx,
        "palette_position",
        _PALETTE_POSITIONS,
        (_PALETTE_POSITIONS[slot % 2],),
    )
    shape_family = _draw_choice(
        ctx,
        "shape_family",
        _SHAPE_FAMILIES,
        (_SHAPE_FAMILIES[slot % len(_SHAPE_FAMILIES)],),
    )
    edge_mode = _draw_choice(
        ctx,
        "edge_mode",
        _EDGE_MODES,
        (_EDGE_MODES[(slot // 3) % 2],),
    )

    color_rng = ctx.draw_rng("colors")
    colors = color_rng.sample(tuple(range(1, 10)), 2 * entry_count)
    entries = [
        (colors[2 * index], colors[2 * index + 1])
        for index in range(entry_count)
    ]
    icon_counts = [1] * entry_count
    anchor_count_index = (int(seed) + int(sample_index)) % entry_count
    icon_counts[anchor_count_index] = max_icons
    if difficulty == "hard" and entry_count > 1 and max_icons > 1:
        icon_counts[(anchor_count_index + 1) % entry_count] = max_icons

    layout_rng = ctx.draw_rng("layout")
    for _attempt in range(80):
        grid = _build_scene(
            height,
            width,
            entries,
            icon_counts,
            palette_position,
            shape_family,
            edge_mode,
            layout_rng,
        )
        if grid is None:
            continue
        observed = observe_overrides(grid)
        requested = {
            "grid_h": height,
            "grid_w": width,
            "entry_count": entry_count,
            "max_icons_per": max_icons,
            "palette_position": palette_position,
            "shape_family": shape_family,
            "edge_mode": edge_mode,
        }
        if observed != requested:
            raise AssertionError(
                f"internal axis drift: requested={requested}, observed={observed}"
            )
        errors = self_check(grid, difficulty=difficulty)
        if errors:
            raise AssertionError("internal invalid scene: " + "; ".join(errors))
        return grid
    raise RuntimeError("unable to place a valid icon family after 80 attempts")


def _grid_shape_error(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return "grid must be a non-empty list of rows"
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return "grid must be rectangular and non-empty"
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "grid colors must be integers in 0..9"
    return None


def _palette_entries(grid):
    entries = []
    for row in range(len(grid) - 1):
        source = grid[row][0]
        frame = grid[row][1]
        if (
            source != 0
            and frame != 0
            and source != frame
            and grid[row + 1][0] == source
            and grid[row + 1][1] == frame
        ):
            entries.append((row, source, frame))
    return entries


def _icon_components(grid, entries):
    by_source = {}
    for row, source, _frame in entries:
        palette_cells = {(row, 0), (row + 1, 0)}
        source_components = components(grid, colors={source})
        icons = [
            component
            for component in source_components
            if set(component["cells"]) != palette_cells
        ]
        by_source[source] = icons
    return by_source


def _enclosed_zero_count(grid, component):
    r1, c1, r2, c2 = component["bbox"]
    zeros = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if grid[r][c] == 0
    }
    seen = set()
    enclosed = 0
    for start in zeros:
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        region = []
        reaches_boundary = False
        while queue:
            row, col = queue.popleft()
            region.append((row, col))
            if row in (r1, r2) or col in (c1, c2):
                reaches_boundary = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (row + dr, col + dc)
                if nxt in zeros and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        if not reaches_boundary:
            enclosed += len(region)
    return enclosed


def _classify_shape_family(grid, icons):
    if any(_enclosed_zero_count(grid, component) > 0 for component in icons):
        return "hollow"
    for component in icons:
        r1, c1, r2, c2 = component["bbox"]
        if len(component["cells"]) < (r2 - r1 + 1) * (c2 - c1 + 1):
            return "concave"
    return "compact"


def _expanded_exterior(grid, component):
    height, width = len(grid), len(grid[0])
    r1, c1, r2, c2 = component["bbox"]
    er1, ec1 = max(0, r1 - 1), max(0, c1 - 1)
    er2, ec2 = min(height - 1, r2 + 1), min(width - 1, c2 + 1)
    allowed = {
        (r, c)
        for r in range(er1, er2 + 1)
        for c in range(ec1, ec2 + 1)
        if grid[r][c] == 0
    }
    starts = {
        (r, c)
        for r, c in allowed
        if r in (er1, er2) or c in (ec1, ec2)
    }
    exterior = set(starts)
    queue = deque(starts)
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (row + dr, col + dc)
            if nxt in allowed and nxt not in exterior:
                exterior.add(nxt)
                queue.append(nxt)
    return exterior


def _analysis(grid):
    result = {"errors": []}
    shape_error = _grid_shape_error(grid)
    if shape_error:
        result["errors"].append(shape_error)
        return result

    height, width = len(grid), len(grid[0])
    if width < 4:
        result["errors"].append("grid must leave icon space to the right of the palette")
        return result
    entries = _palette_entries(grid)
    result["entries"] = entries
    if not (1 <= len(entries) <= 4):
        result["errors"].append(f"expected 1-4 palette entries, got {len(entries)}")
        return result

    starts = [row for row, _source, _frame in entries]
    if any(b - a < 3 for a, b in zip(starts, starts[1:])):
        result["errors"].append("palette entries must be separated into distinct two-row swatches")
    palette_colors = [color for _row, source, frame in entries for color in (source, frame)]
    if len(set(palette_colors)) != len(palette_colors):
        result["errors"].append("palette source/frame colors must be globally distinct")

    allowed_colors = {0, *palette_colors}
    extra_colors = sorted({value for row in grid for value in row} - allowed_colors)
    if extra_colors:
        result["errors"].append(f"input contains colors absent from the palette: {extra_colors}")

    by_source = _icon_components(grid, entries)
    all_icons = []
    for row, source, frame in entries:
        frame_cells = {
            (r, c)
            for r, grid_row in enumerate(grid)
            for c, value in enumerate(grid_row)
            if value == frame
        }
        expected_frame_cells = {(row, 1), (row + 1, 1)}
        if frame_cells != expected_frame_cells:
            result["errors"].append(
                f"frame color {frame} must occur only in its two palette cells"
            )

        source_components = components(grid, colors={source})
        expected_source_cells = {(row, 0), (row + 1, 0)}
        palette_matches = [
            component
            for component in source_components
            if set(component["cells"]) == expected_source_cells
        ]
        if len(palette_matches) != 1:
            result["errors"].append(
                f"source color {source} lacks one exact two-cell palette swatch"
            )
        icons = by_source.get(source, [])
        if not (1 <= len(icons) <= 3):
            result["errors"].append(
                f"source color {source} has {len(icons)} icons (expected 1-3)"
            )
        for component in icons:
            if any(col <= 1 for _row, col in component["cells"]):
                result["errors"].append(
                    f"source color {source} icon intrudes into palette columns"
                )
            exterior = _expanded_exterior(grid, component)
            if not exterior:
                result["errors"].append(
                    f"source color {source} icon has no exterior zero region to frame"
                )
        all_icons.extend(icons)

    result["icons"] = all_icons
    if not all_icons:
        result["errors"].append("scene contains no icons")
        return result

    output = rule_mirror(grid, _analysis_result=result)
    if output == grid:
        result["errors"].append("framing rule is an identity on this input")
    result["output"] = output
    result["shape_family"] = _classify_shape_family(grid, all_icons)
    result["edge_mode"] = (
        "clipped"
        if any(
            r1 == 0 or r2 == height - 1 or c2 == width - 1
            for r1, _c1, r2, c2 in (component["bbox"] for component in all_icons)
        )
        else "interior"
    )
    top_rows = _palette_rows(height, len(entries), "top")
    bottom_rows = _palette_rows(height, len(entries), "bottom")
    if starts == top_rows:
        result["palette_position"] = "top"
    elif starts == bottom_rows:
        result["palette_position"] = "bottom"
    else:
        # Canonical swatches need not use the generator's exact spacing, but
        # generated rows do.  This fallback keeps structural inspection useful
        # for accepted external examples without weakening override round-trips.
        result["palette_position"] = (
            "top" if sum(starts) < sum(height - 1 - r for r in starts) else "bottom"
        )
    result["max_icons_per"] = max(len(by_source[source]) for _row, source, _frame in entries)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding lesson inputs."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    """Recover every declared exact axis from a valid returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "entry_count": len(analysis["entries"]),
        "max_icons_per": analysis["max_icons_per"],
        "palette_position": analysis["palette_position"],
        "shape_family": analysis["shape_family"],
        "edge_mode": analysis["edge_mode"],
    }


def rule_mirror(grid, _analysis_result=None):
    """Test-only mirror of the canonical Racket rule.

    Racket remains the output authority.  This mirror exists for structural
    checks, regression fixtures, and count-backed semantic censuses.
    """
    entries = (
        _analysis_result.get("entries")
        if _analysis_result is not None
        else _palette_entries(grid)
    )
    by_source = _icon_components(grid, entries)
    output = [row[:] for row in grid]
    for _row, source, frame in entries:
        for component in by_source.get(source, []):
            for r, c in _expanded_exterior(grid, component):
                if output[r][c] == 0:
                    output[r][c] = frame
    return output
