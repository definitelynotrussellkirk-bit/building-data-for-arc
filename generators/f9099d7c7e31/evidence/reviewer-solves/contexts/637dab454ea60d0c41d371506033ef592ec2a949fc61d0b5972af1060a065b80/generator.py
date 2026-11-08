"""Generator for arc_additional_puzzle_bank_volume4:M25.

Select non-zero monochrome objects by the lexicographic key
``(bounding-box width, object size)``.  Crop the ORIGINAL grid to the selected
object's bounding box, preserving background holes and any other-colored cells
that happen to lie inside that box.

The four-sample schedule retains two canonical morphology anchors and includes
shortcut counterexamples:

* a foreign-color cell inside the selected bbox (not an object-mask output),
* a narrower object with more cells (not largest-by-area), and
* a taller, sparser equal-width object losing by size (not bbox area/height), and
* an interior winner (not an always-border crop).
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]

GENERATOR_ID = "f9099d7c7e31"
TASK_ID = "f9099d7c7e31"
VERSION = "4.0.0"
RULE_HASH = "9a6f1f4b6ce5"  # normalized canonical program_solution

SUMMARY = (
    "A 0-background 9-11 square-ish grid contains 3-4 distinct-colored, "
    "4-connected objects. Select by (bbox width DESC, cell count DESC), then "
    "crop the original grid to that object's tight bbox. The crop preserves "
    "the selected shape's holes and any foreign-colored cells inside the bbox."
)

INVARIANTS = [
    "grid is 9..11 by 9..11 with modal background 0",
    "there are exactly 3 or 4 distinct-colored 4-connected objects",
    "the lexicographic maximum (bbox width, size) is unique",
    "selected bbox width is 4..5 and height is 2..3",
    "the selected bbox is a proper crop and is not completely filled by the selected object",
]

EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = (0, 1, 2, 3)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor by difficulty",
        "valid": "9..11",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor by difficulty",
        "valid": "9..11",
    },
    "n_objects": {
        "type": "int",
        "default": "scheduled 3 or 4",
        "valid": "3..4",
    },
    "target_width": {
        "type": "int",
        "default": "scheduled canonical width 4 or 5",
        "valid": "4..5",
    },
    "target_height": {
        "type": "int",
        "default": "scheduled canonical height 2 or 3",
        "valid": "2..3",
    },
    "selection_mode": {
        "type": "str",
        "default": "unique-width anchors and one adversarial size tie-break lesson",
        "valid": "unique_width|width_tie_size",
    },
    "intruder_in_crop": {
        "type": "bool",
        "default": "scheduled False|True",
        "valid": "false|true",
    },
    "larger_narrow_decoy": {
        "type": "bool",
        "default": "scheduled False|True",
        "valid": "false|true",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Complete linked coarse morphology for all five official inputs.  Shape is
# represented by (cells, bbox_h, bbox_w, bbox_area_minus_cells). Horizontal/vertical
# reflection and translation preserve the width rule; quarter-turns do NOT.
_CANONICAL_LINKED_PROFILES = {
    (9, 9, ((3, 2, 2, 1), (4, 2, 3, 2), (5, 2, 4, 3)), False),
    (9, 9, ((3, 2, 2, 1), (5, 2, 4, 3), (7, 3, 5, 8)), True),
    (10, 10, ((3, 2, 2, 1), (4, 2, 3, 2), (5, 2, 4, 3), (7, 3, 5, 8)), False),
    (11, 11, ((4, 2, 3, 2), (5, 2, 4, 3), (7, 3, 5, 8)), False),
    (11, 11, ((3, 2, 2, 1), (4, 2, 3, 2), (5, 2, 4, 3), (7, 3, 5, 8)), False),
}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    """Expose the four-slot lesson schedule to the semantic gate."""
    del seed, difficulty
    return int(sample_index) % 4


def _scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _scheduled_choice(ctx, label: str, options: tuple[Any, ...], scheduled: Any) -> Any:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_defaults(difficulty: str | None, profile: int) -> dict[str, Any]:
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    if band == "easy":
        rows = (
            (9, 9, 3, 4, 2, "unique_width", False, False),
            (9, 9, 3, 5, 3, "unique_width", True, False),
            (9, 9, 4, 5, 3, "width_tie_size", True, True),
            (9, 9, 3, 4, 2, "unique_width", False, False),
        )
    elif band == "hard":
        rows = (
            (11, 11, 3, 5, 3, "unique_width", False, False),
            (11, 11, 4, 5, 3, "unique_width", True, False),
            (11, 11, 4, 5, 3, "width_tie_size", True, True),
            (11, 11, 4, 5, 3, "unique_width", False, False),
        )
    else:
        rows = (
            (10, 10, 4, 5, 3, "unique_width", False, False),
            (10, 10, 4, 5, 3, "unique_width", True, False),
            (10, 10, 4, 5, 3, "width_tie_size", True, True),
            (10, 10, 4, 5, 3, "unique_width", False, False),
        )
    values = rows[profile]
    return dict(zip(AXES, values, strict=True))


def _bbox(cells: set[Cell]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components_nonzero(grid: Grid) -> list[dict[str, Any]]:
    """Same-color 4-connected non-zero objects, matching the task oracle."""
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells: set[Cell] = set()
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0, c0, r1, c1 = _bbox(cells)
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "size": len(cells),
                    "bbox": (r0, c0, r1, c1),
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                }
            )
    return result


def _selected_object(components: list[dict[str, Any]]) -> dict[str, Any]:
    return max(components, key=lambda obj: (obj["width"], obj["size"]))


def _crop(grid: Grid, bbox: tuple[int, int, int, int]) -> Grid:
    r0, c0, r1, c1 = bbox
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _canonical_transform(grid: Grid) -> Grid:
    components = _components_nonzero(grid)
    if not components:
        return []
    return _crop(grid, _selected_object(components)["bbox"])


def _shape_l(height: int, width: int, corner: str) -> set[Cell]:
    if corner not in {"tl", "tr", "bl", "br"}:
        raise ValueError(f"unknown L corner {corner!r}")
    row = 0 if corner[0] == "t" else height - 1
    col = 0 if corner[1] == "l" else width - 1
    return {(row, c) for c in range(width)} | {(r, col) for r in range(height)}


def _dense_tie_geometry(target_height: int, target_width: int, selection_mode: str) -> bool:
    """Only the default 3x5 tie lesson has room for this stronger witness.

    A taller same-width connected loser needs at least h+w cells. Small 2x4
    crops cannot exceed that while retaining both a foreign and a zero cell.
    Keep their lawful legacy geometry rather than silently changing overrides.
    """
    return (target_height, target_width, selection_mode) == (3, 5, "width_tie_size")


def _target_shape(height: int, width: int, corner: str, *, dense_tie: bool) -> set[Cell]:
    if not dense_tie:
        return _shape_l(height, width, corner)
    # Ten connected cells in a 3x5 bbox; the top-right three-cell recess lets
    # a 4x3 narrower, larger object intrude while zeros remain below it.
    shape = {(r, c) for r, length in enumerate((2, 3, 5)) for c in range(length)}
    if corner[0] == "t":
        shape = {(height - 1 - r, c) for r, c in shape}
    if corner[1] == "r":
        shape = {(r, width - 1 - c) for r, c in shape}
    return shape


def _shape_line(width: int) -> set[Cell]:
    return {(0, c) for c in range(width)}


def _shape_solid3() -> set[Cell]:
    return {(r, c) for r in range(3) for c in range(3)}


def _shape_dims(shape: set[Cell]) -> tuple[int, int]:
    r0, c0, r1, c1 = _bbox(shape)
    return r1 - r0 + 1, c1 - c0 + 1


def _translate(shape: set[Cell], r0: int, c0: int) -> set[Cell]:
    return {(r0 + r, c0 + c) for r, c in shape}


def _inside_bbox(cell: Cell, bbox: tuple[int, int, int, int]) -> bool:
    r, c = cell
    r0, c0, r1, c1 = bbox
    return r0 <= r <= r1 and c0 <= c <= c1


def _candidate_placements(
    shape: set[Cell],
    *,
    h: int,
    w: int,
    occupied: set[Cell],
    target_bbox: tuple[int, int, int, int],
    must_intrude: bool,
    rng,
    prefer_left_of: int | None,
) -> list[set[Cell]]:
    sh, sw = _shape_dims(shape)
    placements: list[set[Cell]] = []
    for r0 in range(h - sh + 1):
        for c0 in range(w - sw + 1):
            cells = _translate(shape, r0, c0)
            if cells & occupied:
                continue
            inside = sum(_inside_bbox(cell, target_bbox) for cell in cells)
            if must_intrude:
                if inside == 0 or inside == len(cells):
                    continue
            elif inside:
                continue
            placements.append(cells)
    rng.shuffle(placements)
    if prefer_left_of is not None:
        placements.sort(key=lambda cells: min(c for _, c in cells) >= prefer_left_of)
    return placements


def _place_specs(
    specs: list[dict[str, Any]],
    *,
    h: int,
    w: int,
    occupied: set[Cell],
    target_bbox: tuple[int, int, int, int],
    rng,
    require_left_witness: bool,
) -> list[set[Cell]] | None:
    ordered = sorted(specs, key=lambda spec: (not spec["intruder"], -len(spec["shape"])))
    placed: list[set[Cell]] = []

    def search(index: int, current: set[Cell]) -> bool:
        if index == len(ordered):
            if require_left_witness:
                target_left = target_bbox[1]
                if not any(min(c for _, c in cells) < target_left for cells in placed):
                    return False
            return True
        spec = ordered[index]
        candidates = _candidate_placements(
            spec["shape"],
            h=h,
            w=w,
            occupied=current,
            target_bbox=target_bbox,
            must_intrude=bool(spec["intruder"]),
            rng=rng,
            prefer_left_of=target_bbox[1] if require_left_witness else None,
        )
        for cells in candidates:
            placed.append(cells)
            if search(index + 1, current | cells):
                return True
            placed.pop()
        return False

    if search(0, set(occupied)):
        # `ordered` controls placement order; return aligned with those specs.
        for spec, cells in zip(ordered, placed, strict=True):
            spec["cells"] = cells
        return placed
    return None


def _canonical_distractor_widths(
    h: int,
    w: int,
    n_objects: int,
    target_width: int,
    target_height: int,
    selection_mode: str,
    intruder: bool,
    larger_narrow: bool,
) -> tuple[int, ...] | None:
    if selection_mode != "unique_width" or larger_narrow:
        return None
    mapping = {
        (9, 9, 3, 4, 2, False): (2, 3),
        (9, 9, 3, 5, 3, True): (2, 4),
        (10, 10, 4, 5, 3, False): (2, 3, 4),
        (11, 11, 3, 5, 3, False): (3, 4),
        (11, 11, 4, 5, 3, False): (2, 3, 4),
    }
    return mapping.get((h, w, n_objects, target_width, target_height, intruder))


def _build_specs(
    *,
    n_objects: int,
    target_width: int,
    target_height: int,
    selection_mode: str,
    intruder: bool,
    larger_narrow: bool,
    canonical_widths: tuple[int, ...] | None,
    rng,
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    if canonical_widths is not None:
        for width in canonical_widths:
            height = 2
            specs.append(
                {
                    "kind": "canonical",
                    "width": width,
                    "shape": _shape_l(height, width, rng.choice(("tl", "tr", "bl", "br"))),
                    "intruder": False,
                }
            )
        if intruder:
            candidates = [spec for spec in specs if spec["width"] == 2]
            if not candidates:
                raise ValueError("canonical intruder profile lacks a width-2 object")
            candidates[0]["intruder"] = True
        return specs

    dense_tie = _dense_tie_geometry(target_height, target_width, selection_mode)
    if selection_mode == "width_tie_size":
        # In the adversarial lesson the 4x5 sparse loser has 8 cells; the 3x5
        # target has 10. This distinguishes cell count from height and bbox area.
        tie_shape = (
            _shape_l(4, 5, rng.choice(("tl", "tr", "bl", "br")))
            if dense_tie else _shape_line(target_width)
        )
        specs.append(
            {
                "kind": "width_tie",
                "width": target_width,
                "shape": tie_shape,
                "intruder": False,
            }
        )

    if larger_narrow:
        specs.append(
            {
                "kind": "larger_narrow",
                "width": 3,
                "shape": ({(r, c) for r in range(4) for c in range(3)}
                          if dense_tie else _shape_solid3()),
                "intruder": bool(intruder),
            }
        )

    if intruder and not any(spec["intruder"] for spec in specs):
        specs.append(
            {
                "kind": "intruder",
                "width": 2,
                "shape": _shape_l(2, 2, "bl"),
                "intruder": True,
            }
        )

    if dense_tie and n_objects == 4 and len(specs) < n_objects - 1:
        # Both height directions must lose in the SAME complete lesson. Merely
        # replacing the old short tie by a tall tie creates a shortest-widest
        # shortcut. Four-object defaults have a slot for both counterexamples.
        specs.append({"kind": "short_width_tie", "width": target_width,
                      "shape": _shape_line(target_width), "intruder": False})

    candidates = [target_width - 1, 3, 2]
    cursor = 0
    while len(specs) < n_objects - 1:
        width = candidates[cursor % len(candidates)]
        cursor += 1
        if width >= target_width:
            continue
        specs.append(
            {
                "kind": "regular",
                "width": width,
                "shape": _shape_l(2, width, rng.choice(("tl", "tr", "bl", "br"))),
                "intruder": False,
            }
        )
    if len(specs) > n_objects - 1:
        raise ValueError(
            "requested semantic controls require more objects than n_objects permits"
        )
    return specs


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _scheduled_defaults(difficulty, profile)

    h = _scheduled_int(ctx, "grid_h", 9, 11, int(defaults["grid_h"]))
    w = _scheduled_int(ctx, "grid_w", 9, 11, int(defaults["grid_w"]))
    n_objects = _scheduled_int(ctx, "n_objects", 3, 4, int(defaults["n_objects"]))
    target_width = _scheduled_int(
        ctx, "target_width", 4, 5, int(defaults["target_width"])
    )
    target_height = _scheduled_int(
        ctx, "target_height", 2, 3, int(defaults["target_height"])
    )
    selection_mode = str(
        _scheduled_choice(
            ctx,
            "selection_mode",
            ("unique_width", "width_tie_size"),
            defaults["selection_mode"],
        )
    )
    intruder = bool(
        _scheduled_choice(ctx, "intruder_in_crop", (False, True), defaults["intruder_in_crop"])
    )
    larger_narrow = bool(
        _scheduled_choice(
            ctx,
            "larger_narrow_decoy",
            (False, True),
            defaults["larger_narrow_decoy"],
        )
    )

    layout_rng = ctx.draw_rng("layout")
    colors = list(ctx.draw_distinct_colors("object_colors", n=n_objects, exclude={0}))
    layout_rng.shuffle(colors)

    canonical_widths = _canonical_distractor_widths(
        h,
        w,
        n_objects,
        target_width,
        target_height,
        selection_mode,
        intruder,
        larger_narrow,
    )
    specs = _build_specs(
        n_objects=n_objects,
        target_width=target_width,
        target_height=target_height,
        selection_mode=selection_mode,
        intruder=intruder,
        larger_narrow=larger_narrow,
        canonical_widths=canonical_widths,
        rng=layout_rng,
    )

    dense_tie = _dense_tie_geometry(target_height, target_width, selection_mode)
    target_corners = ["bl"] if intruder else ["tl", "tr", "bl", "br"]
    layout_rng.shuffle(target_corners)
    candidate_origins = [
        (r0, c0)
        for r0 in range(h - target_height + 1)
        for c0 in range(w - target_width + 1)
    ]
    layout_rng.shuffle(candidate_origins)

    def origin_score(origin: tuple[int, int]) -> tuple[int, int]:
        r0, c0 = origin
        r1, c1 = r0 + target_height - 1, c0 + target_width - 1
        if profile == 0:
            preferred = r0 == 0
        elif profile == 2:
            preferred = c1 == w - 1 and r0 >= 2
        else:
            preferred = r0 > 0 and c0 > 0 and r1 < h - 1 and c1 < w - 1
        intrusion_room = (not intruder) or r0 >= (3 if dense_tie and larger_narrow else 2)
        return (0 if preferred and intrusion_room else 1, 0 if intrusion_room else 1)

    candidate_origins.sort(key=origin_score)
    require_left_witness = profile in (1, 2)

    for corner in target_corners:
        target_local = _target_shape(target_height, target_width, corner, dense_tie=dense_tie)
        for r0, c0 in candidate_origins:
            target_cells = _translate(target_local, r0, c0)
            target_bbox = (r0, c0, r0 + target_height - 1, c0 + target_width - 1)
            trial_specs = [dict(spec) for spec in specs]
            placed = _place_specs(
                trial_specs,
                h=h,
                w=w,
                occupied=target_cells,
                target_bbox=target_bbox,
                rng=layout_rng,
                require_left_witness=require_left_witness,
            )
            if placed is None:
                continue
            grid = full_grid(h, w, 0)
            for r, c in target_cells:
                grid[r][c] = colors[0]
            for index, spec in enumerate(sorted(trial_specs, key=lambda item: (not item["intruder"], -len(item["shape"])))):
                for r, c in spec["cells"]:
                    grid[r][c] = colors[index + 1]
            errors = self_check(grid)
            if errors:
                continue
            observed = observe_overrides(grid)
            requested = {
                "n_objects": n_objects,
                "target_width": target_width,
                "target_height": target_height,
                "selection_mode": selection_mode,
                "intruder_in_crop": intruder,
                "larger_narrow_decoy": larger_narrow,
            }
            if any(observed[key] != value for key, value in requested.items()):
                continue
            return grid

    raise ValueError(
        "could not place a lawful scene for "
        f"{h=} {w=} {n_objects=} {target_width=} {target_height=} "
        f"{selection_mode=} {intruder=} {larger_narrow=}"
    )


def observe_overrides(grid: Grid) -> dict[str, Any]:
    """Recover every exact declared axis from the returned grid."""
    h = len(grid)
    w = len(grid[0]) if grid else 0
    components = _components_nonzero(grid) if h and w else []
    if not components:
        return {
            "grid_h": h,
            "grid_w": w,
            "n_objects": 0,
            "target_width": 0,
            "target_height": 0,
            "selection_mode": "invalid",
            "intruder_in_crop": False,
            "larger_narrow_decoy": False,
        }
    target = _selected_object(components)
    max_width = target["width"]
    widest = [obj for obj in components if obj["width"] == max_width]
    selection_mode = "unique_width" if len(widest) == 1 else "width_tie_size"
    foreign_inside = any(
        grid[r][c] != 0 and (r, c) not in target["cells"]
        for r in range(target["bbox"][0], target["bbox"][2] + 1)
        for c in range(target["bbox"][1], target["bbox"][3] + 1)
    )
    larger_narrow = any(
        obj["width"] < target["width"] and obj["size"] > target["size"]
        for obj in components
    )
    return {
        "grid_h": h,
        "grid_w": w,
        "n_objects": len(components),
        "target_width": target["width"],
        "target_height": target["height"],
        "selection_mode": selection_mode,
        "intruder_in_crop": foreign_inside,
        "larger_narrow_decoy": larger_narrow,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-valid input grammar and reject rule-hiding scenes."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    height = len(grid)
    errors: list[str] = []
    if not 9 <= height <= 11 or not 9 <= width <= 11:
        errors.append(f"grid must be 9..11 by 9..11, got {height}x{width}")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors
    counts = {value: sum(cell == value for row in grid for cell in row) for value in range(10)}
    if counts[0] <= max(counts[color] for color in range(1, 10)):
        errors.append("background 0 must be the modal color")

    components = _components_nonzero(grid)
    if not 3 <= len(components) <= 4:
        errors.append(f"expected 3-4 non-zero objects, found {len(components)}")
        return errors
    colors = [obj["color"] for obj in components]
    if len(colors) != len(set(colors)):
        errors.append("each object must use a distinct color exactly once")
    for obj in components:
        if obj["size"] < 3:
            errors.append(f"color-{obj['color']} object has fewer than 3 cells")

    ranked = sorted(components, key=lambda obj: (obj["width"], obj["size"]), reverse=True)
    target = ranked[0]
    if len(ranked) > 1 and (ranked[0]["width"], ranked[0]["size"]) == (
        ranked[1]["width"],
        ranked[1]["size"],
    ):
        errors.append("top (bbox width, size) key is tied; selected object is ambiguous")
    if not 4 <= target["width"] <= 5:
        errors.append(f"selected bbox width must be 4..5, found {target['width']}")
    if not 2 <= target["height"] <= 3:
        errors.append(f"selected bbox height must be 2..3, found {target['height']}")
    r0, c0, r1, c1 = target["bbox"]
    if target["height"] == height and target["width"] == width:
        errors.append("selected bbox is the whole input; crop operation is hidden")
    bbox_area = target["height"] * target["width"]
    if target["size"] >= bbox_area:
        errors.append("selected object fills its bbox; holes/crop preservation are hidden")
    if not any(grid[r][c] == 0 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
        errors.append("selected bbox has no background cell to preserve")
    return errors


def _coarse_signature(obj: dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        obj["size"],
        obj["height"],
        obj["width"],
        obj["height"] * obj["width"] - obj["size"],
    )


def semantic_observables(grid: Grid) -> dict[str, Any]:
    components = _components_nonzero(grid)
    if not components:
        return {}
    target = _selected_object(components)
    observed = observe_overrides(grid)
    return {
        **observed,
        "object_signatures": tuple(sorted(_coarse_signature(obj) for obj in components)),
        "target_touches_top": target["bbox"][0] == 0,
        "target_touches_bottom": target["bbox"][2] == len(grid) - 1,
        "target_touches_left": target["bbox"][1] == 0,
        "target_touches_right": target["bbox"][3] == len(grid[0]) - 1,
        "target_is_leftmost": target["bbox"][1] == min(obj["bbox"][1] for obj in components),
    }


def strict_canonical_like(grid: Grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return list(errors)
    obs = semantic_observables(grid)
    profile = (
        obs["grid_h"],
        obs["grid_w"],
        obs["object_signatures"],
        obs["intruder_in_crop"],
    )
    if obs["selection_mode"] != "unique_width":
        return ["official inputs have a unique widest object"]
    if profile not in _CANONICAL_LINKED_PROFILES:
        return [f"linked morphology {profile!r} is not one of the five official profiles"]
    return []


MIN_STRICT_FRAC = 0.20


def _largest_by_size(grid: Grid) -> Grid:
    components = _components_nonzero(grid)
    if not components:
        return []
    return _crop(grid, max(components, key=lambda obj: (obj["size"], obj["width"]))["bbox"])


def _mask_winner_only(grid: Grid) -> Grid:
    components = _components_nonzero(grid)
    if not components:
        return []
    target = _selected_object(components)
    r0, c0, r1, c1 = target["bbox"]
    return [
        [grid[r][c] if (r, c) in target["cells"] else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _smallest_of_widest(grid: Grid) -> Grid:
    components = _components_nonzero(grid)
    if not components:
        return []
    max_width = max(obj["width"] for obj in components)
    target = min(
        (obj for obj in components if obj["width"] == max_width),
        key=lambda obj: obj["size"],
    )
    return _crop(grid, target["bbox"])


def _leftmost_object(grid: Grid) -> Grid:
    components = _components_nonzero(grid)
    if not components:
        return []
    target = min(components, key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))
    return _crop(grid, target["bbox"])


def _largest_bbox_area(grid: Grid) -> Grid:
    components = _components_nonzero(grid)
    if not components:
        return []
    target = max(components, key=lambda obj: (obj["height"] * obj["width"],
                                              obj["width"], obj["size"]))
    return _crop(grid, target["bbox"])


def _widest_then_tallest(grid: Grid) -> Grid:
    components = _components_nonzero(grid)
    if not components:
        return []
    target = max(components, key=lambda obj: (obj["width"], obj["height"], obj["size"]))
    return _crop(grid, target["bbox"])


def _widest_then_shortest(grid: Grid) -> Grid:
    components = _components_nonzero(grid)
    if not components:
        return []
    target = max(components, key=lambda obj: (obj["width"], -obj["height"], obj["size"]))
    return _crop(grid, target["bbox"])


def _on_border(obj: dict[str, Any], h: int, w: int) -> bool:
    r0, c0, r1, c1 = obj["bbox"]
    return r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1


def _border_only(grid: Grid) -> Grid:
    components = _components_nonzero(grid)
    border = [obj for obj in components if _on_border(obj, len(grid), len(grid[0]))]
    if not border:
        return []
    return _crop(grid, _selected_object(border)["bbox"])


def _geometry_witness(grid: Grid, name: str) -> bool:
    components = _components_nonzero(grid)
    if not components:
        return False
    target = _selected_object(components)
    if name == "interior_target":
        return not _on_border(target, len(grid), len(grid[0]))
    if name == "taller_same_width_loses":
        return any(obj["width"] == target["width"] and obj["height"] > target["height"]
                   and obj["size"] < target["size"] for obj in components)
    if name == "shorter_same_width_loses":
        return any(obj["width"] == target["width"] and obj["height"] < target["height"]
                   and obj["size"] < target["size"] for obj in components)
    if name == "larger_bbox_loses":
        return any(obj["height"] * obj["width"] > target["height"] * target["width"]
                   for obj in components)
    raise ValueError(f"unknown geometry witness: {name}")


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "largest_by_area": _largest_by_size,
    "winner_pixels_only": _mask_winner_only,
    "smallest_of_widest": _smallest_of_widest,
    "leftmost_object": _leftmost_object,
    "largest_bbox_area": _largest_bbox_area,
    "widest_then_tallest": _widest_then_tallest,
    "widest_then_shortest": _widest_then_shortest,
    "border_only": _border_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "largest_bbox_area": _largest_bbox_area,
    "widest_then_tallest": _widest_then_tallest,
    "largest_by_area": _largest_by_size,
    "smallest_of_widest": _smallest_of_widest,
}

SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "shorter_same_width_loses": lambda grid: _geometry_witness(grid, "shorter_same_width_loses"),
    "larger_bbox_loses": lambda grid: _geometry_witness(grid, "larger_bbox_loses"),
    "taller_same_width_loses": lambda grid: _geometry_witness(grid, "taller_same_width_loses"),
    "interior_target": lambda grid: _geometry_witness(grid, "interior_target"),
    "foreign_cell_inside_crop": lambda grid: bool(
        semantic_observables(grid).get("intruder_in_crop")
    ),
    "narrower_object_has_more_cells": lambda grid: bool(
        semantic_observables(grid).get("larger_narrow_decoy")
    ),
    "width_tie_resolved_by_size": lambda grid: (
        semantic_observables(grid).get("selection_mode") == "width_tie_size"
    ),
    "target_not_leftmost": lambda grid: not bool(
        semantic_observables(grid).get("target_is_leftmost", True)
    ),
}

WITNESS_RIVALS = {
    "shorter_same_width_loses": ["widest_then_shortest"],
    "larger_bbox_loses": ["largest_bbox_area"],
    "taller_same_width_loses": ["widest_then_tallest"],
    "interior_target": ["border_only"],
    "foreign_cell_inside_crop": ["winner_pixels_only"],
    "narrower_object_has_more_cells": ["largest_by_area"],
    "width_tie_resolved_by_size": ["smallest_of_widest"],
    "target_not_leftmost": ["leftmost_object"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Name every wrong rule that survives all demos but changes the query."""
    survivors: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query["output"]:
                survivors.append(name)
    if survivors:
        return [f"plausible rival(s) survive all demonstrations: {survivors}"]
    return []
