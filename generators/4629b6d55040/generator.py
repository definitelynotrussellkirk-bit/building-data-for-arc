"""Generator for task 4629b6d55040 — sort cropped objects by area.

The input contains several isolated, single-colour 4-connected objects on a
zero background.  Each object is cropped to its own bounding box, the crops are
sorted by occupied-cell count from smallest to largest, and the sorted crops
are packed left-to-right with one zero column between them.  Crops are
vertically centred in the output height.
"""
from __future__ import annotations

from collections.abc import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4629b6d55040"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "036057069849"

SUMMARY = (
    "Find every same-colour 4-connected nonzero object, crop each object to "
    "its bounding box, sort the crops by occupied-cell count ascending, and "
    "pack them left-to-right with one zero column between crops while "
    "vertically centring each crop in the tallest crop's height."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and all foreground cells use literal ARC colours 1..9",
    "there are 3..5 isolated same-colour 4-connected objects",
    "each object has a distinct colour and a distinct occupied-cell count",
    "the row-major discovery order is not already ascending by object area",
    "at least one object is non-rectangular and generated crop heights make centring observable",
]

# Keep the externally steerable surface exact and observable.  Grid dimensions,
# shape choices, positions, and colours are deterministic local variation, not
# pseudo-axes that silently ignore caller overrides.
AXES = {
    "n_blobs": {
        "type": "int",
        "default": "3 on canonical-anchor samples; otherwise difficulty-aware 3..5",
        "valid": "3..5",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

Cell = tuple[int, int]
Shape = frozenset[Cell]

# The 5- and 6-cell shapes deliberately share the same 3x3 bounding box.  This
# makes sorting by occupied area distinguishable from sorting by bbox area.
_SHAPES_BY_AREA: dict[int, tuple[Shape, ...]] = {
    5: (
        frozenset({(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}),
        frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}),
    ),
    6: (
        frozenset({(0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2)}),
        frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)}),
    ),
    7: (
        frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)}),
    ),
    8: (
        frozenset({
            (0, 0), (0, 1), (0, 2),
            (1, 0),         (1, 2),
            (2, 0), (2, 1), (2, 2),
        }),
    ),
    9: (
        frozenset({
            (0, 0), (0, 1), (0, 2),
            (1, 0), (1, 1), (1, 2),
            (2, 0), (2, 1), (2, 2),
        }),
    ),
    10: (
        frozenset({
            (0, 0), (0, 1), (0, 2),
            (1, 0),         (1, 2),
            (2, 0),         (2, 2),
            (3, 0), (3, 1), (3, 2),
        }),
    ),
    11: (
        frozenset({
            (0, 0), (0, 1), (0, 2),
            (1, 0), (1, 1), (1, 2),
            (2, 0),         (2, 2),
            (3, 0), (3, 1), (3, 2),
        }),
    ),
    12: (
        # A 5x3 ring has 12 cells.  Its height differs from the mandatory
        # 3x3 five/six-cell pair by two rows, so vertical centring moves those
        # smaller crops down one row instead of remaining top-aligned.
        frozenset({
            (0, 0), (0, 1), (0, 2),
            (1, 0),         (1, 2),
            (2, 0),         (2, 2),
            (3, 0),         (3, 2),
            (4, 0), (4, 1), (4, 2),
        }),
    ),
    13: (
        frozenset({
            (0, 0), (0, 1), (0, 2), (0, 3),
            (1, 0), (1, 1),         (1, 3),
            (2, 0),                 (2, 3),
            (3, 0), (3, 1), (3, 2), (3, 3),
        }),
    ),
    14: (
        frozenset(
            (r, c)
            for r in range(4)
            for c in range(4)
            if (r, c) not in {(1, 1), (2, 2)}
        ),
    ),
    15: (
        frozenset(
            (r, c)
            for r in range(4)
            for c in range(4)
            if (r, c) != (1, 1)
        ),
    ),
}


def _normalise_shape(cells: Iterable[Cell]) -> Shape:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _transform_shape(shape: Shape, transform_index: int) -> Shape:
    """Apply one of the eight dihedral transforms and normalise."""
    cells = set(shape)
    rotations, reflected = divmod(transform_index, 2)
    for _ in range(rotations):
        cells = {(c, -r) for r, c in cells}
    if reflected:
        cells = {(r, -c) for r, c in cells}
    return _normalise_shape(cells)


