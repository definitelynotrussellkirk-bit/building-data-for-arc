"""Generator for arc_puzzle_bank_next21:M14 — fill the largest hollow object.

The authoritative Racket rule finds every same-color 4-connected object with
one or more enclosed zero regions, selects the hollow object with the greatest
number of colored cells, and fills all of that object's holes with its color.
Other hollow objects and all solid objects remain unchanged.

The original v1 distribution contained only one hollow object, so the
"largest" choice was never observable.  This version schedules four scene
profiles that make the selection rule identifiable and explicitly contradict
plausible shortcuts based on scan order, hole count, bounding-box area, outer
perimeter, or the largest object regardless of hollowness.  The bbox-conflict
profile has a thick-walled, two-hole winner, so filling only one hole is wrong.
Keyed row/column stretching varies actual component geometry, not just color
and placement, while preserving each profile's intended counterexample.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c2b9484357c1"
TASK_ID = "c2b9484357c1"
VERSION = "2.1.0"
RULE_HASH = "4d65cf4d4b83"

SUMMARY = (
    "A 0-background grid contains two differently colored hollow objects and "
    "optionally one larger solid distractor. Select the hollow object with the "
    "greatest number of colored cells, fill every enclosed zero region of that "
    "object with its own color, and leave every other object unchanged."
)

INVARIANTS = [
    "background is color 0 and all nonzero components have distinct colors",
    "there are one or two hollow components and at most one solid rectangle",
    "the largest hollow component by colored-cell count is unique",
    "every hollow component has a complete outer perimeter and one or two enclosed zero regions",
    "each ordinary four-example lesson includes a two-hole winner with a shorter outer perimeter",
    "ordinary generated draws contain exactly two hollow candidates, so the selection is observable",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

SCENE_PROFILES = (
    "aligned_first",
    "aligned_last",
    "hole_count_conflict",
    "bbox_area_conflict",
)
SCHEDULE_PROFILES = SCENE_PROFILES
PALETTE_KINDS = ("canonical", "broad")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 8..12 with canonical-profile anchors",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 9..14 with canonical-profile anchors",
        "valid": "9..14",
    },
    "scene_profile": {
        "type": "enum",
        "default": "four-slot lesson schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "solid_decoy": {
        "type": "bool",
        "default": "scheduled false|true",
        "valid": "false|true",
    },
    "palette_kind": {
        "type": "enum",
        "default": "scheduled canonical|broad",
        "valid": "|".join(PALETTE_KINDS),
    },
}

# Every declared boundary combination is supported.  Declaring the empty list
# opts the override checker into the strict policy: an unexpected rejection is
# a defect, not a legacy-policy warning.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_CANONICAL_COLORS = (2, 3, 4, 5)
_BROAD_COLORS = (1, 6, 7, 8, 9)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_DIMS = {
    "easy": (8, 9),
    "medium": (9, 10),
    "hard": (10, 11),
}
_PROFILE_SCHEDULE = SCENE_PROFILES
_SOLID_SCHEDULE = (False, True, True, False)
_PALETTE_SCHEDULE = ("canonical", "broad", "canonical", "broad")

Grid = list[list[int]]
Cell = tuple[int, int]


def _copy_grid(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _bbox(cells: Iterable[Cell]) -> tuple[int, int, int, int]:
    materialized = tuple(cells)
    rows = [r for r, _ in materialized]
    cols = [c for _, c in materialized]
    return min(rows), min(cols), max(rows), max(cols)


def _perimeter(r0: int, c0: int, r1: int, c1: int) -> set[Cell]:
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _components(grid: Grid) -> list[dict[str, Any]]:
    """Same-color, 4-connected nonzero components in scan order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells: set[Cell] = set()
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            bb = _bbox(cells)
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": bb,
                    "size": len(cells),
                    "scan_key": (bb[0], bb[1]),
                }
            )
    return result


