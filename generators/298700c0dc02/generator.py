"""Generator for 298700c0dc02 — mirror only the vertically symmetric object.

A full-height color-5 guide bar divides the canvas.  Two to four separate
color-4 objects appear strictly to its left.  Exactly one object is symmetric
under a left/right flip of its own tight bounding box; the canonical rule
copies only that object across the guide bar in color 8.

The default four-profile schedule is intentionally lesson-level rather than
merely morphological.  Across every three consecutive demonstrations it
changes the target's row-major position, relative size, size uniqueness, and
distance from the bar.  This prevents plausible shortcuts such as "mirror the
first object", "mirror the largest object", and "mirror the nearest object"
from surviving an otherwise valid generated lesson.
"""
from __future__ import annotations

import copy
from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "298700c0dc02"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7bd61d1b9182"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "A full-height color-5 bar has 2-4 separate color-4 objects on its left. "
    "Exactly one object is left/right symmetric within its own bounding box; "
    "mirror only that object across the bar in color 8."
)

INVARIANTS = [
    "background is 0 and the only input colors are 0, 4, and 5",
    "there is exactly one full-height color-5 guide column and no stray color 5",
    "there are 2-4 separate four-connected color-4 objects strictly left of the bar",
    "exactly one color-4 object is left/right symmetric within its tight bounding box",
    "every other color-4 object is demonstrably asymmetric",
    "the symmetric object's reflected landing cells are in bounds and empty",
]