def _shape_dims(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _objects(grid: list[list[int]]) -> list[dict]:
    """Same-colour 4-connected components in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[Cell] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            components.append({
                "color": color,
                "cells": tuple(cells),
                "size": len(cells),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return components


def _crop(grid: list[list[int]], obj: dict) -> list[list[int]]:
    r1, c1, r2, c2 = obj["bbox"]
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Input-pure Python mirror for tests; the Racket rule is authoritative."""
    components = sorted(_objects(grid), key=lambda obj: obj["size"])
    if not components:
        return [[]]
    crops = [_crop(grid, obj) for obj in components]
    out_h = max(len(crop) for crop in crops)
    out_w = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = full_grid(out_h, out_w, 0)
    left = 0
    for crop in crops:
        top = (out_h - len(crop)) // 2
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0:
                    output[top + r][left + c] = value
        left += len(crop[0]) + 1
    return output


def _analysis(grid) -> dict:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"]}
    height = len(grid)
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["grid contains a non-literal ARC colour"]}
    if not any(value == 0 for row in grid for value in row):
        errors.append("grid must contain zero background")

    components = _objects(grid)
    colors = [obj["color"] for obj in components]
    sizes = [obj["size"] for obj in components]
    bbox_dims = [
        (obj["bbox"][2] - obj["bbox"][0] + 1, obj["bbox"][3] - obj["bbox"][1] + 1)
        for obj in components
    ]
    if not 3 <= len(components) <= 5:
        errors.append(f"expected 3..5 objects, found {len(components)}")
    if len(set(colors)) != len(components):
        errors.append("each object must have a distinct colour")
    if len(set(sizes)) != len(components):
        errors.append("object occupied-cell counts must be strictly distinct")
    if components and min(sizes) < 3:
        errors.append("every object must contain at least three cells")
    if sizes == sorted(sizes):
        errors.append("row-major object order is already area-sorted")
    nonrectangular = [
        size < bbox_h * bbox_w
        for size, (bbox_h, bbox_w) in zip(sizes, bbox_dims)
    ]
    if components and not any(nonrectangular):
        errors.append("at least one object must be non-rectangular")
    if components and len({bbox_h for bbox_h, _ in bbox_dims}) < 2:
        errors.append("object crop heights must differ so vertical centring is visible")

    # Different colours may remain distinct under the oracle even if they touch,
    # but teaching examples keep them spatially isolated to avoid a multicolour
    # grouping shortcut.
    owner = {
        cell: index
        for index, obj in enumerate(components)
        for cell in obj["cells"]
    }
    touching_pairs: set[tuple[int, int]] = set()
    for (r, c), owner_index in owner.items():
        for dr, dc in ((1, 0), (0, 1)):
            other = owner.get((r + dr, c + dc))
            if other is not None and other != owner_index:
                touching_pairs.add(tuple(sorted((owner_index, other))))
    if touching_pairs:
        errors.append("different objects must not touch orthogonally")

    sorted_components = sorted(components, key=lambda obj: obj["size"])
    sorted_colors = [obj["color"] for obj in sorted_components]
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "objects": components,
        "sizes": sizes,
        "bbox_dims": bbox_dims,
        "nonrectangular": nonrectangular,
        "sorted_colors": sorted_colors,
        "palette_size": len(set(value for row in grid for value in row)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful teaching grammar and all canonical inputs."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Require the exact canonical coarse profile plus task-linked grammar."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["height"], analysis["width"]) != (12, 12):
        reasons.append("canonical inputs are exactly 12x12")
    if len(analysis["objects"]) != 3:
        reasons.append("canonical inputs contain exactly three objects")
    if analysis["palette_size"] != 4:
        reasons.append("canonical inputs use background plus three object colours")
    if not 10 <= max(analysis["sizes"]) <= 13:
        reasons.append("canonical largest-object support is 10..13 cells")
    return reasons


MIN_STRICT_FRAC = 0.20


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"n_blobs": len(analysis["objects"])}


