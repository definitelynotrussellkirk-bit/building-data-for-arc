"""Generator for hard_p07 — dock color-matched objects at crosshair targets.

Each nonzero object color appears once as a marker in the top row and once as
an independently placed marker in the left column.  Their intersection is the
object's target center.  The output removes the markers and moves the object's
unchanged bounding-box crop so that it is centered on that color-matched
crosshair.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c94f3e28d713"
TASK_ID = "c94f3e28d713"
VERSION = "2.0.0"
RULE_HASH = "5cb8d4760722"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "A zero-background grid contains 2-3 distinctly colored connected objects. "
    "Each object color also appears exactly once in the top row and once in "
    "the left column. Move each object's unchanged crop so its bounding box is "
    "centered at the intersection of the matching color's row and column "
    "markers; erase the markers and original locations."
)

INVARIANTS = [
    "background is 0 and the top-left corner is 0",
    "2-3 colors each have one top marker, one left marker, and one interior object",
    "top and left marker orders are either equal or reversed",
    "each target crop fits in-bounds and target bounding boxes do not overlap",
    "object shape and color are preserved exactly while marker cells disappear",
    "every four consecutive default samples include aligned and crossed marker orders, a three-object scene, and a partially pre-docked scene",
]

PAIRINGS = ("same", "reverse")
DOCKING_STATES = ("all_move", "one_docked")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot schedule anchored at 10/11, otherwise difficulty-skewed",
        "valid": "9..14",
        "doc": "Returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot schedule anchored at 10/11, otherwise difficulty-skewed",
        "valid": "9..14",
        "doc": "Returned grid width.",
    },
    "n_objs": {
        "type": "int",
        "default": "four-slot schedule covering two and three objects",
        "valid": "2..3",
        "doc": "Number of marker colors and interior objects.",
    },
    "marker_pairing": {
        "type": "str",
        "default": "sample_index alternates same and reverse marker orders",
        "valid": "same|reverse",
        "doc": "Whether top-row and left-column color orders agree or reverse.",
    },
    "shape_cells": {
        "type": "int",
        "default": "2/3 on canonical slots, then difficulty-skewed 3..5",
        "valid": "2..5",
        "doc": "Exact nonzero cell count of every interior object.",
    },
    "docking_state": {
        "type": "str",
        "default": "three all-move slots and one one-docked slot per lesson",
        "valid": "all_move|one_docked",
        "doc": "Whether zero or exactly one source object is already at its target.",
    },
}

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# Every shape has at most a 3x2 or 2x3 bounding box.  That keeps the complete
# 9x9 / three-object override boundary constructible without target overlap.
_BASE_SHAPES = {
    2: (
        {(0, 0), (0, 1)},
    ),
    3: (
        {(0, 0), (1, 0), (1, 1)},
        {(0, 0), (0, 1), (0, 2)},
    ),
    4: (
        {(0, 0), (1, 0), (1, 1), (1, 2)},
        {(0, 0), (0, 1), (1, 1), (1, 2)},
        {(0, 0), (0, 1), (0, 2), (1, 1)},
    ),
    5: (
        {(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)},
        {(0, 0), (0, 1), (0, 2), (1, 1), (1, 2)},
        {(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)},
    ),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _transform(cells: Iterable[tuple[int, int]], code: int) -> frozenset[tuple[int, int]]:
    pts = set(cells)
    if code >= 4:
        pts = {(r, -c) for r, c in pts}
    for _ in range(code % 4):
        pts = {(c, -r) for r, c in pts}
    return _normalize(pts)


def _variants(size: int, *, canonical_like: bool = False) -> tuple[frozenset[tuple[int, int]], ...]:
    bases = _BASE_SHAPES[size]
    if canonical_like and size == 3:
        bases = bases[:1]  # official triominoes are 2x2 L shapes
    out = {_transform(shape, code) for shape in bases for code in range(8)}
    return tuple(sorted(out, key=lambda s: sorted(s)))


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _components_for_color(
    grid: list[list[int]], color: int, *, interior_only: bool = True
) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    allowed = {
        (r, c)
        for r in range(1 if interior_only else 0, h)
        for c in range(1 if interior_only else 0, w)
        if grid[r][c] == color
    }
    seen: set[tuple[int, int]] = set()
    comps: list[set[tuple[int, int]]] = []
    for start in sorted(allowed):
        if start in seen:
            continue
        todo = [start]
        seen.add(start)
        comp: set[tuple[int, int]] = set()
        while todo:
            cell = todo.pop()
            comp.add(cell)
            r, c = cell
            for dr, dc in _DIR4:
                nxt = (r + dr, c + dc)
                if nxt in allowed and nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        comps.append(comp)
    return comps


def _analysis(grid) -> dict:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be non-empty"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty"]}
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["cells must be integer ARC colors 0..9"]}

    h = len(grid)
    if not (9 <= h <= 14 and 9 <= w <= 14):
        errors.append("grid dimensions must both be in 9..14")
    if grid[0][0] != 0:
        errors.append("top-left corner must be background 0")

    top = [(c, grid[0][c]) for c in range(1, w) if grid[0][c] != 0]
    left = [(r, grid[r][0]) for r in range(1, h) if grid[r][0] != 0]
    top_colors = [color for _, color in top]
    left_colors = [color for _, color in left]
    if not 2 <= len(top) <= 3:
        errors.append("top row must contain two or three markers")
    if len(left) != len(top):
        errors.append("left marker count must equal top marker count")
    if len(top_colors) != len(set(top_colors)):
        errors.append("top marker colors must be distinct")
    if len(left_colors) != len(set(left_colors)):
        errors.append("left marker colors must be distinct")
    if set(top_colors) != set(left_colors):
        errors.append("top and left marker color sets must agree")

    pairing = None
    if top_colors and left_colors:
        if top_colors == left_colors:
            pairing = "same"
        elif top_colors == list(reversed(left_colors)):
            pairing = "reverse"
        else:
            errors.append("marker color orders must be equal or reversed")

    # A blank separator prevents a marker from joining its same-colored object
    # under the authority's per-color connected-component extraction.
    if any(grid[1][c] != 0 for c in range(w)) or any(grid[r][1] != 0 for r in range(h)):
        errors.append("row 1 and column 1 must remain blank marker/object separators")

    border_colors = set(top_colors) | set(left_colors)
    interior_colors = {
        grid[r][c]
        for r in range(1, h)
        for c in range(1, w)
        if grid[r][c] != 0
    }
    if interior_colors != border_colors:
        errors.append("interior object colors must match marker colors exactly")

    top_by_color = {color: c for c, color in top}
    row_by_color = {color: r for r, color in left}
    object_map: dict[int, dict] = {}
    target_boxes: list[tuple[int, int, int, int]] = []
    for color in sorted(border_colors):
        comps = _components_for_color(grid, color)
        if len(comps) != 1:
            errors.append(f"color {color} must form exactly one interior object")
            continue
        cells = comps[0]
        r1, c1, r2, c2 = _bbox(cells)
        oh, ow = r2 - r1 + 1, c2 - c1 + 1
        if not 2 <= len(cells) <= 5:
            errors.append(f"color {color} object must contain 2..5 cells")
        if oh > 3 or ow > 3:
            errors.append(f"color {color} object bbox must be at most 3x3")
        target_r = row_by_color.get(color)
        target_c = top_by_color.get(color)
        if target_r is None or target_c is None:
            continue
        top0 = target_r - oh // 2
        left0 = target_c - ow // 2
        target_box = (top0, left0, top0 + oh - 1, left0 + ow - 1)
        if top0 < 0 or left0 < 0 or target_box[2] >= h or target_box[3] >= w:
            errors.append(f"color {color} target crop would leave the grid")
        object_map[color] = {
            "color": color,
            "cells": cells,
            "bbox": (r1, c1, r2, c2),
            "dims": (oh, ow),
            "target_center": (target_r, target_c),
            "target_bbox": target_box,
            "docked": (r1, c1) == (top0, left0),
        }
        target_boxes.append(target_box)

    for i, first in enumerate(target_boxes):
        for second in target_boxes[i + 1 :]:
            if _overlap(first, second):
                errors.append("target bounding boxes must not overlap")
                break

    sizes = {len(obj["cells"]) for obj in object_map.values()}
    common_shape_cells = next(iter(sizes)) if len(sizes) == 1 else None
    docked_count = sum(obj["docked"] for obj in object_map.values())
    docking_state = (
        "all_move" if docked_count == 0 else "one_docked" if docked_count == 1 else "multiple_docked"
    )
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "top_markers": top,
        "left_markers": left,
        "top_colors": top_colors,
        "left_colors": left_colors,
        "pairing": pairing,
        "object_map": object_map,
        "n_objs": len(object_map),
        "shape_cells": common_shape_cells,
        "docked_count": docked_count,
        "docking_state": docking_state,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, object]:
    info = _analysis(grid)
    return {
        "grid_h": info.get("height"),
        "grid_w": info.get("width"),
        "n_objs": info.get("n_objs"),
        "marker_pairing": info.get("pairing"),
        "shape_cells": info.get("shape_cells"),
        "docking_state": info.get("docking_state"),
    }


def _crop(grid, bbox):
    r1, c1, r2, c2 = bbox
    return [list(row[c1 : c2 + 1]) for row in grid[r1 : r2 + 1]]


def _paste(out, crop, top: int, left: int, *, solid: bool = False):
    color = next((v for row in crop for v in row if v != 0), 0)
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if solid:
                value = color
            if value != 0:
                out[top + r][left + c] = value


def rule_mirror(grid) -> list[list[int]]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("invalid docking scene: " + "; ".join(info["errors"]))
    out = full_grid(info["height"], info["width"], 0)
    for color in info["top_colors"]:
        obj = info["object_map"][color]
        crop = _crop(grid, obj["bbox"])
        top, left = obj["target_bbox"][:2]
        _paste(out, crop, top, left)
    return out


def strict_canonical_like(grid) -> list[str]:
    info = _analysis(grid)
    if info["errors"]:
        return [f"self_check: {reason}" for reason in info["errors"]]
    profile = (info["height"], info["width"], info["n_objs"] + 1)
    if profile not in {(10, 10, 3), (11, 11, 3), (11, 11, 4)}:
        return [f"linked canonical profile mismatch: {profile!r}"]
    if info["pairing"] != "same":
        return ["canonical marker orders are color-aligned"]
    for obj in info["object_map"].values():
        if len(obj["cells"]) not in (2, 3) or max(obj["dims"]) > 2:
            return ["canonical object crops use two or three cells inside at most 2x2"]
    return []


def _scheduled_values(slot: int, band: str) -> dict[str, object]:
    if slot == 0:
        return dict(grid_h=10, grid_w=10, n_objs=2, marker_pairing="same", shape_cells=2, docking_state="all_move")
    if slot == 1:
        return dict(grid_h=11, grid_w=11, n_objs=2, marker_pairing="reverse", shape_cells=3, docking_state="all_move")
    if slot == 2:
        return dict(grid_h=11, grid_w=11, n_objs=3, marker_pairing="same", shape_cells=3, docking_state="one_docked")
    return {
        "easy": dict(grid_h=9, grid_w=9, n_objs=2, marker_pairing="reverse", shape_cells=3, docking_state="all_move"),
        "medium": dict(grid_h=12, grid_w=12, n_objs=3, marker_pairing="reverse", shape_cells=4, docking_state="all_move"),
        "hard": dict(grid_h=14, grid_w=14, n_objs=3, marker_pairing="reverse", shape_cells=5, docking_state="all_move"),
    }[band]


def _draw_axis(ctx, label: str, scheduled, *, lo=None, hi=None, options=None):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        if options is not None:
            return ctx.draw_choice(label, options)
        return ctx.draw_int(label, lo, hi)
    if options is not None:
        return ctx.draw_choice(label, (scheduled,))
    return ctx.draw_int(label, int(scheduled), int(scheduled))


def _target_layout(h, w, colors, shapes, pairing, rng):
    n = len(colors)
    row_combos = list(combinations(range(2, h - 1), n))
    col_combos = list(combinations(range(2, w - 1), n))
    rng.shuffle(row_combos)
    rng.shuffle(col_combos)
    for rows in row_combos:
        row_colors = colors if pairing == "same" else tuple(reversed(colors))
        row_by_color = dict(zip(row_colors, rows))
        for cols in col_combos:
            col_by_color = dict(zip(colors, cols))
            boxes = []
            valid = True
            for color, shape in zip(colors, shapes):
                sh, sw = _dims(shape)
                top = row_by_color[color] - sh // 2
                left = col_by_color[color] - sw // 2
                box = (top, left, top + sh - 1, left + sw - 1)
                # Keep targets away from marker-bearing row/column so the
                # one-docked curriculum branch remains a valid source scene.
                if top < 2 or left < 2 or box[2] >= h or box[3] >= w:
                    valid = False
                    break
                if any(_overlap(box, other) for other in boxes):
                    valid = False
                    break
                boxes.append(box)
            if valid:
                return row_by_color, col_by_color, dict(zip(colors, boxes))
    raise ValueError("could not realize non-overlapping crosshair targets")


def _translated(shape, top, left):
    return {(top + r, left + c) for r, c in shape}


def _separated(cells, occupied):
    if cells & occupied:
        return False
    for r, c in cells:
        if any((r + dr, c + dc) in occupied for dr, dc in _DIR8):
            return False
    return True


def _place_sources(h, w, colors, shapes, targets, docking_state, rng):
    occupied: set[tuple[int, int]] = set()
    placements: dict[int, tuple[int, int]] = {}
    docked_color = colors[0] if docking_state == "one_docked" else None
    for color, shape in zip(colors, shapes):
        sh, sw = _dims(shape)
        target_top, target_left = targets[color][:2]
        if color == docked_color:
            cells = _translated(shape, target_top, target_left)
            if not _separated(cells, occupied):
                raise ValueError("docked object collides with prior source object")
            placements[color] = (target_top, target_left)
            occupied |= cells
            continue
        candidates = [
            (r, c)
            for r in range(2, h - sh + 1)
            for c in range(2, w - sw + 1)
            if (r, c) != (target_top, target_left)
        ]
        rng.shuffle(candidates)
        # Prefer movement in both axes; it refutes row-only and column-only
        # docking without creating a separate synthetic branch.
        candidates.sort(key=lambda rc: not (rc[0] != target_top and rc[1] != target_left))
        placed = False
        for top, left in candidates:
            cells = _translated(shape, top, left)
            if _separated(cells, occupied):
                placements[color] = (top, left)
                occupied |= cells
                placed = True
                break
        if not placed:
            # The complete override boundary is more important than a visual
            # moat. Different colors remain distinct authority objects even if
            # they touch, so retry with non-overlap only.
            for top, left in candidates:
                cells = _translated(shape, top, left)
                if not (cells & occupied):
                    placements[color] = (top, left)
                    occupied |= cells
                    placed = True
                    break
        if not placed:
            raise ValueError("could not place source objects")
    return placements


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    band = difficulty or "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = int(sample_index) % EXAMPLES_NEEDED
    schedule = _scheduled_values(slot, band)
    h = _draw_axis(ctx, "grid_h", schedule["grid_h"], lo=9, hi=14)
    w = _draw_axis(ctx, "grid_w", schedule["grid_w"], lo=9, hi=14)
    n = _draw_axis(ctx, "n_objs", schedule["n_objs"], lo=2, hi=3)
    pairing = _draw_axis(ctx, "marker_pairing", schedule["marker_pairing"], options=PAIRINGS)
    shape_cells = _draw_axis(ctx, "shape_cells", schedule["shape_cells"], lo=2, hi=5)
    docking_state = _draw_axis(ctx, "docking_state", schedule["docking_state"], options=DOCKING_STATES)

    rng = ctx.draw_rng("layout")
    colors = tuple(rng.sample(range(1, 10), n))
    canonical_like_slot = not overrides and slot in (0, 2)
    variants = _variants(shape_cells, canonical_like=canonical_like_slot)
    shapes = [rng.choice(variants) for _ in colors]
    if shape_cells >= 3 and all(_dims(shape)[0] * _dims(shape)[1] == shape_cells for shape in shapes):
        shapes[0] = next(shape for shape in variants if _dims(shape)[0] * _dims(shape)[1] != shape_cells)

    # Deterministic retries vary only an internal salt stream; public keyed axes
    # stay pinned and observable from the returned grid.
    last_error = None
    for attempt in range(80):
        attempt_rng = ctx.draw_rng(f"layout_retry_{attempt}")
        try:
            row_by_color, col_by_color, targets = _target_layout(
                h, w, colors, shapes, pairing, attempt_rng
            )
            placements = _place_sources(
                h, w, colors, shapes, targets, docking_state, attempt_rng
            )
            grid = full_grid(h, w, 0)
            for color in colors:
                grid[0][col_by_color[color]] = color
                grid[row_by_color[color]][0] = color
            for color, shape in zip(colors, shapes):
                top, left = placements[color]
                for r, c in shape:
                    grid[top + r][left + c] = color
            errors = self_check(grid)
            if errors:
                raise ValueError("; ".join(errors))
            observed = observe_overrides(grid)
            requested = {
                "grid_h": h,
                "grid_w": w,
                "n_objs": n,
                "marker_pairing": pairing,
                "shape_cells": shape_cells,
                "docking_state": docking_state,
            }
            if any(observed[key] != value for key, value in requested.items()):
                raise ValueError(f"observable axis mismatch: {observed!r} != {requested!r}")
            return grid
        except ValueError as exc:
            last_error = exc
    raise ValueError(f"could not realize docking scene: {last_error}")


def _rival_pair_markers_by_rank(grid):
    """Wrong rule: pair the i-th top marker with the i-th left marker."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError(info["errors"][0])
    out = full_grid(info["height"], info["width"], 0)
    rows = [r for r, _ in info["left_markers"]]
    for index, color in enumerate(info["top_colors"]):
        obj = info["object_map"][color]
        crop = _crop(grid, obj["bbox"])
        top = rows[index] - obj["dims"][0] // 2
        left = info["top_markers"][index][0] - obj["dims"][1] // 2
        _paste(out, crop, top, left)
    return out