# Every declared axis is exact and recoverable from the returned grid.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty/profile schedule within 9..13",
        "valid": "9..13",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty/profile schedule within 11..17",
        "valid": "11..17",
    },
    "n_objects": {
        "type": "int",
        "default": "profile schedule 2..4",
        "valid": "2..4",
    },
    "target_is_first": {
        "type": "bool",
        "default": "profile schedule false|true",
        "valid": "false|true",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Profile 0 and 2 put the target first and farther from the bar; profiles 1 and
# 3 put it last and adjacent to the bar.  Relative sizes are chosen so every
# three consecutive profiles refute every named shortcut below.
_PROFILE_DEFAULTS = {
    0: {
        "n_objects": 3,
        "target_is_first": True,
        "target_size": 5,
        "distractor_sizes": (4, 4),
        "target_far": True,
    },
    1: {
        "n_objects": 2,
        "target_is_first": False,
        "target_size": 4,
        "distractor_sizes": (7,),
        "target_far": False,
    },
    2: {
        "n_objects": 4,
        "target_is_first": True,
        "target_size": 7,
        "distractor_sizes": (3, 3, 3),
        "target_far": True,
    },
    3: {
        "n_objects": 2,
        "target_is_first": False,
        "target_size": 4,
        "distractor_sizes": (4,),
        "target_far": False,
    },
}

# Exact canonical dimensions occur regularly in every difficulty band; larger
# hard examples broaden the curriculum without eliminating canonical support.
_DIMENSION_SCHEDULE = {
    None: ((10, 13), (9, 11), (11, 15), (10, 13)),
    "easy": ((10, 13), (9, 11), (11, 13), (10, 13)),
    "medium": ((10, 13), (11, 15), (12, 15), (11, 13)),
    "hard": ((11, 15), (12, 17), (13, 17), (12, 15)),
}

# Every target form is left/right symmetric in its own tight bounding box.
_TARGET_FORMS = {
    4: (
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ),
    7: (
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
}

# Base asymmetric motifs.  Their complete dihedral transform sets are used at
# generation time, with every accidentally symmetric transform filtered out.
_DISTRACTOR_BASES = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (2, 3)),
    ),
    7: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0), (3, 0), (3, 1)),
    ),
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _norm(cells: Any) -> tuple[tuple[int, int], ...]:
    cells = list(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _dims(cells: Any) -> tuple[int, int]:
    normalized = _norm(cells)
    return (
        max(r for r, _ in normalized) + 1,
        max(c for _, c in normalized) + 1,
    )


def _rot_cw(cells: Any) -> tuple[tuple[int, int], ...]:
    return _norm((c, -r) for r, c in cells)


def _flip_lr_cells(cells: Any) -> tuple[tuple[int, int], ...]:
    return _norm((r, -c) for r, c in cells)


def _all_transforms(cells: Any) -> tuple[tuple[tuple[int, int], ...], ...]:
    forms: list[tuple[tuple[int, int], ...]] = []
    current = _norm(cells)
    for _ in range(4):
        for candidate in (current, _flip_lr_cells(current)):
            if candidate not in forms:
                forms.append(candidate)
        current = _rot_cw(current)
    return tuple(forms)


def _is_lr_symmetric(cells: Any) -> bool:
    normalized = _norm(cells)
    if not normalized:
        return False
    _, width = _dims(normalized)
    return normalized == tuple(sorted((r, width - 1 - c) for r, c in normalized))


def _connected(cells: Any) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    start = min(remaining)
    queue = deque([start])
    seen = {start}
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            neighbor = (r + dr, c + dc)
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == remaining


def _distractor_forms(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    forms: list[tuple[tuple[int, int], ...]] = []
    for base in _DISTRACTOR_BASES[size]:
        for form in _all_transforms(base):
            if (
                len(form) == size
                and _connected(form)
                and not _is_lr_symmetric(form)
                and form not in forms
            ):
                forms.append(form)
    if not forms:
        raise RuntimeError(f"no asymmetric connected distractor forms for size {size}")
    return tuple(forms)


_DISTRACTOR_FORMS = {
    size: _distractor_forms(size) for size in sorted(_DISTRACTOR_BASES)
}


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r0 in range(height):
        for c0 in range(width):
            if grid[r0][c0] != color or (r0, c0) in seen:
                continue
            component: list[tuple[int, int]] = []
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in _CARDINAL:
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and grid[rr][cc] == color
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            components.append(sorted(component))
    return components


def _analyze_grid(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    """Structural and semantic analysis shared by all public hooks."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"], None
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"], None
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid contains a non-ARC color"], None

    height = len(grid)
    errors: list[str] = []
    colors = {value for row in grid for value in row}
    unexpected = sorted(colors - {0, 4, 5})
    if unexpected:
        errors.append(f"unexpected input colors: {unexpected}; expected only 0, 4, and 5")

    full_bars = [
        c for c in range(width)
        if all(grid[r][c] == 5 for r in range(height))
    ]
    if len(full_bars) != 1:
        errors.append(f"expected exactly one full-height color-5 bar, found {len(full_bars)}")
        return errors, None
    bar_col = full_bars[0]
    if any(grid[r][c] == 5 and c != bar_col for r in range(height) for c in range(width)):
        errors.append("color 5 appears outside the full-height guide bar")

    components = _components(grid, 4)
    if not (2 <= len(components) <= 4):
        errors.append(f"expected 2-4 separate color-4 objects, found {len(components)}")

    infos: list[dict[str, Any]] = []
    for index, cells in enumerate(components):
        normalized = _norm(cells)
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        if len(cells) < 3:
            errors.append(f"object {index} has only {len(cells)} cells; expected at least 3")
        if max_c >= bar_col:
            errors.append(f"object {index} is not strictly left of the guide bar")
        symmetric = _is_lr_symmetric(normalized)
        infos.append({
            "index": index,
            "cells": tuple(cells),
            "normalized": normalized,
            "bbox": (min_r, min_c, max_r, max_c),
            "size": len(cells),
            "symmetric": symmetric,
            "distance_to_bar": bar_col - 1 - max_c,
        })

    symmetric_infos = [info for info in infos if info["symmetric"]]
    if len(symmetric_infos) != 1:
        errors.append(
            "expected exactly one left/right-symmetric color-4 object, "
            f"found {len(symmetric_infos)}"
        )
        target = None
    else:
        target = symmetric_infos[0]
        for r, c in target["cells"]:
            mirror_c = 2 * bar_col - c
            if not (0 <= mirror_c < width):
                errors.append("symmetric object's reflected landing is out of bounds")
            elif grid[r][mirror_c] != 0:
                errors.append("symmetric object's reflected landing is not empty")

    analysis = {
        "height": height,
        "width": width,
        "bar_col": bar_col,
        "components": infos,
        "target": target,
        "target_index": None if target is None else target["index"],
    }
    return sorted(set(errors)), analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and property-selection impostors."""
    del difficulty, meta
    errors, _ = _analyze_grid(grid)
    return errors


def observe_overrides(grid) -> dict[str, int | bool]:
    """Recover every exact declared axis from a valid returned grid."""
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None or analysis["target"] is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_objects": len(analysis["components"]),
        "target_is_first": analysis["target_index"] == 0,
    }


def _paint_mirrors(grid: list[list[int]], infos: list[dict[str, Any]]) -> list[list[int]]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside rule domain: " + "; ".join(errors))
    out = copy.deepcopy(grid)
    bar_col = analysis["bar_col"]
    for info in infos:
        for r, c in info["cells"]:
            mirror_c = 2 * bar_col - c
            if 0 <= mirror_c < len(out[0]) and out[r][mirror_c] == 0:
                out[r][mirror_c] = 8
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python reference for tests and shortcut analysis only.

    The canonical Racket program remains the output authority used by the
    pipeline and validation gates.
    """
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None or analysis["target"] is None:
        raise ValueError("outside rule domain: " + "; ".join(errors))
    return _paint_mirrors(grid, [analysis["target"]])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold, stricter than coarse morphology."""
    reasons, analysis = _analyze_grid(grid)
    if reasons or analysis is None or analysis["target"] is None:
        return reasons
    if not (9 <= analysis["height"] <= 11):
        reasons.append(f"canonical height is 9..11, got {analysis['height']}")
    if analysis["width"] not in {11, 13, 15}:
        reasons.append(f"canonical width is one of 11, 13, 15, got {analysis['width']}")
    if not (2 <= len(analysis["components"]) <= 3):
        reasons.append("canonical examples contain 2-3 color-4 objects")
    if analysis["target"]["size"] not in {4, 5}:
        reasons.append(
            f"canonical symmetric target has 4 or 5 cells, got {analysis['target']['size']}"
        )
    return reasons


def _analysis_if_valid(grid) -> dict[str, Any] | None:
    errors, analysis = _analyze_grid(grid)
    return None if errors else analysis


def _unique_extreme(infos: list[dict[str, Any]], key: Callable[[dict[str, Any]], Any], *, maximum: bool) -> dict[str, Any] | None:
    values = [key(info) for info in infos]
    extreme = (max if maximum else min)(values)
    candidates = [info for info in infos if key(info) == extreme]
    return candidates[0] if len(candidates) == 1 else None


def _rival_from_selector(grid, selector: Callable[[dict[str, Any]], list[dict[str, Any]]]) -> list[list[int]]:
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return copy.deepcopy(grid)
    selected = selector(analysis)
    if not selected:
        return copy.deepcopy(grid)
    return _paint_mirrors(grid, selected)


def _rival_first(grid):
    return _rival_from_selector(grid, lambda a: [a["components"][0]])


def _rival_last(grid):
    return _rival_from_selector(grid, lambda a: [a["components"][-1]])


def _rival_largest(grid):
    def select(analysis):
        info = _unique_extreme(analysis["components"], lambda x: x["size"], maximum=True)
        return [] if info is None else [info]
    return _rival_from_selector(grid, select)


def _rival_smallest(grid):
    def select(analysis):
        info = _unique_extreme(analysis["components"], lambda x: x["size"], maximum=False)
        return [] if info is None else [info]
    return _rival_from_selector(grid, select)


def _rival_unique_size(grid):
    def select(analysis):
        counts = Counter(info["size"] for info in analysis["components"])
        candidates = [info for info in analysis["components"] if counts[info["size"]] == 1]
        return candidates if len(candidates) == 1 else []
    return _rival_from_selector(grid, select)


def _rival_nearest_bar(grid):
    def select(analysis):
        info = _unique_extreme(
            analysis["components"], lambda x: x["distance_to_bar"], maximum=False
        )
        return [] if info is None else [info]
    return _rival_from_selector(grid, select)


def _rival_all(grid):
    return _rival_from_selector(grid, lambda a: list(a["components"]))


SEMANTIC_RIVALS = {
    "mirror_first_object": _rival_first,
    "mirror_last_object": _rival_last,
    "mirror_largest_object": _rival_largest,
    "mirror_smallest_object": _rival_smallest,
    "mirror_unique_size_object": _rival_unique_size,
    "mirror_nearest_bar_object": _rival_nearest_bar,
    "mirror_all_objects": _rival_all,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_strict(grid):
    return strict_canonical_like(grid) == []


def _witness_target_first(grid):
    analysis = _analysis_if_valid(grid)
    return analysis is not None and analysis["target_index"] == 0


def _witness_target_not_first(grid):
    analysis = _analysis_if_valid(grid)
    return analysis is not None and analysis["target_index"] != 0


def _witness_target_smaller(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    target = analysis["target"]
    return target is not None and any(target["size"] < x["size"] for x in analysis["components"])


def _witness_target_larger(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    target = analysis["target"]
    return target is not None and any(target["size"] > x["size"] for x in analysis["components"])


def _witness_target_size_tied(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    target = analysis["target"]
    return target is not None and sum(x["size"] == target["size"] for x in analysis["components"]) > 1


def _witness_target_farther(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    target = analysis["target"]
    return target is not None and any(
        target["distance_to_bar"] > x["distance_to_bar"]
        for x in analysis["components"]
        if x is not target
    )


def _witness_n_objects(count: int):
    def witness(grid):
        analysis = _analysis_if_valid(grid)
        return analysis is not None and len(analysis["components"]) == count
    return witness


SEMANTIC_WITNESSES = {
    "strict_canonical_scale_anchor": _witness_strict,
    "target_is_first_position": _witness_target_first,
    "target_is_not_first_position": _witness_target_not_first,
    "target_smaller_than_a_distractor": _witness_target_smaller,
    "target_larger_than_a_distractor": _witness_target_larger,
    "target_size_tied_with_a_distractor": _witness_target_size_tied,
    "target_farther_from_bar_than_a_distractor": _witness_target_farther,
    "object_count_2": _witness_n_objects(2),
    "object_count_3": _witness_n_objects(3),
    "object_count_4": _witness_n_objects(4),
}

WITNESS_RIVALS = {
    "strict_canonical_scale_anchor": ["mirror_all_objects"],
    "target_is_first_position": ["mirror_last_object", "mirror_all_objects"],
    "target_is_not_first_position": ["mirror_first_object", "mirror_all_objects"],
    "target_smaller_than_a_distractor": ["mirror_largest_object"],
    "target_larger_than_a_distractor": ["mirror_smallest_object"],
    "target_size_tied_with_a_distractor": ["mirror_unique_size_object"],
    "target_farther_from_bar_than_a_distractor": ["mirror_nearest_bar_object"],
    "object_count_2": ["mirror_all_objects"],
    "object_count_3": ["mirror_all_objects"],
    "object_count_4": ["mirror_all_objects"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson on which a named plausible shortcut survives."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the symmetry-selection rule")
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )
    return reasons


SCHEDULE_PROFILES = ("P0", "P1", "P2", "P3")


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return f"P{sample_index % 4}"


def _draw_int_axis(ctx, label: str, lo: int, hi: int, default: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_bool_axis(ctx, label: str, default: bool) -> bool:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return bool(ctx.draw_choice(label, (False, True)))
    return bool(ctx.draw_choice(label, (default,)))


def _translated(shape: Any, top: int, left: int) -> tuple[tuple[int, int], ...]:
    return tuple((top + r, left + c) for r, c in shape)


def _clear_of(cells: Any, occupied: set[tuple[int, int]]) -> bool:
    cells = set(cells)
    if cells & occupied:
        return False
    return not any(
        (r + dr, c + dc) in occupied
        for r, c in cells
        for dr, dc in _CARDINAL
    )


def _candidate_placements(
    size: int,
    *,
    row_lo: int,
    row_hi: int,
    bar_col: int,
    occupied: set[tuple[int, int]],
    rng,
    prefer_near: bool,
) -> list[tuple[tuple[int, int], ...]]:
    forms = list(_DISTRACTOR_FORMS[size])
    rng.shuffle(forms)
    candidates: list[tuple[tuple[int, int], ...]] = []
    for form in forms:
        form_h, form_w = _dims(form)
        if form_h > row_hi - row_lo or form_w > bar_col:
            continue
        for top in range(row_lo, row_hi - form_h + 1):
            for left in range(0, bar_col - form_w + 1):
                cells = _translated(form, top, left)
                if _clear_of(cells, occupied):
                    candidates.append(cells)
    rng.shuffle(candidates)
    if prefer_near:
        candidates.sort(key=lambda cells: bar_col - 1 - max(c for _, c in cells))
    return candidates


def _place_distractors(
    sizes: tuple[int, ...],
    *,
    row_lo: int,
    row_hi: int,
    bar_col: int,
    occupied: set[tuple[int, int]],
    rng,
    force_first_near: bool,
) -> list[tuple[tuple[int, int], ...]] | None:
    placed: list[tuple[tuple[int, int], ...]] = []

    def search(index: int) -> bool:
        if index == len(sizes):
            return True
        candidates = _candidate_placements(
            sizes[index],
            row_lo=row_lo,
            row_hi=row_hi,
            bar_col=bar_col,
            occupied=occupied,
            rng=rng,
            prefer_near=(force_first_near and index == 0),
        )
        if force_first_near and index == 0:
            nearest = [
                cells for cells in candidates
                if max(c for _, c in cells) == bar_col - 1
            ]
            if nearest:
                candidates = nearest
        for cells in candidates:
            occupied.update(cells)
            placed.append(cells)
            if search(index + 1):
                return True
            placed.pop()
            occupied.difference_update(cells)
        return False

    return list(placed) if search(0) else None


def _build_grid(
    *,
    height: int,
    width: int,
    n_objects: int,
    target_is_first: bool,
    target_size: int,
    distractor_sizes: tuple[int, ...],
    target_far: bool,
    rng,
) -> list[list[int]]:
    bar_col = (width - 1) // 2
    target_forms = list(_TARGET_FORMS[target_size])
    rng.shuffle(target_forms)

    for target_shape in target_forms:
        target_h, target_w = _dims(target_shape)
        target_top = 0 if target_is_first else height - target_h
        target_left = 0 if target_far else bar_col - target_w
        if target_left < 0 or target_left + target_w > bar_col:
            continue
        target_cells = _translated(target_shape, target_top, target_left)
        occupied = set(target_cells)

        if target_is_first:
            row_lo, row_hi = target_h + 1, height
        else:
            row_lo, row_hi = 0, height - target_h - 1
        if row_hi <= row_lo:
            continue

        placed = _place_distractors(
            distractor_sizes,
            row_lo=row_lo,
            row_hi=row_hi,
            bar_col=bar_col,
            occupied=occupied,
            rng=rng,
            force_first_near=target_far,
        )
        if placed is None:
            continue

        grid = full_grid(height, width, 0)
        for r in range(height):
            grid[r][bar_col] = 5
        for r, c in target_cells:
            grid[r][c] = 4
        for cells in placed:
            for r, c in cells:
                grid[r][c] = 4

        errors = self_check(grid)
        if errors:
            continue
        observed = observe_overrides(grid)
        if observed["n_objects"] != n_objects:
            continue
        if observed["target_is_first"] != target_is_first:
            continue
        if target_far:
            analysis = _analysis_if_valid(grid)
            target = analysis["target"] if analysis is not None else None
            if target is None or not any(
                target["distance_to_bar"] > info["distance_to_bar"]
                for info in analysis["components"]
                if info is not target
            ):
                continue
        return grid

    raise ValueError(
        "could not realize a valid one-symmetric-object layout for "
        f"{height}x{width}, n_objects={n_objects}, target_is_first={target_is_first}"
    )


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for label in ("grid_h", "grid_w", "n_objects"):
        if label in overrides and overrides[label] is not None and type(overrides[label]) is not int:
            raise ValueError(f"{label} override must be an integer")
    if (
        "target_is_first" in overrides
        and overrides["target_is_first"] is not None
        and type(overrides["target_is_first"]) is not bool
    ):
        raise ValueError("target_is_first override must be a boolean")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile_index = sample_index % 4
    profile = _PROFILE_DEFAULTS[profile_index]
    default_h, default_w = _DIMENSION_SCHEDULE[difficulty][profile_index]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_int_axis(ctx, "grid_h", 9, 13, default_h)
    width = _draw_int_axis(ctx, "grid_w", 11, 17, default_w)
    n_objects = _draw_int_axis(
        ctx, "n_objects", 2, 4, int(profile["n_objects"])
    )
    target_is_first = _draw_bool_axis(
        ctx, "target_is_first", bool(profile["target_is_first"])
    )
    rng = ctx.draw_rng("layout")

    if n_objects == profile["n_objects"]:
        distractor_sizes = tuple(profile["distractor_sizes"])
    else:
        # Boundary overrides must remain realizable even at 9x11.  Small L
        # triominoes preserve the semantic domain while packing reliably.
        distractor_sizes = (3,) * (n_objects - 1)
    if len(distractor_sizes) != n_objects - 1:
        raise RuntimeError("profile's distractor count does not match n_objects")

    grid = _build_grid(
        height=height,
        width=width,
        n_objects=n_objects,
        target_is_first=target_is_first,
        target_size=int(profile["target_size"]),
        distractor_sizes=distractor_sizes,
        target_far=bool(profile["target_far"]),
        rng=rng,
    )
    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed an invalid scene: " + "; ".join(errors))
    return grid