def _shape_for_area(area: int, rng, *, force_height: int | None = None) -> Shape:
    shape = rng.choice(_SHAPES_BY_AREA[area])
    transform_indices = list(range(8))
    rng.shuffle(transform_indices)
    for index in transform_indices:
        candidate = _transform_shape(shape, index)
        if force_height is None or _shape_dims(candidate)[0] == force_height:
            return candidate
    raise AssertionError(f"area-{area} template has no height-{force_height} orientation")


def _candidate_positions(shape: Shape, h: int, w: int) -> list[tuple[int, int]]:
    shape_h, shape_w = _shape_dims(shape)
    return [
        (top, left)
        for top in range(h - shape_h + 1)
        for left in range(w - shape_w + 1)
    ]


def _isolated(translated: set[Cell], used: set[Cell]) -> bool:
    if translated & used:
        return False
    for r, c in translated:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (r + dr, c + dc) in used:
                return False
    return True


def _place_scene(
    *, h: int, w: int, shapes: list[Shape], colors: list[int], rng
) -> list[list[int]] | None:
    """Place all shapes, rejecting already-area-sorted row-major scenes."""
    for _ in range(240):
        used: set[Cell] = set()
        placements: dict[int, set[Cell]] = {}
        order = list(range(len(shapes)))
        rng.shuffle(order)
        failed = False
        for shape_index in order:
            shape = shapes[shape_index]
            candidates = _candidate_positions(shape, h, w)
            rng.shuffle(candidates)
            chosen = None
            for top, left in candidates:
                translated = {(top + r, left + c) for r, c in shape}
                if _isolated(translated, used):
                    chosen = translated
                    break
            if chosen is None:
                failed = True
                break
            placements[shape_index] = chosen
            used.update(chosen)
        if failed:
            continue

        grid = full_grid(h, w, 0)
        for shape_index, cells in placements.items():
            for r, c in cells:
                grid[r][c] = colors[shape_index]
        analysis = _analysis(grid)
        if (
            not analysis["errors"]
            and 6 in analysis["sizes"]
            and 5 in analysis["sizes"]
            and analysis["sizes"].index(6) < analysis["sizes"].index(5)
        ):
            # Bbox-area sorting sees the 5- and 6-cell 3x3 crops as tied and
            # therefore preserves this 6-before-5 discovery order.  The true
            # occupied-area rule must reverse them.
            return grid
    return None


def _band(difficulty) -> str:
    return difficulty if difficulty in {"easy", "medium", "hard"} else "medium"


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    requested_n = overrides.get("n_blobs")
    if requested_n is not None:
        requested_n = int(requested_n)
        if not 3 <= requested_n <= 5:
            raise ValueError("n_blobs must be in 3..5")

    # One in four ordinary samples is an exact 12x12 / 3-object canonical
    # anchor.  A caller's lawful n_blobs override always wins and simply opts
    # out of that anchor when it requests 4 or 5 objects.
    canonical_anchor = sample_index % 4 == 0 and requested_n in (None, 3)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    n_blobs = ctx.draw_int(
        "n_blobs",
        3,
        3 if canonical_anchor else 5,
    )
    rng = ctx.draw_rng("scene")

    if canonical_anchor:
        h = w = 12
    else:
        min_side = {3: 12, 4: 14, 5: 16}[n_blobs]
        band_bonus = {"easy": 0, "medium": 1, "hard": 2}[band]
        h = rng.randint(min_side, min(20, min_side + 2 + band_bonus))
        w = rng.randint(min_side, min(20, min_side + 3 + band_bonus))

    # Every scene includes the 5/6 same-bbox pair and a 12-cell height-five
    # object.  Additional areas vary, but remain distinct and larger than six.
    extra_pool = [7, 8, 9, 10, 11, 13, 14, 15]
    extras = rng.sample(extra_pool, n_blobs - 3)
    areas = [5, 6, 12, *extras]
    areas.sort()

    shapes: list[Shape] = []
    for area in areas:
        shapes.append(_shape_for_area(area, rng, force_height=5 if area == 12 else None))

    colors = rng.sample(range(1, 10), n_blobs)
    # Prevent color rank from accidentally matching either ascending or
    # descending area rank in any generated scene.
    if colors == sorted(colors) or colors == sorted(colors, reverse=True):
        colors = colors[1:] + colors[:1]

    grid = _place_scene(h=h, w=w, shapes=shapes, colors=colors, rng=rng)
    if grid is None:
        raise AssertionError(
            f"failed to place {n_blobs} isolated objects in {h}x{w} after 240 attempts"
        )
    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid sort-and-pack scene: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks
# ---------------------------------------------------------------------------


def _valid_analysis(grid) -> dict | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _witness_order_inversion(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["sizes"] != sorted(analysis["sizes"]))


def _witness_same_bbox_different_area(grid) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis:
        return False
    components = analysis["objects"]
    for i, left in enumerate(components):
        lh = left["bbox"][2] - left["bbox"][0] + 1
        lw = left["bbox"][3] - left["bbox"][1] + 1
        for right in components[i + 1:]:
            rh = right["bbox"][2] - right["bbox"][0] + 1
            rw = right["bbox"][3] - right["bbox"][1] + 1
            if (lh, lw) == (rh, rw) and left["size"] != right["size"]:
                return True
    return False


def _witness_nonrectangular_crop(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and any(analysis["nonrectangular"]))


def _witness_vertical_centering(grid) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis:
        return False
    # Unequal heights alone are insufficient: with heights 3 and 4, floor
    # centring leaves the 3-row crop at top=0 and a top-align shortcut gives
    # the same answer.  Require an actual answer difference.
    return _competitor_top_aligned(grid) != rule_mirror(grid)


def _witness_color_order_rebuttal(grid) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis:
        return False
    colors = analysis["sorted_colors"]
    return colors != sorted(colors) and colors != sorted(colors, reverse=True)


def _witness_canonical_anchor(grid) -> bool:
    return strict_canonical_like(grid) == []


SEMANTIC_WITNESSES = {
    "input_order_differs_from_area_order": _witness_order_inversion,
    "same_bbox_different_occupied_area": _witness_same_bbox_different_area,
    "nonrectangular_crop_preserves_zeros": _witness_nonrectangular_crop,
    "unequal_crop_heights_require_vertical_centering": _witness_vertical_centering,
    "color_rank_does_not_encode_area_rank": _witness_color_order_rebuttal,
    "exact_canonical_profile_anchor": _witness_canonical_anchor,
}


def _pack_in_order(grid, components: list[dict], *, center: bool = True) -> list[list[int]]:
    crops = [_crop(grid, obj) for obj in components]
    out_h = max(len(crop) for crop in crops)
    out_w = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = full_grid(out_h, out_w, 0)
    left = 0
    for crop in crops:
        top = (out_h - len(crop)) // 2 if center else 0
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0:
                    output[top + r][left + c] = value
        left += len(crop[0]) + 1
    return output


def _competitor_input_order(grid):
    return _pack_in_order(grid, _objects(grid))


def _competitor_descending_area(grid):
    return _pack_in_order(grid, sorted(_objects(grid), key=lambda obj: -obj["size"]))


def _competitor_bbox_area(grid):
    return _pack_in_order(
        grid,
        sorted(
            _objects(grid),
            key=lambda obj: (
                (obj["bbox"][2] - obj["bbox"][0] + 1)
                * (obj["bbox"][3] - obj["bbox"][1] + 1)
            ),
        ),
    )


def _competitor_color_order(grid):
    return _pack_in_order(grid, sorted(_objects(grid), key=lambda obj: obj["color"]))


def _competitor_top_aligned(grid):
    return _pack_in_order(
        grid,
        sorted(_objects(grid), key=lambda obj: obj["size"]),
        center=False,
    )


_COMPETITORS = {
    "pack objects in input discovery order": _competitor_input_order,
    "sort objects by area descending": _competitor_descending_area,
    "sort by bounding-box area instead of occupied area": _competitor_bbox_area,
    "sort by colour value": _competitor_color_order,
    "top-align crops instead of vertically centring": _competitor_top_aligned,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible shortcut survives all demonstrations."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        errors = self_check(pair.get("input"))
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match the area-sort rule")

    query_input = query.get("input")
    query_errors = self_check(query_input)
    if query_errors:
        reasons.append("query input is outside the teaching grammar")
        return reasons
    query_expected = rule_mirror(query_input)
    if query.get("output") != query_expected:
        reasons.append("query output does not match the area-sort rule")

    for name, competitor in _COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query_input) != query_expected:
                reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
