"""Generator for Area-Sorted Packing (task 95fb3503a9be).

Canonical rule
--------------
Find every monochrome 4-connected nonzero object and crop its bounding box.
Sort the crops by object CELL COUNT descending; equal-area objects are ordered
by color ascending. Pack the crops left-to-right with one zero column between
neighbors, top-aligned on a zero canvas whose height is the tallest crop.

The four-sample schedule deliberately teaches all decisive semantics and the
canonical scene geometry:

* sample 0: the canonical [5, 5, 4] area profile, requiring the color tie-break;
* sample 1: distinct areas with cell-area order disagreeing with bbox-area,
  color-only, ascending-area, and left-to-right rival rules;
* sample 2: a second equal-area tie with different shapes/bbox areas;
* sample 3: a second distinct-area scene for stability and shape variety.

Sample 1 also uses a canonical 1x4 crop and places two objects in overlapping
column ranges.  That prevents a shortcut which segments the input into three
independent vertical bands instead of finding connected components.

Only dimensions are declared as exact override axes.  The semantic schedule is
part of the versioned curriculum rather than a caller-controlled axis.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.selfcheck import components, components_have_clearance

GENERATOR_ID = "95fb3503a9be"
TASK_ID = GENERATOR_ID
RULE_HASH = "6d794ce158dc"
VERSION = "3.1.0"

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

H_LO, H_HI = 9, 11
W_LO, W_HI = 11, 14

SUMMARY = (
    "A 9..11 by 11..14 zero-background grid contains exactly three separated, "
    "distinct-color, monochrome 4-connected objects. Crop each object's bbox, "
    "sort by CELL AREA descending and then COLOR ascending for equal areas, "
    "and pack the true crops left-to-right with one zero separator column. "
    "The versioned four-sample schedule alternates canonical 5/5/4 ties, "
    "distinct-area bbox conflicts, a second tie family, and distinct-area "
    "shape variation so area, tie-break, crop, and packing semantics are visible. "
    "One cell also includes the canonical horizontal 1x4 crop and overlapping "
    "object column ranges, defeating disjoint vertical-band segmentation."
)

INVARIANTS = [
    "background is 0",
    "grid dimensions are within the canonical 9..11 by 11..14 envelope",
    "exactly three monochrome 4-connected nonzero objects",
    "object colors are distinct and objects have a one-cell 8-neighborhood moat",
    "object cell counts are 3..7, not all equal, and at least one crop is non-rectangular",
    "equal-area objects are lawful and are ordered by ascending color",
    "a four-sample lesson includes overlapping object column ranges and a 1x4 crop",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 9..11",
        "valid": "9..11",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 11..14",
        "valid": "11..14",
    },
}

# Every shape is 4-connected and normalized.  The library intentionally pairs
# equal cell counts with different bbox geometries, and includes non-rectangles
# so a learner cannot replace crops by solid blocks.
_SHAPES_BY_SIZE = {
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (3, 0)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ),
}


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(cells, code):
    raw = []
    for r, c in cells:
        if code == 1:
            raw.append((c, -r))
        elif code == 2:
            raw.append((-r, -c))
        elif code == 3:
            raw.append((-c, r))
        elif code == 4:
            raw.append((r, -c))
        elif code == 5:
            raw.append((-r, c))
        elif code == 6:
            raw.append((c, r))
        elif code == 7:
            raw.append((-c, -r))
        else:
            raw.append((r, c))
    return _normalize(raw)


def _dims(cells):
    return 1 + max(r for r, _ in cells), 1 + max(c for _, c in cells)


def _oriented(base, rng, *, max_width=3):
    options = sorted(
        {
            _transform(base, code)
            for code in range(8)
            if _dims(_transform(base, code))[1] <= max_width
        }
    )
    if not options:
        raise ValueError("shape has no orientation fitting the placement slot")
    return rng.choice(options)


def _composition(total, parts, rng):
    """Deterministic random weak composition of total into `parts` parts."""
    if total <= 0:
        return [0] * parts
    cuts = sorted(rng.randint(0, total) for _ in range(parts - 1))
    points = [0, *cuts, total]
    return [points[i + 1] - points[i] for i in range(parts)]


def _object_records(grid):
    records = []
    for comp in components(grid, same_color=True):
        r1, c1, r2, c2 = comp["bbox"]
        crop = [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]
        records.append({
            "color": comp["color"],
            "cells": tuple(comp["cells"]),
            "bbox": comp["bbox"],
            "size": len(comp["cells"]),
            "crop": crop,
            "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
        })
    return records


def _canonical_order(records):
    return sorted(range(len(records)), key=lambda i: (-records[i]["size"], records[i]["color"]))


def _pack(records, order, *, separator=1, solid_bbox=False):
    if not records:
        raise ValueError("cannot pack a grid with no objects")
    crops = []
    for i in order:
        rec = records[i]
        crop = rec["crop"]
        if solid_bbox:
            crop = [
                [rec["color"] for _ in row]
                for row in crop
            ]
        crops.append(crop)
    out_h = max(len(crop) for crop in crops)
    out_w = sum(len(crop[0]) for crop in crops) + separator * (len(crops) - 1)
    out = full_grid(out_h, out_w, 0)
    left = 0
    for crop in crops:
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value:
                    out[r][left + c] = value
        left += len(crop[0]) + separator
    return out


def rule_mirror(grid):
    """Independent Python mirror for tests; Racket remains output authority."""
    records = _object_records(grid)
    return _pack(records, _canonical_order(records))


def observe_overrides(grid):
    """Recover every declared exact axis directly from the returned grid."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural input grammar that accepts all canonical train/test inputs."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]

    errors: list[str] = []
    height = len(grid)
    if not (H_LO <= height <= H_HI):
        errors.append(f"height {height} outside {H_LO}..{H_HI}")
    if not (W_LO <= width <= W_HI):
        errors.append(f"width {width} outside {W_LO}..{W_HI}")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-ARC color")
        return errors

    comps = components(grid, same_color=True)
    if len(comps) != 3:
        errors.append(f"expected exactly 3 monochrome objects; got {len(comps)}")
        return errors

    colors = [comp["color"] for comp in comps]
    if len(set(colors)) != 3:
        errors.append(f"object colors must be distinct; got {colors}")

    sizes = [len(comp["cells"]) for comp in comps]
    if any(size < 3 or size > 7 for size in sizes):
        errors.append(f"object sizes must lie in 3..7; got {sizes}")
    if len(set(sizes)) == 1:
        errors.append(f"all object sizes are equal {sizes}; primary area ordering is hidden")

    if not components_have_clearance(grid, comps, diagonal=True):
        errors.append("objects must have a one-cell 8-neighborhood moat")

    if not any(
        len(comp["cells"])
        < (comp["bbox"][2] - comp["bbox"][0] + 1)
        * (comp["bbox"][3] - comp["bbox"][1] + 1)
        for comp in comps
    ):
        errors.append("at least one object must have a non-rectangular bbox crop")
    return errors