def _rival_pair_markers_by_reverse_rank(grid):
    """Wrong rule: pair top markers with left markers in reverse rank order."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError(info["errors"][0])
    out = full_grid(info["height"], info["width"], 0)
    rows = [r for r, _ in info["left_markers"]]
    for index, color in enumerate(info["top_colors"]):
        obj = info["object_map"][color]
        crop = _crop(grid, obj["bbox"])
        top = rows[-1 - index] - obj["dims"][0] // 2
        left = info["top_markers"][index][0] - obj["dims"][1] // 2
        _paste(out, crop, top, left)
    return out


def _rival_solid_bbox(grid):
    """Wrong rule: dock a solid rectangle instead of preserving the motif."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError(info["errors"][0])
    out = full_grid(info["height"], info["width"], 0)
    for color in info["top_colors"]:
        obj = info["object_map"][color]
        crop = _crop(grid, obj["bbox"])
        top, left = obj["target_bbox"][:2]
        _paste(out, crop, top, left, solid=True)
    return out


def _rival_keep_source(grid):
    """Wrong rule: erase markers but leave every interior object in place."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError(info["errors"][0])
    out = full_grid(info["height"], info["width"], 0)
    for obj in info["object_map"].values():
        for r, c in obj["cells"]:
            out[r][c] = obj["color"]
    return out


def _witness_pairing(name):
    return lambda grid: _analysis(grid).get("pairing") == name


def _witness_n(n):
    return lambda grid: _analysis(grid).get("n_objs") == n


def _witness_docking(name):
    return lambda grid: _analysis(grid).get("docking_state") == name


def _witness_nonrectangular(grid):
    info = _analysis(grid)
    return any(
        len(obj["cells"]) < obj["dims"][0] * obj["dims"][1]
        for obj in info.get("object_map", {}).values()
    )


def _witness_two_axis_move(grid):
    info = _analysis(grid)
    return any(
        obj["bbox"][0] != obj["target_bbox"][0]
        and obj["bbox"][1] != obj["target_bbox"][1]
        for obj in info.get("object_map", {}).values()
    )


SEMANTIC_WITNESSES = {
    "aligned_marker_orders": _witness_pairing("same"),
    "crossed_marker_orders": _witness_pairing("reverse"),
    "all_objects_move": _witness_docking("all_move"),
    "one_object_already_docked": _witness_docking("one_docked"),
    "preserve_nonrectangular_shape": _witness_nonrectangular,
    "both_row_and_column_change": _witness_two_axis_move,
}

SEMANTIC_RIVALS = {
    "pair_markers_by_rank": _rival_pair_markers_by_rank,
    "pair_markers_by_reverse_rank": _rival_pair_markers_by_reverse_rank,
    "solid_bbox_at_target": _rival_solid_bbox,
    "keep_objects_in_place": _rival_keep_source,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
WITNESS_RIVALS = {
    "aligned_marker_orders": ["pair_markers_by_reverse_rank"],
    "crossed_marker_orders": ["pair_markers_by_rank"],
    "preserve_nonrectangular_shape": ["solid_bbox_at_target"],
    "all_objects_move": ["keep_objects_in_place"],
    "one_object_already_docked": ["keep_objects_in_place"],
    "both_row_and_column_change": ["keep_objects_in_place"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    inputs = []
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        output = pair.get("output")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(grid)
        if output != expected:
            reasons.append(f"demo {index} output disagrees with color-matched docking")
        inputs.append(grid)
    pairings = {_analysis(grid)["pairing"] for grid in inputs}
    if pairings != set(PAIRINGS):
        reasons.append(f"demos cover marker pairings {sorted(pairings)!r}, not both")
    if not any(_analysis(grid)["n_objs"] == 3 for grid in inputs):
        reasons.append("demos omit a three-object scene")
    if not any(_analysis(grid)["docking_state"] == "one_docked" for grid in inputs):
        reasons.append("demos omit the already-docked-object branch")
    for name, rival in SEMANTIC_RIVALS.items():
        if not any(rule_mirror(grid) != rival(grid) for grid in inputs):
            reasons.append(f"{name} rival survives every demo")

    q_grid = query.get("input")
    q_output = query.get("output")
    q_errors = self_check(q_grid)
    if q_errors:
        reasons.append(f"query malformed: {q_errors[0]}")
    elif q_output != rule_mirror(q_grid):
        reasons.append("query output disagrees with color-matched docking")
    return reasons


def mutation_fixtures():
    """Near-miss inputs that the teaching grammar must reject."""
    base = generate(7001, 2, difficulty="medium")
    info = _analysis(base)

    missing_top = [row[:] for row in base]
    missing_top[0][info["top_markers"][0][0]] = 0

    wrong_left_color = [row[:] for row in base]
    wrong_left_color[info["left_markers"][0][0]][0] = 9
    if 9 in set(info["top_colors"]):
        wrong_left_color[info["left_markers"][0][0]][0] = 8

    duplicate_top = [row[:] for row in base]
    blank_col = next(c for c in range(2, len(base[0]) - 1) if duplicate_top[0][c] == 0)
    duplicate_top[0][blank_col] = info["top_colors"][0]

    split_object = [row[:] for row in base]
    color = info["top_colors"][0]
    r, c = next(iter(info["object_map"][color]["cells"]))
    split_object[r][c] = 0
    split_object[-1][-1] = color

    mixed_order = [row[:] for row in base]
    left_rows = [r for r, _ in info["left_markers"]]
    colors = list(info["left_colors"])
    if len(colors) == 3:
        mixed = [colors[1], colors[2], colors[0]]
        for row, value in zip(left_rows, mixed):
            mixed_order[row][0] = value

    target_overlap = [row[:] for row in base]
    # Move the second top marker next to the first so their 2x2/3x2 target
    # boxes overlap while preserving marker-color counts.
    c0, _ = info["top_markers"][0]
    c1, color1 = info["top_markers"][1]
    target_overlap[0][c1] = 0
    new_c = c0 + 1 if c0 + 1 < len(base[0]) - 1 and target_overlap[0][c0 + 1] == 0 else c0 - 1
    target_overlap[0][new_c] = color1

    return [
        ("missing_top_marker", missing_top),
        ("left_marker_color_without_object", wrong_left_color),
        ("duplicate_top_marker_color", duplicate_top),
        ("split_same_color_object", split_object),
        ("mixed_marker_permutation", mixed_order),
        ("overlapping_crosshair_targets", target_overlap),
    ]