def _hole_regions(cells: set[Cell]) -> list[set[Cell]]:
    """Return enclosed 4-connected zero regions inside the component bbox.

    This mirrors the canonical Racket rule: the local mask contains only this
    component's cells, and a zero region is a hole iff it does not touch the
    local bounding-box border.
    """
    r0, c0, r1, c1 = _bbox(cells)
    height = r1 - r0 + 1
    width = c1 - c0 + 1
    occupied = {(r - r0, c - c0) for r, c in cells}
    unseen = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in occupied
    }
    holes: list[set[Cell]] = []
    while unseen:
        start = next(iter(unseen))
        unseen.remove(start)
        queue = deque([start])
        region = {start}
        touches_border = False
        while queue:
            rr, cc = queue.popleft()
            if rr in (0, height - 1) or cc in (0, width - 1):
                touches_border = True
            for dr, dc in _DIR4:
                nxt = (rr + dr, cc + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    region.add(nxt)
                    queue.append(nxt)
        if not touches_border:
            holes.append({(r0 + r, c0 + c) for r, c in region})
    return holes


def _scene(grid: Grid) -> list[dict[str, Any]]:
    scene = _components(grid)
    for obj in scene:
        holes = _hole_regions(obj["cells"])
        obj["holes"] = holes
        obj["hole_cells"] = set().union(*holes) if holes else set()
        obj["hollow"] = bool(holes)
        r0, c0, r1, c1 = obj["bbox"]
        obj["bbox_area"] = (r1 - r0 + 1) * (c1 - c0 + 1)
    return scene


def _hollows(scene: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (obj for obj in scene if obj["hollow"]),
        key=lambda obj: obj["scan_key"],
    )


def _largest_hollow(scene: list[dict[str, Any]]) -> dict[str, Any] | None:
    hollow = _hollows(scene)
    return max(hollow, key=lambda obj: obj["size"]) if hollow else None


def _fill_objects(grid: Grid, selected: Iterable[dict[str, Any]]) -> Grid:
    out = _copy_grid(grid)
    for obj in selected:
        for r, c in obj["hole_cells"]:
            out[r][c] = obj["color"]
    return out


def _true_output(grid: Grid) -> Grid:
    scene = _scene(grid)
    target = _largest_hollow(scene)
    return _fill_objects(grid, [target] if target is not None else [])


def _fill_all_hollows(grid: Grid) -> Grid:
    scene = _scene(grid)
    return _fill_objects(grid, _hollows(scene))


def _fill_smallest_hollow(grid: Grid) -> Grid:
    scene = _scene(grid)
    hollow = _hollows(scene)
    target = min(hollow, key=lambda obj: obj["size"]) if hollow else None
    return _fill_objects(grid, [target] if target is not None else [])


def _fill_first_hollow(grid: Grid) -> Grid:
    hollow = _hollows(_scene(grid))
    return _fill_objects(grid, hollow[:1])


def _fill_last_hollow(grid: Grid) -> Grid:
    hollow = _hollows(_scene(grid))
    return _fill_objects(grid, hollow[-1:])


def _fill_largest_bbox_hollow(grid: Grid) -> Grid:
    scene = _scene(grid)
    hollow = _hollows(scene)
    target = max(hollow, key=lambda obj: obj["bbox_area"]) if hollow else None
    return _fill_objects(grid, [target] if target is not None else [])


def _fill_most_hole_regions_hollow(grid: Grid) -> Grid:
    scene = _scene(grid)
    hollow = _hollows(scene)
    target = max(hollow, key=lambda obj: len(obj["holes"])) if hollow else None
    return _fill_objects(grid, [target] if target is not None else [])


def _fill_largest_object_overall(grid: Grid) -> Grid:
    scene = _scene(grid)
    target = max(scene, key=lambda obj: obj["size"]) if scene else None
    return _fill_objects(grid, [target] if target is not None else [])


def _outer_perimeter(obj: dict[str, Any]) -> int:
    r0, c0, r1, c1 = obj["bbox"]
    return 2 * ((r1 - r0 + 1) + (c1 - c0 + 1)) - 4


def _fill_largest_outer_perimeter(grid: Grid) -> Grid:
    hollow = _hollows(_scene(grid))
    chosen = max(hollow, key=_outer_perimeter) if hollow else None
    return _fill_objects(grid, [chosen] if chosen is not None else [])


def _fill_largest_single_hole(grid: Grid) -> Grid:
    hollow = [obj for obj in _hollows(_scene(grid)) if len(obj["holes"]) == 1]
    chosen = max(hollow, key=lambda obj: obj["size"]) if hollow else None
    return _fill_objects(grid, [chosen] if chosen is not None else [])


def _fill_one_hole_of_largest(grid: Grid) -> Grid:
    chosen = _largest_hollow(_scene(grid))
    out = _copy_grid(grid)
    if chosen is not None:
        # Canonical, deterministic scan order, independent of set traversal.
        hole = min(chosen["holes"], key=min)
        for r, c in hole:
            out[r][c] = chosen["color"]
    return out


def _identity(grid: Grid) -> Grid:
    return _copy_grid(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "fill_all_hollows": _fill_all_hollows,
    "fill_smallest_hollow": _fill_smallest_hollow,
    "fill_first_hollow": _fill_first_hollow,
    "fill_last_hollow": _fill_last_hollow,
    "fill_largest_bbox_hollow": _fill_largest_bbox_hollow,
    "fill_most_hole_regions_hollow": _fill_most_hole_regions_hollow,
    "fill_largest_object_overall": _fill_largest_object_overall,
    "identity": _identity,
    "fill_largest_outer_perimeter": _fill_largest_outer_perimeter,
    "fill_largest_single_hole": _fill_largest_single_hole,
    "fill_one_hole_of_largest": _fill_one_hole_of_largest,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS

# These shortcuts all fit every official pair.  The generated witnesses below
# are therefore essential: canonical demonstrations alone cannot falsify them.
CANONICAL_SHORTCUTS = {
    "fill_first_hollow": _fill_first_hollow,
    "fill_largest_bbox_hollow": _fill_largest_bbox_hollow,
    "fill_most_hole_regions_hollow": _fill_most_hole_regions_hollow,
    "fill_largest_object_overall": _fill_largest_object_overall,
    "fill_largest_outer_perimeter": _fill_largest_outer_perimeter,
    "fill_largest_single_hole": _fill_largest_single_hole,
    "fill_one_hole_of_largest": _fill_one_hole_of_largest,
}


def _profile_from_scene(scene: list[dict[str, Any]]) -> str:
    hollow = _hollows(scene)
    if len(hollow) != 2:
        return "unclassified"
    target = max(hollow, key=lambda obj: obj["size"])
    rival = hollow[0] if hollow[1] is target else hollow[1]
    if len(rival["holes"]) > len(target["holes"]):
        return "hole_count_conflict"
    if rival["bbox_area"] > target["bbox_area"]:
        return "bbox_area_conflict"
    return "aligned_first" if hollow[0] is target else "aligned_last"


def observe_overrides(grid: Grid) -> dict[str, Any]:
    """Recover every exact non-dimension axis from the returned grid."""
    scene = _scene(grid)
    colors = {obj["color"] for obj in scene}
    if colors and colors <= set(_CANONICAL_COLORS):
        palette_kind = "canonical"
    elif colors and colors <= set(_BROAD_COLORS):
        palette_kind = "broad"
    else:
        palette_kind = "mixed_or_invalid"
    return {
        "scene_profile": _profile_from_scene(scene),
        "solid_decoy": sum(not obj["hollow"] for obj in scene) == 1,
        "palette_kind": palette_kind,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input grammar and reject rule-hiding impostors."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    height = len(grid)
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    scene = _scene(grid)
    if not 2 <= len(scene) <= 3:
        errors.append(f"expected 2-3 nonzero components, found {len(scene)}")
    colors = [obj["color"] for obj in scene]
    if len(colors) != len(set(colors)):
        errors.append("each disconnected component must use a distinct color")

    hollow = _hollows(scene)
    solids = [obj for obj in scene if not obj["hollow"]]
    if not 1 <= len(hollow) <= 2:
        errors.append(f"expected 1-2 hollow components, found {len(hollow)}")
    if len(solids) > 1:
        errors.append(f"expected at most one solid distractor, found {len(solids)}")
    if len(hollow) == 1 and len(solids) != 1:
        errors.append("a one-hollow scene must also contain one solid distractor")

    for obj in scene:
        color = obj["color"]
        cells = obj["cells"]
        r0, c0, r1, c1 = obj["bbox"]
        foreign = [
            (r, c, grid[r][c])
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if grid[r][c] != 0 and (r, c) not in cells
        ]
        if foreign:
            errors.append(
                f"color-{color} bbox contains foreign nonzero cells, which the oracle would overwrite"
            )
        if obj["hollow"]:
            if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
                errors.append(f"color-{color} hollow bbox is smaller than 3x3")
            if not _perimeter(r0, c0, r1, c1) <= cells:
                errors.append(f"color-{color} hollow object lacks a complete outer perimeter")
            if not 1 <= len(obj["holes"]) <= 2:
                errors.append(
                    f"color-{color} must contain one or two enclosed regions, found {len(obj['holes'])}"
                )
        else:
            area = (r1 - r0 + 1) * (c1 - c0 + 1)
            if obj["size"] != area:
                errors.append(f"color-{color} solid distractor does not fill its bbox")

    if hollow:
        sizes = sorted((obj["size"] for obj in hollow), reverse=True)
        if len(sizes) > 1 and sizes[0] == sizes[1]:
            errors.append("largest hollow component is tied")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the official manifold and a narrow generated anchor subset."""
    errors = self_check(grid)
    if errors:
        return list(errors)
    reasons: list[str] = []
    dims = (len(grid), len(grid[0]))
    if dims not in {(8, 9), (9, 10), (10, 11)}:
        reasons.append(f"dimensions {dims} are outside the three canonical profiles")
    scene = _scene(grid)
    colors = {obj["color"] for obj in scene}
    if not colors <= set(_CANONICAL_COLORS):
        reasons.append("nonzero colors fall outside canonical palette {2,3,4,5}")
    if len(scene) != 2:
        reasons.append("canonical inputs contain exactly two components")
    for obj in _hollows(scene):
        r0, c0, r1, c1 = obj["bbox"]
        if obj["cells"] != _perimeter(r0, c0, r1, c1):
            reasons.append("canonical hollow objects are plain rectangular frames")
            break
    return reasons


def _lawful_two_hollow_scene(grid: Grid) -> tuple[list[dict[str, Any]], dict[str, Any]] | None:
    if self_check(grid):
        return None
    scene = _scene(grid)
    hollow = _hollows(scene)
    if len(hollow) != 2:
        return None
    return scene, max(hollow, key=lambda obj: obj["size"])


def _witness_two_hollows(grid: Grid) -> bool:
    return _lawful_two_hollow_scene(grid) is not None


def _witness_target_first(grid: Grid) -> bool:
    parsed = _lawful_two_hollow_scene(grid)
    return parsed is not None and _hollows(parsed[0])[0] is parsed[1]


def _witness_target_last(grid: Grid) -> bool:
    parsed = _lawful_two_hollow_scene(grid)
    return parsed is not None and _hollows(parsed[0])[-1] is parsed[1]


def _witness_hole_count_conflict(grid: Grid) -> bool:
    parsed = _lawful_two_hollow_scene(grid)
    if parsed is None:
        return False
    scene, target = parsed
    rival = next(obj for obj in _hollows(scene) if obj is not target)
    return len(rival["holes"]) > len(target["holes"])


def _witness_bbox_area_conflict(grid: Grid) -> bool:
    parsed = _lawful_two_hollow_scene(grid)
    if parsed is None:
        return False
    scene, target = parsed
    rival = next(obj for obj in _hollows(scene) if obj is not target)
    return rival["bbox_area"] > target["bbox_area"]


def _witness_solid_larger_than_target(grid: Grid) -> bool:
    parsed = _lawful_two_hollow_scene(grid)
    if parsed is None:
        return False
    scene, target = parsed
    solids = [obj for obj in scene if not obj["hollow"]]
    return bool(solids) and max(obj["size"] for obj in solids) > target["size"]


def _witness_multi_hole_target(grid: Grid) -> bool:
    parsed = _lawful_two_hollow_scene(grid)
    return parsed is not None and len(parsed[1]["holes"]) == 2


def _witness_outer_perimeter_conflict(grid: Grid) -> bool:
    parsed = _lawful_two_hollow_scene(grid)
    if parsed is None:
        return False
    scene, target = parsed
    rival = next(obj for obj in _hollows(scene) if obj is not target)
    return _outer_perimeter(rival) > _outer_perimeter(target)


SEMANTIC_WITNESSES = {
    "two_hollow_candidates": _witness_two_hollows,
    "target_first": _witness_target_first,
    "target_last": _witness_target_last,
    "hole_count_conflict": _witness_hole_count_conflict,
    "bbox_area_conflict": _witness_bbox_area_conflict,
    "solid_larger_than_target": _witness_solid_larger_than_target,
    "multi_hole_target": _witness_multi_hole_target,
    "outer_perimeter_conflict": _witness_outer_perimeter_conflict,
}

WITNESS_RIVALS = {
    "two_hollow_candidates": ["fill_all_hollows", "fill_smallest_hollow", "identity"],
    "target_first": ["fill_last_hollow"],
    "target_last": ["fill_first_hollow"],
    "hole_count_conflict": ["fill_most_hole_regions_hollow"],
    "bbox_area_conflict": ["fill_largest_bbox_hollow"],
    "solid_larger_than_target": ["fill_largest_object_overall"],
    "multi_hole_target": ["fill_largest_single_hole", "fill_one_hole_of_largest"],
    "outer_perimeter_conflict": ["fill_largest_outer_perimeter"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons for which a named shortcut survives with a new answer."""
    candidates: dict[str, Callable[[Grid], Grid]] = {
        "true": _true_output,
        **SEMANTIC_RIVALS,
    }
    survivors = set(candidates)
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        grid = demo.get("input")
        official = demo.get("output")
        if self_check(grid):
            reasons.append(f"demo {index} input is outside the declared grammar")
            continue
        outputs = {name: fn(grid) for name, fn in candidates.items()}
        if outputs["true"] != official:
            reasons.append(f"demo {index} output disagrees with the Python audit mirror")
            continue
        survivors &= {name for name, output in outputs.items() if output == official}
    query_grid = query.get("input")
    query_answer = query.get("output")
    if self_check(query_grid):
        reasons.append("query input is outside the declared grammar")
        return reasons
    query_outputs = {name: fn(query_grid) for name, fn in candidates.items()}
    if query_outputs["true"] != query_answer:
        reasons.append("query output disagrees with the Python audit mirror")
        return reasons
    for name in sorted(survivors - {"true"}):
        if query_outputs[name] != query_answer:
            reasons.append(
                f"competitor {name!r} fits every demo but gives a different query answer"
            )
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return _PROFILE_SCHEDULE[sample_index % EXAMPLES_NEEDED]


def _draw_frame(grid: Grid, rect: tuple[int, int, int, int], color: int) -> None:
    r0, c0, r1, c1 = rect
    for r, c in _perimeter(r0, c0, r1, c1):
        grid[r][c] = color


def _fill_rect(grid: Grid, rect: tuple[int, int, int, int], color: int) -> None:
    r0, c0, r1, c1 = rect
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid[r][c] = color


def _base_scene(
    profile: str,
    *,
    target_color: int,
    rival_color: int,
    solid_color: int | None,
) -> Grid:
    """Construct a profile on the universal minimum 8x9 canvas."""
    grid = full_grid(8, 9, 0)
    if profile == "aligned_first":
        _draw_frame(grid, (0, 0, 3, 4), target_color)  # size 14, bbox 20
        _draw_frame(grid, (5, 0, 7, 2), rival_color)   # size 8, bbox 9
        solid_rect = (0, 6, 4, 8)                      # size 15
    elif profile == "aligned_last":
        _draw_frame(grid, (0, 0, 2, 2), rival_color)   # size 8
        _draw_frame(grid, (4, 0, 7, 4), target_color)  # size 14
        solid_rect = (0, 6, 4, 8)                      # size 15
    elif profile == "hole_count_conflict":
        _draw_frame(grid, (0, 0, 3, 4), target_color)  # one hole region, size 14
        _draw_frame(grid, (5, 0, 7, 4), rival_color)
        grid[6][2] = rival_color                       # two holes, size 13
        solid_rect = (0, 6, 4, 8)                      # size 15
    elif profile == "bbox_area_conflict":
        _draw_frame(grid, (0, 0, 3, 5), rival_color)   # size 16, bbox 24, rim 16
        _fill_rect(grid, (4, 0, 7, 4), target_color)   # bbox 20, rim 14
        grid[5][1] = 0
        grid[6][3] = 0                               # size 18, two hole regions
        solid_rect = (0, 6, 7, 8)                    # size 24, all overrides fit
    else:
        raise ValueError(f"unknown scene profile: {profile!r}")
    if solid_color is not None:
        _fill_rect(grid, solid_rect, solid_color)
    return grid


def _stretch_scene(
    base: Grid, height: int, width: int, rng, *, profile: str, strict_anchor: bool
) -> Grid:
    """Sample shape changes, retaining the selected profile's exact inequalities.

    Repeating complete rows/columns preserves component connectivity, holes,
    rectangular solid decoys and non-overlap. It can change which component is
    largest, so accept only candidates with the intended input-observable roles.
    At most 24 attempts; the proven minimum scene is always a valid fallback.
    No generated labels or rejection decisions depend on a Python output oracle.
    """
    base_h, base_w = len(base), len(base[0])
    for _ in range(24):
        row_counts = [1] * base_h
        col_counts = [1] * base_w
        for _ in range(rng.randint(0, height - base_h)):
            row_counts[rng.randrange(base_h)] += 1
        for _ in range(rng.randint(0, width - base_w)):
            col_counts[rng.randrange(base_w)] += 1
        candidate = []
        for row, count in zip(base, row_counts):
            wide = [value for value, n in zip(row, col_counts) for _ in range(n)]
            candidate.extend(list(wide) for _ in range(count))
        scene = _scene(candidate)
        if _profile_from_scene(scene) != profile:
            continue
        target = _largest_hollow(scene)
        if target is None:
            continue
        if sum(obj["size"] == target["size"] for obj in _hollows(scene)) != 1:
            continue
        solids = [obj for obj in scene if not obj["hollow"]]
        if solids and solids[0]["size"] <= target["size"]:
            continue
        if profile == "bbox_area_conflict":
            rival = next(obj for obj in _hollows(scene) if obj is not target)
            if _outer_perimeter(rival) <= _outer_perimeter(target):
                continue
        if strict_anchor and any(
            obj["cells"] != _perimeter(*obj["bbox"]) for obj in _hollows(scene)
        ):
            continue
        return candidate
    return _copy_grid(base)


def _transpose(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)]


def _flip_lr(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in grid]


def _embed(base: Grid, height: int, width: int, rng) -> Grid:
    base_h, base_w = len(base), len(base[0])
    if base_h > height or base_w > width:
        raise ValueError(
            f"scene {base_h}x{base_w} does not fit requested grid {height}x{width}"
        )
    top = rng.randint(0, height - base_h)
    left = rng.randint(0, width - base_w)
    grid = full_grid(height, width, 0)
    for r in range(base_h):
        for c in range(base_w):
            grid[top + r][left + c] = base[r][c]
    return grid


def _draw_axis_choice(ctx, label: str, options: tuple[Any, ...], default: Any) -> Any:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _draw_dimension(ctx, label: str, lo: int, hi: int, anchor: int | None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if anchor is not None:
        return ctx.draw_int(label, anchor, anchor)
    return ctx.draw_int_diff(label, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = sample_index % EXAMPLES_NEEDED
    scheduled_profile = _PROFILE_SCHEDULE[slot]
    profile = _draw_axis_choice(ctx, "scene_profile", SCENE_PROFILES, scheduled_profile)
    solid_decoy = _draw_axis_choice(
        ctx, "solid_decoy", (False, True), _SOLID_SCHEDULE[slot]
    )
    palette_kind = _draw_axis_choice(
        ctx, "palette_kind", PALETTE_KINDS, _PALETTE_SCHEDULE[slot]
    )

    anchor_dims = _CANONICAL_DIMS.get(difficulty) if slot == 0 else None
    if slot == 0 and anchor_dims is None:
        anchor_dims = ((8, 9), (9, 10), (10, 11))[
            ctx.draw_rng("canonical_profile").randrange(3)
        ]
    height = _draw_dimension(
        ctx, "grid_h", 8, 12, anchor_dims[0] if anchor_dims else None
    )
    width = _draw_dimension(
        ctx, "grid_w", 9, 14, anchor_dims[1] if anchor_dims else None
    )

    palette = _CANONICAL_COLORS if palette_kind == "canonical" else _BROAD_COLORS
    n_colors = 3 if solid_decoy else 2
    colors = ctx.draw_rng("colors").sample(list(palette), n_colors)
    target_color, rival_color = colors[:2]
    solid_color = colors[2] if solid_decoy else None
    base = _base_scene(
        profile,
        target_color=target_color,
        rival_color=rival_color,
        solid_color=solid_color,
    )

    layout_rng = ctx.draw_rng("layout")
    # Choose orientation before stretching so both available dimensions are
    # respected. Horizontal mirrors preserve scan order in the vertical layout.
    if height >= 9 and layout_rng.randrange(2):
        base = _transpose(base)
    elif layout_rng.randrange(2):
        base = _flip_lr(base)
    base = _stretch_scene(
        base, height, width, ctx.draw_rng("geometry"), profile=profile,
        strict_anchor=(slot == 0 and profile == "aligned_first"),
    )
    grid = _embed(base, height, width, layout_rng)

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "scene_profile": profile,
        "solid_decoy": solid_decoy,
        "palette_kind": palette_kind,
    }
    if observed != expected:
        raise RuntimeError(f"axis realization mismatch: expected {expected}, observed {observed}")
    return grid