def _scheduled_specs(sample_index, colors, rng):
    """Return [(size, color, cells), ...] for one curriculum schedule cell."""
    mode = sample_index % 4
    ordered_colors = sorted(colors)

    if mode == 0:
        sizes = [5, 5, 4]
        # Assign the smallest color to the smallest object so color-only order
        # starts with area 4, contradicting the canonical area-first rule.
        assigned = [ordered_colors[1], ordered_colors[2], ordered_colors[0]]
        bases = [
            _SHAPES_BY_SIZE[5][0],
            _SHAPES_BY_SIZE[5][1],
            _SHAPES_BY_SIZE[4][1],
        ]
    elif mode == 1:
        sizes = [6, 5, 4]
        # bbox areas are 6, 9, 4, so bbox-area sorting swaps the first two.
        # Colors ascend with size, making color-only order exactly area-ascending.
        assigned = [ordered_colors[2], ordered_colors[1], ordered_colors[0]]
        bases = [
            _SHAPES_BY_SIZE[6][0],
            _SHAPES_BY_SIZE[5][0],
            _SHAPES_BY_SIZE[4][2],
        ]
    elif mode == 2:
        sizes = [6, 4, 4]
        assigned = [ordered_colors[2], ordered_colors[1], ordered_colors[0]]
        bases = [
            _SHAPES_BY_SIZE[6][2],
            _SHAPES_BY_SIZE[4][0],
            _SHAPES_BY_SIZE[4][1],
        ]
    else:
        sizes = [7, 5, 3]
        assigned = [ordered_colors[2], ordered_colors[1], ordered_colors[0]]
        bases = [
            rng.choice(_SHAPES_BY_SIZE[7]),
            rng.choice(_SHAPES_BY_SIZE[5]),
            rng.choice(_SHAPES_BY_SIZE[3]),
        ]

    specs = []
    for index, (size, color, base) in enumerate(zip(sizes, assigned, bases)):
        if mode == 1:
            # Keep this cell's geometry deliberate: a 2x3 rectangle, a 3x3
            # plus, and the canonical horizontal four-cell bar.  The general
            # orientation sampler previously made the declared line shape dead
            # code and capped every generated crop at width three.
            cells = _transform(base, 1) if index == 2 else _normalize(base)
        else:
            cells = _oriented(base, rng, max_width=3)
        specs.append((size, color, cells))
    return specs


def _layout_specs(specs, h, w, sample_index, rng):
    """Return row/column origins for the scheduled objects.

    Most schedule cells retain the useful cyclic horizontal derangement.  The
    second cell deliberately mirrors the canonical two-dimensional geometry:
    the largest object and the 1x4 bar share columns while remaining separated
    by a wide vertical moat.  A connected-component solver handles both; a
    three-independent-column-bands shortcut does not.
    """
    if sample_index % 4 == 1:
        dims = [_dims(cells) for _, _, cells in specs]
        if dims != [(2, 3), (3, 3), (1, 4)]:
            raise ValueError(f"unexpected overlap-layout dimensions: {dims}")
        rows = {
            0: 1,
            1: max(3, h // 2 - 1),
            2: h - 2,
        }
        cols = {
            0: w - 4,
            1: 1,
            2: w - 5,
        }
        return rows, cols

    # Canonical order is semantic; left-to-right input placement is a deliberate
    # cyclic derangement so position/read-order shortcuts fail.
    semantic = sorted(range(3), key=lambda i: (-specs[i][0], specs[i][1]))
    shift = 1 + (sample_index % 2)
    spatial = semantic[shift:] + semantic[:shift]

    widths = [_dims(specs[i][2])[1] for i in spatial]
    free = w - sum(widths) - 2  # two mandatory separator/moat columns
    if free < 0:
        raise ValueError(f"scheduled objects do not fit width {w}: widths={widths}")
    margins = _composition(free, 4, rng)

    cols = {}
    left = margins[0]
    for pos, i in enumerate(spatial):
        cols[i] = left
        left += _dims(specs[i][2])[1]
        if pos < 2:
            left += 1 + margins[pos + 1]
    rows = {
        i: rng.randint(0, h - _dims(specs[i][2])[0])
        for i in range(3)
    }
    return rows, cols


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", H_LO, H_HI)
    w = ctx.draw_int_diff("grid_w", W_LO, W_HI)
    rng = ctx.draw_rng("scene")

    colors = rng.sample(range(1, 10), 3)
    specs = _scheduled_specs(sample_index, colors, rng)
    rows, cols = _layout_specs(specs, h, w, sample_index, rng)

    grid = full_grid(h, w, 0)
    for i, (_, color, cells) in enumerate(specs):
        paint_at(grid, rows[i], cols[i], cells, color)

    problems = self_check(grid)
    if problems:
        raise ValueError("internal generation invariant failed: " + "; ".join(problems))
    return grid


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks
# ---------------------------------------------------------------------------


def strict_canonical_like(grid) -> list[str]:
    """Canonical family: exactly the observed 4/5/5 area multiset."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    sizes = sorted(rec["size"] for rec in _object_records(grid))
    if sizes != [4, 5, 5]:
        reasons.append(f"object-size multiset {sizes} differs from canonical [4, 5, 5]")
    return reasons


def _has_tied_area(grid):
    sizes = [rec["size"] for rec in _object_records(grid)]
    return len(set(sizes)) < len(sizes)


def _has_unequal_area(grid):
    sizes = [rec["size"] for rec in _object_records(grid)]
    return len(set(sizes)) > 1


def _bbox_area_rival_disagrees(grid):
    records = _object_records(grid)
    canonical = _canonical_order(records)
    rival = sorted(
        range(len(records)),
        key=lambda i: (-records[i]["bbox_area"], records[i]["color"]),
    )
    return rival != canonical


def _left_to_right_rival_disagrees(grid):
    records = _object_records(grid)
    canonical = _canonical_order(records)
    rival = sorted(
        range(len(records)),
        key=lambda i: (records[i]["bbox"][1], records[i]["bbox"][0]),
    )
    return rival != canonical


def _has_nonrectangular_crop(grid):
    return any(rec["size"] < rec["bbox_area"] for rec in _object_records(grid))


def _has_overlapping_bbox_columns(grid):
    records = _object_records(grid)
    return any(
        max(records[i]["bbox"][1], records[j]["bbox"][1])
        <= min(records[i]["bbox"][3], records[j]["bbox"][3])
        for i in range(len(records))
        for j in range(i + 1, len(records))
    )


def _has_four_column_crop(grid):
    return any(rec["bbox"][3] - rec["bbox"][1] + 1 >= 4 for rec in _object_records(grid))


def _competitor_color_only(grid):
    records = _object_records(grid)
    return _pack(records, sorted(range(len(records)), key=lambda i: records[i]["color"]))


def _competitor_bbox_area(grid):
    records = _object_records(grid)
    order = sorted(
        range(len(records)),
        key=lambda i: (-records[i]["bbox_area"], records[i]["color"]),
    )
    return _pack(records, order)


def _competitor_left_to_right(grid):
    records = _object_records(grid)
    order = sorted(
        range(len(records)),
        key=lambda i: (records[i]["bbox"][1], records[i]["bbox"][0]),
    )
    return _pack(records, order)


def _competitor_area_ascending(grid):
    records = _object_records(grid)
    order = sorted(range(len(records)), key=lambda i: (records[i]["size"], records[i]["color"]))
    return _pack(records, order)


def _competitor_solid_bboxes(grid):
    records = _object_records(grid)
    return _pack(records, _canonical_order(records), solid_bbox=True)


def _competitor_no_separator(grid):
    records = _object_records(grid)
    return _pack(records, _canonical_order(records), separator=0)


def _competitor_tie_color_descending(grid):
    """Plausible tie bug: sort equal-area objects by color descending."""
    records = _object_records(grid)
    order = sorted(
        range(len(records)),
        key=lambda i: (-records[i]["size"], -records[i]["color"]),
    )
    return _pack(records, order)


def _competitor_crop_width_three(grid):
    """Support shortcut learned from the old corpus: clip every crop to width 3."""
    records = _object_records(grid)
    clipped = []
    for rec in records:
        clone = dict(rec)
        clone["crop"] = [row[:3] for row in rec["crop"]]
        clipped.append(clone)
    return _pack(clipped, _canonical_order(clipped))


def _competitor_column_bands(grid):
    """Plausible shortcut: treat each occupied x-run as one object crop."""
    occupied = [any(row[c] != 0 for row in grid) for c in range(len(grid[0]))]
    runs = []
    start = None
    for c, used in enumerate([*occupied, False]):
        if used and start is None:
            start = c
        elif not used and start is not None:
            runs.append((start, c - 1))
            start = None

    records = []
    for c1, c2 in runs:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c in range(c1, c2 + 1)
            if row[c] != 0
        ]
        if not cells:
            continue
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        values = [grid[r][c] for r, c in cells]
        records.append({
            "color": min(values),
            "cells": tuple(cells),
            "bbox": (r1, c1, r2, c2),
            "size": len(cells),
            "crop": [row[c1:c2 + 1] for row in grid[r1:r2 + 1]],
            "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
        })
    return _pack(records, _canonical_order(records))


SEMANTIC_RIVALS = {
    "color_only": _competitor_color_only,
    "bbox_area": _competitor_bbox_area,
    "left_to_right": _competitor_left_to_right,
    "area_ascending": _competitor_area_ascending,
    "solid_bboxes": _competitor_solid_bboxes,
    "no_separator": _competitor_no_separator,
    "tie_color_descending": _competitor_tie_color_descending,
    "crop_width_three": _competitor_crop_width_three,
    "column_bands": _competitor_column_bands,
}

# The same executable wrong rules are scored both at individual witness sites
# and over complete four-demonstration lessons.
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "equal_area_color_tiebreak": _has_tied_area,
    "unequal_area_primary_order": _has_unequal_area,
    "cell_area_not_bbox_area": _bbox_area_rival_disagrees,
    "semantic_order_not_left_to_right": _left_to_right_rival_disagrees,
    "preserve_nonrectangular_crops": _has_nonrectangular_crop,
    "objects_not_disjoint_vertical_bands": _has_overlapping_bbox_columns,
    "canonical_four_column_crop": _has_four_column_crop,
    "separator_columns_present": lambda grid: (
        _competitor_no_separator(grid) != rule_mirror(grid)
    ),
}

WITNESS_RIVALS = {
    "equal_area_color_tiebreak": ["tie_color_descending"],
    "unequal_area_primary_order": ["area_ascending"],
    "cell_area_not_bbox_area": ["bbox_area"],
    "semantic_order_not_left_to_right": ["left_to_right"],
    "preserve_nonrectangular_crops": ["solid_bboxes"],
    "objects_not_disjoint_vertical_bands": ["column_bands"],
    "canonical_four_column_crop": ["crop_width_three"],
    "separator_columns_present": ["no_separator"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival survives all demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except Exception as exc:
            reasons.append(f"demo {index} input is outside the rule domain: {exc}")
            continue
        if expected != demo.get("output"):
            reasons.append(f"demo {index} output disagrees with the canonical area-sort rule")

    try:
        query_answer = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query input is outside the rule domain: {exc}")
        return reasons
    if query.get("output") is not None and query["output"] != query_answer:
        reasons.append("query output disagrees with the canonical area-sort rule")

    for name, competitor in LESSON_COMPETITORS.items():
        if not all(competitor(demo["input"]) == demo["output"] for demo in demos):
            continue
        rival_answer = competitor(query["input"])
        if rival_answer != query_answer:
            reasons.append(
                f"rival '{name}' fits every demonstration but changes the query answer"
            )
    return reasons
